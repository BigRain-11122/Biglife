#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""atlas_manifest.py - P-72 census 形象面数据行制（resident-atlas paper-doll manifest）.

每居民一行调色数据（skin/hair/cloth/eye/badge 五 hex）→ census/export/citizen-atlas.jsonl
（R3 再生面·gitignored）。消费方=FluxVerse M2 分层 SpriteRenderer（同一 9 部件图集切片）
+群像墙——万人推演=1 图集+1 数据面，零个体图像文件。

法源：集团令 P-72（docs/orders.md L185·CEO 09-24 ~21:10 居民图集部件化「census 形象面=数据行制转 BigLife」）
·规格=cph4/research/R-20260924-resident-atlas.md §二（9 部件正典+调色交换律·每居民一行五 hex）
+批 1.5 manifest 惯例（cph4/research/sprites-20260924/batch1/manifest.json·只读·字段族同源去 file 面）；
眼色族=CODEX §七.1 形象律（碳源族琥珀 LED 眼+生活暖装/硅源族电光青 LED 眼+机房冷灰/
像素灵=半透明发光小体[skin=发光体色·透明度归渲染层]+机源胸前机器徽记[badge 渲染位]）；
形象面默认深水=PUBLIC-WHITELIST §三律（不入公面直至 T2 登记+显式收录）。

确定性：md5(id) 派生（python hash() 进程随机化——禁用）·分物种槽空间+冲突顺移
→同一 census 输入=逐字节一致；(skin,hair,cloth,badge) 四元组全库唯一（颜色即个性·像素零重复）。
零 LLM·零 API。Usage: python -X utf8 atlas_manifest.py [--qc]
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(CO, "census", "export", "citizen-atlas.jsonl")

ACCENTS = ("#5EEAD4", "#60A5FA", "#4ADE80", "#A78BFA",
           "#F472B6", "#FBBF24", "#FB923C", "#EAB308")

FAMILIES = {
    "carbon": {  # CODEX §七.1 碳源族：琥珀 LED 眼+生活暖装
        "eye": "#FFD27A",
        "skin": ("#C9986B", "#C9A47E", "#D8A87A", "#DBAF85",
                 "#E6B184", "#E8C098", "#CFA070", "#B88A5E"),
        "hair": ("#6B4A32", "#8A4A32", "#2E2A26", "#3E7A72", "#D8D8D0", "#C9A56A",
                 "#5A5A5A", "#6E5A80", "#4A3A2A", "#8C6A4A", "#A8A89E", "#3A3A44"),
        "cloth": ("#A83A3A", "#B3A23E", "#C07A2E", "#4E7A3E", "#9E4E7E", "#3E6E9E",
                  "#3E7A72", "#2E5E4E", "#3A4E7E", "#8A5A3E", "#7A746A", "#B86A4A",
                  "#6E5E3E", "#8E3A5E", "#4A6E8E", "#5E4E2E"),
        "badge": ACCENTS,
    },
    "silicon": {  # CODEX §七.1 硅源族：电光青 LED 眼+机房冷灰
        "eye": "#40F0E0",
        "skin": ("#B8AC98", "#CFC2AC", "#D8C8B0", "#C2B8A8", "#B0C4C8", "#AEBEC0"),
        "hair": ("#2E6E6E", "#C8D4E8", "#8A9AB8", "#9E7EB8",
                 "#5E7E9E", "#7E9EB8", "#4E8E8E", "#88A8C8"),
        "cloth": ("#3E6E9E", "#2E5E4E", "#3A4E7E", "#5E6E7E", "#4E5E6E",
                  "#6E7E8E", "#2E4E6E", "#5E4E7E", "#6E8E9E", "#3E3E50"),
        "badge": ACCENTS,
    },
    "sprite": {  # CODEX §七.1 像素灵：半透明发光小体+机源徽记
        "eye": "#FFD27A",  # 批 1.5 惯例（C-01879/C-02815 均琥珀）
        "skin": ("#40F0E0", "#7DE3FF", "#B388FF", "#69F0AE",
                 "#FFD180", "#FF8A80", "#82B1FF", "#F48FB1"),
        "hair": ("#E0F8FF", "#C5E1FF", "#F8BBD0", "#B9F6CA", "#FFF59D", "#E1BEE7"),
        "cloth": ("#26A69A", "#4DD0E1", "#7E57C2", "#66BB6A",
                  "#FFA726", "#EF5350", "#42A5F5", "#EC407A"),
        "badge": ACCENTS,
    },
}


