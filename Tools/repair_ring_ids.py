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

巡检面（R3353·T-20261117-02 补）：本工具只清「单号」这一面；`Tools/ring_lint.py`
另有两面判据——内部码 `[GBSPT]####`（CODE_RE）与机队词（INFRA_RE）。这两面**不做机械
替换**（码嵌在句子中间，换掉易生病句），`--detect` 只产「待清清单」供重写：

  python -X utf8 Tools/repair_ring_ids.py --detect         # 巡检面待清清单（rc=1 有残留）

用法：
  python -X utf8 Tools/repair_ring_ids.py                # dry-run，只报不写
  python -X utf8 Tools/repair_ring_ids.py --report out.md # dry-run + 全量改动对照写盘
  python -X utf8 Tools/repair_ring_ids.py --apply        # 落盘
"""
import argparse
import datetime
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

# ---- 巡检面判据（与 Tools/ring_lint.py 逐字同源，改一处须同步另一处）----
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})[ \t]*(.+)$")
CODE_RE = re.compile(r"(?<![A-Za-z0-9-])[GBSPT]\d{1,4}(?:\.\d+)?(?![0-9])")
INFRA_RE = re.compile(r"显存|VRAM|GPU|显卡|机队", re.I)
FACE2 = ((u'内部码', CODE_RE), (u'机队词', INFRA_RE))
# 出生站切点（同 ring_lint）：切点前=存量冻结，切点后=新产，须优先重写
DEFAULT_FIX_CUT = "2026-10-26T18:57"
INFRA_FIX_CUT = "2026-11-13T00:00"
CUTS = {u'内部码': DEFAULT_FIX_CUT, u'机队词': INFRA_FIX_CUT,
        u'_floor': '2026-10-20'}  # 巡检窗 floor（ring_lint --since 默认）
PENDING = os.path.join(ROOT, 'qa', 'RING-ID-PENDING-%s.md')
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


def _mtime(path):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%dT%H:%M')
    except OSError:
        return ''


def ring_lines(text):
    """产 **年轮** 块内的年轮行 (date, body)——与 cycle() 同一切点。"""
    in_rings = False
    for l in text.split('\n'):
        if l.startswith('**年轮**'):
            in_rings = True
            continue
        if in_rings and l.startswith('**'):
            in_rings = False
        if in_rings and l.startswith('- 20'):
            m = RING_RE.match(l)
            if m:
                yield m.group(1), m.group(2)


def _load_fingerprints(name):
    """读 ring_lint 的存量指纹基线（不存在=空集，纯 mtime 口径）。"""
    import json
    p = os.path.join(ROOT, 'qa', name)
    if not os.path.exists(p):
        return set()
    try:
        with io.open(p, encoding='utf-8') as f:
            return set(json.load(f).get('fingerprints') or [])
    except (OSError, ValueError):
        return set()


def detect_face2(include_archives=False):
    """巡检面残留扫描：产 (rel, date, kind, tokens, era, body)。只读，不改盘。
    判代口径与 Tools/ring_lint.py 逐字一致（指纹基线优先，mtime 切点次之），
    否则同卡其它改动刷新 mtime 会把老存量误标成新产。"""
    import hashlib
    base = {u'内部码': _load_fingerprints('ring-lint-baseline.json'),
            u'机队词': _load_fingerprints('ring-infra-baseline.json')}
    rows = []
    for p in card_paths():
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        mt = _mtime(p)
        cid = os.path.splitext(os.path.basename(p))[0]
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        for date, body in ring_lines(text):
            fp = '%s|%s|%s' % (cid, date, hashlib.md5(body.encode('utf-8')).hexdigest())
            for kind, rx in FACE2:
                toks = sorted(set(rx.findall(body)))
                if not toks:
                    continue
                if fp in base[kind]:
                    era = u'存量'
                elif date < CUTS[u'_floor']:
                    era = u'存量·巡检窗外'
                elif mt and mt < CUTS[kind]:
                    era = u'存量'
                else:
                    era = u'新产'
                rows.append((rel, date, kind, u'/'.join(toks), era, body))
    if include_archives:
        for p in archive_paths():
            rel = os.path.relpath(p, ROOT).replace('\\', '/')
            mt = _mtime(p)
            with io.open(p, encoding='utf-8') as f:
                raw = f.read()
            for kind, rx in FACE2:
                toks = sorted(set(rx.findall(raw)))
                if not toks:
                    continue
                era = u'新产' if (mt and mt >= CUTS[kind]) else u'存量'
                rows.append((rel, '', kind, u'/'.join(toks), era, ''))
    return rows


def write_pending(rows, path):
    by_kind = {}
    by_era = {}
    for r in rows:
        by_kind[r[2]] = by_kind.get(r[2], 0) + 1
        by_era[r[4]] = by_era.get(r[4], 0) + 1
    out = [
        u'# 年轮巡检面待清清单（%s）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        u'',
        u'判据=与 `Tools/ring_lint.py` 逐字同源：内部码 `%s`、机队词 `%s`；'
        u'判代同源（指纹基线优先，mtime 切点次之）。'
        % (CODE_RE.pattern, INFRA_RE.pattern),
        u'',
        u'**本清单只检测不替换**——内部码/机队词嵌在句子中间，机械替换必生病句，须按条重写'
        u'（人或 LLM 逐条改，改后重跑 `Tools/ring_lint.py` 复核）。`新产` 优先。',
        u'',
        u'合计 **%d** 环次：%s；分代 %s。'
        % (len(rows),
           u'、'.join(u'%s=%d' % (k, v) for k, v in sorted(by_kind.items())),
           u'、'.join(u'%s=%d' % (k, v) for k, v in sorted(by_era.items()))),
        u'',
        u'| 卡片 | 年轮日期 | 类型 | 命中 | 代 | 原句（截 80 字） |',
        u'|---|---|---|---|---|---|',
    ]
    for rel, date, kind, toks, era, body in rows:
        snippet = (body or '').replace('|', u'｜')[:80]
        out.append(u'| %s | %s | %s | `%s` | %s | %s |'
                   % (rel, date, kind, toks, era, snippet))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', default=None, help='dry-run 全量对照写盘（UTF-8）')
    ap.add_argument('--archives', action='store_true',
                    help='同时清污 census/export/growth-archives（成长档案快照）')
    ap.add_argument('--detect', action='store_true',
                    help='巡检面（内部码/机队词）待清清单：只检测不替换，rc=1=有新产残留')
    ap.add_argument('--pending', default=None, help='--detect 清单写盘路径')
    ap.add_argument('--fail-on-stock', action='store_true',
                    help='--detect 时连存量残留也算失败（默认只拦新产）')
    args = ap.parse_args()

    if args.detect:
        rows = detect_face2(include_archives=args.archives)
        path = args.pending or PENDING % datetime.date.today().strftime('%Y%m%d')
        write_pending(rows, path)
        new = sum(1 for r in rows if r[4] == u'新产')
        print('DETECT face2 hits=%d new=%d stock=%d report=%s'
              % (len(rows), new, len(rows) - new, path))
        if new:
            return 1
        return 1 if (args.fail_on_stock and rows) else 0

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
