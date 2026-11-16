"""R3212 回归：渲染量随日期滚动的面必须绕过 dep 指纹压制。

病根（实锚）：city-ring-recency.html 07:56 构建（今日 273），源
census/export/citizens-light.jsonl 08:55 被行为线同内容重写（字节不变→指纹一致），
round_daily --run 判 fresh；到 12:48 面仍停在 273，重建后为 330（+21%）。
该页「今日 N 环 / 叙龄分档」由构建时刻的日期算出，源内容不变时跨日/跨小时也会变，
指纹（内容哈希）永远看不见这类漂移，故这类面必须跳过指纹压制。

本测试直接验判定函数，不碰真盘：正控=普通面在指纹一致时仍判 fresh；
负控=FP_SKIP 面在指纹一致时仍判 stale。
"""
import os
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))

import round_daily as rd  # noqa: E402


class DepFingerprintSkipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = self.tmp.name
        self._old_root = rd.ROOT
        rd.ROOT = base
        self._old_depends = dict(rd.DEPENDS)
        self._old_snapshot = rd._load_dep_snapshot
        self._old_fp = rd._dep_fingerprint

        dep = os.path.join(base, "src.jsonl")
        with open(dep, "w", encoding="utf-8") as f:
            f.write('{"a":1}\n')
        self.dep_rel = "src.jsonl"

        # 产物比源旧 2 小时（越过 60 分钟冷却下限）
        self.out = os.path.join(base, "out.html")
        with open(self.out, "w", encoding="utf-8") as f:
            f.write("<html></html>")
        old = time.time() - 7200
        os.utime(self.out, (old, old))

        rd.DEPENDS["_t_plain"] = [self.dep_rel]
        rd.DEPENDS["_t_skip"] = [self.dep_rel]
        rd._load_dep_snapshot = lambda: {"_t_plain": "SAME", "_t_skip": "SAME"}
        rd._dep_fingerprint = lambda key: "SAME"
        rd._DEP_FP_CACHE.clear()
        if "_t_skip" not in rd.DEPENDS_FP_SKIP:
            rd.DEPENDS_FP_SKIP.add("_t_skip")

    def tearDown(self):
        rd.ROOT = self._old_root
        rd.DEPENDS.clear()
        rd.DEPENDS.update(self._old_depends)
        rd._load_dep_snapshot = self._old_snapshot
        rd._dep_fingerprint = self._old_fp
        rd._DEP_FP_CACHE.clear()
        rd.DEPENDS_FP_SKIP.discard("_t_skip")
        self.tmp.cleanup()

    def test_plain_face_suppressed_by_matching_fingerprint(self):
        self.assertIsNone(rd._dep_mtime_stale("_t_plain", [self.out]))

    def test_rolling_face_not_suppressed_by_matching_fingerprint(self):
        self.assertIsNotNone(rd._dep_mtime_stale("_t_skip", [self.out]))

    def test_ring_recency_is_registered_in_skip_set(self):
        self.assertIn("ring_recency", rd.DEPENDS_FP_SKIP)
        self.assertEqual(rd.DEPENDS_FLOOR_OVERRIDE.get("ring_recency"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
