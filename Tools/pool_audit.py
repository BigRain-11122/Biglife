#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_audit.py - machine gate for the language line (cognition pools).

Single gatekeeper for pool iterations (CODEX §14): coverage vs targets,
global dup, length/digit/banned-word cleanliness, and same-version draw
determinism (in-process double draw, byte-identical). Exit 1 on hard fail;
under-target buckets are listed as the pool-round reopen signal (OS loop
reads this output). Zero LLM, fully deterministic.
Usage: python -X utf8 pool_audit.py [--target 15] [--sprite-target 10]
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
POOL = os.path.join(CO, "cognition", "pools.json")

BANNED = ["CEO", "Jason", "公司", "集团", "总部", "董事长", "经理"]
AXES = ["烟火", "秩序", "求新", "怀旧", "侠气", "逍遥"]
CONTEXTS = ["morning", "dusk", "night", "weekend", "rain", "typhoon",
            "heatwave", "coldsnap", "market_open", "market_close", "ceo_order", "festival"]

# --- greetings face (T-20260924-06③; contract = cognition/GREETINGS.md v1.0) ---
GREET = os.path.join(CO, "cognition", "greetings.json")
GKEYS = ["first_meet", "reunion", "smalltalk", "farewell"]
ENV_CHARS = "雨风雪月星"
ENV_TOKENS = ("今早", "今晚", "今夜", "清晨", "早晨", "早上", "早安", "晚安",
              "晚上", "深夜", "夜深", "晨光", "黄昏", "傍晚", "凌晨", "半夜",
              "正午", "晌午", "中午")
GREET_TARGET, GREET_FLOOR = 10, 6
FAQ_TARGET, FAQ_FLOOR = 3, 2

def g_clean(l):
    if not (4 <= len(l) <= 24): return "len"
    if re.search(r"[0-9]", l): return "digit"
    if any(b in l for b in BANNED): return "banned"
    if re.match(r"^[A-Za-z]+[\"'“”]", l): return "role-artifact"
    if re.search(r"(user|assistant|system)[\"'“”‘’]", l): return "role-artifact"
    if any(c in l for c in ENV_CHARS): return "env-char"
    if any(t in l for t in ENV_TOKENS): return "env-token"
    return None

def pool_line_set(pools):
    s = set()
    for v in pools.values():
        for ax in v.values():
            if isinstance(ax, list): s.update(ax)
            else:
                for ctx in ax.values(): s.update(ctx)
    return s

def audit_greetings(g, plines):
    hard, under, seen = [], [], {}
    glines = fpairs = flines = g_at = f_at = 0
    def chk(l, where, maxlen=24):
        bad = g_clean(l)
        if bad: hard.append(f"{bad} {l!r} ({where})")
        elif not (4 <= len(l) <= maxlen): hard.append(f"len {l!r} ({where})")
        if l in plines: hard.append(f"cross-face dup {l!r} ({where})")
        if l in seen: hard.append(f"dup {l!r} ({seen[l]} vs {where})")
        else: seen[l] = where
    for axis in AXES:
        for gk in GKEYS:
            b = g.get("greet", {}).get("axes", {}).get(axis, {}).get(gk)
            if b is None:
                hard.append(f"missing greet axes/{axis}/{gk}"); continue
            glines += len(b)
            if len(b) >= GREET_TARGET: g_at += 1
            else: under.append(f"greet/{axis}/{gk}={len(b)}")
            for l in b: chk(l, f"greet/{axis}/{gk}")
            if len(b) < GREET_FLOOR: hard.append(f"greet/{axis}/{gk} below floor ({len(b)})")
    for gk in GKEYS:
        b = g.get("greet", {}).get("sprite", {}).get(gk)
        if b is None:
            hard.append(f"missing greet sprite/{gk}"); continue
        glines += len(b)
        if len(b) >= GREET_TARGET: g_at += 1
        else: under.append(f"greet/sprite/{gk}={len(b)}")
        for l in b: chk(l, f"greet/sprite/{gk}")
        if len(b) < GREET_FLOOR: hard.append(f"greet/sprite/{gk} below floor ({len(b)})")
    for fam in AXES + ["sprite"]:
        b = g.get("faq", {}).get(fam)
        if b is None:
            hard.append(f"missing faq/{fam}"); continue
        fpairs += len(b); flines += 2 * len(b)
        if len(b) >= FAQ_TARGET: f_at += 1
        else: under.append(f"faq/{fam}={len(b)}")
        for p in b:
            if not (isinstance(p, dict) and "q" in p and "a" in p):
                hard.append(f"faq/{fam} bad pair {p!r}"); continue
            chk(p["q"], f"faq/{fam}/q", maxlen=20)
            chk(p["a"], f"faq/{fam}/a")
        if len(b) < FAQ_FLOOR: hard.append(f"faq/{fam} below floor ({len(b)})")
    return glines, fpairs, flines, g_at, f_at, hard, under

