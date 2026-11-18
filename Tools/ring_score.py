# -*- coding: utf-8 -*-
"""年轮质量评分器：把「像不像人写的」拆成可测指标，用于调参 A/B 对比。

Why（CEO 2026-11-18「不断调试，直到搭配出最好的」）：
  没有客观指标就分不清一次改动是变好还是变坏。

六维（0-100，权重见 W）：
  1 形式分化 — 字数标准差（目标 σ≥15）
  2 具体对象 — 出现具体人名/称谓的比例
  3 对话     — 正文内部含引号对白的比例（先剥最外层「」，否则 100% 假阳性）
  4 无空话   — 不含结尾感悟套话的比例
  5 无天气   — 不含天气断言的比例
  6 无编造   — 不含越界数据的比例（风力等级>12、温度>45 或 <-20）

用法：
  python -X utf8 Tools/ring_score.py [--last N] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
TODAY = os.path.join(CO, "census", "export", "today-rings.jsonl")

W = {"form": 0.20, "object": 0.22, "dialog": 0.16, "nofiller": 0.18,
     "noweather": 0.12, "nofake": 0.12}

NAME_RE = re.compile(
    r"(老[\u4e00-\u9fa5]|小[\u4e00-\u9fa5]|阿[\u4e00-\u9fa5]|"
    r"[\u4e00-\u9fa5]{1,2}婶|[\u4e00-\u9fa5]{1,2}叔|[\u4e00-\u9fa5]{1,2}婆|"
    r"[\u4e00-\u9fa5]{1,2}哥|[\u4e00-\u9fa5]{1,2}姐|"
    r"修鞋的|卖菜的|对门的|隔壁的|收废品的)")
FILLER_RE = re.compile(r"这日子(嘛|啊|就)|急不得|慢慢来|说到底|日子是过出来的|"
                       r"火候到了自然|该来的总会来")
WEATHER_RE = re.compile(r"风(不小|挺大|好大|很大|硬得像|刮得|把|顺着|灌得|撞在)|"
                        r"天阴着|天晴|云厚|云压|下雨|雨点|雨丝|"
                        r"\d+\s*级的风")
DIALOG_RE = re.compile(r"[「“\"][^」”\"]{4,}[」”\"]")
TEMP_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°C|度|℃)")
WIND_RE = re.compile(r"(\d+)\s*级的风")

QUOTES = "「“\"'"


def _inner(s):
    """剥掉年轮整体的「」包裹，否则每一行都像有对话。"""
    s = (s or "").strip()
    if len(s) >= 2 and s[0] in QUOTES and s[-1] in "」”\"'":
        return s[1:-1]
    return s


def score(rows):
    n = len(rows)
    if n == 0:
        return None
    lens = [r.get("chars") or len(r.get("ring") or "") for r in rows]
    sd = statistics.pstdev(lens) if n > 1 else 0.0
    form = min(100.0, sd / 15.0 * 100.0)

    def ratio(pred):
        return sum(1 for r in rows if pred(r)) / n * 100.0

    obj = ratio(lambda r: bool(NAME_RE.search(_inner(r.get("ring")))))
    dlg = ratio(lambda r: bool(DIALOG_RE.search(_inner(r.get("ring")))))
    nofill = 100.0 - ratio(lambda r: bool(FILLER_RE.search(r.get("ring") or "")))
    nowx = 100.0 - ratio(lambda r: bool(WEATHER_RE.search(_inner(r.get("ring")))))

    def is_fake(r):
        s = _inner(r.get("ring"))
        for m in WIND_RE.finditer(s):
            if int(m.group(1)) > 12:
                return True
        for m in TEMP_RE.finditer(s):
            v = float(m.group(1))
            if v > 45 or v < -20:
                return True
        return False

    nofake = 100.0 - ratio(is_fake)
    parts = {"form": form, "object": obj, "dialog": dlg,
             "nofiller": nofill, "noweather": nowx, "nofake": nofake}
    total = sum(parts[k] * W[k] for k in W)
    return {"n": n, "len_min": min(lens), "len_max": max(lens),
            "len_sd": round(sd, 1), **{k: round(v, 1) for k, v in parts.items()},
            "total": round(total, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    rows = []
    try:
        with open(TODAY, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        print("no today-rings.jsonl")
        return 1
    if a.last:
        rows = rows[-a.last:]
    s = score(rows)
    if s is None:
        print("no rows")
        return 1
    if a.json:
        print(json.dumps(s, ensure_ascii=False))
        return 0
    print("样本 %d 条  字数 %d-%d (σ=%.1f)" % (s["n"], s["len_min"], s["len_max"], s["len_sd"]))
    for k, label in (("form", "形式分化"), ("object", "具体对象"), ("dialog", "对话"),
                     ("nofiller", "无空话"), ("noweather", "无天气"), ("nofake", "无编造")):
        print("  %-6s %5.1f  %s" % (label, s[k], "█" * int(s[k] / 5)))
    print("  ─────────────")
    print("  总分   %5.1f" % s["total"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
