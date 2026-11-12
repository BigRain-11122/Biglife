#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b51 基因轮——口头禅 8 / 转折点 5 / 钩子物件 5 / 钩子动作 5。

口径：catchphrases 1427（六主轴上仍有 220+ 存量，担忧点是「功能轴」薄桶：
务实/温情/专注/修补 等每轴仅 1-10 条）、hook_actions 61 为取用面最薄桶。
本轮不再往六主轴堆量，而是补功能轴口头禅 + hook_actions/presents 同族的
生活切片（禁文艺腔、禁空泛祝愿）。只原样追尾，重复项跳过并记 skipped。
"""
import json
from pathlib import Path

LANG = "genes/language.json"
LIVES = "genes/lives.json"

NEW_CATCHPHRASES = [
    ("秩序", "东西归位了，心里才踏实。"),
    ("烟火", "锅里滚着，人就散不了。"),
    ("怀旧", "这味道跟我妈那口锅一个样。"),
    ("逍遥", "走哪算哪，路又不咬人。"),
    ("侠气", "该出手的时候，别算太细。"),
    ("求新", "老法子能成，新法子能快。"),
    ("务实", "多少钱办多少事，别打肿脸。"),
    ("手艺", "手不稳，就别怪料不好。"),
]

NEW_TURNING_POINTS = [
    "头一回被人叫师傅，愣了半天才应声，回头把满手的茧看了又看",
    "城庆那晚收工晚，一个人在桥上看灯，忽然明白自己也算这城里的一盏",
    "把攒了三年的钱借给邻居救急，第二年对方真还了，从此肯信人",
    "第一次修好一件别人都说没救的老物件，从此不肯轻易说报废",
    "有一年冬天下大雪，铺子没客，索性把门开着，让赶路的人进来暖手",
]

NEW_HOOK_OBJECTS = [
    "搪瓷缸子",
    "铁皮饼干盒",
    "铜顶针",
    "半导体收音机",
    "公交月票夹",
]

NEW_HOOK_ACTIONS = [
    "会把 {obj} 里外擦一遍才收起来",
    "给 {obj} 缝了个布套，怕磕碰",
    "{obj} 从不外借，但愿意给人看看",
    "出门前必摸一下 {obj} 还在不在兜里",
    "把 {obj} 摆在柜台最显眼的地方，说这叫镇店",
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
