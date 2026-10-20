# -*- coding: utf-8 -*-
"""城市脉搏面板生成器（确定性·零 LLM·幂等）。

读 census/export/citizens-light.jsonl，产出 census/export/city-dashboard.html：
人口/物种/街区/职业聚合 + 近 7 日年轮新增曲线 + 最新年轮流。
用法: python -X utf8 Tools/build_city_dashboard.py
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(ROOT, "census", "export", "city-dashboard.html")
FEED_LIMIT = 160

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


def main():
    rows = load()
    total = len(rows)
    sp = collections.Counter((r.get("species") or "?") for r in rows)
    dist = collections.Counter((r.get("district") or "(未落户)") for r in rows)
    prof = collections.Counter((r.get("profession") or "(未记)") for r in rows)
    rings = [r for r in rows if r.get("recent_ring")]
    by_date = collections.Counter((r.get("recent_ring_date") or "-") for r in rings)

    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    day_counts = [(d, by_date.get(d, 0)) for d in days]
    day_max = max([c for _, c in day_counts] + [1])

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

    # 用数据源 mtime 作「截至」时间，保证同源输入字节级幂等
    gen_at = datetime.datetime.fromtimestamp(os.path.getmtime(SRC)).strftime("%Y-%m-%d %H:%M:%S")
    cov = len(rings) / total * 100 if total else 0
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
<div class="sub">居民聚合面板 · 数据截至 %(gen)s · 源=census/export/citizens-light.jsonl</div>

<div class="kpis">
  <div class="kpi"><b>%(total)d</b><span>在册居民</span></div>
  <div class="kpi"><b>%(rings)d</b><span>已写年轮</span></div>
  <div class="kpi"><b>%(cov).0f%%</b><span>年轮覆盖率</span></div>
  <div class="kpi"><b>%(nd)d</b><span>街区</span></div>
  <div class="kpi"><b>%(np)d</b><span>职业</span></div>
  <div class="kpi"><b>%(today)d</b><span>今日新增年轮</span></div>
</div>

<section><h2>近 7 日年轮新增</h2>
%(daybars)s
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
        "total": total,
        "rings": len(rings),
        "cov": cov,
        "nd": len(dist),
        "np": len(prof),
        "today": by_date.get(today.isoformat(), 0),
        "daybars": day_bars,
        "sp": bar([(SPECIES_CN.get(k, k), v) for k, v in sp.most_common()], total),
        "dist": bar([(DISTRICT_CN.get(k, k), v) for k, v in dist.most_common()], total),
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