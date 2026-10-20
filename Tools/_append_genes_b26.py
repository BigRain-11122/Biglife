#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（R1842）：把 state/gene-cand-b26.txt 的 4 钩子+3 转折+2 口头禅
追加进 genes/lives.json 与 genes/language.json，保留原排版（文本插入，不做整体 dump）。
候选已经 gene_nearcheck 预检全 CLEAN（near=0）。
"""
import io
import json
import re

CAND = "state/gene-cand-b26.txt"
LIVES = "genes/lives.json"
LANG = "genes/language.json"
HABIT = "出门宁可绕远，也要路过菜市场看看老摊子还开着没"

raw = io.open(CAND, encoding="utf-8").read().splitlines()
hos = [l.split("|", 1)[1].strip() for l in raw if l.startswith("ho|")]
tps = [l.split("|", 1)[1].strip() for l in raw if l.startswith("tp|")]
cps = [(l.split("|")[1].strip(), l.split("|")[2].strip()) for l in raw if l.startswith("cp|")]
assert len(hos) == 4 and len(tps) == 3 and len(cps) == 2, (len(hos), len(tps), len(cps))


def append(path, key, rendered):
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2) :]
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)


append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in hos])
append(LIVES, "turning_points", [json.dumps(x, ensure_ascii=False) for x in tps])
append(LIVES, "habits", [json.dumps(HABIT, ensure_ascii=False)])
append(
    LANG,
    "catchphrases",
    [
        '{\n      "text": %s,\n      "axis": %s\n    }'
        % (json.dumps(tx, ensure_ascii=False), json.dumps(ax, ensure_ascii=False))
        for tx, ax in cps
    ],
)

lives = json.load(io.open(LIVES, encoding="utf-8"))
lang = json.load(io.open(LANG, encoding="utf-8"))
print(
    "counts ho=%d tp=%d habits=%d cp=%d"
    % (
        len(lives["hook_objects"]),
        len(lives["turning_points"]),
        len(lives["habits"]),
        len(lang["catchphrases"]),
    )
)
print("ho751:", lives["hook_objects"][750])
print("tp578:", lives["turning_points"][577])
print("cp1304:", lang["catchphrases"][1304])
print("cp1305:", lang["catchphrases"][1305])
print("habits38:", lives["habits"][38])