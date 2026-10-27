#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b41）：只取 gene_nearcheck PASS 的 10 条原文追加进
genes/lives.json，既有条目零改动。
4 近况 / 4 习惯 / 2 钩子物件——本批按薄轴配平（pr 49→53、ha 50→54、ho 832→834）。
来源：R-new 基因轮候选 13 条（state/gene-cand-b41.txt），3 条近重 FLAG 换句复验后入册。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

HOS = [
    "窗台上压着半块砖头，压的是一双晾着的鞋垫",
    "衣柜顶上放着一只空的鱼缸，里面塞着几张旧报纸",
]
HAS = [
    "出门前总要把拖鞋摆正对着门",
    "吃完饭先把碗泡上水才离开桌子",
    "钥匙挂上门后的钩子才肯换鞋",
    "下楼顺手把对门的快递挪到门缝里",
]
PRS = [
    "惦记着去旧书摊把那套连环画凑齐",
    "打算趁着秋天把窗帘摘下来洗一遍",
    "想着把厨房抽油烟机里的油盒拆下来泡一夜",
    "盘算着下月把老屋的木门重新刷一遍漆",
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
before = (
    len(before_lives["hook_objects"]),
    len(before_lives["habits"]),
    len(before_lives["presents"]),
)

append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in HOS])
append(LIVES, "habits", [json.dumps(x, ensure_ascii=False) for x in HAS])
append(LIVES, "presents", [json.dumps(x, ensure_ascii=False) for x in PRS])

lives = load(LIVES)
after = (
    len(lives["hook_objects"]),
    len(lives["habits"]),
    len(lives["presents"]),
)
print("counts before ho=%d ha=%d pr=%d -> after ho=%d ha=%d pr=%d" % (before + after))
for x in HOS:
    assert x in lives["hook_objects"], x
for x in HAS:
    assert x in lives["habits"], x
for x in PRS:
    assert x in lives["presents"], x
print("verify: all %d landed" % (len(HOS) + len(HAS) + len(PRS)))