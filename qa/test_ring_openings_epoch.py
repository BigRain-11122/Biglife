# -*- coding: utf-8 -*-
"""开口族仪表「口径纪元」常驻回归（零 LLM·不写仓·不改盘）。

判例=R2786：族表是代码常量，立一次族就把当日已在册的环追溯重判一遍，
11-13 的「HAND 40.0% 越线」用当日生效表回算是 25.0%。页面若照旧渲染
「越线」，等于把重分类读数误植成「闸被绕过」。本测锁定三件事：
  ① 跨口径日（none/multi/curr-missing）不给 OVER/PASS，一律 CROSS-EPOCH；
  ② 同口径日（single）仍按 25% 正常判 OVER；
  ③ 渲染面同时出现「单一口径」「跨口径」两态，且不再出现旧因果断言「新病症」。

用法: python -X utf8 qa/test_ring_openings_epoch.py   （判据=rc 0）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "Tools"))

import ring_open_family as rof          # noqa: E402
import build_ring_openings as B         # noqa: E402

FAILS = []


def check(name, got, want):
    if got != want:
        FAILS.append("%s: got %r want %r" % (name, got, want))


def _day_rows(day, hand=8, other=4):
    return [(day, "手里那截旧护缆缠了两圈，风从廊下过")] * hand + \
           [(day, "巷口的光一点点退到墙根，收摊的竹筐磕着石板")] * other


def main():
    # 四天各 12 环（≥min_denom=8），HAND 8/12=66.7% 现表必然越线
    rows = []
    for d in ("2026-11-10", "2026-11-11", "2026-11-12", "2026-11-13"):
        rows.extend(_day_rows(d))

    epochs = {
        "2026-11-13": [],                          # 无纪元登记 -> none
        "2026-11-12": [rof.TABLE_EPOCH],           # 正合现表 -> single
        "2026-11-11": ["2026-10-01T09:00", "2026-11-13T15:38"],  # -> multi
        "2026-11-10": ["2026-10-01T09:00"],        # 旧表出生 -> curr-missing
    }
    orig = rof.epochs_of
    rof.epochs_of = lambda day: epochs.get(day, [])
    try:
        model = B.build(rows, today="2026-11-13")
        got = {r["day"]: (r["mix"], r["verdict"]) for r in model["daily"]}
        check("11-13 none", got["2026-11-13"], ("none", "CROSS-EPOCH"))
        check("11-12 single", got["2026-11-12"], ("single", "OVER"))
        check("11-11 multi", got["2026-11-11"], ("multi", "CROSS-EPOCH"))
        check("11-10 curr-missing", got["2026-11-10"], ("curr-missing", "CROSS-EPOCH"))

        html = B.render(model)
        html2 = B.render(B.build(rows, today="2026-11-13"))
        check("render 幂等", html == html2, True)
        check("含单一口径", "单一口径" in html, True)
        check("含跨口径", "跨口径" in html, True)
        check("含口径列", ">口径<" in html, True)
        check("旧错误断言已除", "新病症" in html, False)
        check("越线仍在同口径日出现", "越线 HAND_DEICTIC" in html, True)
        check("KPI 当日判定存在", "当日判定" in html, True)
    finally:
        rof.epochs_of = orig

    if FAILS:
        print("FAIL %d/%d" % (len(FAILS), 7 + 4))
        for f in FAILS:
            print("  -", f)
        return 1
    print("PASS 11 probes (mix/verdict 四态 + render 八面)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
