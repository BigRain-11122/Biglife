# -*- coding: utf-8 -*-
"""年轮体式：8 种日记体，每种带完整样文（few-shot），按 cid 稳定分配。

方法来源（2026-11-18 CEO「去参考别人已有的模板」「颗粒度不够细」）：
  - SillyTavern Character Card V2：角色一致性靠 `mes_example`（示例对话）而非描述；
    `scenario` 给当前情境；`alternate_greetings` 给多条完整开场而非模板。
  - DSH Tavern（1.6k⭐）：前台模型只写正文，格式与校验交给后台——
    prompt 塞满禁令会分散注意力，这正是「千篇一律」的病根。
  结论：给样文 > 给规则。每种体式配 2-3 条完整示例，模型照着写；禁令交给闸门事后查。

纪律：
  - 8 种体式按 cid 稳定分配（同一人永远同一体式，人格连贯）
  - 每种自带长度区间与样文；样文只示范「写成什么样」，内容不许抄
  - 明确禁：结尾感悟、无对象的动作清单、比喻收尾、凑字数
  - 天气与环境只在真挡了手上的活时提一句

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

FORMS = [
    ("gripe", "抱怨", (25, 55),
     "写今天让你烦的一件小事：谁添了乱、什么没办成、哪口气咽不下。要有具体的人顶着。",
     ["隔壁老周又把货堆到我门口，说了三回，回回说「就一天」。这回我直接把箱子挪他灶台边上了，爱咋咋地。",
      "说好今早来取修的收音机，等到日头偏西人影没见。我这人好说话，可也不能把我当没脾气的。"]),

    ("dialogue", "对话", (40, 75),
     "写一段今天真实发生的对话：谁先开的口、他说什么、你怎么回。用引号写出来，至少两句来回。",
     ["她说这单急，我说急也没用，船在江心。她急得直跺脚，我说你站这儿等，我跑一趟，最多半个钟头。",
      "老李凑过来问：「这价还能再低点不？」我说不能，这已是抹了零头的。他咂咂嘴，掏了钱。"]),

    ("log", "记账", (30, 55),
     "像记流水账那样写今天：做了几单、进多少、出多少、什么用完了要补。数字要具体。",
     ["早上卖了三屉粢饭，进八十四块；补了两斤油条面，出十二块；还给对门垫了五块，说是明儿还。",
      "修了四台收音机，收八十；换的两个管子是存货，不算成本；中午买面花十二，剩六十八。"]),

    ("observe", "看别人", (40, 70),
     "写今天你注意到的别人：对门、熟客、巷口那家、一个陌生人。全程不写自己。",
     ["对门那家老太太每天这时候出来晒被子，晒了半个钟头又收回去，说是怕鸟在上面拉。她家老头走了三年，被子还是两床。",
      "巷口修鞋的老许，一天不说话，只拿锤子敲。今天有个小孩蹲他旁边看了半个钟头，他也没撵。"]),

    ("oneline", "就一句", (10, 25),
     "只写一句。短，说清一件事或一个念头。不要第二个句子。",
     ["锁修好了，钥匙还是那把。", "明天又是双日，得早。", "这锅底，糊了三回了。"]),

    ("message", "留话", (30, 50),
     "给某个人留的话：给家里、给熟客、给不在的人、给明天来的客人。称呼要具体。",
     ["老张，你那把扳手放我这儿了，明早来拿，别忘。我七点开摊。",
      "阿婆，路滑，您别自己来，我收摊绕过去给您送。"]),

    ("story", "一件事", (70, 100),
     "写今天完整的一件小事：起因、经过、结果。要有具体的人、具体的地点，可以有意外。",
     ["早上开摊才发现秤砣不见了，昨儿收摊还在这儿。翻遍了筐也没有，只能拿隔壁那杆秤凑合。做了两单，第三单时老周从他摊子底下摸出来——是他收摊时顺手挪的。我骂了他一句，他把秤砣塞我手里，说赔你一包茶叶。",
      "收摊前来了个小姑娘，说拾到一张票，问是不是我的。我一看是隔壁面馆的，让她送过去。她跑了两趟才找着人。回来跟我说，那边的老板给了她一个糖。"]),

    ("mood", "心气", (25, 50),
     "写今天的心气：闷、松快、憋着、忽然想通。别直接说情绪名，用手上的动作带出来。",
     ["今天手上的活越做越慢，明明没几件，坐下来就不想动。收了摊在门口石阶上坐了好一会儿，也没想什么。",
      "今儿不知怎么了，做起事来手特别快。该两天的活半天就完了，还想再找点事做。"]),
]

FORBID = ("禁止：结尾感悟句（「这日子嘛」「急不得」「慢慢来」）、"
          "无对象的动作清单（「把X挪了挪」）、比喻收尾（「像…一样」）、凑字数。"
          "天气与环境只在你手上的活真被挡住时提一句，不写天气也可以。")


def form_of(cid):
    h = hashlib.md5(("form|%s" % cid).encode("utf-8")).hexdigest()
    return FORMS[int(h[:8], 16) % len(FORMS)]


def block_for_prompt(cid):
    key, name, (lo, hi), instr, examples = form_of(cid)
    ex = "\n".join("  · %s" % e for e in examples)
    return ("【本轮体式·%s】%s篇幅 %d-%d 字。\n"
            "照着下面这些的样子写（只学写法与口气，内容一个字都不许抄）：\n%s\n%s\n"
            % (name, instr, lo, hi, ex, FORBID))


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
