# -*- coding: utf-8 -*-
"""年轮拒稿归因读面（T-20261115-04 观察态件·零 LLM / 零网络）。

病根：`state/ring-refusals.jsonl` 从 2026-11-15 起在记，但读数只在临时脚本里
做过（R3205 n=80 基线）。同一条读数每次重算 = 每次结论不可复现；而「真拒稿源
在哪」正是 T-20261115-04 换靶的靶点，必须有个可反复跑、口径固定的工具。

口径（写死，改口径须改本文件并留判据）：
  - 一行 = 一次被拒尝试；`gate` 数组 = 该次尝试同时命中的全部理由，不去重合并。
  - `cid` 去重 = 受影响居民数（retry_livelock 会把同一个 cid 记很多行）。
  - `solo` = 该次尝试只命中一条理由 → 这条理由单独改掉就能救回这一环。
  - `pair` = 命中两条及以上 → 改单条不足以救回，属结构性同源。

跑法：
  python -X utf8 Tools/ring_refusal_attribution.py
  python -X utf8 Tools/ring_refusal_attribution.py --day 2026-11-16
  python -X utf8 Tools/ring_refusal_attribution.py --top 6 --json
rc=0 正常（有读数或空账）／rc=1 账本缺失或解析错
"""
import argparse
import collections
import json
import os
import sys

CO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(CO, "state", "ring-refusals.jsonl")


def load(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                bad += 1
    return rows, bad


def attribution(rows):
    combo = collections.Counter()
    solo = collections.Counter()
    gate_hit = collections.Counter()
    fam = collections.Counter()
    day = collections.Counter()
    repeats = collections.Counter()
    for r in rows:
        gates = tuple(sorted(r.get("gate") or []))
        combo[gates] += 1
        if len(gates) == 1:
            solo[gates[0]] += 1
        for g in gates:
            gate_hit[g] += 1
        fam[r.get("family") or "?"] += 1
        day[str(r.get("ts", ""))[:10]] += 1
        if r.get("cid"):
            repeats[r["cid"]] += 1
    return {
        "rows": len(rows),
        "distinct_cid": len(repeats),
        "solo_rows": sum(solo.values()),
        "pair_rows": len(rows) - sum(solo.values()),
        "combo": combo,
        "solo": solo,
        "gate_hit": gate_hit,
        "family": fam,
        "day": day,
        "repeats": repeats,
    }


def render(a, top):
    out = []
    out.append("== ring_refusal_attribution ==")
    out.append("rows=%d distinct_cid=%d solo=%d pair+=%d"
               % (a["rows"], a["distinct_cid"], a["solo_rows"], a["pair_rows"]))
    if not a["rows"]:
        out.append("账本为空（当日无拒稿或未接线）")
        return "\n".join(out)
    out.append("-- combo (top %d) --" % top)
    for gates, n in a["combo"].most_common(top):
        out.append("%5d  %s" % (n, "+".join(gates) if gates else "(empty)"))
    out.append("-- solo reasons --")
    for g, n in a["solo"].most_common(top):
        out.append("%5d  %s" % (n, g))
    out.append("-- gate_hit (参与次数) --")
    for g, n in a["gate_hit"].most_common(top):
        out.append("%5d  %s" % (n, g))
    out.append("-- family (top %d) --" % top)
    for f, n in a["family"].most_common(top):
        out.append("%5d  %s" % (n, f))
    out.append("-- day --")
    for d, n in sorted(a["day"].items()):
        out.append("%5d  %s" % (n, d))
    worst = a["repeats"].most_common(3)
    if worst and worst[0][1] > 1:
        out.append("-- repeat_cid (top 3) --")
        for cid, n in worst:
            out.append("%5d  %s" % (n, cid))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", help="只看某日，如 2026-11-16")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ledger", default=LEDGER)
    args = ap.parse_args(argv)

    if not os.path.exists(args.ledger):
        print("MISSING %s" % args.ledger)
        return 1
    rows, bad = load(args.ledger)
    if bad:
        print("PARSE_ERROR lines=%d" % bad)
        return 1
    if args.day:
        rows = [r for r in rows if str(r.get("ts", "")).startswith(args.day)]

    a = attribution(rows)
    if args.json:
        payload = {k: (dict(v) if isinstance(v, collections.Counter) else v)
                   for k, v in a.items()}
        payload["combo"] = {"+".join(k): v for k, v in a["combo"].items()}
        payload["day_filter"] = args.day
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(a, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
