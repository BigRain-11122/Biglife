# -*- coding: utf-8 -*-
"""年轮内部码巡检（零 LLM·确定性）——出生站闸的证据面。

背景（2026-10-26 R2251）：居民年轮里混进开发循环的内部编号（G08 / S2.5 /
B2396）。提示词 v0.64 已禁照抄但仍漏（10-24 16.0%、10-25 23.6%、10-26 21.0%
的当日年轮带码），根因是锚定律要求逐字引用喂入事件、而喂入事件本身带码。
修法=喂入面清洗 + 门内 regen 拒收 + 落环口兜底拒写（Tools/evolve_citizen.py）。
本工具负责计量与回归看守：每日跑一次，把带码年轮按日按人列出。

用法：
  python -X utf8 Tools/ring_lint.py                # 全库扫描，写报告
  python -X utf8 Tools/ring_lint.py --since 2026-10-24
  python -X utf8 Tools/ring_lint.py --today-only   # 只看今天（退出码=切点后带码数>0）
  python -X utf8 Tools/ring_lint.py --fix-cut 2026-10-27T09:00   # 换新切点
产物：
  qa/RING-LINT-REPORT.md   人读报告（按日汇总 + 切点对照 + 样本 + 涉及居民清单）
  qa/ring-lint.jsonl       机器清单（date/card/name/codes/text/mtime/phase）
退出码：
  0 = 切点后零带码（存量不计）；1 = 切点后仍有新产带码
口径（2026-10-26 R2260）：出生站修复落在 18:57，同日内修前/修后混杂，
日级切点分不开——故带码行按**卡片文件 mtime** 划 pre/post 两段。
存量带码不回归（锚定律保全原文），只计量；只有 post 段带码才判回归失败。
"""
from __future__ import annotations

import argparse
import datetime
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "qa", "RING-LINT-REPORT.md")
MACHINE = os.path.join(ROOT, "qa", "ring-lint.jsonl")

RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) [ \t]*(.+)$", re.M)
HEAD_RE = re.compile(r"^#\s*(C-\d+)\s*·\s*(.+)$")
# 与 Tools/evolve_citizen.py EVENT_CODE_RE 同源（带横杠的居民 ID 合法，故不含横杠）
CODE_RE = re.compile(r"(?<![A-Za-z0-9-])[GBSPT]\d{1,4}(?:\.\d+)?(?![0-9])")
# 出生站修复切点（commit 06cbdf461 2026-10-26 18:57 三面收口：喂入清码/门内拒收/落环兜底）
DEFAULT_FIX_CUT = "2026-10-26T18:57"


def card_mtime(path: str) -> str:
    """卡片文件最后写入时刻（本地时间，分钟精度）——年轮落环即写卡，用作代用时间戳。"""
    try:
        ts = os.path.getmtime(path)
    except OSError:
        return ""
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%dT%H:%M")


