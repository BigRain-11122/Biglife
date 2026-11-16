#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3220 自测：拒稿回灌闸（opening_seed_block / retry_skeleton）三向验证。

正控 1：今日有拒稿行 -> 该骨架不再发给任何居民（今天的核心修复）
正控 2：retry_skeleton 给出一条可用的替用骨架（不是被拒那条、不在排除集）
负控 1：拒稿行是昨天的 -> 骨架选择与改动前逐字相同（不跨日误伤）
负控 2：无拒稿文件 -> 选择与旧算法逐字相同（零漂移律）
负控 3：8 字前缀容忍只命中同前缀骨架，不误删无关骨架

跑法：python -X utf8 qa/test_opening_refusal_memo.py   （零网络/零 LLM/零产物写入）
"""

import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))

import evolve_citizen as ec  # noqa: E402  (需先插 Tools 进 sys.path)

HOT = "这会儿手边最碍事的就是这些，"      # 11-15/11-16 实测热骨架（24 条拒稿/9 人）
CID_HOT = None                            # 旧算法拿 HOT 的那个 cid，运行期反查
CIDS = ["C-%05d" % (i * 37 % 10120) for i in range(60)]


def _legacy_pick(cid, pool=None):
    pool = pool or ec.OPENING_SKELETONS
    n = sum((i + 1) * ord(ch) for i, ch in enumerate(cid or ""))
    return pool[n % len(pool)]


def _seed_of(block):
    m = re.search(r"「(.+?)」", block or "")
    return m.group(1) if m else ""


class _MemoCase(unittest.TestCase):
    """把 STATE_DIR 指到临时目录后跑三向判据。"""

    def setUp(self):
        global CID_HOT
        self._tmp = tempfile.TemporaryDirectory()
        self._old = ec.STATE_DIR
        ec.STATE_DIR = self._tmp.name
        self.path = os.path.join(self._tmp.name, "ring-refusals.jsonl")
        if CID_HOT is None:
            for cid in CIDS:
                if _legacy_pick(cid) == HOT:
                    CID_HOT = cid
                    break

    def tearDown(self):
        ec.STATE_DIR = self._old
        self._tmp.cleanup()

    def _write(self, rows):
        with open(self.path, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    def _row(self, cid, ts, opening12):
        return {"ts": ts, "cid": cid, "gate": ["recent-family-opening"],
                "family": "TIME_OPEN", "opening12": opening12}

    def _sig(self, cid):
        return {
            "cid": cid,
            "today_open_ids": {},
            "today_refused_openings": ec.today_refused_openings(),
            "recent_banned_openings": [],
        }

    # ---- 正控 1：今日拒稿 -> 该骨架当天不再发放（含抓 HOT 的那个 cid）----
    def test_today_refusal_removes_skeleton(self):
        key = re.sub(r"\s+", "", HOT)[:12]
        self._write([self._row("C-03117", ec.today() + " 17:04:33", key)])
        got = ec.today_refused_openings()
        self.assertIn(key, got, "今日拒稿行未被读回（回灌闸未接线）")
        self.assertIsNotNone(CID_HOT, "测试样本里没有拿 HOT 的 cid（样本失效需换）")
        for cid in CIDS:
            self.assertNotEqual(_seed_of(ec.opening_seed_block(cid, self._sig(cid))),
                                HOT, "%s 仍被发放今日已拒骨架" % cid)

    # ---- 正控 2：retry_skeleton 给可用替用骨架 ----
    def test_retry_skeleton_usable(self):
        key = re.sub(r"\s+", "", HOT)[:12]
        self._write([self._row("C-03117", ec.today() + " 17:04:33", key)])
        sig = self._sig(CID_HOT)
        alt = ec.retry_skeleton(sig, 0, banned=key)
        self.assertTrue(alt, "替用骨架为空（池被排空或接线断了）")
        self.assertNotEqual(re.sub(r"\s+", "", alt)[:12], key, "替用骨架等于被拒骨架")
        self.assertFalse(ec._opening_is_dead(alt, ec.today_refused_openings()),
                         "替用骨架落在排除集里")
        # 不同 attempt 给不同骨架（同一 cid 连续重试不该反复同一条）
        alts = {ec.retry_skeleton(sig, a, banned=key) for a in range(4)}
        self.assertGreater(len(alts), 1, "同一 cid 四次重试拿到同一条替用骨架")

    # ---- 负控 1：昨日拒稿不跨日误伤 ----
    def test_yesterday_refusal_no_effect(self):
        key = re.sub(r"\s+", "", HOT)[:12]
        self._write([self._row("C-03117", "1999-01-01 17:04:33", key)])
        self.assertEqual(ec.today_refused_openings(), set(),
                         "昨日拒稿被当成今日拒稿（跨日误伤）")
        hit = 0
        for cid in CIDS:
            if _seed_of(ec.opening_seed_block(cid, self._sig(cid))) == HOT:
                hit += 1
        self.assertGreater(hit, 0, "无今日拒稿时 HOT 仍应可被正常发放（过度过滤）")

    # ---- 负控 2：无拒稿文件 -> 与旧算法逐字相同 ----
    def test_no_file_zero_drift(self):
        self.assertEqual(ec.today_refused_openings(), set())
        for cid in CIDS:
            self.assertEqual(_seed_of(ec.opening_seed_block(cid, self._sig(cid))),
                             _legacy_pick(cid), "%s 提示词骨架发生漂移" % cid)

    # ---- 负控 3：8 字前缀容忍只命中同前缀，不误删无关骨架 ----
    def test_prefix_tolerance_scoped(self):
        hot_key = re.sub(r"\s+", "", HOT)[:8] + "xx"
        self.assertTrue(ec._opening_is_dead(HOT, {hot_key}), "同 8 字前缀未命中")
        others = [s for s in ec.OPENING_SKELETONS if s != HOT]
        self.assertFalse(any(ec._opening_is_dead(s, {hot_key}) for s in others),
                         "前缀容忍误伤其他骨架")


if __name__ == "__main__":
    unittest.main(verbosity=2)
