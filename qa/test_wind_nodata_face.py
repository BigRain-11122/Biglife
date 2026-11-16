#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3229 (2026-11-16): 无风力读数时的「风断言」闸面契约（提示词 ↔ 闸同口径）。

病根（gap #68 同型，方向相反）：``weather_recap`` 在无风速数据时早已写死
「实况无风速数据：完全不提风。」，而 ``ring_violations`` 的 ``wind-nodata``
只认量级词（风大不大／微风／风轻），于是施事/布景形状
（「风把塑料布吹得啪啦响」「风撞在窗玻璃上闷响」）一路放行。
2026-11-16 实测：当日 25 条拒稿里 ``WIND_AGENT_OPEN`` 11 条（44%）为最大单一族，
``opening_capacity --window 12`` 的重复开口 9 条全是风形，浪费 35%。

修法边界（宁漏不误伤）：
  · 认风作主语的施事/受力形状（风把/掀/撞/扯/刮/灌/扑/卷/钻/顶/推/扫/裹/吹）
    与「风从窗/门/巷/缝…」布景形状；
  · 先掩掉器物名与专名（风控=街区词、台风=人设史、风扇/风筝/风铃/风衣/风箱/
    风车/风镜/风油精/风机/风湿/风干/风门）；
  · 风声/风里/风凉 放行（风声=消息、风里=旧年轮习惯语、风凉=风凉话）；
  · 有风力读数时本闸不介入（量级闸 wind-under/wind-over 照旧）。

零 LLM / 零 GPU / 确定性。运行：python -X utf8 qa/test_wind_nodata_face.py
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "Tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import evolve_citizen as ec  # noqa: E402

# 今日真实喂入形态：无风速读数（FluxVerse world-state: kind=cloud, temp_c=18.3）
NODATA = {"weather": "cloud 18.3°C", "now": "2026-11-16 14:50 周一",
          "weekday": "周一", "weekend": False, "events": [], "event_zones": [],
          "today_ban_families": set()}
MEASURED = dict(NODATA, weather="cloud 18.3°C wind 6.4m/s")


def gates(line, sig):
    return ec.ring_violations(line, dict(sig))


class WindNodataGate(unittest.TestCase):
    # ---- 正控：无读数时的风断言必须被拒 ----
    def test_positive_agent_shapes(self):
        for line in (
            "风把塑料布吹得啪啦响，我正把边角压实。",
            "风撞在窗玻璃上闷响，我正把灯芯拨亮。",
            "风把雨棚掀得直响，我把货往里挪了挪。",
            "风刮得紧，我又把绳子绕了一圈。",
            "风从窗缝里挤进来，我抹了把窗台的水汽。",
            "风卷着落叶打在门板上，我把门缝塞紧。",
        ):
            self.assertIn("wind-nodata", gates(line, NODATA), line)

    def test_positive_quantity_stays(self):
        # 旧面不得回归：量级词仍判（wc 变体）
        self.assertIn("wind-nodata", gates("风好大，我把帽子按住了。", NODATA))
        self.assertIn("wind-nodata", gates("微风，我慢慢往前挪。", NODATA))

    # ---- 负控：器物名/专名/歧义词不得误伤 ----
    def test_negative_objects_and_names(self):
        for line in (
            "今天风控高地那台机柜又报了警，我去看了一眼。",
            "我把电风扇拆开，给轴承上了点油",
            "台风夜守摊那回，街坊都来搭手",
            "去年台风把摊子掀了，是街坊凑料帮着重搭的",
            "风筝线缠在杆子上，我解了半天",
            "桥上的风里全是消息，我听了半宿",
            "风声传来时我正在理账",
            "风干了两天的腊味，我翻了翻",
        ):
            self.assertNotIn("wind-nodata", gates(line, NODATA), line)

    # ---- 有读数时本闸不介入（量级闸照旧）----
    def test_measured_feed_not_refused_by_nodata(self):
        self.assertNotIn("wind-nodata", gates("风把塑料布吹得啪啦响，我正把边角压实。", MEASURED))
        # 量级闸仍在岗
        self.assertIn("wind-under", gates("风轻轻的，我把货码好。", MEASURED))


class WindPromptPlacement(unittest.TestCase):
    """提示词侧：风句限位（R3229 主修法·大风天风句不得作开头）。"""

    def test_windy_feed_gets_placement_rule(self):
        recap = ec.weather_recap("cloud 18.1°C wind 9.8m/s", seed="C-03117")
        self.assertIn("严禁用风句开头", recap)
        # 量级口径不得因限位而丢失（9.8>3 → 风大面）
        self.assertIn("风不小", recap)

    def test_light_wind_feed_keeps_level_rule(self):
        recap = ec.weather_recap("clear 20.0°C wind 1.8m/s", seed="C-03228")
        self.assertIn("严禁用风句开头", recap)
        self.assertIn("风不大", recap)

    def test_nodata_feed_says_no_wind(self):
        recap = ec.weather_recap("cloud 18.1°C", seed="C-03303")
        self.assertIn("完全不提风", recap)

    def test_empty_feed_returns_empty(self):
        self.assertEqual(ec.weather_recap("", seed="C-03117"), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
