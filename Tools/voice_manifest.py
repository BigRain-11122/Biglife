#!/usr/bin/env python3
"""voice_manifest.py - deterministic per-citizen voice params (four-faces voice line).

Mirror of atlas_manifest.py law: md5(id) derivation, no python hash(), species/
age/gender banding, byte-identical double runs. Output census/export/citizen-voice.jsonl
is an R3 regenerable face (gitignored) - consumers regenerate before use (~seconds).

Honored seats (C-00001~03) are emitted with blocked=true (CEO persona-reserved).

Contract: cognition/VOICE-POOL.md v1.0 (CODEX 12th section T2 v3.9).
Usage: python -X utf8 voice_manifest.py [--qc]
"""
import argparse, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(CO, "census", "export", "citizen-voice.jsonl")
BASE_VOICE = "sapi-huihui-zh-CN"

# (pitch_lo, pitch_hi, rate_lo, rate_hi) - bands per contract section 1.
BANDS = {
    ("carbon", "m"): {"minor": (5, 8, 10, 20), "youth": (0, 4, 0, 10),
                      "mid": (-4, 0, -5, 5), "elder": (-8, -5, -15, -5)},
    ("carbon", "f"): {"minor": (8, 10, 10, 25), "youth": (3, 7, 0, 10),
                      "mid": (0, 4, -5, 5), "elder": (-3, 1, -15, -5)},
    ("silicon", "m"): {"all": (-10, -6, -5, 5)},
    ("silicon", "x"): {"all": (-4, 0, -5, 5)},
    ("sprite", "x"): {"all": (7, 10, 10, 25)},
}

def age_band(age):
    # light rows may carry age as int or as "42 岁" style strings
    if age is None:
        return None
    m = re.findall(r"\d+", str(age))
    if not m:
        return None
    a = int(m[0])
    if a < 18: return "minor"
    if a < 40: return "youth"
    if a < 60: return "mid"
    return "elder"

def pick(h, lo, hi):
    span = hi - lo
    return lo if span <= 0 else lo + (h % (span + 1))

def voice_for(row):
    cid = row["id"]
    if row.get("faction") == "honored":
        return {"base": BASE_VOICE, "pitch": 0, "rate": 0, "vol": 100}, True
    sp = row.get("species") or "carbon"
    g = (row.get("gender") or "")
    gk = "m" if g.startswith("\u7537") else ("f" if g.startswith("\u5973") else "x")
    band = age_band(row.get("age"))
    key = (sp, gk)
    tbl = BANDS.get(key)
    if tbl is None and (sp, "x") in BANDS:
        tbl = BANDS[(sp, "x")]
    if tbl is None:
        tbl = BANDS[("carbon", gk if gk != "x" else "f")]
    slot = band if (band and band in tbl) else next(iter(tbl))
    p_lo, p_hi, r_lo, r_hi = tbl[slot]
    h = int(hashlib.md5(cid.encode("utf-8")).hexdigest()[:12], 16)
    pitch = pick(h % 9973, p_lo, p_hi)
    rate = pick((h >> 13) % 9973, r_lo, r_hi)
    vol = pick((h >> 23) % 9973, 80, 100)
    return {"base": BASE_VOICE, "pitch": pitch, "rate": rate, "vol": vol}, False

def build():
    rows, bad = [], 0
    with open(LIGHT, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                v, blocked = voice_for(r)
                rows.append({"id": r["id"], "name": r.get("name", ""),
                             "species": r.get("species"), "gender": r.get("gender"),
                             "age": r.get("age"), "district": r.get("district"),
                             "voice": v, "blocked": blocked})
            except Exception:
                bad += 1
    return rows, bad

def dump(rows, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

def qc(rows, bad):
    fails = []
    if bad: fails.append("bad_light_rows=%d" % bad)
    if len(rows) != 10003: fails.append("rows=%d" % len(rows))
    blocked = [r for r in rows if r["blocked"]]
    if len(blocked) != 3: fails.append("blocked=%d" % len(blocked))
    for r in rows:
        if r["blocked"]:
            continue
        v = r["voice"]
        if not (-10 <= v["pitch"] <= 10): fails.append("pitch out %s" % r["id"]); break
        if not (-15 <= v["rate"] <= 25): fails.append("rate out %s" % r["id"]); break
        if not (80 <= v["vol"] <= 100): fails.append("vol out %s" % r["id"]); break
    ids = {r["id"] for r in rows}
    if len(ids) != len(rows): fails.append("dup ids")
    # determinism: rebuild and compare byte-identical
    rows2, bad2 = build()
    d1 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows]
    d2 = [json.dumps(r, ensure_ascii=False, separators=(",", ":")) for r in rows2]
    if d1 != d2: fails.append("double-run drift")
    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    rows, bad = build()
    dump(rows, OUT)
    print("voice manifest rows=%d bad=%d blocked=%d -> %s" %
          (len(rows), bad, sum(1 for r in rows if r["blocked"]), OUT))
    if a.qc:
        fails = qc(rows, bad)
        if fails:
            print("QC FAIL: " + "; ".join(fails)); sys.exit(1)
        print("QC PASS (rows/bands/blocked/dup/double-run all green)")

if __name__ == "__main__":
    main()
