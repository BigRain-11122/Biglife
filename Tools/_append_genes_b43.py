#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b43 批，只取 gene_nearcheck PASS 的 8 条原创追加进
genes/lives.json（幂等不重载）。
4 钩子物件 / 1 随身物 / 3 习惯。
来源：R2387 让路窗零 LLM 确定性产出——16+8 候选过 nearcheck 双闸，8 CLEAN 落地，
其余 FLAG 弃用不替换。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

HOS = [
    "楼道声控灯的灯泡，塑料罩子上积了一层灰",
    "阳台外挑的晾衣杆上卡着三个颜色不一的塑料夹",
    "老式防盗门的猫眼镜片被摸得发白",
    "电饭煲的蒸汽嘴套着一段旧胶管，把气导到窗边",
]
HAS = [
    "下班路过菜场一定绕到最里面那家，看看当天还剩什么",
    "进楼道先跺一下脚，把声控灯叫醒再上楼",
    "买菜回来先把零钱按面额理好收进铁罐",
]
PRS = [
    "一沓按年份订好的公交卡，最早那张已经刷不上",
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
print("verify: all %d landed" % (len(HOS) + len(HAS) + len(PRS)))