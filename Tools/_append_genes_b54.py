#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b54 基因轮——口头禅 5 / 钩子物件 2 = 7 条。

口径（承 b53「三桶已近饱和」判断，本轮只走薄轴 + 行当器械）：
- catchphrases 1450 条 21 轴，仍薄的 送件(2)/无痕(2)/体面(2)/较真(3)/节俭(2) 各补 1。
- hook_objects 861 条，补 2 条走码头/送货器械面（不做通用生活切片）。

实测（14 条候选跑 Tools/gene_nearcheck.py）：
入选 7 条；被拦 7 条中 6 条败在通用 4-gram（「靠岸先」「还能用三」「手机扣」
「喊一嗓子」「茶凉了」「钉子」「一眼认出」），1 条败在语义近重——
再次证实薄轴已近饱和，本轮不出文艺腔、不出空泛祝愿，只原样追尾。
"""
import json
from pathlib import Path

LANG = "genes/language.json"
LIVES = "genes/lives.json"

NEW_CATCHPHRASES = [
    ("送件", "单子上门牌对不上，就先打个电话，别硬敲。"),
    ("无痕", "抹布收进工具箱，桌上什么都不留。"),
    ("体面", "袖口破了先不缝，把领子熨平要紧。"),
    ("较真", "账本数字对不上，就从第一页重新翻。"),
    ("节俭", "电线头留长两寸，下回接灯不用买新的。"),
]

NEW_HOOK_OBJECTS = [
    "码头水位尺的铅锤",
    "送货摩托的防水包",
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
