#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""needs.py - V2-A motivation layer (SILICON-LIFE.md life sign #8).

Deterministic need derivation for ALL citizens: city reality (weather /
real time / event types) x persona (axis/age/district/species) -> four need
intensities in [0,2]. Zero LLM, zero API. Output: census/export/
citizen-needs.jsonl (R3 regenerable face - gitignored, run on demand by
consumers: CityWatch v2 / M2 engine / OSLoop).
Same (city snapshot, time bucket, persona) => byte-identical output.
Usage: python -X utf8 needs.py [--qc]
"""
import datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(CO, "census", "export", "citizen-needs.jsonl")
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))

NEED_KEYS = ["anwen", "shengji", "shejiao", "haoqi"]  # 安稳/生计/社交/好奇

REGISTRY = os.path.join(CO, "cognition", "fact-needs-registry.json")

def load_registry():
    """T-20260924-16a: fact-source -> need mappings live in the registry file;
    new city fact sources register rows there, zero changes to this script."""
    try:
        with open(REGISTRY, encoding="utf-8") as f:
            return json.load(f).get("rows") or []
    except Exception:
        return []

def city_signals():
    sig = {"weather": "", "wind": None, "events": set(), "now": datetime.datetime.now()}
    try:
        with open(os.path.join(FV_WORLD, "world-state.json"), encoding="utf-8") as f:
            st = json.load(f)
        r = st.get("reality") or st
        sig["weather"] = str(r.get("weather_kind") or "")
        w = r.get("weather") or {}
        wtext = " ".join(str(x) for x in (w.get("temperature"), w.get("desc")) if x)
        m = re.search(r"(-?\d+(?:\.\d+)?)", wtext or str(r.get("weather_temp_c") or ""))
        if m:
            sig["wind"] = None
        wtext2 = str(r.get("weather_wind_ms") or w.get("wind") or "")
        m2 = re.search(r"(-?\d+(?:\.\d+)?)", wtext2)
        if m2:
            sig["wind"] = float(m2.group(1))
    except Exception:
        pass
    files = sorted(glob.glob(os.path.join(FV_WORLD, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if files:
        try:
            with open(files[0], encoding="utf-8", errors="replace") as f:
                for ln in f.readlines()[-40:]:
                    try:
                        e = json.loads(ln)
                    except Exception:
                        continue
                    t = str(e.get("type", ""))
                    if t:
                        sig["events"].add(t)
        except Exception:
            pass
    return sig

def cap2(x):
    return max(0, min(2, int(x)))

def derive(r, sig, hb, reg_rows=()):
    """Deterministic per-citizen needs. hb = hour bucket (0-7, 3h slots).
    Persona/time base rules below; all fact-sourced adjustments (weather /
    event types / event density) come from the registry lookup so new fact
    sources need zero changes here (T-20260924-16a)."""
    sp = r.get("species")           # carbon / silicon / sprite
    ax = r.get("axis") or ""        # thought axis (may be None for anchors)
    age = r.get("age") or 0
    d = r.get("district") or ""
    weather = sig["weather"]
    ev = sig["events"]
    weekend = sig["now"].weekday() >= 5

    # 安稳 safety: elderly feel it more (persona base)
    an = 0
    if sp == "carbon" and isinstance(age, int) and age >= 60:
        an += 1
    # 生计 livelihood: daytime working hours (time base)
    sj = 0
    if 6 <= sig["now"].hour < 19 and not weekend:
        sj += 1
    # 社交 social: weekend & evenings lift adults (time base)
    sh = 0
    if weekend:
        sh += 1
    if 17 <= hb_slot_hour(hb) < 23 and sp != "sprite":
        sh += 1
    # 好奇 curiosity: 求新 axis, sprites and the young (persona base)
    qi = 0
    if ax == "求新":
        qi += 1
    if sp == "sprite":
        qi += 1
    if sp == "carbon" and isinstance(age, int) and age <= 17:
        qi += 1
    needs = {"anwen": an, "shengji": sj, "shejiao": sh, "haoqi": qi}
    for row in reg_rows:
        fact = str(row.get("fact", ""))
        args = row.get("args") or {}
        if fact == "event:any_of":
            if not (set(args.get("of") or []) & ev):
                continue
        elif fact == "meta:event_types_ge":
            if len(ev) < int(args.get("min", 5)):
                continue
        elif fact.startswith("event:"):
            if fact[6:] not in ev:
                continue
        elif fact.startswith("weather:"):
            if fact != "weather:" + weather:
                continue
        else:
            continue
        if row.get("species") and row.get("species") != sp:
            continue
        if row.get("district") and row.get("district") != d:
            continue
        for k, v in (row.get("needs") or {}).items():
            if k in needs:
                needs[k] += int(v)
    needs = {k: cap2(v) for k, v in needs.items()}
    top = max(NEED_KEYS, key=lambda k: (needs[k], -NEED_KEYS.index(k))) if max(needs.values()) > 0 else "anwen"
    return needs, top

def hb_slot_hour(hb):
    return hb * 3 + 1  # representative hour of the 3h bucket

def main():
    qc_only = "--qc" in sys.argv
    sig = city_signals()
    hb = sig["now"].hour // 3
    if not qc_only:
        reg_rows = load_registry()
        with open(LIGHT, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        out = []
        for r in rows:
            needs, top = derive(r, sig, hb, reg_rows)
            out.append({"id": r["id"], "needs": needs, "top": top, "v": 1,
                        "ctx": "hb=%d,wx=%s,ev=%d,wd=%d" % (hb, sig["weather"] or "na",
                                                            len(sig["events"]), sig["now"].weekday())})
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            for o in out:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
    # QC pass (always)
    bad = 0
    with open(OUT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    for o in rows:
        nk = o.get("needs") or {}
        if set(nk.keys()) != set(NEED_KEYS):
            bad += 1; continue
        if any((not isinstance(v, int)) or v < 0 or v > 2 for v in nk.values()):
            bad += 1; continue
        if o.get("top") not in NEED_KEYS:
            bad += 1
    print(f"rows={len(rows)} bad={bad} ctx_hb={hb} weather={sig['weather'] or 'na'} "
          f"events={sorted(sig['events'])[:6]}")
    # export face is 10003 rows since v1.9 honored seats C-00001~03 joined
    sys.exit(1 if (bad or len(rows) != 10003) else 0)

if __name__ == "__main__":
    main()
