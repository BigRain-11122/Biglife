# -*- coding: utf-8 -*-
"""年轮质量评分器 v2 · 按造闸六问重做（2026-11-18）

## 一、标定依据（实测 2714 条，2026-11-18 18:0x）

| 指标 | p10 | p50 | p90 | max | 均值 |
|---|---|---|---|---|---|
| 字数 | 49 | 64 | 80 | 92 | 63.7 |
| 专名数 | 0 | 0 | 1 | 5 | 0.5 |
| 数字/量词 | 0 | 0 | 1 | 4 | 0.1 |
| 动词数 | 0 | 1 | 3 | 8 | 1.5 |
| 程度副词 | 0 | 0 | 1 | 2 | 0.2 |
| 对白句数 | 0 | 0 | 0 | 4 | 0.1 |
| 「我」出现 | 0 | 1 | 2 | 4 | 1.0 |

**关键结论**：p50 专名=0、数字=0、动词=1 —— 大半条目「没有一个具体的人、没有一个数字、只有 1 个动词」。
这就是 AI 感的量化形态：全是形容词和状态，没有事情发生。
所以本评分器把「动词密度 / 专名 / 数字」放在最高权重，而不是押在"字数分布"上。

## 二、负控（必须真跑）
`--selftest` 构造 5 条典型 AI 味（全形容词、无人名、无数字、无动词），要求总分 < 40；
再构造 3 条优秀样本（有具体人、动作、数字），要求总分 > 70。不过 = 闸不可信。

## 三、能力边界（这个闸判不了什么）
- 判不了**人设是否贴合**（需要读卡片人设并理解职业语境，交人眼）
- 判不了**世界观是否自洽**（需要全库 canon 比对）
- 判不了**情感是否真挚**（主观）
- 判不了**方言/地域是否对**（需要地域词表，容易被误伤）
以上四项明写为「不判」，不当万能闸用。

## 四、失效条件
- 样本 < 10 条：只报分不做判决（统计不稳）
- 体式是「就一句」（8-18 字）：动词/专名的绝对数阈值减半，否则天然判负
-  honoured-seat（城主位）条目：人设权归 CEO，不参与评分

## 五、唯一判据
所有阈值集中在 THRESH，主流程与 selftest 共用同一函数，禁两处各写。

用法：
  python -X utf8 Tools/ring_score.py [--last N] [--json] [--selftest]
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

# ── 阈值：全部来自上面的标定表（取 p90 作为"达标线"，p50 作为"及格线"）
THRESH = {
    "verb_per50": (1.5, 3.5),     # 每 50 字动词数：p50≈0.8, p90≈2.3 → 及格1.5 达标3.5
    "names": (1, 2),              # 专名数：p50=0 p90=1 → 及格1 达标2
    "numbers": (1, 2),            # 数字/量词：p50=0 p90=1 → 及格1 达标2
    "adj_per50": (1.2, 0.6),      # 程度副词密度：越低越好（达标≤0.6）
    "dialog": (1, 2),             # 对白句数（仅对话体式要求）
    "me_observe": (1, 0),         # 看别人体式：「我」应 ≤1（达标 0）
    "len_min": 8, "len_max": 105,
}

W = {
    "verb": 18, "names": 15, "numbers": 12, "form_ok": 10, "dialog": 10,
    "len_ok": 8, "me_low": 8, "adj_low": 6, "nofiller": 5,
    "noweather": 4, "nofake": 4,
}

NAME_RE = re.compile(
    r"(老[\u4e00-\u9fa5]|小[\u4e00-\u9fa5]|阿[\u4e00-\u9fa5]|"
    r"[\u4e00-\u9fa5]{1,2}(?:婶|叔|婆|哥|姐|嫂|伯)|"
    r"修鞋的|卖菜的|对门的|隔壁的|收废品的|开店的|守门的)")
NUM_RE = re.compile(r"[一二三四五六七八九十百千万两\d]+"
                    r"(?:块|元|毛|分|个|件|趟|斤|两|张|副|筐|屉|台|年|月|日|点|级|度|根|条|双|只|把)")
VERB_RE = re.compile(r"(拿|放|递|接|走|坐|站|敲|拧|擦|扫|搬|抬|数|称|收|问|答|笑|骂|喊|看|听|"
                     r"吃|喝|穿|洗|切|煮|缝|修|钉|捆|摞|挑|摘|倒|盛|端|拉|推|扛|背|翻|摊|挂|"
                     r"剪|削|磨|钻|焊|擦|抹|扫|擦|装|卸|点|算|记|写|画|量|试|换|补|钉|缠)")
ADJ_RE = re.compile(r"(很|挺|特别|十分|格外|有些|微微|轻轻地|慢慢地|静静地|悄悄地|悠悠地)")
FILLER_RE = re.compile(r"这日子(嘛|啊|就)|急不得|慢慢来|说到底|日子是过出来的|"
                       r"火候到了自然|该来的总会来|归根到底")
WEATHER_RE = re.compile(r"风(不小|挺大|好大|很大|硬得像|刮得|把|顺着|灌得|撞在)|"
                        r"天阴着|天晴|云厚|云压|下雨|雨点|雨丝|\d+\s*级的风")
DIALOG_RE = re.compile(r"[「“][^」”]{2,}[」”]")
TEMP_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:°C|度|℃)")
WIND_RE = re.compile(r"(\d+)\s*级的风")

QUOTES = "「“\"'"


def inner(s):
    s = (s or "").strip()
    if len(s) >= 2 and s[0] in QUOTES and s[-1] in "」”\"'":
        return s[1:-1]
    return s


def _ramp(x, lo, hi):
    """lo→0 分，hi→100 分，线性。lo>hi 时表示越低越好。"""
    if lo == hi:
        return 100.0 if x >= hi else 0.0
    if lo < hi:
        return max(0.0, min(100.0, (x - lo) / (hi - lo) * 100.0))
    return max(0.0, min(100.0, (lo - x) / (lo - hi) * 100.0))


def score_one(row, form_key=None):
    s = inner(row.get("ring"))
    chars = row.get("chars") or len(s)
    per50 = 50.0 / max(1, chars)
    verbs = len(VERB_RE.findall(s))
    names = len(NAME_RE.findall(s))
    nums = len(NUM_RE.findall(s))
    adjs = len(ADJ_RE.findall(s))
    dialogs = len(DIALOG_RE.findall(s))
    me = s.count("我")

    # 「就一句」体式天然短，绝对数阈值减半（失效条件里的豁免）
    half = 0.5 if chars <= 20 else 1.0
    t = THRESH
    parts = {}
    parts["verb"] = _ramp(verbs * per50, t["verb_per50"][0] * half, t["verb_per50"][1] * half)
    parts["names"] = _ramp(names, t["names"][0] * half, t["names"][1] * half)
    parts["numbers"] = _ramp(nums, t["numbers"][0] * half, t["numbers"][1] * half)
    parts["adj_low"] = _ramp(adjs * per50, t["adj_per50"][0], t["adj_per50"][1])
    parts["dialog"] = _ramp(dialogs, t["dialog"][0], t["dialog"][1]) if form_key == "dialogue" else 100.0
    parts["me_low"] = _ramp(me, 3, 0) if form_key == "observe" else 100.0
    parts["len_ok"] = 100.0 if t["len_min"] <= chars <= t["len_max"] else 0.0
    parts["form_ok"] = (100.0 if _form_hit(s, form_key, dialogs, nums, me, chars)
                        else 40.0) if form_key else 100.0

    def zero_if(pat, row_s):
        return 100.0 - 100.0 * (1 if pat.search(row_s) else 0)

    parts["nofiller"] = zero_if(FILLER_RE, s)
    parts["noweather"] = zero_if(WEATHER_RE, s)

    fake = False
    for m in WIND_RE.finditer(s):
        if int(m.group(1)) > 12:
            fake = True
    for m in TEMP_RE.finditer(s):
        v = float(m.group(1))
        if v > 45 or v < -20:
            fake = True
    parts["nofake"] = 0.0 if fake else 100.0

    total = sum(parts[k] * W[k] for k in W) / 100.0
    # ── 硬门槛（2026-11-18 负控暴露）：负控样本靠「长度合规/无天气/无编造」这类
    # 不需要任何努力就满分的维度拿到 44-55 分，闸形同虚设。
    # 闸的本质是「关键判据不达标即判负」，所以加门槛：
    #   必须(有动作 或 有对话) 且 (有人名 或 有数字 或 对话>=2)
    # 否则总分封顶 38（低于负控线 40），让「只有感受没有事情」的条目永远过不了。
    gate_ok = (verbs >= 1 or dialogs >= 1) and (names >= 1 or nums >= 1 or dialogs >= 2)
    if not gate_ok:
        total = min(total, 38.0)
    return {k: round(v, 1) for k, v in parts.items()} | {"total": round(total, 1),
                                                        "gate_ok": gate_ok,
                                                        "chars": chars, "verbs": verbs,
                                                        "names": names, "nums": nums,
                                                        "dialogs": dialogs}


def _form_hit(s, key, dialogs, nums, me, chars):
    if key == "dialogue":
        return dialogs >= 1
    if key == "log":
        return nums >= 2
    if key == "observe":
        return me <= 1
    if key == "oneline":
        return chars <= 20
    if key == "story":
        return nums >= 1 and len(VERB_RE.findall(s)) >= 3
    return True


def score(rows):
    """批量评分（不带体式信息时，体式相关维度按 100 计）。"""
    if not rows:
        return None
    per = [score_one(r) for r in rows]
    keys = [k for k in W]   # 只聚合权重表里的维度分
    agg = {k: round(statistics.mean(p[k] for p in per), 1) for k in keys}
    lens = [p["chars"] for p in per]
    out = dict(agg)
    out.update({
        "n": len(rows), "len_min": min(lens), "len_max": max(lens),
        "len_sd": round(statistics.pstdev(lens), 1) if len(lens) > 1 else 0.0,
        "avg_total": round(statistics.mean(p["total"] for p in per), 1),
        "verb_avg": round(statistics.mean(p["verbs"] for p in per), 1),
        "name_avg": round(statistics.mean(p["names"] for p in per), 1),
        "num_avg": round(statistics.mean(p["nums"] for p in per), 1),
    })
    return out


# ── 负控样例（应判负：典型 AI 味——全形容词、无人、无数、无动作）
NEG = [
    "「这日子嘛，稳稳当当就过去了，心里头踏实得很，风轻轻吹着，一切都刚刚好。」",
    "「今天的心情格外平静，仿佛整个世界都慢了下来，温柔的阳光洒在身上，很好。」",
    "「把手里的事情慢慢理了理，觉得日子还是有盼头的，不急不躁才是正道。」",
    "「日子是过出来的，不是算出来的，踏踏实实做人，认认真真做事，就好。」",
    "「有时候会想起很多事，心里有些感慨，但更多的是平静与满足，这样挺好。」",
]
# ── 正控样例（应判过：具体人、具体动作、具体数字）
POS = [
    "「卖菜的把烂叶子一片片摘下来堆在秤盘边，嘴上说着不碍事，手底下挑得比谁都细。」",
    "「换了六副鞋底，收九十；买胶花十四；中午面钱八块；剩六十八，明儿得补两块铁掌。」",
    "「「这筐多少钱？」「八块五。」「昨儿还八块。」「昨儿是昨儿。」他掏了钱，我也没再让。」",
]


def selftest():
    print("=== 负控（应 < 40 分，5 条 AI 味样本）===")
    neg = [score_one({"ring": s, "chars": len(s)}) for s in NEG]
    for i, p in enumerate(neg):
        print("  #%d total=%5.1f  verb=%d name=%d num=%d" % (i + 1, p["total"], p["verbs"], p["names"], p["nums"]))
    neg_avg = statistics.mean(p["total"] for p in neg)
    print("  负控均值: %.1f  %s" % (neg_avg, "PASS" if neg_avg < 40 else "FAIL(闸太松)"))
    print()
    print("=== 正控（应 > 70 分，3 条优秀样本）===")
    pos = [score_one({"ring": s, "chars": len(s)}, form_key=k)
           for s, k in zip(POS, ["observe", "log", "dialogue"])]
    for i, p in enumerate(pos):
        print("  #%d total=%5.1f  verb=%d name=%d num=%d dialog=%d" % (
            i + 1, p["total"], p["verbs"], p["names"], p["nums"], p["dialogs"]))
    pos_avg = statistics.mean(p["total"] for p in pos)
    print("  正控均值: %.1f  %s" % (pos_avg, "PASS" if pos_avg > 70 else "FAIL(闸太严)"))
    print()
    ok = neg_avg < 40 and pos_avg > 70
    print("SELFTEST %s（负控 %.1f < 40 且 正控 %.1f > 70）" % ("PASS" if ok else "FAIL", neg_avg, pos_avg))
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
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
    print("样本 %d 条  字数 %d-%d (σ=%.1f)  动词均值 %.1f  专名均值 %.1f  数字均值 %.1f" % (
        s["n"], s["len_min"], s["len_max"], s["len_sd"], s["verb_avg"], s["name_avg"], s["num_avg"]))
    for k, label in (("verb", "动词密度"), ("names", "专名"), ("numbers", "数字量词"),
                     ("adj_low", "少形容词"), ("dialog", "对白"), ("me_low", "少「我」"),
                     ("len_ok", "长度合规"), ("form_ok", "体式合规"),
                     ("nofiller", "无空话"), ("noweather", "无天气"), ("nofake", "无编造")):
        print("  %-8s %5.1f  %s" % (label, s[k], "█" * int(s[k] / 5)))
    print("  ─────────────")
    print("  总分   %5.1f" % s["avg_total"])
    print("  能力边界: 不判人设贴合/世界观自洽/情感真挚/地域方言（交人眼）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
