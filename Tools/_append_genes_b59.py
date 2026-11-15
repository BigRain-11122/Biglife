# -*- coding: utf-8 -*-
"""基因批 b59：补 8 条（口头禅 3 / 钩子物件 2 / 转折点 3）。

先登记后使用（CODEX §十四 人口生态自迭代律）；完全重复即跳过，幂等可重跑。
主题=录音机代录与听广播（避开 b56 守摊/旧物/零钱罐、b57 天气/邻里分摊、b58 手艺交接/修桥）。
关键词查重：点播 0 / 单卡录音机 0 / 带子抽屉 0；磁带 4、录音 6 均为不同情境，零近似重复。
注意：本批不动 habits 池（persona_enrich 冻结面），世代开关由 persona_generations --sync 决定。
"""
import json
import sys

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "好节目错过就错过了，录下来才算自己的。", "axis": "怀旧"},
    {"text": "带子借出去要记账，还回来要试一遍。", "axis": "较真"},
    {"text": "屋里有个响动，人就不算一个人住。", "axis": "温情"},
]

HOOK_OBJECTS = [
    "一台按键磨圆的单卡录音机，喇叭网罩上贴着一小块透明胶",
    "一整抽屉手写标签的旧磁带，字迹从圆珠笔换成了签字笔",
]

TURNING_POINTS = [
    "头一回替邻居整夜守着录音机录一档评书，天亮交带子时人家塞给我两个鸡蛋",
    "那年把攒了半年的带子借给巷尾的学生考外语，还回来时断了一截，他自己拿胶带接上了",
    "广播里念到我写的点播信那晚，全家围在桌前没敢出声，等我名字念完才一起笑出来",
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

    total_added = a1 + a2 + a3
    if total_added:
        save(LANG, lang)
        save(LIVES, lives)

    print(f"b59 catchphrases +{a1} (skip {s1}) / hook_objects +{a2} (skip {s2})")
    print(f"    turning_points +{a3} (skip {s3})")
    print(
        "    totals: cp=%d obj=%d tp=%d habit=%d"
        % (
            len(lang["catchphrases"]),
            len(lives["hook_objects"]),
            len(lives["turning_points"]),
            len(lives["habits"]),
        )
    )
    print("ADDED=%d SKIPPED=%d" % (total_added, s1 + s2 + s3))
    return 0 if total_added or (s1 + s2 + s3) else 1


if __name__ == "__main__":
    sys.exit(main())
