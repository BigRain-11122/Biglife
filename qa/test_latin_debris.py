# -*- coding: utf-8 -*-
"""v0.69 回归：洗码残渣闸（latin-debris）。

证两件事：
  1. `ring_violations()` 对「字母残渣+句点+紧跟汉字」「文件名扩展名」判违例；
     对合法面名（P楼/G区/Q区/G系）与居民 ID（C-07743 / H-QT2232）零误伤。
  2. 喂入面 `scrub_machine_words()` 清码后不再留 "c." 这类半个拉丁词。

判据面实证：全库 17063 圈扫描命中 2 例真缺陷（10-24 / 11-12，同一张 C-00110
的两代残句），合法面名样本 0 命中。

Run: python -X utf8 qa/test_latin_debris.py
Exit 0 = 全部用例 PASS。零 LLM、零仓内写入。
"""
import os
import sys

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Tools")
sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True

import evolve_citizen as ec  # noqa: E402

SIG = {}


def has(line, tag):
    try:
        return tag in ec.ring_violations(line, SIG)
    except Exception:
        return tag in ec.ring_violations(line, dict(SIG))


CASES = [
    # (label, line, expect_latin_debris)
    ("残句-单字母+句点（11-12 实弹）",
     "我正盯着那行c.的根，补丁没补完，就先搁着。", True),
    ("残句-文件名（10-24 实弹）",
     "我正盯着那行c.json的flag根，补丁没补完。", True),
    ("残句-大写扩展名",
     "那本README.md还摊在桌上。", True),
    ("合法-面名 P楼",
     "风挺大，吹得P楼大堂的铜铃直响，我照例给老主顾捎了信。", False),
    ("合法-面名 G区",
     "风不小，吹得G区脚手架嘎吱响，正好把今天搭的景拆了迭代。", False),
    ("合法-面名 G系灯塔",
     "雨点子砸在塔檐上噼啪响，我顺手把G系灯塔的旧工具又擦了一遍。", False),
    ("合法-居民ID",
     "与 C-00193 相遇：他是修表的，手稳。", False),
    ("合法-家户ID",
     "家户 H-GM1137 就我一个人住，灯留着。", False),
    ("合法-日常句",
     "夜里冷，喝口热的再走，老藤椅还在等我说话呢。", False),
]

SCRUB_CASES = [
    ("喂入洗码-文件名+代码词", "我正盯着那行c.json的flag根", "c."),
    ("喂入洗码-单字母残渣", "那行c.的根还没补", "c."),
]


def main():
    fails = 0
    for label, line, expect in CASES:
        got = has(line, "latin-debris")
        ok = got == expect
        fails += 0 if ok else 1
        print("%s %-26s expect=%s got=%s" % ("PASS" if ok else "FAIL", label, expect, got))

    for label, text, banned in SCRUB_CASES:
        out = ec.scrub_machine_words(text)
        ok = banned not in out
        fails += 0 if ok else 1
        print("%s %-26s scrub=%r" % ("PASS" if ok else "FAIL", label, out))

    print("RESULT %d/%d PASS" % (len(CASES) + len(SCRUB_CASES) - fails,
                                 len(CASES) + len(SCRUB_CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
