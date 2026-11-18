# -*- coding: utf-8 -*-
"""列出当前 due 的居民 id（供并发分段用）。

Why：`evolve --batch N` 自己选人，两个并发进程会选到同一批 id 互相踩。
并发方案 = 先取全量 due，再切段，各进程 `--force <段>`，靠 `--lock-name` 隔离。

用法：
  python -X utf8 Tools/due_list.py --limit 60
  python -X utf8 Tools/due_list.py --limit 60 --chunks 3   # 输出 3 段，每段一行
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import evolve_citizen as ec  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--chunks", type=int, default=0)
    a = ap.parse_args()
    cursor = ec.load_cursor()
    due = ec.due_citizens(cursor, a.limit)
    if not a.chunks or a.chunks <= 1:
        print(" ".join(due))
        return 0
    n = len(due)
    size = max(1, (n + a.chunks - 1) // a.chunks)
    for i in range(a.chunks):
        seg = due[i * size:(i + 1) * size]
        print(" ".join(seg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
