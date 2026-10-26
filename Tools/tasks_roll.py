#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""任务板滚动归档（T-20260926-05 契约⑤ 防再膨胀滚动律）。

把 tasks/TASKS.md 中「日期 <= --before」的实录/轮记类整段逐字移入
tasks/archive/TASKS-<YYYY-MM>.md（原文保全·零删改），板面原位留一行指针。

用法：
  python -X utf8 Tools/tasks_roll.py --dry-run
  python -X utf8 Tools/tasks_roll.py --before 2026-10-25

规则：
  - 只动标题含 实录 / 轮记 / 轮值 的段（规格/立法/任务单段零触碰）
  - 标题日期 <= before 才移；无日期的段不动
  - 归档前后逐块逐字对账（移动文本必须出现在月档）
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, "tasks", "TASKS.md")
ARCH_DIR = os.path.join(ROOT, "tasks", "archive")

HDR = re.compile(r"^(##|###)\s+(.*)$")
DATE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
ROLL_TITLE = re.compile(r"(实录|轮记|轮值)")
# 派工/承令/规格类段即便带「实录」二字也不动（内含任务单或立法内容）
SKIP_TITLE = re.compile(r"(派工|承令|令|规格|契约|立法|批（)")


def fmt_date(header):
    m = DATE.search(header)
    if not m:
        return None
    return "%s-%s-%s" % (m.group(1), m.group(2), m.group(3))


def find_blocks(lines, before):
    starts = []
    for i, line in enumerate(lines):
        m = HDR.match(line)
        if m:
            starts.append((i, len(m.group(1)), m.group(2)))
    blocks = []
    for k, (i, lvl, title) in enumerate(starts):
        if not ROLL_TITLE.search(title) or SKIP_TITLE.search(title):
            continue
        d = fmt_date(title)
        if d is None or d > before:
            continue
        end = len(lines)
        for i2, lvl2, _ in starts[k + 1:]:
            if lvl2 <= lvl:
                end = i2
                break
        blocks.append((i, end, title))
    return blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=None, help="归档该日（含）之前的实录段 YYYY-MM-DD")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not a.before:
        print("need --before YYYY-MM-DD")
        return 2

    txt = io.open(BOARD, encoding="utf-8").read()
    lines = txt.split("\n")
    blocks = find_blocks(lines, a.before)
    if not blocks:
        print("nothing to roll (before=%s)" % a.before)
        return 0

    moved = []
    for s, e, title in blocks:
        moved.append("\n".join(lines[s:e]).rstrip("\n"))
    pay = sum(len(b.encode("utf-8")) + 2 for b in moved)
    print("blocks=%d move_bytes=%d board_before=%d board_after=%d"
          % (len(blocks), pay, len(txt.encode("utf-8")),
             len(txt.encode("utf-8")) - pay))
    if a.dry_run:
        for s, e, t in blocks:
            print("  L%d-%d %s" % (s + 1, e, t[:48]))
        return 0

    # 按月档分组（段标题月份 = 归档目标月，跨月不混入）
    groups = {}
    for (s, e, title), body in zip(blocks, moved):
        ym = fmt_date(title)[:7]
        groups.setdefault(ym, []).append((body, title))

    today = __import__("datetime").date.today().isoformat()
    days = today
    os.makedirs(ARCH_DIR, exist_ok=True)
    written_arch = []
    for ym, items in sorted(groups.items()):
        arch = os.path.join(ARCH_DIR, "TASKS-%s.md" % ym)
        old = io.open(arch, encoding="utf-8").read() if os.path.exists(arch) else "# BigLife 任务板月档 %s\n" % ym
        head = "\n\n## 滚动归档 %s（before=%s · %d 段 · 逐字移入）\n" % (
            days, a.before, len(items))
        new_arch = old.rstrip("\n") + head + "\n" + "\n\n".join(b for b, _ in items) + "\n"
        bad = [t for b, t in items if b not in new_arch]
        if bad:
            print("VERIFY FAIL: %s missing %d blocks" % (ym, len(bad)))
            return 1
        io.open(arch, "w", encoding="utf-8", newline="\n").write(new_arch)
        written_arch.append((ym, arch, len(items)))

    # 板面：移除块，首块位置留一行指针
    drop = set()
    for s, e, _ in blocks:
        drop.update(range(s, e))
    pointer = "> 前日实录已滚动归档 → tasks/archive/TASKS-*.md（%s · %d 段）" % (
        days, len(blocks))
    out = []
    first = min(s for s, _, _ in blocks)
    for i, line in enumerate(lines):
        if i == first:
            out.append(pointer)
        if i in drop:
            continue
        out.append(line)
    new_board = "\n".join(out)
    new_board = re.sub(r"\n{4,}", "\n\n\n", new_board)

    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(new_board)
    for ym, arch, n in written_arch:
        print("rolled %d blocks -> %s" % (n, os.path.relpath(arch, ROOT)))
    print("board: %d -> %d bytes" % (len(txt.encode("utf-8")), len(new_board.encode("utf-8"))))
    print("verify: %d/%d blocks verbatim in archive" % (len(blocks), len(blocks)))
    return 0


if __name__ == "__main__":
    sys.exit(main())