#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_interchat.py - 互聊台账日更 wrapper v0 (T-20261112-03 修法②).

病根 = interchat_ledger.py 需外部喂源（--feed-rumor/--event-text），
无任何轮次引用 → cognition/interchat-ledger.jsonl 停更 16.8 天无人发现。
本件把「取当日流言产物作喂源」这段确定性黏合固化成一条命令，
供 Tools/round_daily.py 的 input 档按 dated 路径调用。

判据（T-20261112-03 验收）:
  连续 3 生产日 ledger 尾部 date=当日 且 --qc PASS；单轮 LLM/GPU 调用 0。
无源诚实律: 当日 rumors 文件缺失或首行无 chain = 静默跳过 rc=0（不造假源、不补写）。
幂等: 底层 append_rows 行级去重，复跑零新增。
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import interchat_ledger as IL  # noqa: E402  (垫话闭集单源律: 经它导入 rumor_chain)

RUMOR_DIR = os.path.join(ROOT, "cognition", "rumors")


def today():
    try:
        import datetime
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    except Exception:
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d")


def load_seed(date):
    """取当日流言产物首条含 chain 的行。返回 (row, reason) 或 (None, reason)。"""
    path = os.path.join(RUMOR_DIR, "rumors-%s.jsonl" % date)
    if not os.path.exists(path):
        return None, "no_source:%s" % path
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if isinstance(o.get("chain"), dict) and o["chain"].get("hops"):
                return o, "ok:%s" % path
    return None, "empty_chain:%s" % path


def main():
    ap = argparse.ArgumentParser(description="互聊台账日更 wrapper（零 LLM 确定性派生）")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD（缺省=北京时间今天）")
    ap.add_argument("--dry-run", action="store_true", help="只报增量零写盘")
    ap.add_argument("--qc", action="store_true", help="转调 interchat_ledger --qc")
    args = ap.parse_args()

    if args.qc:
        IL.qc()
        return

    date = args.date or today()
    seed_row, reason = load_seed(date)
    if seed_row is None:
        print("daily_interchat: SKIP %s (诚实律: 无源不造)" % reason)
        return

    chain = seed_row["chain"]
    event_text = seed_row.get("text") or ""
    if not event_text:
        print("daily_interchat: SKIP empty_origin_text (字符集门无基)")
        return

    rows = IL.scan_meet_rings()
    n_meet = len(rows)
    try:
        rows += IL.rumor_rows(chain, event_text)
    except ValueError as e:
        print("daily_interchat: SKIP rumor_rows rejected (%s)" % e)
        return
    n_rumor = len(rows) - n_meet

    ids = IL.load_light_ids()
    for r in rows:
        for p in r["participants"]:
            if p not in ids:
                sys.exit("error: 参与者不在 census 导出面: %s" % p)

    if args.dry_run:
        existing = set()
        if os.path.exists(IL.LEDGER):
            with open(IL.LEDGER, encoding="utf-8") as f:
                existing = {l.rstrip("\n") for l in f}
        fresh = [j for j in (IL.row_json(r) for r in rows) if j not in existing]
        print("dry-run %s: meet_ring=%d rumor_hop=%d fresh=%d"
              % (date, n_meet, n_rumor, len(fresh)))
        return

    IL.append_rows(rows)
    # mtime 语义（诚实标注）= 「本生产日已用真实源核对过」而非「内容有变化」：
    # 幂等空跑（当日已追加过）不写盘，若不刷新 mtime，round_daily 的 data 档
    # 每轮都会判 stale 并重跑。只在源真实存在且校验通过时刷新，无源路径
    # 走上方 SKIP 分支不触发 → 源断供时仍能如实暴露 stale。
    if os.path.exists(IL.LEDGER) and not args.dry_run:
        os.utime(IL.LEDGER, None)
    print("date=%s meet_ring=%d rumor_hop=%d source_ref=%s"
          % (date, n_meet, n_rumor, chain.get("event_id")))


if __name__ == "__main__":
    main()
