# -*- coding: utf-8 -*-
"""tasks/TASKS.md 编码修复（T-20261020-02 / R1820 立单）。

机理（R1821 本轮回溯实测）：
  损坏形态=「三字节标记 `31 A4 37`（"1¤7"）+ 前一字尾字节被压成 0x84」。
  例：'）'=EF BC 89 -> EF BC 84 + 1¤7；'踪'=E8 B8 AA -> E8 B8 84 + 1¤7。
  即每个标记点=丢失 1 个 UTF-8 尾字节 -> 原字不可无上下文还原（全文件 15394 处）。
  另有尾部整段 GBK 混入（R1816 段）。

修复策略（不臆造）：
  1) 标记 `1\\xa47` -> U+FFFD（保留原字宽位与可读性，不猜字）；
  2) 逐行：utf-8 严格通过=原样；失败则 gbk 严格通过=换 UTF-8；再不行则 utf-8 替换；
  3) 全文件必须 utf-8 严格可解才落盘，落盘前备份到 state/。

用法：
    python -X utf8 Tools/repair_tasks_utf8.py --check
    python -X utf8 Tools/repair_tasks_utf8.py --apply
"""

import argparse
import os
import shutil
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "tasks", "TASKS.md")
MARK = b"1\xa47"
FFFD = "\ufffd"


def repair_line(raw):
    try:
        return raw.decode("utf-8"), "utf8"
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("gbk"), "gbk"
    except Exception:
        pass
    return raw.decode("utf-8", "replace"), "utf8-replace"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    data = open(TARGET, "rb").read()
    marks = data.count(MARK)
    data = data.replace(MARK, FFFD.encode("utf-8"))

    stats = {}
    out = []
    for raw in data.split(b"\n"):
        text, tag = repair_line(raw)
        stats[tag] = stats.get(tag, 0) + 1
        out.append(text)

    text = "\n".join(out)
    blob = text.encode("utf-8")
    blob.decode("utf-8")  # 复验：必须严格可解

    print("marks_repaired=%d  lines=%d  %s" % (marks, len(out), stats))
    print("utf8_strict_after=OK  U+FFFD=%d  bytes=%d->%d"
          % (text.count(FFFD), len(open(TARGET, "rb").read()), len(blob)))

    if not args.apply:
        return

    state = os.path.join(ROOT, "state")
    os.makedirs(state, exist_ok=True)
    bak = os.path.join(state, "TASKS.bak-%s.md" % time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(TARGET, bak)
    with open(TARGET, "wb") as f:
        f.write(blob)
    print("backup=%s\nwritten=%s" % (bak, TARGET))


if __name__ == "__main__":
    main()