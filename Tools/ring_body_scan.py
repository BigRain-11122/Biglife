# -*- coding: utf-8 -*-
"""年轮正文中后段骨架扫描（只读·确定性·零 LLM·零 GPU）。

补 ring_open_family 的留白：开头族（首 12 字）与第二句已各有硬闸/软引导，
第 3 句起（含末句）从未度量。本工具给三面读数：

  1. sent_dup   同日跨卡「归一化后逐字相同」的重复句占比 + Top 例题
  2. mid_family 第 3 句起 句首 6 字骨架的 Top 集中度
  3. tail_family 末句 句首 6 字骨架的 Top 集中度
  4. dup（--dup）同日跨卡「共用 8 字片段」的环占比——逐字相同之外的近似重复面，
     并**剔除口头禅驱动的合法复用**（承 R2568/R2580 判例：禁词不误伤人设）

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
DUP_N = 8           # 跨卡近似重复取 8 字片段
DUP_MIN_RINGS = 3   # 同一片段至少被 3 个不同环共用才算重复（2 个可能是巧合）
HEAVY_RATIO = 0.30  # 共用片段占本环片段 >=30% 判「模板化重度」（单处共用不算）
LANG_RE = re.compile(r"^\*\*语言\*\*(.+)$", re.M)
QUOTE_RE = re.compile(r"「([^」]{2,24})」")
_PUNCT = "。！？；…，、,.“”\"'‘’（）()《》 \t"


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


def load_catchphrases(registry=None):
    """全库取居民口头禅（**语言** 行的「…」引号段）→ set[str]。

    用途=在近似重复度量里剔除「人设驱动的合法复用」，避免把 135 卡共用
    口头禅判成模板照抄（R2568/R2580 判例）。
    """
    root = registry or REGISTRY
    out = set()
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            m = LANG_RE.search(s)
            if not m:
                continue
            for q in QUOTE_RE.finditer(m.group(1)):
                out.add(re.sub(r"\s+", "", q.group(1)))
    return out


def dup_analyze(bodies, catchphrases, n=DUP_N, min_rings=DUP_MIN_RINGS):
    """同日跨卡近似重复面（剔口头禅）→ dict。

    口径：把每环切成 n 字滑窗集合；某片段被 >= min_rings 个不同环共用即算重复；
    若该片段整体落在任一居民口头禅内（或被口头禅完整覆盖），不计——那是人设复用。
    """
    gram_rings = collections.defaultdict(set)
    per_ring = []
    for i, body in enumerate(bodies):
        grams = {body[j:j + n] for j in range(max(0, len(body) - n + 1))}
        per_ring.append(grams)
        for g in grams:
            gram_rings[g].add(i)

    catch = [c for c in (catchphrases or ()) if c]
    excluded = 0
    shared = {}
    for g, rings in gram_rings.items():
        if len(rings) < min_rings:
            continue
        # 剥两端标点后再判：跨口头禅边界的片段（「。这城里好玩的东」）也须被认领，
        # 否则合法人设复用会被记成模板照抄（selftest dup-catch-excluded 探针）。
        core = g.strip(_PUNCT)
        if any(core in c or c in core for c in catch):
            excluded += 1
            continue
        shared[g] = rings

    hit = sum(1 for grams in per_ring if grams & shared.keys())
    # 严重度分档：单独一处共用不等于整篇模板化，故再算「共用片段占本环片段比」，
    # 只有占比 >= HEAVY_RATIO 的环才算模板化重度（避免任一巧合片段把整环判重）。
    ratios = [(len(grams & shared.keys()) / len(grams)) if grams else 0.0
              for grams in per_ring]
    heavy = sum(1 for x in ratios if x >= HEAVY_RATIO)
    return {
        "rings": len(bodies),
        "dup_rings": hit,
        "dup_rings_pct": round(100.0 * hit / len(bodies), 1) if bodies else 0.0,
        "heavy_rings": heavy,
        "heavy_rings_pct": round(100.0 * heavy / len(bodies), 1) if bodies else 0.0,
        "grams_total": sum(len(g) for g in per_ring),
        "grams_shared": sum(len(g & shared.keys()) for g in per_ring),
        "dup_groups": len(shared),
        "excluded_catchphrase": excluded,
        "top_dups": [[g, len(r)] for g, r in
                     sorted(shared.items(), key=lambda kv: -len(kv[1]))[:8]],
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

    # 6) 近似重复：模型自创片段被 3 环共用 → 全环命中
    invented = ["开头各不同%d%d%d。风把檐下的灯笼摇个不停，人挤人。" % (i, i, i) for i in range(3)]
    d1 = dup_analyze(invented, set())
    chk("dup-invented", d1["dup_rings_pct"] == 100.0 and d1["dup_groups"] > 0,
        json.dumps(d1, ensure_ascii=False)[:200])

    # 7) 口头禅驱动的合法复用 → 剔除，不判重复
    catch = {"这城里好玩的东西一天比一天多"}
    legit = ["甲%d%d%d。这城里好玩的东西一天比一天多。" % (i, i, i) for i in range(3)]
    d2 = dup_analyze(legit, catch)
    chk("dup-catch-excluded", d2["dup_rings_pct"] == 0.0 and d2["excluded_catchphrase"] > 0,
        json.dumps(d2, ensure_ascii=False)[:200])

    # 8) 只有 2 环共用 → 低于门槛不计（防巧合误判）
    d3 = dup_analyze(["甲甲甲甲甲。风把门帘整个掀起来。", "乙乙乙乙乙。风把门帘整个掀起来。"], set())
    chk("dup-threshold", d3["dup_rings_pct"] == 0.0, json.dumps(d3, ensure_ascii=False)[:200])

    # 9) 口头禅抽取：**语言** 行引号段被读出，其它行不误抓
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "C-9.md"), "w", encoding="utf-8") as f:
            f.write("# C-9\n\n**语言** 「灵光」的底色，口头禅「一句话的事」，别的不算。\n\n"
                    "**钩子** 「这不是口头禅」\n")
        got = load_catchphrases(td)
    chk("catch-extract", got == {"灵光", "一句话的事"}, repr(got))

    for f in fails:
        print("FAIL", f)
    print("selftest: %d probes, %d fail" % (9, len(fails)))
    return 0 if not fails else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--day")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json")
    ap.add_argument("--dup", action="store_true", help="加测跨卡 8 字近似重复面（剔口头禅）")
    ap.add_argument("--min-rings", type=int, default=DUP_MIN_RINGS,
                    help="片段至少被 N 个不同环共用才算重复（默认 3）")
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
    catch = load_catchphrases() if args.dup else set()
    for d in days:
        bodies = by_day.get(d, [])
        if not bodies:
            continue
        r = analyze_day(bodies)
        r["day"] = d
        if args.dup:
            dd = dup_analyze(bodies, catch, min_rings=args.min_rings)
            r.update({"dup_" + k: v for k, v in dd.items() if k != "rings"})
        rows.append(r)
        print("[%s] rings=%d sent=%d dup=%d(%.1f%%, %d kinds) mid_top=%s %.1f%% | tail_top=%s %.1f%%"
              % (d, r["rings"], r["sent_total"], r["sent_dup_tokens"], r["sent_dup_pct"],
                 r["dup_sent_kinds"], r["mid_top"], r["mid_top_pct"], r["tail_top"], r["tail_top_pct"]))
        if args.dup:
            print("      近似重复: %d/%d 环=%.1f%% | 模板化重度=%.1f%% | 片段组=%d | 口头禅剔除=%d | top=%s"
                  % (r["dup_dup_rings"], r["rings"], r["dup_dup_rings_pct"], r["dup_heavy_rings_pct"],
                     r["dup_dup_groups"], r["dup_excluded_catchphrase"],
                     "；".join("%s×%d" % (g, n) for g, n in r["dup_top_dups"][:3])))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print("json ->", args.json)
    print("days=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