def parse(path: str) -> tuple[str, str, list[tuple[str, str]]]:
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    head = text.splitlines()[0] if text else ""
    m = HEAD_RE.match(head)
    cid, name = (m.group(1), m.group(2).strip()) if m else ("", head.strip())
    rings: list[tuple[str, str]] = []
    if "**年轮**" in text:
        block = text.split("**年轮**", 1)[1].split("**进化**", 1)[0]
        rings = [(d, b) for d, b in RING_RE.findall(block)]
    return cid, name, rings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--today-only", action="store_true")
    ap.add_argument("--fix-cut", default=DEFAULT_FIX_CUT,
                    help="出生站修复切点（本地时间 ISO，如 2026-10-26T18:57）")
    args = ap.parse_args()
    fix_cut = args.fix_cut.replace(" ", "T")[:16]
    today = datetime.date.today().isoformat()
    floor = today if args.today_only else args.since

    per_day: dict[str, list[int]] = {}
    rows: list[dict] = []
    for path in sorted(glob.glob(os.path.join(ROOT, "census", "registry", "**", "*.md"),
                                recursive=True)):
        cid, name, rings = parse(path)
        mtime = card_mtime(path)
        for date, body in rings:
            if date < floor:
                continue
            bucket = per_day.setdefault(date, [0, 0])
            bucket[0] += 1
            codes = sorted(set(CODE_RE.findall(body)))
            if not codes:
                continue
            bucket[1] += 1
            rows.append({
                "date": date,
                "card": os.path.relpath(path, ROOT).replace("\\", "/"),
                "id": cid,
                "name": name,
                "codes": codes,
                "text": body[:160],
                "mtime": mtime,
                "phase": "pre" if (mtime and mtime < fix_cut) else "post",
            })

    total = sum(v[0] for v in per_day.values())
    bad = sum(v[1] for v in per_day.values())
    rate = (100.0 * bad / total) if total else 0.0
    pre_rows = [r for r in rows if r["phase"] == "pre"]
    post_rows = [r for r in rows if r["phase"] == "post"]
    verdict = "PASS" if not post_rows else "FAIL"

    os.makedirs(os.path.join(ROOT, "qa"), exist_ok=True)
    with io.open(MACHINE, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# 年轮内部码巡检报告",
        "",
        "扫描面：`census/registry/**/*.md` 的年轮段（日期 ≥ %s）· 生成 %s" % (floor, today),
        "",
        "判据：年轮正文出现内部编号（字母+数字组合码，如 G08 / S2.5 / B2396）即计一条。",
        "居民 ID（C-07743 / H-QT2232）带横杠，不在判据内。",
        "",
        "## 按日汇总",
        "",
        "| 日期 | 年轮数 | 带码数 | 带码率 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for date in sorted(per_day):
        t, b = per_day[date]
        lines.append("| %s | %d | %d | %.1f%% |" % (date, t, b, 100.0 * b / t if t else 0.0))
    lines += [
        "| **合计** | **%d** | **%d** | **%.1f%%** |" % (total, bad, rate),
        "",
        "## 修复切点对照",
        "",
        "切点=%s（出生站三面收口 commit 06cbdf461）· 划段依据=卡片文件 mtime" % fix_cut,
        "",
        "| 阶段 | 带码年轮 | 口径 |",
        "| --- | ---: | --- |",
        "| 修前存量 | %d | 锚定律保全原文，不回改；只作历史计量 |" % len(pre_rows),
        "| 修后新产 | %d | 回归指标；>0 即修复失效 |" % len(post_rows),
        "",
        "判定：**%s**" % verdict,
        "",
        "## 涉及居民（最多列 30 条）",
        "",
    ]
    if rows:
        for row in rows[:30]:
            lines.append("- `%s` %s %s [%s] — 码 %s — %s"
                         % (row["id"], row["name"], row["date"], row["phase"],
                            "/".join(row["codes"]), row["text"]))
    else:
        lines.append("- （扫描面内零带码）")
    lines += [
        "",
        "## 修法指针",
        "",
        "- 喂入面：`Tools/evolve_citizen.py` `real_signals()` 用 `scrub_event_codes()` 清掉事件码，",
        "  锚定律因此不再被逼着逐字引用内部编号。",
        "- 门内：`ring_violations()` 新增 `event-code` 违例，`gated_llm()` 带尾巴提示要求重写。",
        "- 落环口：`add_ring()` 兜底拒写带码行（该席留 due，下轮再试）。",
        "- 存量带码年轮不回改（锚定律要求原文保全），只作计量与回归看守；",
        "  如需回修须另立单由导演席裁定。",
        "",
        "机器清单：`qa/ring-lint.jsonl`",
    ]
    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print("rings=%d coded=%d pre=%d post=%d verdict=%s report=%s"
          % (total, bad, len(pre_rows), len(post_rows), verdict,
             os.path.relpath(REPORT, ROOT)))
    if args.today_only:
        return 1 if post_rows else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())