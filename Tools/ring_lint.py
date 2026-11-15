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
口径（2026-10-26 R2260 / 2026-10-27 修订）：出生站修复落在 18:57，同日内修前/修后混杂，
日级切点分不开——带码行按 pre/post 两段划。划段先查 **违规指纹基线**
（`qa/ring-lint-baseline.json`：修复当刻扫描件逐环 id|日期|正文 md5 冻结），命中即存量；
未命中再用卡片 mtime 与切点比较。缘由：卡片被合法重写（turning_points 补段/去重）会刷新
mtime，若只看 mtime，旧环原文会被误判成「修后新产」——10-27 15:32 补段批即触发 4 条假警。
存量带码不回归（锚定律保全原文），只计量；只有 post 段带码才判回归失败。

§二 机队术语（2026-11-15 R2970 立）：D-20261115-01 定谳上游 `RESIDENT_SAY` 台词被机队台账
占满（「显存稳…轮转」），这些字句经锚定律逐字引用后串进居民口中——实测 130 条年轮带
显存/GPU/机队等词，集中在 10-24~10-27 与 11-12（喂料侧街区母题替代 Tools/city_life_events.py
生效前）。词表刻意收窄（不含「算力」「内存」等城内地名可用词）以免误伤。划段同 §一口径：
先查 `qa/ring-infra-baseline.json` 指纹基线（本工具 --freeze-infra-baseline 一键冻结），
未命中再看卡片 mtime 与 11-13 零点切点。11-13 起实测三日零污染，故 post 段 >0 即判喂料回归。
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "qa", "RING-LINT-REPORT.md")
MACHINE = os.path.join(ROOT, "qa", "ring-lint.jsonl")
# 修复当刻违规指纹基线（由 06cbdf461 的 qa/ring-lint.jsonl 逐环指纹冻结生成）
BASELINE = os.path.join(ROOT, "qa", "ring-lint-baseline.json")
# 机队术语污染指纹基线（2026-11-15 冻结：上游台账字句经锚定律逐字引用的存量，见文件头 §二）
INFRA_BASELINE = os.path.join(ROOT, "qa", "ring-infra-baseline.json")

RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) [ \t]*(.+)$", re.M)
HEAD_RE = re.compile(r"^#\s*(C-\d+)\s*·\s*(.+)$")
# 与 Tools/evolve_citizen.py EVENT_CODE_RE 同源（带横杠的居民 ID 合法，故不含横杠）
CODE_RE = re.compile(r"(?<![A-Za-z0-9-])[GBSPT]\d{1,4}(?:\.\d+)?(?![0-9])")
# 机队术语：FluxVerse 台账台词（「显存稳…轮转」）被锚定律逐字引用进居民年轮后的串种面。
# 词表刻意收窄（只收机器硬件/机队专名），算力/内存等城内地名可用词不入判据，避免误伤。
INFRA_RE = re.compile(r"显存|VRAM|GPU|显卡|机队", re.I)
# 出生站修复切点（commit 06cbdf461 2026-10-26 18:57 三面收口：喂入清码/门内拒收/落环兜底）
DEFAULT_FIX_CUT = "2026-10-26T18:57"
# 机队术语切点：喂料侧街区母题替代（Tools/city_life_events.py R2566）自 11-12 起生效，
# 实测 11-13/11-14/11-15 三日零污染，故以 11-13 零点为「修后新产」判据起点；11-12 及以前=存量。
INFRA_FIX_CUT = "2026-11-13T00:00"


def ring_fingerprint(cid: str, date: str, body: str) -> str:
    """单条年轮的稳定指纹（id|日期|正文 md5）——卡片重写换不掉它，用于区分历史冻结与真回炉。"""
    return "%s|%s|%s" % (cid, date, hashlib.md5(body.encode("utf-8")).hexdigest())


def load_baseline(path: str = BASELINE) -> tuple[set[str], dict]:
    """读违规指纹基线；缺席=纯 mtime 口径（旧行为），不新增失败面。"""
    if not os.path.exists(path):
        return set(), {}
    try:
        with io.open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return set(data.get("fingerprints") or []), data.get("meta") or {}
    except (OSError, ValueError):
        return set(), {}


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


def scan_registry(floor: str = ""):
    """遍历 registry，产 (path, cid, name, date, body)；floor 为空=全量。"""
    for path in sorted(glob.glob(os.path.join(ROOT, "census", "registry", "**", "*.md"),
                                recursive=True)):
        cid, name, rings = parse(path)
        for date, body in rings:
            if floor and date < floor:
                continue
            yield path, cid, name, date, body


