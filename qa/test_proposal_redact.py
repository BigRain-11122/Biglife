# -*- coding: utf-8 -*-
"""qa/test_proposal_redact.py — 提案面片段级脱敏回归（零 LLM·只读仓·不写盘）

判据（rc=0 为 PASS）：
  1 正控：含机读串的提案句，脱敏后 machine_hits()==0，且建议正文汉字保留；
  2 压缩：连续占位符串压成一个，不出现「〔专名〕_〔专名〕」式噪声；
  3 负控：不含机读串的干净句零改动原样返回；
  4 产物：census/export/city-proposals.html 零机读串泄漏，且 9 条提案全部可读。

背景：2026-11-13 R2794，提案面此前 9/9 整条遮蔽，CEO 打开看到零条实意。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))

import build_city_proposals as b  # noqa: E402

PAGE = os.path.join(ROOT, "census", "export", "city-proposals.html")
LEAK_WORDS = ["BigMoney", "CODELY", "CrazyCampus", "Token", "B2396", "G08",
              "GAME", "STAGE", "S2.5", "决策委员会", "集团", "任务单", "机队"]

fails = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (("  " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


# 1 正控：专名 + 事件码 + 中文术语混排
cases = [
    ("建议在CrazyCampus_G08 / B2396 / S2.5 -> G12的转变节点，先复核一遍流程。", "复核一遍流程"),
    ("建议把「GAME STAGE: B2396 -> G12」这段光路，连成同桌间的每日通路。", "每日通路"),
    ("建议决策委员会统计时也听听雨声蛙的合唱。", "雨声蛙"),
    ("建议使用「BigMoney CODELY反弹」的契机，开展社区经济教育。", "社区经济教育"),
]
for src, keep in cases:
    red, n = b.redact_machine(src)
    check("正控 残留=0  " + keep, b.machine_hits(red) == 0, red)
    check("正控 正文保留  " + keep, keep in red and n > 0, red)

# 2 压缩：连续占位符不得堆叠
red, _ = b.redact_machine("建议在CrazyCampus_G08 / B2396 / S2.5 -> G12的转变节点。")
check("压缩 无占位符串联", not re.search(r"〔[^〕]+〕[\s_\-/、·:：]*(?:->|→)*[\s]*〔", red), red)

# 3 负控：干净句零改动
clean = "建议在广场办一场读书会。"
red, n = b.redact_machine(clean)
check("负控 干净句原样", red == clean and n == 0, red)

# 4 产物页
if not os.path.isfile(PAGE):
    check("产物页存在", False, PAGE)
else:
    s = io.open(PAGE, encoding="utf-8").read()
    leaks = [w for w in LEAK_WORDS if w in s]
    check("产物页 零机读串泄漏", not leaks, ",".join(leaks))
    check("产物页 9 条全可读", s.count("建议") >= 9, "count=%d" % s.count("建议"))
    check("产物页 无整条遮蔽文案", "不展示原文" not in s)

print()
if fails:
    print("RESULT FAIL (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("RESULT PASS (all checks)")
