#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（R2242 基因轮·b31）：读 state/gene-cand-b31.txt 的 5 钩子物件+3 转折点+4 口头禅，
追加进 genes/lives.json 与 genes/language.json。只做原文追加，不改动既有条目（不整体 dump）。
候选已过 gene_nearcheck 预筛（near=0·12/12 CLEAN，三轮改写后收敛）。沿用 b30 范式；
本批口头禅偏向薄轴（务实/专注/温情），补口头禅轴分布长尾。
"""
import io
import json
import re

CAND = "state/gene-cand-b31.txt"
LIVES = "genes/lives.json"
LANG = "genes/language.json"

raw = io.open(CAND, encoding="utf-8").read().splitlines()
hos = [l.split("|", 1)[1].strip() for l in raw if l.startswith("ho|")]
tps = [l.split("|", 1)[1].strip() for l in raw if l.startswith("tp|")]
cps = [(l.split("|")[1].strip(), l.split("|")[2].strip()) for l in raw if l.startswith("cp|")]
assert len(hos) == 5 and len(tps) == 3 and len(cps) == 4, (len(hos), len(tps), len(cps))


def append(path, key, rendered):
    t = io.open(path, encoding="utf-8").read()
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2) :]
    io.open(path, "w", encoding="utf-8", newline="\n").write(t)


before_lives = json.load(io.open(LIVES, encoding="utf-8"))
before_lang = json.load(io.open(LANG, encoding="utf-8"))
before = (
    len(before_lives["hook_objects"]),
    len(before_lives["turning_points"]),
    len(before_lang["catchphrases"]),
)

append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in hos])
append(LIVES, "turning_points", [json.dumps(x, ensure_ascii=False) for x in tps])
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
after = (len(lives["hook_objects"]), len(lives["turning_points"]), len(lang["catchphrases"]))
print("counts before ho=%d tp=%d cp=%d -> after ho=%d tp=%d cp=%d" % (before + after))
for x in hos:
    assert x in lives["hook_objects"], x
for x in tps:
    assert x in lives["turning_points"], x
for tx, ax in cps:
    assert any(e.get("text") == tx and e.get("axis") == ax for e in lang["catchphrases"]), tx
print("verify: all 12 landed")