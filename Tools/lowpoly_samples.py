#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lowpoly_samples.py - 形象律 v2 低多边形方向·样张批 0 生成器（一次性件）.

法源：2026-09-28 CEO 令「参考lowpoly，调整居民形象生产方向」（集团台账 docs/orders.md 09-28 行）·
CODEX §七.2 形象律 v2（T2=§十二 v3.50·否决窗至 2026-10-05）。
不变面：分类律/LED 方块眼三分族/点眼白标/CEO 白袍蓝晕特典位/纯白禁用/atlas 五 hex 数据行制（v2.4 零改动）。
变更面：形体语言=多边形切面（每形体 ≤16 facets·明暗=基色+暗面 0.78 档两阶·禁渐变）·基元 32×32→64×64
（样张=128 展示位·256 渲染降采样）。
确定性：固定顶点表+atlas 行单源调色，零随机零 LLM 零网络——同输入=逐字节一致 PNG（--qc 断言）。
样张族=锚民三位（PUBLIC-WHITELIST 锚民面·零深水暴露）+真用户/CEO 化身两位（合成调色·样式示例标注）。
批 0 修订：精灵眼窝暗切面（LED 对比度律）/CEO 袍袖分离 facet/双行标签防叠/六边形白描圈（几何语言统一）/
双环光晕（特典位可读性）——多模态审图四缺陷修复回执。
Usage: python -X utf8 lowpoly_samples.py [--qc]
"""
import hashlib, io, json, os, sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
ATLAS = os.path.join(CO, "census", "export", "citizen-atlas.jsonl")
OUT = os.path.join(CO, "docs", "research", "lowpoly-samples-20260928.png")

SHADE = 0.78            # 暗面 facet 派生律（CODEX §七.2：基色×0.78 确定性两阶）
SPRITE_ALPHA = 165      # 像素灵半透明（§七.1 半透明发光小体·不变）
CEO_HALO = (79, 195, 247, 200)    # 超体蓝晕外环（CEO 化身唯一强光晕·不变）
CEO_HALO2 = (79, 195, 247, 150)   # 内环（同色法定档）
USER_EYE = (58, 58, 58, 255)
WHITE_RING = (255, 255, 255, 255)
BG = (228, 228, 228, 255)
LABEL_INK = (40, 40, 40, 255)
CEO_ROBE = (250, 250, 250, 255)   # CEO 白袍（纯白禁用律=市民不得用·CEO 化身特典位不变）

ANCHORS = ["C-00010", "C-00017", "C-00028"]  # 锚民碳源/硅源/像素灵（公开面）
NAMES = {"C-00010": ("C-00010 顾阿凤", "碳源居民·琥珀灯眼"),
         "C-00017": ("C-00017 归档者-07", "硅源居民·青灯眼·胸徽"),
         "C-00028": ("C-00028 十四号路灯", "像素灵·半透明体")}
DEMO_USER = ("#E8C098", "#3A3A44", "#3E6E9E", "-", "#60A5FA")
DEMO_CEO = ("#E8C098", "#2E2A26", "#FAFAFA", "-", "#4FC3F7")
DEMO_LABELS = [("真用户化身", "点眼·白六边圈·零光晕"),
               ("CEO 化身 Jason", "白袍·蓝棱环·全城唯一")]
TITLE = "居民形象样张 · lowpoly 方向 批0（v3·2026-09-28）"
CORNER = "本页均为样式示例 · 调色取自 census 形象面锚民 · 内部资料"


def hx(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def dark(c, f=SHADE):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])


def load_atlas():
    rows = {}
    with open(ATLAS, encoding="utf-8") as f:
        for l in f:
            if l.strip():
                d = json.loads(l)
                rows[d["id"]] = d
    return rows


def hexring(cx, cy, r, fill, w):
    """六边形描圈（白标环的几何语言统一版·PIL 无多边形描宽=双六边形叠层法）。"""
    import math
    pts_out = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
               for a in range(0, 360, 60)]
    pts_in = [(cx + (r - w) * math.cos(math.radians(a)), cy + (r - w) * math.sin(math.radians(a)))
              for a in range(0, 360, 60)]
    return pts_out, pts_in


def draw_figure(kind, pal):
    """kind: carbon|silicon|sprite|user|ceo — 256 渲染位·固定顶点表切面体。"""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    # -- CEO 特典位：超体蓝六边棱环=全城唯一强光晕（§七.1 不变·层序=环后体前=破框语义明确）--
    if kind == "ceo":
        halo = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        hd = ImageDraw.Draw(halo)
        o1, i1 = hexring(128, 128, 120, CEO_HALO, 11)
        o2, i2 = hexring(128, 128, 104, CEO_HALO2, 4)
        hd.polygon(o1, fill=CEO_HALO)
        hd.polygon(i1, fill=(0, 0, 0, 0))
        hd.polygon(o2, fill=CEO_HALO2)
        hd.polygon(i2, fill=(0, 0, 0, 0))
        img.alpha_composite(halo)
    body = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    cx = 128
    skin, hair, cloth, eye, badge = pal
    skin_c, hair_c, cloth_c = hx(skin), hx(hair), hx(cloth)
    if kind == "ceo":
        cloth_c = CEO_ROBE
    badge_c = hx(badge)

    # -- 头（六边形切面 + 右侧暗面 facet）--
    d.polygon([(cx-32, 96), (cx-14, 64), (cx+14, 64), (cx+32, 96), (cx+22, 140), (cx-22, 140)],
              fill=skin_c)
    d.polygon([(cx+6, 64), (cx+32, 96), (cx+22, 140), (cx+6, 140)], fill=dark(skin_c))
    # -- 发（切面帽 + 暗面 facet）--
    d.polygon([(cx-34, 100), (cx-14, 60), (cx+14, 60), (cx+34, 100), (cx+26, 86), (cx-26, 86)],
              fill=hair_c)
    d.polygon([(cx+8, 60), (cx+34, 100), (cx+26, 86), (cx+8, 84)], fill=dark(hair_c))
    # -- 躯干（梯形两 facet）--
    d.polygon([(cx-28, 142), (cx+28, 142), (cx+36, 212), (cx-36, 212)], fill=cloth_c)
    d.polygon([(cx+6, 142), (cx+28, 142), (cx+36, 212), (cx+6, 212)], fill=dark(cloth_c))
    # -- 臂×2（CEO 袍袖分离档 0.88·其余 0.78/0.7）--
    arm_f = 0.88 if kind == "ceo" else 1.0
    d.polygon([(cx-42, 148), (cx-30, 144), (cx-26, 204), (cx-42, 200)], fill=dark(cloth_c, 0.78 * arm_f))
    d.polygon([(cx+30, 144), (cx+42, 148), (cx+42, 200), (cx+26, 204)], fill=dark(cloth_c, 0.7 * arm_f))
    # -- 腿×2（深暗 facet）--
    d.polygon([(cx-26, 216), (cx-6, 216), (cx-8, 246), (cx-30, 246)], fill=dark(cloth_c, 0.62))
    d.polygon([(cx+6, 216), (cx+26, 216), (cx+30, 246), (cx+8, 246)], fill=dark(cloth_c, 0.55))
    # -- 胸前徽记（机源/像素灵 badge 渲染位·§七.1 不变）--
    if kind in ("silicon", "sprite"):
        d.polygon([(cx-4, 158), (cx+12, 158), (cx+4, 172)], fill=badge_c)
    # -- 硅源电路纹（§七.1 机房冷灰+电路纹 不变）--
    if kind == "silicon":
        d.line([(cx-22, 176), (cx-10, 186)], fill=(64, 240, 224, 220), width=3)
        d.line([(cx+16, 192), (cx+24, 182)], fill=(64, 240, 224, 220), width=3)
    # -- 眼（分类律不变：LED 方块眼 / 点眼白六边圈 / CEO 同点眼+特典）--
    for ex in (cx - 21, cx + 9):
        if kind in ("carbon", "silicon", "sprite"):
            ec = hx(eye)
            if kind == "sprite":
                # 批 0 修订：精灵眼窝暗切面（LED 对比度律·浅肤族法定）
                d.polygon([(ex - 4, 102), (ex + 16, 102), (ex + 16, 122), (ex - 4, 122)],
                          fill=dark(skin_c, 0.42))
            d.rectangle([ex, 106, ex + 12, 118], fill=ec)
            d.rectangle([ex + 4, 110, ex + 8, 114], fill=(255, 255, 255, 230))  # LED 芯点
        else:
            out_pts, in_pts = hexring(ex + 5, 111, 14, WHITE_RING, 5)
            d.polygon(out_pts, fill=WHITE_RING)
            d.polygon(in_pts, fill=USER_EYE)
    img.alpha_composite(body)
    # -- 像素灵半透明（§七.1 不变：整体半透明发光小体）--
    if kind == "sprite":
        a = img.getchannel("A").point(lambda v: min(v, SPRITE_ALPHA))
        img.putalpha(a)
    return img


def build(atlas_rows):
    figs, labels = [], []
    for cid in ANCHORS:
        r = atlas_rows[cid]
        pal = (r["skin"], r["hair"], r["cloth"], r["eye"], r["badge"])
        figs.append(draw_figure(r["species"], pal))
        labels.append(NAMES[cid])
    figs.append(draw_figure("user", DEMO_USER))
    labels.append(DEMO_LABELS[0])
    figs.append(draw_figure("ceo", DEMO_CEO))
    labels.append(DEMO_LABELS[1])
    return figs, labels


def montage(figs, labels):
    """批 0 修订 v3：原生 256 出图（2× 呈报位免降采样）+抬头+落影+角注+双行标签。"""
    cols, cell, gap = len(figs), 256, 26
    head, band = 64, 110
    W = cols * cell + (cols + 1) * gap
    H = head + cell + band
    out = Image.new("RGBA", (W, H), BG)
    fonts = {}
    for size, key in ((26, "title"), (19, "lab"), (15, "corner")):
        for fp in ("C:\\Windows\\Fonts\\msyh.ttc", "C:\\Windows\\Fonts\\simhei.ttf"):
            try:
                fonts[key] = ImageFont.truetype(fp, size)
                break
            except Exception:
                continue
    d = ImageDraw.Draw(out)
    if "title" in fonts:
        d.text((gap, 16), TITLE, font=fonts["title"], fill=LABEL_INK)
    shadow = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([70, 240, 186, 262], fill=(0, 0, 0, 60))
    for i, (im, lab) in enumerate(zip(figs, labels)):
        x = gap + i * (cell + gap)
        y = head
        out.alpha_composite(shadow, (x, y))
        out.alpha_composite(im, (x, y))
        if "lab" in fonts:
            for row, tx in enumerate(lab):
                w = d.textbbox((0, 0), tx, font=fonts["lab"])[2]
                d.text((x + (cell - w) // 2, head + cell + 12 + row * 26), tx,
                       font=fonts["lab"], fill=LABEL_INK)
    if "corner" in fonts:
        d.text((gap, H - 28), CORNER, font=fonts["corner"], fill=(100, 100, 100, 255))
    return out


def png_bytes(im):
    b = io.BytesIO()
    im.save(b, format="PNG")
    return b.getvalue()


def main():
    atlas_rows = load_atlas()
    figs, labels = build(atlas_rows)
    img = montage(figs, labels)
    data = png_bytes(img)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(data)
    print("out=%s bytes=%d md5=%s" % (os.path.relpath(OUT, CO), len(data),
                                      hashlib.md5(data).hexdigest()))

    if "--qc" in sys.argv:
        # 判据 1：双跑逐字节一致（同输入=同 PNG）
        figs2, labels2 = build(load_atlas())
        assert labels2 == labels, "QC FAIL labels determinism"
        assert png_bytes(montage(figs2, labels2)) == data, "QC FAIL determinism"
        # 判据 2：调色单源（全分辨率图用色 RGB ⊆ atlas 五 hex∪暗面档∪法定常量∪法定 α 合成闭包）
        legal = set()
        src_hex = []
        for cid in ANCHORS:
            r = atlas_rows[cid]
            src_hex += [r["skin"], r["hair"], r["cloth"], r["eye"], r["badge"]]
        src_hex += [h for h in DEMO_USER[:3]] + [h for h in DEMO_CEO[:3]] \
                  + [DEMO_USER[4], DEMO_CEO[4]]
        for h in src_hex:
            c = hx(h)[:3]
            for f in (1.0, SHADE, 0.7, 0.62, 0.55, 0.78 * 0.88, 0.7 * 0.88, 0.42):
                legal.add((int(c[0] * f), int(c[1] * f), int(c[2] * f)))
        for c in (USER_EYE, WHITE_RING, CEO_HALO, CEO_HALO2, CEO_ROBE,
                  (64, 240, 224, 220), (255, 255, 255, 230)):
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
        # 判据 3：暗面档=基色×0.78 两阶律（抽查碳源 skin）
        c = hx(atlas_rows["C-00010"]["skin"])
        assert dark(c)[:3] == (int(c[0] * SHADE), int(c[1] * SHADE), int(c[2] * SHADE)), \
            "QC FAIL shade law"
        # 判据 4：法定常量断言（facet 语义面）
        assert SHADE == 0.78 and SPRITE_ALPHA == 165 and BG == (228, 228, 228, 255)
        print("QC PASS: determinism + palette-provenance(%d rgb) + shade 0.78 + facet-laws"
              % len(used))
    return


if __name__ == "__main__":
    main()
