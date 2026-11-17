"""一次性登记工具：b61 基因轮（2026-11-17 让路窗内确定性产出·零 LLM）

口径（承 b52/b60 近饱和记录）：四池已至 cp1526/ho910/tp698/ha85，通用切片不再堆量。
本轮取「手艺与担子」母题——口头禅走修表/挑担两轴（手艺、逍遥），
钩子物件补两件雨天与报修同族的小物（干袜子、报修单），钩子动作补一条署名制，
用「怕和人家的混了」立分寸感。

全部候选已过 Tools/gene_nearcheck.py 近重预检（Layer A 4-gram + Layer B 同池阈值），
命中项已弃用换句；入库前再跑一次预检为门禁。

用法：python -X utf8 Tools/_append_genes_b61.py
"""
import io, json

LANG = "genes/language.json"
LIVES = "genes/lives.json"

CATCHPHRASES = [
    {"text": "修表这行当，眼睛比手指更要紧。", "axis": "手艺"},
    {"text": "担子挑得动就多挑一程，天黑前总能到。", "axis": "逍遥"},
]

HOOK_OBJECTS = ["一双叠得整齐的干袜子", "一张折了四折的报修单"]

HOOK_ACTIONS = ["给 {obj} 写上自己的姓，怕和人家的混了"]


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
    ho_add, ho_skip = append_unique(lives["hook_objects"], HOOK_OBJECTS)
    ha_add, ha_skip = append_unique(lives["hook_actions"], HOOK_ACTIONS)

    save(LANG, lang)
    save(LIVES, lives)

    print(f"cp +{cp_add}/skip{cp_skip}  ho +{ho_add}/skip{ho_skip}  ha +{ha_add}/skip{ha_skip}")
    print(f"pools: cp={len(lang['catchphrases'])} ho={len(lives['hook_objects'])} ha={len(lives['hook_actions'])}")


if __name__ == "__main__":
    main()
