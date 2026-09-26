#!/usr/bin/env python3
"""agency.py - deterministic daily self-initiated actions (agency dimension v0).

Implements the #1 gap of the nine-dimension ladder (order O-20260926-0942-bm-c,
research R-20260925-resident-full-intelligence): GOAP-style need -> goal ->
daily initiative, fully deterministic (md5(id+date), zero LLM, zero cloud).

Complementary split (no overlap with the loop's behavior.py five rings):
behavior.py = WHERE a citizen is right now; agency = what they INTEND today.
Intentions are plans (legal per loop precedent C-0012-style intent lines),
never state claims about weather/time/celestial/sessions.

Inputs (R3 faces, auto-regenerated when missing): citizens-light.jsonl,
citizen-needs.jsonl (needs.py), citizen-persona.jsonl (persona_enrich.py).
Output: census/export/citizen-initiatives.jsonl (R3, gitignored).
Contract: cognition/AGENCY.md v1.0 (CODEX 12th section T2).

Usage: python -X utf8 agency.py [--date YYYY-MM-DD] [--qc]
"""
import argparse, datetime, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
EXPORT = os.path.join(CO, "census", "export")
LIGHT = os.path.join(EXPORT, "citizens-light.jsonl")
NEEDS = os.path.join(EXPORT, "citizen-needs.jsonl")
PERSONA = os.path.join(EXPORT, "citizen-persona.jsonl")
OUT = os.path.join(EXPORT, "citizen-initiatives.jsonl")

# need axis -> initiative templates (intentions only, styled later with persona)
POOLS = {
    "anwen": ["把{likes}翻出来理一理", "守着老地方，把家伙什再点一遍",
              "早点收档，把屋里的备件换一茬", "挑个安静的位子坐坐，把旧账捋顺"],
    "shengji": ["赶在开档前把料备足", "把今天的手艺活再过一遍",
                "去老主顾那儿回访一趟", "把摊面上的货色理出个新花样"],
    "shejiao": ["去广场听街坊聊一段", "给对门捎句自家的话",
                "约老熟人来摊前坐坐", "把攒的话头找个人讲讲"],
    "haoqi": ["绕路去看看城里新动的工", "翻两页档案馆的新档案",
              "找件新玩意琢磨一下午", "跟行家讨教一手新招"],
    "_recover": ["先把手头的活匀一匀，别赶", "找个老熟人说说话解解乏",
                 "把欠的觉好好补一补", "把心头的账找张纸捋一捋"],
}

def h32(cid, salt):
    return int(hashlib.md5((cid + "#" + salt).encode("utf-8")).hexdigest()[:10], 16)

def ensure_faces():
    """R3 contract: regenerate missing derived faces before use (~seconds)."""
    changed = []
    if not os.path.isfile(NEEDS):
        os.system('"' + sys.executable + '" -X utf8 "' + os.path.join(HERE, "needs.py") + '"')
        changed.append("needs")
    if not os.path.isfile(PERSONA):
        os.system('"' + sys.executable + '" -X utf8 "' + os.path.join(HERE, "persona_enrich.py") + '"')
        changed.append("persona")
    return changed

def load_jsonl(path, key="id"):
    out = {}
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            out[r.get(key)] = r
    return out

def style(text, persona, cid):
    """Light persona styling: occasionally prefix the sentence tic."""
    if persona and persona.get("tic") and h32(cid, "st") % 3 == 0:
        return persona["tic"] + "，" + text
    return text

def fill(text, persona):
    if "{likes}" in text:
        likes = (persona or {}).get("likes") or "老物件"
        text = text.replace("{likes}", likes)
    return text

def initiatives_for(cid, date, light, needs, persona):
    if light.get("faction") == "honored":
        return [], True
    n = (needs or {}).get("needs") or {}
    top = (needs or {}).get("top")
    crash = (needs or {}).get("crash")
    picks = []
    if crash:
        pool = POOLS["_recover"]
        idx = h32(cid + date, "rc") % len(pool)
        picks.append(fill(pool[idx], persona))
    else:
        axes = [a for a in ("anwen", "shengji", "shejiao", "haoqi") if n.get(a, 0) >= 1]
        if top and top in POOLS and n.get(top, 0) >= 1:
            pool = POOLS[top]
            idx = h32(cid + date, "p1") % len(pool)
            picks.append(fill(pool[idx], persona))
            axes = [a for a in axes if a != top]
            if axes and h32(cid + date, "p2") % 2 == 0:
                second = axes[h32(cid + date, "s2") % len(axes)]
                pool2 = POOLS[second]
                idx2 = h32(cid + date, "p3") % len(pool2)
                picks.append(fill(pool2[idx2], persona))
    if not picks:
        # zero-strength day: one gentle default keeps the ring alive
        pool = POOLS["anwen"]
        picks.append(fill(pool[h32(cid + date, "d") % len(pool)], persona))
    return [style(p, persona, cid) for p in picks], False

def build(date):
    ensure_faces()
    lights = load_jsonl(LIGHT)
    needs = load_jsonl(NEEDS)
    personas = load_jsonl(PERSONA)
    rows = []
    for cid, light in lights.items():
        inits, blocked = initiatives_for(cid, date, light, needs.get(cid), personas.get(cid))
        rows.append({"id": cid, "date": date, "top": (needs.get(cid) or {}).get("top"),
                     "crash": (needs.get(cid) or {}).get("crash"),
                     "initiatives": inits, "blocked": blocked})
    return rows

def dump(rows, date):
    path = OUT if not date else OUT
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

GATE_TOKENS = ["雨", "雪", "月", "星", "台风", "开盘", "收盘", "今早", "今晚", "今夜", "深夜"]

def qc(rows, date):
    fails = []
    if len(rows) != 10003:
        fails.append("rows=%d" % len(rows))
    blocked = [r for r in rows if r.get("blocked")]
    if len(blocked) != 3:
        fails.append("blocked=%d" % len(blocked))
    n_active = 0
    for r in rows:
        if r.get("blocked"):
            if r["initiatives"]:
                fails.append("blocked has initiatives %s" % r["id"])
            continue
        n_active += 1
        if not r.get("initiatives") or len(r["initiatives"]) > 2:
            fails.append("init count %s" % r["id"]); break
        for s in r["initiatives"]:
            if len(s) < 4 or len(s) > 36:
                fails.append("len %s" % r["id"]); break
            for tok in GATE_TOKENS:
                if tok in s:
                    fails.append("gate token '%s' at %s" % (tok, r["id"])); break
    rows2 = build(date)
    d1 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows]
    d2 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows2]
    if d1 != d2:
        fails.append("double-run drift")
    return fails, n_active

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    rows = build(a.date)
    dump(rows, a.date)
    n_act = sum(1 for r in rows if not r.get("blocked"))
    print("agency rows=%d active=%d date=%s -> %s" % (len(rows), n_act, a.date, OUT))
    if a.qc:
        fails, n_active = qc(rows, a.date)
        if fails:
            print("QC FAIL: " + "; ".join(fails[:6]))
            sys.exit(1)
        print("QC PASS (rows/blocked/1-2-inits/len/gate-tokens/double-run all green)")

if __name__ == "__main__":
    main()
