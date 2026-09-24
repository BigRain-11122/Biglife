#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rumor_chain.py v1.0 — 流言链引擎（T-20260924-16b·契约=cognition/RUMOR-CHAIN.md v1.0）

事件经居民 A→B 确定性跳数传播（带冷却+失真闭集）——用户从他人之口听见城市=社会性在场证明。
零 LLM 零 API 纯确定性：选跳/延迟/失真全 md5 派生（python hash() 进程随机化禁用=behavior.py 同律）。
按需调用面（非 R3 再生面）·FluxVerse 事件流只读零写回。

字段名勘误处理：契约 §一 JSON 形状将「跳数」与「跳列表」同名 hops 各列一次（对象键不可重复），
按后者为定谳——列表承 hops 名，跳数=len(hops)，--qc 判据 2 断言补位。
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
ENGINE_V = "v1.0"
HOPS_MIN, HOPS_MAX, HOPS_DEFAULT = 1, 6, 3
COOL_DEFAULT = 60
RESERVED = ("C-00001", "C-00002", "C-00003")  # 荣誉席=人设权 CEO 保留面，不自动入链（显式 --seed 仍可）
PADDING = ("听说", "好像")  # 垫话闭集（二选一）——零天气/天体/时段词（机审门触发词族规避=R40 纪律）
FUZZ = "几"  # 数字模糊唯一引入字符
OPS = ("trunc", "fuzz", "pad", "noop")  # 失真闭集（每跳至多 1 次）
CLAUSE = re.compile(r"(?<=[。！？；!?;])")


def m(*parts):
    return hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def m_int(*parts):
    return int(m(*parts), 16)


def load_census():
    """census/export/citizens-light.jsonl 只读消费（id+district 两键足用）。"""
    out = []
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("id"):
                out.append((o["id"], o.get("district") or ""))
    return out


def t_trunc(text):
    """截尾（末分句）：单分句/截后为空 → None（回退无操作）。"""
    parts = [p for p in CLAUSE.split(text) if p]
    if len(parts) < 2:
        return None
    out = "".join(parts[:-1])
    return out or None


def t_fuzz(text):
    """数字模糊：阿拉伯数字串→「几」；无数字 → None。"""
    out = re.sub(r"[0-9]+", FUZZ, text)
    return out if out != text else None


def apply_op(text, op, pick):
    """闭集变换（至多 1 次）+回退：trunc/fuzz 不可施作时回退 noop。"""
    if op == "trunc":
        return t_trunc(text)
    if op == "fuzz":
        return t_fuzz(text)
    if op == "pad":
        return PADDING[pick] + text
    return text


def hop_delay(event_id, seed, hop, cool_min):
    """确定性延迟 = cool_min + md5 % cool_min（上界 2×cool_min）；cool_min=0=不冷却档。"""
    if cool_min <= 0:
        return 0
    return cool_min + m_int(event_id, seed, hop, "delay") % cool_min


def pick_next(event_id, seed, hop, chain_ids, census, seed_district):
    """选人词域：seed 城区池优先，池尽则全城池；链内去重；md5 榜序确定性。"""
    used = set(chain_ids)
    for pred in (lambda d: d == seed_district, lambda d: True):
        cands = [cid for cid, dist in census
                 if cid not in used and cid not in RESERVED and pred(dist)]
        if not cands:
            continue
        cands.sort(key=lambda cid: m(event_id, seed, hop, cid))
        return cands[0]
    return None


