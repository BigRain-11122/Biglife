# -*- coding: utf-8 -*-
"""R2593 常驻回归件：due_citizens 选区跨城区分散（T-2593 出生站闸）。

背景：人口 ~95% 聚一城，纯 ID 序选人让每批 3 席同城区 → 消费同一组母题
（R2590 实读留档）。修法只在**选人**层做分散，不动母题库、不动闸、不动年轮文本面。

判据：
  T1 混合城区 -> 批内城区尽量互异，且首座保持优先级（质量返修配额头位不被挤掉）
  T2 单城区城市 -> 回落到原序，绝不少给座位（防饿死）
  T3 batch=1 -> 与旧行为逐字一致（只取头位）
  T4 城区解析为空（卡无 **城区** 行）-> 不参与去重，仍按原序补座
  T5 窗口足够长 -> 第二席取「首个不同城区」，不是原序第二席
  T6 真盘集成 -> due_citizens(cursor,3) 返回 <=3 且可被 find_card 解析（不崩、不超扫）

跑法：python -X utf8 qa/test_due_district_spread.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "Tools"))

import evolve_citizen as E  # noqa: E402

fails = []


def check(name, cond, detail=""):
    if cond:
        print("PASS %s %s" % (name, detail))
    else:
        fails.append(name)
        print("FAIL %s %s" % (name, detail))


# ---- T1 混合城区：头位保全 + 席位互异 --------------------------------
c = ["C-1", "C-2", "C-3", "C-4"]
z = {"C-1": "GAME", "C-2": "GAME", "C-3": "LIFE", "C-4": "QUANT"}
got = E._pick_spread(c, z, 3)
check("T1-head", got[0] == "C-1", "head=%s" % got[0])
check("T1-spread", len({z[g] for g in got}) == 3, "zones=%s" % [z[g] for g in got])
check("T1-size", len(got) == 3, "n=%d" % len(got))

# ---- T2 单城区：原序回落，不少给座位 --------------------------------
c2 = ["C-1", "C-2", "C-3", "C-4"]
z2 = {k: "GAME" for k in c2}
got2 = E._pick_spread(c2, z2, 3)
check("T2-fallback-order", got2 == ["C-1", "C-2", "C-3"], "got=%s" % got2)

# ---- T3 batch=1：与旧行为一致 --------------------------------------
check("T3-single", E._pick_spread(c, z, 1) == ["C-1"], "")
check("T3-zero", E._pick_spread(c, z, 0) == [], "")

# ---- T4 城区解析为空：去重不生效但不丢座 ----------------------------
c4 = ["C-1", "C-2", "C-3"]
z4 = {"C-1": "", "C-2": "", "C-3": ""}
check("T4-empty-zone", E._pick_spread(c4, z4, 3) == c4, "got=%s" % E._pick_spread(c4, z4, 3))

# ---- T5 第二席取首个异城区 ------------------------------------------
c5 = ["C-1", "C-2", "C-3", "C-4", "C-5"]
z5 = {"C-1": "GAME", "C-2": "GAME", "C-3": "GAME", "C-4": "LIFE", "C-5": "GAME"}
got5 = E._pick_spread(c5, z5, 2)
check("T5-skip-same-zone", got5 == ["C-1", "C-4"], "got=%s" % got5)

# ---- T6 真盘集成（只读） -------------------------------------------
try:
    cur = E.load_cursor()
    picked = E.due_citizens(cur, 3)
    zones = {}
    ok = True
    for cid in picked:
        p = E.find_card(cid)
        if not p:
            ok = False
            continue
        with open(p, encoding="utf-8") as f:
            zones[cid] = E.citizen_zone(f.read())
    check("T6-real-pick", 1 <= len(picked) <= 3 and ok,
          "picked=%s zones=%s" % (picked, list(zones.values())))
    check("T6-scan-cap", E.SCAN_CAP == 48, "cap=%d" % E.SCAN_CAP)
except Exception as exc:  # 盘面不可用时不得假绿
    check("T6-real-pick", False, "exception=%r" % (exc,))

print("---")
print("RESULT: %d/%d PASS" % (6 - 0, 6) if not fails else "RESULT: FAIL %s" % fails)
sys.exit(0 if not fails else 1)
