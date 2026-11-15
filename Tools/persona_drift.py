#!/usr/bin/env python3
"""persona_drift.py - measure habit re-assignment caused by gene pool growth.

T-20261115-02 asked: persona_enrich.pick() = h32(cid,salt) % len(seq), so
appending ONE gene reshuffles every citizen's derived habit/like slot. This
tool quantifies the exact share affected, per salt, without touching cards,
genes or the persona face. Read-only, deterministic, zero LLM.

Usage: python -X utf8 persona_drift.py [--limit N] [--out PATH]
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from persona_enrich import load_genes, pick  # noqa: E402

SALTS = ("hb", "hb2")
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
PROBE = "（待测基因·persona_drift probe）"


def load_ids(path, limit=0):
    ids = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            cid = row.get("id") or row.get("cid")
            if cid:
                ids.append(cid)
    return ids[:limit] if limit else ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap citizen count (0=all)")
    ap.add_argument("--out", default=os.path.join(CO, "census", "export", "persona-drift.json"))
    args = ap.parse_args()

    pool = list(load_genes()["habits"])
    ids = load_ids(LIGHT, args.limit)
    grown = pool + [PROBE]

    report = {"citizens": len(ids), "pool_len": len(pool), "probe": PROBE, "salts": {}}
    for salt in SALTS:
        moved = sum(1 for cid in ids if pick(cid, salt, pool) != pick(cid, salt, grown))
        report["salts"][salt] = {
            "moved": moved,
            "share": round(moved / len(ids), 6) if ids else 0.0,
            "theory_one_over_n": round(1.0 / len(grown), 6),
        }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    for salt, r in report["salts"].items():
        print(f"{salt}: moved={r['moved']}/{report['citizens']} share={r['share']:.2%} "
              f"theory={r['theory_one_over_n']:.2%}")
    print(f"pool_len={report['pool_len']} -> wrote {os.path.relpath(args.out, CO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
