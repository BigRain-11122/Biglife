#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""relations_manifest.py v1.0 — 关系面 manifest（T-20260925-09 分步②·契约=R209 认领行判据先行）

三源→一面（纯解析确定性·零 LLM·只读 census 卡面+年轮·FluxVerse 零触碰）：
  ① 家户共址 rel=household：卡面「关系」字段「家户 H-*（描述）」同 H 号跨卡两两成对（src=H 号）
     ——判据③零编造规则：双成员描述均非「独居」才成对（独居=卡面自否认同户；P-0 批次
     6 巨型家户 H-GM1137/H-QT2251/H-MD1660/H-NS0498/H-OR0229/H-RV2371 共 4578 成员
     99.7% 自标独居=家户位复用瑕疵，同户对将与卡面直接矛盾故排除·缺描述词=无否认照常成对）
  ② 街区共域 rel=block：卡头「城区」字段值全串等值跨卡两两成对（字段与「物种」同行以 ｜ 分隔、
     值含街区段=同街区；荣誉席卡头自注「不入城区分布」→ 排除·人设权保守面；src=街区名=末段）
  ③ 年轮互链 rel=meet：年轮行「与 C-* 相遇」跨卡互引（单向提及亦记·双向互引去重成单行·src=最早日期）

输出 census/export/citizen-relations.jsonl（R3 再生面·gitignored）：
  行型 {a,b,rel,src} · a<b 规范对序 · (a,rel,b) 主键去重 · (a,rel,b) 升序确定性排序

审判据：①纯解析确定性零 LLM ②同输入双跑逐字节一致（MD5）③关系零编造（三源外零数据源·
  H/C 号域校验·a<b 对偶自反不重复成行）④QC 门（schema 白名单+rel 闭集+引用 ID 存在性全查+
  排序不降+相邻去重+组内共域复核 bad=0·--qc 含 disk==re-derive 逐字节复核）
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS_DIR = os.path.join(ROOT, 'census')
OUT_PATH = os.path.join(ROOT, 'census', 'export', 'citizen-relations.jsonl')

DISTRICT_PREFIX = '**城区**'
RELATION_PREFIX = '**关系**'
H_RE = re.compile(r'家户 (H-[A-Z0-9]+)(?:（([^）]*)）)?')
MEET_RE = re.compile(r'与 (C-\d{5}) 相遇')
RING_RE = re.compile(r'^- (\d{4}-\d{2}-\d{2}) ')
CID_RE = re.compile(r'^C-\d{5}$')
REL_SET = ('block', 'household', 'meet')  # 闭集（升序=发射序）
ALONE_DESC = '独居'


def load_cards():
    """只读解析全部户籍卡（含 census/reserved/ 荣誉席）→ {cid: {district, household, alone, meets}}"""
    cards = {}
    for path in sorted(glob.glob(os.path.join(CENSUS_DIR, '**', 'C-*.md'), recursive=True)):
        cid = os.path.splitext(os.path.basename(path))[0]
        if not CID_RE.match(cid):
            continue
        district = None
        household = None
        alone = False
        meets = []
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                s = line.strip()
                if DISTRICT_PREFIX in s:  # 「城区」与「物种」同行（｜ 分隔）→ 取字段后段
                    district = s.split(DISTRICT_PREFIX, 1)[1].strip()
                elif s.startswith(RELATION_PREFIX):
                    m = H_RE.search(s)
                    if m:
                        household = m.group(1)
                        alone = (m.group(2) or '') == ALONE_DESC
                elif RING_RE.match(s):
                    dm = MEET_RE.search(s)
                    if dm:
                        date = RING_RE.match(s).group(1)
                        other = dm.group(1)
                        if other != cid:
                            meets.append((other, date))
        cards[cid] = {'district': district, 'household': household, 'alone': alone, 'meets': meets}
    return cards


def block_name(district_value):
    """街区名=卡头「城区」字段值末段（无 ' · ' 分隔则整值）。荣誉席自注→None=不入 block 源。"""
    if not district_value or '荣誉席' in district_value:
        return None
    parts = [p.strip() for p in district_value.split(' · ')]
    return parts[-1] if parts else district_value


