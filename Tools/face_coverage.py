# -*- coding: utf-8 -*-
"""面覆盖自动发现（零 LLM·只读扫描·确定性）。

病根（T-20261112-02 同族，第十例起）：round_daily.py 的 REGISTRY 是**人手登记表**，
于是「有生成器、有产出、无任何轮次引用」的面只能一轮发现一个——
10-27 起 12 个面停更 15 天、lexicon 断供 15.7 天、social-graph 17 天、
ring_lint 17 天、citizen-tasks 48 天，全是同一病理的连续个案。

修法=不再靠人肉枚举，改为扫源自动对账：
  ① 扫 Tools/*.py 里的产物字面量（city-*.html / *.jsonl / *.md ...）；
  ② 逐个落盘解析（export/ 根/cognition/qa/state/docs/genes/events）；
  ③ 与 round_daily.REGISTRY + INPUTS 的登记产物做差集；
  ④ 差集按 mtime 年龄降序 = 「下一个会静默停更的面」风险序。

用法:
  python -X utf8 Tools/face_coverage.py            # 打印风险表（rc=0，纯只读）
  python -X utf8 Tools/face_coverage.py --write    # 同时写 qa/FACE-COVERAGE-REPORT.md
  python -X utf8 Tools/face_coverage.py --json     # 机器可读
  python -X utf8 Tools/face_coverage.py --max-age 3  # 只报超过 N 天的未登记面（默认 1）
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "Tools")

# 产物候选字面量：扩展名闭集，长度上限防止把整段提示词当文件名
ART_RE = re.compile(
    r"""["']([A-Za-z0-9_\-./{}]{2,80}\.(?:html|jsonl|json|md|txt))["']""")

# 落盘解析顺序：先摸清各仓内产物目录，再退回仓根（社交图谱等故意落根的例外）
SEARCH_DIRS = ["census/export", "", "census", "cognition", "cognition/rumors",
               "qa", "state", "docs", "docs/research", "genes", "events",
               "events/life"]

# 非产物：脚本自身引用、schema、锁文件
SKIP_SUFFIX = (".py", ".ps1", ".psd1", ".cmd", ".bat", ".exe", ".lock")

# 只认「对外/可见面」三种形态，其余（state/*.json 内部状态、genes/* 正本源、
# 一次性候选 txt、README/INDEX 文档）不算面 —— 首跑实测它们构成 80% 噪声，
# 且按 mtime 年龄排序只会把它们排在风险表首屏，掩盖真正会烂的面。
# append-only 台账：按「上游有没有料」增长，不是按日重建的确定性面。
# 实测两例（2026-11-13）：proposals.jsonl 停 19.6 天（议员提案线实际停产）、
# city-chronicle.jsonl 停 1.4 天（当日无显著事件＝正常）。把它们混进「该重建」队列
# 会让闸永远报 STALE，故单列一节「供料缺口」：报事实、不自动重建。
APPEND_ONLY = {"proposals.jsonl", "city-chronicle.jsonl", "reflections.jsonl",
               "interchat-ledger.jsonl", "surprise-log.jsonl",
               "citizen-relations.jsonl", "derive-audit.json"}

# 「盘上无产物」候选的分类（2026-11-13 全 32 条逐条核验后落定）。
# 未分类的缺口才是真缺口——若不分，一个真死生成器会埋在这个噪声桶里永远看不见。
# 分类只解释「为什么不落盘」，不改判据；新候选落不进任何一类 → unexplained，必须人看。
_EXAMPLE_CITIZEN = re.compile(r"^C-\d+\.md$")
INERT_PLACEHOLDER = ("{", "}")           # {PAGED_PREFIX}01.html / {month}.jsonl
INERT_EMPTY_JOIN = re.compile(r"-\.[a-z]+$")   # rumors-.jsonl = 变量为空时的拼接串
# 外部只读输入（兄弟司正典，本司只读不产）
INERT_EXTERNAL = {"world-state.json", "world-events.jsonl"}
# schema / 参考件 / 纯读工具的输入名——存在即被读，不存在也不该由本司生产
INERT_INPUT = {"citizen-behavior.schema.json", "citizen-needs.schema.json",
               "citizen-tasks.schema.json", "citizens-light.schema.json",
               ".jsonl", "decisions.md", "evolution-ledger.md", "TASKS.md",
               "batch-policy.json", "ledger.jsonl", "manifest.json",
               "tokens.txt", "lexicon-zh.txt", "lexicon-us-en.txt",
               "gene_nearcheck_qc.txt", "benchmark-gap-biglife.jsonl",
               "sublimate-gate.jsonl", "no-such-chronicle.jsonl"}


def _missing_class(name: str) -> str:
    """给「盘上无产物」的候选归因；返回 unexplained 即真缺口。"""
    if name in INERT_INPUT:
        return "inert-input"
    if name in INERT_EXTERNAL:
        return "external-readonly"
    if _EXAMPLE_CITIZEN.match(name) or name.endswith(".schema.json"):
        return "inert-input"
    if any(ch in name for ch in INERT_PLACEHOLDER):
        return "placeholder"
    if INERT_EMPTY_JOIN.search(name):
        return "placeholder"
    return "unexplained"


def _is_face(name: str, path: str) -> bool:
    rel = os.path.relpath(path, ROOT).replace("\\", "/")
    if name.endswith(".html"):
        return True
    if name.endswith(".jsonl"):
        return rel.startswith(("cognition/", "events/"))
    if name.endswith(".md"):
        return rel.startswith("qa/")
    return False


def _registered() -> tuple[set, dict]:
    """从 round_daily 取唯一登记源（单源律：不在此处复制一份登记表）。"""
    try:
        import round_daily as rd
    except Exception as exc:  # noqa: BLE001 - 导入失败要如实报，不静默
        raise SystemExit("FACE-COVERAGE: cannot import round_daily (%s)" % exc)
    today = datetime.date.today().isoformat()
    names, owners = set(), {}
    for entry in list(rd.REGISTRY) + list(rd.INPUTS):
        key, _tier, script, outs = entry[:4]
        for n in outs:
            n = n.replace("{date}", today)
            base = os.path.basename(n)
            names.add(base)
            owners[base] = "%s <- %s" % (key, script)
    return names, owners


def _scan_literals() -> dict:
    """扫 Tools/*.py 产物字面量 -> {basename: [来源脚本...]}"""
    found = {}
    for fn in sorted(os.listdir(TOOLS)):
        if not fn.endswith(".py") or fn == "face_coverage.py":
            continue
        path = os.path.join(TOOLS, fn)
        try:
            with io.open(path, encoding="utf-8", errors="replace") as f:
                src = f.read()
        except OSError:
            continue
        for m in ART_RE.finditer(src):
            lit = m.group(1)
            if lit.endswith(SKIP_SUFFIX):
                continue
            base = os.path.basename(lit.replace("{date}", ""))
            if not base or base in (".", ".."):
                continue
            found.setdefault(base, [])
            if fn not in found[base]:
                found[base].append(fn)
    return found


def _resolve(name: str) -> str | None:
    for d in SEARCH_DIRS:
        p = os.path.join(ROOT, d, name) if d else os.path.join(ROOT, name)
        if os.path.exists(p):
            return p
    return None


def _age_days(path: str) -> float:
    return (time.time() - os.path.getmtime(path)) / 86400.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="写 qa/FACE-COVERAGE-REPORT.md")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--max-age", type=float, default=1.0,
                    help="只报超龄未登记面（天，默认 1）")
    args = ap.parse_args()

    reg, owners = _registered()
    cand = _scan_literals()

    unregistered, missing, fresh_unreg, ledger_gap = [], [], [], []
    for base, scripts in sorted(cand.items()):
        if base in reg:
            continue
        p = _resolve(base)
        if p is None:
            missing.append({"name": base, "from": scripts,
                            "class": _missing_class(base)})
            continue
        if not _is_face(base, p):
            continue
        item = {"name": base, "path": p, "from": scripts,
                "age_days": round(_age_days(p), 1),
                "mtime": datetime.datetime.fromtimestamp(
                    os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")}
        if base in APPEND_ONLY:
            ledger_gap.append(item)
        elif item["age_days"] > args.max_age:
            unregistered.append(item)
        else:
            fresh_unreg.append(item)

    unregistered.sort(key=lambda x: -x["age_days"])
    ledger_gap.sort(key=lambda x: -x["age_days"])
    unexplained = [m for m in missing if m["class"] == "unexplained"]
    payload = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "registered": len(reg),
        "candidates": len(cand),
        "unregistered_stale": len(unregistered),
        "unregistered_fresh": len(fresh_unreg),
        "unregistered_missing": len(missing),
        "missing_unexplained": len(unexplained),
        "ledger_gap": len(ledger_gap),
        "items": unregistered,
        "fresh": fresh_unreg,
        "ledgers": ledger_gap,
        "missing": missing[:40],
    }

    if args.json:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
    else:
        print("== face_coverage (%s) ==" % payload["ts"])
        print("registered=%d candidates=%d stale=%d fresh=%d ledger_gap=%d missing=%d (unexplained=%d)"
              % (len(reg), len(cand), len(unregistered),
                 len(fresh_unreg), len(ledger_gap), len(missing), len(unexplained)))
        if unregistered:
            print("-- 未登记且已超 %.0f 天（下一个会静默停更的面）--" % args.max_age)
            for it in unregistered:
                print("  %6.1fd  %-34s %s  <= %s"
                      % (it["age_days"], it["name"], it["mtime"],
                         ",".join(it["from"][:3])))
        else:
            print("verdict: no stale unregistered face")
        if ledger_gap:
            print("-- append-only 台账供料缺口（不自动重建·查上游有无料）--")
            for it in ledger_gap:
                print("  %6.1fd  %-34s %s  <= %s"
                      % (it["age_days"], it["name"], it["mtime"],
                         ",".join(it["from"][:3])))

    if args.write:
        day = datetime.date.today().isoformat()
        lines = ["# 面覆盖自动发现报告（%s）" % payload["ts"], "",
                 "> 零 LLM 只读扫描。判据=「Tools 里有生成器字面量、盘上有产物、"
                 "但 round_daily 登记表里没有它」。登记表是唯一权威，本报告只做差集。", "",
                 "- 已登记面：%d" % len(reg),
                 "- 扫描候选产物名：%d" % len(cand),
                 "- 未登记且超 %.0f 天：**%d**" % (args.max_age, len(unregistered)),
                 "- 未登记但新鲜：%d" % len(fresh_unreg),
                 "- append-only 台账供料缺口：%d" % len(ledger_gap),
                 "- 未登记且盘上无产物：%d（其中**未解释 %d**）"
                 % (len(missing), len(unexplained)), ""]
        if unregistered:
            lines += ["## 风险序（下一个会静默停更的面）", "",
                      "| 年龄 | 产物 | 最后写入 | 生成器 |", "|---|---|---|---|"]
            for it in unregistered:
                lines.append("| %.1f 天 | `%s` | %s | %s |"
                             % (it["age_days"], it["name"], it["mtime"],
                                ", ".join(it["from"][:3])))
            lines.append("")
        if fresh_unreg:
            lines += ["## 未登记但新鲜（窗口内，观察）", ""]
            for it in fresh_unreg:
                lines.append("- %.1fd `%s` <= %s"
                             % (it["age_days"], it["name"], ", ".join(it["from"][:3])))
            lines.append("")
        if ledger_gap:
            lines += ["## append-only 台账供料缺口", "",
                      "> 按上游事件增长，不是按日重建的确定性面——本表只报事实与上游，"
                      "不自动重建（重建会写假行）。年龄大＝该线上游已停产。", "",
                      "| 静默 | 台账 | 最后追加 | 生成器 |", "|---|---|---|---|"]
            for it in ledger_gap:
                lines.append("| %.1f 天 | `%s` | %s | %s |"
                             % (it["age_days"], it["name"], it["mtime"],
                                ", ".join(it["from"][:3])))
            lines.append("")
        if missing:
            cls_count = {}
            for m in missing:
                cls_count[m["class"]] = cls_count.get(m["class"], 0) + 1
            lines += ["## 盘上无产物候选（已归因）", "",
                      "> 归因只解释「为什么不落盘」，不改判据。"
                      "**unexplained 非零＝真缺口，必须人看**；"
                      "新候选落不进任何一类就会出现在这里。", "",
                      "- 分类计数：" + "／".join(
                          "%s=%d" % (k, cls_count[k]) for k in sorted(cls_count)), ""]
            if unexplained:
                lines += ["### unexplained（真缺口）", "",
                          "| 候选 | 生成器 |", "|---|---|"]
                for m in unexplained:
                    lines.append("| `%s` | %s |"
                                 % (m["name"], ", ".join(m["from"][:3])))
                lines.append("")
            else:
                lines += ["**unexplained = 0**（当前无真缺口，本轮无动作）", ""]
        out = os.path.join(ROOT, "qa", "FACE-COVERAGE-REPORT.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
        print("written: qa/FACE-COVERAGE-REPORT.md (%s)" % day)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
