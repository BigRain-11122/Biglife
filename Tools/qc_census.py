#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qc_census.py - BigLife census invariant scanner (OS-loop QC rounds).

Read-only scan of existing cards: unique ids / unique names / required
sections / evolution ring sanity. Writes census/QC-REPORT.md. Never regenerates.
--schema adds the R3 export-face JSON Schema structural layer (T-20260926-17):
default path is byte-identical to the pre-flag scanner (assertion zero-drift).
"""
import glob, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")

REQUIRED = ["**物种**", "**性格**", "**信条**", "**思想**", "**语言**", "**服装**", "**经历**", "**行为**", "**关系**", "**钩子**", "**进化**", "**溯源**"]

# T-20260926-17: one schema definition (Tools/schemas/), reused here.
SCHEMA_FACES = [
    ("citizens-light", "citizens-light.schema.json"),
    ("citizen-needs", "citizen-needs.schema.json"),
    ("citizen-behavior", "citizen-behavior.schema.json"),
    ("citizen-tasks", "citizen-tasks.schema.json"),
]

def schema_scan(problems):
    """Validate the four R3 regen faces against Tools/schemas/*.schema.json."""
    import json
    try:
        import jsonschema
    except ImportError:
        problems.append("schema: jsonschema not installed (local dep missing)")
        return 0, 1, []
    rows = bad = 0
    per = []
    for face, sf in SCHEMA_FACES:
        data = os.path.join(CENSUS, "export", face + ".jsonl")
        spath = os.path.join(HERE, "schemas", sf)
        if not os.path.exists(data):
            problems.append(f"schema: missing face file {face}.jsonl")
            bad += 1
            per.append((face, 0, 1))
            continue
        with open(spath, encoding="utf-8") as f:
            validator = jsonschema.Draft202012Validator(json.load(f))
        face_rows = face_bad = 0
        with open(data, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                s = line.strip()
                if not s:
                    continue
                face_rows += 1
                rec = json.loads(s)
                errs = list(validator.iter_errors(rec))
                if errs:
                    face_bad += 1
                    if face_bad <= 20:
                        problems.append(f"schema {face} line {i}: {errs[0].message}")
        rows += face_rows
        bad += face_bad
        per.append((face, face_rows, face_bad))
    return rows, bad, per

def main():
    schema_mode = "--schema" in sys.argv[1:]
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
    schema_rows = schema_bad = 0
    if schema_mode:
        schema_rows, schema_bad, per = schema_scan(problems)
        report[-1:] = [f"- 异常数：{len(problems)}（卡面 {len(problems) - schema_bad} + 结构层 {schema_bad}）", "",
                       "## Schema 结构层（--schema·T-20260926-17）", "",
                       f"- 校验行数：{schema_rows}",
                       f"- 结构违例：{schema_bad}",
                       "- 逐面：" + " · ".join(f"{f} {r}/{b}" for f, r, b in per), ""]
    if problems:
        report += ["## 异常明细", ""] + [f"- {p}" for p in problems[:100]] + ["", f"（共 {len(problems)} 条，仅列前 100）"]
    else:
        report += ["## 结论", "", "全部不变量 PASS：编号唯一/姓名唯一/必备段齐备/年轮锚定律无违例。", ""]
    with open(os.path.join(CENSUS, "QC-REPORT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(report))
    tail = f" schema_rows={schema_rows} schema_bad={schema_bad}" if schema_mode else ""
    print(f"QC done cards={len(ids)} evolved={evolved} problems={len(problems)}{tail}")
    if problems:
        print("QC FAILED")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
