#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""opening_capacity - 开口容量的证据读数器（只读·零 LLM·不动产线）

用途：回答「跨席开口撞车到底该扩哪个池子」这个被反复拍脑袋的问题。

背景：R3208 记「genes 的 sentence_tics.openers 仅 7 条 → 结构性碰撞源」，
但 evolve_citizen v0.65 注释实写「skeleton reuse, not skeleton count, was the
real today-dup-opening source」，且 v0.62 已把 OPENING_SKELETONS 从 12 扩到 24。
两套说法指向不同的修法（扩 tics 池 vs 扩骨架池 vs 改提示词），必须先有口径。

本工具的两个读数：
  1) 容量面：骨架池大小 × 当日参与居民数 → 每个骨架的期望公开席位负载
     （负载 >1 = 同骨架必然被 ≥2 人拿到，模型逐字抄骨架即撞车）。
  2) 归属面：把 state/ring-refusals.jsonl 的历史 opening12 逐条判归属——
     命中骨架池=骨架驱动；命中 PROMPT_EXAMPLE_ECHO=示例回声；都不命中=模型自造
     吸引子。归错池子的修法救不回另外两池。

口径纪律：骨架/示例池一律从 Tools/evolve_citizen.py 源码 AST 取值，不 import
（该脚本 4000 行，import 有副作用），也不在这里重抄一份（两套副本必漂移）。

用法：
  python -X utf8 Tools/opening_capacity.py
  python -X utf8 Tools/opening_capacity.py --as-of 2026-11-16 --window 24 --json
  python -X utf8 Tools/opening_capacity.py --report   # 落 qa/OPENING-CAPACITY-<date>.md
