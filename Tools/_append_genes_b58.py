# -*- coding: utf-8 -*-
"""基因批 b58：补 8 条（口头禅 3 / 钩子物件 2 / 转折点 2 / 习惯 1）。

先登记后使用（CODEX §十四 人口生态自迭代律）；完全重复即跳过，幂等可重跑。
主题=手艺交接与合力（避开 b56 守摊/旧物/零钱簇、b57 天气/邻里分寸簇）。
全部候选已过 gene_nearcheck（8/8 CLEAN，零近重）。
注意：habits 池属 persona_enrich 冻结面，本批增补将开新世代（老居民按 gen1 冻结池不动）。
"""
import json
import sys

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "活儿赶不得，账糊涂不得。", "axis": "沉稳"},
    {"text": "教会了徒弟不算亏，手艺搁在一个人手里才叫亏。", "axis": "传承"},
    {"text": "受人一升，还人一斗，邻里才长久。", "axis": "人情"},
]

HOOK_OBJECTS = [
    "一把黄铜角尺，边角磕出几个豁口，跟了我大半辈子",
    "一只白铁皮水壶，壶身有一处凹坑，搬家那年磕出来的",
]

TURNING_POINTS = [
    "第一回让后生独自上手做整件活，我蹲在门槛上看，忍住没伸手",
    "那年桥修到一半停了工，整条街凑钱凑料凑人手，完工那天在桥头吃了一顿流水席",
]

HABITS = [
    "每月朔日必把墙上的年历撤下重贴，卷起的塞进木匣",
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

    print(f"b58 catchphrases +{a1} (skip {s1}) / hook_objects +{a2} (skip {s2})")
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
