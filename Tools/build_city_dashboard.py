# -*- coding: utf-8 -*-
"""城市脉搏面板生成器（确定性·零 LLM·幂等）。

读 census/export/citizens-light.jsonl，产出 census/export/city-dashboard.html：
人口/物种/街区/职业聚合 + 近 7 日年轮新增曲线 + 最新年轮流。
用法: python -X utf8 Tools/build_city_dashboard.py
"""
import collections
import datetime
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(ROOT, "census", "export", "city-dashboard.html")
FEED_LIMIT = 160
RING_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ")

SPECIES_CN = {
    "carbon": "碳基",
    "silicon": "硅基",
    "sprite": "精灵",
    "artifact-spirit": "器物灵",
    "memory-spirit": "记忆灵",
    "imagery-spirit": "意象灵",
}
DISTRICT_CN = {
    "GM": "中央市集 GM",
    "QT": "低语巷 QT",
    "MD": "机房区 MD",
    "NS": "北槐街区 NS",
    "OR": "旧站台 OR",
    "RV": "河岸 RV",
}


def load():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def bar(items, total, limit=None):
    """横向条形块 HTML。"""
    items = items[:limit] if limit else items
    out = []
    for name, cnt in items:
        pct = (cnt / total * 100) if total else 0
        out.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i style="width:%.1f%%"></i></span>'
            '<span class="num">%d · %.0f%%</span></div>'
            % (html.escape(name), pct, cnt, pct)
        )
    return "\n".join(out)


def live_lines():
    """对外实况三行（产品优先律 5）：读 docs/status-export.json 的 top_text。

    取不到就返回空列表（页面不渲染该块）——不编造、不用心跳猜。
    """
    src = os.path.join(ROOT, "docs", "status-export.json")
    try:
        with open(src, encoding="utf-8") as f:
            top = (json.load(f) or {}).get("top_text") or ""
    except Exception:
        return []
    lines = [x.strip() for x in top.splitlines() if x.strip()]
    return lines[:3] if len(lines) >= 3 else []


def ring_day_counts():
    """按卡面日期统计全部年轮圈数（逐日）。

    citizens-light 每位居民只留最新一圈，按它统计会把「同日多圈」与历史圈
    全丢掉（2026-11-13 实测今日 551 vs 真实 554、昨日 742 vs 751），且
    一旦某日无最新圈就显示 0——所以逐日曲线必须回卡面数圈。
    """
    days = collections.Counter()
    files = glob.glob(os.path.join(ROOT, "census", "registry", "**", "*.md"), recursive=True)
    files += glob.glob(os.path.join(ROOT, "census", "anchors", "*.md"))
    for p in files:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = RING_LINE.match(line)
                    if m:
                        days[m.group(1)] += 1
        except OSError:
            continue
    return days


def main():
    rows = load()
    total = len(rows)
    sp = collections.Counter((r.get("species") or "?") for r in rows)
    # 口径（2026-11-13）：创始家庭/荣誉市民（anchor 且无城区）是城主席，不是街区居民——
    # 不计入街区数，单列「荣誉席」桶；非荣誉席却无城区才是真缺口，保留「(未落户)」让它可见。
    hon = [r for r in rows if r.get("anchor") and not (r.get("district") or "").strip()]
    dist = collections.Counter(
        (r.get("district") or "").strip()
        for r in rows
        if (r.get("district") or "").strip()
    )
    unhomed = total - sum(dist.values()) - len(hon)
    if unhomed:
        dist["(未落户)"] = unhomed
    prof = collections.Counter((r.get("profession") or "(未记)") for r in rows)
    rings = [r for r in rows if r.get("recent_ring")]
    by_date = collections.Counter((r.get("recent_ring_date") or "-") for r in rings)
    ring_days = ring_day_counts()

    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    day_counts = [(d, ring_days.get(d, 0)) for d in days]
    day_max = max([c for _, c in day_counts] + [1])

    # 供给断供显式化：老日期全 0 曾连 14 天无人发现（10-29→11-11），不能只靠肉眼读条。
    # 按近 21 日全史找最长空窗段（今日之前），窗口内空窗与窗外延续段都能报出。
    streak = best = 0
    best_end = ""
    for i in range(20, 0, -1):
        d = (today - datetime.timedelta(days=i)).isoformat()
        if ring_days.get(d, 0):
            streak = 0
        else:
            streak += 1
            if streak >= best:
                best, best_end = streak, d
    last_day = max(ring_days) if ring_days else ""
    if ring_days.get(today.isoformat(), 0) == 0:
        gap_line = "今日暂未落环"
        if last_day:
            gap_line += "，最后一圈 %s" % last_day
    elif best >= 3:
        start = (datetime.date.fromisoformat(best_end) - datetime.timedelta(days=best - 1)).isoformat()
        gap_line = "近三周最长断供 %d 天（%s → %s 无新增，最后一圈 %s）" % (
            best, start, best_end, last_day)
    else:
        gap_line = ""

    feed = sorted(
        rings,
        key=lambda r: (r.get("recent_ring_date") or "", r.get("id") or ""),
        reverse=True,
    )[:FEED_LIMIT]

    day_bars = "\n".join(
        '<div class="row"><span class="lab">%s</span>'
        '<span class="track"><i style="width:%.1f%%"></i></span>'
        '<span class="num">%d</span></div>' % (d[5:], c / day_max * 100, c)
        for d, c in day_counts
    )

    cards = []
    for r in feed:
        nm = html.escape(r.get("name") or r.get("id") or "")
        meta = " · ".join(
            x
            for x in [
                html.escape(r.get("id") or ""),
                html.escape(DISTRICT_CN.get(r.get("district") or "", r.get("district") or "")),
                html.escape(r.get("profession") or ""),
            ]
            if x
        )
        cards.append(
            '<article class="card"><header><b>%s</b><time>%s</time></header>'
            '<p class="meta">%s</p><p class="ring">%s</p></article>'
            % (nm, html.escape(r.get("recent_ring_date") or ""), meta,
               html.escape(r.get("recent_ring") or ""))
        )

    # 用数据源 mtime 作「截至」时间，保证同源输入字节级幂等。
    # 注意：此串是 round_daily 内容闸的契约（SNAPSHOT_SPECS 对 citizens-light），
    # 卡面年轮数只改曲线口径，不改这个时间戳，否则每一轮都会被判 content-stale。
    gen_at = datetime.datetime.fromtimestamp(os.path.getmtime(SRC)).strftime("%Y-%m-%d %H:%M:%S")
    cov = len(rings) / total * 100 if total else 0
    live = live_lines()
    live_html = ""
    if live:
        live_html = '<div class="live">%s</div>' % "".join(
            "<div>%s</div>" % html.escape(x) for x in live
        )
    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城市脉搏 · 居民聚合面板</title>
