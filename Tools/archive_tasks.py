#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_tasks.py — 任务板拆月归档引擎（T-20260926-05·token 止血令④本司面·滚动律防再膨胀）

契约（单内判据先行 v0·R304 立单）：
①历史实录行族=逐字移动至 tasks/archive/TASKS-<YYYY-MM>.md（原文保全铁律·月件入 git）·板面原位留一行指针
②open/in-progress 单头/状态/交付行零触碰（只动「批实录」行族：迭代批实录/进化批实录/相遇轮实录/语言线闸实跑/池轮补深收口开头）
③滚动律=次日首轮裸跑（默认 cutoff=今日·移今日之前全部实录行·幂等零匹配即零动作）
④验收内建断言（任一不过即中止零写盘）：非移动行序逐字节零漂移 + 检查框行计数保全 + 移动行数=月件新增行数 + 抽验 10 行原文逐字命中月件
⑤实录族全形判据（T-20260928-01 修面 v0.2·R817 补 `> ` 引用前缀形；T-20261016-01 v0.3 补 R#### 轮注形；T-20261018-02 v0.4 补 bold+缩位形）：正典形=OPENERS 开头（缩进随旧例）；缺标记形/补记形=列 0 `- [日期…]` 且 **R### 粗体轮注或落款 @BigLife-OSLoop；引用前缀形=列 0 `> [日期…]` 同三判据之一；无 - 前缀形=列 0 `[日期…]` 同三判据之一；R#### 轮注形=列 0 `- R#### 日期…`/`R#### 日期…` 且落款 @BigLife-OSLoop（R1256 起轮实录行族）；bold+缩位形=列 0 `- **R####（MM-DD HH:MM…）**：`（R1501 起现行轮实录正形·年份缺位=本纪年 2026·列 0 锚定=任务单头/缩进体行误吞防线）。
   tokens 计量行（`- tokens: local=…`·无日期）=轮实录附属行，随前一实录行同月归档（中间空行不断）；列 0 残留形（回溯无实录父行=父块已被先前归档收走·手术脚本遗留面）→ 按当前月归档收口（v0.4）。
   缩进任务体行（status/交付/证据行）恒非实录=零误吞（判据②红线：open/in-progress 单头/状态/交付行零触碰）。
