# -*- coding: utf-8 -*-
"""年轮喂料连续性闸（零 LLM·确定性）——T-20261112-01 的验收载体。

病根（2026-11-12 R2566 立单）：年轮品质差的供给侧原因是「事件窗口恒空」——
evolve_citizen 侧 200 行窗口全是机器台账，居民只剩天气可锚，于是套话。修法②已补
街区日常母题池（events/life/<date>.jsonl）与流言链（cognition/rumors/）两条喂料，
但验收条件「连续 3 个生产日窗口非空」原先只写在任务板的人话里＝承诺挂错载体
（D-20261112-08）。本工具把该验收摊成每日一行机器判据，任何班次 rc 即可判红。

判据（逐日，默认回看 3 天）：
  motif = events/life/<date>.jsonl 存在且 ≥1 条 LIFE_MOTIF（META 行不算供给）
  rumor = cognition/rumors/rumors-<date>.jsonl 存在且 ≥1 条
  ready = motif and rumor

退出码：连续 ready 天数 ≥ --days → 0；未达 → 2（进行中，非故障）。

用法：
  python -X utf8 Tools/ring_material_check.py [--days 3] [--json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def count_motifs(date: str) -> int:
    path = os.path.join(ROOT, "events", "life", f"{date}.jsonl")
    if not os.path.exists(path):
        return 0
    n = 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("type") == "LIFE_MOTIF":
                n += 1
    return n


def count_rumors(date: str) -> int:
    path = os.path.join(ROOT, "cognition", "rumors", f"rumors-{date}.jsonl")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        return sum(1 for line in fh if line.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="年轮喂料连续性闸（T-20261112-01 验收）")
    ap.add_argument("--days", type=int, default=3, help="连续达标所需天数（默认 3）")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args()

    today = datetime.date.today()
    days: list[dict] = []
    streak = 0
    broken = False
    for i in range(args.days):
        d = (today - datetime.timedelta(days=i)).isoformat()
        motif, rumor = count_motifs(d), count_rumors(d)
        ready = motif > 0 and rumor > 0
        days.append({"date": d, "motifs": motif, "rumors": rumor, "ready": ready})
        if ready and not broken:
            streak += 1
        else:
            broken = True

    ok = streak >= args.days
    if args.json:
        print(json.dumps({"days": days, "streak": streak, "need": args.days,
                          "verdict": "PASS" if ok else "IN-PROGRESS"},
                         ensure_ascii=False, indent=2))
    else:
        print("== ring_material_check (T-20261112-01 acceptance) ==")
        for row in reversed(days):
            print("  %s motif=%-3d rumor=%-3d %s" % (
                row["date"], row["motifs"], row["rumors"],
                "ready" if row["ready"] else "MISSING"))
        print("streak=%d/%d verdict: %s" % (streak, args.days,
                                             "PASS" if ok else "IN-PROGRESS"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
