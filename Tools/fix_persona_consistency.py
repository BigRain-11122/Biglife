# -*- coding: utf-8 -*-
"""人设一致性修复：把跨字段矛盾（男穿旗袍 / 年轻人戴老花镜）就地改正。

Why（CEO 2026-11-18「务必把每个居民都生成一个活生生的真人感的硅基居民」）：
  实锚：10111 人已 100% 有年轮，但人设本身是批量生成时**字段独立采样、互不校验**——
  出现「35 岁男性穿靛蓝改良旗袍」「12 岁戴磁悬浮老花镜」这类硬矛盾。
  人设先崩了，年轮写得再好也不像活人。

修法（确定性、零 LLM、可回滚）：
  1. 男性 + 旗袍 → 按年龄换同性向服装
  2. <50 岁 + 老花镜 → 删掉该配饰（保留句子通顺）
  3. 其余一概不动

用法：
  python -X utf8 Tools/fix_persona_consistency.py --audit     # 矛盾全谱计数（只读）
  python -X utf8 Tools/fix_persona_consistency.py --check     # 只报不改
  python -X utf8 Tools/fix_persona_consistency.py --apply     # 就地修
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census", "registry")

AGE_RE = re.compile(r"\*\*性别·年龄\*\*\s*(\S+)\s*·\s*(\d+)\s*岁")
CLOTH_RE = re.compile(r"(\*\*服装\*\*\s*)(.+)")

FEM_WEAR = ("旗袍", "连衣裙", "半身裙", "吊带裙")
FEM_SHOE = ("高跟鞋",)
PRESBYOPIA = ("老花镜",)

# 男性替换：按年龄给不同质感，避免全城一个样
MALE_REPL = [
    (0, 29, ["靛蓝立领短褂", "深蓝工装夹克", "靛蓝对襟短衫"]),
    (30, 59, ["靛蓝对襟褂", "深蓝立领长衫", "靛蓝粗布对襟上衣"]),
    (60, 200, ["靛蓝立领长衫", "深灰对襟褂", "靛蓝粗布长衫"]),
]


def pick_male(age, seed):
    for lo, hi, pool in MALE_REPL:
        if lo <= age <= hi:
            return pool[seed % len(pool)]
    return "靛蓝对襟褂"


def fix_text(text, cid):
    """按「，」切句段后逐段判定，比正则跨段替换更稳。"""
    m_age = AGE_RE.search(text)
    m_cloth = CLOTH_RE.search(text)
    if not (m_age and m_cloth):
        return text, []
    gender, age = m_age.group(1), int(m_age.group(2))
    cloth = m_cloth.group(2).rstrip()
    tail = ""
    if cloth.endswith("。"):
        cloth, tail = cloth[:-1], "。"
    segs = [s for s in cloth.split("，")]
    seed = sum(ord(c) for c in cid)
    fixes = []
    out = []
    replaced_main = False
    for seg in segs:
        s = seg.strip()
        if not s:
            continue
        if gender.startswith("男") and not replaced_main and any(k in s for k in FEM_WEAR):
            repl = pick_male(age, seed)
            out.append(repl)
            replaced_main = True
            fixes.append("男穿女装→%s" % repl)
            continue
        if gender.startswith("男") and any(k in s for k in FEM_SHOE):
            out.append("黑布鞋")
            fixes.append("男穿高跟鞋→黑布鞋")
            continue
        if age < 40 and any(k in s for k in PRESBYOPIA):
            fixes.append("去老花镜")
            continue
        out.append(s)
    if not fixes:
        return text, []
    new_cloth = "，".join(out) + tail
    return text.replace(m_cloth.group(0), m_cloth.group(1) + new_cloth, 1), fixes


# 矛盾全谱（只读审计用）：名称 -> (性别条件, 关键词组, 年龄条件)
FEMININE_MARKS = ("旗袍", "连衣裙", "半身裙", "高跟鞋", "口红", "发簪", "耳坠", "珍珠项链")
MASC_MARKS = ("领带", "中山装")
FRAIL_MARKS = ("老花镜", "拐杖", "假牙", "助听器")
HARD_LABOR = ("搬运", "扛包", "下矿", "砌墙", "伐木", "码头工", "装卸")
AUDIT_PATTERNS = [
    ("男-女性服饰", "男", FEMININE_MARKS, None),
    ("女-男士领带", "女", MASC_MARKS, None),
    ("<16岁-衰老器具", None, FRAIL_MARKS, (0, 15)),
    ("<40岁-老花镜", None, ("老花镜",), (0, 39)),
    ("<16岁-重体力", None, HARD_LABOR, (0, 15)),
]

# 世界观泄漏：这些词属于现实金融/量化线，不该出现在硅基居民的经历里
LEAK_TERMS = ("回测", "策略", "年化", "收益率", "仓位", "持仓", "波段", "止损",
              "阿尔法", "因子", "K线", "复利", "净值", "对冲", "套利")


def audit(as_json=False):
    total = 0
    hits = {name: [] for name, _, _, _ in AUDIT_PATTERNS}
    leaks = {t: 0 for t in LEAK_TERMS}
    tic_citizens = 0
    tic_rings = 0
    rings_total = 0
    tic_recent_total = 0
    tic_recent_hit = 0
    for root, _, fs in os.walk(CENSUS):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            total += 1
            for t in LEAK_TERMS:
                if t in text:
                    leaks[t] += 1
            # 口头禅复读：同一人多条年轮里逐字复用同一句
            mt = TIC_RE.search(text)
            if mt:
                tic = mt.group(1)
                rings = RING_LINE_RE.findall(text)
                rings_total += len(rings)
                hit = sum(1 for _, body in rings if tic in body)
                tic_rings += hit
                if hit >= 2:
                    tic_citizens += 1
                # 近 7 天口径：历史复读改不回来，只能看新产出的趋势
                for d, body in rings:
                    try:
                        if (dt.date.today() - dt.date.fromisoformat(d)).days <= 7:
                            tic_recent_total += 1
                            if tic in body:
                                tic_recent_hit += 1
                    except ValueError:
                        pass
            m_age = AGE_RE.search(text)
            if not m_age:
                continue
            gender, age = m_age.group(1), int(m_age.group(2))
            m_cloth = CLOTH_RE.search(text)
            cloth = m_cloth.group(2) if m_cloth else ""
            for name, g, marks, rng in AUDIT_PATTERNS:
                if g and not gender.startswith(g):
                    continue
                if rng and not (rng[0] <= age <= rng[1]):
                    continue
                if any(k in cloth for k in marks):
                    hits[name].append(f[:-3])
    if as_json:
        import json as _j
        print(_j.dumps({
            "total": total,
            "cloth_contradictions": len(hits["男-女性服饰"]) + len(hits["<40岁-老花镜"])
                                   + len(hits["<16岁-衰老器具"]),
            "male_feminine": len(hits["男-女性服饰"]),
            "presbyopia_under40": len(hits["<40岁-老花镜"]),
            "frail_under16": len(hits["<16岁-衰老器具"]),
            "tic_rings": tic_rings,
            "tic_rings_total": rings_total,
            "tic_citizens_repeat2plus": tic_citizens,
            "tic_ratio": round(tic_rings / max(1, rings_total), 4),
            "tic_recent_rings": tic_recent_total,
            "tic_recent_ratio": round(tic_recent_hit / max(1, tic_recent_total), 4),
        }, ensure_ascii=False))
        return 0
    print("扫描 %d 份" % total)
    for name, _, _, _ in AUDIT_PATTERNS:
        ids = hits[name]
        print("  %-16s %5d 份 (%.2f%%)  例: %s" % (
            name, len(ids), 100.0 * len(ids) / max(1, total), " ".join(ids[:4])))
    print("世界观泄漏（含正文任意位置）：")
    for t, c in sorted(leaks.items(), key=lambda kv: -kv[1]):
        if c:
            print("  %-6s %5d 份 (%.2f%%)" % (t, c, 100.0 * c / max(1, total)))
    return 0


def leak_samples(per_term=4, width=42):
    """打印泄漏词的上下文片段，供人工定替换词。"""
    seen = {t: 0 for t in LEAK_TERMS}
    import io
    for root, _, fs in sorted(os.walk(CENSUS)):
        for f in sorted(fs):
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            for t in LEAK_TERMS:
                if t not in text or seen[t] >= per_term:
                    continue
                i = text.find(t)
                frag = text[max(0, i - width):i + width].replace("\n", " ")
                print("[%s] %s  …%s…" % (t, f[:-3], frag))
                seen[t] += 1
            if all(seen[t] >= per_term for t in LEAK_TERMS):
                return 0
    return 0


CLAUSE_RES = {
    "出身": re.compile(r"出身：(.+?)转折："),
    "转折": re.compile(r"转折：(.+?)现状："),
    "现状": re.compile(r"现状：(.+?)(?:\n|$)"),
    "思想": re.compile(r"\*\*思想\*\*\s*(.+?)(?:\n|$)"),
    "性格": re.compile(r"\*\*性格\*\*\s*(.+?)(?:\n|$)"),
    "语言": re.compile(r"\*\*语言\*\*\s*(.+?)(?:\n|$)"),
    "服装": re.compile(r"\*\*服装\*\*\s*(.+?)(?:\n|$)"),
    "行为": re.compile(r"\*\*行为\*\*\s*(.+?)(?:\n|$)"),
    "钩子": re.compile(r"\*\*钩子\*\*\s*(.+?)(?:\n|$)"),
}


def dup_report(topn=6):
    """统计五个叙事字段的逐字重复率——千篇一律的量化证据。"""
    from collections import Counter
    counts = {k: Counter() for k in CLAUSE_RES}
    total = 0
    for root, _, fs in os.walk(CENSUS):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            total += 1
            for k, rx in CLAUSE_RES.items():
                m = rx.search(text)
                if m:
                    counts[k][m.group(1).strip()] += 1
    print("扫描 %d 份" % total)
    for k in CLAUSE_RES:
        c = counts[k]
        tot = sum(c.values())
        uniq = len(c)
        top = c.most_common(topn)
        dup_share = 100.0 * (tot - uniq) / max(1, tot)
        print("\n[%s] 有值 %d 份 · 唯一 %d 条 · 重复占比 %.1f%%" % (k, tot, uniq, dup_share))
        for phrase, n in top:
            print("   x%-4d %s" % (n, phrase[:64]))
    return 0


TIC_RE = re.compile(r"口头禅「([^」]{4,40})」")
RING_LINE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「(.+?)」", re.M)


def tic_report():
    """口头禅复读率：同一人多条年轮里逐字复用口头禅 = 活人感杀手。"""
    files = 0
    with_tic = 0
    citizens_repeat = 0
    rings_total = 0
    rings_with_tic = 0
    worst = []
    for root, _, fs in os.walk(CENSUS):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            files += 1
            mt = TIC_RE.search(text)
            if not mt:
                continue
            with_tic += 1
            tic = mt.group(1)
            rings = RING_LINE_RE.findall(text)
            rings_total += len(rings)
            hit = sum(1 for _, body in rings if tic in body)
            rings_with_tic += hit
            if hit >= 2:
                citizens_repeat += 1
                worst.append((hit, len(rings), f[:-3]))
    worst.sort(reverse=True)
    print("扫描 %d 份 · 带口头禅 %d 份" % (files, with_tic))
    print("年轮 %d 条，其中逐字复读口头禅 %d 条（%.1f%%）" % (
        rings_total, rings_with_tic, 100.0 * rings_with_tic / max(1, rings_total)))
    print("复读≥2 次的居民 %d 人（占有人设 %d 的 %.1f%%）" % (
        citizens_repeat, with_tic, 100.0 * citizens_repeat / max(1, with_tic)))
    print("最严重的 8 位（复读圈数/总圈数）：")
    for hit, tot, cid in worst[:8]:
        print("   %s  %d/%d" % (cid, hit, tot))
    return 0


def hist_report():
    """年轮条数分布 + 最近一条距今多久——「活人」有没有在持续过日子。"""
    import datetime as dt
    from collections import Counter
    per = Counter()
    stale = Counter()
    today = dt.date.today()
    for root, _, fs in os.walk(CENSUS):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            rings = RING_LINE_RE.findall(text)
            per[len(rings)] += 1
            if rings:
                try:
                    last = dt.date.fromisoformat(max(d for d, _ in rings))
                    d = (today - last).days
                    stale["0-1天" if d <= 1 else "2-3天" if d <= 3 else
                          "4-7天" if d <= 7 else "8-14天" if d <= 14 else "15天以上"] += 1
                except ValueError:
                    stale["解析失败"] += 1
            else:
                stale["无年轮"] += 1
    print("年轮条数分布：")
    for n in sorted(per):
        print("   %2d 圈  %5d 人" % (n, per[n]))
    tot = sum(per.values())
    avg = sum(k * v for k, v in per.items()) / max(1, tot)
    print("   平均 %.2f 圈/人" % avg)
    print("最近一条年轮距今：")
    for k in ("0-1天", "2-3天", "4-7天", "8-14天", "15天以上", "无年轮", "解析失败"):
        if stale[k]:
            print("   %-6s %5d 人 (%.1f%%)" % (k, stale[k], 100.0 * stale[k] / max(1, tot)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--leak", action="store_true")
    ap.add_argument("--dup", action="store_true")
    ap.add_argument("--tic", action="store_true")
    ap.add_argument("--hist", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.audit:
        return audit(as_json=a.json)
    if a.leak:
        return leak_samples()
    if a.dup:
        return dup_report()
    if a.tic:
        return tic_report()
    if a.hist:
        return hist_report()
    apply = a.apply
    changed = 0
    total = 0
    samples = []
    backup = {}
    for root, _, fs in os.walk(CENSUS):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            p = os.path.join(root, f)
            cid = f[:-3]
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError:
                continue
            total += 1
            new_text, fixes = fix_text(text, cid)
            if fixes:
                changed += 1
                if len(samples) < 6:
                    mc = CLOTH_RE.search(text)
                    mn = CLOTH_RE.search(new_text)
                    samples.append((cid, "、".join(fixes),
                                    mc.group(2).strip() if mc else "",
                                    mn.group(2).strip() if mn else ""))
                if apply:
                    mc = CLOTH_RE.search(text)
                    if mc:
                        backup[cid] = mc.group(2).strip()
                    try:
                        with open(p, "w", encoding="utf-8", newline="") as fh:
                            fh.write(new_text)
                    except OSError as exc:
                        print("write fail %s: %s" % (cid, exc))
    if apply and backup:
        import json
        bp = os.path.join(CO, "state", "persona-fix-backup.json")
        os.makedirs(os.path.dirname(bp), exist_ok=True)
        with open(bp, "w", encoding="utf-8") as fh:
            json.dump(backup, fh, ensure_ascii=False, indent=1)
        print("回滚档 %d 条 → %s" % (len(backup), bp))
    print("扫描 %d 份，需修 %d 份（%.1f%%）%s" % (
        total, changed, 100.0 * changed / max(1, total), "·已写回" if apply else "·仅检查"))
    for cid, fx, before, after in samples:
        print("  %s  %s" % (cid, fx))
        print("      - %s" % before)
        print("      + %s" % after)


if __name__ == "__main__":
    sys.exit(main() or 0)
