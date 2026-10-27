#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b50 基因轮——补薄桶 presents(62) + hook_actions(51)。

口径：presents 62 / hook_actions 51 对 10114 席居民属最薄两桶，重复率高；
本轮各补 10 / 8 条，全部为日常可验证的生活切片（禁文艺腔、禁空泛祝愿）。
只原样追尾，不做去重改写；重复项跳过并记 skipped。
"""
import json
from pathlib import Path

LIVES = "genes/lives.json"

NEW_PRESENTS = [
    "正攒钱买台二手洗衣机，说冬天手洗实在遭罪",
    "这两天在教隔壁小孩写名字，一笔一划，写完自己先笑了",
    "心里惦记着把楼道的声控灯修好，晚上回来总是要拍半天",
    "近来常去图书馆蹭空调，说那里的报纸是新的，人也是新的",
    "正跟人商量把屋顶租出去装太阳能板，谈了半年还没谈拢",
    "最近迷上用手机拍菜市场的价签，说攒着比价用",
    "开始每天早起半小时跑步，跑得慢，但一天不落",
    "正琢磨着给社区旧书角添个箱子，捐的人多，没人整理",
    "把楼下的信箱钥匙配了几把，分给同楼的几户",
    "被拉去当业委会的记账，一笔一笔抄，抄得手酸但心里踏实",
]

NEW_HOOK_ACTIONS = [
    "逢年过节给 {obj} 换一根新线绳",
    "出门必回头看一眼 {obj} 摆正了没有",
    "用 {obj} 给不认识的人指过路",
    "把 {obj} 借给新搬来的邻居垫桌脚",
    "每年入冬前给 {obj} 裹一层旧布",
    "拿 {obj} 当尺子量过家里所有家具",
    "跟 {obj} 说过一句只有它听得懂的道歉",
    "用 {obj} 垫着写信，字都写得更直了",
]


def append_unique(bucket: list, items: list) -> tuple:
    exist = set(bucket)
    added, skipped = 0, 0
    for it in items:
        if it in exist:
            skipped += 1
            continue
        bucket.append(it)
        exist.add(it)
        added += 1
    return added, skipped


def main():
    path = Path(LIVES)
    data = json.loads(path.read_text(encoding="utf-8"))
    a1, s1 = append_unique(data["presents"], NEW_PRESENTS)
    a2, s2 = append_unique(data["hook_actions"], NEW_HOOK_ACTIONS)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"presents added={a1} skipped={s1} total={len(data['presents'])} | "
        f"hook_actions added={a2} skipped={s2} total={len(data['hook_actions'])}"
    )


if __name__ == "__main__":
    main()