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
    ctx, src = derive_context() if (args.auto or args.demo_auto) else (args.context, "manual")
    if ctx not in CONTEXTS:
        print(f"unknown context: {ctx}"); sys.exit(2)
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
    print(f"ctx={ctx} (src={src})" + (f" tier=standard slot={slot}" if slot is not None else " tier=barks"))
    for cid in ids:
        line = draw_line(cid, ctx, pools, rows, slot=slot)
        if line is None:
            print(f"{cid}: (pool empty)")
        else:
            print(f"{cid} {rows[cid]['name']} [{'sprite' if rows[cid].get('species') == 'sprite' else (rows[cid].get('axis') or '烟火')}]: {line}")

if __name__ == "__main__":
    main()
