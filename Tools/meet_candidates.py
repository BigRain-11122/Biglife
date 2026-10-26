# -*- coding: utf-8 -*-
"""相遇候选单（确定性·零 LLM·幂等）

T-20261026-03：相遇维度是全库最薄面（78/10,111）。本工具在夜窗相遇轮开工前
先把「该让谁和谁遇见」算清楚，夜里只做 GenerativeAI 那一步：
  - 读 census/export/citizens-light.jsonl（户籍：城区/街区/年轮/六轴/物种）
  - 读 census/registry/*/*.md 相遇行（既有相遇对，源自 build_city_meets.load_cards）
  - 只在同城区、双方都已长过年轮、且从未相遇的人之间选对
  - 街区同源优先（同一街区更可能撞见），年轮越新越靠前，六轴/物种互补加分
  - 每人最多进一对（候选单是一份可照单开工的队列，不是同一批人反复配对）

产出：
  1) census/export/meet-candidates.jsonl —— top N 对（含打分与一行理由）
  2) census/export/meet-candidates.html —— 同一批候选的可见页面

确定性：不含墙上时钟，as_of 取数据内最大年轮日；同输入双跑逐字节一致。

用法: python -X utf8 Tools/meet_candidates.py [--top 60]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
SRC = os.path.join(EXP, "citizens-light.jsonl")
OUT_JSONL = os.path.join(EXP, "meet-candidates.jsonl")
OUT_HTML = os.path.join(EXP, "meet-candidates.html")

sys.path.insert(0, os.path.join(ROOT, "Tools"))
from build_city_meets import DISTRICT_CN, load_cards  # noqa: E402

BLOCK_WINDOW = 12  # 每街区只取最近活跃的 N 人参与配对枚举（控组合爆炸）
W_SAME_BLOCK = 40
W_AXIS_DIFF = 12
W_SPECIES_DIFF = 6
W_HOOK = 4
W_RECENT_MAX = 30


def esc(s):
    return html.escape(str(s), quote=True)


def load_rows():
    rows = []
    with open(SRC, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def existing_pairs(meets):
    """既有相遇对（不分日期，双向归一）——候选对不得与之重复。"""
    pairs = set()
    for _date, a, b, _text in meets:
        if a != b:
            pairs.add(tuple(sorted((a, b))))
    return pairs


def eligible(rows):
    """可进入相遇轮的人：有城区、有年轮、非荣誉席（T0 人设权 CEO 保留面）。"""
    out = []
    for r in rows:
        if not r.get("district") or not r.get("recent_ring"):
            continue
        if r.get("faction") == "honored" or r.get("anchor"):
            continue
        out.append(r)
    return out


def date_of(r):
    d = (r.get("recent_ring_date") or "").strip()
    try:
        return datetime.date.fromisoformat(d)
    except ValueError:
        return None


def pair_score(a, b, as_of):
    """确定性打分：街区同源 > 年轮新鲜度 > 六轴互补 > 物种互补 > 钩子物。"""
    score = 0
    bits = []
    if a.get("block") and a.get("block") == b.get("block"):
        score += W_SAME_BLOCK
        bits.append("同街区")
    fresh = []
    for r in (a, b):
        d = date_of(r)
        fresh.append(W_RECENT_MAX if d is None else max(0, W_RECENT_MAX - 2 * (as_of - d).days))
    score += fresh[0] + fresh[1]
    ax = (a.get("axis"), b.get("axis"))
    if ax[0] and ax[1] and ax[0] != ax[1]:
        score += W_AXIS_DIFF
        bits.append("六轴互补 %s×%s" % ax)
    elif ax[0] and ax[0] == ax[1]:
        bits.append("同轴 %s" % ax[0])
    sp = (a.get("species"), b.get("species"))
    if sp[0] and sp[1] and sp[0] != sp[1]:
        score += W_SPECIES_DIFF
        bits.append("物种互补 %s×%s" % sp)
    elif sp[0] and sp[0] == sp[1]:
        bits.append("同物种 %s" % sp[0])
    if a.get("hook") and b.get("hook"):
        score += W_HOOK
        bits.append("双方各有钩子物件")
    return score, bits


def build_candidates(rows, met, top):
    people = eligible(rows)
    as_of = max((date_of(r) for r in people if date_of(r)), default=None)
    if as_of is None:
        return [], as_of, people

    by_block = collections.defaultdict(list)
    for r in people:
        by_block[(r["district"], r.get("block") or "")].append(r)

    pool = []
    for key, members in by_block.items():
        members = sorted(members, key=lambda r: (-(date_of(r) or as_of).toordinal(), r["id"]))[:BLOCK_WINDOW]
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                pair = tuple(sorted((a["id"], b["id"])))
                if pair in met:
                    continue
                score, bits = pair_score(a, b, as_of)
                pool.append((-score, pair[0], pair[1], a, b, bits))

    pool.sort(key=lambda t: (t[0], t[1], t[2]))

    picked = []
    used = set()
    for neg, _ia, _ib, a, b, bits in pool:
        if len(picked) >= top:
            break
        if a["id"] in used or b["id"] in used:
            continue
        used.add(a["id"])
        used.add(b["id"])
        picked.append({
            "rank": len(picked) + 1,
            "pair": [a["id"], b["id"]],
            "names": [a.get("name") or a["id"], b.get("name") or b["id"]],
            "district": a["district"],
            "district_cn": DISTRICT_CN.get(a["district"], a["district"]),
            "block": a.get("block") or b.get("block") or "",
            "axis": [a.get("axis"), b.get("axis")],
            "species": [a.get("species"), b.get("species")],
            "ring_dates": [(a.get("recent_ring_date") or ""), (b.get("recent_ring_date") or "")],
            "score": -neg,
            "why": "同属 %s%s；双方年轮最近 %s / %s；%s；尚未相遇" % (
                DISTRICT_CN.get(a["district"], a["district"]),
                ("·" + (a.get("block") or "")) if a.get("block") else "",
                a.get("recent_ring_date") or "—",
                b.get("recent_ring_date") or "—",
                "、".join(bits) if bits else "同城区活跃居民",
            ),
            "as_of": as_of.isoformat(),
        })
    return picked, as_of, people


def write_jsonl(picked):
    tmp = OUT_JSONL + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for c in picked:
            fh.write(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n")
    os.replace(tmp, OUT_JSONL)


def bars(rows):
    if not rows:
        return ""
    mx = max(n for _k, n in rows) or 1
    out = []
    for label, n in rows:
        pct = 100.0 * n / mx
        out.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i style="width:%.1f%%"></i></span>'
            '<span class="num">%d</span></div>' % (esc(label), pct, n)
        )
    return "\n".join(out)


STYLE = """
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
.row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}
.lab{flex:0 0 150px;color:var(--fg)}
.track{flex:1;height:8px;background:#161b22;border-radius:4px;overflow:hidden}
.track i{display:block;height:100%;background:linear-gradient(90deg,#3d7dd6,#63b3ff);border-radius:4px}
.num{flex:0 0 90px;text-align:right;color:var(--dim);font-variant-numeric:tabular-nums}
ol.cands{list-style:none;padding:0;margin:0;counter-reset:c}
ol.cands li{counter-increment:c;background:#161b22;border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-bottom:10px}
ol.cands li::before{content:counter(c,decimal-leading-zero);color:var(--acc);font-variant-numeric:tabular-nums;margin-right:10px;font-size:12px}
.who{font-weight:600}
.tag{font-size:11px;color:var(--dim);border:1px solid var(--line);border-radius:999px;padding:1px 8px;margin-left:8px}
.why{color:var(--dim);font-size:12.5px;margin:6px 0 0}
.sc{float:right;color:var(--warm);font-size:12px}
footer{color:var(--dim);font-size:12px;border-top:1px solid var(--line);padding-top:14px}
"""


def write_html(picked, as_of, scope, met_n):
    per_dist = collections.Counter(c["district"] for c in picked)
    dist_rows = [(DISTRICT_CN.get(k, k), n) for k, n in sorted(per_dist.items(), key=lambda kv: (-kv[1], kv[0]))]
    items = []
    for c in picked:
        items.append(
            '<li><span class="sc">%d 分</span>'
            '<div class="who">%s <span class="tag">%s</span> × %s <span class="tag">%s</span>'
            '<span class="tag">%s</span></div>'
            '<p class="why">%s</p></li>' % (
                c["score"],
                esc(c["names"][0]), esc(c["pair"][0]),
                esc(c["names"][1]), esc(c["pair"][1]),
                esc(c["district_cn"] + ("·" + c["block"] if c["block"] else "")),
                esc(c["why"]),
            )
        )
    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>相遇候选单 · 今晚该让谁遇见谁</title>
<style>%s</style></head><body><div class="wrap">
<h1>相遇候选单</h1>
<p class="sub">数据截至 %s · 同城区 + 双方已有年轮 + 从未相遇 · 每人最多进一对（确定性选人，零 LLM）</p>
<div class="kpis">
<div class="kpi"><b>%d</b><span>候选对（可按序开工）</span></div>
<div class="kpi"><b>%d</b><span>可配对居民池</span></div>
<div class="kpi"><b>%d</b><span>全库已有相遇对</span></div>
<div class="kpi"><b>%d</b><span>覆盖城区</span></div>
</div>
<section><h2>候选分城区</h2>
%s
</section>
<section><h2>候选队列（按分排序）</h2>
<ol class="cands">
%s
</ol>
</section>
<footer>机器清单：census/export/meet-candidates.jsonl · 生成器：Tools/meet_candidates.py（同一输入双跑逐字节一致）</footer>
</div></body></html>
""" % (STYLE, esc(as_of.isoformat()), len(picked), scope, met_n, len(per_dist),
       bars(dist_rows), "\n".join(items))
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=60)
    args = ap.parse_args()

    rows = load_rows()
    _people, meets = load_cards()
    met = existing_pairs(meets)
    picked, as_of, pool = build_candidates(rows, met, args.top)
    if not picked:
        print("NO-CANDIDATES")
        return 0

    write_jsonl(picked)
    write_html(picked, as_of, len(pool), len(met))
    per_dist = collections.Counter(c["district"] for c in picked)
    print("pairs=%d pool=%d met=%d as_of=%s districts=%s" % (
        len(picked), len(pool), len(met), as_of.isoformat(),
        ",".join("%s:%d" % (k, n) for k, n in sorted(per_dist.items()))))
    print("top1 %s %s + %s %s" % (
        picked[0]["pair"][0], picked[0]["names"][0], picked[0]["pair"][1], picked[0]["names"][1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())