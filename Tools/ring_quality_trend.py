# -*- coding: utf-8 -*-
"""年轮品质趋势（零 LLM·确定性）——品质闸的「过程可见」面。

背景（2026-10-27 R2396）：R2381 的三查只给了一张当日快照，看不出方向——
写得好没好、重写波起没起效，全靠人翻报告。本工具把同一套判据按「年轮日期」
摊成时间序列，让每一个生产日都能横向对比，今晚起的重写波次日即可验。

判据与 ring_simile_audit 同源（直接复用其 parse/core/grams/jaccard 与阈值）：
  short = 正文（去 [锚] 注脚）去标点后 < SHORT_CHARS 字
  sim   = 与本卡上一圈正文 3-gram Jaccard ≥ SIM_TH（算在后一圈的日期上）
  tmpl  = 含全局模板句（TMPL_GRAM 字窗口被 ≥ TMPL_CITIZENS 位居民共用）
  def   = 该圈命中任一判据（圈级缺陷率 = def / 当日年轮数）

产物：
  census/export/city-ring-trend.html   走势页（日柱状 + 逐日表）
  state/ring-trend-latest.json         机器面（逐日指标，落盘不入库）

用法：
  python -X utf8 Tools/ring_quality_trend.py [--since 2026-09-01] [--days 28]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import html
import io
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ring_simile_audit import (  # noqa: E402
    PUNCT_RE,
    SHORT_CHARS,
    SIM_TH,
    TMPL_CITIZENS,
    TMPL_GRAM,
    core,
    grams,
    jaccard,
    parse,
)
from ring_open_family import (  # noqa: E402
    FAMILY_MIN_DENOM,
    FAMILY_QUOTA,
    check_verdict,
    epoch_mix_state,
    epochs_of,
    family_of,
    over_quota,
    second_attrs_of,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "census", "export", "city-ring-trend.html")
SNAP = os.path.join(ROOT, "state", "ring-trend-latest.json")


def collect(since: str) -> tuple[list[dict], dict[str, int], dict[str, list[str]]]:
    """逐圈明细 + 全局模板句计数 + 按日正文（开头族判据复用同一趟扫盘）。"""
    rows: list[dict] = []
    gram_citizens: dict[str, set[str]] = collections.defaultdict(set)
    bodies: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(ROOT, "census", "registry", "**", "*.md"),
                                 recursive=True)):
        cid, _name, rings = parse(path)
        if not cid:
            continue
        rings = [(d, b) for d, b in rings if d >= since]
        if not rings:
            continue
        prev = None
        for date, body in rings:
            bodies[date].append(body)
            c = core(body)
            clean = PUNCT_RE.sub("", c)
            sh = {clean[i:i + TMPL_GRAM]
                  for i in range(max(0, len(clean) - TMPL_GRAM + 1))}
            for x in sh:
                gram_citizens[x].add(cid)
            sim = jaccard(prev, grams(c)) if prev is not None else 0.0
            rows.append({"date": date, "cid": cid, "chars": len(clean),
                         "sh": sh, "sim": sim})
            prev = grams(c)
    return rows, {k: len(v) for k, v in gram_citizens.items()}, bodies


def _opening_body(text: str) -> str:
    """剥掉年轮引号，复现闸口 _ring_pat 的 group(1) 口径（含/不含「」差 1 字即错位）。"""
    t = (text or "").strip()
    if t[:1] in ("「", "『"):
        t = t[1:]
    if t[-1:] in ("」", "』"):
        t = t[:-1]
    return t


def family_daily(bodies: dict[str, list[str]]) -> list[dict]:
    """按生产日统计开头骨架族与第二句吸引子占比。

    判据单源=ring_open_family（family_of／second_attrs_of／over_quota），
    与 evolve_citizen 拒稿闸同一套 regex，故本页读数即闸口读数，不会漂移。
    """
    out = []
    for date in sorted(bodies):
        texts = [t for t in (_opening_body(x) for x in bodies[date])
                 if len("".join(t.split())) >= 8]
        total = len(texts)
        fam = collections.Counter(f for f in (family_of(t) for t in texts) if f)
        sec: collections.Counter = collections.Counter()
        for t in texts:
            for name in second_attrs_of(t):
                sec[name] += 1
        hand = fam.get("HAND_DEICTIC", 0)
        wind = sec.get("WIND_ACTION", 0)
        over_fams = sorted(
            ((k, round(100.0 * n / total, 1)) for k, n in fam.items() if n / total > FAMILY_QUOTA),
            key=lambda x: -x[1])
        out.append({
            "date": date,
            "rings": total,
            "fam": dict(fam),
            "hand": hand,
            "hand_rate": round(100.0 * hand / total, 1) if total else 0.0,
            "wind_rate": round(100.0 * wind / total, 1) if total else 0.0,
            "over": over_quota(total, dict(fam)),
            "over_fams": over_fams,
            "judged": total >= FAMILY_MIN_DENOM,
            # 纪元口径（与 --check 同源）：立族当天/守卫上线前的读数跨两版族表，
            # 占比不可与 25% 线对账，展示「跨口径」而非 OVER（R2790）。
            "mix": epoch_mix_state(epochs_of(date)),
        })
    return out


def daily(rows: list[dict], gram_citizens: dict[str, int]) -> list[dict]:
    tmpl_set = {k for k, n in gram_citizens.items() if n >= TMPL_CITIZENS}
    buckets: dict[str, list[dict]] = collections.defaultdict(list)
    for r in rows:
        r["short"] = r["chars"] < SHORT_CHARS
        r["dup"] = r["sim"] >= SIM_TH
        r["tmpl"] = bool(r["sh"] & tmpl_set)
        r["defect"] = r["short"] or r["dup"] or r["tmpl"]
        buckets[r["date"]].append(r)
    out = []
    for date in sorted(buckets):
        g = buckets[date]
        n = len(g)
        d = sum(1 for r in g if r["defect"])
        out.append({
            "date": date,
            "rings": n,
            "citizens": len({r["cid"] for r in g}),
            "chars_median": int(statistics.median(r["chars"] for r in g)),
            "short": sum(1 for r in g if r["short"]),
            "dup": sum(1 for r in g if r["dup"]),
            "tmpl": sum(1 for r in g if r["tmpl"]),
            "defect": d,
            "defect_rate": round(100.0 * d / n, 1),
        })
    return out


def spark(days: list[dict], key: str, ink: str, unit: str) -> str:
    """等宽日柱：值越高柱越高（defect_rate 用同一函数，读的时候看数字）。"""
    if not days:
        return '<p class="meta">（无数据）</p>'
    top = max(d[key] for d in days) or 1
    bar_w = 24
    gap = 6
    w = len(days) * (bar_w + gap)
    h = 120
    parts = []
    for i, d in enumerate(days):
        v = d[key]
        bh = max(2, int(h * v / top))
        x = i * (bar_w + gap)
        parts.append(
            '<rect x="%.0f" y="%d" width="%d" height="%d" fill="%s" rx="2"><title>%s %s%s</title></rect>'
            % (x, h - bh, bar_w, bh, ink, d["date"], v, unit))
        parts.append('<text x="%.0f" y="%d" fill="#8d94a3" font-size="9" text-anchor="middle">%s</text>'
                     % (x + bar_w / 2, h + 14, d["date"][5:]))
    return ('<svg viewBox="0 0 %d %d" width="100%%" height="%d" role="img">%s</svg>'
            % (max(w, 1), h + 20, h + 20, "".join(parts)))


def build_page(days: list[dict], stats: dict, fams: list[dict]) -> str:
    e = html.escape
    recent = days[-stats["days"]:]
    fam_recent = fams[-stats["days"]:]
    def _verdict(f: dict) -> str:
        if not f["judged"]:
            return "—"
        if not f["over"]:
            return "OK"
        # 表内只列 HAND_DEICTIC，超线族可能是另两族，必须点名防误读为「本列超线」
        _names = "、".join("%s %.1f%%" % x for x in f["over_fams"])
        if f.get("mix") != "single":
            # 混口径日（立族当天重扫/守卫上线前）：越线来自新表对旧环的重分类，
            # 不等于当日生产越线 → 明标不可比（R2790，与 --check 三态同源）
            return "跨口径（%s）" % _names
        return "OVER（%s）" % _names

    fam_table = "".join(
        "<tr><td>%s</td><td>%d</td><td>%d</td><td>%.1f%%</td><td>%.1f%%</td><td>%s</td></tr>"
        % (e(f["date"]), f["rings"], f["hand"], f["hand_rate"], f["wind_rate"], _verdict(f))
        for f in reversed(fam_recent))
    row_fmt = ("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>"
               "<td>%d</td><td>%.1f%%</td></tr>")
    rows = "".join(
        row_fmt
        % (e(d["date"]), d["rings"], d["citizens"], d["chars_median"],
           d["short"], d["dup"], d["tmpl"], d["defect_rate"])
        for d in reversed(recent))
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>年轮品质走势 · BigLife</title>
<style>
:root{{--bg:#12141a;--fg:#e6e6e6;--dim:#8d94a3;--line:#262a33;--accent:#7fb0d8;--warn:#d89a7f;--ok:#8fc79a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "Noto Sans SC","Microsoft YaHei",sans-serif}}
header{{padding:28px 20px 12px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:20px;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;padding:16px 20px;border-bottom:1px solid var(--line)}}
.kpi{{border:1px solid var(--line);border-radius:6px;padding:10px 14px;background:#171a21;min-width:150px}}
.kpi b{{display:block;font-size:22px;font-weight:600}}
.kpi span{{color:var(--dim);font-size:12px}}
h2.sec{{padding:20px 20px 6px;font-size:16px;margin:0}}
.chart{{padding:0 20px 6px}}
table{{border-collapse:collapse;margin:0 20px 10px;font-size:14px}}
th,td{{border:1px solid var(--line);padding:6px 10px;text-align:left}}
th{{color:var(--dim);font-weight:500}}
.meta{{color:var(--dim);font-size:12px;padding:0 20px}}
footer{{padding:16px 20px 40px;color:var(--dim);font-size:12px;border-top:1px solid var(--line);margin-top:12px}}
</style></head>
<body><!--bl-nav:index--><div style="position:fixed;left:12px;top:12px;z-index:9999"><a href="index.html" style="display:inline-block;padding:5px 10px;background:rgba(20,24,30,.86);border:1px solid #303740;border-radius:4px;color:#c8a06a;font:12px/1 'Songti SC',Georgia,serif;text-decoration:none">← 城市目录</a></div>
<header>
<h1>年轮品质走势</h1>
<p class="sub">扫描面 {e(stats['since'])} 起 · 覆盖 {stats['active_days']} 个生产日 ·
最近 {stats['days']} 日展示 · 生成 {e(stats['day'])}（零 LLM·判据同 RING-SIMILE 三查）</p>
</header>
<div class="kpis">
<div class="kpi"><b>{stats['rings']}</b><span>年轮总数（扫描面内）</span></div>
<div class="kpi"><b>{stats['recent_rate']:.1f}%</b><span>近 7 日圈级缺陷率</span></div>
<div class="kpi"><b>{stats['best'][0]}</b><span>最佳日缺陷率（{stats['best'][1]}）</span></div>
<div class="kpi"><b>{stats['worst'][0]}</b><span>最差日缺陷率（{stats['worst'][1]}）</span></div>
<div class="kpi"><b>{stats['hand_now']:.1f}%</b><span>最近生产日手部指示开头（闸线 {stats['quota']:.0f}%）</span></div>
<div class="kpi"><b>{stats['hand_verdict']}</b><span>开头族闸判定（{stats['hand_day']}·{stats['hand_rings']} 环{('·超线 ' + stats['hand_over']) if stats['hand_over'] else ''}）</span></div>
</div>
<h2 class="sec">每日年轮产量</h2>
<div class="chart">{spark(recent, 'rings', '#7fb0d8', ' 圈')}</div>
<h2 class="sec">每日圈级缺陷率（越低越好）</h2>
<div class="chart">{spark(recent, 'defect_rate', '#d89a7f', '%')}</div>
<h2 class="sec">年轮开头骨架族占比（源头闸判据 · 闸线 {stats['quota']:.0f}%）</h2>
<div class="chart">{spark(fam_recent, 'hand_rate', '#d89a7f', '%')}</div>
<h2 class="sec">逐日开头族 / 第二句吸引子（日期倒序）</h2>
<table><tr><th>日期</th><th>年轮</th><th>HAND_DEICTIC</th><th>占比</th><th>第二句 WIND_ACTION</th><th>闸判定</th></tr>{fam_table}</table>
<p class="meta">开头族只量正文前 12 字，句中合法身体描写（如下半句的「手心的汗」）不计入；
闸判定 OVER = 族表中 <b>任一</b>族当日占比 &gt; {stats['quota']:.0f}%（{stats['min_denom']} 环以下不判，记「—」）；
本表只列 HAND_DEICTIC，故 0.0% 仍可能判 OVER——括号内点名超线族。
第二句 WIND_ACTION 为只观测指标，尚未入闸（T-20261112-05 观测窗）。</p>
<h2 class="sec">逐日明细（近 {len(recent)} 日 · 日期倒序）</h2>
<table><tr><th>日期</th><th>年轮</th><th>居民</th><th>中位字数</th><th>偏短</th><th>复读</th><th>模板</th><th>缺陷率</th></tr>{rows}</table>
<p class="meta">缺陷判定为圈级去重计数：同一圈命中多项只算一次，故「偏短+复读+模板」三列之和可能大于缺陷数。</p>
<footer>
判据：偏短 = 正文去标点后 &lt; {SHORT_CHARS} 字；复读 = 与本卡上一圈 3-gram Jaccard ≥ {SIM_TH:.2f}（记在后一圈的日期上）；
模板 = 含 &lt; {TMPL_GRAM} 字窗口被 ≥ {TMPL_CITIZENS} 位居民共用的句块。存量年轮不回改（锚定律），本页只计量。
机器面：state/ring-trend-latest.json · 相邻品质页：city-ring-quality.html（重写队列）
</footer>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-09-01")
    ap.add_argument("--days", type=int, default=28)
    args = ap.parse_args()

    day = datetime.date.today().isoformat()
    rows, gram_citizens, bodies = collect(args.since)
    days = daily(rows, gram_citizens)
    if not days:
        print("no rings since %s" % args.since)
        return 1
    fams = family_daily(bodies)
    judged = [f for f in fams if f["judged"]] or fams
    now = judged[-1] if judged else {"date": day, "hand_rate": 0.0, "rings": 0,
                                     "over": [], "mix": "single"}

    last7 = days[-7:]
    recent_def = sum(d["defect"] for d in last7)
    recent_rings = sum(d["rings"] for d in last7)
    ranked = sorted(days, key=lambda d: d["defect_rate"])
    stats = {
        "since": args.since, "day": day, "days": args.days,
        "active_days": len(days),
        "rings": sum(d["rings"] for d in days),
        "recent_rate": 100.0 * recent_def / recent_rings if recent_rings else 0.0,
        "best": ("%.1f%%" % ranked[0]["defect_rate"], ranked[0]["date"]),
        "worst": ("%.1f%%" % ranked[-1]["defect_rate"], ranked[-1]["date"]),
        "hand_now": now["hand_rate"],
        "hand_day": now["date"],
        "hand_rings": now["rings"],
        "hand_verdict": ("跨口径" if now.get("mix") != "single"
                         else ("OVER" if now["over"] else "OK")),
        "hand_over": "、".join("%s %.1f%%" % x for x in now.get("over_fams") or []),
        "quota": 100.0 * FAMILY_QUOTA,
        "min_denom": FAMILY_MIN_DENOM,
    }

    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    os.makedirs(os.path.dirname(SNAP), exist_ok=True)
    with io.open(PAGE, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_page(days, stats, fams))
    with io.open(SNAP, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generated": day, "since": args.since, "days": days,
                   "families": fams, "family_quota": FAMILY_QUOTA},
                  f, ensure_ascii=False, indent=1)

    tail = days[-stats["days"]:]
    print("days=%d rings=%d recent7_rate=%.1f%% best=%s(%s) worst=%s(%s) page=%s"
          % (stats["active_days"], stats["rings"], stats["recent_rate"],
             stats["best"][0], stats["best"][1], stats["worst"][0], stats["worst"][1],
             os.path.relpath(PAGE, ROOT)))
    print("opening-family: %s %d圈 HAND_DEICTIC=%.1f%% (线 %.0f%%) verdict=%s%s"
          % (stats["hand_day"], stats["hand_rings"], stats["hand_now"],
             stats["quota"], stats["hand_verdict"],
             (" [超线 " + stats["hand_over"] + "]") if stats["hand_over"] else ""))
    print("last: " + ", ".join("%s %d圈/%.1f%%" % (d["date"][5:], d["rings"], d["defect_rate"])
                               for d in tail[-6:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())