# -*- coding: utf-8 -*-
"""城市叙龄面板（确定性·零 LLM·幂等）

读 census/export/citizens-light.jsonl，产出 census/export/city-ring-recency.html：
  1) 全城「距上次年轮天数」分档（0 / 1-2 / 3-6 / 7-13 / 14-29 / 30+ / 无日期）
  2) 分街区叙龄（人数·今日·7 日内·中位天数·最久天数）
  3) 最久未开口的居民名单（附其最后一句年轮），夜间年轮批可照单开工
  4) 产能口径：今日落环数 → 现有人口覆盖一轮需多少天

为什么单开这一面（缺什么补什么）：
  - city-ring-trend.html 管「质量」（缺陷率/开口族占比），city-coverage.html 管
    「结构欠账」（四维齐备），两者都不回答「有多少居民多久没说过话」。
  - 2026-11-13 实测：10114 居民里 7366 人（72.8%）叙龄 14-29 天、1455 人 30 天+，
    而当日只落 551 环 —— 这条产能差距此前没有任何可见面承载，只能人肉翻导出。

口径注：荣誉席（faction=honored，创始家庭/CEO 保留面）年轮由 CEO 亲定，不计叙龄。
用法: python -X utf8 Tools/build_ring_recency.py
注意：直接跑本脚本会覆盖页面、连带抹掉 build_export_index 注入的导航条
（<!--bl-nav:index-->）——改完页面后必须紧随跑一次 build_export_index.py，
否则该页失去「回到总目录」入口（正常轮内走 round_daily --run 时索引档自动补）。
"""
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
SRC = os.path.join(EXP, "citizens-light.jsonl")
OUT_HTML = os.path.join(EXP, "city-ring-recency.html")
TOP = 24

import sys

sys.path.insert(0, os.path.join(ROOT, "Tools"))
from build_city_meets import DISTRICT_CN  # noqa: E402

# 分档顺序固定（判据=天数，不是标签）——改档位必须同步改 BUCKETS 与 bucket_of
BUCKETS = [
    ("0d", "今日", 0, 0),
    ("1-2d", "1-2 天", 1, 2),
    ("3-6d", "3-6 天", 3, 6),
    ("7-13d", "7-13 天", 7, 13),
    ("14-29d", "14-29 天", 14, 29),
    ("30d+", "30 天以上", 30, 10 ** 6),
]
NODATE = "无日期"

