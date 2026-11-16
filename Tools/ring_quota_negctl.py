# -*- coding: utf-8 -*-
"""12h 全城开口配额闸的实弹负控台（T-20261115-04 换靶线 · R3204 协议可执行化）。

背景：T-20261115-04 的修法补丁已静态过 12/12 回归但从未实弹跑过，协议原先只活在
TASKS.md 的一段中文里（「三数 + 回退口」）。人手誊数会漂，回退会漏，故把协议落成
一条命令：A 臂（补丁未生效）→ B 臂（补丁生效）→ 逐项比对 → 判 PASS/FAIL →
FAIL 自动 git apply -R 还原，判据与读数写进 qa/。

回退口（三条硬线，任一破即还原）：
  1) 落环数：B 臂 written < A 臂 written            → 修法伤产线
  2) 命中率：B 臂 citywide-ban 命中 / 尝试席位 > 30% → 闸过宽，整城开口被摘太多
  3) 复读面：当日 wasted_calls 或 max_repeats 高于 A 臂读数 → 把 R3115 修好的
     调度缺陷重新引入（同人被拉回队头）

用后即视：本脚本不改任何闸阈值/族表，只决定那份补丁留或撤。

用法：
  python -X utf8 Tools/ring_quota_negctl.py            # 实弹 A/B（各 8 席，跑 LLM）
  python -X utf8 Tools/ring_quota_negctl.py --batch 6  # 改每臂席位数
  python -X utf8 Tools/ring_quota_negctl.py --dry-run  # 只体检：补丁可打性 + 当日基线
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCH = os.path.join(ROOT, "state", "pending", "R3204-quota-gate.patch")
EVOLVE = os.path.join(ROOT, "Tools", "evolve_citizen.py")
REFUSALS = os.path.join(ROOT, "state", "ring-refusals.jsonl")
QA = os.path.join(ROOT, "qa")

SUMMARY_RE = re.compile(r"OK evolved=(\d+) of (\d+) due \(written=(\d+) skipped=(\d+)\)")
BAN_RE = re.compile(r"gate: citywide-ban hit (\S+)")
YIELD_RE = re.compile(r"yield-window")


def _run(args, timeout=None):
    """跑子进程并按 UTF-8 收口（Windows 控制台默认 GBK，中文读数会乱码）。"""
    p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
    out = (p.stdout or b"").decode("utf-8", "replace")
    err = (p.stderr or b"").decode("utf-8", "replace")
    return p.returncode, out, err


def _git(args):
    return _run(["git"] + args)


def patch_applies():
    rc, out, err = _git(["apply", "--check", PATCH])
    return rc == 0, (out + err).strip()


def patch_applied():
    """补丁是否已在工作树生效（=生成面已带 refusal_bans 接线）。"""
    try:
        with open(EVOLVE, encoding="utf-8") as fh:
            return "citywide-refusal-ban" in fh.read()
    except OSError:
        return False


def refusal_metrics(day):
    """当日拒稿面三数：rows / distinct_cid / wasted_calls / max_repeats。"""
    rows = 0
    cids = {}
    try:
        with open(REFUSALS, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                except Exception:  # noqa: BLE001
                    continue
                if not (rec.get("ts") or "").startswith(day):
                    continue
                rows += 1
                cid = rec.get("cid") or "?"
                cids[cid] = cids.get(cid, 0) + 1
    except FileNotFoundError:
        return {"rows": 0, "distinct_cid": 0, "wasted_calls": 0, "max_repeats": 0}
    return {
        "rows": rows,
        "distinct_cid": len(cids),
        "wasted_calls": rows - len(cids),
        "max_repeats": max(cids.values()) if cids else 0,
    }


def arm(batch, label):
    """跑一臂年轮批，返回 stdout 解析出的可判读数。"""
    rc, out, err = _run([sys.executable, "-X", "utf8", EVOLVE,
                         "--batch", str(batch), "--via", "BigLife-OSLoop"])
    if YIELD_RE.search(out):
        return {"label": label, "yield": True, "rc": rc, "out": out}
    m = SUMMARY_RE.search(out)
    written = int(m.group(3)) if m else 0
    done = int(m.group(1)) if m else 0
    return {
        "label": label,
        "yield": False,
        "rc": rc,
        "written": written,
        "done": done,
        "ban_hits": len(BAN_RE.findall(out)),
        "summary": m.group(0) if m else "(no summary line)",
        "err_tail": err.strip()[-400:],
    }


def judge(a, b, before, after, batch):
    """三条硬线。返回 (verdict, 明细行列表)。"""
    lines = []
    ok = True

    if b["written"] < a["written"]:
        ok = False
        lines.append("FAIL 落环数 %d < 基线 %d（修法伤产线）" % (b["written"], a["written"]))
    else:
        lines.append("ok   落环数 %d >= 基线 %d" % (b["written"], a["written"]))

    rate = (b["ban_hits"] / float(batch)) if batch else 0.0
    if rate > 0.30:
        ok = False
        lines.append("FAIL 命中率 %.0f%% > 30%%（%d/%d 席，闸过宽）"
                     % (rate * 100, b["ban_hits"], batch))
    else:
        lines.append("ok   命中率 %.0f%% <= 30%%（%d/%d 席）"
                     % (rate * 100, b["ban_hits"], batch))

    if after["wasted_calls"] > before["wasted_calls"]:
        ok = False
        lines.append("FAIL wasted_calls %d > %d（同人被拉回队头=R3115 缺陷回归）"
                     % (after["wasted_calls"], before["wasted_calls"]))
    if after["max_repeats"] > before["max_repeats"]:
        ok = False
        lines.append("FAIL max_repeats %d > %d（同人重试冒头）"
                     % (after["max_repeats"], before["max_repeats"]))
    if after["wasted_calls"] <= before["wasted_calls"] and after["max_repeats"] <= before["max_repeats"]:
        lines.append("ok   复读面 wasted=%d max_repeats=%d 未升高"
                     % (after["wasted_calls"], after["max_repeats"]))

    return ("PASS" if ok else "FAIL"), lines


def write_report(day, batch, a, b, verdict, lines, applied_now):
    os.makedirs(QA, exist_ok=True)
    path = os.path.join(QA, "RING-QUOTA-NEGCTL-%s.md" % day.replace("-", ""))
    body = [
        "# 12h 全城开口配额闸·实弹负控（%s）" % day,
        "",
        "- 执行：`Tools/ring_quota_negctl.py`（R3204 协议可执行化·T-20261115-04 换靶线）",
        "- 补丁：`state/pending/R3204-quota-gate.patch`（A 臂=未打，B 臂=已打）",
        "- 每臂席位：%d" % batch,
        "",
        "## 两臂读数",
        "",
        "| 臂 | 补丁 | written | done | citywide-ban 命中 | 摘要行 |",
        "|---|---|---|---|---|---|",
        "| A | 否 | %s | %s | - | `%s` |" % (a.get("written"), a.get("done"), a.get("summary")),
        "| B | 是 | %s | %s | %s | `%s` |" % (b.get("written"), b.get("done"), b.get("ban_hits"), b.get("summary")),
        "",
        "## 判定",
        "",
        "```",
    ] + lines + [
        "```",
        "",
        "**verdict: %s**　补丁现状=%s"
        % (verdict, "已留在工作树（待轮末 commit）" if applied_now else "已 git apply -R 还原"),
        "",
        "## 回退口（三条硬线）",
        "",
        "1. B 臂 written < A 臂 written → 伤产线",
        "2. B 臂命中率 > 30% → 闸过宽",
        "3. 当日 wasted_calls / max_repeats 高于 A 臂前读数 → R3115 调度缺陷回归",
        "",
    ]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(body))
    return path


def main():
    ap = argparse.ArgumentParser(description="12h 全城开口配额闸实弹负控")
    ap.add_argument("--batch", type=int, default=8, help="每臂席位数（默认 8）")
    ap.add_argument("--dry-run", action="store_true", help="只体检：补丁可打性 + 当日基线")
    args = ap.parse_args()

    day = datetime.date.today().strftime("%Y-%m-%d")
    base = refusal_metrics(day)

    if not os.path.exists(PATCH):
        print("patch missing:", PATCH)
        return 2

    applied = patch_applied()
    if applied:
        ok, msg = True, "(补丁已在工作树)"
    else:
        ok, msg = patch_applies()
    print("patch applies: %s %s" % ("YES" if ok else "NO", msg))
    print("baseline %s: rows=%d distinct=%d wasted=%d max_repeats=%d"
          % (day, base["rows"], base["distinct_cid"],
             base["wasted_calls"], base["max_repeats"]))

    if args.dry_run:
        print("dry-run: 未跑 LLM、未改工作树")
        return 0 if ok else 2
    if not ok:
        print("patch does not apply cleanly -> abort")
        return 2

    print("arm A (patch OFF) ...", flush=True)
    a = arm(args.batch, "A")
    if a.get("yield"):
        print("yield-window: 产线让路期，A 臂未跑（0 LLM/0 改动）")
        return 3

    before = refusal_metrics(day)
    applied_now = False
    try:
        rc, out, err = _git(["apply", PATCH])
        if rc != 0:
            print("git apply failed:", (out + err).strip())
            return 2
        applied_now = True
        print("arm B (patch ON) ...", flush=True)
        b = arm(args.batch, "B")
        if b.get("yield"):
            print("yield-window: B 臂未跑 -> 还原补丁")
            return 3
        after = refusal_metrics(day)
        verdict, lines = judge(a, b, before, after, args.batch)
    finally:
        if applied_now and verdict_is_fail(locals()):
            rc, out, err = _git(["apply", "-R", PATCH])
            print("revert:", "done" if rc == 0 else ("FAILED " + (out + err).strip()))
            applied_now = False

    for ln in lines:
        print(ln)
    path = write_report(day, args.batch, a, b, verdict, lines, applied_now)
    print("report:", os.path.relpath(path, ROOT))
    print("verdict:", verdict, "| patch in tree:", "yes" if applied_now else "no")
    return 0 if verdict == "PASS" else 1


def verdict_is_fail(scope):
    """finally 里判是否要撤补丁（verdict 尚未算出=按失败撤，宁撤不留）。"""
    return scope.get("verdict", "FAIL") != "PASS"


if __name__ == "__main__":
    sys.exit(main())
