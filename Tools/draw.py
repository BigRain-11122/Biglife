#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""draw.py - deterministic bark draw (cognition layer 2, zero LLM).

Same (citizen id, date, context) => byte-identical line, forever.
Contexts are ACTIVATED ONLY BY REAL DATA (cognition/README fact gate):
--auto derives context from FluxVerse world-state (read-only): real events
take precedence over weather over time-of-day. Pools carry no facts; facts
enter only via the real gate that selects the context bucket.
Usage:
  python -X utf8 draw.py --ids C-00010,C-00045 --context morning
  python -X utf8 draw.py --ids C-00071 --auto
  python -X utf8 draw.py --demo-auto   # one random citizen per district
"""
import argparse, datetime, glob, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
POOL = os.path.join(CO, "cognition", "pools.json")
GREET = os.path.join(CO, "cognition", "greetings.json")
GKEYS = ["first_meet", "reunion", "smalltalk", "farewell"]
NEG = os.path.join(CO, "cognition", "pools-negative.json")
NEEDS_FACE = os.path.join(CO, "census", "export", "citizen-needs.jsonl")
# T-20260924-16d step 3 (contract cognition/NEEDS-CRASH.md sec.2.3): negative
# speech face. crash -> negative bucket, recovering -> recovery bucket;
# non-crash routing unchanged. Law-8.3 caps mirror behavior.py truncation
# (city CITY_CAP, then district CRASH_CAP, overflow by (strength, hash)).
CRASH_AXES = ("anwen", "shengji", "shejiao", "haoqi")
CRASH_CAP = 0.05   # same-district visible crash residents (speech face)
CITY_CAP = 0.03    # whole-city crash population
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))

CONTEXTS = ["morning", "dusk", "night", "weekend", "rain", "typhoon",
            "heatwave", "coldsnap", "market_open", "market_close", "ceo_order", "festival"]

def load_rows():
    rows = {}
    with open(LIGHT, encoding="utf-8") as f:
        for l in f:
            if not l.strip(): continue
            r = json.loads(l)
            rows[r["id"]] = r
    return rows

def derive_context():
    """Fact gate: real events > real weather > real time-of-day."""
    ctx = None
    src = "time"
    ws = os.path.join(FV_WORLD, "world-state.json")
    now = datetime.datetime.now()
    hour = now.hour
    kind = ""
    try:
        if os.path.isfile(ws):
            with open(ws, encoding="utf-8") as f:
                st = json.load(f)
            r = st.get("reality") or {}
            kind = str(r.get("weather_kind") or "")
    except Exception:
        pass
    # events take precedence
    ev = os.path.join(FV_WORLD, "world-events.jsonl")
    try:
        if os.path.isfile(ev):
            with open(ev, encoding="utf-8") as f:
                lines = [l for l in f.readlines() if l.strip()][-15:]
            types = set()
            for l in lines:
                try:
                    e = json.loads(l)
                    types.add(str(e.get("type", "")))
                except Exception:
                    pass
            if "CEO_ORDER" in types: ctx, src = "ceo_order", "event"
            elif "MARKET_OPEN" in types: ctx, src = "market_open", "event"
            elif "MARKET_CLOSE" in types: ctx, src = "market_close", "event"
            elif "WEATHER_ALERT" in types: ctx, src = "typhoon", "event"
    except Exception:
        pass
    # weather
    if not ctx:
        if kind in ("rain", "storm", "drizzle", "shower"): ctx, src = "rain", "weather"
        elif kind in ("snow", "sleet"): ctx, src = "coldsnap", "weather"
        elif kind in ("typhoon", "gale", "wind"): ctx, src = "typhoon", "weather"
    # time of day
    if not ctx:
        if 5 <= hour < 11: ctx = "morning"
        elif 17 <= hour < 19: ctx = "dusk"
        elif hour >= 19 or hour < 5: ctx = "night"
        else: ctx = "morning" if hour < 15 else "dusk"
        src = "clock"
    # weekend overlay when no stronger signal
    if src == "clock" and now.weekday() >= 5 and ctx in ("morning", "dusk", "night"):
        ctx, src = "weekend", "clock"
    return ctx, src

def draw_line(cid, ctx, pools, rows, date=None, slot=None):
    date = date or datetime.date.today().isoformat()
    r = rows.get(cid)
    if not r: return None
    if r.get("species") == "sprite":
        bucket = pools.get("sprite", {}).get(ctx) or []
    else:
        axis = r.get("axis") or "烟火"
        bucket = pools.get("axes", {}).get(axis, {}).get(ctx) or []
        if not bucket:
            bucket = pools.get("axes", {}).get("烟火", {}).get(ctx) or []
    if not bucket: return None
    key = cid + "|" + date + "|" + ctx if slot is None else cid + "|" + date + "|s" + str(slot) + "|" + ctx
    seed = hashlib.md5(key.encode("utf-8")).hexdigest()
    return bucket[int(seed[:8], 16) % len(bucket)]

def load_greetings():
    with open(GREET, encoding="utf-8") as f:
        return json.load(f)

def greet_line(cid, gkey, greets, rows, date=None):
    """Same (id, date, gkey) => byte-identical greet (GREETINGS.md sec.4)."""
    date = date or datetime.date.today().isoformat()
    r = rows.get(cid)
    if not r: return None
    if r.get("species") == "sprite":
        bucket = greets.get("greet", {}).get("sprite", {}).get(gkey) or []
    else:
        axis = r.get("axis") or "烟火"
        bucket = greets.get("greet", {}).get("axes", {}).get(axis, {}).get(gkey) or []
        if not bucket:
            bucket = greets.get("greet", {}).get("axes", {}).get("烟火", {}).get(gkey) or []
    if not bucket: return None
    seed = hashlib.md5((cid + "|" + date + "|greet|" + gkey).encode("utf-8")).hexdigest()
    return bucket[int(seed[:8], 16) % len(bucket)]

def faq_pair(cid, greets, rows, date=None):
    """Same (id, date) => byte-identical faq pair (GREETINGS.md sec.4)."""
    date = date or datetime.date.today().isoformat()
    r = rows.get(cid)
    if not r: return None
    fam = "sprite" if r.get("species") == "sprite" else (r.get("axis") or "烟火")
    bucket = greets.get("faq", {}).get(fam) or greets.get("faq", {}).get("烟火") or []
    if not bucket: return None
    seed = hashlib.md5((cid + "|" + date + "|faq").encode("utf-8")).hexdigest()
    return bucket[int(seed[:8], 16) % len(bucket)]

def _shash(s):
    # stable hash (python hash() is process-randomized - behavior.py same law)
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:8], 16)

def load_crash(rows):
    """Needs-face crash state (R3 regen face; missing -> regen via needs.py,
    behavior.py precedent). Returns {id: (crash, crash_axis, strength)}."""
    if not os.path.isfile(NEEDS_FACE):
        try:
            import subprocess
            subprocess.run([sys.executable, "-X", "utf8",
                           os.path.join(HERE, "needs.py")],
                          check=True, capture_output=True, timeout=180)
        except Exception:
            pass
    face = {}
    if not os.path.isfile(NEEDS_FACE):
        return face
    with open(NEEDS_FACE, encoding="utf-8") as f:
        for l in f:
            if not l.strip(): continue
            d = json.loads(l)
            c, ax = d.get("crash"), d.get("crash_axis")
            if c in ("crash", "recovering") and ax in CRASH_AXES:
                face[str(d.get("id"))] = (c, ax, float((d.get("needs") or {}).get(ax) or 0))
    return face

def neg_visible_plan(rows, face):
    """Law-8.3 speech-face truncation (pure): ids whose crash state stays
    visible on the speech face. City CITY_CAP first, then per-district
    CRASH_CAP; overflow truncated by (axis strength desc, hash(id)) -
    truncated crash residents fall back to the normal pools so both faces
    stay density-consistent. Honored seats excluded (needs.py same law)."""
    cands = [(cid, ax, st) for cid, (c, ax, st) in face.items()
             if c == "crash" and cid in rows
             and cid not in ("C-00001", "C-00002", "C-00003")]
    if not cands:
        return set()
    kmax = int(CITY_CAP * len(rows))
    if len(cands) > kmax:
        cands = sorted(cands, key=lambda t: (-t[2], _shash(t[0])))[:kmax]
    dist_pop = {}
    for r in rows.values():
        d = r.get("district") or "?"
        dist_pop[d] = dist_pop.get(d, 0) + 1
    vis_by_d = {}
    for cid, ax, st in cands:
        d = rows[cid].get("district") or "?"
        vis_by_d.setdefault(d, []).append((-st, _shash(cid), cid))
    ok = set()
    for d, lst in vis_by_d.items():
        lst.sort()
        ok.update(x[2] for x in lst[:int(CRASH_CAP * dist_pop.get(d, 0))])
    return ok

def neg_line(cid, neg, face, plan_ok, rows, date=None, slot=None):
    """T-16d crash/recovering speech routing (NEEDS-CRASH.md sec.2.3).
    Returns (line, tag) or None -> caller falls back to the normal pools.
    Law-8.3 slot cooldown: adjacent slots never both draw the negative /
    recovery face (parity of the slot ordinal - standard tier = 45-min
    slot index, barks tier = day-of-year); same (id, slot) => same line."""
    ent = face.get(cid)
    if not ent: return None
    c, ax, _st = ent
    r = rows.get(cid)
    if not r: return None
    date = date or datetime.date.today().isoformat()
    ordinal = slot if slot is not None else datetime.date.fromisoformat(date).timetuple().tm_yday
    if ordinal % 2: return None
    if c == "crash":
        if cid not in plan_ok: return None
        fam = "sprite" if r.get("species") == "sprite" else ax
        bucket = (neg.get("negative") or {}).get(fam) or []
        tag = "neg:" + fam
    else:
        bucket = neg.get("recovering") or []
        tag = "recovering"
    if not bucket: return None
    key = cid + "|" + date + ("|s" + str(slot) if slot is not None else "") + "|" + tag
    seed = hashlib.md5(key.encode("utf-8")).hexdigest()
    return bucket[int(seed[:8], 16) % len(bucket)], tag

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="")
    ap.add_argument("--context", default=None)
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--demo-auto", action="store_true")
    ap.add_argument("--tier", choices=["barks", "standard"], default="barks",
                    help="barks=day-granular (v1); standard=45-min slot granular, "
                         "line stable within each slot = engine 45min cooldown tier (v2)")
    ap.add_argument("--face", choices=["greet", "faq"], default=None,
                    help="social faces (GREETINGS.md v1.0): greet needs --gkey, faq pairs by id+date")
    ap.add_argument("--gkey", choices=GKEYS, default="smalltalk",
                    help="social timepoint for --face greet")
    args = ap.parse_args()
    rows = load_rows()
    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    if args.face:
        greets = load_greetings()
        if args.face == "greet":
            print(f"face=greet gkey={args.gkey}")
            for cid in ids:
                line = greet_line(cid, args.gkey, greets, rows) if cid in rows else None
                print(f"{cid} {rows[cid]['name']}: {line}" if line else f"{cid}: (greet bucket empty)")
        else:
            print("face=faq")
            for cid in ids:
                p = faq_pair(cid, greets, rows) if cid in rows else None
                print(f"{cid} {rows[cid]['name']} 问：{p['q']} 答：{p['a']}" if p else f"{cid}: (faq bucket empty)")
        return
    with open(POOL, encoding="utf-8") as f:
        pools = json.load(f)
    # T-20260924-16d step 3: negative speech face (crash/recovering routing).
    neg = None; cface = {}; plan_ok = set()
    try:
        with open(NEG, encoding="utf-8") as f:
            neg = json.load(f)
    except Exception:
        neg = None
    if neg:
        cface = load_crash(rows)
        if cface:
            plan_ok = neg_visible_plan(rows, cface)
    ctx, src = derive_context() if (args.auto or args.demo_auto) else (args.context, "manual")
    if ctx not in CONTEXTS:
        print(f"unknown context: {ctx}"); sys.exit(2)
    # 城市情绪导演接线（T-16c·契约=cognition/MOOD-DIRECTOR.md）：导演态只调桶选择——
    # clock 档加权抽签（事件/天气/手动=事实门优先不改写）；线级确定性不动（同(id,日期,ctx)恒同句）。
    mood_st = None
    if args.auto or args.demo_auto:
        try:
            sys.path.insert(0, HERE)
            from mood_director import current_state, mood_ctx_lottery
            mood_st = current_state()
        except Exception:
            mood_st = None
    slot = None
    if args.tier == "standard":
        now = datetime.datetime.now()
        slot = (now.hour * 60 + now.minute) // 45
    ids = []
    if args.demo_auto:
        by_d = {}
        for r in rows.values():
            by_d.setdefault(r["district"], []).append(r)
        for d, rs in sorted(by_d.items()):
            ids.append(rs[hash(d + str(datetime.date.today())) % len(rs)]["id"])
    else:
        ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    head = f"ctx={ctx} (src={src}" + (f" mood={mood_st['mood']}" if mood_st else "") + ")"
    print(head + (f" tier=standard slot={slot}" if slot is not None else " tier=barks"))
    date = datetime.date.today().isoformat()
    for cid in ids:
        use_ctx = ctx
        if mood_st is not None and src == "clock":
            use_ctx = mood_ctx_lottery(ctx, src, mood_st["weights"],
                                       cid + "|" + date + "|" + ("s" + str(slot) if slot is not None else "") + "|" + mood_st["mood"])
        nl = neg_line(cid, neg, cface, plan_ok, rows, date=date, slot=slot) if neg else None
        if nl is not None:
            line, ftag = nl
            print(f"{cid} {rows[cid]['name']} [{ftag}]: {line}")
            continue
        line = draw_line(cid, use_ctx, pools, rows, slot=slot)
        if line is None:
            print(f"{cid}: (pool empty)")
        else:
            tag = 'sprite' if rows[cid].get('species') == 'sprite' else (rows[cid].get('axis') or '烟火')
            mark = f"{tag}|{use_ctx}←mood" if use_ctx != ctx else tag
            print(f"{cid} {rows[cid]['name']} [{mark}]: {line}")

if __name__ == "__main__":
    main()
