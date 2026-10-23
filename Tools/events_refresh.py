#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Refresh event shards from cards, then run the replay gate in one step.

Why (R-20261023-scan-silicon-city action 1): cards are the source of truth and
`events/` is regenerable, but nothing re-derives the shards after a ring batch,
so `events_replay.py` reports stale mismatches (first live run: 700 mismatches
on 10091 cards). This tool closes that loop so the gate measures correctness
instead of staleness.

Usage:
  python -X utf8 Tools/events_refresh.py           # derive + replay
  python -X utf8 Tools/events_refresh.py --gate    # same, exit 1 on replay FAIL
"""
import argparse, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


def run(script, *args):
    cmd = [sys.executable, "-X", "utf8", str(HERE / script), *args]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="exit non-zero when the replay gate fails")
    args = ap.parse_args()

    rc_d, out_d, err_d = run("events_derive.py")
    if rc_d != 0:
        print(f"derive FAIL rc={rc_d} {err_d[-300:]}")
        return 2
    rc_r, out_r, err_r = run("events_replay.py")
    print(f"derive: {out_d.splitlines()[-1] if out_d else '-'}")
    print(f"replay: {out_r or err_r[-300:]}")
    if args.gate and rc_r != 0:
        return rc_r
    return 0


if __name__ == "__main__":
    sys.exit(main())