# -*- coding: utf-8 -*-
"""memory_stream.py — 居民记忆检索：按「新近 × 重要 × 相关」取回，而不是取最近三条。

为什么改（2026-11-20）
---------------------
原先年轮提示词里的「你最近的记忆」= **最后 3 条年轮**（按日期倒序取尾）。
那是"流水账式回忆"：一个人不会因为某天更近就记住它，他记住的是**当时更要紧**、
并且**跟眼下手头的事有关**的那些天。

参考实现：Stanford「Generative Agents: Interactive Simulacra of Human Behavior」
（joonspk-research/generative_agents）的 memory stream 检索——
    score = α_recency · recency + α_importance · importance + α_relevance · relevance
三项各自归一化到 [0,1]，α 全取 1，取 top-k。那篇论文的 importance 由 LLM 打 1–10 分；
本机不为此多烧一次推理（每条年轮一次打分＝每天上万次调用），改用**确定性关键词打分**
（冲突/钱/身体/亲人/第一次/决定…），并在文档里标明这是代理指标：它评的是
"这条经历里有没有事"，不是"当事人的感受值多大"。

判断依据（可测）：改动后同一批居民喂给模型的 3 条记忆，应与"最近 3 条"有显著差异；
抽样看"被选中但不在最近三条里"的比例，落在 30–70% 说明检索真的在起作用
（0% = 没生效；100% = 把新近性完全丢了，人会显得失忆）。
"""
from __future__ import annotations

import datetime
import math
import re

# 重要度关键词（代理指标，只判"有没有事"，不判情绪烈度）
IMPORTANT = [
    ("失去", 5), ("走了", 4), ("病", 4), ("伤", 4), ("药", 2), ("住院", 5),
    ("钱", 3), ("账", 2), ("欠", 3), ("赔", 4), ("涨价", 3), ("工钱", 3),
    ("第一次", 4), ("头一回", 3), ("决定", 4), ("分手", 5), ("吵", 3), ("闹", 3),
    ("亲", 3), ("娃", 3), ("孩子", 3), ("阿婆", 2), ("师父", 3), ("老主顾", 3),
    ("塌", 4), ("坏", 2), ("修好", 3), ("丢", 4), ("找回来", 4),
    ("雨", 1), ("风", 1),
]
AGE_DAYS = 60.0          # recency 的时间常数（天）


def _imp(text):
    s = 0
    for kw, w in IMPORTANT:
        if kw in text:
            s += w
    return min(10.0, s)


def _grams(text, n=2):
    t = re.sub(r"[^\u4e00-\u9fa5]", "", text or "")
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def _rel(text, ctx):
    a, b = _grams(text), _grams(ctx)
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def select(ents, ctx="", k=3, today=None):
    """ents=[(date_str, text)] → 按「新近×重要×相关」取 k 条，按日期升序返回。"""
    if not ents:
        return []
    today_d = today or datetime.date.today()
    rows = []
    for d, tx in ents:
        try:
            days = max(0.0, (today_d - datetime.date.fromisoformat(d)).days)
        except (ValueError, TypeError):
            days = 999.0
        rec = math.exp(-days / AGE_DAYS)
        imp = _imp(tx) / 10.0
        rel = _rel(tx, ctx)
        rows.append((rec + imp + rel, d, tx))
    rows.sort(key=lambda r: (-r[0], r[1]))
    top = rows[:k]
    top.sort(key=lambda r: r[1])
    return [(d, tx) for _s, d, tx in top]
