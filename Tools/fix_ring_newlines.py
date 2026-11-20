# -*- coding: utf-8 -*-
"""修「年轮段换行被吃掉」的卡：**年轮**- 2026-10-10 …- 2026-10-24 … 全挤成一行。

后果：所有按行匹配的逻辑（reconcile 覆盖率、add_ring 同日幂等、ring_score 取样）
都看不见这些环 → 覆盖率高估、补产写不进去、缺口永远不动。今天 106 人补不上就这原因。

修法：只在 **年轮** 与 **进化** 之间的片段里，把「）」或「」」后面紧跟的 "- 20"
断成新行。不碰其它段落，不改任何文字。

用法：python -X utf8 Tools/fix_ring_newlines.py [--dry-run]
回滚：state/ring-newline-backup.json（cid -> 原片段）
"""
import json
import os
import re
import sys

CO = r"C:\Users\sjs20\Desktop\FluxGroup\life\BigLife"
REG = os.path.join(CO, "census", "registry")
BACKUP = os.path.join(CO, "state", "ring-newline-backup.json")

SEC = re.compile(r"(\*\*\u5e74\u8f6e\*\*)(.*?)(\*\*\u8fdb\u5316\*\*)", re.S)
JOIN = re.compile(r"(\u300d|\uff09)\s*-\s*(20\d{2}-\d{2}-\d{2})")

dry = "--dry-run" in sys.argv
fixed = 0
backup = {}
for root, _, fs in os.walk(REG):
    for f in fs:
        if not (f.startswith("C-") and f.endswith(".md")):
            continue
        p = os.path.join(root, f)
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        m = SEC.search(t)
        if not m:
            continue
        body = m.group(2)
        # 标题后也要断开：**年轮**- 2026-10-10 这种「标题直接被首条年轮接上」的形态
        if body.lstrip().startswith("- "):
            body = "\n" + body.lstrip()
        new_body = JOIN.sub(lambda x: x.group(1) + "\n- " + x.group(2), body)
        if new_body == body:
            continue
        fixed += 1
        backup[f[:-3]] = body[:200]
        if dry:
            continue
        t2 = t[:m.start(2)] + new_body + t[m.end(2):]
        try:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(t2)
        except OSError:
            backup.pop(f[:-3], None)
if not dry and backup:
    try:
        with open(BACKUP, "w", encoding="utf-8") as fh:
            json.dump(backup, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass
print("修复 %d 张卡%s" % (fixed, "（dry-run）" if dry else "，回滚档 ring-newline-backup.json"))
