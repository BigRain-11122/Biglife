#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refresh_census_index.py - rebuild census/INDEX.md from live exports.

Why (2026-11-14 R2864, T-20261114-01): INDEX.md 是 generate_census.py 的
「批次快照」产物 —— 只有整库重生成（P-0）时才写一次。此后新居民由复产批 /
影射册 / 荣誉席等独立通道入册，卡片照常落盘，INDEX.md 却无人再写：
实测停更 24.6 天、总人口仍写 10109 而 light 面实为 10114（差 5）。
与 T-20261112-02 同病根：有产物、有读者、无轮次引用 ⇒ 静默漂移。

本工具只做一件事：按当前 census/export/citizens-light.jsonl 实测重算统计，
确定性重写 census/INDEX.md（零 LLM）。已登记 Tools/round_daily.py 日更闸，
数据变即重建，不再靠人记得手跑。

Honesty: 派生不出的段一律不写（不拿旧快照冒充新数）——
  * 年龄段需卡面 band，light 面不含该字段（真实人源 age=None），故不列；
  * 指纹唯一性只在出生时校验过（REG.fingerprints），事后无法从导出面复原，故不列。

Usage: python -X utf8 Tools/refresh_census_index.py [--check]
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
META = os.path.join(CO, "genes", "meta.json")
OUT = os.path.join(CO, "census", "INDEX.md")

SP_DISP = {"carbon": "碳基市民", "silicon": "硅基民", "sprite": "像素灵"}
RESERVED_LABEL = "荣誉席（城主位/创始家庭）"


def load_rows(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build(rows, meta):
    dname = {d["id"]: d["name"] for d in meta["districts"]}
    fname = {}
    for sp in meta["species"]:
        for fac in sp.get("factions", []):
            if fac.get("name"):
                fname[fac["id"]] = fac["name"]
    by_district = collections.Counter()
    by_species = collections.Counter()
    by_faction = collections.Counter()
    by_gender = collections.Counter()
    by_axis = collections.Counter()
    reserved = 0
    for r in rows:
        dist = r.get("district") or ""
        if dist == "":
            reserved += 1
        else:
            by_district[dname.get(dist, dist)] += 1
        by_species[r.get("species") or "?"] += 1
        by_faction[r.get("faction") or "?"] += 1
        by_gender[r.get("gender") or "?"] += 1
        by_axis[r.get("axis") or "手写锚（六轴之外）"] += 1

    names = [r.get("name") for r in rows]
    hooks = [r.get("hook") for r in rows if r.get("hook")]
    dup_names = len(names) - len(set(names))
    dup_hooks = len(hooks) - len(set(hooks))

    total = len(rows)
    L = ["# INDEX —— 万人户籍名册统计（数据源实测）", "",
         "> 本文件由 `Tools/refresh_census_index.py` 确定性重建（零 LLM），"
         "数据源=`census/export/citizens-light.jsonl` 实读行数 + `genes/meta.json` 显示名。",
         "> 2026-11-14 起纳入 `Tools/round_daily.py` 日更闸：数据变即重建，"
         "不再随出生批次手写快照漂移（此前停更 24.6 天、总人口差 5 无人发现）。", "",
         ("**总人口：%d**（light 面实读 %d 行；其中%s %d 席不入城区分布）"
          % (total, total, RESERVED_LABEL, reserved)), "",
         "## 按城区（light 面实读）", ""]
    for k, v in sorted(by_district.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("- %s：%d" % (k, v))
    if reserved:
        L.append("- %s：%d——不入城区分布（CEO 命名令 orders/O-20260924-1620-bm-a）"
                 % (RESERVED_LABEL, reserved))
    L += ["", "## 按物种（light 面实读）", ""]
    for k, v in sorted(by_species.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("- %s：%d" % (SP_DISP.get(k, "%s（未登记显示名·原文 id）" % k), v))
    L += ["", "## 按派系（light 面实读）", ""]
    for k, v in sorted(by_faction.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("- %s：%d" % (fname.get(k, "%s（未登记显示名·原文 id）" % k), v))
    L += ["", "## 按性别（light 面实读）", ""]
    for k, v in sorted(by_gender.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("- %s：%d" % (k, v))
    L += ["", "## 按思想六轴（light 面实读）", ""]
    for k, v in sorted(by_axis.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("- %s：%d" % (k if k.endswith("轴") else k + "轴", v))
    L += ["", "## 唯一性（light 面可复算项）", "",
          "- 姓名唯一：%s（在册 %d，重名 %d）"
          % ("PASS" if dup_names == 0 else "FAIL", len(names), dup_names),
          "- 钩子唯一：%s（在册 %d，重复 %d）"
          % ("PASS" if dup_hooks == 0 else "FAIL", len(hooks), dup_hooks),
          "- 指纹唯一：出生时校验（`REG.fingerprints`），导出面不含该字段，事后不可复算——不在此列。", "",
          "## 未列入的段（诚实边界）", "",
          "- 年龄段：需卡面 `band`，light 面不含（真实人源 `age=None`），故不列；卡面「性别·年龄」行为准。", "",
          "消费面：`census/export/citizens-light.jsonl`（引擎/CityWatch 只读）。"
          "手写锚见 `census/anchors/`。保留席见 `census/reserved/README.md`。", ""]
    return "\n".join(L)


def main():
    if not os.path.exists(LIGHT):
        print("MISSING light export: %s (run census export first)" % LIGHT)
        return 2
    with open(META, encoding="utf-8") as f:
        meta = json.load(f)
    text = build(load_rows(LIGHT), meta)
    check = "--check" in sys.argv[1:]
    old = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = f.read()
    if old == text:
        if not check:
            # v0.25 (2026-11-14 R2908): 幂等重建不写文件 ⇒ mtime 停在旧值，而
            # round_daily 的 dep-mtime 判据（源 light 面每轮由行为线重写）会每轮
            # 判 stale —— 假红噪音。touch 表示「产物已核验至此刻、内容与源一致」，
            # 判据收口且不产生 git 改动（内容未变）。--check 只读不 touch。
            os.utime(OUT, None)
        print("OK unchanged (idempotent) out=%s" % os.path.relpath(OUT, CO))
        return 0
    if check:
        print("STALE out=%s" % os.path.relpath(OUT, CO))
        return 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("OK rebuilt out=%s lines=%d" % (os.path.relpath(OUT, CO), text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
