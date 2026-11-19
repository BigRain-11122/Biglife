# -*- coding: utf-8 -*-
"""social_audit.py — 居民社交图的「双向性」体检与修复。

为什么（CEO 2026-11-19「硅基居民互相也要有联系和连接，不是孤单的个体」）
--------------------------------------------------------------------------
实测 census/export/citizen-relations.jsonl：285 万条边里 283 万是 `block`
（同街区相邻的噪音），真关系只有 1.88 万条（buddy 15131 / household 3629 /
meet 73），而**双向率 0%**——A 的卡面写着「棋友 B」，B 的卡面里没有 A。
于是每个人在文本里都只有一个"单向的熟人"：他提你，你不提他。
这不是社交，是各说各话。

判据
----
- reciprocal_rate：真关系边里，反向边也存在的比例。**目标 ≥ 80%**。
- isolated：卡面 0 条真关系的居民数。**目标 ≤ 2%**。
- 只统计 buddy / household / meet；block 是地理噪音，不计入社交。

用法
----
  python -X utf8 Tools/social_audit.py --check          # 只读体检
  python -X utf8 Tools/social_audit.py --check --json
  python -X utf8 Tools/social_audit.py --fix            # 补反向关系（写回滚档）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

REL_JSONL = os.path.join(CO, "census", "export", "citizen-relations.jsonl")
BACKUP = os.path.join(CO, "state", "social-fix-backup.json")
REAL_RELS = ("buddy", "household", "meet")
REL_LINE_RE = re.compile(r"\*\*关系\*\*\s*(.+?)(?:\n|$)")
NAME_RE = re.compile(r"^#\s*(C-\d{5})\s*·\s*(\S+)")
ID_RE = re.compile(r"C-\d{5}")
# 反向标签：对称关系照抄；「常客/老主顾」是单向视角（店主↔客人），
# 反向写成「常客」会变成「我是我自己的常客」这种病句，统一落成「相熟」。
MIRROR = {
    "茶友": "茶友", "忘年交": "忘年交", "对手": "对手", "牌友": "牌友",
    "邻居": "邻居", "老搭档": "老搭档", "棋友": "棋友", "工友": "工友",
    "常客": "相熟", "老主顾": "相熟",
}
MAX_REL = 4          # 一张卡最多几条真关系，超出就不再补，避免关系行膨胀


def load_edges():
    out = []
    try:
        with open(REL_JSONL, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    e = json.loads(ln)
                except ValueError:
                    continue
                if e.get("rel") in REAL_RELS and e.get("a") and e.get("b"):
                    out.append(e)
    except OSError:
        pass
    return out


def card_path(cid):
    import evolve_citizen as ec
    return ec.find_card(cid)


def read_card(cid):
    p = card_path(cid)
    if not p:
        return None, ""
    try:
        with open(p, encoding="utf-8") as fh:
            return p, fh.read()
    except OSError:
        return None, ""


def rel_line(text):
    m = REL_LINE_RE.search(text or "")
    return m.group(1).strip() if m else ""


def name_of(text, cid):
    m = NAME_RE.search(text or "")
    if m and m.group(1) == cid:
        return m.group(2)
    return ""


def audit(edges):
    cache = {}
    def info(cid):
        if cid not in cache:
            p, t = read_card(cid)
            cache[cid] = (p, t, rel_line(t), name_of(t, cid))
        return cache[cid]

    recip = 0
    pairs = set((e["a"], e["b"]) for e in edges)
    for a, b in pairs:
        _pa, _ta, _ra, _na = info(a)
        _pb, _tb, rb, _nb = info(b)
        if a in rb:
            recip += 1
    have = {}
    for a, b in pairs:
        have[a] = have.get(a, 0) + 1
        have[b] = have.get(b, 0) + 1
    isolated = sum(1 for cid, (_p, _t, _r, _n) in cache.items() if have.get(cid, 0) == 0)
    return {
        "real_edges": len(edges),
        "pairs": len(pairs),
        "reciprocal_pairs": recip,
        "reciprocal_rate": round(recip / max(1, len(pairs)), 4),
        "nodes": len(cache),
        "isolated": isolated,
        "isolated_rate": round(isolated / max(1, len(cache)), 4),
    }


def fix(edges, dry=False):
    """给缺反向的一方补一条关系。只补 buddy/meet；household 是 H- 编号，形状不同。"""
    added = skipped = 0
    backup = {}
    touched = {}
    by_b = {}
    for e in edges:
        if e["rel"] not in ("buddy", "meet"):
            continue
        by_b.setdefault(e["b"], []).append(e)
    for b, es in by_b.items():
        p, text = read_card(b)
        if not p:
            skipped += len(es)
            continue
        cur = rel_line(text)
        if not cur:
            continue
        if cur.count("；") + 1 >= MAX_REL:
            skipped += len(es)
            continue
        ins = []
        for e in es:
            a = e["a"]
            if a in cur or a in "".join(ins):
                continue
            _pa, ta = read_card(a)
            nm = name_of(ta, a)
            if not nm:
                continue
            label = "相识" if e["rel"] == "meet" else str(e.get("src") or "")
            label = re.split(r"[、,，/]", label)[0].strip()
            label = MIRROR.get(label, "街坊")
            ins.append("%s %s %s" % (label, a, nm))
        if not ins:
            continue
        new = cur.rstrip("。") + "；" + "；".join(ins) + "。"
        backup[b] = cur
        if not dry:
            txt2 = REL_LINE_RE.sub("**关系** " + new, text, count=1)
            if txt2 == text:
                skipped += len(ins)
                continue
            try:
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(txt2)
            except OSError:
                skipped += len(ins)
                continue
        touched[b] = new
        added += len(ins)
    if not dry and backup:
        try:
            os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
            with open(BACKUP, "w", encoding="utf-8") as fh:
                json.dump(backup, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return added, skipped, len(touched)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    edges = load_edges()
    if not edges:
        print("没有真关系边（citizen-relations.jsonl 缺失或只有 block）")
        return 1
    if a.fix:
        added, skipped, cards = fix(edges, dry=a.dry_run)
        print("补反向关系：新增 %d 条，涉及 %d 张卡（跳过 %d）%s"
              % (added, cards, skipped, "·dry-run" if a.dry_run else "·已写回"))
        edges = load_edges()
    st = audit(edges)
    if a.json:
        print(json.dumps(st, ensure_ascii=False))
        return 0
    print("真关系边 %d（唯一对 %d）· 双向率 %.1f%% · 节点 %d · 零关系 %d 人（%.1f%%）"
          % (st["real_edges"], st["pairs"], st["reciprocal_rate"] * 100,
             st["nodes"], st["isolated"], st["isolated_rate"] * 100))
    if st["reciprocal_rate"] < 0.80:
        print("判定：不达标（目标 ≥80%%）——居民各说各话，需要补反向关系")
    else:
        print("判定：达标")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