def greet_determinism(g):
    sys.path.insert(0, HERE)
    import draw
    rows = draw.load_rows()
    ids = [r for r in rows.values() if r.get("species") != "sprite"]
    sprites = [r for r in rows.values() if r.get("species") == "sprite"]
    sample = [ids[0]["id"], ids[len(ids) // 2]["id"], ids[-1]["id"]]
    sample += [s["id"] for s in sprites[:2]]
    pairs = bad = empty = 0
    for cid in sample:
        for gk in GKEYS:
            a = draw.greet_line(cid, gk, g, rows)
            b = draw.greet_line(cid, gk, g, rows)
            pairs += 1
            if a != b: bad += 1
            if a is None: empty += 1
        p1 = draw.faq_pair(cid, g, rows)
        p2 = draw.faq_pair(cid, g, rows)
        pairs += 1
        if p1 != p2: bad += 1
        if p1 is None: empty += 1
    return len(sample), pairs, bad, empty

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
    ap.add_argument("--target", type=int, default=15)
    ap.add_argument("--sprite-target", dest="starget", type=int, default=10)
    args = ap.parse_args()
    with open(POOL, encoding="utf-8") as f:
        pools = json.load(f)
    total, al, sl, ax_ok, sp_ok, hard, under = audit_pools(pools, args.target, args.starget)
    n_ids, pairs, bad, empty = determinism(pools)
    # greetings face (GREETINGS.md v1.0; the gate lands with the data file itself)
    if os.path.isfile(GREET):
        with open(GREET, encoding="utf-8") as f:
            g = json.load(f)
        glines, fpairs, flines, g_at, f_at, ghard, gunder = audit_greetings(g, pool_line_set(pools))
        hard += ghard; under += gunder
        gn, gpairs, gbad, gempty = greet_determinism(g)
    else:
        glines = fpairs = flines = g_at = f_at = gn = gpairs = gbad = gempty = 0
        hard.append("greetings face missing (cognition/greetings.json)")
    print("== pool_audit (language line machine gate) ==")
    print(f"axes buckets 72: lines={al} at_target={ax_ok}")
    print(f"sprite buckets 12: lines={sl} at_target={sp_ok}")
    print(f"total lines: {total}")
    print(f"greet buckets 28: lines={glines} at_target={g_at}")
    print(f"faq buckets 7: pairs={fpairs} lines={flines} at_target={f_at}")
    print(f"hard_fails: {len(hard)}")
    for h in hard[:10]:
        print("  HARD:", h)
    print(f"under_target (pool {args.target}/{args.starget} + greet {GREET_TARGET} + faq {FAQ_TARGET}): "
          f"{'NONE - SELF_TERMINATE' if not under else ' '.join(under)}")
    print(f"determinism: {pairs} pairs double-drawn, mismatch={bad}, empty_draw={empty} "
          f"({n_ids} ids x 12 ctx)")
    print(f"greet determinism: {gpairs} pairs double-drawn, mismatch={gbad}, empty_draw={gempty} "
          f"({gn} ids x 4 gkey + faq)")
    ok = not hard and bad == 0 and empty == 0 and gbad == 0 and gempty == 0
    print("verdict:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
