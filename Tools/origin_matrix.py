# -*- coding: utf-8 -*-
"""人口构成：56 源流协议 × 34 来处区 × 域外节点（CEO 2026-11-18 令）。

设计（不是贴标签，是给文化质地）：
  - 56 个民族 → 56 条「源流协议」：手艺 / 纹样 / 声感 / 一句生活底子。
    不写族名，写它在硅基城市里的形态（如「苗岭银饰协议」「雪域经幡协议」）。
  - 34 个省级行政区 → 34 个「来处区」：保留地理质感 + 一句说话脾气。
  - 域外节点约 5%：南洋/东瀛/半岛/南亚/新月/欧洲/非洲/拉美/北美。
  - 民族与省份**独立分配**（汉族也能生在滇池），域外整体替换来处。

纪律：
  - 稳定分配（同一 cid 永远同一结果），按权重（汉族约 60%，其余按现实比例递减）
  - 提示词里明确「别把源流当身份标签」，只当手上的习惯
  - 只给文化质地，不给刻板剧情

用法：
  python -X utf8 Tools/origin_matrix.py --id C-01222
  python -X utf8 Tools/origin_matrix.py --stats
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
DATA = os.path.join(CO, "data", "origin-matrix.json")
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")

_CACHE = {}


def load():
    if "m" in _CACHE:
        return _CACHE["m"]
    with open(DATA, encoding="utf-8") as f:
        m = json.load(f)
    _CACHE["m"] = m
    return m


def _pick(items, key, total=None):
    """按权重稳定选一项。"""
    h = int(hashlib.md5(key.encode("utf-8")).hexdigest()[:8], 16)
    tot = total if total is not None else sum(i["w"] for i in items)
    x = h % int(tot * 10000)
    acc = 0
    for it in items:
        acc += int(it["w"] * 10000)
        if x < acc:
            return it
    return items[-1]


def assign(cid):
    """返回 dict(people, province, outside, years)。"""
    m = load()
    peoples, provs, outside = m["peoples"], m["provinces"], m["outside"]
    pw = sum(p["w"] for p in peoples)
    zw = sum(p["w"] for p in provs)
    ow = sum(p["w"] for p in outside)
    # 域外比例 = ow / (pw + zw + ow)
    h0 = int(hashlib.md5(("zz|%s" % cid).encode("utf-8")).hexdigest()[:8], 16)
    is_out = (h0 % 10000) < int(10000 * ow / (pw + zw + ow))
    out = {"outside": None, "people": None, "province": None}
    if is_out:
        out["outside"] = _pick(outside, "out|" + cid, ow)
    else:
        out["people"] = _pick(peoples, "ppl|" + cid, pw)
        out["province"] = _pick(provs, "prv|" + cid, zw)
    h = int(hashlib.md5(("yrs|%s" % cid).encode("utf-8")).hexdigest()[:4], 16)
    out["years"] = 1 + h % 30
    return out


def block_for_prompt(cid, faction=None):
    """拼进 prompt 的一段（自然、不贴标签）。"""
    a = assign(cid)
    y = a["years"]
    if a["outside"]:
        o = a["outside"]
        return (
            "【你的来处】你不是本城土生——从%s那一带来，在这城里住了 %d 年。"
            "说话%s，偶尔漏出一两个外乡词。住了这么久，早被城里的日子磨圆了，"
            "别刻意学口音，也别拿它当身份标签。\n" % (o["n"], y, o["taste"]))
    p, v = a["people"], a["province"]
    return (
        "【你的来处·手上的老习惯】你在%s长大，在这城里住了 %d 年。"
        "源流是「%s」那一路：%s，%s的纹样，说话%s。%s。\n"
        "这些只落在手上和嘴上——别把它当身份标签念，也别解释来处，"
        "更别把源流写成异域风情。%s的底子，说出来就是%s那样。\n"
        % (v["n"], y, p["n"], p["craft"], p["pattern"], p["sound"], p["life"],
           v["n"], v["taste"]))


def stats():
    names = []
    try:
        with open(LIGHT, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    names.append(json.loads(line).get("id"))
                except ValueError:
                    continue
    except OSError:
        names = ["C-%05d" % i for i in range(1000, 3000)]
    pc, vc, oc = collections.Counter(), collections.Counter(), collections.Counter()
    for cid in names:
        a = assign(cid)
        if a["outside"]:
            oc[a["outside"]["n"]] += 1
        else:
            pc[a["people"]["n"]] += 1
            vc[a["province"]["n"]] += 1
    n = len(names)
    print("总人口 %d" % n)
    print("源于域外: %d (%.1f%%)" % (sum(oc.values()), 100.0 * sum(oc.values()) / n))
    print("\n-- 源流 Top 8 --")
    for k, v in pc.most_common(8):
        print("  %-10s %5d (%4.1f%%)" % (k, v, 100.0 * v / n))
    print("源流覆盖种类: %d" % len(pc))
    print("\n-- 来处 Top 8 --")
    for k, v in vc.most_common(8):
        print("  %-10s %5d (%4.1f%%)" % (k, v, 100.0 * v / n))
    print("来处覆盖种类: %d / 34" % len(vc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.id:
        print(block_for_prompt(a.id))
        return 0
    if a.stats:
        stats()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
