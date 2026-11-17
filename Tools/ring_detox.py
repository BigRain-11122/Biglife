# -*- coding: utf-8 -*-
"""年轮技术黑话清污（R3368·2026-11-17·T-20261117-02 续）

出生地病根=evolve_citizen 事件码黑名单只认「字母+数字」「字母-字母」，机队词与
城市内部码一路放行（R3342 已堵单号面）。repair_ring_ids.py 只清「治理单号」面，
其巡检面（内部码/机队词）标注「不做机械替换，须按条重写」。

本工具走第三条路：**有限模式映射表**——每条映射人工审定，只覆盖语义可无损城市化的
形态（技术黑话→城市日常语），映射不命中即原样保留并进待办报告。与自由生成不同，
本工具是确定性的、可审计的、幂等的。

安全设计：
  1. 只在 `**年轮**` 块内的 `- YYYY-MM-DD` 行改写（与 repair_ring_ids.cycle 同切点）；
  2. 改写后**在内存里跑 ring_lint 同源判据复核**，残余新产>0 则拒绝落盘；
  3. 默认 dry-run，`--apply` 才写；`--report` 产对照表供人审。

正典映射依据：
  · G08/G16 等 GAME 城楼号 -> 游戏楼（docs/CODEX.md §三 街区「P01-P08 游戏楼」）
  · S2.5 类版本号 -> 新版本
  · B2396/B2166 类外仓编号 -> 老楼
  · GPU_VRAM_LOW / 显存 / 显卡 / 机队 -> 城市日常语（算力/机房/老机器）

用法：
  python -X utf8 Tools/ring_detox.py                  # dry-run 报覆盖率
  python -X utf8 Tools/ring_detox.py --report out.md  # dry-run + 对照表写盘
  python -X utf8 Tools/ring_detox.py --apply          # 落盘（须复核 PASS）
"""
import argparse
import datetime
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "census", "registry")

# ---- 与 ring_lint.py 逐字同源的判据（改一处须同步两处）----
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})[ \t]*(.+)$")
CODE_RE = re.compile(r"(?<![A-Za-z0-9-])[GBSPT]\d{1,4}(?:\.\d+)?(?![0-9])")
INFRA_RE = re.compile(r"显存|VRAM|GPU|显卡|机队", re.I)
FACE2 = ((u'内部码', CODE_RE), (u'机队词', INFRA_RE))

