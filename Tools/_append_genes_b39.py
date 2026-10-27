#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b39）：只取 gene_nearcheck PASS 的 10 条原文追加进
genes/lives.json 与 genes/language.json，既有条目零改动。
2 钩子物件 / 3 转折点 / 2 习惯 / 1 近况 / 2 口头禅。
来源：R-new 基因轮两批候选共 28 条近重预检（state/gene-cand-b39*.txt），18 条 FLAG 弃用。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"
LANG = "genes/language.json"

HOS = [
    "门后那把折叠伞收起来总比别的伞长一截，骨架焊过一回",
    "自行车筐里常年搁着一卷电工胶布，缠车把的活一直没干",
]
TPS = [
    "早上赶着出门，钥匙反锁在屋里，蹲在门口等开锁师傅等了四十分钟",
    "下雨没带伞，跑到公交站檐下，跟一个不认识的人并排站着等雨小",
    "搬来一箱书，楼道拐角歇了三次，隔壁老太太开门递了杯凉白开",
]
HAS = [
    "烧水壶响了不马上去倒，非要等那阵哨音自己落下去",
    "洗完手顺手把台面上的水抹干净，抹布挂回原处",
]
PRS = [
    "想着哪天有空把老相册扫进电脑，怕放久了纸都发脆",
]
CPS = [
    ("不急，等它自己凉。", "秩序"),
    ("能帮就帮一把，举手的事。", "侠气"),
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