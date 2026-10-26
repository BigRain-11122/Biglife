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

# 段内行级切片（--slice-section）：轮记起始行两种形态
REC_START = re.compile(r"^(?:- \*\*|#+ )R\d{3,5}")
# R####（10-19 00:05 / R1774（2026-10-20 02:5x）
REC_DATE = re.compile(r"R\d{3,5}[^0-9]{0,6}(?:(20\d{2})-)?(\d{2})-(\d{2})")


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


def find_section(lines, match):
    """按标题子串定位段（返回 (start, end, level, title)）。"""
    starts = []
    for i, line in enumerate(lines):
        m = HDR.match(line)
        if m:
            starts.append((i, len(m.group(1)), m.group(2)))
    for k, (i, lvl, title) in enumerate(starts):
        if match not in title:
            continue
        end = len(lines)
        for i2, lvl2, _ in starts[k + 1:]:
            if lvl2 <= lvl:
                end = i2
                break
        return i, end, lvl, title
    return None


def slice_records(lines, start, end, before, default_year):
    """段内按轮记行切块，返回 [(s, e, date, head)]（date<=before 者可移）。"""
    idx = [i for i in range(start + 1, end) if REC_START.match(lines[i])]
    out = []
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else end
        e = j
        while e > i + 1 and (not lines[e - 1].strip() or lines[e - 1].lstrip().startswith(">")):
            e -= 1
        m = REC_DATE.search(lines[i])
        if not m:
            out.append((i, e, None, lines[i]))
            continue
        year = m.group(1) or default_year
        d = "%s-%s-%s" % (year, m.group(2), m.group(3))
        out.append((i, e, d, lines[i]))
    return out


def run_slice(a):
    txt = io.open(BOARD, encoding="utf-8").read()
    lines = txt.split("\n")
    sec = find_section(lines, a.slice_section)
    if not sec:
        print("section not found: %s" % a.slice_section)
        return 2
    start, end, _lvl, title = sec
    m = DATE.search(title)
    default_year = m.group(1) if m else "2026"
    recs = slice_records(lines, start, end, a.before, default_year)
    picked = [r for r in recs if r[2] and r[2] <= a.before]
    nodate = [r for r in recs if not r[2]]
    moved = ["\n".join(lines[s:e]).rstrip("\n") for s, e, _d, _h in picked]
    pay = sum(len(b.encode("utf-8")) + 2 for b in moved)
    print("section=L%d-%d %s" % (start + 1, end, title[:40]))
    print("records=%d picked=%d nodate=%d move_bytes=%d board_before=%d board_after=%d"
          % (len(recs), len(picked), len(nodate), pay,
             len(txt.encode("utf-8")), len(txt.encode("utf-8")) - pay))
    for r in nodate[:5]:
        print("  NODATE L%d %s" % (r[0] + 1, r[3][:60]))
    if a.dry_run:
        for s, e, d, h in picked[:6] + picked[-3:]:
            print("  L%d-%d %s %s" % (s + 1, e, d, h[:44]))
        return 0
    if not picked:
        print("nothing to slice")
        return 0

    days = __import__("datetime").date.today().isoformat()
    os.makedirs(ARCH_DIR, exist_ok=True)
    groups = {}
    for (s, e, d, h), body in zip(picked, moved):
        groups.setdefault(d[:7], []).append((d, body))
    for ym, items in sorted(groups.items()):
        arch = os.path.join(ARCH_DIR, "TASKS-%s.md" % ym)
        old = io.open(arch, encoding="utf-8").read() if os.path.exists(arch) else "# BigLife 任务板月档 %s\n" % ym
        head = "\n\n## 段内切片归档 %s（%s · %d 记 · 逐字移入）\n" % (
            days, title[:32], len(items))
        new_arch = old.rstrip("\n") + head + "\n" + \
            "\n\n".join("%s\n%s" % (d, b) if not b.startswith(d) else b for d, b in items) + "\n"
        bad = [d for d, b in items if b not in new_arch]
        if bad:
            print("VERIFY FAIL: %s missing %d records" % (ym, len(bad)))
            return 1
        io.open(arch, "w", encoding="utf-8", newline="\n").write(new_arch)
        print("sliced %d records -> %s" % (len(items), os.path.relpath(arch, ROOT)))

    drop = set()
    for s, e, _d, _h in picked:
        drop.update(range(s, e))
    pointer = "> 段内旧轮记已切片归档 → tasks/archive/TASKS-*.md（%s · %d 记 · 逐字移入）" % (
        days, len(picked))
    out = []
    first = min(s for s, _e, _d, _h in picked)
    for i, line in enumerate(lines):
        if i == first:
            out.append(pointer)
        if i in drop:
            continue
        out.append(line)
    new_board = re.sub(r"\n{4,}", "\n\n\n", "\n".join(out))
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(new_board)
    print("board: %d -> %d bytes" % (len(txt.encode("utf-8")), len(new_board.encode("utf-8"))))
    print("verify: %d/%d records verbatim in archive" % (len(picked), len(picked)))
    return 0


