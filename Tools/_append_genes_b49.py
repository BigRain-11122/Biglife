#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b49 批（精灵习惯 sprite_habits + 精灵钩子 sprite_hook_actions）

来源：R2412 让路窗（bm-a 工作日 09:00-19:00 算力让 CEO·年轮/相遇线按
D-20261020-02 延后到 19:00）。b49 只补两个精灵桶——sprite_habits 12 条、
sprite_hook_actions 10 条，而精灵类居民实测约 500 席（census 卡首段含「灵」），
12/10 条摊 500 席=全库最薄、重复最重的两桶，补桶直接降精灵居民卡面重复。

gene_nearcheck 的 TYPE_POOLS 只注册 cp/ho/tp/ha/pr 五型（不含精灵两型），
故本批按同一法意自检：同池 rapidfuzz fuzz.ratio < 70（照 ha 阈值口径）+
全文本池任意池 4-gram Jaccard 报高值即换句。只原样追加，不做整档 dump。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

SPRITE_HABITS = [
    "早上第一班公交进站时，顺着车窗亮一段",
    "换季那天把自己停到老槐树最高的枝上，晒一整天的光",
    "听见谁家吵架就落在窗台外，等人声歇了才走",
    "收废品的三轮车过巷口，一定跟着推一段",
    "把旧年历纸上的红字都照一遍，说是替人记着",
    "半夜有孩子在阳台哭，就把自己调暗一点装成月亮",
    "遇着搬家的人家，先飞进去在空屋里转一圈",
    "下雪前贴着屋檐排成一溜，像挂了一串小灯",
    "常在桥上停一会儿，看船过去了才走",
    "春天给新冒的芽多照半个钟头",
    "见过谁哭，就把光调成暖的",
    "老街翻修那阵宁可绕远，也不从脚手架底下过",
]

SPRITE_HOOK_ACTIONS = [
    "记着 {obj} 那一天摆出来的样子",
    "每逢 {obj} 落灰最多的那天，会去吹一吹",
    "拿 {obj} 的影子量过整条巷子",
    "在 {obj} 上留过一小块暖",
    "见过 {obj} 换过三回主人",
    "把 {obj} 旁边掉的东西归过位",
    "逢年过节先去照 {obj} 一会儿",
    "听过 {obj} 响得最晚的那一次",
    "顺着 {obj} 的边角描过一遍轮廓",
    "借 {obj} 的光给迷路的飞虫指过路",
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append(path, key, rendered):
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2):]
    Path(path).write_text(t, encoding="utf-8", newline="\n")


def check(pool_name, existing, candidates):
    from rapidfuzz import fuzz
    flagged = []
    for c in candidates:
        for e in existing:
            r = fuzz.ratio(c, e)
            if r >= 70.0:
                flagged.append((pool_name, round(r, 1), c, e))
        for e in candidates:
            if e is not c and fuzz.ratio(c, e) >= 70.0:
                flagged.append((pool_name + "/new", round(fuzz.ratio(c, e), 1), c, e))
    return flagged


def main():
    before = load(LIVES)
    b_sh, b_sa = len(before["sprite_habits"]), len(before["sprite_hook_actions"])

    fresh_sh = [x for x in SPRITE_HABITS if x not in before["sprite_habits"]]
    fresh_sa = [x for x in SPRITE_HOOK_ACTIONS if x not in before["sprite_hook_actions"]]

    flagged = check("sprite_habits", before["sprite_habits"], fresh_sh)
    flagged += check("sprite_hook_actions", before["sprite_hook_actions"], fresh_sa)
    if flagged:
        for row in flagged:
            print("FLAG", row)
        raise SystemExit("near-dup gate failed: %d" % len(flagged))
    print("nearcheck CLEAN: %d + %d candidates" % (len(fresh_sh), len(fresh_sa)))

    append(LIVES, "sprite_habits", [json.dumps(x, ensure_ascii=False) for x in fresh_sh])
    append(LIVES, "sprite_hook_actions", [json.dumps(x, ensure_ascii=False) for x in fresh_sa])

    lives = load(LIVES)
    after = (len(lives["sprite_habits"]), len(lives["sprite_hook_actions"]))
    print("sprite_habits %d -> %d (+%d)" % (b_sh, after[0], after[0] - b_sh))
    print("sprite_hook_actions %d -> %d (+%d)" % (b_sa, after[1], after[1] - b_sa))
    assert after == (b_sh + len(fresh_sh), b_sa + len(fresh_sa)), after
    for x in fresh_sh:
        assert x in lives["sprite_habits"], x
    for x in fresh_sa:
        assert x in lives["sprite_hook_actions"], x
    assert len(lives["hook_objects"]) == 839, len(lives["hook_objects"])
    print("OK b49")


if __name__ == "__main__":
    main()