#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b48 批（心愿 presents + 钩子动作 hook_actions）

来源：R2408 让路窗（bm-a 工作日 09:00-19:00 算力让 CEO·年轮/相遇线按
D-20261020-02 延后到 19:00）。b48 只补两个最薄的桶——presents 55 条、
hook_actions 43 条，两桶都由 generate_census 逐居民取样（卡面心愿行 +
钩子动作行），桶浅=全库重复率高，补桶直接降重复。

候选全部过 gene_nearcheck 双层判据（ha 阈 70 / pr 阈 37·R417+T-20261027-01
定谳值），两轮共 31 条候选收 14 条 CLEAN（b48 首轮 20 投 9 CLEAN，b48b 换句
11 投 5 CLEAN·首轮 11 条 FLAG 已按判据换句互验）。只原样追加，不做整档 dump。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

PRS = [
    "正给隔壁两家为一道墙的事说和，一碗茶工夫就说开了",
    "在给自家阳台搭个小棚，想冬天也能吃到自己种的葱",
    "刚开始记家里的进出账，说这把年纪该把日子算明白了",
    "正打算把厨房那口老盐罐腾出来，换一套新的腌菜方子",
    "每周三去社区夜校代课，白天没人得闲，来的都是夜里才腾出手的街坊",
    "想着给巷口老石凳加个木靠背，坐久了腰实在吃不消",
]

HAS = [
    "每逢节气在 {obj} 旁边换一束当季的野花",
    "每天夜里给 {obj} 留一盏小灯",
    "每逢集市就把 {obj} 摆出来当招牌",
    "喜欢拿 {obj} 引出一段跟它毫不相干的旧事",
    "换季时把 {obj} 逐个翻面晾一天",
    "给 {obj} 一年拍一张照，按节气贴满一整面墙",
    "给每件 {obj} 都挂个小牌，牌上是它进门的年月",
    "常拿 {obj} 给街坊指路，指错了自罚请茶",
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


def main():
    before = load(LIVES)
    b_pr, b_ha = len(before["presents"]), len(before["hook_actions"])

    fresh_pr = [x for x in PRS if x not in before["presents"]]
    fresh_ha = [x for x in HAS if x not in before["hook_actions"]]

    append(LIVES, "presents", [json.dumps(x, ensure_ascii=False) for x in fresh_pr])
    append(LIVES, "hook_actions", [json.dumps(x, ensure_ascii=False) for x in fresh_ha])

    lives = load(LIVES)
    after = (len(lives["presents"]), len(lives["hook_actions"]))
    print("presents %d -> %d (+%d)" % (b_pr, after[0], after[0] - b_pr))
    print("hook_actions %d -> %d (+%d)" % (b_ha, after[1], after[1] - b_ha))
    assert after == (b_pr + len(fresh_pr), b_ha + len(fresh_ha)), after
    for x in fresh_pr:
        assert x in lives["presents"], x
    for x in fresh_ha:
        assert x in lives["hook_actions"], x
    assert len(lives["hook_objects"]) == 839, len(lives["hook_objects"])
    print("OK b48")


if __name__ == "__main__":
    main()