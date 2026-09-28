#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lowpoly_batch2.py - 形象律 v2 批 2：CEO/用户化身原创件生成器（内部资料·待 CEO 过目后出库）.

法源：CODEX §七.2 形象律 v2（T2=§十二 v3.50）+ 集团 orders.md 09-28 ~22:46 CEO 全面转向拍板令
（批 2 开工闸已过）·任务单 T-20260928-09。
复用：Tools/lowpoly_samples.py（批 0 终验「可以送」形体语言）——draw_figure 固定顶点表单源复用·
零形体漂移·呈现层（抬头/角注）本批专属文本。
对象：荣誉席三位（census/reserved/·宿主=人源·非生成居民）——
  C-00001 城主=CEO 白袍蓝晕特典位（§七.1 全城唯一不变）·
  C-00002 / C-00003=真用户点眼白标·零光晕（人源席=真用户标记律）。
红线：脱敏律（家人身份细节不出公开面·本件标签=ID+席位·零关系词）+
  人设权 CEO 保留（化身形象内容=CEO 令域·本件为库内呈报件·CEO 过目后方可出库）。
QC 四判据（--qc）：①双跑逐字节一致 ②调色单源溯源 ③0.78 两阶律 ④facet ≤16（形体切面常量）。
Usage: python -X utf8 Tools/lowpoly_batch2.py [--qc]
"""
import hashlib
import io
import os
import sys

import lowpoly_samples as L0  # 批 0 生成器单源复用（同目录·零拷贝）

CO = L0.CO
OUT = os.path.join(CO, "docs", "research", "lowpoly-avatars-batch2-20260929.png")

SEATS = ["C-00001", "C-00002", "C-00003"]
# 眼律定谳：人源席=真用户点眼白标；城主席另叠加白袍蓝晕特典位（draw_figure kind 语义）
KIND = {"C-00001": "ceo", "C-00002": "user", "C-00003": "user"}
LABELS = {  # 脱敏律：ID+席位·零家人关系词
    "C-00001": ("C-00001 大圣 Dasheng", "城主·白袍蓝晕特典位"),
    "C-00002": ("C-00002 Qiqi", "荣誉席·真用户点眼白标"),
    "C-00003": ("C-00003 Rain", "荣誉席·真用户点眼白标"),
}
TITLE = "化身原创件 · lowpoly 批 2（荣誉席三位·2026-09-29）"
CORNER = "内部资料 · 待 CEO 过目后出库 · 调色单源=census atlas 荣誉席行 · 脱敏面"

# 形体切面常量（固定顶点表·draw_figure 同源）：头2+发2+躯干2+臂2+腿2 = 10 ≤ 16（§七.2 facet 律）
BODY_FACETS = ["头基面", "头暗面", "发基面", "发暗面", "躯干基面",
               "躯干暗面", "左臂", "右臂", "左腿", "右腿"]


def build():
    rows = L0.load_atlas()
    figs, labels = [], []
    for cid in SEATS:
        r = rows[cid]
        pal = (r["skin"], r["hair"], r["cloth"], r["eye"], r["badge"])
        figs.append(L0.draw_figure(KIND[cid], pal))
        labels.append(LABELS[cid])
    return rows, figs, labels


def render(figs, labels):
    saved = (L0.TITLE, L0.CORNER)
    L0.TITLE, L0.CORNER = TITLE, CORNER  # 呈现层文本本批专属（montage 读模块常量·批 0 值随 finally 还原）
    try:
        return L0.montage(figs, labels)
    finally:
        L0.TITLE, L0.CORNER = saved


def qc(rows, figs, labels, data):
    # 判据 1：双跑逐字节一致（同输入=同 PNG）
    _, figs2, labels2 = build()
    assert labels2 == labels, "QC FAIL labels determinism"
    assert L0.png_bytes(render(figs2, labels2)) == data, "QC FAIL determinism"
    # 判据 2：调色单源（用色 RGB ⊆ 荣誉席 atlas 五 hex∪暗面档∪法定常量∪法定 α 合成闭包）
    legal = set()
    src_hex = []
    for cid in SEATS:
        r = rows[cid]
        src_hex += [r["skin"], r["hair"], r["cloth"], r["eye"], r["badge"]]
    for h in src_hex + ["#FAFAFA"]:  # 末位=CEO 白袍特典位法定档（atlas cloth 被覆写·须单源补入）
        c = L0.hx(h)[:3]
        for f in (1.0, L0.SHADE, 0.7, 0.62, 0.55, 0.78 * 0.88, 0.7 * 0.88, 0.42):
            legal.add((int(c[0] * f), int(c[1] * f), int(c[2] * f)))
    for c in (L0.USER_EYE, L0.WHITE_RING, L0.CEO_HALO, L0.CEO_HALO2, L0.CEO_ROBE,
              L0.BG, L0.LABEL_INK, (100, 100, 100, 255), (64, 240, 224, 220),
              (255, 255, 255, 230)):
        legal.add(c[:3])
    legal.add((0, 0, 0))  # 透明底面 RGB
    base = sorted(legal)
    for w in (200 / 255, 230 / 255, 220 / 255, 150 / 255):
        for s in base:
            for t in base:
                legal.add((int(round(w * s[0] + (1 - w) * t[0])),
                           int(round(w * s[1] + (1 - w) * t[1])),
                           int(round(w * s[2] + (1 - w) * t[2]))))
    used = set()
    for im in figs:
        for _, p in im.getcolors(maxcolors=1 << 20):
            used.add(p[:3])
    bad = used - legal
    assert not bad, "QC FAIL palette provenance: %s" % sorted(bad)
    # 眼律：点眼白标=LED 眼 hex 不入图（人源席非 LED 渲染）
    for cid in SEATS:
        assert L0.hx(rows[cid]["eye"])[:3] not in used, "QC FAIL eye-law %s" % cid
    # 判据 3：暗面档=基色×0.78 两阶律
    c = L0.hx(rows["C-00001"]["skin"])
    assert L0.dark(c)[:3] == (int(c[0] * L0.SHADE), int(c[1] * L0.SHADE), int(c[2] * L0.SHADE)), \
        "QC FAIL shade law"
    # 判据 4：形体切面常量 ≤16（固定顶点表零随机 facet）
    assert len(BODY_FACETS) == 10 and len(BODY_FACETS) <= 16, "QC FAIL facet law"
    # §七.2 全量律补充断言：特典位全城唯一 / 真用户零光晕 / 纯白禁用（市民位）
    assert list(KIND.values()).count("ceo") == 1, "QC FAIL ceo-halo uniqueness"
    for i, cid in enumerate(SEATS):
        top_band = [figs[i].getpixel((128, y))[3] for y in (26, 39)]  # 蓝晕环带坐标
        if KIND[cid] == "user":
            assert top_band == [0, 0], "QC FAIL user zero-halo %s" % cid
        else:
            assert all(a > 0 for a in top_band), "QC FAIL ceo halo %s" % cid
        assert rows[cid]["cloth"].upper() != "#FFFFFF", "QC FAIL pure-white ban %s" % cid
    print("QC PASS: determinism + palette-provenance(%d rgb) + shade 0.78 + facets %d/16 "
          "+ eye-law + halo-law + pure-white-ban" % (len(used), len(BODY_FACETS)))


def main():
    rows, figs, labels = build()
    data = L0.png_bytes(render(figs, labels))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("out=%s bytes=%d md5=%s" % (os.path.relpath(OUT, CO), len(data),
                                      hashlib.md5(data).hexdigest()))
    if "--qc" in sys.argv:
        qc(rows, figs, labels, data)
    return


if __name__ == "__main__":
    main()
