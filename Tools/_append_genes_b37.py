#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b37）：只取 gene_nearcheck PASS 的 8 条原文追加进
genes/lives.json 与 genes/language.json，既有条目零改动。
2 钩子物件 / 2 转折点 / 1 习惯 / 1 近况 / 2 口头禅。
来源：R2374 基因轮三批候选共 17 条近重预检，9 条 FLAG 弃用（4-gram 池内撞句）。
"""
import io
import json
import re

LIVES = "genes/lives.json"
LANG = "genes/language.json"

HOS = [
    "一本软皮通讯录，边角翻毛，夹页里塞着两张公交车票",
    "半截铅笔插在空罐头瓶里，瓶身贴着没撕净的价签",
]
TPS = [
    "买菜找零摊主多给两毛，他走出去半条街又拐回来还",
    "头一班夜车回家，靠在车窗上看见自家那排窗还留着一盏灯",
]
HAS = [
    "锁门之后必再推一把，确认推不动才走",
]
PRS = [
    "近来惦记给阳台那盆快枯的茉莉换个盆，一直没腾出空",
]
CPS = [
    ("能修的别扔，扔了怪可惜。", "修补"),
    ("不着急，水开了自然有茶。", "温情"),
]


def append(path, key, rendered):
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2):]
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)


before_lives = json.load(io.open(LIVES, encoding="utf-8"))
before_lang = json.load(io.open(LANG, encoding="utf-8"))
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

lives = json.load(io.open(LIVES, encoding="utf-8"))
lang = json.load(io.open(LANG, encoding="utf-8"))
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