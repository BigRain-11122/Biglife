# -*- coding: utf-8 -*-
"""年轮喂料连续性闸（零 LLM·确定性）——T-20261112-01 的验收载体。

病根（2026-11-12 R2566 立单）：年轮品质差的供给侧原因是「事件窗口恒空」——
evolve_citizen 侧 200 行窗口全是机器台账，居民只剩天气可锚，于是套话。修法②已补
街区日常母题池（events/life/<date>.jsonl）与流言链（cognition/rumors/）两条喂料，
但验收条件「连续 3 个生产日窗口非空」原先只写在任务板的人话里＝承诺挂错载体
（D-20261112-08）。本工具把该验收摊成每日一行机器判据，任何班次 rc 即可判红。

判据（逐日，默认回看 3 天）——名义量 + **有效量**两面都看：
  motif = events/life/<date>.jsonl 存在且 ≥1 条 LIFE_MOTIF（META 行不算供给）
  rumor = cognition/rumors/rumors-<date>.jsonl 存在且 ≥1 条
  motif_eff / rumor_eff = 按 evolve_citizen 真实 ingest 过滤后仍能进 prompt 的条数
  ready = 名义 ≥1 **且** 有效 ≥1（两面都要）

为什么要有效量（2026-11-12 R2600 实锚）：流言文件 8 条齐全、mtime 当日，
但年轮侧 rumor_line_for 有 trigger-free 纪律（RUMOR_TRIGGERS 含 风/雨/云/雾…），
8 条全是「风从窗缝里挤进来」这类句子 → **有效通过 0 条**。只看文件存在就是
假绿：连跑 3 天也只会证明「有人会写文件」，证明不了「居民吃到了人味素材」。

退出码：连续 ready 天数 ≥ --days → 0；未达 → 2（进行中，非故障）。

用法：
  python -X utf8 Tools/ring_material_check.py [--days 3] [--json]
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _ingest_filters():
    """判据单源：直接取 evolve_citizen 的 ingest 过滤器，禁在本文件重抄一份。

    两处各自维护一份 trigger 表时，闸绿与产线红会长期并行（本司已吃过同类判例），
    所以这里的「有效」必须与 rumor_line_for 逐字同口径。
    """
    tools_dir = os.path.join(ROOT, "Tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import evolve_citizen as ec  # noqa: E402

    return ec.RUMOR_TRIGGERS, ec.RUMOR_DEV_ID


def _rows(path: str):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def counts(date: str, triggers, dev_id) -> tuple[int, int, int, int]:
    """返回 (motif_n, motif_eff, rumor_n, rumor_eff)。"""
    motif_p = os.path.join(ROOT, "events", "life", f"{date}.jsonl")
    motif_n = motif_eff = 0
    for row in _rows(motif_p):
        if row.get("type") != "LIFE_MOTIF":
            continue
        motif_n += 1
        text = str(row.get("text") or "").strip()
        # 与 load_life_motifs 同口径：非空且含中文才算进 prompt 的供给。
        if text and CJK_RE.search(text):
            motif_eff += 1

    rumor_p = os.path.join(ROOT, "cognition", "rumors", f"rumors-{date}.jsonl")
    rumor_n = rumor_eff = 0
    for row in _rows(rumor_p):
        rumor_n += 1
        text = str(row.get("text") or "")
        if not text:
            continue
        if any(tok in text for tok in triggers):
            continue
        if dev_id.search(text):
            continue
        rumor_eff += 1

    return motif_n, motif_eff, rumor_n, rumor_eff


def main() -> int:
    ap = argparse.ArgumentParser(description="年轮喂料连续性闸（T-20261112-01 验收）")
    ap.add_argument("--days", type=int, default=3, help="连续达标所需天数（默认 3）")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args()

    triggers, dev_id = _ingest_filters()

    today = datetime.date.today()
    days: list[dict] = []
    streak = 0
    broken = False
    for i in range(args.days):
        d = (today - datetime.timedelta(days=i)).isoformat()
        motif, motif_eff, rumor, rumor_eff = counts(d, triggers, dev_id)
        ready = motif > 0 and rumor > 0 and motif_eff > 0 and rumor_eff > 0
        days.append({"date": d, "motifs": motif, "motifs_eff": motif_eff,
                     "rumors": rumor, "rumors_eff": rumor_eff, "ready": ready})
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
            print("  %s motif=%d/%d eff  rumor=%d/%d eff  %s" % (
                row["date"], row["motifs_eff"], row["motifs"],
                row["rumors_eff"], row["rumors"],
                "ready" if row["ready"] else
                ("BLOCKED" if row["rumors"] else "MISSING")))
        print("streak=%d/%d verdict: %s" % (streak, args.days,
                                            "PASS" if ok else "IN-PROGRESS"))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
