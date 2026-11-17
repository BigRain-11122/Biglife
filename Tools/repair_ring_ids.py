# -*- coding: utf-8 -*-
"""年轮单号残句存量清污（R3342·2026-11-17）

出生地病根=evolve_citizen 的事件码黑名单只认「字母+数字」(G08) 与「字母-字母」
(BG-A)，治理单号 `T-/O-/D-/PR-` 与轮次号 `R####` 一路放行（R3342 已补闸）。
本工具做存量清污，与 repair_dup_rings.py（R1772）同一口径：出生地已堵，存量也收。

改写规则（只动 **年轮** 块内含单号的年轮行；溯源/进化等簿记行不碰）：
  1. 相邻拉丁机器词 order/job/task/ref -> 「那单」
  2. 单号按语境改写：
     · 引号内（“…”/「…」）      -> 那张通告
     · 紧跟在 单子/订单/那单 之后 -> 直接删（保留「单子」）
     · 紧跟 这单/的单 之前       -> 直接删（保留后文）
     · 「把 O-…」句式            -> 直接删
     · 其余                      -> 那张通告
  3. 收拾残渣：中英夹缝空格、重复替换词、空引号、连续标点
年轮条数与日期一字不动，圈数无需重算。

用法：
  python -X utf8 Tools/repair_ring_ids.py                # dry-run，只报不写
  python -X utf8 Tools/repair_ring_ids.py --report out.md # dry-run + 全量改动对照写盘
  python -X utf8 Tools/repair_ring_ids.py --apply        # 落盘
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "census", "registry")

# 允许末尾半截（fit_ring_line 90 字截断会把 token 切掉尾段）
IDPAT = re.compile(
    r'(?<![A-Za-z0-9-])[ODT]-\d{8}(?:-\d{1,4})*(?:-[a-z]{1,4})*-?(?![A-Za-z0-9])'
    r'|(?<![A-Za-z0-9-])PR-\d{8}-\d+[a-z]?-?(?![A-Za-z0-9])'
    r'|(?<![A-Za-z0-9-])R\d{4,}(?![0-9])'
)
LEAD_LATIN = re.compile(r'(?<![A-Za-z0-9])(order|job|task|ref)(?![A-Za-z0-9])', re.I)
REPLACEMENT = u'那张通告'
POST_FIXES = (
    (u'那单' + REPLACEMENT, u'那单'),
    (REPLACEMENT + u'那张通告', REPLACEMENT),
    (REPLACEMENT + u'这张通告', REPLACEMENT),
    (REPLACEMENT + u'这单', u'这单'),
    (REPLACEMENT + u'那单', u'那单'),
    (u'“”', u''),
    (u'「」', u''),
    (u'————', u'——'),
    (u'，、', u'，'),
    (u'、，', u'，'),
    (u'，，', u'，'),
    (u'、、', u'、'),
    (u'，。', u'。'),
    (u'：，', u'：'),
)


def tidy(s):
    # 三项以上同词列表（某条广播污染了整串单号）直接删净，避免「那张通告、那张通告、…」
    s = re.sub(u'[—：，、]?(?:' + REPLACEMENT + u'、){2,}' + REPLACEMENT, u'', s)
    s = re.sub(u'[—：，、]?' + REPLACEMENT + u'、' + REPLACEMENT, u'', s)
    # 中英夹缝空格：替换词两侧不留空格；「把 + 空格」一并收；标点两侧不留空格
    s = re.sub(r'[ \t]+(?=' + REPLACEMENT + r')', '', s)
    s = re.sub(r'(?<=' + REPLACEMENT + r')[ \t]+', '', s)
    s = re.sub(r'把[ \t]+(?=[这那])', u'把', s)
    # 只收标点内侧空格（开引号前的「- 日期 」空格是行格式，必须保留）
    s = re.sub(r'(?<=[：，、；。！？])[ \t]+', '', s)
    s = re.sub(r'[ \t]+(?=[：，、；。！？」”])', '', s)
    for a, b in POST_FIXES:
        while a in s:
            s = s.replace(a, b)
    s = re.sub(r'[ \t]{2,}', u' ', s)
    s = re.sub(r'——(?=[。，、；：」])', u'', s)
    s = re.sub(r'(?<=[「“])[、，,]', u'', s)
    return s


def repair_line(line):
    # fit_ring_line 90 字截断可能把单号切成「…和O」这类残尾，先连词一起去掉
    # （残尾后面可能紧跟 」 与 [锚] 注脚，不只行尾）
    s = re.sub(r'[和跟与][ODT](?=」?[ \t]*(?:\[锚\]|$))', u'', line)
    s = LEAD_LATIN.sub(u'那单', s)
    hits = 0
    pos = 0
    while True:
        m = IDPAT.search(s, pos)
        if not m:
            break
        head, tail = s[:m.start()], s[m.end():]
        prev = head.rstrip(u' \u3000')
        nxt_s = tail.lstrip(u' \u3000')
        if (u'“' in head[-12:] and (u'”' in tail[:12])) or \
           (u'「' in head[-12:] and (u'」' in tail[:12])):
            repl = REPLACEMENT
        elif re.search(r'把[ \u3000]?$', prev):
            repl = REPLACEMENT
        elif prev.endswith((u'单子', u'订单', u'那单', u'一单', u'这单')):
            repl = u''
        elif nxt_s.startswith((u'这单', u'的单')):
            repl = u''
        else:
            repl = REPLACEMENT
        s = head + repl + tail
        hits += 1
        pos = len(head) + len(repl)
    return (tidy(s) if hits or s != line else line), hits



def card_paths():
    for d, _, fs in os.walk(REG):
        for f in sorted(fs):
            if f.endswith('.md') and f.startswith('C-'):
                yield os.path.join(d, f)


ARCH = os.path.join(ROOT, 'census', 'export', 'growth-archives')


def archive_paths():
    if not os.path.isdir(ARCH):
        return
    for f in sorted(os.listdir(ARCH)):
        if f.endswith('.json'):
            yield os.path.join(ARCH, f)


def cycle_archive(text):
    """成长档案 JSON：递归清污所有含单号的字符串（month_lines / rings[].quote.text），
    用原文替换，不改文件排版。"""
    import json
    try:
        obj = json.loads(text)
    except ValueError:
        return text, 0
    found = []

    def walk(v):
        if isinstance(v, str):
            if IDPAT.search(v):
                found.append(v)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(obj)
    changed = 0
    new_text = text
    for s in found:
        nl, _ = repair_line(s)
        if nl == s:
            continue
        old_lit = json.dumps(s, ensure_ascii=False)
        new_lit = json.dumps(nl, ensure_ascii=False)
        if old_lit in new_text:
            new_text = new_text.replace(old_lit, new_lit, 1)
            changed += 1
    return (new_text, changed) if changed else (text, 0)


def cycle(text):
    """只改 **年轮** 块内的年轮行；返回 (新文本, 改写行数)。"""
    lines = text.split('\n')
    out = []
    in_rings = False
    changed = 0
    for l in lines:
        if l.startswith('**年轮**'):
            in_rings = True
            out.append(l)
            continue
        if in_rings and l.startswith('**'):
            in_rings = False
        if in_rings and l.startswith('- 20'):
            nl, _hits = repair_line(l)
            if nl != l:
                changed += 1
                l = nl
        out.append(l)
    return ('\n'.join(out), changed) if changed else (text, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', default=None, help='dry-run 全量对照写盘（UTF-8）')
    ap.add_argument('--archives', action='store_true',
                    help='同时清污 census/export/growth-archives（成长档案快照）')
    args = ap.parse_args()
    cards = lines = 0
    report = []
    targets = [(p, cycle) for p in card_paths()]
    if args.archives:
        targets += [(p, cycle_archive) for p in archive_paths()]
    for p, fn in targets:
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        new, changed = fn(text)
        if not changed:
            continue
        cards += 1
        lines += changed
        rel = os.path.relpath(p, ROOT)
        print('%s: lines=%d' % (rel, changed))
        if (args.report or not args.apply):
            old_lines = [l for l in text.split('\n')
                         if l.startswith('- 20') and IDPAT.search(l)]
            new_lines = [l for l in new.split('\n') if l.startswith('- 20')]
            for a in old_lines:
                b = [x for x in new_lines if x[:12] == a[:12]]
                if b:
                    report.append('### ' + rel)
                    report.append('OLD: ' + a)
                    report.append('NEW: ' + b[0])
                    report.append('')
        if args.apply:
            with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(new)
    mode = 'APPLIED' if args.apply else 'DRY-RUN'
    print('%s cards=%d lines=%d' % (mode, cards, lines))
    if args.report:
        io.open(args.report, 'w', encoding='utf-8', newline='\n').write('\n'.join(report))
        print('report=' + args.report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
