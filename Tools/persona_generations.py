#!/usr/bin/env python3
"""persona_generations.py - generational pool freeze for persona-v2 assignment.

T-20261115-02 measured that appending ONE gene reshuffles the derived habit slot
of 99.1% of citizens: pick() = h32(cid,salt) % len(seq) moves every bucket
boundary when N grows, so no arithmetic trick survives. Decision (b) of that
task (CODEX §14 「习惯分配稳定性口径」): freeze a pool snapshot per generation
and pin each citizen to the snapshot of the generation it was born in; citizens
created later read the newest snapshot. Old snapshots are append-only.

Drift is zero by construction: an old citizen's snapshot list never changes, so
h32(cid,salt) % len(snapshot) never changes. New genes reach new residents only.

Usage:
  python -X utf8 persona_generations.py           # report generations + sync need
  python -X utf8 persona_generations.py --sync    # append a generation if pools grew
  python -X utf8 persona_generations.py --check   # rc=1 when pools grew (sync owed)
"""
import argparse, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from persona_enrich import load_genes  # noqa: E402

OUT = os.path.join(CO, "genes", "persona-pool-generations.json")
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")


def current_pools():
    g = load_genes()
    tics = g.get("sentence_tics") or {}
    return {
        "habits": list(g.get("habits") or []),
        "likes": list(g.get("likes") or []),
        "dislikes": list(g.get("dislikes") or []),
        "address_terms": list(g.get("address_terms") or []),
        "seed_wrappers": list(g.get("seed_wrappers") or []),
        "tics_openers": list(tics.get("openers") or []),
        "tics_closers": list(tics.get("closers") or []),
    }


def max_cid():
    hi = 0
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cid = json.loads(line).get("id") or ""
            try:
                hi = max(hi, int(cid.split("-")[-1]))
            except ValueError:
                continue
    return hi


def load(path=OUT):
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError):
        doc = {}
    doc.setdefault("v", 1)
    doc.setdefault("generations", [])
    return doc


def save(doc, path=OUT):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")


def pending(doc, pools):
    gens = doc.get("generations") or []
    if not gens:
        return list(pools)
    last = (gens[-1].get("pools") or {})
    return [k for k in pools if last.get(k) != pools[k]]


def sync(doc, pools, horizon, today):
    gens = doc.setdefault("generations", [])
    if not gens:
        gens.append({"gen": 1, "created": today, "cutoff_cid": horizon, "pools": pools})
        return "opened gen 1 (cutoff C-%05d)" % horizon
    last = gens[-1]
    changed = pending(doc, pools)
    if not changed:
        return "no change (gen %d current, cutoff C-%05d)" % (last["gen"], last["cutoff_cid"])
    gens.append({
        "gen": last["gen"] + 1, "created": today, "cutoff_cid": horizon,
        "pools": pools, "grew_from_gen": last["gen"], "changed": changed,
    })
    return "opened gen %d (cutoff C-%05d, changed=%s)" % (last["gen"] + 1, horizon, ",".join(changed))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync", action="store_true", help="append a generation when pools grew")
    ap.add_argument("--check", action="store_true", help="rc=1 when a sync is owed")
    a = ap.parse_args()

    pools = current_pools()
    doc = load()
    horizon = max_cid()
    need = pending(doc, pools)

    if a.sync:
        msg = sync(doc, pools, horizon, datetime.date.today().isoformat())
        save(doc)
        print("sync: " + msg)
        need = pending(doc, pools)
    else:
        print("pools: " + ", ".join("%s=%d" % (k, len(v)) for k, v in pools.items()))

    for g in doc.get("generations") or []:
        print("gen %d  cutoff C-%05d  created %s  habits=%d%s" % (
            g.get("gen", 0), g.get("cutoff_cid", 0), g.get("created", "?"),
            len((g.get("pools") or {}).get("habits") or []),
            ("  grew_from_gen=%s" % g["grew_from_gen"]) if g.get("grew_from_gen") else ""))
    print("max_cid=C-%05d  pending_sync=%s" % (horizon, ",".join(need) if need else "none"))

    if a.check and need:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
