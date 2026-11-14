# -*- coding: utf-8 -*-
"""基因批 b56：补 8 条（口头禅 3 / 钩子物件 2 / 转折点 2 / 习惯 1）。

先登记后使用（CODEX §十四 人口生态自迭代律）；完全重复即跳过，幂等可重跑。
"""
import json
import sys

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "生意做的是回头客，不是头一回。", "axis": "守摊"},
    {"text": "再赶也得吃口热的，凉了的东西不养人。", "axis": "烟火"},
    {"text": "东西旧了不丢人，糊弄人才丢人。", "axis": "修补"},
]

HOOK_OBJECTS = [
    "一只掉了漆的搪瓷缸，杯沿磕出两个豁口",
    "半截粉笔头，揣在裤兜里磨得发圆",
]

TURNING_POINTS = [
    "那年冬天雨水多，铺子的门板泡发了，撬了三回才合上——往后每逢阴天头一件事就是看门轴",
    "头一回被邻街的师傅叫去帮着看活，紧张得一宿没睡，第二天上手却稳得出奇",
]

HABITS = [
    "关门前把当天的零钱码一遍，角票压在最小的那摞底下",
]


def append_unique(bucket, items):
    added, skipped = 0, 0
    for it in items:
        key = it if isinstance(it, str) else it.get("text")
        exists = any((x if isinstance(x, str) else x.get("text")) == key for x in bucket)
        if exists:
            skipped += 1
            continue
        bucket.append(it)
        added += 1
    return added, skipped


def save(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    lang = json.load(open(LANG, encoding="utf-8"))
    lives = json.load(open(LIVES, encoding="utf-8"))

    a1, s1 = append_unique(lang["catchphrases"], CATCHPHRASES)
    a2, s2 = append_unique(lives["hook_objects"], HOOK_OBJECTS)
    a3, s3 = append_unique(lives["turning_points"], TURNING_POINTS)
    a4, s4 = append_unique(lives["habits"], HABITS)

    total_added = a1 + a2 + a3 + a4
    if total_added:
        save(LANG, lang)
        save(LIVES, lives)

    print(f"b56 catchphrases +{a1} (skip {s1}) / hook_objects +{a2} (skip {s2})")
    print(f"    turning_points +{a3} (skip {s3}) / habits +{a4} (skip {s4})")
    print(
        "    totals: cp=%d obj=%d tp=%d habit=%d"
        % (
            len(lang["catchphrases"]),
            len(lives["hook_objects"]),
            len(lives["turning_points"]),
            len(lives["habits"]),
        )
    )
    print("ADDED=%d SKIPPED=%d" % (total_added, s1 + s2 + s3 + s4))
    return 0 if total_added or (s1 + s2 + s3 + s4) else 1


if __name__ == "__main__":
    sys.exit(main())
