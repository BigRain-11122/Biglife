#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""needs.py - V2-A motivation layer (SILICON-LIFE.md life sign #8).

Deterministic need derivation for ALL citizens: city reality (weather /
real time / event types) x persona (axis/age/district/species) -> four need
intensities in [0,2]. Zero LLM, zero API. Output: census/export/
citizen-needs.jsonl (R3 regenerable face - gitignored, run on demand by
consumers: CityWatch v2 / M2 engine / OSLoop).
T-20260924-16d step 1: additive crash/crash_axis fields - pure-threshold
crash state per contract cognition/NEEDS-CRASH.md v1.0; honored seats
C-00001~03 stay crash=null (CEO persona-reserved face).
T-20260925-12: --tasks candidate task face - pure table lookup over the
live needs face (strength >= 1 -> one row per (citizen, axis), axis ->
asset-face mapping per D-20260925-11); output census/export/
citizen-tasks.jsonl (R3 regenerable face - gitignored).
Same (city snapshot, time bucket, persona) => byte-identical output.
Usage: python -X utf8 needs.py [--qc] [--tasks]
"""
import datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(CO, "census", "export", "citizen-needs.jsonl")
TASKS_OUT = os.path.join(CO, "census", "export", "citizen-tasks.jsonl")  # T-20260925-12 R3 face
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))

NEED_KEYS = ["anwen", "shengji", "shejiao", "haoqi"]  # 安稳/生计/社交/好奇

# T-20260925-12 (D-20260925-11 unlock; R-20260924-bl-value-system table
# row 1): axis -> asset face for candidate task derivation. 安稳->履历盘点 /
# 生计->台词产出 / 社交->问候演出 / 好奇->讲师候选.
AXIS_FACE = {"anwen": "ledger", "shengji": "lines", "shejiao": "greet",
             "haoqi": "lecturer"}

# T-20260924-16d (contract cognition/NEEDS-CRASH.md v1.0): crash thresholds,
# all parameterized - CEO can retune with one line (engine recalibrates by
# measured distribution, recorded in task log).
CRASH_T = 2.0    # crash: axis at top band with no registry satisfaction this round
RECOVER_T = 1.5  # recovering: high axis newly satisfied by a registry hit
HONORED_IDS = {"C-00001", "C-00002", "C-00003"}  # CEO reserved seats: crash always null

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

def crash_state(r, needs, satisfied):
    """T-20260924-16d contract §一: pure-threshold crash derivation, zero LLM.
    crash = axis >= CRASH_T with no registry satisfaction this round;
    recovering = axis >= RECOVER_T with registry satisfaction this round;
    honored seats C-00001~03 stay null (persona-reserved face). Ties resolve
    by (value desc, NEED_KEYS order) - deterministic."""
    if str(r.get("id")) in HONORED_IDS:
        return None, None
    hot = [(needs[k], -NEED_KEYS.index(k), k) for k in NEED_KEYS
           if needs[k] >= CRASH_T and k not in satisfied]
    if hot:
        return "crash", max(hot)[2]
    warm = [(needs[k], -NEED_KEYS.index(k), k) for k in NEED_KEYS
            if needs[k] >= RECOVER_T and k in satisfied]
    if warm:
        return "recovering", max(warm)[2]
    return None, None

def derive_full(r, sig, hb, reg_rows=()):
    """Deterministic per-citizen needs + crash state. hb = hour bucket (0-7, 3h slots).
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
    satisfied = set()
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
                if int(v) > 0:
                    satisfied.add(k)
    needs = {k: cap2(v) for k, v in needs.items()}
    top = max(NEED_KEYS, key=lambda k: (needs[k], -NEED_KEYS.index(k))) if max(needs.values()) > 0 else "anwen"
    crash, crash_axis = crash_state(r, needs, satisfied)
    return needs, top, crash, crash_axis

