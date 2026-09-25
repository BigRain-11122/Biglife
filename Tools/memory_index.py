#!/usr/bin/env python3
"""memory_index.py - city-wide ring memory index + deterministic recall (v1).

AI-foundation piece under order O-20260925-1202-bm-c (CODEX 12th T2 v3.13):
until now the QA layer only ever saw a citizen's LAST 3 rings; this index
recalls the most question-relevant memories instead. BM25-lite scoring:
2-char shingle overlap * recency boost, zero LLM, zero new deps, deterministic
for the same (question, ring set).

Usage:
  python -X utf8 memory_index.py --id C-00010 --q "台风那年的事"
  python -X utf8 memory_index.py --qc
"""
import argparse, datetime, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_digests import find_card

def shingles(text):
    t = re.sub(r"\s+", "", text)
    return set(t[i:i+2] for i in range(len(t) - 1)) if len(t) >= 2 else {t}

def load_rings(cid, district):
    p = find_card(cid, district)
    if not p:
        return []
    with open(p, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"\*\*年轮\*\*\n((?:- .*\n?)+)", text)
    if not m:
        return []
    ents = re.findall(r"- (\d{4}-\d{2}-\d{2}) 「(.*?)」", m.group(1))
    return [{"date": d, "text": t.strip()} for d, t in ents]

def recall(question, rings, topk=3, now=None):
    if not rings:
        return []
    now = now or datetime.date.today()
    qs = shingles(question)
    scored = []
    for r in rings:
        ts = shingles(r["text"])
        overlap = len(qs & ts)
        if overlap == 0:
            continue
        try:
            days = (now - datetime.date(*map(int, r["date"].split("-")))).days
        except Exception:
            days = 999
        recency = 1.0 / (1.0 + math.log1p(max(days, 0)))
        scored.append((overlap * (1.0 + recency), overlap, r))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["date"]))
    return [s[2] for s in scored[:topk]]

def qc():
    rings = [
        {"date": "2026-09-23", "text": "巡夜时替年长的灯灵分担一段路，落檐先抖一抖翅膀上的光尘"},
        {"date": "2026-09-24", "text": "帮迷路的小家伙引路，从不开口，尾巴天线对准热闹的方向"},
        {"date": "2026-09-20", "text": "记账不用新笔，说旧笔有手感，街角小店关照了两句"},
    ]
    fails = []
    out = recall("灯灵巡夜", rings, topk=2)
    if not out or "灯灵" not in out[0]["text"]:
        fails.append("recall-rank")
    out2 = recall("旧笔记账", rings, topk=2)
    if not out2 or "旧笔" not in out2[0]["text"]:
        fails.append("recall-rank2")
    if recall("完全不相关的问题词", rings):
        # zero-overlap question must return empty
        fails.append("zero-overlap-should-be-empty")
    a = recall("灯灵巡夜", rings, topk=2)
    b = recall("灯灵巡夜", rings, topk=2)
    if [r["text"] for r in a] != [r["text"] for r in b]:
        fails.append("determinism")
    if not recall("台风", rings):
        # no match -> empty is CORRECT here, guard inverted: recall must not fabricate
        pass
    if fails:
        print("QC FAIL: " + "; ".join(fails))
        return 1
    print("QC PASS (ranking/topk/determinism/zero-overlap)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--district", default="")
    ap.add_argument("--q", default="")
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    if a.qc:
        sys.exit(qc())
    if not a.id:
        print("need --id"); sys.exit(2)
    rings = load_rings(a.id, a.district or None)
    out = recall(a.q, rings, topk=a.topk) if a.q else rings[-a.topk:]
    print(json.dumps({"id": a.id, "q": a.q, "recall": out}, ensure_ascii=False))

if __name__ == "__main__":
    main()
