#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_audit.py - machine gate for the language line (cognition pools).

Single gatekeeper for pool iterations (CODEX §14): coverage vs targets,
global dup, length/digit/banned-word cleanliness, and same-version draw
determinism (in-process double draw, byte-identical). Exit 1 on hard fail;
under-target buckets are listed as the pool-round reopen signal (OS loop
reads this output). Zero LLM, fully deterministic.
Usage: python -X utf8 pool_audit.py [--target 8] [--sprite-target 6]
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
POOL = os.path.join(CO, "cognition", "pools.json")

BANNED = ["CEO", "Jason", "公司", "集团", "总部", "董事长", "经理"]
AXES = ["烟火", "秩序", "求新", "怀旧", "侠气", "逍遥"]
CONTEXTS = ["morning", "dusk", "night", "weekend", "rain", "typhoon",
            "heatwave", "coldsnap", "market_open", "market_close", "ceo_order", "festival"]

def audit_pools(pools, target, starget):
    hard, under, seen = [], [], {}
    axes_lines = sprite_lines = 0
    at_target_axes = at_target_sprite = 0
    for axis in AXES:
        for ctx in CONTEXTS:
            bucket = pools.get("axes", {}).get(axis, {}).get(ctx)
            if bucket is None:
                hard.append(f"missing bucket axes/{axis}/{ctx}")
                continue
            axes_lines += len(bucket)
            if len(bucket) >= target:
                at_target_axes += 1
            else:
                under.append(f"axes/{axis}/{ctx}={len(bucket)}")
            for l in bucket:
                if not (5 <= len(l) <= 24):
                    hard.append(f"len {l!r}")
                if re.search(r"[0-9]", l):
                    hard.append(f"digit {l!r}")
                if re.search(r"(19|20)\d{2}年", l):
                    hard.append(f"year {l!r}")
                if any(b in l for b in BANNED):
                    hard.append(f"banned {l!r}")
                if l in seen:
                    hard.append(f"dup {l!r} ({seen[l]} vs axes/{axis}/{ctx})")
                else:
                    seen[l] = f"axes/{axis}/{ctx}"
            if len(bucket) < 4:
                hard.append(f"axes/{axis}/{ctx} below floor 4 ({len(bucket)})")
    for ctx in CONTEXTS:
        bucket = pools.get("sprite", {}).get(ctx)
        if bucket is None:
            hard.append(f"missing bucket sprite/{ctx}")
            continue
        sprite_lines += len(bucket)
        if len(bucket) >= starget:
            at_target_sprite += 1
        else:
            under.append(f"sprite/{ctx}={len(bucket)}")
        for l in bucket:
            if not (4 <= len(l) <= 24):
                hard.append(f"sprite len {l!r}")
            if re.search(r"[0-9]", l):
                hard.append(f"sprite digit {l!r}")
            if any(b in l for b in BANNED):
                hard.append(f"sprite banned {l!r}")
            if l in seen:
                hard.append(f"sprite dup {l!r} ({seen[l]} vs sprite/{ctx})")
            else:
                seen[l] = f"sprite/{ctx}"
        if len(bucket) < 3:
            hard.append(f"sprite/{ctx} below floor 3 ({len(bucket)})")
    total = axes_lines + sprite_lines
    return total, axes_lines, sprite_lines, at_target_axes, at_target_sprite, hard, under

def determinism(pools):
    sys.path.insert(0, HERE)
    import draw
    rows = draw.load_rows()
    by_d = {}
    for r in rows.values():
        by_d.setdefault(r.get("district"), []).append(r)
    sample = []
    for d in sorted(by_d):
        rs = by_d[d]
        sample.append(rs[len(rs) // 3]["id"])
        sample.append(rs[len(rs) * 2 // 3]["id"])
    sprites = [r["id"] for r in rows.values() if r.get("species") == "sprite"][:2]
    sample += sprites
    pairs = bad = empty = 0
    for cid in sample:
        for ctx in CONTEXTS:
            a = draw.draw_line(cid, ctx, pools, rows)
            b = draw.draw_line(cid, ctx, pools, rows)
            pairs += 1
            if a != b:
                bad += 1
            if a is None:
                empty += 1
    return len(sample), pairs, bad, empty

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=8)
    ap.add_argument("--sprite-target", dest="starget", type=int, default=6)
    args = ap.parse_args()
    with open(POOL, encoding="utf-8") as f:
        pools = json.load(f)
    total, al, sl, ax_ok, sp_ok, hard, under = audit_pools(pools, args.target, args.starget)
    n_ids, pairs, bad, empty = determinism(pools)
    print("== pool_audit (language line machine gate) ==")
    print(f"axes buckets 72: lines={al} at_target={ax_ok}")
    print(f"sprite buckets 12: lines={sl} at_target={sp_ok}")
    print(f"total lines: {total}")
    print(f"hard_fails: {len(hard)}")
    for h in hard[:10]:
        print("  HARD:", h)
    print(f"under_target ({args.target}/{args.starget}): "
          f"{'NONE - SELF_TERMINATE' if not under else ' '.join(under)}")
    print(f"determinism: {pairs} pairs double-drawn, mismatch={bad}, empty_draw={empty} "
          f"({n_ids} ids x 12 ctx)")
    ok = not hard and bad == 0 and empty == 0
    print("verdict:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
