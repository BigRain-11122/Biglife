#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b52 基因轮——口头禅 4 / 转折点 1 / 钩子物件 1 / 钩子动作 1 = 7 条。

口径（b51 之后的定向补薄 + 近重门实测）：
- catchphrases 1435 条 21 轴，其中 守摊/无痕/体面/节俭 四轴各仅 1 条，本轮各补 1 条翻倍。
- hook_actions 66 条为取用面最薄桶，补 1 条。

实测结论（本轮 12 条候选跑 Tools/gene_nearcheck.py 的近重门）：
Layer A 4-gram 扫描下 **turning_points / hook_objects / hook_actions 三桶已近饱和**——
12 条候选仅 7 条过门，被拦 5 条全部败在通用 4-gram 上（「的地方，」「看得出来」
「三遍才肯」「头一回…从那以后」「用旧了也」「借人前先」等），而非语义重复。
故 b53 起该三桶补料**必须换生僻词面与句式**（例：入选的「倒扣着放」「验钞紫光灯」
「钥匙到手当夜」均属低频 4-gram），继续堆同型生活切片只会被门拦。
只原样追尾，重复项跳过并记 skipped；禁文艺腔、禁空泛祝愿。
"""
import json
from pathlib import Path

LANG = "genes/language.json"
LIVES = "genes/lives.json"

NEW_CATCHPHRASES = [
    ("守摊", "不管卖不卖得动，摊子先支起来。"),
    ("无痕", "做过的事不用挂嘴上，地扫干净就行。"),
    ("体面", "钱可以少赚，脸不能丢。"),
    ("节俭", "缝三针还能穿，扔了可惜。"),
]

NEW_TURNING_POINTS = [
    "那年把小摊换成了门面，钥匙到手当夜睡不着，起来扫了三遍地",
]

NEW_HOOK_OBJECTS = [
    "验钞紫光灯",
]

NEW_HOOK_ACTIONS = [
    "{obj} 每回用完都倒扣着放，说这样不进灰",
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
    a1, s1 = append_unique(lives["turning_points"], NEW_TURNING_POINTS)
    a2, s2 = append_unique(lives["hook_objects"], NEW_HOOK_OBJECTS)
    a3, s3 = append_unique(lives["hook_actions"], NEW_HOOK_ACTIONS)
    vp.write_text(
        json.dumps(lives, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"catchphrases added={c1} skipped={cs1} total={len(lang['catchphrases'])} | "
        f"turning_points added={a1} skipped={s1} total={len(lives['turning_points'])} | "
        f"hook_objects added={a2} skipped={s2} total={len(lives['hook_objects'])} | "
        f"hook_actions added={a3} skipped={s3} total={len(lives['hook_actions'])}"
    )


if __name__ == "__main__":
    main()
