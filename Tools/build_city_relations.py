# -*- coding: utf-8 -*-
"""城市人情志生成器（确定性·零 LLM·幂等）

读 census/export/citizen-relations.jsonl + citizens-light.jsonl，
产出 census/export/city-relations.html：关系类型分布 / 关系来源 / 枢纽居民 /
城区互往 / 相逢录（recent_ring 含「相遇」者）。
关系边体量大（百万级），逐行手工切分解析，避免 json.loads 开销。

用法: python -X utf8 Tools/build_city_relations.py
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
REL = os.path.join(EXP, "citizen-relations.jsonl")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-relations.html")

REL_CN = {
    "block": "同业",
    "buddy": "伙伴",
    "household": "同户",
    "friend": "朋友",
    "family": "亲属",
    "neighbor": "邻里",
    "rival": "竞争",
    "teacher": "师徒",
    "customer": "常客",
}
DISTRICT_CN = {
    "GM": "中央市集 GM",
    "QT": "低语巷 QT",
    "MD": "机房区 MD",
    "NS": "北槐街区 NS",
    "OR": "旧站台 OR",
    "RV": "河岸 RV",
}
HUB_N = 12
MEET_N = 30


def parse_edge(line):
    """快速解析一行关系边；结构异常回退 json。"""
    parts = line.split('","')
    if len(parts) == 4 and parts[0].startswith('{"a":"') and parts[1].startswith('b":"'):
        a = parts[0][6:]
        b = parts[1][4:]
        rel = parts[2][6:] if parts[2].startswith('rel":"') else None
        src = parts[3][6:-2] if parts[3].startswith('src":"') else None
        if rel is not None and src is not None and parts[3].endswith('"}'):
            return a, b, rel, src
    try:
        d = json.loads(line)
        return d["a"], d["b"], d.get("rel", ""), d.get("src", "")
    except Exception:
        return None


def load_light():
    info = {}
    meets = []
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cid = d.get("id", "")
            ring = (d.get("recent_ring") or "").strip()
            info[cid] = {
                "name": d.get("name", cid),
                "district": DISTRICT_CN.get(d.get("district") or "", d.get("district") or "") or "—",
                "profession": d.get("profession", "") or "",
                "ring": ring,
                "date": d.get("recent_ring_date", "") or "",
            }
            if "相遇" in ring:
                meets.append(cid)
    return info, meets


def bar(items, total):
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


def card(title, cnt, note=""):
    return (
        '<div class="card"><div class="k">%s</div>'
        '<div class="v">%s</div><div class="n">%s</div></div>'
        % (html.escape(title), html.escape(str(cnt)), html.escape(note))
    )


def hub_line(cid, deg, info):
    p = info.get(cid, {})
    name = p.get("name", cid)
    dist = p.get("district", "—")
    prof = p.get("profession", "")
    ring = (p.get("ring") or "")[:64]
    extra = " · ".join(x for x in (prof, ring) if x)
    return (
        '<li><b>%s</b><span class="d">%s</span><span class="x">%s · 度 %d</span></li>'
        % (html.escape(name), html.escape(dist), html.escape(extra), deg)
    )


def meet_line(cid, info):
    p = info.get(cid, {})
    return (
        '<li><b>%s</b><span class="d">%s</span><span class="x">%s　<span class="t">%s</span></span></li>'
        % (
            html.escape(p.get("name", cid)),
            html.escape(p.get("district", "—")),
            html.escape((p.get("ring") or "")[:160]),
            html.escape(p.get("date", "")),
        )
    )


def main():
    info, meet_ids = load_light()

    rel_cnt = collections.Counter()
    src_cnt = collections.Counter()
    degree = collections.Counter()
    pair_cnt = collections.Counter()
    edges = 0
    unparsed = 0
    nodes = set()

    with open(REL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            e = parse_edge(line)
            if e is None:
                unparsed += 1
                continue
            a, b, rel, src = e
            edges += 1
            rel_cnt[rel] += 1
            src_cnt[src] += 1
            degree[a] += 1
            degree[b] += 1
            nodes.add(a)
            nodes.add(b)
            da = info.get(a, {}).get("district", "")
            db = info.get(b, {}).get("district", "")
            if da and db:
                pair_cnt[(da, db)] += 1

    total_deg = sum(degree.values())
    avg_deg = (total_deg / len(degree)) if degree else 0
    hubs = degree.most_common(HUB_N)
    rel_top = [(REL_CN.get(k, k or "未标注"), c) for k, c in rel_cnt.most_common(12)]
    pair_top = [("%s ↔ %s" % (a, b), c) for (a, b), c in pair_cnt.most_common(12)]

    meet_ids.sort(key=lambda c: info.get(c, {}).get("date", ""), reverse=True)
    meet_rows = meet_ids[:MEET_N]
    meet_total = len(meet_ids)

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市人情志 · 硅基城市</title>
<style>
:root{{--bg:#0f1216;--fg:#e8ecf1;--dim:#8b97a6;--line:#232a33;--acc:#c9a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 "Microsoft YaHei",system-ui,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-size:26px;margin:0 0 6px}}
.sub{{color:var(--dim);font-size:13px;margin-bottom:24px}}
h2{{font-size:17px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.card{{background:#151a21;border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.card .k{{color:var(--dim);font-size:12px}}
.card .v{{font-size:24px;font-weight:600;margin:4px 0 2px}}
.card .n{{color:var(--dim);font-size:12px}}
.row{{display:flex;align-items:center;gap:10px;margin:6px 0}}
.lab{{width:190px;flex:none;color:#c9d4e0;font-size:13px}}
.track{{flex:1;height:8px;background:#1c232c;border-radius:5px;overflow:hidden}}
.track i{{display:block;height:100%;background:linear-gradient(90deg,#8d7248,#c9a06a)}}
.num{{width:104px;flex:none;text-align:right;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}}
ul{{margin:0;padding-left:0;list-style:none}}
li{{display:flex;gap:12px;padding:6px 0;border-top:1px solid #1b222b;font-size:13px}}
li:first-child{{border-top:0}}
li b{{width:150px;flex:none;font-weight:500}}
li .d{{width:110px;flex:none;color:var(--dim)}}
li .x{{color:#a9b6c4}}
li .t{{color:#5f6b7a;font:11px/1 ui-monospace,monospace;margin-left:6px}}
.note{{background:#1a1712;border:1px solid #3a3020;border-radius:10px;padding:14px 16px;color:#c9bb9f;font-size:13px}}
.note b{{color:var(--acc)}}
.foot{{margin-top:40px;color:#5f6b7a;font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>城市人情志</h1>
<div class="sub">人怎么彼此连着 · 生成 {now} · 数据源 census/export/citizen-relations.jsonl + citizens-light.jsonl</div>

<div class="cards">
{card("关系边", edges, "每条边=一次明确的两人关系")}
{card("涉及居民", len(nodes), "关系网覆盖人数")}
{card("人均度", "%.1f" % avg_deg, "一人平均连着几条边")}
{card("相逢记录", meet_total, "cap 内最近 %d 条取自年轮" % MEET_N)}
</div>

<h2>一 · 关系类型</h2>
{bar(rel_top, total_deg)}
<div class="sub" style="margin-top:10px">未标注类型 {rel_cnt.get("", 0) + rel_cnt.get("None", 0)} 条，按原值保留在数据面，不在此页归并。</div>

<h2>二 · 关系从哪里来</h2>
{bar(src_cnt.most_common(10), edges)}

<h2>三 · 十二位枢纽居民</h2>
<div class="sub">按边数排序的社交重心；被引用最多的人不是最有名的人，只是被最多关系穿过的人。</div>
<ul>
{"".join(hub_line(c, d, info) for c, d in hubs)}
</ul>

<h2>四 · 城区互往</h2>
<div class="sub">两端都登记了城区的边，按城区对聚合（含同区内部边）；空城区已排除。</div>
{bar(pair_top, sum(pair_cnt.values())) if pair_top else '<div class="sub">暂无可用城区对。</div>'}

<h2>五 · 相逢录</h2>
<div class="sub">年轮里留下「相遇」事件记录的最近 {len(meet_rows)} 位（共 {meet_total} 位），是双卡互引那一类事件的可见面。</div>
<ul>
{"".join(meet_line(c, info) for c in meet_rows) if meet_rows else '<li><span class="x">本段暂无记录。</span></li>'}
</ul>

<h2>六 · 读法说明</h2>
<div class="note">
<p><b>边数是结构，不是感情。</b>关系边来自对话广场等生成来源，一个度数高的居民首先意味着「被写进了更多关系记录」。</p>
<p>关系类型与来源均按数据面原值归类，未做近义合并；未标注类型如实计数。</p>
<p>相逢录只取 census 导出档的最近一条年轮（recent_ring），不是全部历史。</p>
</div>

<div class="foot">BigLife · 城市人情志 · 确定性生成（零 LLM） · 全部数据 offline 内嵌</div>
</div></body></html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    kb = os.path.getsize(OUT) / 1024
    print("city-relations: %s  %.1f KB  edges=%d nodes=%d rel=%d src=%d pairs=%d meets=%d unparsed=%d"
          % (os.path.relpath(OUT, ROOT), kb, edges, len(nodes), len(rel_cnt), len(src_cnt),
             len(pair_cnt), meet_total, unparsed))
    print("checks: page<300KB=%s  unparsed_rate<0.1%%=%s"
          % (kb < 300, (unparsed / edges * 100 if edges else 0) < 0.1))


if __name__ == "__main__":
    main()