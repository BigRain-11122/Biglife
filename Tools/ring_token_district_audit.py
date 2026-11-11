#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""存量年轮机器串·按城区抽样核验（T-20261112-01 口①②）。

口径：只读 census/registry/<城区>/*.md，扫年轮行里的遗留机器串
（复用 evolve_citizen.MACHINE_TOKEN_ALT 的两个形态：字母码如 BG-A、
ISO 时间戳如 2026-11-12T04:06:57+08:00），按城区统计「带机器串的卡数/总卡数」。
判据：某城区密度 >20% 才单独立批重生成；其余按月 spotlight 顺带统计余量即可。

输出：qa/RING-TOKEN-DISTRICT-<YYYYMMDD>.md + stdout 摘要。
"""
import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evolve_citizen import MACHINE_TOKEN_ALT  # noqa: E402

# MACHINE_TOKEN_ALT 是「拼接用的分支尾部」（以 | 开头、给别的 pattern 追加），
# 单独编译会让首个空分支命中一切；剥掉前导 | 才是真正的两种形态。
TOKEN_RE = re.compile(MACHINE_TOKEN_ALT.lstrip("|"))
PARTIAL_RE = re.compile(r"(?<![A-Za-z0-9-])[GBSPT]\d{1,4}(?:\.\d+)?(?![0-9])")
RING_LINE_RE = re.compile(r"^\s*[-*]\s*\[?\d{4}-\d{2}-\d{2}")

CO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan(district_dir):
    total = 0
    dirty = 0
    samples = []
    for name in sorted(os.listdir(district_dir)):
        if not name.lower().endswith(".md"):
            continue
        path = os.path.join(district_dir, name)
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.readlines()
        except (OSError, UnicodeDecodeError):
            continue
        total += 1
        hits = [(i + 1, ln.strip()) for i, ln in enumerate(lines)
                if RING_LINE_RE.match(ln) and (TOKEN_RE.search(ln) or PARTIAL_RE.search(ln))]
        if hits:
            dirty += 1
            if len(samples) < 3:
                ln_no, text = hits[0]
                samples.append((name, ln_no, text[:90]))
    return total, dirty, samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=20.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = os.path.join(CO, "census", "registry")
    if not os.path.isdir(root):
        print("registry missing: %s" % root)
        return 1

    rows = []
    gt = gd = 0
    for dist in sorted(os.listdir(root)):
        ddir = os.path.join(root, dist)
        if not os.path.isdir(ddir):
            continue
        total, dirty, samples = scan(ddir)
        if not total:
            continue
        gt += total
        gd += dirty
        rows.append((dist, total, dirty, 100.0 * dirty / total, samples))

    today = dt.date.today().strftime("%Y%m%d")
    out = args.out or os.path.join(CO, "qa", "RING-TOKEN-DISTRICT-%s.md" % today)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    over = [r for r in rows if r[3] > args.threshold]
    lines = []
    lines.append("# 存量年轮机器串·城区密度核验 %s\n" % today)
    lines.append("口径=T-20261112-01 口①②；检测=字母码形态 + ISO 时间戳形态 + 残留字母数字码。")
    lines.append("判据=城区密度 >%.0f%% 才单独立批重生成。\n" % args.threshold)
    lines.append("| 城区 | 卡数 | 带机器串卡 | 密度 |")
    lines.append("|---|---|---|---|")
    for dist, total, dirty, pct, _ in sorted(rows, key=lambda r: -r[3]):
        lines.append("| %s | %d | %d | %.1f%% |" % (dist, total, dirty, pct))
    lines.append("| **合计** | %d | %d | %.1f%% |" % (gt, gd, 100.0 * gd / gt if gt else 0.0))
    lines.append("")
    if over:
        lines.append("## 越过 20%% 阈值（需立批）\n")
        for dist, total, dirty, pct, samples in over:
            lines.append("- **%s** %.1f%%（%d/%d）" % (dist, pct, dirty, total))
            for name, ln_no, text in samples:
                lines.append("  - 例 `%s:%d` %s" % (name, ln_no, text))
    else:
        lines.append("## 结论\n")
        lines.append("无城区越过 %.0f%% 阈值 → 按 T-20261112-01 口径**不立批重生成**，"
                     "只累计余量（每月 spotlight 顺带统计）。新环出口已被门禁双面拒绝，存量只减不增。" % args.threshold)

    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")

    print("districts=%d cards=%d dirty=%d density=%.1f%% over_threshold=%d"
          % (len(rows), gt, gd, 100.0 * gd / gt if gt else 0.0, len(over)))
    for dist, total, dirty, pct, _ in sorted(rows, key=lambda r: -r[3])[:6]:
        print("  %-4s %4d cards %4d dirty %5.1f%%" % (dist, total, dirty, pct))
    print("report: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
