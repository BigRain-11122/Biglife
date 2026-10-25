#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（R2114 基因轮·b27）：把 state/gene-cand-b27.txt 的 4 物件+3 转折+2 口头禅+1 习惯
追加进 genes/lives.json 与 genes/language.json。只做原文追加（文本编辑，不整体 dump）。
候选已过 gene_nearcheck 预筛（near=0）。
"""
import io
import json
import re

CAND = "state/gene-cand-b27.txt"
LIVES = "genes/lives.json"
LANG = "genes/language.json"
HABIT = "出门前必把三轮车的刹车捏两下，响不对就不走"

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
for x in hos:
    assert x in lives["hook_objects"], x
for x in tps:
    assert x in lives["turning_points"], x
assert HABIT in lives["habits"]
for tx, _ in cps:
    assert any(c["text"] == tx for c in lang["catchphrases"]), tx
print("readback OK")