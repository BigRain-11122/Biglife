#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b47 批 habits（生活小动作）候选池。

来源：R2404 让路窗（bm-a 工作日 09:00-19:00 算力让 CEO·年轮/相遇线按
D-20261020-02 延后至 19:00）。既有 88 条集中在家务/工位/街坊/天气应对/
公共资源/老物件/工具排布，本轮补五个仍空的稀区：数字生活（相册）、
口味偏好（吃面）、通勤观察（公交数站）、邻里暗助（挂菜不留名）、
动火安全（刨花）、门面（门牌）与食材手感（抓米）。

先过 gene_nearcheck 双层判据（ha 阈值 70），只收 CLEAN；
首轮 6 条 FLAG 已按判据换句互验（b47 → b47b → 单条三验）。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

CANDIDATES = [
    "每周日晚上把手机相册清一遍，只留九张，说太多就记不住那天",
    "吃面先喝半口汤再放醋，说先尝原味才知道今天的汤熬够不够",
    "坐公交只挑靠窗的单座，一路数站牌，坐过两站也认了",
    "每月买两份菜，一份挂在楼上老两口门把手上，不留名",
    "初一必清一次柜顶，把尘扫干净了心里才清爽",
    "动火之前先把地上的刨花扫净，说火星子最认这个",
    "每样工具都拴根红绳，谁借走了绳就挂在哪家门上",
    "洗之前把手伸进每个兜底摸一圈，摸出什么都摆在桌上认一遍",
    "傍晚坐在广场石阶上，看放学的娃娃们成群往家走",
    "过节前把门牌擦到能照出人影，说门面是给人找路的",
    "买米必抓一把放手心里看，米粒断得多就不买",
    "遇到话多的客人先递杯水，说话说一半自然就缓下来了",
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def append(path, key, rendered):
    t = Path(path).read_text(encoding="utf-8")
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: %s in %s" % (key, path))
    add = "".join(",\n      " + x for x in rendered)
    t = t[: m.end(2)] + add + t[m.end(2):]
    Path(path).write_text(t, encoding="utf-8", newline="\n")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", nargs="*", default=None,
                    help="nearcheck CLEAN 的候选原文；缺省=全收")
    a = ap.parse_args()
    keep = CANDIDATES if a.keep is None else [x for x in CANDIDATES if x in a.keep]
    before = len(load(LIVES)["habits"])
    fresh = [x for x in keep if x not in load(LIVES)["habits"]]
    append(LIVES, "habits", [json.dumps(x, ensure_ascii=False) for x in fresh])
    lives = load(LIVES)
    after = len(lives["habits"])
    print("habits %d -> %d (appended %d)" % (before, after, len(fresh)))
    for x in fresh:
        assert x in lives["habits"], x
    assert after == before + len(fresh)
    print("verify: all %d landed, pool now %d" % (len(fresh), after))


if __name__ == "__main__":
    main()