CSS = """
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e;--red:#e5605c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:12px;margin-bottom:28px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
.kpi{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
.kpi.warn b{color:var(--warm)}
.kpi.bad b{color:var(--red)}
section{margin-bottom:28px}
h2{font-size:15px;color:var(--dim);font-weight:600;letter-spacing:.4px;margin:0 0 12px;text-transform:uppercase}
.row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}
.lab{flex:0 0 110px;color:var(--fg)}
.track{flex:1;height:8px;background:#161b22;border-radius:4px;overflow:hidden}
.track i{display:block;height:100%;background:linear-gradient(90deg,#3d7dd6,#63b3ff);border-radius:4px}
.track i.hot{background:linear-gradient(90deg,#c9762f,#f0a35e)}
.track i.cold{background:linear-gradient(90deg,#a13c39,#e5605c)}
.num{flex:0 0 150px;text-align:right;color:var(--dim);font-variant-numeric:tabular-nums}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:600;font-size:12px}
td{font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px}
.card{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card header b{font-size:14px}
.card time{color:var(--warm);font-size:11px;font-variant-numeric:tabular-nums}
.meta{color:var(--dim);font-size:11px;margin:2px 0 8px}
.ring{margin:0;font-size:13px;color:#c9d1d9}
.note{color:var(--dim);font-size:12.5px;line-height:1.8;margin:10px 0 0}
.note a{color:var(--acc);text-decoration:none}
footer{margin-top:36px;color:#57606a;font-size:11px;border-top:1px solid var(--line);padding-top:14px}
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load_rows():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def days_since(raw, today):
    """返回距今天数；无日期/坏日期返回 None（如实计入「无日期」档，不猜）。"""
    d = (raw or "").strip()
    if not d:
        return None
    try:
        return (today - datetime.date.fromisoformat(d[:10])).days
    except ValueError:
        return None


def bucket_of(age):
    if age is None:
        return NODATE
    if age < 0:
        # 未来日期=数据异常，单列不并入今日，避免把坏数据洗成健康信号
        return NODATE
    for key, _lab, lo, hi in BUCKETS:
        if lo <= age <= hi:
            return key
    return NODATE


def median(vals):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def main():
    rows = load_rows()
    today = datetime.date.today()
    total = len(rows)

    scope, reserved, nodate_names = [], 0, []
    for r in rows:
        if r.get("faction") == "honored":
            reserved += 1
            continue
        scope.append(r)

    counts = {key: 0 for key, _l, _lo, _hi in BUCKETS}
    counts[NODATE] = 0
    ages = []
    by_dist = {}
    silent = []

    for r in scope:
        age = days_since(r.get("recent_ring_date"), today)
        key = bucket_of(age)
        counts[key] = counts.get(key, 0) + 1
        if age is None:
            nodate_names.append(r)
        else:
            ages.append(age)
        d = r.get("district") or ""
        cell = by_dist.setdefault(d or "", {"n": 0, "today": 0, "week": 0, "ages": [], "max": 0})
        cell["n"] += 1
        if age is not None:
            if age == 0:
                cell["today"] += 1
            if age <= 6:
                cell["week"] += 1
            cell["ages"].append(age)
            cell["max"] = max(cell["max"], age)
        silent.append((age if age is not None else 10 ** 9, r))

    covered = len(scope) - counts[NODATE]
    fresh7 = sum(counts[k] for k in ("0d", "1-2d", "3-6d"))
    due_now = len(scope) - counts["0d"]
    rate = counts["0d"] or 0
    cycle = (due_now / rate) if rate else None
    med = median(ages)

    # ── 分档条 ──
    bars = []
    for key, label, _lo, _hi in BUCKETS:
        cnt = counts[key]
        pct = cnt / len(scope) * 100 if scope else 0
        cls = "cold" if key == "30d+" else ("hot" if key in ("14-29d",) else "")
        bars.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i class="%s" style="width:%.1f%%"></i></span>'
            '<span class="num">%d · %.1f%%</span></div>'
            % (esc(label), cls, pct, cnt, pct)
        )
    if counts[NODATE]:
        cnt = counts[NODATE]
        pct = cnt / len(scope) * 100 if scope else 0
        bars.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i class="cold" style="width:%.1f%%"></i></span>'
            '<span class="num">%d · %.1f%%</span></div>' % (esc(NODATE), pct, cnt, pct)
        )

    # ── 街区表（按叙龄中位数降序：最沉默的城区排前面）──
    dist_rows = []
    ranking = []
    for code, cell in by_dist.items():
        ranking.append((median(cell["ages"]) if cell["ages"] else 9999, code, cell))
    ranking.sort(key=lambda x: (-(x[0] if x[0] is not None else 9999), x[1]))
    for m, code, cell in ranking:
        name = DISTRICT_CN.get(code, code) or "未落区"
        dist_rows.append(
            "<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%s</td><td>%d</td></tr>"
            % (esc(name), cell["n"], cell["today"], cell["week"],
               ("%.1f" % m) if m is not None else "—", cell["max"])
        )

    # ── 最久未开口名单（含最后一句，供年轮批照单开工）──
    silent.sort(key=lambda x: (-x[0], (x[1].get("id") or "")))
    cards = []
    for age, r in silent[:TOP]:
        if age >= 10 ** 9:
            continue
        last = (r.get("recent_ring") or "").strip()
        if len(last) > 60:
            last = last[:60] + "…"
        cards.append(
            '<article class="card"><header><b>%s</b><time>%d 天</time></header>'
            '<p class="meta">%s · %s · 上次 %s</p><p class="ring">%s</p></article>'
            % (esc(r.get("name") or r.get("id")), age,
               esc(DISTRICT_CN.get(r.get("district") or "", r.get("district") or "未落区")),
               esc(r.get("profession") or r.get("species") or ""),
               esc((r.get("recent_ring_date") or "")[:10]), esc(last or "（无留痕）"))
        )

    last_date = max((r.get("recent_ring_date") or "")[:10] for r in scope) if scope else "—"
    kpi_cycle = ("%.1f 天" % cycle) if cycle else "—"
    kpi_med = ("%.1f 天" % med) if med is not None else "—"

    doc = (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>硅基城市叙龄 · 谁还开着口</title>\n<style>%s</style></head><body><div class=\"wrap\">\n"
        "<h1>硅基城市叙龄 · 谁还开着口</h1>\n"
        '<div class="sub">全城居民「距上次年轮天数」分档 + 分街区叙龄 + 最久未开口名单 · '
        "源 census/export/citizens-light.jsonl（最新叙龄日 %s）· 在册 %d · 荣誉席 %d 不计</div>\n"
        '<div class="kpis">\n'
        '  <div class="kpi"><b>%d</b><span>计入叙龄的居民</span></div>\n'
        '  <div class="kpi"><b>%d</b><span>7 日内开过口 · 占 %.1f%%</span></div>\n'
        '  <div class="kpi warn"><b>%d</b><span>14 天以上没开口 · 占 %.1f%%</span></div>\n'
        '  <div class="kpi bad"><b>%d</b><span>30 天以上没开口</span></div>\n'
        '  <div class="kpi"><b>%s</b><span>全城中位叙龄</span></div>\n'
        '  <div class="kpi"><b>%s</b><span>按今日落环 %d 环算，覆盖一轮所需</span></div>\n'
        "</div>\n"
        "<section><h2>叙龄分档（越靠下越久没说话）</h2>\n%s\n"
        '<p class="note">「叙龄」=今天减上次年轮日期。零 LLM·确定性派生；'
        "日期缺失/坏日期单列「无日期」，不当作今日健康信号（%d 席）。</p></section>\n"
        "<section><h2>分街区叙龄（按中位叙龄降序）</h2>\n"
        "<table><thead><tr><th>街区</th><th>居民</th><th>今日</th><th>7 日内</th>"
        "<th>中位叙龄</th><th>最久</th></tr></thead><tbody>\n%s\n</tbody></table></section>\n"
        "<section><h2>最久未开口 %d 席（年轮批可照单开工）</h2>\n<div class=\"grid\">\n%s\n"
        "</div></section>\n"
        '<footer>产能口径：今日落环 %d 环 / 待更新 %d 人 ⇒ 覆盖一轮约 %s；'
        "全员 7 日一轮需 ≈%.0f 环/日。相关面："
        '<a href="city-ring-trend.html">质量趋势</a> · '
        '<a href="city-ring-quality.html">年轮体检</a> · '
        '<a href="city-coverage.html">库覆盖缺口</a> · '
        '<a href="meet-candidates.html">相遇候选</a>。'
        "生成器 Tools/build_ring_recency.py（零 LLM·幂等·同输入双跑逐字节一致）</footer>\n"
        "</div></body></html>\n"
    ) % (
        CSS, esc(last_date), total, reserved,
        len(scope), fresh7, (fresh7 / len(scope) * 100 if scope else 0),
        counts["14-29d"] + counts["30d+"],
        ((counts["14-29d"] + counts["30d+"]) / len(scope) * 100 if scope else 0),
        counts["30d+"],
        kpi_med, kpi_cycle, rate,
        "\n".join(bars),
        counts[NODATE],
        "\n".join(dist_rows),
        min(TOP, len(cards)),
        "\n".join(cards),
        rate, due_now, kpi_cycle, len(scope) / 7.0,
    )

    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)

    print(
        "ring-recency: scope=%d reserved=%d fresh7d=%d(%.1f%%) stale14=%d stale30=%d "
        "nodate=%d median=%s today=%d cycle=%s -> %s"
        % (len(scope), reserved, fresh7, (fresh7 / len(scope) * 100 if scope else 0),
           counts["14-29d"] + counts["30d+"], counts["30d+"], counts[NODATE],
           kpi_med, rate, kpi_cycle, os.path.basename(OUT_HTML))
    )
    for key, label, _lo, _hi in BUCKETS:
        cnt = counts[key]
        print("  %-8s %5d %.1f%%" % (label, cnt, cnt / len(scope) * 100 if scope else 0))


if __name__ == "__main__":
    main()
