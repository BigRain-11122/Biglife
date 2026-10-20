# -*- coding: utf-8 -*-
"""城区志生成器（确定性·零 LLM·幂等）。

读 census/export/citizens-light.jsonl 与 genes/meta.json，按城区聚合：
人口 / 物种 / 派系 / 职业 / 街区 / 六轴 / 年轮覆盖 / 代表居民与最新年轮，
产出 census/export/city-districts.html。

用法: python -X utf8 Tools/build_district_chronicle.py
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
META = os.path.join(ROOT, "genes", "meta.json")
OUT = os.path.join(ROOT, "census", "export", "city-districts.html")

SPECIES_CN = {
    "carbon": "碳基",
    "silicon": "硅基",
    "sprite": "精灵",
    "artifact-spirit": "器物灵",
    "memory-spirit": "记忆灵",
    "imagery-spirit": "意象灵",
}
FACTION_CN = {
    "native": "原生代",
    "honored": "荣誉席",
    "resident": "居民",
    "drift": "漂流派",
    "migrant": "迁入派",
}
BLOCK_TOP = 6
PROF_TOP = 8
AXIS_TOP = 6
REP_N = 3


def load_rows():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def district_meta():
    try:
        with open(META, encoding="utf-8") as f:
            meta = json.load(f)
        return [(d["id"], d["name"]) for d in meta.get("districts", [])]
    except Exception:
        return []


def bar(items, total, limit=None):
    items = items[:limit] if limit else items
    out = []
    for name, cnt in items:
        pct = (cnt / total * 100) if total else 0
        out.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i style="width:%.1f%%"></i></span>'
            '<span class="num">%d · %.0f%%</span></div>'
            % (html.escape(str(name)), pct, cnt, pct)
        )
    return "\n".join(out)


def main():
    rows = load_rows()
    total = len(rows)
    names = district_meta()
    order = [d for d, _ in names] or sorted({(r.get("district") or "?") for r in rows})
    label = dict(names)

    groups = collections.OrderedDict((d, []) for d in order)
    for r in rows:
        d = r.get("district") or ""
        if d in groups:
            groups[d].append(r)

    ring_rows = [r for r in rows if r.get("recent_ring")]
    latest = sorted(
        ring_rows,
        key=lambda r: (r.get("recent_ring_date") or "", r.get("id") or ""),
        reverse=True,
    )[:24]

    # 全城近 7 日年轮密度
    by_date = collections.Counter((r.get("recent_ring_date") or "-") for r in ring_rows)
    today = datetime.date.today()
    days = [(today - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    day_counts = [(d, by_date.get(d, 0)) for d in days]
    day_max = max([c for _, c in day_counts] + [1])
    day_bars = "\n".join(
        '<div class="row"><span class="lab">%s</span>'
        '<span class="track"><i style="width:%.1f%%"></i></span>'
        '<span class="num">%d</span></div>' % (d[5:], c / day_max * 100, c)
        for d, c in day_counts
    )

    sections = []
    for d, members in groups.items():
        n = len(members)
        if not n:
            sections.append(
                '<section class="dist"><h2>%s<em>%s</em></h2>'
                '<p class="empty">暂无在册居民</p></section>'
                % (html.escape(label.get(d, d)), html.escape(d))
            )
            continue

        sp = collections.Counter((r.get("species") or "?") for r in members)
        fac = collections.Counter((r.get("faction") or "?") for r in members)
        prof = collections.Counter((r.get("profession") or "(未记)") for r in members)
        blk = collections.Counter((r.get("block") or "(未记)") for r in members)
        axis = collections.Counter((r.get("axis") or "(未记)") for r in members)
        covered = sum(1 for r in members if r.get("recent_ring"))
        cov = covered / n * 100

        reps = sorted(
            [r for r in members if r.get("recent_ring")],
            key=lambda r: (r.get("recent_ring_date") or "", r.get("id") or ""),
            reverse=True,
        )[:REP_N]
        rep_html = "".join(
            '<article class="mini"><header><b>%s</b><span>%s · %s</span></header>'
            '<p>%s</p><time>%s</time></article>'
            % (
                html.escape(str(r.get("name") or r.get("id") or "")),
                html.escape(str(r.get("id") or "")),
                html.escape(str(r.get("profession") or "")),
                html.escape(str(r.get("recent_ring") or "")),
                html.escape(str(r.get("recent_ring_date") or "")),
            )
            for r in reps
        ) or '<p class="empty">本区暂无带年轮居民</p>'

        sp_items = [(SPECIES_CN.get(k, k), v) for k, v in sp.most_common()]
        fac_items = [(FACTION_CN.get(k, k), v) for k, v in fac.most_common()]

        sections.append(
            """<section class="dist">
