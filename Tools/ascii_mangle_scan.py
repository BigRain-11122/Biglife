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
  python -X utf8 Tools/ascii_mangle_scan.py --update-baseline  # 把当前命中记为已知基线

基线抑制：某些历史写盘事故把中文整段替换成 '?'，原字节已丢失、不可逆，
重复报警只会淹没新缺陷。`--update-baseline` 把当下命中的「文件+行内容哈希」
记入 qa/ascii-mangle-baseline.json；此后同一行不再计入 FOUND，只报 suppressed。
判据变严不变松：新出现的编码损坏仍会立刻命中，退出码仍为 1。

退出码：0=干净（含已抑制），1=发现未被基线覆盖的候选行（需人工按证据修复，禁机械替换）。
"""
import argparse
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QMARK_RUN = re.compile(r"\?{2,}")
EXTS = (".md", ".json", ".jsonl", ".html", ".py", ".txt", ".csv")
SKIP_DIRS = {".git", "__pycache__", ".ruff_cache", ".codely-cli", "voice-cache"}
SKIP_TOP = {"state", "logs"}
BASELINE_PATH = os.path.join(ROOT, "qa", "ascii-mangle-baseline.json")


def _line_key(rel, line):
    h = hashlib.sha1(line.strip().encode("utf-8", "replace")).hexdigest()[:16]
    return rel.replace(os.sep, "/") + "\u241f" + h


def load_baseline():
    try:
        with open(BASELINE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("entries", []))
    except (OSError, ValueError):
        return set()


def save_baseline(entries):
    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    payload = {"note": "已知不可逆编码损坏（中文已被写成 '?'，原字节丢失）；新命中不在册即报警",
               "entries": sorted(entries)}
    with open(BASELINE_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


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
        hits.append((i, line.strip()))
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
    ap.add_argument("--update-baseline", action="store_true",
                    help="把当前全部命中记为已知基线（仅用于原字节已丢失的不可逆损坏）")
    args = ap.parse_args()

    base = os.path.join(ROOT, args.path) if args.path else ROOT
    if os.path.isfile(base):
        files = [base]
    else:
        files = list(walk(base, args.all))

    baseline = load_baseline()
    fresh = set()
    total = 0
    suppressed = 0
    for path in sorted(files):
        hits = scan_file(path)
        if not hits:
            continue
        rel = os.path.relpath(path, ROOT)
        kept = []
        for lineno, line in hits:
            key = _line_key(rel, line)
            fresh.add(key)
            if key in baseline and not args.update_baseline:
                suppressed += 1
                continue
            kept.append((lineno, line))
        if not kept:
            continue
        total += len(kept)
        print("HIT %s: %d 行" % (rel, len(kept)))
        for lineno, line in kept[:5]:
            print("   L%d %s" % (lineno, line[:100]))

    if args.update_baseline:
        save_baseline(fresh)
        print("baseline updated: %d entries -> %s" % (len(fresh), os.path.relpath(BASELINE_PATH, ROOT)))
        return 0

    print("scan files=%d hit_lines=%d suppressed=%d verdict=%s"
          % (len(files), total, suppressed, "CLEAN" if total == 0 else "FOUND"))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())