<style>
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:12px;margin-bottom:28px}
.live{background:#161b22;border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:10px 14px;margin:0 0 24px;font-size:12.5px;color:#c9d1d9}
.live div+div{margin-top:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
.kpi{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
section{margin-bottom:28px}
h2{font-size:15px;color:var(--dim);font-weight:600;letter-spacing:.4px;margin:0 0 12px;text-transform:uppercase}
.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media(max-width:760px){.two{grid-template-columns:1fr}}
.row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}
.lab{flex:0 0 130px;color:var(--fg);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.track{flex:1;height:8px;background:#161b22;border-radius:4px;overflow:hidden}
.track i{display:block;height:100%%;background:linear-gradient(90deg,#3d7dd6,#63b3ff);border-radius:4px}
.num{flex:0 0 88px;text-align:right;color:var(--dim);font-variant-numeric:tabular-nums}
.gap{margin:10px 0 0;font-size:12px;color:var(--warm)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px}
.card{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card header b{font-size:14px}
.card time{color:var(--warm);font-size:11px;font-variant-numeric:tabular-nums}
.meta{color:var(--dim);font-size:11px;margin:2px 0 8px}
.ring{margin:0;font-size:13px;color:#c9d1d9;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
footer{margin-top:36px;color:#57606a;font-size:11px;border-top:1px solid var(--line);padding-top:14px}
</style></head><body><div class="wrap">
<h1>硅基城市脉搏</h1>
<div class="sub">居民聚合面板 · 数据截至 %(gen)s · 源=census/export/citizens-light.jsonl + census/registry 卡面年轮</div>
%(live)s

<div class="kpis">
  <div class="kpi"><b>%(total)d</b><span>在册居民</span></div>
  <div class="kpi"><b>%(rings)d</b><span>已写年轮</span></div>
  <div class="kpi"><b>%(cov).0f%%</b><span>年轮覆盖率</span></div>
  <div class="kpi"><b>%(nd)d</b><span>街区</span></div>
  <div class="kpi"><b>%(hon)d</b><span>荣誉席·创始家庭</span></div>
  <div class="kpi"><b>%(np)d</b><span>职业</span></div>
  <div class="kpi"><b>%(today)d</b><span>今日新增年轮</span></div>
</div>

<section><h2>近 7 日年轮新增 · 全圈</h2>
%(daybars)s
%(gap)s
</section>

<div class="two">
<section><h2>物种构成</h2>
%(sp)s
</section>
<section><h2>街区分布</h2>
%(dist)s
</section>
</div>

<section style="margin-top:28px"><h2>职业分布 · Top 12</h2>
%(prof)s
</section>

<section><h2>最新年轮流 · 前 %(feed)d 位</h2>
<div class="grid">
%(cards)s
</div>
</section>

<footer>确定性生成 · 生成器=Tools/build_city_dashboard.py · 无 LLM 参与 · 幂等重跑覆盖本文件</footer>
</div></body></html>
""" % {
        "gen": gen_at,
        "live": live_html,
        "total": total,
        "rings": len(rings),
        "cov": cov,
        "nd": len(dist),
        "hon": len(hon),
        "np": len(prof),
        "today": ring_days.get(today.isoformat(), 0),
        "daybars": day_bars,
        "gap": ('<p class="gap">%s</p>' % html.escape(gap_line)) if gap_line else "",
        "sp": bar([(SPECIES_CN.get(k, k), v) for k, v in sp.most_common()], total),
        "dist": bar(
            [(DISTRICT_CN.get(k, k), v) for k, v in dist.most_common()]
            + ([("荣誉席（创始家庭·非街区）", len(hon))] if hon else []),
            total,
        ),
        "prof": bar(prof.most_common(), total, limit=12),
        "feed": len(feed),
        "cards": "\n".join(cards),
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    print("OK total=%d rings=%d cards=%d out=%s bytes=%d"
          % (total, len(rings), len(feed), OUT, len(doc.encode("utf-8"))))


if __name__ == "__main__":
    main()