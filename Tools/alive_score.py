# -*- coding: utf-8 -*-
"""alive_score.py — 活人感五项体检（有效性指标，不是产量指标）。

为什么必须有它：CEO 反复说「产出要有效、要真有人味」。产量（条数/覆盖率）能
证明机器在动，证明不了"像人"。这里按设计目标逐项打分，写 state/ALIVE.md，
并供夜间报告引用。

五项与目标（阈值来自 2026-11-20 全量基线 10057 条）：
  熟人提及 ≥50% ｜ 摩擦（没办成/卡住）≥65% ｜ 真对话 ≥20% ｜ 具体物件 ≥85% ｜ 平均长度 40-90
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
REG = os.path.join(CO, "census", "registry")
OUT_MD = os.path.join(CO, "state", "ALIVE.md")

RING_T = r"^- %s 「(.+?)」"
REL = re.compile(r"\*\*关系\*\*\s*(.+?)(?:\n|$)")
NAME = re.compile(r"C-\d{5}\s+([^\s；。（），、]+)")
FRICTION = ("没办成", "没成", "卡住", "卡在", "差", "黄了", "白跑", "撂", "拖", "还没", "不肯")
DIALOG = re.compile(r"「[^」]{2,}」|“[^”]{2,}”")
THING = re.compile(r"(刀|壶|秤|绳|钉|布|纸|盒|锅|碗|鞋|伞|窗|门|锁|线|笔|筐|算盘|架子|抽屉)")
TARGET = {"rel": 50.0, "fric": 65.0, "dlg": 20.0, "thing": 85.0}


def score(day=None):
    day = day or datetime.date.today().isoformat()
    ring = re.compile(RING_T % day, re.M)
    n = h_rel = h_fric = h_dlg = h_thing = 0
    lens = []
    for root, _, fs in os.walk(REG):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                t = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            m = ring.search(t)
            if not m:
                continue
            s = m.group(1)
            n += 1
            lens.append(len(s))
            mr = REL.search(t)
            names = set(NAME.findall(mr.group(1))) if mr else set()
            if names and any(x in s for x in names):
                h_rel += 1
            if any(w in s for w in FRICTION):
                h_fric += 1
            if DIALOG.search(s):
                h_dlg += 1
            if THING.search(s):
                h_thing += 1
    pct = lambda x: round(100.0 * x / max(1, n), 1)  # noqa: E731
    out = {"day": day, "n": n, "rel": pct(h_rel), "fric": pct(h_fric),
           "dlg": pct(h_dlg), "thing": pct(h_thing),
           "len_avg": round(sum(lens) / max(1, len(lens)), 1) if lens else 0}
    out["pass"] = sum(1 for k in TARGET if out[k] >= TARGET[k])
    return out


def write_md(st):
    lines = ["# 活人感体检 · %s" % st["day"], "",
             "样本 %d 条（今日全量）" % st["n"], "",
             "| 指标 | 实测 | 目标 | 判定 |", "|---|---|---|---|"]
    for k, label in (("rel", "提到自己的熟人"), ("fric", "有摩擦/没办成"),
                     ("dlg", "含真对话"), ("thing", "有具体物件")):
        ok = "PASS" if st[k] >= TARGET[k] else "**FAIL**"
        lines.append("| %s | %.1f%% | ≥%.0f%% | %s |" % (label, st[k], TARGET[k], ok))
    lines.append("| 平均长度 | %.1f 字 | 40–90 | %s |"
                 % (st["len_avg"], "PASS" if 40 <= st["len_avg"] <= 90 else "**FAIL**"))
    lines.append("")
    lines.append("通过 %d/4 项硬指标。" % st["pass"])
    try:
        with open(OUT_MD, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except OSError:
        pass


def main():
    _day = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    st = score(_day)
    # 跨日刚过时今天还没有环 → 回看昨天，别报一个 n=0 的空表（2026-11-21 实锚）
    if st["n"] == 0 and not _day:
        st = score((datetime.date.today() - datetime.timedelta(days=1)).isoformat())
    write_md(st)
    if "--json" in sys.argv:
        print(json.dumps(st, ensure_ascii=False))
    else:
        print("活人感 %s：熟人 %.1f%% 摩擦 %.1f%% 对话 %.1f%% 物件 %.1f%% 长度 %.1f（%d/4 达标）"
              % (st["day"], st["rel"], st["fric"], st["dlg"], st["thing"], st["len_avg"], st["pass"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
