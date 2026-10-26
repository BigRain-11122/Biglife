#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hq_feedback_daily.py - once-per-day gate for the HQ feedback face.

Step 8 of the OS round prompt is a DAILY duty ("the round before 23:00"), but
rounds run every few minutes, so the prompt-level wording produced one 日清
line per round: 2026-10-27 00:0x-02:5x alone appended 15 lines to the root
HQ-FEEDBACK.md. That is bookkeeping spam on the CEO-visible face and blows the
round bookkeeping budget.

This gate makes the duty mechanical: a line is appended only when today's date
is absent from the file. `--force` overrides for a genuine same-day follow-up
(new blocker found after the daily line landed).

Usage:
  python -X utf8 Tools/hq_feedback_daily.py --text "日清：..."
  python -X utf8 Tools/hq_feedback_daily.py --check          # report only
Exit 0 = written or skipped (both normal); exit 2 = unusable input.
"""
import argparse, datetime, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
FACE = os.path.join(CO, "HQ-FEEDBACK.md")


def today_lines(path, day):
    """Return the count of dated bullet lines carrying `day` (YYYY-MM-DD)."""
    prefix = "- [%s" % day
    with open(path, encoding="utf-8") as f:
        return sum(1 for line in f if line.startswith(prefix))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="", help="feedback body (without the date stamp)")
    ap.add_argument("--check", action="store_true", help="report only, never write")
    ap.add_argument("--force", action="store_true", help="append even if today's line exists")
    args = ap.parse_args()

    if not os.path.exists(FACE):
        print("FAIL: HQ-FEEDBACK.md missing")
        return 2
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    n = today_lines(FACE, today)

    if args.check:
        print("day=%s lines=%d %s" % (today, n, "OPEN" if n == 0 else "ALREADY_REPORTED"))
        return 0

    if not args.text.strip():
        print("FAIL: --text required unless --check")
        return 2
    if n and not args.force:
        print("SKIP: day=%s already reported (%d line(s)) - daily duty satisfied" % (today, n))
        return 0

    body = " ".join(args.text.split())
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(FACE, "ab") as f:
        if os.path.getsize(FACE) > 0:
            with open(FACE, "rb") as r:
                r.seek(-1, os.SEEK_END)
                if r.read(1) != b"\n":
                    f.write(b"\n")
        f.write(("\n- [%s] %s\n" % (stamp, body)).encode("utf-8"))
    print("OK: appended day=%s (prior lines=%d)" % (today, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())