def shash(cid):
    # stable per-id hash (python hash() is process-randomized - never use it)
    return int(hashlib.md5(str(cid).encode("utf-8")).hexdigest()[:8], 16)


def slot_colors(fam, slot):
    """slot -> (skin, hair, cloth, badge); mixed-radix decompose."""
    nb, nc, nh = len(fam["badge"]), len(fam["cloth"]), len(fam["hair"])
    b_i = slot % nb
    c_i = (slot // nb) % nc
    h_i = (slot // (nb * nc)) % nh
    s_i = slot // (nb * nc * nh)
    return (fam["skin"][s_i], fam["hair"][h_i], fam["cloth"][c_i], fam["badge"][b_i])


def derive_rows(light_rows):
    """hash-seeded slot + collision-walk per species => fixed input, fixed output."""
    used = {"carbon": set(), "silicon": set(), "sprite": set()}
    out = []
    for r in light_rows:
        sp = r.get("species") if r.get("species") in FAMILIES else "carbon"
        fam = FAMILIES[sp]
        total = (len(fam["skin"]) * len(fam["hair"])
                 * len(fam["cloth"]) * len(fam["badge"]))
        slot = shash(r.get("id") or "") % total
        while slot in used[sp]:
            slot = (slot + 1) % total
        used[sp].add(slot)
        skin, hair, cloth, badge = slot_colors(fam, slot)
        out.append({"id": r.get("id"), "name": r.get("name"), "species": sp,
                    "gender": r.get("gender"), "district": r.get("district"),
                    "profession": r.get("profession"),
                    "skin": skin, "hair": hair, "cloth": cloth,
                    "eye": fam["eye"], "badge": badge})
    return out


def main():
    qc_only = "--qc" in sys.argv
    with open(LIGHT, encoding="utf-8") as f:
        light_rows = [json.loads(l) for l in f if l.strip()]

    derived = derive_rows(light_rows)
    lines = [json.dumps(o, ensure_ascii=False, separators=(",", ":")) for o in derived]

    if not qc_only:
        tmp = OUT + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            for ln in lines:
                f.write(ln + "\n")
        os.replace(tmp, OUT)

    # QC pass (always): rows/order/determinism/pool membership/eye family/
    # mirror fields/tuple uniqueness (颜色即个性)
    with open(OUT, encoding="utf-8") as f:
        on_disk = [l.rstrip("\n") for l in f if l.strip()]
    bad = 0
    if len(on_disk) != len(light_rows):
        print("QC FAIL rows %d != light %d" % (len(on_disk), len(light_rows)))
        bad += 1
    tuples = set()
    dup = 0
    for i, ln in enumerate(on_disk):
        if ln != lines[i]:  # determinism: on-disk == same-input re-derive
            bad += 1
        o = json.loads(ln)
        r = derived[i]
        fam = FAMILIES.get(o.get("species"), FAMILIES["carbon"])
        if (o.get("id") != r.get("id") or o.get("eye") != fam["eye"]
                or o.get("skin") not in fam["skin"] or o.get("hair") not in fam["hair"]
                or o.get("cloth") not in fam["cloth"] or o.get("badge") not in fam["badge"]
                or o.get("name") != r.get("name") or o.get("gender") != r.get("gender")
                or o.get("district") != r.get("district")
                or o.get("profession") != r.get("profession")):
            bad += 1
        t = (o.get("skin"), o.get("hair"), o.get("cloth"), o.get("badge"))
        if t in tuples:
            dup += 1
        tuples.add(t)
    n_bytes = sum(len(l.encode("utf-8")) + 1 for l in on_disk)
    sp_count = {}
    for l in on_disk:
        s = json.loads(l)["species"]
        sp_count[s] = sp_count.get(s, 0) + 1
    print("rows=%d bad=%d dup=%d bytes=%d avg=%dB sp=%s" %
          (len(on_disk), bad, dup, n_bytes, n_bytes // max(1, len(on_disk)),
           ",".join("%s:%d" % kv for kv in sorted(sp_count.items()))))
    sys.exit(1 if (bad or dup) else 0)


if __name__ == "__main__":
    main()