红线：CEO 人设权保留面/荣誉席卡面/QC·sync·census 户籍面零涉（本件只读写 tasks/ 两文件）。
用法：python -X utf8 Tools/archive_tasks.py [--before 2026-09-26] [--dry-run] [--qc]
"""
import argparse
import datetime
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, 'tasks', 'TASKS.md')
ADIR = os.path.join(ROOT, 'tasks', 'archive')

OPENERS = ('迭代批实录', '进化批实录', '相遇轮实录', '语言线闸实跑', '池轮补深收口', '轮批实录')
# R817：实录行族新增 `> [` 引用前缀形（R782 行实锚漏扫·T-20260928-01 同病二犯收口）
DATE_RE = re.compile(rb'^[ \t]*(?:- |> )\[(\d{4})-(\d{2})-(\d{2})[^\]]*\][ \t]*(.*)$')
BARE_DATE_RE = re.compile(rb'^\[(\d{4})-(\d{2})-(\d{2})[^\]]*\][ \t]*(.*)$')
ROUND_NOTE_RE = re.compile(r'\*\*R\d+ ')
CLOSED_HEAD_RE = re.compile(rb'^- \[x\] ')
BOUNDARY_RE = re.compile(rb'^(?:- \[|#)')
# T-20261016-01 v0.3：R#### 轮注形（R1256 起·`- R#### 日期…`/`R#### 日期…`+落款 @BigLife-OSLoop）；tokens 计量行=附属跟行
ROUND_LOG_RE = re.compile(rb'^[ \t]*(?:- )?R\d{3,5} (\d{4})-(\d{2})-(\d{2})')
TOKENS_RE = re.compile(rb'^[ \t]*- tokens: local=')
# T-20261018-02 v0.4：现行轮实录 bold+缩位形（R1501 起板面正形 `- **R####（MM-DD HH:MM…）**：`）。
# 列 0 锚定=误吞防线（任务单头 `- [ ] **T…`/`- **T…`/`- **PR-…` 与缩进体行均不匹配）；年份缺位=本纪年 2026。
BOLD_ROUND_RE = re.compile(rb'^- \*\*R\d{3,5}\xef\xbc\x88(\d{2})-(\d{2})')


def classify(line, cutoff):
    """返回行日期（属实录行族且早于 cutoff），否则 None。
    T-20260928-01：判据兼容实录族全形（补记行/无 `- ` 前缀行/缺标记行）；
    缩进任务体行（status/交付/证据行）缩进即豁免——列 0 判据是误吞防线。"""
    m = DATE_RE.match(line)
    if m:
        date = (m.group(1) + b'-' + m.group(2) + b'-' + m.group(3)).decode('ascii')
        if date >= cutoff:
            return None
        try:
            rest = m.group(4).decode('utf-8')
            head = line[:m.start(4)].decode('utf-8', 'replace')
        except UnicodeDecodeError:
            return None
        if rest.startswith(OPENERS):
            return date
        if line.startswith((b'- [', b'> [')) and (ROUND_NOTE_RE.match(rest) or '@BigLife-OSLoop' in head):
            return date
        return None
    m = BARE_DATE_RE.match(line)
    if m:
        date = (m.group(1) + b'-' + m.group(2) + b'-' + m.group(3)).decode('ascii')
        if date >= cutoff:
            return None
        try:
            rest = m.group(4).decode('utf-8')
            head = line[:m.start(4)].decode('utf-8', 'replace')
        except UnicodeDecodeError:
            return None
        if rest.startswith(OPENERS) or ROUND_NOTE_RE.match(rest) or '@BigLife-OSLoop' in head:
            return date
    # T-20261016-01 v0.3：R#### 轮注形（无 [日期] 括号·日期为裸文本）
    m = ROUND_LOG_RE.match(line)
    if m:
        date = (m.group(1) + b'-' + m.group(2) + b'-' + m.group(3)).decode('ascii')
        if date >= cutoff:
            return None
        if b'@BigLife-OSLoop' in line:
            return date
    # T-20261018-02 v0.4：bold+缩位形（列 0 锚定=误吞防线·年份=本纪年 2026）
    m = BOLD_ROUND_RE.match(line)
    if m:
        date = '2026-%s-%s' % (m.group(1).decode('ascii'), m.group(2).decode('ascii'))
        if date >= cutoff:
            return None
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
    moved = set()
    month_of = {}
    block_at = {}
    for (s, e) in blocks:
        head_txt = lines[s].decode('utf-8', 'replace')
        # R1102 修：任务号形=T-YYYYMMDD-NN（无年内连字符），旧式 T-(\d{4})-(\d{2}) 永不匹配→月归属恒落默认今月
        m = re.search(r'(?:T|PR)-(\d{4})(\d{2})\d{2}-\d', head_txt)
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


def propagate_tokens(lines, flags):
    """T-20261016-01 v0.3：tokens 计量行=轮实录附属行（无日期·随前一实录行同月·中间空行不断）。
    T-20261018-02 v0.4：列 0 残留形收口——回溯最近非空行非实录行（父块已被先前归档/手术移动收走）
    且本行列 0 → 按当前月归档（tokens 行=轮末计量附属·板面无独立合法态·残留恒为近期批遗留）。"""
    for i in range(len(lines)):
        if flags[i] is None and TOKENS_RE.match(lines[i]):
            j = i - 1
            while j >= 0 and lines[j].strip() == b'':
                j -= 1
            if j >= 0 and flags[j]:
                flags[i] = flags[j]
            elif lines[i].startswith(b'- tokens: '):
                flags[i] = datetime.date.today().strftime('%Y-%m') + '-01'
    return flags


def qc_battery():
    """T-20261018-02 v0.4 断言电池：合成夹具零触碰真件（R99 契约范式）。
    覆盖=实录族全形六正形 + v0.4 bold+缩位正/护栏/半角防护 + 误吞防护八负例 + tokens 附属三态。"""
    CUT = '2026-10-19'

    def u(s):
        return s.encode('utf-8')

    results = []

    def chk(name, got, want):
        results.append((name, got == want, repr(got), repr(want)))

    chk('正典形（OPENERS 开头）', classify(u('- [2026-09-26 12:00] 迭代批实录：R1 收口'), CUT), '2026-09-26')
    chk('裸日期+粗体轮注形', classify(u('[2026-09-26 12:30] **R240 收口记录'), CUT), '2026-09-26')
    chk('引用前缀形', classify(u('> [2026-09-26 22:2x] 进化批实录：x'), CUT), '2026-09-26')
    chk('R#### 全日期轮注形', classify(u('- R1234 2026-09-26 22:00 收口 @BigLife-OSLoop'), CUT), '2026-09-26')
    chk('R#### 全日期无落款·防护', classify(u('- R1234 2026-09-26 22:00 收口（无落款）'), CUT), None)
    chk('v0.4 bold+缩位形（现行正形）', classify(u('- **R1594（10-18 07:4x~08:1x·基因轮兑现轮）**：轮首三步毕…'), CUT), '2026-10-18')
    chk('v0.4 当日实录不移（cutoff 护栏）', classify(u('- **R1595（10-18 08:2x·测试轮）**：…'), '2026-10-18'), None)
    chk('v0.4 半角括号形·不识别', classify(u('- **R1594(10-18 07:4x·半角变体）**：…'), CUT), None)
    chk('误吞防护·任务单头 [ ]（内嵌字面示例）', classify(u('- [ ] **T-20261018-02**（缺陷单·内嵌字面 `- **R####（MM-DD…` 示例）'), CUT), None)
    chk('误吞防护·bold T- 单头', classify(u('- **T-20260926-18**（集团令·升华律执行件 v1.3）'), CUT), None)
    chk('误吞防护·bold PR- 提案头', classify(u('- **PR-20260928-BL01**（自驱提案轨首件）'), CUT), None)
    chk('误吞防护·节标题', classify(u('## 自领池（OS 循环/交互会话按优先级自领）'), CUT), None)
    chk('误吞防护·归档指针行', classify(u('  - 【实录已归档】12 行批实录（2026-10）已逐字移至 tasks/archive/TASKS-2026-10.md——T-20260926-05 拆月归档（原文保全）'), CUT), None)
    chk('误吞防护·缩进状态行', classify(u('  - status: open（2026-10-18 08:1x @BigLife-OSLoop R1594 立单）'), CUT), None)
    chk('误吞防护·缩进证据行（含 @落款）', classify(u('  - [2026-09-25 19:1x @BigLife-OSLoop R240] **U208 清理整合分步③**：①项回落标注'), CUT), None)
    chk('误吞防护·缩进 bold 轮形（非列 0）', classify(u('  - **R1594（10-18 07:4x·缩进变体）**：…'), CUT), None)
    # tokens 附属三态
    lines = [u('- **R1590（10-18 07:0x·附属测试轮）**：…'), b'', u('  - tokens: local=0 api=0 api_reason=-（测试）')]
    flags = propagate_tokens(lines, [classify(l, CUT) for l in lines])
    chk('tokens 正常附属·随父行同月', flags[2], '2026-10-18')
    lines = [u('  - 【实录已归档】12 行批实录（2026-10）已逐字移至 tasks/archive/TASKS-2026-10.md…'), b'', b'',
             u('- tokens: local=10 api=0 api_reason=-（残留形）')]
    flags = propagate_tokens(lines, [classify(l, CUT) for l in lines])
    chk('tokens 列 0 残留形·当前月收口', flags[3], datetime.date.today().strftime('%Y-%m') + '-01')
    lines = [u('  - status: open（任务体行·2026-10-18 08:1x）'), b'',
             u('  - tokens: local=0 api=0 api_reason=-（无父行缩进形）')]
    flags = propagate_tokens(lines, [classify(l, CUT) for l in lines])
    chk('tokens 无父缩进形·零误吞不附着', flags[2], None)

    bad = [r for r in results if not r[1]]
    for name, ok, got, want in results:
        print('%s  %s  got=%s want=%s' % ('PASS' if ok else 'FAIL', name, got, want))
    print('archive_tasks --qc: %d/%d PASS' % (len(results) - len(bad), len(results)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--before', default=None, help='YYYY-MM-DD（默认=今日·移该日之前实录行）')
    ap.add_argument('--closed-blocks', action='store_true', help='分步②：已结单整块详情逐字移月件（板面留单头+指针）')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--qc', action='store_true', help='断言电池（合成夹具·零触碰真件）')
    args = ap.parse_args()
    if args.qc:
        return qc_battery()
    cutoff = args.before or datetime.date.today().isoformat()

    with open(BOARD, 'rb') as f:
        raw = f.read()
    eol = b'\r\n' if b'\r\n' in raw else b'\n'
    lines = raw.splitlines(keepends=True)

    if args.closed_blocks:
        return run_closed_blocks(raw, eol, lines, args.dry_run)

    flags = propagate_tokens(lines, [classify(l, cutoff) for l in lines])

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
