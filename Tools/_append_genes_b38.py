#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b38）：只取 gene_nearcheck PASS 的 8 条原文追加进
genes/lives.json 与 genes/language.json，既有条目零改动。
2 钩子物件 / 2 转折点 / 1 习惯 / 1 近况 / 2 口头禅。
来源：R2476 基因轮三批候选共 16 条近重预检（state/gene-cand-b38*.txt），8 条 FLAG 弃用。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"
LANG = "genes/language.json"

HOS = [
    "牛仔裤后兜露出半包纸巾和一颗薄荷糖，糖纸磨毛了",
    "抽屉里攒着一把没用过的钥匙，是哪扇门上的早忘了",
]
TPS = [
    "下楼倒垃圾碰上老街坊，俩人站楼道口聊到楼上有人探头喊吃饭",
    "午休蹲在花坛边啃馒头，路过的小孩分了半包榨菜给他",
]
HAS = [
    "吃完晚饭必把碗摞好端到水池，从不等攒够一堆再洗",
]
PRS = [
    "想把车棚里那辆二八车的链条上点油，锈得早转不动了",
]
CPS = [
    ("路近就走着去，省一趟车钱。", "务实"),
    ("少一样也能过，凑齐了才累。", "逍遥"),
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