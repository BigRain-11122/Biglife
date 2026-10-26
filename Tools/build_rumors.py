# -*- coding: utf-8 -*-
"""城市流言录生成器（确定性·零 LLM·幂等）。

把当天居民年轮当作「被人说出口的话」，交给 RUMOR-CHAIN v1.0 引擎
（Tools/rumor_chain.py 契约=cognition/RUMOR-CHAIN.md）在城区里经口耳相传，
产出 cognition/rumors/rumors-YYYY-MM-DD.jsonl 与 census/export/city-rumors.html。

与 city-today.html 的区别：日报是「谁在今天说了什么」，流言录是「同一句话
穿过几条街之后变成了什么」——城市的社会性在场证明。

用法: python -X utf8 Tools/build_rumors.py [--date YYYY-MM-DD] [--per-day 8]
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "Tools")
EVENTS = os.path.join(ROOT, "events")
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
OUT_DIR = os.path.join(ROOT, "cognition", "rumors")
OUT_HTML = os.path.join(ROOT, "census", "export", "city-rumors.html")

ANCHOR_TAIL = re.compile(r"\[锚\][^\n]*$")
OPS_CN = {"trunc": "掐头去尾", "fuzz": "数目模糊", "pad": "先垫一句", "noop": "原话照搬"}

sys.path.insert(0, TOOLS)
import rumor_chain as rc  # noqa: E402


def md5(*parts) -> str:
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def load_people():
    """id → (name, district)"""
    people = {}
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            cid = o.get("id")
            if cid:
                people[cid] = (o.get("name") or cid, o.get("district") or "")
    return people


def load_rings(day: str):
    """当天 ring 事件，按居民取最新一条（保持文件顺序，末条胜出）。"""
    path = os.path.join(EVENTS, day[:7] + ".jsonl")
    if not os.path.exists(path):
        return []
    seen = {}
    order = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "ring" or not str(o.get("ts", "")).startswith(day):
                continue
            payload = o.get("payload") or {}
            text = payload.get("text") or ""
            if not text.strip():
                continue
            cid = o.get("citizen")
            if not cid:
                continue
            if cid not in seen:
                order.append(cid)
            seen[cid] = (o.get("ts"), text)
    return [(cid, seen[cid][0], seen[cid][1]) for cid in order]


def pick(rings, people, per_day):
    """跨城区轮转抽样：每个城区轮流各取一条，全域铺开而非永远同一批人。"""
    buckets = {}
    for cid, ts, text in rings:
        d = people.get(cid, ("", ""))[1] or "未落区"
        buckets.setdefault(d, []).append((cid, ts, text))
    for d in buckets:
        buckets[d].sort(key=lambda r: md5("pick", r[0]))
    picked, keys = [], sorted(buckets)
    idx = 0
    while len(picked) < per_day and keys:
        alive = False
        for d in keys:
            if idx < len(buckets[d]):
                picked.append((d, buckets[d][idx]))
                alive = True
                if len(picked) >= per_day:
                    break
        if not alive:
            break
        idx += 1
    return picked


def clean_text(text: str) -> str:
    t = ANCHOR_TAIL.sub("", text).strip()
    t = t.strip("「」").strip()
    return t


def build(day: str, per_day: int):
    people = load_people()
    rc.CENSUS = rc.load_census()
    rings = load_rings(day)
    picked = pick(rings, people, per_day)
    base = datetime.datetime.strptime(day + " 00:00", "%Y-%m-%d %H:%M")
    out = []
    for district, (cid, ts, text) in picked:
        body = clean_text(text)
        if len(body) < 8:
            continue
        event_id = "RUMOR-%s-%s" % (day.replace("-", ""), cid)
        hops = 3 + rc.m_int(event_id, cid, "nhops") % 2  # 3 或 4 跳
        at = base + datetime.timedelta(hours=8, minutes=rc.m_int(event_id, cid, "min0") % 600)
        chain = rc.build_chain(event_id, body, cid, hops, 45, at)
        out.append({"day": day, "district": district, "origin": cid,
                    "origin_name": people.get(cid, (cid, ""))[0], "text": body,
                    "chain": chain})
    return out


def render(day: str, items, people) -> str:
    names = {cid: v[0] for cid, v in people.items()}
    rows = []
    for it in items:
        hops = it["chain"]["hops"]
        hop_html = []
        for h in hops:
            frm = names.get(h["from"], h["from"])
            to = names.get(h["to"], h["to"])
            hop_html.append(
                '<div class="hop"><div class="who">%s <span class="arw">→</span> %s'
                '<span class="op">%s</span><span class="tsx">%s</span></div>'
                '<div class="said">%s</div></div>'
                % (esc(frm), esc(to), esc(OPS_CN.get(h["op"], h["op"])),
                   esc(h["ts"][-5:]), esc(h["text"]))
            )
        rows.append(
            '<article class="card"><header><h3>%s</h3>'
            '<span class="meta">%s · 源自 %s · %d 跳</span></header>'
            '<div class="origin"><span class="lbl">最初说</span>%s</div>%s</article>'
            % (esc(it["district"] or "未落区"), esc(it["day"]),
               esc(it["origin_name"]), len(hops), esc(it["text"]), "".join(hop_html))
        )
    body = "".join(rows)
    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市流言录 · %(day)s · 硅基生命</title>
<style>
:root{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}
header.top{padding:30px 22px 14px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}
.sub{color:var(--dim);font-size:13px}
main{padding:18px 22px 70px;max-width:960px}
.card{background:#14181e;border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:5px;padding:14px 16px;margin:0 0 14px}
.card h3{margin:0;font-size:15px;color:#e6e3dc}
.meta{font:11px/1.6 ui-monospace,monospace;color:#6a7078}
.origin{color:#cfc9bd;font-size:14px;margin:8px 0 10px;padding-left:10px;border-left:1px solid #2c333c}
.lbl{display:inline-block;font:10px/1 ui-monospace,monospace;color:#7d838b;margin-right:8px}
.hop{padding:7px 0 7px 14px;border-left:1px dashed #2c333c}
.who{font:11.5px/1.6 ui-monospace,monospace;color:#8b8f96}
.arw{color:#c8a06a;margin:0 4px}
.op{color:#6a7078;margin-left:8px}
.tsx{color:#5f656d;margin-left:8px}
.said{color:#d8d3c8;font-size:14px}
footer{padding:18px 22px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}
</style></head><body>
<header class="top"><h1>城市流言录</h1>
<div class="sub">%(day)s · %(n)d 条话在城里走街串巷 · 确定性引擎 RUMOR-CHAIN v1.0（零 LLM）</div></header>
<main>%(body)s</main>
<footer>本页由 Tools/build_rumors.py 从 events/ 当日年轮生成；逐跳传播/延迟/失真全部由 md5 派生，同一日重跑逐字节一致。</footer>
</body></html>
""" % {"day": esc(day), "n": len(items), "body": body}


def main():
    ap = argparse.ArgumentParser(description="城市流言录生成器（确定性·零 LLM）")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD；缺省=今天")
    ap.add_argument("--per-day", type=int, default=8)
    args = ap.parse_args()
    day = args.date or datetime.date.today().isoformat()
    people = load_people()
    items = build(day, args.per_day)
    if not items:
        print("no rings for", day)
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    jl = os.path.join(OUT_DIR, "rumors-%s.jsonl" % day)
    with open(jl, "w", encoding="utf-8", newline="\n") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False, separators=(",", ":")) + "\n")
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(day, items, people))
    hops = sum(len(it["chain"]["hops"]) for it in items)
    print("chains=%d hops=%d jsonl=%s html=%s" % (len(items), hops, jl, OUT_HTML))


if __name__ == "__main__":
    main()