#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b45 批 habits（生活小动作）8 条。

来源：R2393 让路窗（bm-a 工作日算力让 CEO·年轮/相遇线按 D-20261020-02 延后），
本轮改在基因面补稀面——既有 71 条习惯集中在厨房/钥匙/鞋/碗这类家务门类，
工位（秤、螺丝）、街坊（台阶、门口吵架、抄电表）、循环物（自行车）三面偏空，
故补 8 条落 lives.json。全部过 gene_nearcheck 双层判据（ha 阈值 70）零近重。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

HAS = [
    "修东西前先把拆下的螺丝按位置摆在地上，一颗不差地摆回去",
    "自行车链子每个月上一次油，铃按不响就拿布包着敲两下",
    "听见楼下有人吵架就先关窗，等静下来了才开",
    "打烊前把秤砣拎起来对一遍斤两，秤杆放平了才锁抽屉",
    "三楼台阶有块松砖，雨天先踩一脚试过才让后面的人过",
    "吃完药把空药板剪成小块再扔，说怕人捡了去",
    "每月抄电表多走一趟对门，数字记在自己本子背面",
    "收了别人的袋子，隔天必洗净了还回去",
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


before = len(load(LIVES)["habits"])
fresh = [x for x in HAS if x not in load(LIVES)["habits"]]
append(LIVES, "habits", [json.dumps(x, ensure_ascii=False) for x in fresh])

lives = load(LIVES)
after = len(lives["habits"])
print("habits %d -> %d (appended %d)" % (before, after, len(fresh)))
for x in fresh:
    assert x in lives["habits"], x
assert after == before + len(fresh)
print("verify: all %d landed, pool now %d" % (len(fresh), after))