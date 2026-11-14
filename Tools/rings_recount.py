#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rings_recount.py - 年轮计数对账面（单一事实源，终结计数口径口水仗）。

背景：R3042→R3043→R3044 三度出现「心跳 rings_today / 卡面行数 / 居民数 / 看板数」
四个数字不相等，被当成写盘缺陷反复立案。实读后成因有三类，全部是可解释的
口径差而不是丢写：

1. 时刻差 — 心跳行是某一时刻的快照，之后交互会话继续落环（本账打印心跳行
   的时刻与数字，与当刻机器直数的差=快照后新增）。
2. 行数≠居民数 — 同一居民当日可落多轮年轮（软闸放行/相遇双写），行数必然
   ≥ 卡数，差额=多环居民数。
3. 谓词差 — 心跳谓词要求行首 "- <今日>" 且含 "[锚]"、且排除 "V2-B 反思层"
   （见 update_status_export.count_rings）。绕过谓词裸数行首会把反思层/
   缺锚行算进来，凭空造出差额。

本工具零 LLM、只读：按各口径分别直数并打印一张对账表，最后给出机器直数
与心跳行的差及判定（OK=与最近一轮落环数吻合 / DRIFT=需要人看）。退出码
恒 0（除 IO 异常），因为它是账面工具不是门禁。
Usage: python -X utf8 rings_recount.py [--today 2026-11-15]
"""
import argparse, datetime, glob, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEARTBEAT = os.path.join(ROOT, "state", "heartbeat.txt")
RING_PREFIX = "- %s"
EXCLUDE = "V2-B 反思层"


def _walk_md(root):
    for base, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(".md"):
                yield os.path.join(base, fn)


def scan(dirpath, today):
    """返回 (锚行数, 带锚卡数, 裸行数, 裸卡数)。"""
    anch_lines = anch_cards = bare_lines = bare_cards = 0
    for p in _walk_md(dirpath):
        a = b = 0
        with io.open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if not line.startswith(RING_PREFIX % today):
                    continue
                b += 1
                if "[锚]" in line and EXCLUDE not in line:
                    a += 1
        if a:
            anch_cards += 1
            anch_lines += a
        if b:
            bare_cards += 1
            bare_lines += b
    return anch_lines, anch_cards, bare_lines, bare_cards


def last_heartbeat_rings():
    """读心跳尾部的 rings_today=<n> 行 -> (数字, 原始行)。"""
    if not os.path.exists(HEARTBEAT):
        return None, ""
    hit = (None, "")
    with io.open(HEARTBEAT, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.search(r"rings_today=(\d+)", line)
            if m:
                hit = (int(m.group(1)), line.strip())
    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    args = ap.parse_args()
    today = args.today

    reg = scan(os.path.join(ROOT, "census", "registry"), today)
    anc = scan(os.path.join(ROOT, "census", "anchors"), today)
    machine_lines = reg[0] + anc[0]
    machine_cards = reg[1] + anc[1]
    bare_lines = reg[2] + anc[2]
    bare_cards = reg[3] + anc[3]

    hb_val, hb_line = last_heartbeat_rings()

    print("== rings_recount (%s) ==" % today)
    print("registry  锚行=%d 卡=%d | 裸行=%d 卡=%d" % reg)
    print("anchors   锚行=%d 卡=%d | 裸行=%d 卡=%d" % anc)
    print("机器直数(心跳谓词)  行=%d 居民=%d  多环居民=%d"
          % (machine_lines, machine_cards, machine_lines - machine_cards))
    print("裸行首谓词         行=%d 居民=%d  谓词虚增=%d"
          % (bare_lines, bare_cards, bare_lines - machine_lines))
    if hb_line:
        print("心跳行  %s" % hb_line)
    if hb_val is None:
        print("verdict: NO-HEARTBEAT")
        return 0

    delta = machine_lines - hb_val
    if delta < 0:
        verdict = "DRIFT-NEGATIVE (心跳大于实测 -> 心跳写错或卡被回退)"
    elif delta == 0:
        verdict = "OK (与心跳同刻一致)"
    elif delta <= 20:
        verdict = "OK (心跳快照后新增 %d 环，属时刻差)" % delta
    else:
        verdict = "CHECK (差 %d 过大，比对心跳时刻与写盘 mtime)" % delta
    print("心跳 vs 实测: 实测-心跳=%+d -> %s" % (delta, verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
