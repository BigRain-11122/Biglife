# -*- coding: utf-8 -*-
"""年轮体式：8 种日记体，每种带样文（few-shot），按权重稳定分配。

方法来源（CEO 2026-11-18「去参考别人已有的模板」「颗粒度不够细」）：
  - SillyTavern Character Card V2（35.7k⭐）：角色一致性靠 `mes_example` 示例而非描述。
  - DSH Tavern（1.6k⭐）：前台只写正文，格式校验交给后台——prompt 堆禁令会分散注意力。
  结论：给样文 > 给规则。但样文本身也会被逐字抄（实测「老太太收被子怕鸟拉」连出 3 条），
  所以每条样文后面必须附「禁用词」把可辨识细节堵死。

权重依据（2026-11-18 实测）：
  看别人 25%（质量最高：天然禁写「我」，逼出具体人和细节）
  一件事 20% · 对话 20%（内容最实）
  记账 10% · 留话 10%
  抱怨 8% · 就一句 5%
  心气 2%（最容易写空，压到最低）

用法：
  python -X utf8 Tools/ring_forms.py --id C-01222
  python -X utf8 Tools/ring_forms.py --stats
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
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")

# (key, 名字, (lo, hi), 指令, [样文...], 禁用词提示)
FORMS = [
    ("observe", "看别人", (40, 70),
     "写今天你注意到的别人：对门、熟客、巷口那家、一个陌生人。全程不写自己。",
     ["卖菜的把烂叶子一片片摘下来堆在秤盘边，嘴上说着不碍事，手底下挑得比谁都细。",
      "收废品的老头把纸箱拆平，一层层摞齐，再用绳子十字捆好，蹲下去试了试松紧才走。"],
     "不许出现「老太太/被子/鸟/修鞋/秤砣」这些示例里的具体东西"),

    ("story", "一件事", (75, 105),
     "写今天完整的一件小事：起因、经过、结果。要有具体的人、具体的地点，可以有意外。",
     ["开门才发现钥匙插在里侧，拧不动。绕到后窗敲了半天，隔壁听见了，从墙头递过一把钳子。我把窗插销剪开，进去第一件事是给自己倒了杯水，手还在抖。",
      "说好晌午来的人没来，等到日头偏西才见着他，说是路上车坏了。我没多问，把留的那份热了热端上去，他低头吃完才说，其实是又跑了一趟别处。"],
     "不许出现「钥匙/钳子/窗插销/车坏」这些示例里的具体道具"),

    ("dialogue", "对话", (40, 75),
     "写今天真实发生的对话。**必须用引号把双方的话写出来，至少两句来回**；"
     "光用「他说…我说…」转述不算。",
     ["「这筐多少钱？」「八块五。」「昨儿还八块。」「昨儿是昨儿。」他掏了钱，我也没再让。",
      "「你那秤准不准啊？」「准，不准我砸了它。」他笑，我也笑，称完了多给抓了一把葱。"],
     "不许出现「筐/秤/葱/八块五」这些示例里的具体物与价"),

    ("log", "记账", (30, 55),
     "像记流水账那样写今天：做了几单、进多少、出多少、什么用完了要补。数字要具体。",
     ["换了六副鞋底，收九十；买胶花十四；中午面钱八块；剩六十八，明儿得补两块铁掌。",
      "卖了三筐，进一百二；退了一筐半烂的，倒贴十五；净落一百零五，够交这个月摊费。"],
     "不许出现「鞋底/胶/铁掌/筐/摊费」这些示例里的具体项"),

    ("message", "留话", (30, 50),
     "给某个人留的话：给家里、给熟客、给不在的人、给明天来的客人。称呼要具体。",
     ["二丫，锅里有粥，火关小些别糊了。我夜里有活儿，你先睡。",
      "周师傅，您那副镜我调好了，搁在最上一层架子上。您来取时言语一声，我给您验一遍。"],
     "不许出现「二丫/粥/周师傅/镜」这些示例里的具体人与物"),

    ("gripe", "抱怨", (25, 55),
     "写今天让你烦的一件小事：谁添了乱、什么没办成、哪口气咽不下。要有具体的人顶着。",
     ["说好的价临了又砍，砍完还嫌我给得少。这种人下回再来，我宁可空着摊也不接。",
      "刚摆好的东西被一脚踢乱，人家连句对不住都没有，走的时候还回头看了一眼，那眼神我记住了。"],
     "不许出现「砍价/踢乱/摊」这些示例里的具体情节"),

    ("oneline", "就一句", (8, 18),
     "只写一句，**必须 12 字以内**，短到不能再短。不要第二句，不要凑。",
     ["这活儿今天算是收尾了。", "明儿得早起，赶在头一班。"],
     "不许照抄示例的两句"),

    ("mood", "心气", (25, 50),
     "写今天的心气。别直接说情绪名，用手上的动作带出来。",
     ["活儿干到一半就不想动了，手里那件东西翻来覆去看了三遍，还是没下手。",
      "今天手快，平时要磨一下午的，晌午前就完了，完了还坐着发愣。"],
     "不许出现「翻来覆去/发愣」这些示例里的具体动作"),
]

WEIGHTS = {"observe": 25, "story": 20, "dialogue": 20, "log": 10,
           "message": 10, "gripe": 8, "oneline": 5, "mood": 2}

FORBID = ("禁止：结尾感悟句（「这日子嘛」「急不得」「慢慢来」）、"
          "无对象的动作清单（「把X挪了挪」）、比喻收尾（「像…一样」）、凑字数。"
          "**默认不写天气**：不写风、不写云、不写雨、不写温度；"
          "只有风或雨真的让你手上的活干不下去时，才用半句带过，写天气当成跑题。")


def form_of(cid):
    h = int(hashlib.md5(("form|%s" % cid).encode("utf-8")).hexdigest()[:8], 16)
    tot = sum(WEIGHTS[f[0]] for f in FORMS) * 10000
    pick = h % tot
    acc = 0
    for f in FORMS:
        acc += WEIGHTS[f[0]] * 10000
        if pick < acc:
            return f
    return FORMS[0]


def block_for_prompt(cid):
    key, name, (lo, hi), instr, examples, ban = form_of(cid)
    ex = "\n".join("  · %s" % e for e in examples)
    return ("【本轮体式·%s】%s篇幅 %d-%d 字。\n"
            "照下面这些的写法与口气来（**内容一个字都不许抄**，%s）：\n%s\n%s\n"
            % (name, instr, lo, hi, ban, ex, FORBID))


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
    c = collections.Counter()
    for cid in names:
        c[form_of(cid)[1]] += 1
    n = len(names)
    print("总人口 %d，体式分布：" % n)
    for k, v in c.most_common():
        print("  %-6s %5d (%4.1f%%)" % (k, v, 100.0 * v / n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.id:
        print(block_for_prompt(a.id))
    elif a.stats:
        stats()
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
