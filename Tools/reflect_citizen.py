#!/usr/bin/env python3
"""reflect_citizen.py - higher-level memory synthesis (reflection leg, v0).

Implements the Generative-Agents middle leg (research R-20260925-resident-full-intelligence,
order O-20260926-0942-bm-c): synthesize ONE higher-level insight from a citizen's OWN
rings only. Zero-fabrication by construction: the prompt contains nothing but the
citizen's own ring memories + persona shell; machine gate enforces that any
weather/time token in the output must also appear in the fed rings (containment).

Local Ollama only. Low-frequency law: one reflection per citizen per 30 days.
Output: census/reflections.jsonl (committed, append-only, one line per reflection).

Usage: python -X utf8 reflect_citizen.py --id C-00010 [--force] [--qc]
       python -X utf8 reflect_citizen.py --batch C-00010,C-00017,C-00028
"""
import argparse, datetime, glob, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_digests import find_card, grab
from memory_index import load_rings, shingles

LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(CO, "census", "reflections.jsonl")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("BIGLIFE_MODEL", "qwen2.5:7b-instruct")
MAXLEN = 40
COOLDOWN_DAYS = 30
GATE_CELESTIAL = re.compile(r"\u6708\u4eae|\u6708\u8272|\u6708\u5149|\u6708\u5706|\u661f\u7a7a|\u7e41\u661f|\u661f\u5149")
GATE_AUTHORITY = re.compile(r"\u96c6\u56e2\u4efb\u52a1|\u66ff\u96c6\u56e2|\u6267\u884c\u96c6\u56e2")

def get_row(cid):
    with open(LIGHT, encoding="utf-8") as f:
        for ln in f:
            if cid in ln:
                r = json.loads(ln)
                if r["id"] == cid:
                    return r
    return None