# ---- 映射表（先整串后单点，顺序即优先级）----
# 每条=(正则, 替换, 说明)。整串模式必须能独立成句，避免留下病句。
MAPS = [
    # --- CrazyCampus 迁移串（~30 条，是同一事件广播被复读）---
    (re.compile(r'[，,：:—]*\s*G0?8\s*CrazyCampus\s*[:：]?\s*B\d{3,5}\s*(?:->|→|到)\s*S\d(?:\.\d+)?'),
     u'营地搬迁那摊事', u'G08 CrazyCampus 迁移整串'),
    (re.compile(r'CrazyCampus\s*[:：]?\s*B\d{3,5}\s*(?:->|→|到)\s*S\d(?:\.\d+)?'),
     u'营地搬迁', u'CrazyCampus 迁移串'),
    (re.compile(r'\s*CrazyCampus\s*'), u'', u'CrazyCampus 裸词'),
    # --- GPU_VRAM_LOW 各类包裹 ---
    (re.compile(r'verdict\s*=\s*GPU_VRAM_LOW'), u'体检没过', u'verdict=GPU_VRAM_LOW'),
    (re.compile(r'[“"「]GPU_VRAM_LOW[”"」]'), u'那张告警条', u'引号内告警串'),
    (re.compile(r'GPU_VRAM_LOW'), u'告警条', u'裸告警串'),
    # --- 整句模板污染（同一条广播复读）---
    (re.compile(r'[，,]?\s*(?:得)?抓紧优化代码[，,]\s*显存紧张[！!]?'), u'', u'模板句：抓紧优化代码'),
    (re.compile(r'显存紧张得紧'), u'算力吃紧得厉害', u'显存紧张得紧'),
    (re.compile(r'显存紧张了?'), u'算力吃紧', u'显存紧张'),
    (re.compile(r'显存低了'), u'算力吃紧了', u'显存低了'),
    (re.compile(r'显存稳着'), u'算力稳着', u'显存稳着'),
    (re.compile(r'显存没报警'), u'机器没告警', u'显存没报警'),
    (re.compile(r'显存优化'), u'手艺打磨', u'显存优化'),
    (re.compile(r'显存这东西'), u'这点余量', u'显存这东西'),
    (re.compile(r'显存'), u'算力', u'显存（兜底）'),
    (re.compile(r'VRAM'), u'余量', u'VRAM'),
    (re.compile(r'旧的?显卡'), u'老机器', u'显卡'),
    (re.compile(r'块显卡'), u'台机器', u'块显卡'),
    (re.compile(r'像素显卡'), u'像素机', u'像素显卡'),
    (re.compile(r'显卡'), u'机器', u'显卡（兜底）'),
    (re.compile(r'GPU'), u'老机器', u'GPU'),
    # --- 机队 -> 机房（城市里机房是合理场所）---
    (re.compile(r'机队(\w?)的?舱口'), u'机房\\1门口', u'机队舱口'),
    (re.compile(r'机队C'), u'机房C', u'机队C'),
    (re.compile(r'机队'), u'机房', u'机队（兜底）'),
    # --- 内部码：S 版本号 ---
    (re.compile(r'(?<![A-Za-z0-9-])S\d\.\d(?![0-9])'), u'新版本', u'S2.5 版本号'),
    (re.compile(r'(?<![A-Za-z0-9-])S\d(?![.\d])'), u'新版本', u'S1 版本号'),
    # --- 内部码：P02-W02 工位 ---
    (re.compile(r'(?<![A-Za-z0-9-])P\d{2}\s*[-—]\s*W\d{2}(?![0-9])'), u'那片工位', u'P02-W02 工位'),
    (re.compile(r'(?<![A-Za-z0-9-])P\d{2}(?![0-9])'), u'那片工位', u'P02 工位'),
    # --- 内部码：B/G/P 楼号（正典=游戏楼/楼栋）---
    (re.compile(r'(?<![A-Za-z0-9-])B\d{3,5}(?![0-9])'), u'老楼', u'B2396 类外仓编号'),
    (re.compile(r'(?<![A-Za-z0-9-])G\d{2,3}(?![0-9])\s*楼'), u'游戏楼', u'G08楼'),
    (re.compile(r'(?<![A-Za-z0-9-])G\d{2,3}(?![0-9])'), u'游戏楼', u'G08 类楼号'),
    (re.compile(r'(?<![A-Za-z0-9-])P0\s*按钮族'), u'最要紧的按钮', u'P0按钮族'),
    (re.compile(r'(?<![A-Za-z0-9-])P0(?![0-9])'), u'头等要紧', u'P0 优先级'),
    (re.compile(r'(?<![A-Za-z0-9])T\d{3,4}(?![0-9])'), u'那档子事', u'T#### 内部任务号'),
]

# 改写后收拾残渣（整串删除留下的空壳）
POST = [
    (u'，。', u'。'), (u'。，', u'。'), (u'，，', u'，'), (u'、，', u'，'),
    (u'，、', u'，'), (u'：，', u'：'), (u'——，', u'——'), (u'，——', u'——'),
    (u'“”', u''), (u'「」', u''), (u'（）', u''), (u'  ', u' '),
    (u'游戏楼楼', u'游戏楼'), (u'老楼楼', u'老楼'),
    (u'老老机器', u'老机器'), (u'老老楼', u'老楼'), (u'那片工位那', u'那片工位'),
    (u'新版本-那档子事', u'新版本那档子事'),
    (u'新版本-', u'新版本'), (u'-那档子事', u'那档子事'),
]


def tidy(s):
    for a, b in POST:
        if a == b:            # 防御：自反替换会让 while 永不退出
            continue
        while a in s:
            nxt = s.replace(a, b)
            if nxt == s:
                break
            s = nxt
    # 替换点在原文两侧带空格时，会留下「核对完 游戏楼 的流水」这类汉字夹缝空格
    s = re.sub(r'(?<=[\u4e00-\u9fff])[ \t]+(?=[\u4e00-\u9fff])', '', s)
    s = re.sub(r'[ \t]+(?=[：，、；。！？」”])', '', s)
    s = re.sub(r'(?<=[：，、；。！？])[ \t]+', '', s)
    s = re.sub(r'——(?=[。，、；：」])', u'', s)
    s = re.sub(r'^[ \t]*[，、]', u'', s)
    return s


