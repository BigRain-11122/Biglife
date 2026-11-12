# -*- coding: utf-8 -*-
"""T-20261112-04 副作用回归：开头族硬闸 ↔ 提示词/骨架一致性（零 LLM·确定性）。

病根（R2588）：v0.65 把「开头骨架族 >25% 即拒稿」做成硬闸，但提示词五处仍在
把模型往 HAND_DEICTIC 推（city_phr/today/second 三块 + 两条 regen 尾注），且
today_ban_families 只喂闸与控制台，从没告诉模型禁哪一族；24 条开场骨架里另有
2 条本身落在被禁族。结果＝3 次重写同提示词必重入同一吸引子（gap #68），
19:00 首批会把应产席位全留 due。

判据（8 探针，全 PASS 即 rc=0）：
  T1 禁 HAND_DEICTIC 时不得再发该族骨架　T2 禁 TIME_OPEN 同理
  T3 无禁时提示词骨架逐字零漂移　　　　　T4 _hand_word 按禁令切换「手上/身上」
  T5 硬闸仍按族拒稿（未被削弱）　　　　　T6 句中/第二句身体描写不被误拦
  T7 FAMILY_OPEN_HINTS 覆盖族定义全部族　T8 双跑逐字一致

用法：python -X utf8 qa/test_family_prompt_consistency.py  （rc=0 即通过）
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import evolve_citizen as E          # noqa: E402
import ring_open_family as F        # noqa: E402

IDS = ["C-%05d" % i for i in range(1, 400, 3)]
fails = []


def _check(tag, ok, detail=""):
    print("%s %s" % (tag, "PASS" if ok else "FAIL " + str(detail)))
    if not ok:
        fails.append(tag)


def _skel_family(block):
    return F.family_of(block.split("「")[1].split("」")[0])


_check("T1 skeleton hand-filter", not [
    s for s in IDS
    if _skel_family(E.opening_seed_block(
        s, {"today_ban_families": {"HAND_DEICTIC"}})) == "HAND_DEICTIC"])

_check("T2 skeleton time-filter", not [
    s for s in IDS
    if _skel_family(E.opening_seed_block(
        s, {"today_ban_families": {"TIME_OPEN"}})) == "TIME_OPEN"])

_check("T3 zero-drift no-ban", not [
    s for s in IDS
    if not (E.opening_seed_block(s) == E.opening_seed_block(s, {}) ==
            E.opening_seed_block(s, {"today_ban_families": set()}))])

_check("T4 hand_word switch",
       E._hand_word({"today_ban_families": {"HAND_DEICTIC"}}) == "身上"
       and E._hand_word({}) == "手上" and E._hand_word(None) == "手上")

SIG = {"today_ban_families": {"HAND_DEICTIC"}, "card_text": "",
       "batch_openings": set(), "batch_phrases": {}, "batch_used": [],
       "now": "12:00", "weather": "clear", "recent_grams": {},
       "recent_open_ids": {}}

_check("T5 gate still hard",
       "opening-family-quota" in E.ring_violations(
           "手上的活儿刚收尾，账本翻到第三页。", SIG),
       E.ring_violations("手上的活儿刚收尾，账本翻到第三页。", SIG))

_check("T6 body detail legal",
       "opening-family-quota" not in E.ring_violations(
           "账本翻到第三页，手上的墨还没干。", SIG))

_check("T7 hint coverage", not [k for k in F.FAMILIES if k not in E.FAMILY_OPEN_HINTS],
       [k for k in F.FAMILIES if k not in E.FAMILY_OPEN_HINTS])

_check("T8 determinism",
       [E.opening_seed_block(s, {"today_ban_families": {"HAND_DEICTIC"}})
        for s in IDS[:50]] ==
       [E.opening_seed_block(s, {"today_ban_families": {"HAND_DEICTIC"}})
        for s in IDS[:50]])

print("RESULT:", "ALL PASS" if not fails else "FAIL " + ",".join(fails))
sys.exit(0 if not fails else 1)
