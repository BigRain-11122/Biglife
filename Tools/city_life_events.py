#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""街区日常母题池 — T-20261112-01 修法②（2026-11-12 R2567 @BigLife-OSLoop）

问题（R2566 实测）：FluxVerse 生产事件流尾部 200 行里，scrub 之后含中文内容
字段的行 = 0（机器台账占满窗口，残留的 RESIDENT_SAY 全是「显存稳…轮转」）。
居民的年轮因此只剩真实天气可锚，靠 LLM 惯性套话（tmpl 16.7%、defect 22.9%）。

律的边界（本工具的诚实声明，写进产物的 META 行）：
  * FluxVerse 事件流 = 兄弟公司仓，只读；本工具绝不写那边。
  * 真实事件不足时不许造「新闻」——本工具产出的是**街区长期日常母题**
    （这条街上本来就在发生的生活底子），不是今天新发生的事。
  * 因此每条都带 provenance：kind=motif / generator / seed / 基因出处，
    消费面（evolve_citizen.real_signals）按素材库口径喂、锚注脚同步标口径。

确定性：同一 (date) -> 字节相同（md5 seeding），复跑幂等（不改写既有文件）。

用法：
  python -X utf8 Tools/city_life_events.py                # 生成/校验今天
  python -X utf8 Tools/city_life_events.py --date 2026-11-12 --print
"""
import argparse
import datetime
import hashlib
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "events", "life")
GENES = os.path.join(ROOT, "genes")

# 城区分布按 census 实际人口加权（2026-11-12 抽样 400 卡：GAME 城 381/400
# = 游戏楼/X026 城门/八号楼/像素匠人巷；北外滩 4；QUANT 城 4）。
DISTRICTS = (
    ("GAME 城 · 游戏楼街区", "gaming", 2),
    ("GAME 城 · 像素匠人巷", "gaming", 2),
    ("GAME 城 · 八号楼街区", "gaming", 1),
    ("GAME 城 · X026 城门区", "gaming", 1),
    ("北外滩·治理岸 · 脑环广场街区", "governance", 1),
    ("QUANT 城 · K线广场", "quant", 1),
)

# 六个句式族（错开骨架，避免 6 条母题长成一个模板）。
# 全部避开天气词（雨/晴/太阳/风/晒/雾/月/星）与时段词（今早/傍晚/夜），
# 因为这些断言归真实天气与真实时刻管，母题库不许越权。
FRAMES = (
    "{d}的{prof}把{obj}挪到门口搁着，{habit}。",
    "巷子里有人拿{obj}来换{obj2}，{prof}说值不值另讲，先用着。",
    "{obj}旧了，{prof}拿在手里掂了掂，到底没舍得扔。",
    "{prof}把{obj}用布包好压在箱底，箱角还塞着{obj2}。",
    "邻家小孩围着{obj}看，{prof}讲了半天来历，说得自己先笑了。",
    "{prof}家的{obj}被借走三天，还回来时多了道磕痕，谁也没提。",
)


def m(*parts):
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


# 母题不许越权的字面：天气类（雨/晴/太阳/风/晒/雾/雷/雪/云/月/星）归真实天气与
# 实况闸管，时段类（今早/傍晚/深夜/放学…）归真实时刻闸管。带这些字的基因一律
# 不进母题库——否则居民会把母题里的「下雨天」写成今天的实况，反被判负。
BANNED_GENE = re.compile(
    r"雨|雪|晴|阴|云|风|雾|雷|晒|太阳|月亮|月光|星空|台风|"
    r"今早|今晨|早晨|清晨|清早|晨光|晨风|上午|中午|晌午|下午|傍晚|黄昏|"
    r"今晚|今夜|深夜|夜深|放学|天亮|天黑")
PUNCT = "。！？!?.、，,；; \u3000"


def _clean(frag, cap=14):
    """基因原文多是整段描述（「卖鱼摊的木盆沿，常年渗着水渍」），只取首个
    短语做母题里的物件名，否则句子会长成两句并成一句。"""
    s = str(frag).strip()
    s = re.split(r"[，,。；;！!？?]", s)[0].strip()
    s = s[:cap].strip(PUNCT)
    return s


def load_genes():
    with open(os.path.join(GENES, "lives.json"), encoding="utf-8") as f:
        lives = json.load(f)
    with open(os.path.join(GENES, "professions.json"), encoding="utf-8") as f:
        profs = json.load(f)
    return lives, profs


def build(date_str):
    """-> [ {type, ts, zone, district, text, provenance}, ... ]  同日字节恒定。"""
    lives, profs = load_genes()
    habit = [_clean(g, 20) for g in lives.get("habits") or []
             if g and not BANNED_GENE.search(str(g))]
    habit = [g for g in habit if len(g) >= 4]
    objs = [_clean(g) for g in lives.get("hook_objects") or []
            if g and not BANNED_GENE.search(str(g))]
    objs = [g for g in objs if 2 <= len(g) <= 11 and "的" not in g and "着" not in g] or \
        [g for g in objs if 2 <= len(g) <= 14]
    profl = [_clean(p.get("name") or p.get("text") or "", 8)
             for p in (profs.get("professions") or [])]
    profl = [p for p in profl if p] or ["街坊"]
    if not habit or not objs:
        return []

    n = 0
    rows = []
    for district, zone, weight in DISTRICTS:
        for k in range(weight):
            seed = m(date_str, district, k)
            frame = FRAMES[n % len(FRAMES)]
            obj = objs[int(seed[2:10], 16) % len(objs)]
            obj2 = objs[int(seed[10:18], 16) % len(objs)]
            if obj2 == obj:
                obj2 = objs[(objs.index(obj) + 7) % len(objs)]
            # 第 3 族是「{obj}旧了」，物件名自带旧/老 会叠成「旧日历旧了」。
            if frame is FRAMES[2] and obj[0] in "旧老":
                obj = objs[(objs.index(obj) + 11) % len(objs)]
            text = frame.format(
                d=district.split(" · ")[-1],
                prof=profl[int(seed[18:24], 16) % len(profl)],
                obj=obj, obj2=obj2,
                habit=habit[int(seed[24:30], 16) % len(habit)],
            )
            rows.append({
                "type": "LIFE_MOTIF",
                "ts": date_str,
                "zone": zone,
                "district": district,
                "text": text,
                "provenance": {
                    "kind": "motif",          # 素材库母题，不是当日新闻
                    "generator": "Tools/city_life_events.py",
                    "seed": seed,
                    "genes": {"objects": obj, "objects2": obj2},
                },
            })
            n += 1
    meta = {
        "type": "LIFE_MOTIF_META",
        "ts": date_str,
        "count": len(rows),
        "honesty": ("街区长期日常母题（genes/ 母题库按日确定性抽取），"
                    "非 FluxVerse 实时事件、非今日新闻；消费面须按素材库口径喂，"
                    "不得当作城市新发生的事转述。"),
        "generator": "Tools/city_life_events.py",
    }
    return [meta] + rows


def write(date_str, rows, quiet=False):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, date_str + ".jsonl")
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
        if old == body:
            if not quiet:
                print("unchanged", path)
            return path, False
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    if not quiet:
        print("written", path, "rows=%d" % (len(rows) - 1))
    return path, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--print", dest="do_print", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    rows = build(a.date)
    if not rows:
        print("no motif built (genes missing)")
        return 1
    _path, _changed = write(a.date, rows, a.quiet)
    if a.do_print:
        for r in rows[1:]:
            print("[%s] %s" % (r["zone"], r["text"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
