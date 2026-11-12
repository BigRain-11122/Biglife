#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""相遇对称性全库扫描（T-20261027-01 数据面收口腿）。

T-20261027-01 的写面修复已在 evolve_citizen.py 落地（前置过滤 _meet_ring_today
+ 双向断言 _meet_pair_check + 失败回滚）。本工具补的是历史面：写面修复只能拦住
新场次，已经落盘的旧卡里 A 记「与 B 相遇」而 B 当日对的是 C 的不对称仍然存在，
且没有任何读数面能看见。

判据（三条，全部只读卡面文本，零 LLM）：
  1. 单边缺失 —— A 卡某日记「与 B 相遇」，B 卡同日无指向 A 的相遇行
  2. 对方缺卡 —— A 卡记的 partner 在 census 中不存在
  3. 同日多配 —— 同一张卡同一天出现 ≥2 条相遇行（add_ring 规则本不该发生）

分档（闸落地日 GATE_DATE=2026-10-27，commit eb6bd2f27）：
  - 历史遗留：日期 <= GATE_DATE 的不对称一律只报不改——旧卡台词是已发布内容，
    改写等于篡改历史；留档即可。
  - 新增回归：日期 > GATE_DATE 的不对称说明写面闸失效，判 FAIL。
  判定只看回归面，历史面计入报告表供对账。

输出：qa/MEET-SYMMETRY-REPORT.md（可入 qa/ 作为 T-20261027-01 证据），
控制台一行摘要。退出码 0=无回归，1=存在新增回归（供轮内闸消费）。

用法：
  python -X utf8 Tools/meet_asymmetry_scan.py            # 扫描并写报告
  python -X utf8 Tools/meet_asymmetry_scan.py --check    # 只打印摘要，不写盘
"""
import argparse
import collections
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")
CARD_DIRS = ("registry", "anchors", "reserved")
REPORT = os.path.join(CO, "qa", "MEET-SYMMETRY-REPORT.md")

CID_RE = re.compile(r"^C-\d+$")
# 写面闸落地日（commit eb6bd2f27·2026-10-27 相遇闸）。此日及以前的不对称=历史遗留。
GATE_DATE = "2026-10-27"
# 「- 2026-10-14 「与 C-00065 相遇：...」」——日期 + 与 + partner
MEET_RE = re.compile(
    r"^-\s+(\d{4}-\d{2}-\d{2})\s+[「『]?\s*与\s+(C-\d+)\s*相遇[:：]"
)


def iter_cards():
    for sub in CARD_DIRS:
        d = os.path.join(CENSUS, sub)
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if fn.endswith(".md") and CID_RE.match(fn[:-3]):
                    yield fn[:-3], os.path.join(root, fn)


def read_meets(path):
    """卡面全部相遇行 -> [(date, partner)]"""
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = MEET_RE.match(line)
                if m:
                    out.append((m.group(1), m.group(2)))
    except Exception:
        return out
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只打印摘要，不写报告")
    args = ap.parse_args()

    meets = {}
    for cid, path in iter_cards():
        rows = read_meets(path)
        if rows:
            meets[cid] = rows

    missing_partner = []
    one_sided = []
    multi = []

    for cid, rows in sorted(meets.items()):
        by_date = collections.defaultdict(list)
        for d, partner in rows:
            by_date[d].append(partner)
        for d, partners in sorted(by_date.items()):
            if len(partners) > 1:
                multi.append((cid, d, partners))
            for partner in partners:
                if partner not in meets:
                    missing_partner.append((cid, d, partner))
                    continue
                back = [p for (dd, p) in meets[partner] if dd == d]
                if cid not in back:
                    one_sided.append((cid, d, partner, back))

    total_rings = sum(len(v) for v in meets.values())

    def split(rows):
        reg = [r for r in rows if r[1] > GATE_DATE]
        return rows, reg

    one_all, one_reg = split(one_sided)
    miss_all, miss_reg = split(missing_partner)
    multi_all, multi_reg = split(multi)
    bad = len(one_reg) + len(miss_reg) + len(multi_reg)
    verdict = "PASS" if bad == 0 else "FAIL"

    lines = [
        "# 相遇对称性扫描报告（T-20261027-01 数据面）",
        "",
        "- 生成时间：%s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "- 扫描范围：census/{registry,anchors,reserved} 全卡面",
        "- 有相遇行的居民：%d 位 / 相遇行合计 %d 条" % (len(meets), total_rings),
        "- 判据：单边缺失 / 对方缺卡 / 同日多配；分档线=%s（写面闸落地日）" % GATE_DATE,
        "- 判定规则：分档线之前=历史遗留（只报不改）·之后=新增回归（判负）",
        "",
        "## 判定：%s（新增回归 %d 条）" % (verdict, bad),
        "",
        "| 类别 | 合计 | 其中历史遗留 | 其中新增回归 |",
        "| --- | --- | --- | --- |",
        "| 单边缺失（B 卡同日未回指 A） | %d | %d | %d |"
        % (len(one_all), len(one_all) - len(one_reg), len(one_reg)),
        "| 对方缺卡（partner 不在 census） | %d | %d | %d |"
        % (len(miss_all), len(miss_all) - len(miss_reg), len(miss_reg)),
        "| 同日多配（同卡同日 ≥2 相遇） | %d | %d | %d |"
        % (len(multi_all), len(multi_all) - len(multi_reg), len(multi_reg)),
        "",
    ]

    if one_sided:
        lines += ["## 单边缺失明细", "", "| 居民 | 日期 | 档 | 记的对方 | 对方当日实际指向 |",
                  "| --- | --- | --- | --- | --- |"]
        for cid, d, partner, back in one_sided[:200]:
            lines.append("| %s | %s | %s | %s | %s |"
                         % (cid, d, "回归" if d > GATE_DATE else "历史",
                            partner, ", ".join(back) or "（无）"))
        if len(one_sided) > 200:
            lines.append("| … | 其余 %d 条省略 | | | |" % (len(one_sided) - 200))
        lines.append("")

    if missing_partner:
        lines += ["## 对方缺卡明细", "", "| 居民 | 日期 | 缺卡 partner |",
                  "| --- | --- | --- |"]
        for cid, d, partner in missing_partner[:100]:
            lines.append("| %s | %s | %s |" % (cid, d, partner))
        lines.append("")

    if multi:
        lines += ["## 同日多配明细", "", "| 居民 | 日期 | 档 | 当日全部对象 |",
                  "| --- | --- | --- | --- |"]
        for cid, d, partners in multi[:100]:
            lines.append("| %s | %s | %s | %s |"
                         % (cid, d, "回归" if d > GATE_DATE else "历史",
                            ", ".join(partners)))
        lines.append("")

    if bad == 0:
        lines += ["分档线之后无新增回归：写面闸（evolve_citizen.py T-20261027-01）"
                  "自落地以来未再产生不对称。上表历史遗留项按「已发布内容不改写」"
                  "留档，不构成产线缺陷。", ""]

    report = "\n".join(lines)

    print("meet-asymmetry: rings=%d citizens=%d one_sided=%d missing=%d multi=%d "
          "regressions=%d -> %s"
          % (total_rings, len(meets), len(one_all), len(miss_all),
             len(multi_all), bad, verdict))

    if not args.check:
        os.makedirs(os.path.dirname(REPORT), exist_ok=True)
        with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
            f.write(report)

    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
