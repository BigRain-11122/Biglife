# -*- coding: utf-8 -*-
"""self_dup_history 近重复面回归（R2611·T-20261112-08·零 LLM）

运行：python -X utf8 qa/test_self_dup_near.py
判据：4/4 PASS（rc 0）。正控=骨架同只换风句必须拦；负控=不同骨架构句必须放行；
窗口面=超出 SELF_DUP_WINDOW 的老圈不得否决新主题。
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import evolve_citizen as ec  # noqa: E402

SKEL_A = ("我把手边的琴谱往边儿上一搁，扫了扫弦，风不小，吹得那架子直晃，"
          "可这城里好玩的东西一天比一天多呢。")
SKEL_B = ("我把手边的琴谱往边儿上一搁，扫了扫弦，风声盖过了人声，"
          "这城里好玩的东西一天比一天多呢。")


def card(*rings):
    return "**年轮**\n" + "".join(f"- {d} 「{t}」\n" for d, t in rings)


class SelfDupNear(unittest.TestCase):
    def test_verbatim_still_caught(self):
        ct = card(("2026-11-11", "今天照常出摊，江上的光点还是那么多。"))
        self.assertTrue(ec.self_dup_history("今天照常出摊，江上的光点还是那么多。", ct))

    def test_skeleton_reuse_caught(self):
        ct = card(("2026-11-11", SKEL_A))
        self.assertTrue(ec.self_dup_history(SKEL_B, ct))

    def test_new_skeleton_passes(self):
        ct = card(("2026-11-11", SKEL_A))
        now = "巷口的灯又坏了一盏，我搬梯子去换，顺手把楼道的灰扫了。"
        self.assertFalse(ec.self_dup_history(now, ct))

    def test_window_excludes_old_rings(self):
        rings = [("2026-10-30", SKEL_A)]
        rings += [(f"2026-11-0{i}", "巷口灯坏了，我去换了一盏，顺手扫了楼道。")
                  for i in range(1, 6)]
        ct = card(*rings)
        self.assertFalse(ec.self_dup_history(SKEL_B, ct))


if __name__ == "__main__":
    unittest.main(verbosity=2)