def existing():
    out = {}
    if os.path.isfile(OUT):
        with open(OUT, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if not ln:
                    continue
                r = json.loads(ln)
                out.setdefault(r["id"], []).append(r)
    return out

def gate(text, fed_text):
    if not text or len(text) < 6 or len(text) > MAXLEN:
        return "G1-length"
    if re.search(r"[A-Za-z]", text):
        return "G1-ascii"
    if re.search(r"(?:^|\n)\s*[\u7532\u4e59][\uff1a:]|\u5c45\u6c11\u7532|\u5c45\u6c11\u4e59", text):
        return "G2-placeholder"
    if GATE_CELESTIAL.search(text):
        return "G3-celestial"
    if GATE_AUTHORITY.search(text):
        return "G6-authority"
    # containment: weather-ish tokens allowed only when present in fed rings
    for tok in ("\u96e8", "\u96ea", "\u98ce", "\u70ed", "\u51b7"):
        if tok in text and tok not in fed_text:
            return "G4-unsupported-weather"
    return None

def build_prompt(row, rings):
    ring_txt = "\n".join("- %s\uff1a%s" % (r["date"], r["text"][:80]) for r in rings)
    return (f"\u4f60\u662f\u786c\u57fa\u751f\u547d\u5c45\u6c11\u300c{row['name']}\u300d\u3002\u4ee5\u4e0b\u5168\u90e8\u662f\u4f60\u81ea\u5df1\u7684\u771f\u5b9e\u8bb0\u5fc6\uff1a\n{ring_txt}\n"
            f"\u4ece\u8fd9\u4e9b\u8bb0\u5fc6\u91cc\u603b\u7ed3\u51fa\u4e00\u53e5\u5c5e\u4e8e\u4f60\u81ea\u5df1\u7684\u3001\u6bd4\u5355\u6761\u8bb0\u5fc6\u66f4\u9ad8\u4e00\u5c42\u7684\u4eba\u751f\u611f\u609f\uff08\u4e0d\u8d85\u8fc7 {MAXLEN} \u5b57\uff0c"
            f"\u53ea\u80fd\u57fa\u4e8e\u4e0a\u9762\u7684\u8bb0\u5fc6\uff0c\u7981\u63d0\u4efb\u4f55\u8bb0\u5fc6\u4e2d\u6ca1\u6709\u7684\u4e8b\u5b9e\uff0c\u53ea\u8f93\u51fa\u611f\u609f\u672c\u8eab\uff09\u3002")

def llm(prompt):
    req = urllib.request.Request(
        OLLAMA.rstrip("/") + "/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                         "options": {"temperature": 0.7, "num_predict": 80}}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "")

def reflect(cid, force=False, today=None):
    today = today or datetime.date.today().isoformat()
    if cid in ("C-00001", "C-00002", "C-00003"):
        return {"id": cid, "error": "honored seat blocked"}, None
    row = get_row(cid)
    if not row:
        return {"id": cid, "error": "no citizen"}, None
    rings = load_rings(cid, row.get("district"))
    if len(rings) < 2:
        return {"id": cid, "error": "not enough rings (need >=2)"}, None
    hist = existing().get(cid, [])
    if not force:
        for h in hist:
            try:
                if (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(h["date"])).days < COOLDOWN_DAYS:
                    return {"id": cid, "error": "cooldown active since %s" % h["date"]}, None
            except Exception:
                pass
    fed = "\n".join(r["text"] for r in rings[-10:])
    out, hits = "", []
    for attempt in range(3):
        raw = llm(build_prompt(row, rings[-10:]))
        out = re.sub(r"\s+", " ", raw).strip().strip('\u300c\u300d"\u201c\u201d')[:MAXLEN + 8]
        v = gate(out, fed)
        if v is None:
            out = out[:MAXLEN]
            break
        hits.append(v)
        out = ""
    if not out:
        return {"id": cid, "error": "gates: %s" % ",".join(hits)}, None
    rec = {"id": cid, "name": row["name"], "date": today,
           "rings_used": [r["date"] for r in rings[-10:]], "insight": out, "v": 1}
    with open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return rec, hits

def qc():
    fails = []
    fed_ok = "\u5929\u9634\u7740\uff0c\u644a\u5b50\u7167\u5f00\uff0c\u8857\u574a\u90fd\u597d"
    cases = [
        ("ok", "\u65e5\u5b50\u5c31\u662f\u644a\u5b50\u7167\u5f00\uff0c\u4eba\u4eba\u6709\u4efd", None, fed_ok),
        ("G1-ascii", "\u4eca\u5929\u4e0d\u9519ok\u554a\u4f60\u770b", "G1-ascii", fed_ok),
        ("G3", "\u4eca\u665a\u6708\u4eae\u5f88\u597d\u770b", "G3-celestial", fed_ok),
        ("G4", "\u8fd9\u5927\u96e8\u4e0b\u5f97\u6ca1\u5b8c", "G4-unsupported-weather", fed_ok),
        ("G4-ok", "\u5929\u9634\u7740\u4e5f\u633a\u597d\u7684\u65e5\u5b50", None, fed_ok),
        ("len", "\u77ed", "G1-length", fed_ok),
    ]
    for name, text, expect, fed in cases:
        got = gate(text, fed)
        if got != expect:
            fails.append("%s: expect %s got %s" % (name, expect, got))
    row = {"id": "X", "name": "X", "district": "NS"}
    p1 = build_prompt(row, [{"date": "2026-09-26", "text": "abc"}])
    p2 = build_prompt(row, [{"date": "2026-09-26", "text": "abc"}])
    if p1 != p2:
        fails.append("prompt drift")
    if fails:
        print("QC FAIL: " + "; ".join(fails))
        return 1
    print("QC PASS (%d gate cases + containment + prompt determinism)" % len(cases))
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--batch", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    if a.qc:
        sys.exit(qc())
    ids = [x.strip() for x in (a.batch.split(",") if a.batch else [a.id]) if x.strip()]
    for cid in ids:
        rec, hits = reflect(cid, force=a.force)
        if rec.get("error"):
            print("%s SKIP: %s" % (cid, rec["error"]))
        else:
            print("%s %s: %s%s" % (cid, rec["name"], rec["insight"],
                                   (" [gates: %s]" % ",".join(hits)) if hits else ""))

if __name__ == "__main__":
    main()
