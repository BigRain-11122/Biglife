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


CACHE = os.path.join(CO, "state", "reconcile.json")
CACHE_TTL = 300          # 秒；1 万张卡扫一遍约 8 秒，泵一轮可能问 20 次


def _covered_cards(day):
    """卡片真相：直接读卡面有没有当天年轮（export 会滞后，不能用它当判据）。

    2026-11-20 实测：export 说缺口 45，卡面真相 105——差的 60 人是"写了没导出"
    与"游标说已服务但卡上没有"两类，只看 export 会把真缺口藏掉。
    """
    import re
    pat = re.compile(r"^- %s " % day, re.M)
    reg = os.path.join(CO, "census", "registry")
    covered, seen = set(), set()
    for root, _, fs in os.walk(reg):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            seen.add(f[:-3])
            try:
                with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                    if pat.search(fh.read()):
                        covered.add(f[:-3])
            except OSError:
                pass
    # 目标态只用 registry 里的真居民；census/anchors 是展示卡，不该算缺口
    # （2026-11-20 实测：按 corpus.db 全集算，会多出 21 个 anchors 永远补不完）。
    return covered, seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="忽略缓存，强制重扫卡面")
    a = ap.parse_args()
    day = datetime.date.today().isoformat()
    cov = None
    universe = None
    if not a.fresh:
        try:
            with open(CACHE, encoding="utf-8") as fh:
                c = json.load(fh)
            if c.get("day") == day and (datetime.datetime.now().timestamp() - c.get("ts", 0)) < CACHE_TTL:
                cov = set(c.get("covered") or [])
                universe = set(c.get("universe") or []) or None
        except (OSError, ValueError):
            cov = None
    if cov is None or universe is None:
        cov, universe = _covered_cards(day)
        try:
            with open(CACHE, "w", encoding="utf-8") as fh:
                json.dump({"day": day, "ts": datetime.datetime.now().timestamp(),
                           "covered": sorted(cov), "universe": sorted(universe)},
                          fh, ensure_ascii=False)
        except OSError:
            pass
    ids = sorted(universe)
    missing = [i for i in ids if i and i not in cov]
    if a.json:
        print(json.dumps({"day": day, "total": len(ids), "covered": len(cov),
                          "deficit": len(missing)}, ensure_ascii=False))
        return 0 if not missing else 2
    if a.ids:
        print(" ".join(missing[:a.ids]))
        return 0 if not missing else 2
    print("%s 目标 %d / 实测 %d / 缺口 %d" % (day, len(ids), len(cov), len(missing)))
    if missing:
        print("缺口样例:", " ".join(missing[:12]))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