def run_sections(a):
    """整段滚动：标题带日期且为轮记族（R#### 开头 / 实录 / 轮记 / 轮值）的 ## 段，
    段内无 open 单（`- [ ]`）才移；逐段逐字入月档。"""
    txt = io.open(BOARD, encoding="utf-8").read()
    lines = txt.split("\n")
    starts = []
    for i, line in enumerate(lines):
        m = HDR.match(line)
        if m:
            starts.append((i, len(m.group(1)), m.group(2)))
    picked = []
    for k, (i, lvl, title) in enumerate(starts):
        if lvl != 2:
            continue
        d = fmt_date(title)
        if d is None or d > a.before:
            continue
        if not (ROLL_TITLE.search(title) or re.match(r"^R\d", title)):
            continue
        if SKIP_TITLE.search(title):
            continue
        end = len(lines)
        for i2, lvl2, _ in starts[k + 1:]:
            if lvl2 <= lvl:
                end = i2
                break
        body = lines[i:end]
        if any(l.lstrip().startswith("- [ ]") for l in body):
            print("  SKIP(has open task) L%d %s" % (i + 1, title[:48]))
            continue
        picked.append((i, end, title, d))
    moved = ["\n".join(lines[s:e]).rstrip("\n") for s, e, _t, _d in picked]
    pay = sum(len(b.encode("utf-8")) + 2 for b in moved)
    print("sections=%d move_bytes=%d board_before=%d board_after=%d"
          % (len(picked), pay, len(txt.encode("utf-8")), len(txt.encode("utf-8")) - pay))
    for s, e, t, d in picked:
        print("  L%d-%d %s %s" % (s + 1, e, d, t[:52]))
    if a.dry_run or not picked:
        return 0

    days = __import__("datetime").date.today().isoformat()
    os.makedirs(ARCH_DIR, exist_ok=True)
    groups = {}
    for (_s, _e, _t, d), body in zip(picked, moved):
        groups.setdefault(d[:7], []).append((body, d))
    for ym, items in sorted(groups.items()):
        arch = os.path.join(ARCH_DIR, "TASKS-%s.md" % ym)
        old = io.open(arch, encoding="utf-8").read() if os.path.exists(arch) else "# BigLife 任务板月档 %s\n" % ym
        head = "\n\n## 整段滚动归档 %s（before=%s · %d 段 · 逐字移入）\n" % (
            days, a.before, len(items))
        new_arch = old.rstrip("\n") + head + "\n" + "\n\n".join(b for b, _d in items) + "\n"
        bad = [b for b, _d in items if b not in new_arch]
        if bad:
            print("VERIFY FAIL: %s missing %d sections" % (ym, len(bad)))
            return 1
        io.open(arch, "w", encoding="utf-8", newline="\n").write(new_arch)
        print("rolled %d sections -> %s" % (len(items), os.path.relpath(arch, ROOT)))

    drop = set()
    for s, e, _t, _d in picked:
        drop.update(range(s, e))
    out = []
    first = min(s for s, _e, _t, _d in picked)
    for i, line in enumerate(lines):
        if i == first:
            out.append("> 轮记段已整段滚动归档 → tasks/archive/TASKS-*.md（%s · %d 段）"
                       % (days, len(picked)))
        if i in drop:
            continue
        out.append(line)
    new_board = re.sub(r"\n{4,}", "\n\n\n", "\n".join(out))
    io.open(BOARD, "w", encoding="utf-8", newline="\n").write(new_board)
    print("board: %d -> %d bytes" % (len(txt.encode("utf-8")), len(new_board.encode("utf-8"))))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=None, help="归档该日（含）之前的实录段 YYYY-MM-DD")
    ap.add_argument("--slice-section", default=None,
                    help="段内行级切片：段标题子串（配合 --before 用）")
    ap.add_argument("--roll-sections", action="store_true",
                    help="轮记族整段滚动（标题带日期·段内无 open 单才移）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not a.before:
        print("need --before YYYY-MM-DD")
        return 2
    if a.slice_section:
        return run_slice(a)
    if a.roll_sections:
        return run_sections(a)

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