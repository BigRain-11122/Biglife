# -*- coding: utf-8 -*-
"""ASCII 顶替扫描（T-20261020-04 第三类损伤·R2392 立）。

背景：正文中文经「ascii 编码 + errors=replace」通道写出后，整段变成 '?'，
留下「??」「???」连段且整行零 CJK；tags 闸（U+FFFD / GBK 乱码字）都看不出来。
本工具把这条检测独立成可复用扫描面：任何轮/任何文件都能跑，不改任何数据。

判据（与 Tools/tasks_board.py 同源）：单行出现 >=2 段 '?' 连段，且该行不含 CJK 字符。
正常中文疑问句不会连写两个问号，因此误报面极窄。

用法：
  python -X utf8 Tools/ascii_mangle_scan.py                 # 扫默认面（仓内文本文件）
  python -X utf8 Tools/ascii_mangle_scan.py --path tasks    # 只扫某目录/文件
  python -X utf8 Tools/ascii_mangle_scan.py --all           # 含 state/logs（默认排除）

退出码：0=干净，1=发现候选行（需人工按证据修复，禁机械替换）。
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QMARK_RUN = re.compile(r"\?{2,}")
EXTS = (".md", ".json", ".jsonl", ".html", ".py", ".txt", ".csv")
SKIP_DIRS = {".git", "__pycache__", ".ruff_cache", ".codely-cli", "voice-cache"}
SKIP_TOP = {"state", "logs"}


def scan_file(path):
    try:
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if len(QMARK_RUN.findall(line)) < 2:
            continue
        if any("\u4e00" <= c <= "\u9fff" for c in line):
            continue
        hits.append((i, line.strip()[:100]))
    return hits


def walk(base, include_state):
    for dirpath, dirnames, filenames in os.walk(base):
        rel = os.path.relpath(dirpath, base)
        top = rel.split(os.sep)[0]
        if top in SKIP_TOP and not include_state:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(EXTS):
                yield os.path.join(dirpath, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    base = os.path.join(ROOT, args.path) if args.path else ROOT
    if os.path.isfile(base):
        files = [base]
    else:
        files = list(walk(base, args.all))

    total = 0
    for path in sorted(files):
        hits = scan_file(path)
        if not hits:
            continue
        total += len(hits)
        rel = os.path.relpath(path, ROOT)
        print("HIT %s: %d 行" % (rel, len(hits)))
        for lineno, sample in hits[:5]:
            print("   L%d %s" % (lineno, sample))
    print("scan files=%d hit_lines=%d verdict=%s" % (len(files), total, "CLEAN" if total == 0 else "FOUND"))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())