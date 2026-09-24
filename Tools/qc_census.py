#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qc_census.py - BigLife census invariant scanner (OS-loop QC rounds).

Read-only scan of existing cards: unique ids / unique names / required
sections / evolution ring sanity. Writes census/QC-REPORT.md. Never regenerates.
"""
import glob, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")

REQUIRED = ["**物种**", "**性格**", "**信条**", "**思想**", "**语言**", "**服装**", "**经历**", "**行为**", "**关系**", "**钩子**", "**进化**", "**溯源**"]

def main():
    ids, names, problems = {}, {}, []
    files = []
    for sub in ("anchors", "registry"):
        files += glob.glob(os.path.join(CENSUS, sub, "**", "*.md"), recursive=True)
    files += glob.glob(os.path.join(CENSUS, "reserved", "C-*.md"))  # honored seat cards
    evolved = 0
    for p in sorted(files):
        fn = os.path.basename(p)[:-3]
        with open(p, encoding="utf-8") as f:
            text = f.read()
        if not fn.startswith("C-"):
            problems.append(f"{p}: bad id")
            continue
        if fn in ids:
            problems.append(f"{fn}: duplicate id")
        ids[fn] = p
        m = re.match(r"# (C-\d+) · (.+)", text)
        if not m:
            problems.append(f"{fn}: no title")
            continue
        name = m.group(2).strip()
        if name in names:
            problems.append(f"{name}: duplicate name (also {names[name]})")
        names[name] = fn
        for sec in REQUIRED:
            if sec not in text:
                problems.append(f"{fn}: missing section {sec}")
        if "**年轮**" in text:
            evolved += 1
            if "[锚]" not in text:
                problems.append(f"{fn}: ring without anchor")
    report = ["# QC 报告 —— 万人户籍不变量巡检", "",
              f"- 巡检时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
              f"- 卡片总数：{len(ids)}（在册 {len(names)} 名）",
              f"- 已进化（有年轮）：{evolved}",
              f"- 异常数：{len(problems)}", ""]
    if problems:
        report += ["## 异常明细", ""] + [f"- {p}" for p in problems[:100]] + ["", f"（共 {len(problems)} 条，仅列前 100）"]
    else:
        report += ["## 结论", "", "全部不变量 PASS：编号唯一/姓名唯一/必备段齐备/年轮锚定律无违例。", ""]
    with open(os.path.join(CENSUS, "QC-REPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report))
    print(f"QC done cards={len(ids)} evolved={evolved} problems={len(problems)}")
    if problems:
        print("QC FAILED")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
