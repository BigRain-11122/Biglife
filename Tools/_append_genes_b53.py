#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b53 基因轮——口头禅 3 / 转折点 1 / 钩子物件 3 / 钩子动作 1 = 8 条。

口径（承 b52 留下的 b53 补料令：三桶必须换生僻词面与句式）：
- catchphrases 1439 条 21 轴，取仍薄的 跑腿(2)/实干(3)/守摊(2) 各补 1，均取运输-摊档母题。
- hook_actions 67 条仍为最薄桶，本轮补 1 条（句式走「姿态+持续动作」而非「用完就放」族）。
- hook_objects / turning_points 一律回避通用生活切片 4-gram，改用行当器械与水文时序词面。

实测（16 条候选跑 Tools/gene_nearcheck.py，两批各 12/4）：
入选 8 条；被拦 8 条全部败在通用 4-gram 上而非语义重复——
「慢一点，」「天塌了」「擦一遍，」「钉子上了」「，他把」「那年…鞋里能倒出水」
「抄在烟盒」「第一笔工钱」「边角磨圆」等，证实 b52 的「三桶已近饱和」判断仍在有效期内。
禁文艺腔、禁空泛祝愿。只原样追尾，重复项跳过并记 skipped。
"""
import json
from pathlib import Path

LANG = "genes/language.json"
LIVES = "genes/lives.json"

NEW_CATCHPHRASES = [
    ("跑腿", "拐两个弯的事，别在路口站着想。"),
    ("实干", "说得再好，不如先量一遍尺寸。"),
    ("守摊", "秤可以少一两，话不能多一句。"),
]

NEW_TURNING_POINTS = [
    "潮水退到第三个桥墩，缆绳重编了一夜，编到手指发白也没停",
]

NEW_HOOK_OBJECTS = [
    "渡口铁皮票夹",
    "送件摩托的麻绳扣",
    "船用铜哨",
]

NEW_HOOK_ACTIONS = [
    "{obj} 摆在膝上，颠簸那截路一直用手按着",
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
