#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""city_broadcast.py - city-wide big-event reaction manifest (cognition layer 5).

Layer 5 = layer 2 + layer 3 orchestration (cognition/README):
  majority of citizens -> deterministic axis-bucket draws via draw.py (zero LLM,
  day-stable), + a few citizens per district -> spotlight fact-level replies
  (local Ollama, honesty law: only fed facts, <=40 chars).
Fact gate: broadcast context is ACTIVATED ONLY BY REAL DATA (derive_context,
FluxVerse world read-only: real events > weather > clock). Headlines carry
situational tone only (pool-clean: no digits/names/dates/amounts); facts enter
only via the real gate that selected the bucket and via spotlight replies.
Usage:
  python -X utf8 city_broadcast.py                # auto ctx, plan-only (zero LLM)
  python -X utf8 city_broadcast.py --live         # + real spotlights 1/district
  python -X utf8 city_broadcast.py --ctx typhoon --spot 2 --live
"""
import argparse, datetime, hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw  # shared skeleton: pools path + fact gate + deterministic draw

# big-event templates (subset of CONTEXTS; ambient buckets morning/dusk/night/
# weekend/rain are NOT broadcasts - self-restraint: no big event = no broadcast)
BROADCASTS = {
    "typhoon": "全城防风广播：大风雨压境，各家各户收摊固窗，码头船火早归",
    "heatwave": "高温预警广播：暑气蒸人，遮阳棚下好乘凉，冷饮摊正当行",
    "coldsnap": "寒潮预警广播：寒气锁城，炉火与热茶正当时，出门多添一件",
    "market_open": "开市广播：钟声一响，城里做生意的居民都支棱起来了",
    "market_close": "收市广播：账本合上，行情入夜，市声换成人声",
    "ceo_order": "城主频道广播：超体之城收到新的城主令，全城静候聆听",
    "festival": "节令广播：城里张灯结彩，家家各有各的过节法",
}


def pick_per_district(by_district, district, ctx, date, k):
    """Deterministic spotlight pick: same (district, date, event) -> same citizens."""
    rs = by_district.get(district) or []
    if not rs or k <= 0:
        return []
    h = hashlib.md5((district + "|" + date + "|" + ctx).encode("utf-8")).hexdigest()
    base = int(h[:8], 16)
    return [rs[(base + i * 7919) % len(rs)] for i in range(min(k, len(rs)))]


def sample_majority(pools, rows, ctx):
    """One zero-LLM draw per axis group (+ sprite) - demonstrates the majority tone."""
    by_group = {}
    for r in rows.values():
        key = "sprite" if r.get("species") == "sprite" else (r.get("axis") or "烟火")
        by_group.setdefault(key, []).append(r)
    date = datetime.date.today().isoformat()
    out = []
    for key in sorted(by_group):
        rs = by_group[key]
        h = hashlib.md5((key + "|" + date + "|" + ctx).encode("utf-8")).hexdigest()
        r = rs[int(h[:8], 16) % len(rs)]
        line = draw.draw_line(r["id"], ctx, pools, rows)
        if line:
            out.append({"id": r["id"], "name": r["name"], "axis": key,
                        "district": r["district"], "line": line})
    return out


def spotlight_line(cid):
    """One fact-level reply via the existing spotlight CLI (local Ollama)."""
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "spotlight.py"), "--id", cid],
                           capture_output=True, text=True, encoding="utf-8", timeout=150)
        lines = [l for l in (p.stdout or "").splitlines() if l.strip()]
        return lines[-1].strip() if lines else f"{cid}: （今日不想说话）"
    except Exception:
        return f"{cid}: （今日不想说话）"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctx", default=None, help="manual context override (default: real fact gate)")
    ap.add_argument("--live", action="store_true", help="run real spotlight replies (local LLM)")
    ap.add_argument("--spot", type=int, default=1, help="spotlight citizens per district (0=none)")
    ap.add_argument("--out", default=None, help="optional path to dump the manifest JSON")
    args = ap.parse_args()

    with open(draw.POOL, encoding="utf-8") as f:
        pools = json.load(f)
    rows = draw.load_rows()
    ctx, src = (args.ctx, "manual") if args.ctx else draw.derive_context()
    if ctx not in draw.CONTEXTS:
        print(f"unknown context: {ctx}"); sys.exit(2)
    if ctx not in BROADCASTS:
        manifest = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "event": None, "src": src,
                    "note": f"no big event active (ambient ctx={ctx}) - broadcast layer silent",
                    "majority": None, "spotlights": []}
    else:
        manifest = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                    "event": ctx, "src": src,
                    "headline": BROADCASTS[ctx],
                    "fact_gate": "derive_context: real events > weather > clock (FluxVerse world read-only)",
                    "majority": {"contract": "draw.py --context <event> --tier barks (all citizens, zero LLM, day-stable)",
                                 "standard_tier": "draw.py --tier standard (45-min slot rotation)",
                                 "sample": sample_majority(pools, rows, ctx)},
                    "spotlights": []}
        if args.live and args.spot > 0:
            by_district = {}
            for r in rows.values():
                by_district.setdefault(r["district"], []).append(r)
            date = datetime.date.today().isoformat()
            for d in sorted(by_district):
                for r in pick_per_district(by_district, d, ctx, date, args.spot):
                    manifest["spotlights"].append(
                        {"district": d, "id": r["id"], "name": r["name"],
                         "line": spotlight_line(r["id"])})
    out = json.dumps(manifest, ensure_ascii=False, indent=1)
    print(out)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out + "\n")


if __name__ == "__main__":
    main()
