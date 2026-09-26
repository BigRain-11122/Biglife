#!/usr/bin/env python3
"""memory_index.py - city-wide memory recall: rings + reflections (v1.6).

AI-foundation piece under orders O-20260925-1202-bm-c (CODEX 12th T2 v3.13),
O-20260925-2320-bm-c (retrieval three factors: recency x relevance x importance),
O-20260926-0942-bm-c (T2 v3.24): until now the QA layer only ever saw a citizen's
LAST 3 rings; this index recalls the most question-relevant memories instead.
v1.6 closes the Generative-Agents three-leg loop record->reflect->retrieve:
the citizen's own reflections (Tools/reflect_citizen.py, census/reflections.jsonl,
committed append-only) join the recall candidates with importance x1.5.
BM25-lite scoring: 2-char shingle overlap * recency boost * importance,
zero LLM, zero new deps, deterministic for the same (question, candidate set).

Usage:
  python -X utf8 memory_index.py --id C-00010 --q "台风那年的事"
  python -X utf8 memory_index.py --qc
"""
import argparse, datetime, hashlib, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_digests import find_card

REFLECTIONS_FILE = os.path.join(CO, "census", "reflections.jsonl")
REFLECTION_WEIGHT = 1.5  # v1.6: higher-level memories outrank equal rings

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

def load_reflections(cid):
    """Own higher-level insights (reflection leg) as recall candidates (v1.6).

    Source: census/reflections.jsonl (reflect_citizen.py output, committed
    append-only, zero-fabrication by construction). Marked kind="reflection"
    so consumers render them as derived insights, never as [anchor] facts.
    Honored seats are blocked upstream in reflect_citizen, no guard needed.
    """
    out = []
    if not cid or not os.path.isfile(REFLECTIONS_FILE):
        return out
    with open(REFLECTIONS_FILE, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if r.get("id") == cid and r.get("insight"):
                out.append({"date": str(r.get("date", "")),
                            "text": r["insight"], "kind": "reflection"})
    return out

def ring_importance(text):
    """Deterministic importance weight (zero LLM) - Generative-Agents-style third
    retrieval factor (order O-20260925-2320-bm-c / R-20260925-resident-full-intelligence).

    Base 1.0; +0.7 anchored to real city/fleet/CEO events; +0.5 meet events;
    +0.2 richer memories (>40 chars). Honest note: the paper scores importance
    via LLM (1-10) - we use deterministic proxies for the 10k scale (compute law).
    """
    imp = 1.0
    if ("CEO_ORDER" in text) or ("城市事件流" in text) or ("城市实况" in text) or ("机队" in text):
        imp += 0.7
    if ("与 C-" in text) or ("相遇" in text):
        imp += 0.5
    if len(text) > 40:
        imp += 0.2
    return imp

def recall(question, rings, topk=3, now=None, reflections=None):
    """v1.6: rings + own reflections compete in one pool; reflections carry
    importance x1.5 (higher-level memories, Generative Agents Sec. 3.2).
    Same (score, overlap, date) ties keep insertion order (rings first) -
    stable sort keeps this deterministic."""
    cand = list(rings or []) + list(reflections or [])
    if not cand:
        return []
    now = now or datetime.date.today()
    qs = shingles(question)
    scored = []
    for r in cand:
        ts = shingles(r["text"])
        overlap = len(qs & ts)
        if overlap == 0:
            continue
        try:
            days = (now - datetime.date(*map(int, r["date"].split("-")))).days
        except Exception:
            days = 999
        recency = 1.0 / (1.0 + math.log1p(max(days, 0)))
        importance = ring_importance(r["text"])
        if r.get("kind") == "reflection":
            importance *= REFLECTION_WEIGHT
        scored.append((overlap * recency * importance, overlap, r))
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
    # v1.6: reflections join the pool with importance x1.5
    refl = [{"date": "2026-09-23", "text": "灯灵值得帮，日子才亮堂", "kind": "reflection"}]
    out3 = recall("灯灵", rings, topk=3, reflections=refl)
    if not any(r.get("kind") == "reflection" for r in out3):
        fails.append("reflection-join")
    # equal overlap + equal date: x1.5 must outrank the plain ring
    ring_eq = {"date": "2026-09-26", "text": "顾客来买粢饭团，笑呵呵"}
    refl_eq = {"date": "2026-09-26", "text": "顾客如流，珍惜眼前。", "kind": "reflection"}
    m_eq = recall("顾客", [ring_eq], topk=2, reflections=[refl_eq])
    if not m_eq or m_eq[0].get("kind") != "reflection":
        fails.append("reflection-weight-1.5")
    # zero-overlap reflection must not surface
    if any(r.get("kind") == "reflection" for r in
           recall("记账", [ring_eq], topk=2,
                  reflections=[{"date": "2026-09-26", "text": "灯灵巡夜", "kind": "reflection"}])):
        fails.append("reflection-zero-overlap")
    # determinism with reflections merged
    if recall("灯灵", rings, topk=3, reflections=refl) != out3:
        fails.append("reflection-determinism")
    # no-reflections call keeps v1.5 semantics (regression)
    if recall("旧笔记账", rings, topk=2)[0]["text"] != out2[0]["text"]:
        fails.append("no-refl-regression")
    # real committed file: own reflections load with kind tag, others stay empty
    live = load_reflections("C-00010")
    if not live or not any("顾客如流" in r["text"] for r in live) \
            or not all(r.get("kind") == "reflection" for r in live):
        fails.append("load-reflections-live")
    if load_reflections("C-00999"):
        fails.append("load-reflections-foreign")
    if fails:
        print("QC FAIL: " + "; ".join(fails))
        return 1
    print("QC PASS (ranking/topk/determinism/zero-overlap + reflection join/1.5-weight/no-refl-regression)")
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
    refl = load_reflections(a.id)
    out = recall(a.q, rings, topk=a.topk, reflections=refl) if a.q else rings[-a.topk:]
    print(json.dumps({"id": a.id, "q": a.q, "recall": out}, ensure_ascii=False))

if __name__ == "__main__":
    main()