<h2>{title}<em>{code}</em><span class="pop">{n} 人 · 年轮覆盖 {cov:.0f}%</span></h2>
<div class="cols">
<div><h3>物种</h3>{sp_html}</div>
<div><h3>派系</h3>{fac_html}</div>
<div><h3>职业 · 前 {pl}</h3>{prof_html}</div>
<div><h3>街区 · 前 {bl}</h3>{blk_html}</div>
<div><h3>六轴 · 前 {al}</h3>{axis_html}</div>
</div>
<h3>代表居民（最近落笔）</h3>
<div class="minis">{rep_html}</div>
</section>""".format(
                title=html.escape(label.get(d, d)),
                code=html.escape(d),
                n=n,
                cov=cov,
                sp_html=bar(sp_items, n),
                fac_html=bar(fac_items, n),
                pl=PROF_TOP,
                prof_html=bar(prof.most_common(PROF_TOP), n),
                bl=BLOCK_TOP,
                blk_html=bar(blk.most_common(BLOCK_TOP), n),
                al=AXIS_TOP,
                axis_html=bar(axis.most_common(AXIS_TOP), n),
                rep_html=rep_html,
            )
        )

    feed = "".join(
        '<article class="card"><header><b>%s</b><span>%s · %s</span></header>'
        '<p>%s</p><time>%s</time></article>'
        % (
            html.escape(str(r.get("name") or r.get("id") or "")),
            html.escape(str(r.get("id") or "")),
            html.escape(label.get(r.get("district") or "", r.get("district") or "")),
            html.escape(str(r.get("recent_ring") or "")),
            html.escape(str(r.get("recent_ring_date") or "")),
        )
        for r in latest
    )

    gen_at = datetime.datetime.fromtimestamp(os.path.getmtime(SRC)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    cov_all = len(ring_rows) / total * 100 if total else 0
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城区志 · 硅基生命</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header.top{{padding:30px 22px 14px;border-bottom:1px solid var(--line)}}
header.top h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
main{{padding:18px 22px 70px;max-width:1080px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}}
.dist{{border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:5px;
background:#14181e;padding:14px 16px;margin:0 0 16px}}
.dist h2{{margin:0 0 10px;font-size:17px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}}
.dist h2 em{{font-style:normal;font:11px/1 ui-monospace,monospace;color:#6a7078}}
.dist h2 .pop{{margin-left:auto;font:12px/1 ui-monospace,monospace;color:#8b8f96}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px 18px}}
h3{{font-size:12.5px;color:#b3b0a8;margin:8px 0 6px;font-weight:600;letter-spacing:.04em}}
.row{{display:flex;align-items:center;gap:6px;font-size:12px;color:#b3b0a8;margin:2px 0}}
.lab{{flex:0 0 84px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.track{{flex:1;height:5px;background:#1c222a;border-radius:3px;overflow:hidden}}
.track i{{display:block;height:100%;background:linear-gradient(90deg,#c8a06a,#8a6a3f)}}
.num{{flex:0 0 74px;text-align:right;font:11px/1 ui-monospace,monospace;color:#7c8288}}
.minis{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.mini,.card{{background:#171c23;border:1px solid var(--line);border-radius:4px;padding:10px 12px}}
.mini header,.card header{{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:#8b8f96}}
.mini header b,.card header b{{color:#e6e3dc;font-size:13px}}
.mini p,.card p{{margin:6px 0 4px;font-size:12.5px;color:#b3b0a8;line-height:1.65}}
time{{font:11px/1 ui-monospace,monospace;color:#5f656d}}
.empty{{color:#6a7078;font-size:12px}}
footer{{padding:18px 22px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
</style></head><body>
<header class="top"><h1>城区志</h1>
<div class="sub">全城 {total} 人 · 年轮覆盖 {cov:.0f}% · 六城区逐区人口/职业/街区/六轴聚合 · 目录更新 {now}</div>
</header>
<main>
<h3>全城近 7 日年轮密度</h3>
<div class="cols"><div>{day_bars}</div></div>
{dists}
<h3>全城最近落笔</h3>
<div class="grid">{feed}</div>
</main>
<footer>本页由 Tools/build_district_chronicle.py 从 census/export/citizens-light.jsonl 确定性生成（零 LLM），
数据源 {src_at}；口径与城市看板同源。</footer>
</body></html>
""".format(
        total=total,
        cov=cov_all,
        now=now,
        day_bars=day_bars,
        dists="\n".join(sections),
        feed=feed,
        src_at=gen_at,
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(
        "district-chronicle: %s  %.1f KB  districts=%d  citizens=%d"
        % (
            os.path.relpath(OUT, ROOT),
            len(doc.encode("utf-8")) / 1024.0,
            len(sections),
            total,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())