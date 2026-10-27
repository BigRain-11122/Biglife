#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b40）：只取 gene_nearcheck PASS 的 10 条原文追加进
genes/lives.json 与 genes/language.json，既有条目零改动。
1 钩子物件 / 1 转折点 / 2 习惯 / 2 近况 / 4 口头禅（补 1 计数薄轴：夜班/跑腿/跑船/送件）。
来源：R-new 基因轮两批候选共 52 条（state/gene-cand-b40.txt / b40b.txt），21+10 条近重 FLAG 弃用。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"
LANG = "genes/language.json"

HOS = [
    "冰箱门上贴着一张写满电话号码的便签，字迹被水汽洇开了",
]
TPS = [
    "摆摊时遇上劝离，收摊收到一半又原样摆回去",
]
HAS = [
    "关火之后还要再拧一遍煤气阀，手指要确认到咔一声",
    "洗手池边常备一支旧牙刷，专刷水龙头根部的缝",
]
PRS = [
    "打算把旧手机里的相片导出来，充电线已经找不到了",
    "琢磨着给电动车换个后视镜，看了两个月还没下单",
]
CPS = [
    ("夜里路上没什么人，正好走得快。", "夜班"),
    ("认得路，就不怕绕。", "跑腿"),
    ("船上不带多余的东西。", "跑船"),
    ("这趟送完就回家吃饭。", "送件"),
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append(path, key, rendered):
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2):]
    Path(path).write_text(t, encoding="utf-8", newline="\n")


before_lives = load(LIVES)
before_lang = load(LANG)
before = (
    len(before_lives["hook_objects"]),
    len(before_lives["turning_points"]),
    len(before_lives["habits"]),
    len(before_lives["presents"]),
    len(before_lang["catchphrases"]),
)

append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in HOS])
append(LIVES, "turning_points", [json.dumps(x, ensure_ascii=False) for x in TPS])
append(LIVES, "habits", [json.dumps(x, ensure_ascii=False) for x in HAS])
append(LIVES, "presents", [json.dumps(x, ensure_ascii=False) for x in PRS])
append(
    LANG,
    "catchphrases",
    [
        '{\n      "text": %s,\n      "axis": %s\n    }'
        % (json.dumps(tx, ensure_ascii=False), json.dumps(ax, ensure_ascii=False))
        for tx, ax in CPS
    ],
)

lives = load(LIVES)
lang = load(LANG)
after = (
    len(lives["hook_objects"]),
    len(lives["turning_points"]),
    len(lives["habits"]),
    len(lives["presents"]),
    len(lang["catchphrases"]),
)
print(
    "counts before ho=%d tp=%d ha=%d pr=%d cp=%d -> after ho=%d tp=%d ha=%d pr=%d cp=%d"
    % (before + after)
)
for x in HOS:
    assert x in lives["hook_objects"], x
for x in TPS:
    assert x in lives["turning_points"], x
for x in HAS:
    assert x in lives["habits"], x
for x in PRS:
    assert x in lives["presents"], x
for tx, ax in CPS:
    assert any(e.get("text") == tx and e.get("axis") == ax for e in lang["catchphrases"]), tx
print("verify: all %d landed" % (len(HOS) + len(TPS) + len(HAS) + len(PRS) + len(CPS)))