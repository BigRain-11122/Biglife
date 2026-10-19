"""同日年轮去重修复（R1772·2026-10-20）

出生地病根=evolve_citizen 被中途击杀后重跑，同一居民同日二次落环（cursor 状态
文件未入库，批次中断即丢水位）。本工具做存量清污：同一张卡同一日期若有多条
「年轮」行（相遇行除外——相遇与年轮同日并存属合法双事件），保留第一条，删除
其余，并重算 **进化** 行的圈数。

用法：
  python -X utf8 Tools/repair_dup_rings.py            # dry-run，只报不写
  python -X utf8 Tools/repair_dup_rings.py --apply    # 落盘
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "census", "registry")


def card_paths():
    for d, _, fs in os.walk(REG):
        for f in sorted(fs):
            if f.endswith(".md") and f.startswith("C-"):
                yield os.path.join(d, f)


def repair(text):
    """返回 (新文本, 删除行数)。"""
    lines = text.split("\n")
    seen = set()
    out = []
    removed = 0
    for l in lines:
        m = re.match(r"- (\d{4}-\d{2}-\d{2}) ", l)
        if m and "相遇：" not in l:
            key = m.group(1)
            if key in seen:
                removed += 1
                continue
            seen.add(key)
        out.append(l)
    if not removed:
        return text, 0
    text = "\n".join(out)
    count = len(re.findall(r"(?:^|\n)- \d{4}-\d{2}-\d{2} ", text))
    text = re.sub(r"\*\*进化\*\* .*",
                  f"**进化** v1.{count} · 出生 2026-09-23 · 年轮 {count} 圈 · 锚定律见 docs/CODEX.md §九",
                  text, count=1)
    return text, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    total_cards = 0
    total_lines = 0
    for p in card_paths():
        with io.open(p, encoding="utf-8") as f:
            text = f.read()
        new, removed = repair(text)
        if removed:
            total_cards += 1
            total_lines += removed
            rel = os.path.relpath(p, ROOT)
            print(f"{rel}: removed={removed}")
            if args.apply:
                with io.open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"{mode} cards={total_cards} lines_removed={total_lines}")
    return 0


if __name__ == "__main__":
    sys.exit(main())