def detox_line(line):
    """对一条年轮行做映射；返回 (新行, 改动条数)。"""
    s = line
    hits = 0
    for rx, repl, _tag in MAPS:
        new = rx.sub(repl, s)
        if new != s:
            hits += 1
            s = new
    if not hits:
        return line, 0
    s = tidy(s)
    return s, hits


def ring_lines_with_span(text):
    """产 (行索引, 原文) —— 只取 **年轮** 块内的年轮行。"""
    lines = text.split('\n')
    in_rings = False
    for i, l in enumerate(lines):
        if l.startswith('**年轮**'):
            in_rings = True
            continue
        if in_rings and l.startswith('**'):
            in_rings = False
        if in_rings and l.startswith('- 20'):
            yield i, l


def card_paths():
    for d, _, fs in os.walk(REG):
        for f in sorted(fs):
            if f.endswith('.md') and f.startswith('C-'):
                yield os.path.join(d, f)


def scan(apply=False):
    """遍历全部卡：返回 [(rel, old, new, hits, residual)]。
    residual=改写后仍命中判据的 token 列表（>0 说明该行映射不全）。"""
    rows = []
    for p in card_paths():
        rel = os.path.relpath(p, ROOT).replace('\\', '/')
        with io.open(p, encoding='utf-8') as f:
            text = f.read()
        lines = text.split('\n')
        dirty = False
        for i, line in ring_lines_with_span(text):
            toks = []
            for _k, rx in FACE2:
                toks += rx.findall(line)
            if not toks:
                continue
            new, hits = detox_line(line)
            if new == line:
                rows.append((rel, line, '', 0, sorted(set(toks))))
                continue
            residual = []
            for _k, rx in FACE2:
                residual += rx.findall(new)
            rows.append((rel, line, new, hits, sorted(set(residual))))
            if hits and not residual:
                lines[i] = new
                dirty = True
        if apply and dirty:
            with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(lines))
    return rows


def write_report(rows, path):
    clean = [r for r in rows if r[2] and not r[4]]
    partial = [r for r in rows if r[2] and r[4]]
    untouched = [r for r in rows if not r[2]]
    out = [
        u'# 年轮清污对照表（%s）' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        u'',
        u'判据与 `Tools/ring_lint.py` 同源。映射表见 `Tools/ring_detox.py` MAPS（人工审定）。',
        u'',
        u'- 可安全改写（映射全覆盖、复核零残留）：**%d** 行' % len(clean),
        u'- 部分改写（仍有残留，不落盘）：**%d** 行' % len(partial),
        u'- 映射未命中（须人/LLM 逐条重写）：**%d** 行' % len(untouched),
        u'',
        u'## 一、可安全改写',
        u'',
    ]
    for rel, old, new, _h, _r in clean:
        out.append(u'### ' + rel)
        out.append(u'OLD: ' + old)
        out.append(u'NEW: ' + new)
        out.append(u'')
    out += [u'## 二、部分改写（需补映射）', u'']
    for rel, old, new, _h, res in partial:
        out.append(u'### %s  [残留: %s]' % (rel, u'/'.join(res)))
        out.append(u'OLD: ' + old)
        out.append(u'NEW: ' + new)
        out.append(u'')
    out += [u'## 三、映射未命中', u'']
    for rel, old, _n, _h, res in untouched:
        out.append(u'- `%s` [%s] %s' % (rel, u'/'.join(res), old[:100]))
    io.open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out) + u'\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', default=None)
    args = ap.parse_args()

    rows = scan(apply=args.apply)
    clean = [r for r in rows if r[2] and not r[4]]
    partial = [r for r in rows if r[2] and r[4]]
    untouched = [r for r in rows if not r[2]]
    mode = 'APPLIED' if args.apply else 'DRY-RUN'
    print('%s total=%d clean=%d partial=%d untouched=%d'
          % (mode, len(rows), len(clean), len(partial), len(untouched)))
    if args.report:
        write_report(rows, args.report)
        print('report=' + args.report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
