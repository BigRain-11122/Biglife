#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（b42 批）：只取 gene_nearcheck PASS 的 7 条原创追加进
genes/lives.json（补池不换池）。
3 习惯 / 1 钩子物件 / 1 待办 / 1 转折点。
来源：R2383 本班手工候选 16 条 → nearcheck 7 CLEAN 落地，其余 9 条 FLAG 弃用。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

HOS = [
    "阳台上吊着一只旧鸟笼，笼里放着几颗螺丝钉",
]
HAS = [
    "洗完手把水龙头往左再拧半圈，怕漏水",
    "睡前把手机压在一本旧字典下面",
    "洗完脸把毛巾对折挂在杆上，两头一样齐",
    "换下的袜子当天必须过水，说放着过夜会生分",
]
PRS = [
    "想着把阳台上那台旧风扇拆开，给轴承上点油",
]
TPS = [
    "夜市那头一回有人照着招牌念出他的名号，他隔着油锅愣了几秒",
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
    len(before_lives["turning_points"]),
)

append(LIVES, "hook_objects", [json.dumps(x, ensure_ascii=False) for x in HOS])
append(LIVES, "habits", [json.dumps(x, ensure_ascii=False) for x in HAS])
append(LIVES, "presents", [json.dumps(x, ensure_ascii=False) for x in PRS])
append(LIVES, "turning_points", [json.dumps(x, ensure_ascii=False) for x in TPS])

lives = load(LIVES)
after = (
    len(lives["hook_objects"]),
    len(lives["habits"]),
    len(lives["presents"]),
    len(lives["turning_points"]),
)
print("counts before ho=%d ha=%d pr=%d tp=%d -> after ho=%d ha=%d pr=%d tp=%d" % (before + after))
for x in HOS:
    assert x in lives["hook_objects"], x
for x in HAS:
    assert x in lives["habits"], x
for x in PRS:
    assert x in lives["presents"], x
for x in TPS:
    assert x in lives["turning_points"], x
print("verify: all %d landed" % (len(HOS) + len(HAS) + len(PRS) + len(TPS)))