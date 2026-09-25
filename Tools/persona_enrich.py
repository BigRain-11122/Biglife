#!/usr/bin/env python3
"""persona_enrich.py - persona v2 enrichment face (four-faces depth, zero->one).

Deterministic per-citizen deepening derived from the census CARDS (read-only)
plus the persona-v2 gene pools: trait expression lines, habits, likes/dislikes,
modal-particle print (language personality), address terms, sentence tics and
a signature seed line. Cards are never touched (2KB soft cap intact) - depth
lives in the export face census/export/citizen-persona.jsonl (R3, gitignored).

md5(id) banding, no python hash(), double-run byte-identical (QC built in).
Honored seats C-00001~03 are blocked (CEO persona-reserved, never derived).
Contract: cognition/PERSONA-v2.md v1.0 (CODEX 12th section T2 v3.12).

Usage: python -X utf8 persona_enrich.py [--qc]
"""
import argparse, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_digests import find_card, grab

LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
GENES = os.path.join(CO, "genes", "persona-v2.json")
OUT = os.path.join(CO, "census", "export", "citizen-persona.jsonl")
HONORED = {"C-00001", "C-00002", "C-00003"}

def h32(cid, salt):
    return int(hashlib.md5((cid + "#" + salt).encode("utf-8")).hexdigest()[:10], 16)

def pick(cid, salt, seq):
    return seq[h32(cid, salt) % len(seq)]

def load_genes():
    with open(GENES, encoding="utf-8") as f:
        return json.load(f)

def parse_traits(personality_line):
    # "手痒（...） · 清旧账（...）" -> [("手痒","..."), ...]
    out = []
    for part in re.split(r"\s*·\s*", personality_line):
        m = re.match(r"([^\s（(·]+)[（(](.*?)[）)]\s*$", part.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
        elif part.strip():
            out.append((part.strip(), ""))
    return out

def trait_expr(cid, traits, genes):
    fam = genes["trait_expr_families"]
    lines = []
    for i, (name, elab) in enumerate(traits[:3]):
        pool = None
        for key, arr in fam.items():
            if key in name or name in key:
                pool = arr
                break
        if pool is None:
            pool = genes["trait_expr_generic"]
        pick_i = h32(cid, "te%d" % i) % len(pool)
        lines.append({"trait": name, "expr": pool[pick_i]})
    return lines

def parse_lang(line, species):
    # returns (dialect_key, signature_token) - catchphrase chain:
    # 口头禅 -> 行话 -> first quoted token -> "" (creed fallback in seed)
    sig = ""
    for pat in (r"口头禅「(.*?)」", r"行话「(.*?)」", r"「(.*?)」"):
        m = re.search(pat, line)
        if m and m.group(1).strip():
            sig = m.group(1).strip()
            break
    if species == "silicon":
        return "silicon", sig
    if species == "sprite":
        return "sprite", sig
    key = "_fallback"
    for k in ("上海话", "吴侬软语", "川渝腔", "北方话", "粤语底色", "南方普通话", "netizen"):
        if k in line:
            key = k
            break
    return key, sig

def seed_line(cid, sig, creed, addr, tic, closer, genes):
    base = sig or ("「%s」" % creed[:20] if creed else "")
    if not base:
        return ""
    w = pick(cid, "sw", genes["seed_wrappers"])
    s = (w.replace("{catch}", base).replace("{addr}", addr)
          .replace("{tic}", tic).replace("{closer}", closer))
    return re.sub(r"[，。]{2,}", "。", s).strip()

def derive(row, genes):
    cid = row["id"]
    if row.get("faction") == "honored":
        return {"id": cid, "name": row.get("name", ""), "blocked": True}, None
    p = find_card(cid, row.get("district"))
    card = ""
    if p:
        with open(p, encoding="utf-8") as f:
            card = f.read()
    pline = grab(card, "性格")
    lline = grab(card, "语言")
    traits = parse_traits(pline) or []
    texpr = trait_expr(cid, traits, genes)
    habit = pick(cid, "hb", genes["habits"]) if genes["habits"] else ""
    habits = [habit]
    if h32(cid, "hb2") % 3 == 0 and len(genes["habits"]) > 1:
        h2 = pick(cid, "hb2", genes["habits"])
        if h2 != habit:
            habits.append(h2)
    like = pick(cid, "lk", genes["likes"]) if genes["likes"] else ""
    dislike = pick(cid, "dk", genes["dislikes"]) if genes["dislikes"] else ""
    dialect, sig = parse_lang(lline, row.get("species") or "carbon")
    mpart = pick(cid, "mp", genes["modal_particles"].get(dialect) or genes["modal_particles"]["_fallback"])
    addr = pick(cid, "ad", genes["address_terms"]) if genes["address_terms"] else ""
    tic = pick(cid, "tc", genes["sentence_tics"]["openers"]) if genes.get("sentence_tics") else ""
    closer = pick(cid, "cl", genes["sentence_tics"]["closers"]) if genes.get("sentence_tics") else ""
    creed = grab(card, "信条").strip("「」。 ")
    seed = seed_line(cid, sig, creed, addr, tic, closer, genes)
    return {
        "id": cid, "name": row.get("name", ""), "species": row.get("species"),
        "gender": row.get("gender"), "age": row.get("age"),
        "district": row.get("district"), "axis": row.get("axis"),
        "traits": [t[0] for t in traits][:3],
        "trait_expr": texpr, "habits": habits,
        "likes": like, "dislikes": dislike,
        "dialect": dialect, "modal": mpart, "address": addr,
        "tic": tic, "closer": closer, "seed_line": seed,
        "v": 2, "blocked": False,
    }, None

def build():
    genes = load_genes()
    rows, bad, blocked = [], 0, 0
    with open(LIGHT, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                d, _ = derive(r, genes)
                rows.append(d)
                if d.get("blocked"):
                    blocked += 1
            except Exception:
                bad += 1
    return rows, bad, blocked

def dump(rows):
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

def qc(rows, bad, blocked):
    fails = []
    if bad:
        fails.append("bad=%d" % bad)
    if len(rows) != 10003:
        fails.append("rows=%d" % len(rows))
    if blocked != 3:
        fails.append("blocked=%d" % blocked)
    n_active = 0
    for r in rows:
        if r.get("blocked"):
            continue
        n_active += 1
        for k in ("trait_expr", "habits", "likes", "dislikes", "modal", "address", "seed_line"):
            if not r.get(k):
                fails.append("empty %s at %s" % (k, r["id"]))
                break
    rows2, bad2, bl2 = build()
    d1 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows]
    d2 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows2]
    if d1 != d2:
        fails.append("double-run drift")
    if bad2 != bad or bl2 != blocked:
        fails.append("double-run meta drift")
    return fails, n_active

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    rows, bad, blocked = build()
    dump(rows)
    print("persona v2 rows=%d bad=%d blocked=%d -> %s" % (len(rows), bad, blocked, OUT))
    if a.qc:
        fails, n_active = qc(rows, bad, blocked)
        if fails:
            print("QC FAIL: " + "; ".join(fails))
            sys.exit(1)
        print("QC PASS (rows/blocked/fields-nonempty/double-run all green; active=%d)" % n_active)

if __name__ == "__main__":
    main()