def freeze_infra_baseline() -> int:
    """把当前全库机队术语污染的逐环指纹冻结为存量基线（一次性，改动喂料面后须重冻）。"""
    prints: list[str] = []
    rows = 0
    for _path, cid, _name, date, body in scan_registry():
        if not INFRA_RE.search(body):
            continue
        rows += 1
        prints.append(ring_fingerprint(cid, date, body))
    payload = {
        "meta": {
            "frozen_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"),
            "infra_fix_cut": INFRA_FIX_CUT,
            "rule": "INFRA_RE=%s" % INFRA_RE.pattern,
            "source_commit": os.popen("git rev-parse --short HEAD").read().strip(),
            "note": "喂料侧街区母题替代（Tools/city_life_events.py R2566）落地前的存量污染指纹；"
                    "锚定律保全原文，只计量不回收。",
        },
        "fingerprints": sorted(set(prints)),
    }
    os.makedirs(os.path.join(ROOT, "qa"), exist_ok=True)
    with io.open(INFRA_BASELINE, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    print("frozen infra baseline rows=%d file=%s"
          % (len(payload["fingerprints"]), os.path.relpath(INFRA_BASELINE, ROOT)))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-10-20")
    ap.add_argument("--today-only", action="store_true")
    ap.add_argument("--fix-cut", default=DEFAULT_FIX_CUT,
                    help="出生站修复切点（本地时间 ISO，如 2026-10-26T18:57）")
    ap.add_argument("--infra-fix-cut", default=INFRA_FIX_CUT,
                    help="机队术语修复切点（本地时间 ISO，如 2026-11-13T00:00）")
    ap.add_argument("--freeze-infra-baseline", action="store_true",
                    help="把当前机队术语污染逐环指纹冻结为存量基线后退出")
    args = ap.parse_args()
    if args.freeze_infra_baseline:
        return freeze_infra_baseline()
    fix_cut = args.fix_cut.replace(" ", "T")[:16]
    infra_cut = args.infra_fix_cut.replace(" ", "T")[:16]
    today = datetime.date.today().isoformat()
    floor = today if args.today_only else args.since
    baseline, baseline_meta = load_baseline()
    infra_baseline, infra_meta = load_baseline(INFRA_BASELINE)

    per_day: dict[str, list[int]] = {}
    infra_per_day: dict[str, list[int]] = {}
    rows: list[dict] = []
    for path, cid, name, date, body in scan_registry(floor):
        mtime = card_mtime(path)
        bucket = per_day.setdefault(date, [0, 0])
        bucket[0] += 1
        ibucket = infra_per_day.setdefault(date, [0, 0])
        ibucket[0] += 1
        codes = sorted(set(CODE_RE.findall(body)))
        infra = sorted({w for w in INFRA_RE.findall(body)})
        if codes:
            bucket[1] += 1
        if infra:
            ibucket[1] += 1
        if not codes and not infra:
            continue
        fp = ring_fingerprint(cid, date, body)
        row = {
            "date": date,
            "card": os.path.relpath(path, ROOT).replace("\\", "/"),
            "id": cid,
            "name": name,
            "codes": codes,
            "infra": infra,
            "text": body[:160],
            "mtime": mtime,
            "fingerprint": fp,
        }
        if codes:
            # 划段三判：①基线命中=修复当刻已存在的存量（哪怕卡片后来被合法重写刷了 mtime）
            # ②mtime 早于切点=存量 ③其余=修后新产（回归指标）
            if fp in baseline:
                row["phase"] = "pre"
            else:
                row["phase"] = "pre" if (mtime and mtime < fix_cut) else "post"
        if infra:
            if fp in infra_baseline:
                row["infra_phase"] = "pre"
            else:
                row["infra_phase"] = "pre" if (mtime and mtime < infra_cut) else "post"
        rows.append(row)

    total = sum(v[0] for v in per_day.values())
    bad = sum(v[1] for v in per_day.values())
    rate = (100.0 * bad / total) if total else 0.0
    infra_total = sum(v[0] for v in infra_per_day.values())
    infra_bad = sum(v[1] for v in infra_per_day.values())
    infra_rate = (100.0 * infra_bad / infra_total) if infra_total else 0.0
    pre_rows = [r for r in rows if r.get("phase") == "pre"]
    post_rows = [r for r in rows if r.get("phase") == "post"]
    infra_pre = [r for r in rows if r.get("infra_phase") == "pre"]
    infra_post = [r for r in rows if r.get("infra_phase") == "post"]
    verdict = "PASS" if not post_rows and not infra_post else "FAIL"

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
        "切点=%s（出生站三面收口 commit 06cbdf461）· 划段依据=违规指纹基线 %s 条（源 %s）+ 卡片 mtime 兜底"
        % (fix_cut, len(baseline), baseline_meta.get("source_commit", "缺席")),
        "",
        "划段口径（2026-10-27 修订）：卡片文件被合法重写（补段/去重）会刷新 mtime，旧环原文按锚定律不回改——"
        "故先查指纹基线，命中即判存量，消除「重写即回炉」假警。",
        "",
        "| 阶段 | 带码年轮 | 口径 |",
        "| --- | ---: | --- |",
        "| 修前存量 | %d | 锚定律保全原文，不回改；只作历史计量 |" % len(pre_rows),
        "| 修后新产 | %d | 回归指标；>0 即修复失效 |" % len(post_rows),
        "",
        "判定：**%s**" % verdict,
        "",
        "## 机队术语巡检（19xx 世界失真面）",
        "",
        "判据：年轮正文出现机器硬件/机队专名（%s）即计一条——这类词来自上游台账台词"
        "（「显存稳…轮转」），经锚定律逐字引用后串进居民口中。" % INFRA_RE.pattern,
        "",
        "切点=%s（喂料侧街区母题替代 Tools/city_life_events.py 生效日）· 存量基线 %s 条（冻结 %s）"
        % (infra_cut, len(infra_baseline), infra_meta.get("frozen_at", "缺席")),
        "",
        "| 日期 | 年轮数 | 带机队词 | 占比 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for date in sorted(infra_per_day):
        t, b = infra_per_day[date]
        lines.append("| %s | %d | %d | %.1f%% |" % (date, t, b, 100.0 * b / t if t else 0.0))
    lines += [
        "| **合计** | **%d** | **%d** | **%.1f%%** |" % (infra_total, infra_bad, infra_rate),
        "",
        "| 阶段 | 带机队词年轮 | 口径 |",
        "| --- | ---: | --- |",
        "| 修前存量 | %d | 锚定律保全原文，不回改；只作历史计量 |" % len(infra_pre),
        "| 修后新产 | %d | 回归指标；>0 即喂料面重新漏入 |" % len(infra_post),
        "",
        "## 涉及居民（最多列 30 条）",
        "",
    ]
    if rows:
        for row in rows[:30]:
            mark = "/".join(row["codes"]) if row["codes"] else ""
            if row.get("infra"):
                mark = (mark + " 机队词:" + "/".join(row["infra"])).strip()
            phase = row.get("phase") or row.get("infra_phase") or "-"
            lines.append("- `%s` %s %s [%s] — %s — %s"
                         % (row["id"], row["name"], row["date"], phase,
                            mark, row["text"]))
    else:
        lines.append("- （扫描面内零违规）")
    lines += [
        "",
        "## 修法指针",
        "",
        "- 喂入面：`Tools/evolve_citizen.py` `real_signals()` 用 `scrub_event_codes()` 清掉事件码，",
        "  锚定律因此不再被逼着逐字引用内部编号。",
        "- 门内：`ring_violations()` 新增 `event-code` 违例，`gated_llm()` 带尾巴提示要求重写。",
        "- 落环口：`add_ring()` 兜底拒写带码行（该席留 due，下轮再试）。",
        "- 机队术语：喂料侧以街区日常母题替代上游台账字句（`Tools/city_life_events.py` R2566），",
        "  本巡检看守回归；存量按锚定律保全，不回改。",
        "- 存量带码年轮不回改（锚定律要求原文保全），只作计量与回归看守；",
        "  如需回修须另立单由导演席裁定。",
        "",
        "机器清单：`qa/ring-lint.jsonl`",
    ]
    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    print("rings=%d coded=%d pre=%d post=%d | infra=%d infra_pre=%d infra_post=%d | verdict=%s report=%s"
          % (total, bad, len(pre_rows), len(post_rows), infra_bad, len(infra_pre),
             len(infra_post), verdict, os.path.relpath(REPORT, ROOT)))
    if args.today_only:
        return 1 if (post_rows or infra_post) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())