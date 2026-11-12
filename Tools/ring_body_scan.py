# -*- coding: utf-8 -*-
"""年轮正文中后段骨架扫描（只读·确定性·零 LLM·零 GPU）。

补 ring_open_family 的留白：开头族（首 12 字）与第二句已各有硬闸/软引导，
第 3 句起（含末句）从未度量。本工具给三面读数：

  1. sent_dup   同日跨卡「归一化后逐字相同」的重复句占比 + Top 例题
  2. mid_family 第 3 句起 句首 6 字骨架的 Top 集中度
  3. tail_family 末句 句首 6 字骨架的 Top 集中度

只读：不写 registry、不改任何卡、不参与拒稿判定（判负条件须另行立法）。
用法：
    python -X utf8 Tools/ring_body_scan.py --days 7
    python -X utf8 Tools/ring_body_scan.py --day 2026-11-12
    python -X utf8 Tools/ring_body_scan.py --selftest
"""
import argparse
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ring_open_family import REGISTRY, production_days  # noqa: E402

RING_RE = re.compile(r"- (2026-\d\d-\d\d) 「([^」]{8,})」")
SENT_SPLIT = re.compile(r"[。！？；…]+")
MU_LEN = 6          # 骨架取句首 6 字（开头族用 12 字，中后段句短，故收窄）
MIN_SENT = 6        # 过短句（「她说好」类）不计入骨架统计


def sentences(body):
    """正文 → 归一化句子列表（去空白、按标点切、滤过短句）。"""
    out = []
    for raw in SENT_SPLIT.split(re.sub(r"\s+", "", body or "")):
        if len(raw) >= MIN_SENT:
            out.append(raw)
    return out


def mu(sent):
    return sent[:MU_LEN]


def scan_registry(registry=None):
    """单趟遍历 registry → {day: [body, ...]}（比逐日重扫省 N-1 趟）。"""
    root = registry or REGISTRY
    by_day = collections.defaultdict(list)
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            for m in RING_RE.finditer(s):
                body = re.sub(r"\s+", "", m.group(2))
                if len(body) >= 8:
                    by_day[m.group(1)].append(body)
    return dict(by_day)


def top_share(counter, total):
    if not total:
        return None, 0
    name, n = counter.most_common(1)[0]
    return name, round(100.0 * n / total, 1)


def analyze_day(bodies):
    """单日读数 → dict。"""
    mid = collections.Counter()
    tail = collections.Counter()
    mid_total = tail_total = 0
    sent_counter = collections.Counter()
    sent_total = 0

    for body in bodies:
        sents = sentences(body)
        if not sents:
            continue
        for s in sents:
            sent_counter[s] += 1
            sent_total += 1
        for s in sents[2:]:                 # 第 3 句起
            mid[mu(s)] += 1
            mid_total += 1
        tail[mu(sents[-1])] += 1            # 末句
        tail_total += 1

    dup_sents = {s: n for s, n in sent_counter.items() if n >= 2}
    dup_tokens = sum(dup_sents.values())
    mid_name, mid_pct = top_share(mid, mid_total)
    tail_name, tail_pct = top_share(tail, tail_total)
    return {
        "rings": len(bodies),
        "sent_total": sent_total,
        "sent_dup_tokens": dup_tokens,
        "sent_dup_pct": round(100.0 * dup_tokens / sent_total, 1) if sent_total else 0.0,
        "dup_sent_kinds": len(dup_sents),
        "dup_top": [[s[:28], n] for s, n in sent_counter.most_common(5) if n >= 2],
        "mid_top": mid_name,
        "mid_top_pct": mid_pct,
        "mid_top3": [[k, v] for k, v in mid.most_common(3)],
        "mid_total": mid_total,
        "tail_top": tail_name,
        "tail_top_pct": tail_pct,
        "tail_top3": [[k, v] for k, v in tail.most_common(3)],
        "tail_total": tail_total,
    }


def _selftest():
    """纯函数负控：重复句必被计、正常异句不误伤、位置分桶不越界。"""
    fails = []

    def chk(name, cond, detail=""):
        if not cond:
            fails.append("%s %s" % (name, detail))

    # 1) 句切与过滤（<6 字的「她说好」「后来呢」按设计被滤掉）
    b = "手在门框上停了一下。风把门帘掀起来！她说好。后来呢"
    s = sentences(b)
    chk("split", s == ["手在门框上停了一下", "风把门帘掀起来"], repr(s))

    # 2) 跨卡完全重复必被计（今日 3 卡同句）
    bodies = ["甲甲甲甲甲甲。乙乙乙乙乙乙。丙丙丙丙丙丙。风把门帘整个掀起来。尾尾尾尾尾尾"] * 3
    r = analyze_day(bodies)
    chk("dup-detected", r["sent_dup_tokens"] == 15, json.dumps(r, ensure_ascii=False)[:200])
    chk("dup-pct", r["sent_dup_pct"] == 100.0, str(r["sent_dup_pct"]))

    # 3) 全异句 → 零重复（反例不误伤）
    uniq = ["。".join("%s%d%s" % (c, i, "很长的句子内容") for c in "甲乙丙丁尾") for i in range(6)]
    r2 = analyze_day(uniq)
    chk("no-false-dup", r2["sent_dup_tokens"] == 0, str(r2["sent_dup_tokens"]))

    # 4) 中段族只取第 3 句起：开头同句不算 mid，也不算 tail
    same_open = ["同一个开头的句子内容。乙乙乙乙乙乙。丙%d%d%d%d%d%d。尾%d%d%d%d%d%d" % (i, i, i, i, i, i, i, i, i, i, i, i)
                 for i in range(4)]
    r3 = analyze_day(same_open)
    chk("mid-excludes-open", r3["mid_top"] is not None and not r3["mid_top"].startswith("同一个"), str(r3["mid_top"]))
    chk("tail-is-last", r3["tail_top"].startswith("尾"), str(r3["tail_top"]))

    # 5) 空输入不崩
    r4 = analyze_day([])
    chk("empty", r4["rings"] == 0 and r4["sent_dup_pct"] == 0.0, str(r4))

    for f in fails:
        print("FAIL", f)
    print("selftest: %d probes, %d fail" % (5, len(fails)))
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--day")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    by_day = scan_registry()
    if args.day:
        days = [args.day]
    else:
        days = production_days(limit=args.days)
        if not days:
            days = sorted(by_day)[-args.days:]

    rows = []
    for d in days:
        bodies = by_day.get(d, [])
        if not bodies:
            continue
        r = analyze_day(bodies)
        r["day"] = d
        rows.append(r)
        print("[%s] rings=%d sent=%d dup=%d(%.1f%%, %d kinds) mid_top=%s %.1f%% | tail_top=%s %.1f%%"
              % (d, r["rings"], r["sent_total"], r["sent_dup_tokens"], r["sent_dup_pct"],
                 r["dup_sent_kinds"], r["mid_top"], r["mid_top_pct"], r["tail_top"], r["tail_top_pct"]))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    print("days=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
