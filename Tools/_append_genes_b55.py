#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b55 基因轮——口头禅 7 / 钩子物件 3 = 10 条。

口径（承 b54「薄轴近饱和」判断，本轮只补实测仍薄的轴 + 器械面钩子）：
- catchphrases 1463 条 21 轴，薄轴 跑船(3)/跑腿(4)/手艺(4)/体面(4)/无痕(4)/夜班(5) 各补 1，手艺补 2。
- hook_objects 863 条，补 3 条走秤/雨具/账房器械面（不做通用生活切片）。

实测（Tools/gene_nearcheck.py 两轮共 19 条候选）：
入选 10 条；被拦 9 条多败在通用 4-gram（「也不慌」「先量」「零钱盒」「风再大」
「自行车后」「修鞋摊」「才踏实」「灶台边的」「的公交卡」）。
做法不变：不出文艺腔、不出空泛祝愿，只原样追尾。
"""
import json
from pathlib import Path

LANG = "genes/language.json"
LIVES = "genes/lives.json"

NEW_CATCHPHRASES = [
    ("手艺", "刀刃磨到能剃汗毛，才算收工。"),
    ("手艺", "刨花卷得匀，手就知道刃口正不正。"),
    ("夜班", "灯管闪两下就先记下来，别等它黑。"),
    ("跑船", "上船前先看潮表，急着开不如等着走。"),
    ("体面", "衣角压平了再出门，事没办先有个样。"),
    ("无痕", "走之前把凳子推回墙根，像没人坐过。"),
    ("跑腿", "巷子记在腿上，不用再低头看导航。"),
]

NEW_HOOK_OBJECTS = [
    "秤杆上磨亮的铜星",
    "雨衣内侧贴的线路图",
    "黄铜算盘扣",
]


def append_unique(bucket, items):
    exist = set(bucket)
    added = skipped = 0
    for it in items:
        if it in exist:
            skipped += 1
            continue
        bucket.append(it)
        exist.add(it)
        added += 1
    return added, skipped


def append_catchphrases(bucket, items):
    exist = {x.get("text") for x in bucket}
    added = skipped = 0
    for axis, text in items:
        if text in exist:
            skipped += 1
            continue
        bucket.append({"text": text, "axis": axis})
        exist.add(text)
        added += 1
    return added, skipped


def main():
    lp = Path(LANG)
    lang = json.loads(lp.read_text(encoding="utf-8"))
    c1, cs1 = append_catchphrases(lang["catchphrases"], NEW_CATCHPHRASES)
    lp.write_text(
        json.dumps(lang, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    vp = Path(LIVES)
    lives = json.loads(vp.read_text(encoding="utf-8"))
    a2, s2 = append_unique(lives["hook_objects"], NEW_HOOK_OBJECTS)
    vp.write_text(
        json.dumps(lives, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"catchphrases added={c1} skipped={cs1} total={len(lang['catchphrases'])} | "
        f"hook_objects added={a2} skipped={s2} total={len(lives['hook_objects'])}"
    )


if __name__ == "__main__":
    main()
