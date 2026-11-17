"""一次性登记工具：b62 基因轮（2026-11-17 让路窗内确定性产出·零 LLM）

口径（承 b61 近饱和记录·grep 实况 cp1528/ho912/tp698/ha86）：四池已近满，
本轮按「只收不撞」原则四组候选共 20 条送 Tools/gene_nearcheck.py 逐条筛，
最终仅 3 条 CLEAN——开水房/声控灯/理发摊/月票四组母题全部与库内既存条目 4-gram 相撞，
故弃用不堆量。留下三条走「修车行当」母题：口头禅取修旧轴（链条自接），
钩子动作取旧挂历包皮的惜物法，转折点取借车还油的人情账。

全部候选已过近重预检（Layer A 4-gram + Layer B 同池阈值 cp92/ho95/tp55/ha70），
入库前再跑一次预检为门禁。

用法：python -X utf8 Tools/_append_genes_b62.py
"""
import io, json

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "车链子掉了蹲下就能接，别慌。", "axis": "修旧"},
]

HOOK_OBJECTS = []

HOOK_ACTIONS = ["把 {obj} 用旧挂历包上，边上拿浆糊抹平"]

TURNING_POINTS = ["那年把自行车借给对门小子考试，车回来链条上了油，他什么也没说"]


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

    cp_add, cp_skip = append_unique(lang["catchphrases"], CATCHPHRASES)
    tp_add, tp_skip = append_unique(lives["turning_points"], TURNING_POINTS)
    ha_add, ha_skip = append_unique(lives["hook_actions"], HOOK_ACTIONS)
    ho_add, ho_skip = append_unique(lives["hook_objects"], HOOK_OBJECTS)

    save(LANG, lang)
    save(LIVES, lives)

    print(f"cp +{cp_add}/skip{cp_skip}  tp +{tp_add}/skip{tp_skip}  "
          f"ha +{ha_add}/skip{ha_skip}  ho +{ho_add}/skip{ho_skip}")
    print(f"pools: cp={len(lang['catchphrases'])} ho={len(lives['hook_objects'])} "
          f"tp={len(lives['turning_points'])} ha={len(lives['hook_actions'])}")


if __name__ == "__main__":
    main()
