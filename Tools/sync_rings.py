#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_rings.py - behavior line: mirror newest rings into the export face.

citizens-light.jsonl v1.2 adds recent_ring (latest ring text, <=80 chars)
and recent_ring_date for every citizen (empty when no ring yet). This tool
does the INCREMENTAL refresh: only citizens listed in state/evolve-cursor.json
(ring-bearing) are re-read from their cards; rows still missing the v1.2
fields are migrated in the same pass. Deterministic, zero LLM. Targeted git
commit when anything changed (machine tail tag via --via, versioning 4.1).
Usage: python -X utf8 sync_rings.py [--via BigLife-OSLoop]
"""
import argparse, datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from make_digests import LIGHT, find_card, latest_ring

CURSOR = os.path.join(CO, "state", "evolve-cursor.json")

def commit_light(msg):
    try:
        subprocess.run(["git", "-C", CO, "add", "--", LIGHT], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", CO, "commit", "-q", "-m", msg, "--", LIGHT], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", default="")
    args = ap.parse_args()
    if not os.path.isfile(CURSOR):
        print("no cursor; nothing to sync")
        return 0
    with open(CURSOR, encoding="utf-8") as f:
        cursor = json.load(f)
    with open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    changed = 0
    ring_synced = 0
    for r in rows:
        cid = r["id"]
        d = txt = None
        if cid in cursor:
            p = find_card(cid, r.get("district"))
            if p:
                with open(p, encoding="utf-8") as fh:
                    d, txt = latest_ring(fh.read())
        new_date = d or ""
        new_txt = (txt or "")[:80]
        if r.get("recent_ring") != new_txt or r.get("recent_ring_date") != new_date:
            r["recent_ring_date"] = new_date
            r["recent_ring"] = new_txt
            if new_txt:
                ring_synced += 1
            if float(r.get("v", 0)) < 1.2:
                r["v"] = 1.2
            changed += 1
    if changed:
        with open(LIGHT, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        msg = "行为线 %s: 镜像 rows=%d ring=%d" % (
            datetime.date.today(), changed, len(cursor))
        if args.via:
            msg += " [via %s]" % args.via
        ok = commit_light(msg)
        print(("committed" if ok else "COMMIT FAILED (worktree?)")
              + f" rows_changed={changed} ring_synced={ring_synced}")
    else:
        print("already in sync; zero write")
    return 0

if __name__ == "__main__":
    sys.exit(main())
