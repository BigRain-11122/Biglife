# -*- coding: utf-8 -*-
"""质量哨兵：零 LLM 统计当日产出的质量面，异常写告警。

Why（CEO 2026-11-17「保证高质量」「满负荷不间断」）：
  跑得越快，质量漂移越难靠人眼发现。生产泵只报「写了多少」，不报「写得像不像人」。
  本哨兵把「千人一面」这类可量化信号钉成阈值：
    - 单一意象覆盖率（今天 87% 的人写风 → 现在阈值 45%）
    - 句子长度离群（30-80 字是 prompt 要求；<30 像敷衍，>100 像作文）
    - 开场 8 字聚簇（同开场 ≥8 人 = 模板化）
    - 与昨日条目高度重复（同一个人连续两天说几乎一样的话）

数据源：census/export/today-rings.jsonl（生产泵每批后写）
输出：正常静默退出 0；异常写 state/QUALITY-ALERT.md 并退出 1。

用法：
  python -X utf8 Tools/quality_sentinel.py
  python -X utf8 Tools/quality_sentinel.py --date 2026-11-17 --quiet
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
EXPORT = os.path.join(CO, "census", "export")
STATE = os.path.join(CO, "state")
TODAY = os.path.join(EXPORT, "today-rings.jsonl")
LEDGER = os.path.join(EXPORT, "rings-ledger.jsonl")
ALERT = os.path.join(STATE, "QUALITY-ALERT.md")

IMAGE_WORDS = ("风", "雨", "灯", "汤", "云", "伞", "旧")
IMG_MAX_RATIO = 0.45      # 单一意象覆盖上限
OPEN_MAX_SAME = 8         # 同开场 8 字最多几人
SHORT_MIN = 30            # prompt 要求 30-80 字
LONG_MAX = 100
MIN_SAMPLE = 20           # 样本太少不做判定（避免误报）


def load(path):
    rows = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return rows


def analyze(rows, prev_rows):
    n = len(rows)
    out = {"count": n}
    if n == 0:
        return out
    # 单一意象覆盖率
    img = {}
    for w in IMAGE_WORDS:
        img[w] = sum(1 for r in rows if w in (r.get("ring") or "")) / n
    out["image_ratio"] = {k: round(v, 3) for k, v in img.items()}
    # 句长
    lens = [r.get("chars") or len(r.get("ring") or "") for r in rows]
    out["len_avg"] = round(sum(lens) / n, 1)
    out["short_ratio"] = round(sum(1 for x in lens if x < SHORT_MIN) / n, 3)
    out["long_ratio"] = round(sum(1 for x in lens if x > LONG_MAX) / n, 3)
    # 开场聚簇
    opens = collections.Counter((r.get("ring") or "")[1:9] for r in rows)
    out["top_opens"] = opens.most_common(3)
    # 与昨日逐人比对（同一人两天的句子相似度极简判据：前 12 字相同）
    same_head = 0
    prev_by_cid = {r.get("cid"): (r.get("ring") or "") for r in prev_rows}
    for r in rows:
        p = prev_by_cid.get(r.get("cid"))
        cur = r.get("ring") or ""
        if p and len(cur) >= 12 and p[1:13] == cur[1:13]:
            same_head += 1
    out["same_head_vs_prev"] = same_head
    return out


def judge(st):
    bad = []
    if st.get("count", 0) < MIN_SAMPLE:
        return bad  # 样本不足不判定
    for w, v in (st.get("image_ratio") or {}).items():
        if v > IMG_MAX_RATIO:
            bad.append("意象「%s」覆盖 %.0f%% > %.0f%%（千人一面风险）" % (w, v * 100, IMG_MAX_RATIO * 100))
    if st.get("short_ratio", 0) > 0.25:
        bad.append("过短句（<%d 字）占 %.0f%% > 25%%" % (SHORT_MIN, st["short_ratio"] * 100))
    if st.get("long_ratio", 0) > 0.15:
        bad.append("过长句（>%d 字）占 %.0f%% > 15%%" % (LONG_MAX, st["long_ratio"] * 100))
    for opening, cnt in (st.get("top_opens") or []):
        if cnt >= OPEN_MAX_SAME:
            bad.append("开场「%s…」被 %d 人用（阈值 %d）" % (opening, cnt, OPEN_MAX_SAME))
    if st.get("same_head_vs_prev", 0) >= 20:
        bad.append("与昨日同人同开头 %d 条（自我重复）" % st["same_head_vs_prev"])
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    rows = [r for r in load(TODAY) if r.get("date") == a.date]
    prev_day = (datetime.date.fromisoformat(a.date) - datetime.timedelta(days=1)).isoformat()
    prev = [r for r in load(LEDGER) if r.get("date") == prev_day]
    st = analyze(rows, prev)
    bad = judge(st)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not bad:
        if not a.quiet:
            print("[%s] OK %s | count=%d avg_len=%s top_img=%s" % (
                stamp, a.date, st.get("count", 0), st.get("len_avg"),
                max((st.get("image_ratio") or {"-": 0}).items(), key=lambda kv: kv[1])))
        if os.path.exists(ALERT):
            try:
                os.remove(ALERT)
            except OSError:
                pass
        return 0

    lines = ["# QUALITY-ALERT · %s（%s）" % (stamp, a.date), "", "质量面异常：", ""]
    for b in bad:
        lines.append("- %s" % b)
    lines += ["", "## 实测", "", "```json",
              json.dumps(st, ensure_ascii=False, indent=2), "```", "",
              "## 建议", "",
              "1. 意象超标 → 提高 `wx_skip_block` 分流比例（当前 2/3）或给该意象加配额闸",
              "2. 过短/过长 → 检查 prompt 尾部字数要求是否被模型忽略",
              "3. 开场聚簇 → 检查 `opening_seed_block` 骨架池是否已耗尽",
              "4. 自我重复 → 收紧 `COOLDOWN_DAYS`（当前 2）或调 `SELF_DUP_SIM`（当前 0.60）",
              ""]
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(ALERT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        print("alert write failed: %s" % exc, file=sys.stderr)
    if not a.quiet:
        print("[%s] QUALITY-ALERT: %s" % (stamp, "; ".join(bad)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
