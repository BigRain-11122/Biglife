#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b36）：落在 state/gene-cand-b36c.txt 之前的三批候选中，
只取 gene_nearcheck PASS 的 5 条（2 钩子物件 / 1 转折点 / 2 口头禅）原文追加进
genes/lives.json 与 genes/language.json，既有条目零改动。
来源：b36（cp「先坐着，水马上就开。」）=CLEAN；b36b（ho 铝饭勺 / tp 澡堂遇班主任 / cp 先称一称）=CLEAN；
b36c（ho 米票 / cp 先把手擦干）=CLEAN；其余 25 条近重候选弃用。
"""
import io
import json
import re

LIVES = "genes/lives.json"
LANG = "genes/language.json"

HOS = [
    "一把铝制饭勺，勺柄缠着医用胶布，胶布早就发黄了",
    "铁皮铅笔盒底层压着一张米票，面额五十克，边角已经卷了",
]
TPS = [
    "冬天在澡堂排队，撞见班主任也在等位，两人都没好意思先开口",
]
CPS = [
    ("先坐着，水马上就开。", "烟火"),
    ("先把手擦干，再碰本子。", "秩序"),
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
    len(before_lang["catchphrases"]),
)

append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in HOS])
append(LIVES, "turning_points", [json.dumps(x, ensure_ascii=False) for x in TPS])
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
after = (len(lives["hook_objects"]), len(lives["turning_points"]), len(lang["catchphrases"]))
print("counts before ho=%d tp=%d cp=%d -> after ho=%d tp=%d cp=%d" % (before + after))
for x in HOS:
    assert x in lives["hook_objects"], x
for x in TPS:
    assert x in lives["turning_points"], x
for tx, ax in CPS:
    assert any(e.get("text") == tx and e.get("axis") == ax for e in lang["catchphrases"]), tx
print("verify: all %d landed" % (len(HOS) + len(TPS) + len(CPS)))