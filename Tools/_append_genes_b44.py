#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b44 批，只取 gene_nearcheck PASS 的 11 条原创习惯（ha）
追加进 genes/lives.json（幂等：已在库则跳过）。

选型依据（R2388 让路窗零 LLM 确定性产出）：基因账本显示 catchphrases 1399 条
（供过于求 3.5 倍，used 403），而 habits=61 是最稀缺的 gated 型池——每位居民
都从同一个 61 条池里取习惯，这是年轮「相似度高」的结构性来源之一。本轮只补
稀缺面，不再往饱和面堆量。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

HAS = [
    "洗完碗先把水池滤网里的菜叶倒进垃圾桶，再擦一遍台面",
    "睡前把第二天要穿的衣服搭在椅背上，袜子压在裤腿下面",
    "刷牙时另一只手扶着洗手台边缘，站稳了再低头漱口",
    "晾衣服前把每件T恤的领口拉平，肩线对齐才挂上杆",
    "吃饭时把手机反扣在桌角，屏幕朝下",
    "进门换鞋把鞋尖一律朝里摆齐",
    "炒菜前把调料瓶挨个拧开摆在灶边",
    "每周六早上先用干布抹一遍窗台，再换湿布擦",
    "出门倒垃圾顺手把楼道灯挨个按一遍，看哪个不亮",
    "洗头前先用梳子把头发梳顺，从发尾往上梳",
    "电话响到第三声才伸手去接",
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