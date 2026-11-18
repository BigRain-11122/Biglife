# -*- coding: utf-8 -*-
"""停更居民诊断：为什么 813 人自 10-24 起再没写过新年轮。

只读，不改任何数据。三问：
  1. 他们还在不在语料索引（due_citizens 的 id 全集来源）？
  2. 他们的游标（state/evolve-cursor.json）里 next 是哪天、last 是哪天？
  3. 他们在 registry 还是 anchors（anchors 是展示级锚，可能本就不进演化）？

用法：python -X utf8 Tools/diag_stale.py [--days 15] [--top 12]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census", "registry")
ANCHORS = os.path.join(CO, "census", "anchors")
CURSOR = os.path.join(CO, "state", "evolve-cursor.json")
DB = os.path.join(CO, "state", "corpus.db")
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「", re.M)


def scan(days):
    out = {}
    for base, tag in ((CENSUS, "registry"), (ANCHORS, "anchors")):
        if not os.path.isdir(base):
            continue
        for root, _, fs in os.walk(base):
            for f in fs:
                if not (f.startswith("C-") and f.endswith(".md")):
                    continue
                p = os.path.join(root, f)
                try:
                    with open(p, encoding="utf-8") as fh:
                        dates = RING_RE.findall(fh.read())
                except OSError:
                    continue
                last = max(dates) if dates else ""
                out[f[:-3]] = (last, tag, len(dates))
    t = dt.date.today()
    stale = []
    for cid, (last, tag, n) in out.items():
        if not last:
            stale.append((9999, cid, "-", tag, n))
            continue
        try:
            d = (t - dt.date.fromisoformat(last)).days
        except ValueError:
            continue
        if d >= days:
            stale.append((d, cid, last, tag, n))
    stale.sort(reverse=True)
    return out, stale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=15)
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    allc, stale = scan(a.days)
    print("档案总数 %d · 停更 ≥%d 天 %d 人" % (len(allc), a.days, len(stale)))

    by_tag = {}
    for d, cid, last, tag, n in stale:
        by_tag[tag] = by_tag.get(tag, 0) + 1
    print("按目录：%s" % by_tag)

    # 语料索引覆盖
    ids = set()
    if os.path.exists(DB):
        con = sqlite3.connect(DB)
        try:
            ids = {r[0] for r in con.execute("SELECT id FROM citizens")}
        finally:
            con.close()
    print("语料索引 citizens=%d" % len(ids))
    missing = [cid for _, cid, _, _, _ in stale if cid not in ids]
    print("停更者不在索引里的：%d 人（在索引 %d / 不在 %d）" % (
        len(missing), len(stale) - len(missing), len(missing)))

    cur = {}
    if os.path.isfile(CURSOR):
        try:
            with open(CURSOR, encoding="utf-8") as fh:
                cur = json.load(fh)
        except Exception as exc:  # noqa: BLE001
            print("游标读取失败：%s" % exc)
    print("游标条目 %d" % len(cur))
    have = sum(1 for _, cid, _, _, _ in stale if cid in cur)
    print("停更者在游标里的：%d / %d" % (have, len(stale)))

    print("\n最久未更新的 %d 位：" % a.top)
    for d, cid, last, tag, n in stale[:a.top]:
        c = cur.get(cid) or {}
        print("  %-8s 停 %4s 天  最后 %s  圈 %d  %-8s 游标 last=%s next=%s" % (
            cid, d if d != 9999 else "无圈", last, n, tag,
            c.get("last", "-"), c.get("next", "-")))

    # 游标 next 是否长期过期（说明该被反复抽到却没成功）
    over = [cid for _, cid, _, _, _ in stale
            if (cur.get(cid) or {}).get("next") and cur[cid]["next"] < dt.date.today().isoformat()]
    print("\n游标 next 已过期（本该被抽到）：%d 人" % len(over))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
