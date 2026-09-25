#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_tasks.py — 任务板拆月归档引擎（T-20260926-05·token 止血令④本司面·滚动律防再膨胀）

契约（单内判据先行 v0·R304 立单）：
①历史实录行族=逐字移动至 tasks/archive/TASKS-<YYYY-MM>.md（原文保全铁律·月件入 git）·板面原位留一行指针
②open/in-progress 单头/状态/交付行零触碰（只动「批实录」行族：迭代批实录/进化批实录/相遇轮实录/语言线闸实跑/池轮补深收口开头）
③滚动律=次日首轮裸跑（默认 cutoff=今日·移今日之前全部实录行·幂等零匹配即零动作）
④验收内建断言（任一不过即中止零写盘）：非移动行序逐字节零漂移 + 检查框行计数保全 + 移动行数=月件新增行数 + 抽验 10 行原文逐字命中月件
红线：CEO 人设权保留面/荣誉席卡面/QC·sync·census 户籍面零涉（本件只读写 tasks/ 两文件）。
用法：python -X utf8 Tools/archive_tasks.py [--before 2026-09-26] [--dry-run]
"""
import argparse
import datetime
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, 'tasks', 'TASKS.md')
ADIR = os.path.join(ROOT, 'tasks', 'archive')

OPENERS = ('迭代批实录', '进化批实录', '相遇轮实录', '语言线闸实跑', '池轮补深收口')
DATE_RE = re.compile(rb'^[ \t]*- \[(\d{4})-(\d{2})-(\d{2})[^\]]*\][ \t]*(.*)$')


def classify(line, cutoff):
    """返回行日期（属实录行族且早于 cutoff），否则 None。"""
    m = DATE_RE.match(line)
    if not m:
        return None
    date = (m.group(1) + b'-' + m.group(2) + b'-' + m.group(3)).decode('ascii')
    if date >= cutoff:
        return None
    try:
        rest = m.group(4).decode('utf-8')
    except UnicodeDecodeError:
        return None
    if rest.startswith(OPENERS):
        return date
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default=None, help='YYYY-MM-DD（默认=今日·移该日之前实录行）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    cutoff = args.before or datetime.date.today().isoformat()

    with open(BOARD, 'rb') as f:
        raw = f.read()
    eol = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.splitlines(keepends=True)
    flags = [classify(l, cutoff) for l in lines]

    # 组 run：相邻实录行（允许行间纯空行·版式随行保全）
    runs, cur = [], []
    for i, fl in enumerate(flags):
        if not fl:
            continue
        if cur and i - cur[-1] > 1:
            gap = lines[cur[-1] + 1:i]
            if all(g.strip() == b'' for g in gap):
                cur.extend(range(cur[-1] + 1, i))
            else:
                runs.append(cur)
                cur = []
        cur.append(i)
    if cur:
        runs.append(cur)
    if not runs:
        print('archive_tasks: no log lines before %s — no-op (idempotent)' % cutoff)
        return 0

    moved = set()
    for r in runs:
        moved.update(r)
    run_starts = {r[0]: r for r in runs}

    # 板面重建：run 原位留一行指针；实录行按月归集（版式空行随前一实录行月件）
    out = []
    arc = {}
    ptr_head = '  - 【实录已归档】'.encode('utf-8')
    for i, l in enumerate(lines):
        r = run_starts.get(i)
        if r is not None:
            n = sum(1 for k in r if flags[k])
            months = sorted({flags[k][:7] for k in r if flags[k]})
            ptr = '  - 【实录已归档】%d 行批实录（%s）已逐字移至 %s——T-20260926-05 拆月归档（原文保全·检索走 rg 全文）' % (
                n, '、'.join(months), '、'.join('tasks/archive/TASKS-%s.md' % m for m in months))
            out.append(ptr.encode('utf-8') + eol)
            last_m = None
            for k in r:
                if flags[k]:
                    last_m = flags[k][:7]
                if last_m:
                    c = lines[k]
                    arc.setdefault(last_m, []).append(c if c.endswith((b'\n',)) else c + eol)
        elif i not in moved:
            out.append(l)

    new_raw = b''.join(out)
    arc_raw = {m: b''.join(v) for m, v in arc.items()}

    # 断言④-1 非移动行序逐字节零漂移
    expect = [l for i, l in enumerate(lines) if i not in moved]
    got = [l for l in out if not l.startswith(ptr_head)]
    assert expect == got, 'non-moved line drift!'

    # 断言④-2 检查框行计数保全（open/closed 单头零触碰实证）
    assert new_raw.count(b'- [ ]') == raw.count(b'- [ ]'), 'open checkbox drift!'
    assert new_raw.count(b'- [x]') == raw.count(b'- [x]'), 'closed checkbox drift!'

    # 断言④-3 移动行数=月件新增行数
    total = sum(len(v) for v in arc.values())
    assert total == len(moved), 'moved count != archive lines!'

    # 断言④-4 抽验 ≤10 行原文逐字命中各自月件
    movable = sorted(i for i in moved if flags[i])
    step = max(1, len(movable) // 10)
    sample = movable[::step][:10]
    for i in sample:
        assert lines[i].rstrip(b'\r\n') in arc_raw[flags[i][:7]], 'sample miss: line %d' % i

    print('archive_tasks: cutoff=%s runs=%d moved_lines=%d board %d -> %d bytes' % (
        cutoff, len(runs), len(moved), len(raw), len(new_raw)))
    for m in sorted(arc):
        print('  -> tasks/archive/TASKS-%s.md  +%d lines' % (m, len(arc[m])))
    print('  samples verbatim hit: %d/%d' % (len(sample), len(sample)))

    if args.dry_run:
        print('  (dry-run: nothing written)')
        return 0

    os.makedirs(ADIR, exist_ok=True)
    for m in sorted(arc_raw):
        path = os.path.join(ADIR, 'TASKS-%s.md' % m)
        hdr = b''
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            hdr = ('# BigLife 任务板月度归档 %s（T-20260926-05 拆月归档·token 止血令④）\n'
                   '> 原文保全铁律：本件内容系 tasks/TASKS.md 实录行逐字移入·零删改；检索走 rg 全文。\n\n'
                   % m).encode('utf-8').replace(b'\n', eol)
        with open(path, 'ab') as f:
            f.write(hdr + arc_raw[m])
    with open(BOARD, 'wb') as f:
        f.write(new_raw)
    print('  written: board + %d archive file(s)' % len(arc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
