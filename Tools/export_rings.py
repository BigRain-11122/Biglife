# -*- coding: utf-8 -*-
"""年轮消费接口：把「写进 md 的年轮」变成下游能直接吃的机器可读流。

Why（CEO 2026-11-17「一定用的上」）：
  年轮现在只落在 census/registry/*.md 和 citizens-light 的 recent_ring（每人只留最新 1 条）。
  下游要用「今天城里发生了什么」时，没有稳定入口——要么读 10111 个 md（慢），要么只有
  每人一条（丢了跨人的时间线）。本脚本提供两个面：

    census/export/today-rings.jsonl   当日全量（覆盖写，一行一条，按 cid 排序）
    census/export/rings-ledger.jsonl  累计 append（按 (cid,date) 去重，供回溯/训练）

 字段：date / cid / name / district / profession / species / ring / chars
 数据源：state/corpus.db（秒查；缺失时退回扫 registry）

用法：
  python -X utf8 Tools/export_rings.py              # 导出今日
  python -X utf8 Tools/export_rings.py --date 2026-11-17
  python -X utf8 Tools/export_rings.py --since 2026-11-10   # 补导历史进 ledger
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
EXPORT = os.path.join(CO, "census", "export")
DB = os.path.join(CO, "state", "corpus.db")
TODAY_OUT = os.path.join(EXPORT, "today-rings.jsonl")
LEDGER = os.path.join(EXPORT, "rings-ledger.jsonl")

NAME_RE = re.compile(r"^#\s*(C-\d+)\s+(.+)$")
LIGHT = os.path.join(EXPORT, "citizens-light.jsonl")


def load_names():
    """从 light 面取 id->name（下游展示用，缺失就留空）。"""
    names = {}
    try:
        with open(LIGHT, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    names[o.get("id", "")] = o.get("name", "")
                except ValueError:
                    continue
    except OSError:
        pass
    return names


def rows_from_db(date=None, since=None):
    if not os.path.exists(DB):
        return []
    con = sqlite3.connect(DB)
    try:
        sql = ("SELECT r.date, r.cid, c.district, c.prof, c.species, r.text "
               "FROM rings r JOIN citizens c ON c.id = r.cid WHERE 1=1")
        args = []
        if date:
            sql += " AND r.date = ?"
            args.append(date)
        if since:
            sql += " AND r.date >= ?"
            args.append(since)
        sql += " ORDER BY r.date, r.cid"
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


def write_today(rows, names, day):
    tmp = TODAY_OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for d, cid, dist, prof, species, text in rows:
            f.write(json.dumps({
                "date": d, "cid": cid, "name": names.get(cid, ""),
                "district": dist or "", "profession": prof or "",
                "species": species or "", "ring": text,
                "chars": len(text),
            }, ensure_ascii=False) + "\n")
    os.replace(tmp, TODAY_OUT)
    print("today-rings: %d 条 -> %s" % (len(rows), TODAY_OUT))


def append_ledger(rows, names):
    """按 (cid,date) 去重追加，供回溯与训练取用。"""
    seen = set()
    if os.path.exists(LEDGER):
        try:
            with open(LEDGER, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        o = json.loads(line)
                        seen.add((o.get("cid"), o.get("date")))
                    except ValueError:
                        continue
        except OSError:
            pass
    added = 0
    with open(LEDGER, "a", encoding="utf-8") as f:
        for d, cid, dist, prof, species, text in rows:
            if (cid, d) in seen:
                continue
            f.write(json.dumps({
                "date": d, "cid": cid, "name": names.get(cid, ""),
                "district": dist or "", "profession": prof or "",
                "species": species or "", "ring": text,
                "chars": len(text),
            }, ensure_ascii=False) + "\n")
            seen.add((cid, d))
            added += 1
    print("rings-ledger: +%d 条（累计 %d）" % (added, len(seen)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--since")
    a = ap.parse_args()
    os.makedirs(EXPORT, exist_ok=True)
    names = load_names()
    if a.since:
        rows = rows_from_db(since=a.since)
        append_ledger(rows, names)
        return 0
    rows = rows_from_db(date=a.date)
    if not rows:
        print("no rings for %s (corpus.db 可能未建: 先跑 corpus_index.py --build)" % a.date)
        return 0
    write_today(rows, names, a.date)
    if a.date == datetime.date.today().isoformat():
        append_ledger(rows, names)
    return 0


if __name__ == "__main__":
    sys.exit(main())