def derive(r, sig, hb, reg_rows=()):
    """Legacy 2-tuple face; behavior.py L204 imports this - signature frozen
    (T-20260924-16d keeps the needs vector semantics byte-identical)."""
    n, top, _crash, _axis = derive_full(r, sig, hb, reg_rows)
    return n, top

def hb_slot_hour(hb):
    return hb * 3 + 1  # representative hour of the 3h bucket

def generate_needs(sig, hb):
    """Write the needs face (extracted from main so --tasks can regenerate a
    missing face first; behavior identical to the previous inline block)."""
    reg_rows = load_registry()
    with open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    out = []
    for r in rows:
        nv, top, crash, crash_axis = derive_full(r, sig, hb, reg_rows)
        out.append({"id": r["id"], "needs": nv, "top": top,
                    "crash": crash, "crash_axis": crash_axis, "v": 1,
                    "ctx": "hb=%d,wx=%s,ev=%d,wd=%d" % (hb, sig["weather"] or "na",
                                                        len(sig["events"]), sig["now"].weekday())})
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")


def write_tasks_face():
    """T-20260925-12: candidate task face - pure table lookup over the live
    needs face, zero LLM. One row per (citizen, axis) with strength >= 1;
    id ascending, NEED_KEYS order within a citizen - deterministic double
    run byte-identical. Honored seats derive by the same rule (data
    derivation only; the CEO persona-reserved face is never written here)."""
    out = []
    n_in = 0
    bad = 0
    with open(OUT, encoding="utf-8") as f:
        for l in f:
            if not l.strip():
                continue
            n_in += 1
            try:
                o = json.loads(l)
            except Exception:
                bad += 1
                continue
            cid = str(o.get("id") or "")
            nv = o.get("needs") or {}
            if not cid or set(nv.keys()) != set(NEED_KEYS):
                bad += 1
                continue
            for k in NEED_KEYS:
                v = nv.get(k)
                if isinstance(v, int) and 1 <= v <= 2:
                    out.append({"id": cid, "axis": k, "face": AXIS_FACE[k],
                                "strength": v})
    out.sort(key=lambda t: (t["id"], NEED_KEYS.index(t["axis"])))
    with open(TASKS_OUT, "w", encoding="utf-8", newline="\n") as f:
        for t in out:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return n_in, bad, len(out)


def main():
    qc_only = "--qc" in sys.argv
    tasks_mode = "--tasks" in sys.argv
    sig = city_signals()
    hb = sig["now"].hour // 3
    # T-20260925-12: --tasks reads the live needs face; regenerate it first
    # only when missing (R3 contract). Plain runs keep regenerating as before.
    if not qc_only and not (tasks_mode and os.path.exists(OUT)):
        generate_needs(sig, hb)
    tasks_stats = write_tasks_face() if tasks_mode else None
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
            bad += 1; continue
        c, ca = o.get("crash"), o.get("crash_axis")
        if c not in (None, "crash", "recovering"):
            bad += 1; continue
        if (c is None) != (ca is None) or (ca is not None and ca not in NEED_KEYS):
            bad += 1; continue
        if o.get("id") in HONORED_IDS and c is not None:
            bad += 1; continue
    ncrash = sum(1 for o in rows if o.get("crash") == "crash")
    nrec = sum(1 for o in rows if o.get("crash") == "recovering")
    print(f"rows={len(rows)} bad={bad} ctx_hb={hb} weather={sig['weather'] or 'na'} "
          f"events={sorted(sig['events'])[:6]} crash={ncrash} recovering={nrec}")
    if tasks_stats is not None:
        n_in, bad_t, n_tasks = tasks_stats
        print(f"tasks face: in={n_in} bad_tasks={bad_t} tasks={n_tasks} "
              f"out={os.path.basename(TASKS_OUT)}")
        sys.exit(1 if (bad or len(rows) != 10003 or bad_t or n_in != 10003) else 0)
    # export face is 10003 rows since v1.9 honored seats C-00001~03 joined
    sys.exit(1 if (bad or len(rows) != 10003) else 0)

if __name__ == "__main__":
    main()
