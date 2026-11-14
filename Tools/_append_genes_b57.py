# -*- coding: utf-8 -*-
"""基因批 b57：补 8 条（口头禅 3 / 钩子物件 2 / 转折点 2 / 习惯 1）。

先登记后使用（CODEX §十四 人口生态自迭代律）；完全重复即跳过，幂等可重跑。
主题=天气与邻里分寸（避开 b56 的守摊/旧物/零钱簇）。
"""
import json
import sys

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "雨来了先收衣服，事来了先喘口气。", "axis": "从容"},
    {"text": "话到嘴边留半句，路到拐角慢半步。", "axis": "分寸"},
    {"text": "谁家灶上不冒烟，别人家的事少插嘴。", "axis": "邻里"},
]

HOOK_OBJECTS = [
    "一把骨架散了又用铁丝绑回去的油纸伞",
    "铁皮饼干盒改的针线匣，盖子上贴着一张褪色的风景照",
]

TURNING_POINTS = [
    "那年台风夜守着一锅卤汤不敢睡，天亮时整条街只有我这盏灯还亮着——从此街坊路过都要敲敲我的窗",
    "头一回跟人合伙做买卖，账算到最后一分钱对不上就散了伙；往后凡是搭伙先立字据",
]

HABITS = [
    "每晚把第二天的伞和鞋摆在门边，看天色决定摆哪双",
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

    print(f"b57 catchphrases +{a1} (skip {s1}) / hook_objects +{a2} (skip {s2})")
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
