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
CLOSED_HEAD_RE = re.compile(rb'^- \[x\] ')
BOUNDARY_RE = re.compile(rb'^(?:- \[|#)')


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


def closed_blocks(lines):
    """已结单整块扫描（分步②）：标题行起，至下一顶级行（- [ 或节标题）前。
    尾部纯空行收缩出块（节间版式随板保留）。归档指针行（分步②产物）不算块身=幂等关键。
    返回 [(start, end), ...]。"""
    blocks, i, n = [], 0, len(lines)
    ptr_head = '  - 【详情已归档】'.encode('utf-8')
    while i < n:
        if CLOSED_HEAD_RE.match(lines[i]):
            j = i + 1
            while j < n and not BOUNDARY_RE.match(lines[j]) and not lines[j].startswith(ptr_head):
                j += 1
            end = j
            while end > i + 1 and lines[end - 1].strip() == b'':
                end -= 1
            if end > i + 1:
                blocks.append((i, end))
            i = j
        else:
            i += 1
    return blocks


def run_closed_blocks(raw, eol, lines, dry_run):
    """分步②主流程：已结单整块详情逐字移月件，板面留单头行+一行指针。
    断言④同契约：非移动行零漂移 + [ ]/[x] 计数保全 + 移动行数=月件新增行数 + 抽验 10 行逐字命中。"""
    blocks = closed_blocks(lines)
    ptr_head = '  - 【详情已归档】'.encode('utf-8')
    moved = set()
    month_of = {}
    block_at = {}
    for (s, e) in blocks:
        head_txt = lines[s].decode('utf-8', 'replace')
        m = re.search(r'T-(\d{4})-(\d{2})', head_txt)
        month = (m.group(1) + '-' + m.group(2)) if m else datetime.date.today().strftime('%Y-%m')
        block_at[s] = (e, month)
        for k in range(s + 1, e):
            moved.add(k)
            month_of[k] = month
    # 线性合并：块头行保留 + 追加一行指针；块身行逐字入月件集
    final, arc, ptr_idx = [], {}, set()
    for i, l in enumerate(lines):
        if i in block_at:
            e, month = block_at[i]
            final.append(l)
            ptr = ('  - 【详情已归档】%d 行单内详情已逐字移至 tasks/archive/TASKS-%s.md'
                   '——T-20260926-05 拆月归档分步②（原文保全·检索走 rg 全文）') % (e - i - 1, month)
            final.append(ptr.encode('utf-8') + eol)
            ptr_idx.add(len(final) - 1)
        elif i in moved:
            arc.setdefault(month_of[i], []).append(l if l.endswith((b'\n',)) else l + eol)
        else:
            final.append(l)
    new_raw = b''.join(final)
    # 断言④-1 非移动行零漂移（仅排除本次新增指针行·存量指针行属非移动行）
    expect = [l for i, l in enumerate(lines) if i not in moved]
    got = [l for k, l in enumerate(final) if k not in ptr_idx]
    assert expect == got, 'non-moved line drift!'
    # 断言④-2 检查框计数保全（单头行保留 → [x] 计数不变；块内顶级 [ ] 不可吞 → 计数不变）
    assert new_raw.count(b'- [ ]') == raw.count(b'- [ ]'), 'open checkbox drift!'
    assert new_raw.count(b'- [x]') == raw.count(b'- [x]'), 'closed checkbox drift!'
    # 断言④-3 移动行数=月件新增行数
    total = sum(len(v) for v in arc.values())
    assert total == len(moved), 'moved count != archive lines!'
    # 断言④-4 抽验 ≤10 行原文逐字命中各自月件
    arc_raw = {m: b''.join(v) for m, v in arc.items()}
    movable = sorted(moved)
    step = max(1, len(movable) // 10)
    sample = movable[::step][:10]
    for i in sample:
        assert lines[i].rstrip(b'\r\n') in arc_raw[month_of[i]], 'sample miss: line %d' % i
    print('archive_tasks --closed-blocks: blocks=%d moved_lines=%d board %d -> %d bytes' % (
        len(blocks), len(moved), len(raw), len(new_raw)))
    for m in sorted(arc):
        print('  -> tasks/archive/TASKS-%s.md  +%d lines' % (m, len(arc[m])))
    print('  samples verbatim hit: %d/%d' % (len(sample), len(sample)))
    if dry_run:
        print('  (dry-run: nothing written)')
        return 0
    os.makedirs(ADIR, exist_ok=True)
    for m in sorted(arc_raw):
        path = os.path.join(ADIR, 'TASKS-%s.md' % m)
        hdr = b''
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            hdr = ('# BigLife 任务板月度归档 %s（T-20260926-05 拆月归档·token 止血令④）\n'
                   '> 原文保全铁律：本件内容系 tasks/TASKS.md 已结单详情/实录行逐字移入·零删改；检索走 rg 全文。\n\n'
                   % m).encode('utf-8').replace(b'\n', eol)
        with open(path, 'ab') as f:
            f.write(hdr + arc_raw[m])
    with open(BOARD, 'wb') as f:
        f.write(new_raw)
    print('  written: board + %d archive file(s)' % len(arc_raw))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default=None, help='YYYY-MM-DD（默认=今日·移该日之前实录行）')
    ap.add_argument('--closed-blocks', action='store_true', help='分步②：已结单整块详情逐字移月件（板面留单头+指针）')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    cutoff = args.before or datetime.date.today().isoformat()

    with open(BOARD, 'rb') as f:
        raw = f.read()
    eol = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.splitlines(keepends=True)

    if args.closed_blocks:
        return run_closed_blocks(raw, eol, lines, args.dry_run)

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
    ptr_idx = set()
    for i, l in enumerate(lines):
        r = run_starts.get(i)
        if r is not None:
            n = sum(1 for k in r if flags[k])
            months = sorted({flags[k][:7] for k in r if flags[k]})
            ptr = '  - 【实录已归档】%d 行批实录（%s）已逐字移至 %s——T-20260926-05 拆月归档（原文保全·检索走 rg 全文）' % (
                n, '、'.join(months), '、'.join('tasks/archive/TASKS-%s.md' % m for m in months))
            out.append(ptr.encode('utf-8') + eol)
            ptr_idx.add(len(out) - 1)
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

    # 断言④-1 非移动行序逐字节零漂移（仅排除本次新增指针行·存量指针行属非移动行——与分步②同法）
    expect = [l for i, l in enumerate(lines) if i not in moved]
    got = [l for k, l in enumerate(out) if k not in ptr_idx]
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
