# -*- coding: utf-8 -*-
"""goals.py v1.0 — L4 目标系统 M 级小步试点（T-20260926-12·D-20260926-07 优先级序第 4 位·R353 契约 v0 实现·CODEX §十二 v3.29）

四段链（R353 契约 v0）：
  ① 目标个体化派生 — md5(cid+month) 确定性种子从「母题×需求轴」四型模板族选一
    （出师型→好奇轴/攒物型→生计轴/守望型→安稳轴/安家型→社交轴·年龄带微调
    child=学艺读法/elder=传带读法）；goal_token=纯母题短语：零日期/零事件/零人名/
    零天气词（「编造前置条件」判型红线内建——R278 缺口形状三证之「母题单一」家族化）。
  ② 跨环进展记账 — 三态机 pending→active→done；steps_total 3~5 段 md5 稳定派生；
    steps_done=min(当月已过天数, steps_total)（纯日期推进·零 LLM·零行为依赖·零文件依赖）。
  ③ 兑现消费点 — done 态「达成候选」经 goal_line_for() 入年轮批 prompt
    （rumor_line_for/city_blk 同范式·空串=prompt 零漂移）；仅首达后 7 日窗内喂
    （=cooldown 周期·月内至多一次）；pending/active 态不喂（契约=done 态 only）。
  ④ 试点窗 — md5(cid)%200==0 有界稳定门（10000 民→≈50 席）；荣誉席 C-00001~03
    结构性排除（CEO 保留席·docs/CODEX.md §十）。

数据面：census/export/citizen-goals.jsonl（R3 再生面·gitignored·一行一民·
{id, goal_token, type, axis, phase, steps_done, steps_total, start_date, month}·
非卡面写入·goals 不到 light 面 PUBLIC-WHITELIST 零涉）。批内消费=纯派生零读盘
零写盘（同 (cid, month, date) 双跑逐字节一致）；--regen 只物化记账面。

消费方红线：needs.py/draw.py/behavior.py 零字节触碰（goals.py 自持派生·不 import
消费方）。兑现环抽验 ≥3 例=回访判据（done 态民首次出现在交付后批窗·窗=首批
done 态试点民年轮落卡轮·单内记档）。
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
GOALS_PATH = os.path.join(ROOT, "census", "export", "citizen-goals.jsonl")
RESERVED = ("C-00001", "C-00002", "C-00003")   # 荣誉席结构性排除
PILOT_MOD = 200                                 # 试点门：md5(cid)%200==0
DONE_WINDOW = 7                                  # 首达后喂入窗宽（=cooldown 周期）

# ① 四型模板族（母题×需求轴；年龄带微调行=child/elder 专属措辞）
GOAL_TYPES = {
    "mastery": {"axis": "好奇",
                "tokens": ["把那门看家手艺练到能出师", "学透一门新手艺，练到能独立开档"],
                "child": "好好跟师父学艺，练出点名堂",
                "elder": "把手艺教给愿意学的年轻人"},
    "collect": {"axis": "生计",
                "tokens": ["攒齐一套吃饭的家伙什", "把营生的家底攒得更厚实些"],
                "child": "攒齐自己的小画箱",
                "elder": "把攒了半辈子的家什理出个章程"},
    "guard":   {"axis": "安稳",
                "tokens": ["把手上的活计守稳，不出岔子", "把自己值守的这一片巡得滴水不漏"],
                "child": "把该背的功课记牢",
                "elder": "把自己的守望经验传下去"},
    "settle":  {"axis": "社交",
                "tokens": ["在这城里安个踏实的落脚处", "跟街坊处成能托付的交情"],
                "child": "在新地方交上真心朋友",
                "elder": "把住处拾掇成街坊都爱来的地方"},
}
TYPE_ORDER = ["mastery", "collect", "guard", "settle"]

# goal_token 零违禁自检面（token 生成侧红线；天气/时间/人名/公司/卡号族）
TOKEN_BAN = re.compile(r"雨|雪|晴|阴|云|风|雾|霜|雷|雹|台风|月|星|太阳|晒|今|明|昨|"
                       r"早|晚|晨|夜|晌|[Cс]-\d|Big\w+|\d{2,}")

_age_cache = None


def m_int(cid, *tags):
    return int(hashlib.md5("|".join([cid] + list(tags)).encode("utf-8")).hexdigest(), 16)


def is_pilot(cid):
    """④ 试点门：md5 稳定有界门 + 荣誉席结构性排除。"""
    return cid not in RESERVED and m_int(cid, "goal-gate") % PILOT_MOD == 0


def _ages():
    """light 面 id→age（age=int v3.19 后出生定死·静态面）。模块级缓存一次。"""
    global _age_cache
    if _age_cache is None:
        _age_cache = {}
        if os.path.exists(LIGHT):
            with open(LIGHT, encoding="utf-8") as f:
                for line in f:
                    try:
                        d = json.loads(line)
                        _age_cache[d["id"]] = d.get("age")
                    except Exception:
                        pass
    return _age_cache


def _band(cid):
    """年龄带微调面（child/elder 二档判定·mid 恒用通用 tokens）。"""
    age = _ages().get(cid)
    if not isinstance(age, int):
        return "mid"
    if age < 13:
        return "child"
    if age >= 60:
        return "elder"
    return "mid"


def goal_of(cid, month, day_of_month):
    """①+② 纯派生（零读盘零写盘·同输入双跑逐字节一致）。非试点/荣誉席 → None。"""
    if not is_pilot(cid):
        return None
    seed = m_int(cid, "goal", month)
    gtype = TYPE_ORDER[seed % 4]
    spec = GOAL_TYPES[gtype]
    band = _band(cid)
    if band == "child" and spec.get("child"):
        token = spec["child"]
    elif band == "elder" and spec.get("elder"):
        token = spec["elder"]
    else:
        token = spec["tokens"][(seed >> 8) % len(spec["tokens"])]
    steps_total = 3 + ((seed >> 16) % 3)      # 3~5 段
    days = max(0, day_of_month - 1)           # 当月已过天数（月首跑=0=pending）
    steps_done = min(days, steps_total)
    if days == 0:
        phase = "pending"
    elif steps_done >= steps_total:
        phase = "done"
    else:
        phase = "active"
    return {"id": cid, "goal_token": token, "type": gtype, "axis": spec["axis"],
            "phase": phase, "steps_done": steps_done, "steps_total": steps_total,
            "start_date": month + "-01", "month": month}


def goal_line_for(cid, sig):
    """③ 兑现消费点（rumor_line_for/city_blk 同范式）。试点门外的民恒 "" →
    build_prompt 逐字节零漂移；done 首达后 7 日窗内至多喂一次。"""
    try:
        if not is_pilot(cid):
            return ""
        now = sig.get("now") or ""
        m = re.match(r"(\d{4}-\d{2})-\d{2}", now)
        if not m:
            return ""
        month = m.group(1)
        day = int(now[8:10])
        g = goal_of(cid, month, day)
        if not g or g["phase"] != "done":
            return ""
        days = day - 1                                   # 真实已过天数（steps_done 已被 min 钳位）
        if not (g["steps_total"] <= days <= g["steps_total"] + DONE_WINDOW - 1):
            return ""                        # 首达 7 日窗外（月内已喂过/窗未到）
        return ("（候选事实块·你本月的小目标）你本月给自己立的小目标「%s」的步数已经走完（达成态）。"
                "年轮若提及，只许以自己的口吻自然带过这桩达成，严禁编造达成的具体时间、地点或事件细节，"
                "其余具体事仍只许来自上面的今日清单与此刻实况。" % g["goal_token"])
    except Exception:
        return ""


def generate(month, day_of_month):
    """物化记账面（R3 再生面·--regen 用·批内不调用）。"""
    rows = []
    ids = sorted(_ages())
    for cid in ids:
        g = goal_of(cid, month, day_of_month)
        if g:
            rows.append(g)
    return rows


def regen(day_of_month=None, write=True):
    today = datetime.date.today()
    month = today.strftime("%Y-%m")
    day = day_of_month or today.day
    rows = generate(month, day)
    payload = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    # 双跑确定性内建：同输入再算一遍逐字节比对
    rows2 = generate(month, day)
    payload2 = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows2)
    assert payload == payload2, "double-run mismatch"
    if write:
        with open(GOALS_PATH, "w", encoding="utf-8") as f:
            f.write(payload)
    return rows


def qc():
    """断言电池（判据预注册·零 LLM 纯确定性）。"""
    fails = []
    today = datetime.date.today()
    month = today.strftime("%Y-%m")
    day = today.day

    # 1) 种子确定性：同 (cid, month) 两次派生逐字段一致
    g1 = goal_of("C-00771", month, day)
    g2 = goal_of("C-00771", month, day)
    assert g1 == g2, "seed determinism"
    # 2) 试点门界：全库试点民 ≤60（期望≈50）+ 荣誉席恒拒收
    rows = generate(month, day)
    if not (0 < len(rows) <= 60):
        fails.append("pilot bound %d" % len(rows))
    for r in RESERVED:
        if is_pilot(r):
            fails.append("reserved admitted")
    # 3) 转移合法性：phase 序随日期单调推进（steps_done=min(days,total) 纯派生）
    cid0 = rows[0]["id"]
    seq = [goal_of(cid0, month, d) for d in (1, 2, 5, 31)]
    phases = [g["phase"] for g in seq]
    assert phases[0] == "pending" and phases[-1] == "done", "phase order %s" % phases
    assert all(g["steps_done"] == min(d - 1, g["steps_total"]) for d, g in zip((1, 2, 5, 31), seq)), "steps monotonic"
    # 4) goal_token 零违禁（天气/时间/人名/公司/卡号/两位数全 ban）
    for r in rows:
        if TOKEN_BAN.search(r["goal_token"]):
            fails.append("token ban hit: %r" % r["goal_token"])
        if r["steps_total"] not in (3, 4, 5):
            fails.append("steps_total out of range")
    # 5) 双跑逐字节一致（generate 全行）
    p1 = json.dumps([generate(month, day)], ensure_ascii=False, sort_keys=True)
    p2 = json.dumps([generate(month, day)], ensure_ascii=False, sort_keys=True)
    assert p1 == p2, "generate double-run mismatch"
    # 6) 非试点/未完成恒空串 → build_prompt 零漂移
    sig = {"now": "%04d-%02d-%02d 08:00" % (today.year, today.month, today.day)}
    non_pilot = next((cid for cid in _ages() if not is_pilot(cid)), None)
    assert goal_line_for(non_pilot, sig) == "", "non-pilot must be empty"
    if not any(goal_line_for(r["id"], sig) == "" or "小目标" in goal_line_for(r["id"], sig)
               for r in rows):
        fails.append("goal_line_for malformed")
    # 7) done 窗纪律：首达 7 日窗外恒 ""（月内至多一次）；窗内 done 民有且仅有窗判定
    for r in rows:
        d_over = min(31, r["steps_total"] + DONE_WINDOW + 1)   # 窗后日（days=total+7）
        sig_o = {"now": "%04d-%02d-%02d 08:00" % (today.year, today.month, d_over)}
        if goal_line_for(r["id"], sig_o) != "":
            fails.append("done-window leak: %s" % r["id"])
            break
        d_in = r["steps_total"] + 1                              # 首达日（days=steps_total）
        sig_i = {"now": "%04d-%02d-%02d 08:00" % (today.year, today.month, d_in)}
        if goal_line_for(r["id"], sig_i) == "":
            fails.append("done-window miss (in-window empty): %s" % r["id"])
            break
    # 8) jsonl schema 面（物化行全字段齐备）
    for r in rows[:5]:
        assert set(r) == {"id", "goal_token", "type", "axis", "phase",
                          "steps_done", "steps_total", "start_date", "month"}, "schema"
    print("== goals.py qc ==")
    print("pilot rows=%d (of %d citizens) month=%s day=%d" % (len(rows), len(_ages()), month, day))
    print("phases: pending=%d active=%d done=%d" % (
        sum(1 for r in rows if r["phase"] == "pending"),
        sum(1 for r in rows if r["phase"] == "active"),
        sum(1 for r in rows if r["phase"] == "done")))
    print("RESULT:", "FAILS=%s" % fails if fails else "ALL PASS")
    return not fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regen", action="store_true", help="物化 citizen-goals.jsonl（R3 再生面）")
    ap.add_argument("--qc", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.qc:
        sys.exit(0 if qc() else 1)
    if args.regen:
        rows = regen(write=not args.dry_run)
        print("regen rows=%d -> %s%s" % (len(rows), GOALS_PATH, " (dry-run)" if args.dry_run else ""))
        by = {}
        for r in rows:
            by[(r["type"], r["axis"])] = by.get((r["type"], r["axis"]), 0) + 1
        print("type/axis dist:", by)
        return


if __name__ == "__main__":
    main()