"""

import argparse
import ast
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Tools", "evolve_citizen.py")
REFUSALS = os.path.join(ROOT, "state", "ring-refusals.jsonl")
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
GENES_V2 = os.path.join(ROOT, "genes", "persona-v2.json")
QA_DIR = os.path.join(ROOT, "qa")


def _pools_from_source(path=SRC):
    """从源码 AST 取 OPENING_SKELETONS / PROMPT_EXAMPLE_ECHO（零 import）。"""
    tree = ast.parse(io.open(path, encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id in (
                "OPENING_SKELETONS",
                "PROMPT_EXAMPLE_ECHO",
            ):
                try:
                    out[tgt.id] = [str(x) for x in ast.literal_eval(node.value)]
                except (ValueError, SyntaxError):
                    pass
    return out


def _norm(s):
    """比较用归一：去空白与标点，只留字（骨架带逗号冒号，模型常换/丢）。"""
    return re.sub(r"[\s，。、：；！？——…,.!?:;\"'()（）]+", "", s or "")


def _prefix_hit(opening12, pool):
    """opening12 是否落在某条骨架/示例的字面轨道上（前缀包含，双向容忍截断）。"""
    o = _norm(opening12)
    if not o:
        return None
    for item in pool:
        it = _norm(item)
        if not it:
            continue
        # 骨架 12 字内基本已被模型抄完；容忍模型吞掉尾部标点或补半个字
        if it.startswith(o) or o.startswith(it):
            return item
        # 模型常把骨架与自己的物件拼一起，前 8 字对齐即视为同轨
        if len(o) >= 8 and len(it) >= 8 and o[:8] == it[:8]:
            return item
    return None


def _load_refusals(as_of=None, window_h=None):
    rows = []
    if not os.path.exists(REFUSALS):
        return rows
    end = None
    if as_of:
        end = datetime.strptime(as_of, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    for ln in io.open(REFUSALS, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            row = json.loads(ln)
        except ValueError:
            continue
        ts = row.get("ts") or ""
        try:
            t = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        if end and t > end:
            continue
        if window_h and end:
            if t < end - timedelta(hours=window_h):
                continue
        elif window_h and not end:
            if t < datetime.now() - timedelta(hours=window_h):
                continue
        row["_t"] = t
        rows.append(row)
    return rows


def _evolving_citizens(as_of=None):
    """当日参与年轮的居民数。

    口径修正：`recent_ring` 非空是「历史上有过年轮」=10114 全员，拿它当参与面会
    把负载算高两个量级。真参与面 = `recent_ring_date` 落在当日的人数，这才是与
    骨架池做除法的分子。
    """
    if not os.path.exists(LIGHT):
        return 0
    day = as_of or datetime.now().strftime("%Y-%m-%d")
    n = 0
    for ln in io.open(LIGHT, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            row = json.loads(ln)
        except ValueError:
            continue
        if str(row.get("recent_ring_date") or "")[:10] == day:
            n += 1
    return n


def measure(as_of=None, window_h=None):
    pools = _pools_from_source()
    sk = pools.get("OPENING_SKELETONS") or []
    ex = pools.get("PROMPT_EXAMPLE_ECHO") or []

    tics = {}
    if os.path.exists(GENES_V2):
        try:
            tics = (json.load(io.open(GENES_V2, encoding="utf-8")).get("sentence_tics") or {})
        except (ValueError, IOError):
            tics = {}

    rows = _load_refusals(as_of=as_of, window_h=window_h)

    # 归属判定
    bucket = Counter()
    by_skel = defaultdict(lambda: {"rows": 0, "cids": set(), "openings": set()})
    by_invented = defaultdict(lambda: {"rows": 0, "cids": set()})
    for r in rows:
        o = r.get("opening12") or ""
        cid = r.get("cid") or "?"
        hit = _prefix_hit(o, sk)
        if hit is not None:
            bucket["skeleton"] += 1
            d = by_skel[hit]
            d["rows"] += 1
            d["cids"].add(cid)
            d["openings"].add(_norm(o))
        elif _prefix_hit(o, ex) is not None:
            bucket["prompt_echo"] += 1
        else:
            bucket["invented"] += 1
            d = by_invented[_norm(o)]
            d["rows"] += 1
            d["cids"].add(cid)

    total = sum(bucket.values())

    # 容量面：同批居民 hash 到骨架池的期望负载
    residents = _evolving_citizens(as_of=as_of)
    n_sk = len(sk)
    load = round(residents / n_sk, 2) if n_sk else None

    # 自造吸引子头部（真正「传染」的载体）
    invented_top = sorted(
        (
            {"opening": k, "rows": v["rows"], "cids": len(v["cids"])}
            for k, v in by_invented.items()
        ),
        key=lambda x: (-x["rows"], -x["cids"]),
    )[:10]

    open_counter = Counter(r.get("opening12") or "" for r in rows)
    distinct = len([k for k in open_counter if k])
    multi = sum(1 for k, v in open_counter.items() if k and v > 1)
    cross = sum(
        1
        for k in open_counter
        if k and len({r.get("cid") for r in rows if (r.get("opening12") or "") == k}) > 1
    )
    wasted = sum(v - 1 for k, v in open_counter.items() if k and v > 1)

    return {
        "as_of": as_of or datetime.now().strftime("%Y-%m-%d"),
        "window_h": window_h,
        "rows": total,
        "distinct_openings": distinct,
        "multi_openings": multi,
        "cross_cid_openings": cross,
        "wasted_calls": wasted,
        "waste_ratio": round(wasted / total, 4) if total else 0.0,
        "attribution": {
            "skeleton": bucket.get("skeleton", 0),
            "prompt_echo": bucket.get("prompt_echo", 0),
            "invented": bucket.get("invented", 0),
            "pct": {
                k: (round(v / total, 4) if total else 0.0)
                for k, v in (
                    ("skeleton", bucket.get("skeleton", 0)),
                    ("prompt_echo", bucket.get("prompt_echo", 0)),
                    ("invented", bucket.get("invented", 0)),
                )
            },
        },
        "pools": {
            "opening_skeletons": n_sk,
            "prompt_examples": len(ex),
            "tics_openers": len(tics.get("openers") or []),
            "tics_closers": len(tics.get("closers") or []),
        },
        "capacity": {
            "evolving_residents": residents,
            "expected_load_per_skeleton": load,
            "note": "load>1 = 同骨架必然被 ≥2 人拿到；模型逐字抄骨架即撞",
        },
        "invented_top": invented_top,
        "skeleton_hits": sorted(
            (
                {
                    "skeleton": k,
                    "rows": v["rows"],
                    "cids": len(v["cids"]),
                    "distinct_openings": len(v["openings"]),
                }
                for k, v in by_skel.items()
            ),
            key=lambda x: -x["rows"],
        )[:10],
    }


def _render_md(m):
    L = []
    L.append("# OPENING-CAPACITY · %s（窗=%s h）" % (m["as_of"], m["window_h"] or "全量"))
    L.append("")
    L.append("> 只读证据读数，不改产线、不调模型。口径=AST 取池 + 拒稿逐条归属。")
    L.append("")
    L.append("## 1 池子现状")
    p = m["pools"]
    L.append("| 池 | 条数 | 作用面 |")
    L.append("|---|---|---|")
    L.append("| OPENING_SKELETONS | %d | 逐席哈希分配的开句骨架（模型逐字抄） |" % p["opening_skeletons"])
    L.append("| PROMPT_EXAMPLE_ECHO | %d | 提示词里的示例句（出现即判照抄） |" % p["prompt_examples"])
    L.append("| sentence_tics.openers | %d | 话语口头禅（不是 opening12 的直接来源） |" % p["tics_openers"])
    L.append("| sentence_tics.closers | %d | 收尾口头禅 |" % p["tics_closers"])
    L.append("")
    L.append("## 2 容量面")
    c = m["capacity"]
    L.append("- 当日有年轮的居民（参与面）：**%d**" % c["evolving_residents"])
    L.append("- 骨架池：**%d** 条 → 期望每骨架负载 **%s 人**" % (p["opening_skeletons"], c["expected_load_per_skeleton"]))
    L.append("- 判定：%s" % c["note"])
    L.append("")
    L.append("## 3 拒稿归属（这批撞车到底该怪谁）")
    a = m["attribution"]
    L.append("| 归属 | 行数 | 占比 | 修法指向 |")
    L.append("|---|---|---|---|")
    L.append("| 骨架驱动（命中骨架池） | %d | %.1f%% | 扩 OPENING_SKELETONS |" % (a["skeleton"], a["pct"]["skeleton"] * 100))
    L.append("| 示例回声（命中示例池） | %d | %.1f%% | 改提示词/去示例 |" % (a["prompt_echo"], a["pct"]["prompt_echo"] * 100))
    L.append("| 模型自造吸引子 | %d | %.1f%% | 禁族+短语级闸（现役闸） |" % (a["invented"], a["pct"]["invented"] * 100))
    L.append("")
    L.append("## 4 多烧读数")
    L.append("- rows=%d / 不同开口=%d / 被复用=%d / 跨居民复用=%d / 多烧=%d 条=**%.1f%%**"
             % (m["rows"], m["distinct_openings"], m["multi_openings"],
                m["cross_cid_openings"], m["wasted_calls"], m["waste_ratio"] * 100))
    L.append("")
    if m["invented_top"]:
        L.append("## 5 自造吸引子 top10（真传染载体）")
        L.append("| opening12 | 行数 | 居民数 |")
        L.append("|---|---|---|")
        for it in m["invented_top"]:
            L.append("| %s | %d | %d |" % (it["opening"], it["rows"], it["cids"]))
        L.append("")
    if m["skeleton_hits"]:
        L.append("## 6 骨架命中 top10")
        L.append("| 骨架 | 行数 | 居民数 | 不同开口 |")
        L.append("|---|---|---|---|")
        for it in m["skeleton_hits"]:
            L.append("| %s | %d | %d | %d |"
                     % (it["skeleton"], it["rows"], it["cids"], it["distinct_openings"]))
        L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as-of", help="YYYY-MM-DD，含当日的滚窗终点")
    ap.add_argument("--window", type=int, default=None, help="滚窗小时数（需 --as-of 或取当下）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--json-out", help="同时把 JSON 写到指定路径（UTF-8·无 BOM·供下游 json.load）")
    ap.add_argument("--report", action="store_true", help="落 qa/OPENING-CAPACITY-<date>.md")
    a = ap.parse_args()

    m = measure(as_of=a.as_of, window_h=a.window)

    if a.json_out:
        # PowerShell 5.1 的 `>` 重定向写 UTF-16LE+BOM，下游 json.load 会炸；
        # 需要机读一律走本参数，不要用 shell 重定向。
        with io.open(a.json_out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(m, ensure_ascii=False, indent=2) + "\n")
        print("json -> %s" % a.json_out)

    if a.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
    else:
        print("== opening_capacity (evidence only, no LLM, no pipeline change) ==")
        p = m["pools"]
        print("pools: skeletons=%d examples=%d tics_openers=%d tics_closers=%d"
              % (p["opening_skeletons"], p["prompt_examples"],
                 p["tics_openers"], p["tics_closers"]))
        c = m["capacity"]
        print("capacity: residents=%d  expected_load_per_skeleton=%s"
              % (c["evolving_residents"], c["expected_load_per_skeleton"]))
        a2 = m["attribution"]
        print("attribution: skeleton=%d (%.0f%%)  prompt_echo=%d (%.0f%%)  invented=%d (%.0f%%)"
              % (a2["skeleton"], a2["pct"]["skeleton"] * 100,
                 a2["prompt_echo"], a2["pct"]["prompt_echo"] * 100,
                 a2["invented"], a2["pct"]["invented"] * 100))
        print("waste: rows=%d distinct=%d multi=%d cross_cid=%d wasted=%d (%.1f%%)"
              % (m["rows"], m["distinct_openings"], m["multi_openings"],
                 m["cross_cid_openings"], m["wasted_calls"], m["waste_ratio"] * 100))
        if m["invented_top"]:
            print("invented top3:")
            for it in m["invented_top"][:3]:
                print("   %s  rows=%d cids=%d" % (it["opening"], it["rows"], it["cids"]))
        verdict = "SKELETON_POOL" if a2["skeleton"] > max(a2["invented"], a2["prompt_echo"]) else (
            "PROMPT_ECHO" if a2["prompt_echo"] > max(a2["skeleton"], a2["invented"]) else "INVENTED")
        print("dominant_attribution: %s" % verdict)

    if a.report:
        if not os.path.isdir(QA_DIR):
            os.makedirs(QA_DIR)
        path = os.path.join(QA_DIR, "OPENING-CAPACITY-%s.md" % (a.as_of or datetime.now().strftime("%Y-%m-%d")))
        io.open(path, "w", encoding="utf-8", newline="\n").write(_render_md(m) + "\n")
        print("report -> %s" % os.path.relpath(path, ROOT))

    return 0


if __name__ == "__main__":
    sys.exit(main())
