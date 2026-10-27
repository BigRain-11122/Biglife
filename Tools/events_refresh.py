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


RESERVED_OK = ("C-00001", "C-00002", "C-00003")  # 荣誉席：CODEX §十二 4 明规不进叙事事件流


def coverage():
    """卡全集口径闸：导出卡 = 派生卡 + 荣誉席，且missing只允许荣誉席。

    Why: 派生面(registry+anchors)与导出面(citizens-light)分属两条生成链，
    任何一侧静默丢卡都会让事件流悄悄少掉居民而两闸仍绿（R2398 实锚：
    10114 导出 vs 10111 派生，差 3 = 荣誉席，属设计口径；此断言把该口径固化）。
    """
    reg = pathlib.Path(ROOT / "census" / "registry").rglob("C-*.md")
    anch = pathlib.Path(ROOT / "census" / "anchors").rglob("C-*.md")
    derived = {p.stem for p in reg} | {p.stem for p in anch}
    res = {p.stem for p in pathlib.Path(ROOT / "census" / "reserved").rglob("C-*.md")}
    exp = pathlib.Path(ROOT / "census" / "export" / "citizens-light.jsonl")
    exported = set()
    if exp.exists():
        for line in exp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                import json
                exported.add(json.loads(line).get("id"))
    missing = exported - derived
    bad = sorted(missing - res)
    print(f"coverage: derived={len(derived)} reserved={len(res)} exported={len(exported)} "
          f"unexpected_missing={len(bad)}")
    if bad:
        print("coverage DRIFT: " + ", ".join(bad[:20]))
        return 1
    return 0


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
    rc_c = coverage()
    print(f"derive: {out_d.splitlines()[-1] if out_d else '-'}")
    print(f"replay: {out_r or err_r[-300:]}")
    if args.gate and (rc_r != 0 or rc_c != 0):
        return rc_r or rc_c
    return 0


if __name__ == "__main__":
    sys.exit(main())