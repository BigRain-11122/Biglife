"""一次性登记工具：b60 基因轮（2026-11-16 让路窗内确定性产出·零 LLM）

口径（承 b52 近饱和记录）：不往通用生活切片堆量，取「城市机器面」母题——
口头禅走修补/夜班/脚力/人情四轴；turning_points 走光桥停电与档案馆还卷宗两件城事；
hook_objects 只补 1 条（电池，与停电事件同族）；hook_actions 补 2 条（借出/记日期），
首版「把 {obj} 借给新来的」4-gram 0.33 撞旧卡已弃用，改「上油养护」句式。

用法：python -X utf8 Tools/_append_genes_b60.py
"""
import io, json

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "东西坏了先别扔，拆开看看是哪颗螺丝松了。", "axis": "较真"},
    {"text": "夜班回来先喝口热的，话留到天亮再说。", "axis": "温情"},
    {"text": "路远不打紧，脚力是自己的功夫。", "axis": "逍遥"},
    {"text": "账可以欠，人情不能欠两回。", "axis": "烟火"},
]

TURNING_POINTS = [
    "光桥市集那晚停电，靠着几盏应急灯把最后三笔生意做完——那以后兜里常年揣着两节电池",
    "档案馆闭馆前一刻，把一个借了半年的卷宗亲手还回去——管理员只说了一句，往后档案随他查",
]

HOOK_OBJECTS = ["两节备用电池"]

HOOK_ACTIONS = [
    "逢潮就给 {obj} 上一层油，说机器跟人一样要养",
    "在 {obj} 背面写下当天的日期",
]

DROP_HOOK_ACTIONS = ["把 {obj} 借给新来的，只说用完还回来就行"]


def load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def append_unique(bucket, items):
    added = skipped = 0
    for it in items:
        if it in bucket:
            skipped += 1
            continue
        bucket.append(it)
        added += 1
    return added, skipped


def main():
    lang, lives = load(LANG), load(LIVES)

    dropped = 0
    for bad in DROP_HOOK_ACTIONS:
        while bad in lives["hook_actions"]:
            lives["hook_actions"].remove(bad)
            dropped += 1

    c1, cs1 = append_unique(lang["catchphrases"], CATCHPHRASES)
    a1, s1 = append_unique(lives["turning_points"], TURNING_POINTS)
    a2, s2 = append_unique(lives["hook_objects"], HOOK_OBJECTS)
    a3, s3 = append_unique(lives["hook_actions"], HOOK_ACTIONS)

    save(LANG, lang)
    save(LIVES, lives)

    for e in CATCHPHRASES:
        assert e in lang["catchphrases"], e
    for e in TURNING_POINTS:
        assert e in lives["turning_points"], e
    for e in HOOK_OBJECTS:
        assert e in lives["hook_objects"], e
    for e in HOOK_ACTIONS:
        assert e in lives["hook_actions"], e

    print(
        "b60 catchphrases +%d (skip %d, total %d) | turning_points +%d (skip %d, total %d) | "
        "hook_objects +%d (skip %d, total %d) | hook_actions +%d (skip %d, total %d, dropped-low-quality %d)"
        % (
            c1, cs1, len(lang["catchphrases"]),
            a1, s1, len(lives["turning_points"]),
            a2, s2, len(lives["hook_objects"]),
            a3, s3, len(lives["hook_actions"]), dropped,
        )
    )


if __name__ == "__main__":
    main()