def derive_rows(cards):
    """按 (a, rel, b) 升序流式产出 (a, b, rel, src)——不全局物化（万卡街区对 ~2.4M 行控内存）。

    a 升序外层；rel 按 REL_SET 序（block/household/meet）；每源内 b 升序。
    """
    ids = sorted(cards)
    hh_groups = {}
    blk_groups = {}
    for cid in ids:
        c = cards[cid]
        if c['household'] and not c['alone']:  # 独居=卡面自否认同户（判据③）
            hh_groups.setdefault(c['household'], []).append(cid)
        bn = block_name(c['district'])
        if bn:
            blk_groups.setdefault(bn, []).append(cid)

    # 组内成对：仅发射 b>a 的一半（a<b 对偶自反·不重复成行）
    hh_pairs = {}   # a -> [b...]
    blk_pairs = {}
    for members in hh_groups.values():
        for i, a in enumerate(members):
            hh_pairs.setdefault(a, []).extend(members[i + 1:])
    for members in blk_groups.values():
        for i, a in enumerate(members):
            blk_pairs.setdefault(a, []).extend(members[i + 1:])

    # meet：双向提及合并→(a,b) 最早日期；单向提及亦记
    meet_pairs = {}
    for cid in ids:
        for other, date in cards[cid]['meets']:
            a, b = (cid, other) if cid < other else (other, cid)
            key = (a, b)
            if key not in meet_pairs or date < meet_pairs[key]:
                meet_pairs[key] = date
    mt_pairs = {}
    for (a, b), date in meet_pairs.items():
        mt_pairs.setdefault(a, []).append((b, date))

    for a in ids:
        emit = []
        for b in sorted(blk_pairs.get(a, ())):
            emit.append(('block', b, block_name(cards[a]['district'])))
        for b in sorted(hh_pairs.get(a, ())):
            emit.append(('household', b, cards[a]['household']))
        for b, date in sorted(mt_pairs.get(a, ())):
            emit.append(('meet', b, date))
        # rel 发射序=REL_SET（block<household<meet 与逐源 b 升序天然满足 (a,rel,b) 全序）
        for rel, b, src in emit:
            yield a, b, rel, src


def serialize(rows):
    cache = {}
    for a, b, rel, src in rows:
        sj = cache.get(src)
        if sj is None:
            sj = json.dumps(src, ensure_ascii=False)
            cache[src] = sj
        yield '{"a":"%s","b":"%s","rel":"%s","src":%s}\n' % (a, b, rel, sj)


def derive_md5(cards):
    h = hashlib.md5()
    n = 0
    for chunk in serialize(derive_rows(cards)):
        h.update(chunk.encode('utf-8'))
        n += 1
    return h.hexdigest(), n


def cmd_run(cards):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    stats = {'block': 0, 'household': 0, 'meet': 0}
    with open(OUT_PATH, 'w', encoding='utf-8', newline='\n') as fh:
        for chunk in serialize(derive_rows(cards)):
            fh.write(chunk)
            stats[chunk.split('"rel":"', 1)[1].split('"', 1)[0]] += 1
    md5, total = derive_md5(cards)  # 双跑第二遍=判据②（同输入双跑一致由 --qc 复核落锤）
    print('relations rows=%d block=%d household=%d meet=%d md5=%s' %
          (sum(stats.values()), stats['block'], stats['household'], stats['meet'], md5))
    print('written:', os.path.relpath(OUT_PATH, ROOT))


def cmd_qc(cards):
    bad = 0
    # 判据②：内存双跑 MD5 一致
    m1, n1 = derive_md5(cards)
    m2, n2 = derive_md5(cards)
    if m1 != m2 or n1 != n2:
        bad += 1
        print('QC FAIL: double-run mismatch %s/%s %d/%d' % (m1, m2, n1, n2))
    # disk == re-derive
    if not os.path.exists(OUT_PATH):
        print('QC FAIL: output missing')
        return 1
    h = hashlib.md5()
    rows = 0
    with open(OUT_PATH, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    if h.hexdigest() != m1:
        bad += 1
        print('QC FAIL: disk != re-derive (%s vs %s)' % (h.hexdigest(), m1))
    # 判据④：schema/闭集/存在性/排序/相邻去重/组内共域复核
    prev_key = None
    with open(OUT_PATH, encoding='utf-8') as fh:
        for line in fh:
            rows += 1
            try:
                r = json.loads(line)
            except Exception:
                bad += 1
                continue
            if sorted(r.keys()) != ['a', 'b', 'rel', 'src']:
                bad += 1
                continue
            a, b, rel, src = r['a'], r['b'], r['rel'], r['src']
            if rel not in REL_SET or not CID_RE.match(a) or not CID_RE.match(b) or not a < b:
                bad += 1
                continue
            if a not in cards or b not in cards:
                bad += 1
                continue
            key = (a, rel, b)
            if prev_key is not None and key <= prev_key:
                bad += 1  # 排序降序或相邻重复
                continue
            prev_key = key
            ca, cb = cards[a], cards[b]
            if rel == 'block':
                if block_name(ca['district']) != src or block_name(cb['district']) != src:
                    bad += 1
            elif rel == 'household':
                if ca['household'] != src or cb['household'] != src or ca['alone'] or cb['alone']:
                    bad += 1
            else:  # meet
                ok = any(o == b and d == src for o, d in ca['meets']) or \
                     any(o == a and d == src for o, d in cb['meets'])
                if not ok:
                    bad += 1
    print('QC rows=%d derived=%d bad=%d double_run=%s' % (rows, n1, bad, 'OK' if m1 == m2 else 'FAIL'))
    print('QC %s' % ('PASS' if bad == 0 and rows == n1 else 'FAIL'))
    return 0 if bad == 0 and rows == n1 else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--qc', action='store_true', help='run QC gate (double-run MD5 + full row scan)')
    args = ap.parse_args()
    cards = load_cards()
    if not cards:
        print('no cards found', file=sys.stderr)
        return 1
    if args.qc:
        return cmd_qc(cards)
    cmd_run(cards)
    return 0


if __name__ == '__main__':
    sys.exit(main())
