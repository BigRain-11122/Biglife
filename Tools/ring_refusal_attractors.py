#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""拒稿开口吸引子读数（跨席传染面的可执行基线）

为什么要有这个工具：
`state/ring-refusals.jsonl` 是落环侧硬拒的 append-only 账本。仅看条数无法回答
「这些拒稿里有多少是同一句话被不同居民各撞一次」——而这正是 2026-11-16 定谳的
跨席传染面（R3204/R3205）。19:00 配额闸实弹负控需要**同一口径的前后两读数**：
闸前基线（本工具 --window 12）与闸后复测，否则「命中 N 次」无法判是否有改善。

口径（与 qc/evolve 逐字闸同法，勿改）：
- 键=opening12（落环侧已截断的开头 12 字，账本自带，不重算）；
- 同一 str 计 1 次；multi = 出现次数 >= 2 的开口；
- cross_cids = 该开口下的**不同**居民数（同一人重试循环与跨席传播分开看）。

用法：
  python -X utf8 Tools/ring_refusal_attractors.py                 # 默认 24h 窗口
  python -X utf8 Tools/ring_refusal_attractors.py --window 12
  python -X utf8 Tools/ring_refusal_attractors.py --json          # 供闸前后比对
  python -X utf8 Tools/ring_refusal_attractors.py --as-of "2026-11-16 12:10"  # 复算历史时刻
"""
import argparse
import collections
import datetime
import json
import os
import sys

LEDGER = os.path.join("state", "ring-refusals.jsonl")
FMT = "%Y-%m-%d %H:%M:%S"


def load(path):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def measure(rows, hours, as_of):
    lo = as_of - datetime.timedelta(hours=hours)
    sel = []
    for r in rows:
        try:
            ts = datetime.datetime.strptime(r.get("ts", ""), FMT)
        except ValueError:
            continue
        if lo <= ts <= as_of:
            sel.append(r)
    by = collections.defaultdict(list)
    for r in sel:
        by[r.get("opening12", "")].append(r.get("cid", ""))
    multi = {k: v for k, v in by.items() if len(v) >= 2}
    wasted = sum(len(v) - 1 for v in multi.values())
    return {
        "window_hours": hours,
        "as_of": as_of.strftime(FMT),
        "rows": len(sel),
        "openings": len(by),
        "multi_openings": len(multi),
        "cross_cid_openings": sum(1 for v in multi.values() if len(set(v)) >= 2),
        "wasted_calls": wasted,
        "waste_ratio": round(wasted / len(sel), 4) if sel else 0.0,
        "top": [
            {"opening12": k, "calls": len(v), "cids": len(set(v)), "cid_head": sorted(set(v))[:6]}
            for k, v in sorted(multi.items(), key=lambda x: (-len(x[1]), x[0]))[:10]
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=24.0, help="回看小时数（默认 24）")
    ap.add_argument("--as-of", default="", help='以该时刻为准 "YYYY-MM-DD HH:MM:SS"（复算用）')
    ap.add_argument("--json", action="store_true", help="只输出 JSON（前后比对用）")
    ap.add_argument("--ledger", default=LEDGER)
    a = ap.parse_args()

    as_of = datetime.datetime.now()
    if a.as_of:
        try:
            as_of = datetime.datetime.strptime(a.as_of, FMT)
        except ValueError:
            print("bad --as-of, expect 'YYYY-MM-DD HH:MM:SS'", file=sys.stderr)
            return 2

    rows = load(a.ledger)
    m = measure(rows, a.window, as_of)

    if a.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return 0

    print("== ring-refusal attractors ==")
    print("ledger=%s total_rows=%d" % (a.ledger, len(rows)))
    print("as_of=%s window=%gh" % (m["as_of"], m["window_hours"]))
    print("rows=%d openings=%d multi_openings=%d cross_cid_openings=%d"
          % (m["rows"], m["openings"], m["multi_openings"], m["cross_cid_openings"]))
    print("wasted_calls=%d waste_ratio=%.1f%%" % (m["wasted_calls"], m["waste_ratio"] * 100))
    if m["top"]:
        print("-- top multi openings --")
        for t in m["top"]:
            print("  x%-3d cids=%-3d %s | %s"
                  % (t["calls"], t["cids"], t["opening12"][:20], "/".join(t["cid_head"])))
    else:
        print("-- no multi opening in window --")
    return 0


if __name__ == "__main__":
    sys.exit(main())
