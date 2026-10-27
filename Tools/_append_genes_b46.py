#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具：b46 批 habits（生活小动作）候选池。

来源：R2395 让路窗（bm-a 工作日 09:00-19:00 算力让 CEO·年轮/相遇线按
D-20261020-02 延后至 19:00），本轮继续补习惯面稀区——既有 80 条多集中在
家务/工位/街坊/循环物，天气应对（备伞、收晾、封窗缝）、公共资源排队
（水房、公交卡）、广播与老物件（收音机、旧照片）三面仍空，故备候选落池。
先过 gene_nearcheck 双层判据（ha 阈值 70），只收 CLEAN。
"""
import json
import re
from pathlib import Path

LIVES = "genes/lives.json"

CANDIDATES = [
    "收音机固定在午后两点开，信号不好就转半圈天线再听",
    "出门前多带一把伞放在门口，谁回来晚了正好用",
    "翻旧照片只在下午翻，翻完一定按原来的次序压回抽屉底",
    "公交车卡里剩不到二十块就去充，说免得哪天回不了家",
    "往楼下水房排队只站在第二个位置，说第一个挡人打水",
    "冬天睡前把窗缝用旧报纸塞一道，嫌风钻进来响",
    "邻居家的菜刀钝了拿来磨，磨完顺手把刀背擦干再还",
    "旧手机充着电当闹钟用，响了自己先坐一会儿才起来",
    "腌菜坛子的水槽三天换一次水，手指探进去试凉不凉",
    "楼道灯坏了的当晚就换，说黑着台阶容易摔人",
    "接家里的电话一律站着接，说坐着说不清楚",
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