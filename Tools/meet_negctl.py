#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""相遇写盘出生地拦截 · 负控夹具（T-20261116-16 验收项）.

背景：T-20261116-16 要求在相遇写入路径加自校验（单向不得留存 / 同日同对象
不得重复）。实读 Tools/evolve_citizen.py meet 分支后确认拦截**已在树内**：

  1) 写前查重 `_meet_ring_today(card)` —— 同卡当日已有相遇即 return，
     连 LLM 都不烧（T-20261027-01 candidate filter）；
  2) 写后双向断言 `_meet_pair_check(ids)` —— 任一侧未指名对手即按写前
     快照 `originals` 回滚并 `sys.exit(1)`，不产生半对 commit。

因此本单剩余缺口只是**缺负控证据**（验收要求「构造第二卡写失败场景下单向
不得留存」）。本夹具补上这块：用临时目录造卡 + 替换 find_card，逐条证明
拦截会响，并静态断言回滚分支不许被后续重构静默删除。

零 LLM、零仓内卡片改动、零网络。
用法：python -X utf8 Tools/meet_negctl.py [--json] [--selftest]
rc=0 全过 / rc=1 有检项失败。
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "evolve_citizen.py")


def load_module():
    spec = importlib.util.spec_from_file_location("evolve_citizen", SRC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_card(path, body):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)


def card_with_meet(day, other, line="桥上风大，谁也没多说什么。"):
    return ("# 测试居民 C-00001\n\n## 年轮\n"
            "- %s 与 %s 相遇：%s\n" % (day, other, line))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true",
                    help="同义开关（与其它 negctl 工装口径一致）")
    args = ap.parse_args()

    m = load_module()
    today = m.today()
    checks = []

    def add(name, ok, detail):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    src_text = open(SRC, encoding="utf-8").read()

    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "C-00001.md")
        b = os.path.join(td, "C-00002.md")

        # C1 写前查重：同卡当日已有相遇 -> 必须报出对手 id
        write_card(a, card_with_meet(today, "C-00002"))
        got = m._meet_ring_today(a)
        add("C1-dup-detected", got == "C-00002",
            "_meet_ring_today(今日已有相遇)=%r 期望 C-00002" % (got,))

        # C2 昨日相遇不算重复（避免把长期关系误判成当日 dup）
        write_card(a, card_with_meet("2000-01-01", "C-00002"))
        got = m._meet_ring_today(a)
        add("C2-stale-not-dup", got is None,
            "_meet_ring_today(旧日相遇)=%r 期望 None" % (got,))

        # C3 单向（第二卡未写成功）必须被判不对称 -> 正是回滚触发条件
        write_card(a, card_with_meet(today, "C-00002"))
        write_card(b, "# 测试居民 C-00002\n\n## 年轮\n- %s 独自在家。\n" % today)
        orig = m.find_card
        try:
            m.find_card = lambda cid: {  # 只认本夹具两张卡
                "C-00001": a, "C-00002": b}.get(cid)
            bad = m._meet_pair_check(["C-00001", "C-00002"])
        finally:
            m.find_card = orig
        add("C3-one-sided-flagged", len(bad) == 1 and "C-00002" in bad[0],
            "_meet_pair_check(单向)=%r 期望 1 条且指向 C-00002" % (bad,))

        # C4 双向齐全不得误报（防闸变成常红）
        write_card(b, card_with_meet(today, "C-00001", "我记着那句。"))
        try:
            m.find_card = lambda cid: {
                "C-00001": a, "C-00002": b}.get(cid)
            bad = m._meet_pair_check(["C-00001", "C-00002"])
        finally:
            m.find_card = orig
        add("C4-symmetric-clean", bad == [],
            "_meet_pair_check(双向)=%r 期望 []" % (bad,))

        # C5 写前快照确实存在（回滚的原料），且回滚按快照整文件回写
        add("C5-originals-snapshot",
            "originals[p] = f.read()" in src_text,
            "写侧须在首次落环前缓存 originals（回滚原料）")
        add("C6-rollback-branch-present",
            "meet-asymmetry" in src_text and "sys.exit(1)" in src_text,
            "写侧须保留 meet-asymmetry 回滚分支与 rc=1 退出")

        # C7 查重必须发生在 LLM 调用之前（否则重复对烧一次本地 LLM）
        i_dup = src_text.find("meet-dup:")
        i_llm = src_text.find("resp = gated_llm(", src_text.find("meet-dup:"))
        i_gate = src_text.find('f"你是叙事编剧')
        add("C7-dup-before-llm",
            0 <= i_dup < i_llm and 0 <= i_dup < i_gate,
            "meet-dup@%d < gated_llm@%d < prompt@%d" % (i_dup, i_llm, i_gate))

    fails = [c for c in checks if not c["ok"]]
    verdict = "PASS" if not fails else "FAIL"
    if args.json:
        print(json.dumps({"verdict": verdict, "checks": checks},
                         ensure_ascii=False, indent=2))
    else:
        print("== meet_negctl（相遇写盘拦截负控）==")
        for c in checks:
            print("  [%s] %-26s %s" % ("ok" if c["ok"] else "FAIL",
                                       c["check"], c["detail"]))
        print("verdict: %s (%d checks, %d fail)"
              % (verdict, len(checks), len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