def build_chain(event_id, event_text, seed, hops, cool_min, at):
    """核心链构造：同 (event, seed, 参数) 输出逐字节一致。"""
    seed_district = dict(CENSUS).get(seed, "")
    chain, out_hops = [seed], []
    cur, ts = event_text, at
    for hop in range(1, hops + 1):
        nxt = pick_next(event_id, seed, hop, chain, CENSUS, seed_district)
        if nxt is None:
            break  # 全城池尽（万人库 1..6 跳不可达，护栏）
        op = OPS[m_int(event_id, seed, hop, "op") % 4]
        new = apply_op(cur, op, m_int(event_id, seed, hop, "pad") % 2)
        if new is None:  # trunc/fuzz 不可施作 → 回退无操作
            op, new = "noop", cur
        ts = ts + timedelta(minutes=hop_delay(event_id, seed, hop, cool_min))
        out_hops.append({"hop": hop, "from": chain[-1], "to": nxt,
                         "ts": ts.strftime("%Y-%m-%d %H:%M"), "text": new, "op": op})
        chain.append(nxt)
        cur = new
    return {"event_id": event_id, "seed": seed, "hops": out_hops,
            "cool_min": cool_min, "at": at.strftime("%Y-%m-%d %H:%M"),
            "engine_v": ENGINE_V}


CENSUS = []          # module cache (loaded lazily in main/qc)


def validate(hops, cool_min):
    if not (HOPS_MIN <= hops <= HOPS_MAX):
        sys.exit("error: --hops 有效域 1..6（得 %s）" % hops)
    if cool_min < 0:
        sys.exit("error: --cool-min 不得为负（得 %s）" % cool_min)


def qc():
    """判据 1-5 断言电池（判据 6）：全过才 PASS。"""
    ev = "QC-EV-0001"
    txt = "G16 U184输入链急件修复。round 78: monitoring WQ 71/82。P02-W02验收问闭环。"
    at = datetime(2026, 9, 24, 20, 0)
    seeds = [c for c in ("C-00010", "C-00050", "C-00100", "C-00500", "C-01000",
                          "C-05000", "C-09000", "C-09999") if c in dict(CENSUS)]
    results = []

    def check(name, ok):
        results.append((name, bool(ok)))

    # 判据 1 确定性：同输入双跑逐字节一致（8 seeds × 默认与边界参数）
    for s in seeds:
        a = json.dumps(build_chain(ev, txt, s, 3, 60, at), ensure_ascii=False)
        b = json.dumps(build_chain(ev, txt, s, 3, 60, at), ensure_ascii=False)
        check("determinism %s" % s, a == b)

    # 判据 2 跳数参数化：默认 3 + 边界 1/6；越界拒绝
    check("hops default=3", len(build_chain(ev, txt, seeds[0], 3, 60, at)["hops"]) == 3)
    check("hops=1", len(build_chain(ev, txt, seeds[0], 1, 60, at)["hops"]) == 1)
    check("hops=6", len(build_chain(ev, txt, seeds[0], 6, 60, at)["hops"]) == 6)
    for bad in (0, 7):
        try:
            validate(bad, 60)
            check("hops reject %s" % bad, False)
        except SystemExit:
            check("hops reject %s" % bad, True)

    # 判据 3 冷却参数化：cool=60 相邻跳间隔 ∈[60,120)；cool=0 不冷却档合法
    for s in seeds[:4]:
        ch = build_chain(ev, txt, s, 6, 60, at)
        diffs = [(datetime.strptime(h2["ts"], "%Y-%m-%d %H:%M") -
                  datetime.strptime(h1["ts"], "%Y-%m-%d %H:%M")).total_seconds() / 60
                 for h1, h2 in zip(ch["hops"], ch["hops"][1:])]
        check("cool>=60 %s" % s, all(60 <= d < 120 for d in diffs))
        ch0 = build_chain(ev, txt, s, 6, 0, at)  # cool=0 护栏：零除不死
        d0 = [(datetime.strptime(h2["ts"], "%Y-%m-%d %H:%M") -
               datetime.strptime(h1["ts"], "%Y-%m-%d %H:%M")).total_seconds() / 60
              for h1, h2 in zip(ch0["hops"], ch0["hops"][1:])]
        check("cool=0 legal %s" % s, all(d == 0 for d in d0))

    # 判据 4 失真有界零编造：字符集 ⊆ 原文∪闭集；每跳恰 1 次闭集变换可重derive；垫话零触发词
    allowed = set(txt) | set(PADDING[0] + PADDING[1] + FUZZ)
    for s in seeds:
        cur = txt
        for h in build_chain(ev, txt, s, 6, 60, at)["hops"]:
            check("charset %s h%d" % (s, h["hop"]), set(h["text"]) <= allowed)
            check("op-closed %s h%d" % (s, h["hop"]), h["op"] in OPS)
            red = apply_op(cur, h["op"], m_int(ev, s, h["hop"], "pad") % 2) or cur
            check("op-rederive %s h%d" % (s, h["hop"]), red == h["text"])
            cur = h["text"]
    triggers = ("雨", "月", "台风", "今早", "早晨", "晨光", "今晚", "今夜", "深夜", "夜深", "风")
    check("padding trigger-free", not any(t in PADDING[0] + PADDING[1] + FUZZ for t in triggers))

    # 判据 5 选人词域：链内零重复（含 seed）+from 链连续+全在册+同城区优先（池足时）
    dist = dict(CENSUS)[seeds[0]]
    for s in seeds:
        ch = build_chain(ev, txt, s, 3, 60, at)
        ids = [s] + [h["to"] for h in ch["hops"]]
        check("chain-dedup %s" % s, len(ids) == len(set(ids)))
        check("from-seed %s" % s, ch["hops"][0]["from"] == s)
        check("link-continuity %s" % s,
              all(h2["from"] == h1["to"] for h1, h2 in zip(ch["hops"], ch["hops"][1:])))
        in_book = dict(CENSUS)
        check("all-in-census %s" % s, all(i in in_book for i in ids))
        same_d = [in_book[h["to"]] == in_book[s] for h in ch["hops"]]
        pool_n = sum(1 for cid, d2 in CENSUS if d2 == in_book[s] and cid not in RESERVED)
        check("district-first %s" % s, all(same_d) or pool_n < 4)

    fails = [n for n, ok in results if not ok]
    print("== rumor_chain --qc（契约判据 1-5 电池·%d 断言）==" % len(results))
    print("PASS %d / FAIL %d" % (len(results) - len(fails), len(fails)))
    if fails:
        print("FAILED:", ", ".join(fails))
        sys.exit(1)
    print("QC PASS")


