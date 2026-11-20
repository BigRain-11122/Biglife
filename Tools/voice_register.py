# -*- coding: utf-8 -*-
"""voice_register.py — 按年龄/职业给每个居民定一个**文笔档位**（零 LLM）。

为什么（2026-11-19 实测基线）
---------------------------
按年龄带统计当天 7,593 条年轮：中位长度 66–68 字、p90 84–86、句读密度
8.97–9.15、方言词率 4.2–6.5%——**六个年龄带几乎完全重合**。
六岁的孩子和七十八岁的老人用同一个长度、同一个呼吸、同一个腔调写字，
这正是 CEO 说的「不是数字」：数字才没有年龄，人才有。

档位不是「换个口吻」这么虚的东西，它必须落到**可测的四件事**上：
  ① 长度区间（孩子话少、老人话碎、壮年话多）
  ② 句读密度（孩子短句多感叹、老人多停顿）
  ③ 注意对象（孩子只看眼前物、壮年看账、老人看人）
  ④ 称呼与自我指涉（叔/姨/阿婆、我/俺/咱）

设计律
------
- 只给**写法约束**，不给可抄的句子（抄句子的老毛病已经踩过三次）。
- 与 `ring_forms.py`（八种日记体）正交：体式决定"写什么形式"，档位决定"用什么口气"。
- 职业作微调而非主导：年龄决定呼吸，职业决定用词。
- 任何解析失败返回空串（prompt 零漂移）。
"""
from __future__ import annotations

import re

AGE_RE = re.compile(r"\u6027\u522b\u00b7\u5e74\u9f84\*\*\s*(\S+)\s*\u00b7\s*(\d+)\s*\u5c81")
PROF_RE = re.compile(r"\*\*\u804c\u4e1a\*\*\s*(.+?)(?:\uff1a|\n)")

# (下限, 上限, 名称, 长度区间, 写法)
BANDS = [
    (0, 12, "儿童", (30, 55),
     "眼睛只到柜台高：写你够得着的一件小东西、一句被大人打断的话；短句为主，"
     "可以有问号；不懂就别装懂，不许讲道理、不许感伤。"),
    (13, 17, "少年", (40, 75),
     "半大孩子：在意同伴怎么看你，情绪直白、话里有赌气；句子短促，可以半句就停，"
     "不许用成年人的稳妥口吻。"),
    (18, 25, "青年", (55, 90),
     "刚自己拿主意：算自己的账、算将来，带点自嘲；动作快，句子利落。"),
    (26, 40, "壮年", (60, 95),
     "事情压在身上：写进度、成本、时间不够用；少抒情，多算账、多交代下一步。"),
    (41, 55, "中年", (55, 90),
     "拿过去比现在：一句眼前、一句从前；想给建议但忍住一半，语气稳。"),
    (56, 69, "初老", (50, 85),
     "动作慢了半拍：先顾身体再顾生意；常提旧人旧物，句子里带停顿。"),
    (70, 200, "老年", (30, 65),
     "话少而碎：省主语、省连接词，两三句就完；时间说得模糊（那年、早先、后来）；"
     "重复提一件旧事不算啰嗦。"),
]

# 职业微调（命中即附一句，未命中不写）
PROF_TWEAK = [
    (("师", "匠", "修", "裁", "编"), "手上功夫占一半篇幅：写工具、写手感、写火候。"),
    (("医", "护"), "先看人的气色，再说话。"),
    (("学", "生"), "学校与同伴是主要参照。"),
    (("调", "算", "码", "数据", "算法"), "会留心数字与偏差，但只能用生活话讲。"),
    (("卖", "摊", "商", "店"), "成本与回头客挂在嘴上。"),
]


def _age(text):
    m = AGE_RE.search(text or "")
    return int(m.group(2)) if m else None


def band_of(age):
    for lo, hi, name, rng, spec in BANDS:
        if age is not None and lo <= age <= hi:
            return name, rng, spec
    return None, None, ""


def block_for(cid, card_text):
    """返回文笔档位块（可能为空串）。"""
    try:
        age = _age(card_text)
        name, rng, spec = band_of(age)
        if not spec:
            return ""
        line = "\u4f60\u4eca\u5e74 %d \u5c81\uff08%s\uff09\uff0c\u8fd9\u4e00\u6bb5%s\uff1a\u957f\u5ea6 %d\u2013%d \u5b57\u3002%s" % (
            age, name, "\u5199\u6cd5", rng[0], rng[1], spec)
        m = PROF_RE.search(card_text or "")
        prof = m.group(1) if m else ""
        for keys, tweak in PROF_TWEAK:
            if any(k in prof for k in keys):
                line += tweak
                break
        line += "\u8fd9\u4e9b\u662f\u5199\u6cd5\u8981\u6c42\uff0c\u4e0d\u8981\u628a\u5b83\u4eec\u5199\u8fdb\u53e5\u5b50\u91cc\uff0c\u4e5f\u4e0d\u8981\u63d0\u4f60\u591a\u5927\u3002\n"
        return line
    except Exception:  # noqa: BLE001 - 档位缺失绝不阻断生成
        return ""


def limit_for(card_text, default=90):
    """该居民的**硬**长度上限（给 fit_ring_line 用）。

    提示词里写「30–55 字」实测不管用（模型跟着更近的禁令走），所以档位必须
    落到代码裁剪：儿童 55 / 老年 65 / 其余 90。裁剪本身会切在句末标点上，
    不会切出半句（fit_ring_line 已带收口）。
    """
    try:
        age = _age(card_text)
        name, rng, _spec = band_of(age)
        return rng[1] if rng else default
    except Exception:  # noqa: BLE001
        return default


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"C:\Users\sjs20\Desktop\FluxGroup\life\BigLife\Tools")
    import evolve_citizen as ec
    for cid in sys.argv[1:] or ["C-01326", "C-03392", "C-03608"]:
        p = ec.find_card(cid)
        t = open(p, encoding="utf-8").read() if p else ""
        print(cid, "->", block_for(cid, t).strip()[:120])
