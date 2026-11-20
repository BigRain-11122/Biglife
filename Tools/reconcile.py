# -*- coding: utf-8 -*-
"""reconcile.py — 产出拉齐器（desired-state 而不是 opportunistic）。

CEO 2026-11-20：「每次都说得好，实际不是出问题就是摸鱼，或者自动化停了。
从根本上解决，列一个不断拉齐的自动化任务」。

病根不在某个 bug，在结构：内容面各自判断"我有没有活"，都说没有就 NO-WORK，
于是机器空转——**没有人对"今天每人是否都有一条年轮"这个不变量负责**。
本工具就是那个负责人：只算差值，不讲理由。

  目标态：今天有环的居民数 == 居民总数
  实测态：census/export/today-rings.jsonl 里今天的 cid 去重计数
  差值 > 0 → 输出缺口 id（最多 --limit 条），退出码 2
  差值 = 0 → 退出码 0

用法：
  python -X utf8 Tools/reconcile.py            # 打印缺口数与前若干 id
  python -X utf8 Tools/reconcile.py --ids 24   # 只打印 id（空白分隔，供 --force 用）
  python -X utf8 Tools/reconcile.py --json
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
DB = os.path.join(CO, "state", "corpus.db")
TODAY_JSONL = os.path.join(CO, "census", "export", "today-rings.jsonl")


def _all_ids():
    try:
        con = sqlite3.connect(DB)
        try:
            return [r[0] for r in con.execute("SELECT id FROM citizens")]
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        return []


def _covered(day):
    out = set()
    try:
        with open(TODAY_JSONL, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                if '"date": "%s"' % day in ln or '"date":"%s"' % day in ln:
                    try:
                        out.add(json.loads(ln).get("cid"))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    day = datetime.date.today().isoformat()
    ids = _all_ids()
    cov = _covered(day)
    missing = [i for i in ids if i and i not in cov]
    if a.json:
        print(json.dumps({"day": day, "total": len(ids), "covered": len(ids) - len(missing),
                          "deficit": len(missing)}, ensure_ascii=False))
        return 0 if not missing else 2
    if a.ids:
        print(" ".join(missing[:a.ids]))
        return 0 if not missing else 2
    print("%s 目标 %d / 实测 %d / 缺口 %d" % (day, len(ids), len(ids) - len(missing), len(missing)))
    if missing:
        print("缺口样例:", " ".join(missing[:12]))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