def main():
    global CENSUS
    ap = argparse.ArgumentParser(description="流言链引擎 v1.0（契约=cognition/RUMOR-CHAIN.md）")
    ap.add_argument("--event-id")
    ap.add_argument("--event-text")
    ap.add_argument("--seed")
    ap.add_argument("--hops", type=int, default=HOPS_DEFAULT)
    ap.add_argument("--cool-min", type=int, default=COOL_DEFAULT)
    ap.add_argument("--at", default=None, help="YYYY-MM-DD HH:MM；缺省=当前时刻截整分（显式传参确定性面）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--qc", action="store_true")
    args = ap.parse_args()
    CENSUS = load_census()
    if args.qc:
        qc()
        return
    for k in ("event_id", "event_text", "seed"):
        if not getattr(args, k):
            sys.exit("error: --%s 必填" % k.replace("_", "-"))
    validate(args.hops, args.cool_min)
    by_id = dict(CENSUS)
    if args.seed not in by_id:
        sys.exit("error: seed %s 不在 census 导出面" % args.seed)
    if args.at:
        try:
            at = datetime.strptime(args.at, "%Y-%m-%d %H:%M")
        except ValueError:
            sys.exit("error: --at 格式 YYYY-MM-DD HH:MM")
    else:
        at = datetime.now().replace(second=0, microsecond=0)
    obj = build_chain(args.event_id, args.event_text, args.seed, args.hops, args.cool_min, at)
    blob = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(blob)
        print("written:", args.out, "hops:", len(obj["hops"]))
    else:
        sys.stdout.write(blob)


if __name__ == "__main__":
    main()
