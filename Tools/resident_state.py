# -*- coding: utf-8 -*-
"""resident_state.py — 每天给年轮提示词补一小块**内在状态**：这周压在心头的事、
身边的熟人、还没办成的那一件。

为什么要有它（2026-11-19 审计实锚）
----------------------------------
居民早就有：需求层（needs.py 四轴强度 → census/export/citizen-needs.jsonl）、
意图层（agency.py 每日自主动作）、关系面（卡面 **关系** 行）。
但三样**从来没进过年轮提示词**（evolve 里 agency 只被提过一次且是注释，
relations 引用 0 次，needs 只用于「好奇位采样」旁路）。于是每天写出来的句子
只跟人设 + 当日事件有关——读起来是随机日常片段，不是一个有欲望、有打算、
有熟人的人。CEO 最高要求「每个居民都是硅基智能体活人感」，第一刀不是加产量，
是把已有的内在状态接进表达层。

设计律（都是被踩过的）
--------------------
1. **不给可抄的句子**。agency 的四型模板每轴只有 4 条，直接注入＝一周内被抄满，
   重演出身/现状「127 句撑一万人」的老毛病。这里只给**语义驱动的抽象描述**
   （「跟挣口饭钱有关、还没办成」），语言交给模型。
2. **周锚定，日不变**：需求轴按 md5(cid+ISO周) 在强轴里选，连续 7 天同一件心事；
   纯日锚会让居民每天换一个念头，读起来像失忆。
3. 关系用卡面真名（千人千面、且是这个人自己的生活），不生成新名字。
4. 零 LLM、零新数据面；任一环缺失就少一句，全缺返回空串（prompt 零漂移）。
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
NEEDS_PATH = os.path.join(CO, "census", "export", "citizen-needs.jsonl")

REL_RE = re.compile(r"C-\d{5}\s+([^\s；。（），、]+)")
# 只放行 C- 编号后的人名：家户条目形如「家户 H-1002 老两口（…）」，把 H- 也当 id
# 会抓出「老两口」「夫妻带娃」当名字，状态块就成了「常来往的是夫妻带娃」。
# 另一条是纯中文名：卡面存在「应Kai」「龚Vivi」这类带拉丁的名字，而年轮禁拉丁
# 字母——把这种名字喂进去等于给闸送拒稿（gate 会反复 defer 该席）。
CN_NAME_RE = re.compile(r"^[\u4e00-\u9fa5·]{2,8}$")
NEED_WORD = {
    "anwen": "安顿日子的事",
    "shengji": "挣钱的事",
    "shejiao": "跟人来往的事",
    "haoqi": "琢磨新东西的事",
}
_NEEDS = None


def _needs():
    global _NEEDS
    if _NEEDS is None:
        out = {}
        try:
            with open(NEEDS_PATH, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        e = json.loads(ln)
                    except ValueError:
                        continue
                    if e.get("id"):
                        out[e["id"]] = e
        except OSError:
            pass
        _NEEDS = out
    return _NEEDS


def _relations(card_text):
    """卡面 **关系** 行里的熟人名字（形如「棋友 C-07448 冯小杏」）。"""
    m = re.search(r"\*\*关系\*\*\s*(.+?)(?:\n|$)", card_text or "")
    if not m:
        return []
    seen, out = set(), []
    for part in m.group(1).split("；"):
        for nm in REL_RE.findall(part):
            nm = nm.strip()
            if nm not in seen and CN_NAME_RE.match(nm) and not nm.startswith("H-"):
                seen.add(nm)
                out.append(nm)
    return out[:2]


def _week_axis(cid, day, rec):
    """周锚定：在强度≥1 的轴里按 md5(cid+周) 选一个，整周不变。"""
    needs = (rec or {}).get("needs") or {}
    strong = [a for a in ("shengji", "anwen", "shejiao", "haoqi") if needs.get(a, 0) >= 1]
    if not strong:
        top = (rec or {}).get("top")
        return top if top in NEED_WORD else ""
    y, w, _ = datetime.date.fromisoformat(day).isocalendar()
    h = int(hashlib.md5(("%s#%04dW%02d" % (cid, y, w)).encode("utf-8")).hexdigest()[:8], 16)
    return strong[h % len(strong)]


def block_for(cid, card_text, day=None):
    """拼状态块；空串＝这轮不带状态（prompt 零漂移）。"""
    try:
        day = day or datetime.date.today().isoformat()
        rec = _needs().get(cid) or {}
        lines = []
        axis = _week_axis(cid, day, rec)
        if axis:
            lines.append("这一周你手头压着一件事，是%s，还没办成。"
                         % NEED_WORD.get(axis, ""))
        rels = _relations(card_text)
        if rels:
            lines.append("身边常来往的是%s。" % "、".join(rels))
        if not lines:
            return ""
        lines.append("今天就写这件没办成的事碰到了什么：你手上做了什么、卡在哪、"
                     "谁插了一句话。别把上面几句抄进正文，也别用「计划」「目标」这类词，"
                     "更别把心事直接说出来。")
        return "\n".join(lines) + "\n"
    except Exception:  # noqa: BLE001 - 状态块缺失不该阻断任何生成
        return ""


if __name__ == "__main__":
    import sys
    sys.path.insert(0, HERE)
    cid = sys.argv[1] if len(sys.argv) > 1 else "C-01353"
    import evolve_citizen as ec
    p = ec.find_card(cid)
    txt = open(p, encoding="utf-8").read() if p else ""
    print(block_for(cid, txt))
