#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b35）：state/gene-cand-b35.txt 中的过闸候选取 2 钩子物+4 转折点+2 口头禅，
追加到 genes/lives.json 与 genes/language.json。只做原文追加，不改动既有条目。
候选已过 gene_nearcheck 预筛（12 候选→8 CLEAN，4 FLAG 弃用，near=0 入册）。"""
import io
import json
import re

CAND = "state/gene-cand-b35.txt"
LIVES = "genes/lives.json"
LANG = "genes/language.json"
# 弃用项（nearcheck FLAG）
DROP = {
    "旧木箱的提手换过三回，木头上的握痕还是原来那道",
    "一只纸糊的灯笼骨架，纸早没了，铁丝还立着",
    "手上的还没做完，别急着接新的。",
    "回话之前先在心里过一遍，别图快。",
}

raw = io.open(CAND, encoding="utf-8-sig").read().splitlines()
hos = [l.split("|", 1)[1].strip() for l in raw if l.startswith("ho|")]
tps = [l.split("|", 1)[1].strip() for l in raw if l.startswith("tp|")]
cps = []
for l in raw:
    if l.startswith("cp|"):
        rest = l.split("|", 1)[1]
        tx, ax = rest.rsplit("|", 1)
        cps.append((tx.strip(), ax.strip()))
hos = [x for x in hos if x not in DROP]
tps = [x for x in tps if x not in DROP]
cps = [(t, a) for t, a in cps if t not in DROP]
assert len(hos) == 2 and len(tps) == 4 and len(cps) == 2, (len(hos), len(tps), len(cps))


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
print("verify: all %d landed" % (len(hos) + len(tps) + len(cps)))