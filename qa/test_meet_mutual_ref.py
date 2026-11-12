# -*- coding: utf-8 -*-
"""T-20261027-01 regression: meet mutual-reference gate.

Proves the two guards wired into `evolve_citizen.py --meet`:
  1. `_meet_ring_today()` reports an already-landed same-day meet partner
     (so the write face refuses a second meet ring on that card).
  2. `_meet_pair_check()` returns [] only when BOTH cards name each other;
     a one-sided pair (A names B, B names C) must surface as a defect.

Run: python -X utf8 qa/test_meet_mutual_ref.py
Exit 0 = all cases pass. No LLM, no repo writes (temp dir only).
"""
import os
import sys
import tempfile

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Tools")
sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True

import evolve_citizen as ec  # noqa: E402

DAY = "2026-11-12"
ANCHOR = " [锚] 城市实况 %s（测试）" % DAY


def card(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# C-test\n\n## 年轮\n\n")
        for line in lines:
            f.write(line + "\n")


def meet_line(partner, name="甲"):
    return "- %s 「与 %s 相遇：%s说的话」%s" % (DAY, partner, name, ANCHOR)


def plain_line():
    return "- %s 「今天照常开门，江边走走。」%s" % (DAY, ANCHOR)


def run_case(label, files, ids, expect_pair_bad, expect_dup):
    tmp = tempfile.mkdtemp(prefix="meet-ref-")
    paths = {}
    for cid, lines in files.items():
        p = os.path.join(tmp, cid + ".md")
        card(p, lines)
        paths[cid] = p
    ec.find_card = lambda cid: paths.get(cid)
    ec.today = lambda: DAY

    dup = {cid: ec._meet_ring_today(paths[cid]) for cid in ids}
    bad = ec._meet_pair_check(list(ids))

    ok = True
    if bool(bad) != expect_pair_bad:
        ok = False
        print("  FAIL pair_check: got %r (want %s)" % (bad, "defect" if expect_pair_bad else "empty"))
    for cid, want in expect_dup.items():
        if dup[cid] != want:
            ok = False
            print("  FAIL dup[%s]: got %r want %r" % (cid, dup[cid], want))
    print("%-28s %s  pair_check=%r dup=%r" % (label, "PASS" if ok else "FAIL", bad, dup))
    return ok


def main():
    all_ok = True

    all_ok &= run_case(
        "fresh pair (no meet today)",
        {"C-90001": [plain_line()], "C-90002": [plain_line()]},
        ("C-90001", "C-90002"),
        expect_pair_bad=True,
        expect_dup={"C-90001": None, "C-90002": None},
    )

    all_ok &= run_case(
        "symmetric pair (A<->B)",
        {"C-90001": [meet_line("C-90002")], "C-90002": [meet_line("C-90001")]},
        ("C-90001", "C-90002"),
        expect_pair_bad=False,
        expect_dup={"C-90001": "C-90002", "C-90002": "C-90001"},
    )

    # Negative control: the historical defect shape (A names B, B names C).
    all_ok &= run_case(
        "one-sided pair (A->B, B->C)",
        {"C-90001": [meet_line("C-90002")], "C-90002": [meet_line("C-90003")]},
        ("C-90001", "C-90002"),
        expect_pair_bad=True,
        expect_dup={"C-90001": "C-90002", "C-90002": "C-90003"},
    )

    # A card whose same-day ring is a normal (non-meet) ring must not be
    # mistaken for a duplicate meet.
    all_ok &= run_case(
        "today plain ring only",
        {"C-90001": [plain_line()], "C-90002": [meet_line("C-90001")]},
        ("C-90001", "C-90002"),
        expect_pair_bad=True,
        expect_dup={"C-90001": None, "C-90002": "C-90001"},
    )

    print("verdict:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
