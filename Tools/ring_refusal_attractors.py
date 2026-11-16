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
  python -X utf8 Tools/ring_refusal_attractors.py --trend         # 按自然日曲线（结案判据）

--trend 口径：按自然日切分行，每日调**同一个 measure()**（窗口取该日 23:59:59，
行已按日预筛，故等价于「当日整日」），不另写一套聚合逻辑——避免曲线与单点读数
两套算法漂移。用途=T-20261115-04 观察窗（11-17 到期）结案时看 waste% 走向。
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


def day_series(rows):
    """按自然日切分，每日复用 measure() 出同一口径读数（不另立算法）。"""
    days = sorted({r.get("ts", "")[:10] for r in rows if r.get("ts")})
    out = []
    for d in days:
        try:
            day_end = datetime.datetime.strptime(d + " 23:59:59", FMT)
        except ValueError:
            continue
        day_rows = [r for r in rows if r.get("ts", "").startswith(d)]
        m = measure(day_rows, 24.0, day_end)
        out.append({
            "day": d,
            "rows": m["rows"],
            "openings": m["openings"],
            "multi_openings": m["multi_openings"],
            "cross_cid_openings": m["cross_cid_openings"],
            "wasted_calls": m["wasted_calls"],
            "waste_ratio": m["waste_ratio"],
            "top": m["top"][:3],
        })
    return out


def render_trend(series):
    out = ["== ring-refusal attractors · daily trend =="]
    if not series:
        out.append("账本为空（无日切片）")
        return "\n".join(out)
    out.append("day         rows openings multi cross wasted waste%")
    for s in series:
        out.append("%-11s %4d %8d %5d %5d %6d %5.1f%%"
                   % (s["day"], s["rows"], s["openings"], s["multi_openings"],
                      s["cross_cid_openings"], s["wasted_calls"],
                      s["waste_ratio"] * 100))
    best = min(series, key=lambda s: s["waste_ratio"])
    worst = max(series, key=lambda s: s["waste_ratio"])
    out.append("最差 %s waste%%=%.1f%% ／ 最好 %s waste%%=%.1f%%（口径=measure() 按日复算）"
               % (worst["day"], worst["waste_ratio"] * 100,
                  best["day"], best["waste_ratio"] * 100))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=float, default=24.0, help="回看小时数（默认 24）")
    ap.add_argument("--trend", action="store_true",
                    help="按自然日输出 waste%% 曲线（复用 measure() 同一口径·结案判据用）")
    ap.add_argument("--as-of", default="", help='以该时刻为准 "YYYY-MM-DD HH:MM:SS"（复算用）')
    ap.add_argument("--json", action="store_true", help="只输出 JSON（前后比对用）")
    ap.add_argument("--out", default="",
                    help="把 JSON 写入该文件（UTF-8 无 BOM）。"
                         "注：PowerShell 5.1 的 '>' 重定向默认写 UTF-16，"
                         "落基线/复测读数一律用本参数，勿用重定向。")
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

    if a.trend:
        series = day_series(rows)
        if a.out:
            payload = json.dumps({"ledger": a.ledger, "total_rows": len(rows),
                                  "days": series}, ensure_ascii=False, indent=2)
            d = os.path.dirname(a.out)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            with open(a.out, "w", encoding="utf-8", newline="\n") as f:
                f.write(payload + "\n")
            print("written: %s (utf-8, %d bytes)" % (a.out, len(payload.encode("utf-8"))))
        elif a.json:
            print(json.dumps({"ledger": a.ledger, "total_rows": len(rows),
                              "days": series}, ensure_ascii=False, indent=2))
        else:
            print(render_trend(series))
        return 0

    m = measure(rows, a.window, as_of)

    if a.out:
        payload = json.dumps(m, ensure_ascii=False, indent=2)
        d = os.path.dirname(a.out)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(a.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload + "\n")
        print("written: %s (utf-8, %d bytes)" % (a.out, len(payload.encode("utf-8"))))
        return 0

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
