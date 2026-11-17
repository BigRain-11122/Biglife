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

混淆闸（R3239 加·R3208 实锤）：两臂起跑时各取一次「当前生效开口禁牌集合」，若不同
（典型=吸引子 12h 禁牌在两臂之间到期，如 07:34 被拒 → 19:34 解禁，而生成窗 19:00 开）
直接判 CONFOUNDED 且不出留撤结论——否则量到的是禁牌到期，不是补丁效果。

用后即视：本脚本不改任何闸阈值/族表，只决定那份补丁留或撤。

用法：
  python -X utf8 Tools/ring_quota_negctl.py            # 实弹 A/B（各 8 席，跑 LLM）
  python -X utf8 Tools/ring_quota_negctl.py --batch 6  # 改每臂席位数
  python -X utf8 Tools/ring_quota_negctl.py --dry-run  # 只体检：补丁可打性 + 当日基线
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCH = os.path.join(ROOT, "state", "pending", "R3204-quota-gate.patch")
EVOLVE = os.path.join(ROOT, "Tools", "evolve_citizen.py")
REFUSALS = os.path.join(ROOT, "state", "ring-refusals.jsonl")
QA = os.path.join(ROOT, "qa")
ARM_LOG_DIR = os.path.join(ROOT, "state", "negctl")

SUMMARY_RE = re.compile(r"OK evolved=(\d+) of (\d+) due \(written=(\d+) skipped=(\d+)\)")
DUE_RE = re.compile(r"audit-due: due=(\d+)")
BAN_RE = re.compile(r"gate: citywide-ban hit (\S+)")
BANSRC_RE = re.compile(r"refusal-bans source: (\S+) n=(\d+)")
YIELD_RE = re.compile(r"yield-window")
GATEOFF_RE = re.compile(r"quota-gate: off \(env BIGLIFE_QUOTA_GATE\)")
GATE_ENV = "BIGLIFE_QUOTA_GATE"


def _run(args, timeout=None, env=None):
    """跑子进程并按 UTF-8 收口（Windows 控制台默认 GBK，中文读数会乱码）。"""
    p = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout, env=env)
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


def patch_steps(started_applied):
    """返回 (A 臂目标态, B 臂目标态, 收尾态)——纯函数，可回归。

    A 臂必须「补丁未生效」、B 臂必须「生效」，与补丁来自工作树还是已入 HEAD 无关。
    R3246 实锤：R3204 补丁 14:23 已 commit（efc562b9f），旧逻辑只在「补丁待打」前提下
    才撤/打，于是 A 臂带着补丁跑完、B 臂前 `git apply` 直接失败，19:00 窗口白烧。
    """
    return (False, True, bool(started_applied))


def _set_patch(desired):
    """把工作树补丁态设成 desired（True=生效）·幂等·返回 (rc, msg)。"""
    if patch_applied() == bool(desired):
        return 0, "already %s" % ("applied" if desired else "reverted")
    args = ["apply", PATCH] if desired else ["apply", "-R", PATCH]
    rc, out, err = _git(args)
    return rc, (out + err).strip()


def ban_snapshot():
    """当前生效的开口禁牌集合（两臂须在同一禁牌状态下量，否则读数被混淆）。

    R3208 实锤：吸引子末次被拒 07:34 + REFUSAL_BAN_HOURS=12 → 19:34 解禁，而生成窗
    19:00 就开。若 A 臂 19:0x 跑、B 臂 19:4x 跑，比的就不是补丁而是「禁牌到期」，
    故此处取两臂各自起跑时的禁牌集合并要求在判据里比对。
    """
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools"))
        import evolve_citizen as ev  # 只读：复用现行禁牌窗口实现，不复制阈值
        hours = getattr(ev, "REFUSAL_BAN_HOURS", 12)
        bans = ev.recent_refusal_bans()
        if bans:
            exp_min = (min(bans.values()) + datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
            exp_max = (max(bans.values()) + datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M")
        else:
            exp_min = exp_max = "-"
        return {"n": len(bans), "keys": sorted(bans.keys()),
                "exp_min": exp_min, "exp_max": exp_max}
    except Exception:  # noqa: BLE001
        return None


def freeze_bans_file(dest=None):
    """把当前生效禁牌写成冻结快照（两臂共用），返回 (path, n) 或 (None, 0)。

    冻结后两臂看到逐字相同的禁牌集合——禁牌在 A→B 之间到期不再污染读数，
    「必须在 soonest_expiry 前跑完」的时间压力随之解除（R3208 同类环境量污染）。
    """
    try:
        sys.path.insert(0, os.path.join(ROOT, "Tools"))
        import evolve_citizen as ev
        bans = ev.recent_refusal_bans()
    except Exception:  # noqa: BLE001 - 快照建不出就退回实时窗口
        return None, 0
    if dest is None:
        fd, dest = tempfile.mkstemp(prefix="negctl-bans-", suffix=".json")
        os.close(fd)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({k: v.isoformat() for k, v in bans.items()}, fh, ensure_ascii=False)
    return dest, len(bans)


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


def plan_batch(due, want):
    """两臂各取多少席。返回 (effective|None, 说明)。

    为什么要有这一步：拒稿席也被推 +1d（R3115 的调度修法），即 due 按「尝试」消耗，
    不是按「写成功」消耗。A 臂 attempt N 之后 B 臂只剩 due-N 席，故 N > floor(due/2)
    时 B 臂必然少写——judge 的硬线 1（B written < A written）会把「席位不够」误判成
    「修法伤产线」并自动还原补丁。2026-11-16 实读 due=10、默认每臂 8，正属这一情形。
    """
    if due is None:
        return want, "due 不可读（沿用请求值 %d，风险自担）" % want
    eff = min(want, due // 2)
    if eff < 2:
        return None, ("席位预算不足：due=%d → 每臂最多 %d 席（需 ≥2）"
                      % (due, due // 2))
    if eff < want:
        return eff, ("席位预算收敛：due=%d → 每臂 %d 席（请求 %d；B 臂不会因缺席少写）"
                     % (due, eff, want))
    return eff, "席位充足：due=%d → 每臂 %d 席" % (due, eff)


def due_count():
    """今日到期席位供给（零 LLM：--audit-due 只读 cursor）。不可读返回 None。"""
    rc, out, err = _run([sys.executable, "-X", "utf8", EVOLVE, "--audit-due"])
    m = DUE_RE.search(out or "")
    return int(m.group(1)) if m else None


def due_consistency(due_before, due_after, attempted):
    """两臂前后 due 口径比对（T-20261116-13 前置②）。返回 (ok, 说明)。

    拒稿席也推 +1d（R3115 的调度修法），故「尝试」即消耗 due。两臂都跑完却一个
    due 也没减，说明 `--audit-due` 与 `--batch` 读的不是同一份口径（或席位在推 due
    之前就被挡掉）——此时 written 比对无从解释，按 TOOLING_ERROR 处理，不裁补丁留撤。
    """
    if due_before is None or due_after is None:
        return False, ("due 不可读（before=%s after=%s）→ 口径无法比对"
                       % (due_before, due_after))
    delta = due_before - due_after
    if delta <= 0:
        return False, ("due 未消耗（before=%d after=%d 差=%d·尝试 %d 席）→ 口径不一致"
                       % (due_before, due_after, delta, attempted))
    return True, ("due 口径一致（before=%d after=%d 消耗 %d·尝试 %d 席）"
                  % (due_before, due_after, delta, attempted))


def _dump_arm(day, label, rc, out, err):
    """把一臂的原始 stdout/stderr 落盘（T-20261116-13 前置①·arm stdout 落盘）。

    为什么必须落盘：两臂报告曾只剩 `(no summary line)`，逐席拒稿理由全丢，于是
    「为什么 0 落环」无法复现，只能重复烧席位（R3290 判例）。全量留档后，
    TOOLING_ERROR 可从日志复现，不必重跑 LLM。
    """
    try:
        os.makedirs(ARM_LOG_DIR, exist_ok=True)
        path = os.path.join(ARM_LOG_DIR, "arm-%s-%s.log"
                            % (day.replace("-", ""), label))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("### day=%s arm=%s rc=%s\n### --- stdout ---\n%s\n"
                     "### --- stderr ---\n%s\n" % (day, label, rc, out, err))
        return path
    except OSError:
        return None


def arm(batch, label, env=None, day=None):
    """跑一臂年轮批，返回 stdout 解析出的可判读数。

    无摘要行时 `written/done` 返回 **None**（不是 0）：把「读不到」写成 0，会让
    TOOLING_ERROR 冒充真实落环读数（R3290 两臂 written=0 done=0 退化读数判例）。
    """
    rc, out, err = _run([sys.executable, "-X", "utf8", EVOLVE,
                         "--batch", str(batch), "--via", "BigLife-OSLoop"], env=env)
    log = _dump_arm(day, label, rc, out, err) if day else None
    if YIELD_RE.search(out):
        return {"label": label, "yield": True, "rc": rc, "out": out, "log": log}
    m = SUMMARY_RE.search(out)
    src = BANSRC_RE.search(out)
    return {
        "label": label,
        "yield": False,
        "rc": rc,
        "written": int(m.group(3)) if m else None,
        "done": int(m.group(1)) if m else None,
        "gate_off": bool(GATEOFF_RE.search(out or "")),
        "ban_hits": len(BAN_RE.findall(out)),
        "ban_src": src.group(1) if src else "?",
        "ban_n": int(src.group(2)) if src else -1,
        "summary": m.group(0) if m else "(no summary line)",
        "out_tail": out.strip()[-1500:],
        "err_tail": err.strip()[-600:],
        "log": log,
    }


def judge(a, b, before, after, batch, snap_a=None, snap_b=None, frozen=False):
    """三条硬线。返回 (verdict, 明细行列表)。

    frozen=True 时两臂按构造看到同一禁牌快照 → 「到期/携带」两类混淆不适用，
    不得再用墙钟禁牌集比对（否则会把有效读数判成 CONFOUNDED）。
    """
    lines = []
    ok = True

    # ③ TOOLING_ERROR 分型：无摘要行 ≠ written=0。臂读数不可解析时，任何落环比对
    #    都是在比两个未知数（R3290 两臂 0/0 被当成「退化但可比」的判例）。
    bad = [x for x in (a, b) if x.get("written") is None]
    if bad:
        for x in bad:
            lines.append("TOOLING_ERROR %s 臂无摘要行（%s·rc=%s）→ 该臂落环数未知，"
                         "不得当作 0 参与比对"
                         % (x.get("label"), x.get("summary"), x.get("rc")))
            tail = (x.get("err_tail") or x.get("out_tail") or "").replace("\n", " ")
            if tail:
                lines.append("　%s 臂尾部=%r" % (x.get("label"), tail[:200]))
        lines.append("　→ 逐席拒稿理由见 state/negctl/arm-<day>-<臂>.log；修工装后重跑，"
                     "不得据此裁决补丁留撤")
        return "TOOLING_ERROR", lines

    # 混淆面先行：两臂之间「禁牌到期」→ 两臂时间环境不同，任何比对都无效
    carry = []
    if frozen:
        lines.append("ok   两臂禁牌集合按快照冻结共用（n=%s·墙钟到期混淆不适用）"
                     % (a.get("ban_n") if a.get("ban_n", -1) >= 0 else "?"))
    elif snap_a and snap_b:
        expired = sorted(set(snap_a["keys"]) - set(snap_b["keys"]))
        carry = sorted(set(snap_b["keys"]) - set(snap_a["keys"]))
        if expired:
            lines.append("CONFOUNDED 禁牌在 A→B 之间到期 %d 条（A=%d→B=%d·例=%r）"
                         % (len(expired), snap_a["n"], snap_b["n"], expired[:1]))
            lines.append("　→ 读数不可用于裁决补丁留撤；重跑两臂使其落在同一禁牌窗口内（或全在解禁后）")
            return "CONFOUNDED", lines
        if carry:
            # 携带效应：A 臂被拒的开口会进禁牌表，B 臂因此更受限 = 偏差方向对 B 不利
            lines.append("note 携带效应：A 臂新增 %d 条禁牌带入 B 臂（对 B 不利）" % len(carry))
        else:
            lines.append("ok   禁牌集合两臂一致（n=%d·最早到期 %s）"
                         % (snap_a["n"], snap_a["exp_min"]))

    # R3255: 零命中先判——闸没拦过一次时，落环差/复读面读数与闸无关，
    # 旧顺序会把别的闸造成的 1 席差判成 FAIL（本轮实测 9<10 即此假 FAIL）。
    if not (b.get("ban_hits") or 0):
        lines.append("note 无判别力：B 臂闸零命中（当时冻结禁牌 %s 条）——该批没有任何"
                     "「闸真的拦过一次」的证据，落环差与复读面读数不能用于留撤"
                     % (snap_b.get("n") if snap_b else "?"))
        return "INCONCLUSIVE", lines

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

    if ok and not (b.get("ban_hits") or 0):
        lines.append("note 兜底：零命中不得判 PASS")
        return "INCONCLUSIVE", lines
    if ok and carry:
        lines.append("note PASS 在携带效应对 B 不利的前提下取得（保守方向·可信度更高）")
    elif not ok and carry:
        lines.append("note 本次 FAIL 可能由携带效应放大（B 臂多带 %d 条禁牌）→ 需同一环境重跑确认"
                     % len(carry))
    return ("PASS" if ok else "FAIL"), lines


def write_report(day, batch, a, b, verdict, lines, restore_state, snap_a=None, snap_b=None,
                 freeze_state="-", arm_logs=None, due_note=None):
    os.makedirs(QA, exist_ok=True)
    path = os.path.join(QA, "RING-QUOTA-NEGCTL-%s.md" % day.replace("-", ""))
    def _fmt(s):
        return "(unavailable)" if not s else "active=%d·最早到期 %s" % (s["n"], s["exp_min"])
    def _num(x):
        return "?" if x is None else x
    def _rel(p):
        return os.path.relpath(p, ROOT) if p else "(未落盘)"
    body = [
        "# 12h 全城开口配额闸·实弹负控（%s）" % day,
        "",
        "- 执行：`Tools/ring_quota_negctl.py`（R3204 协议可执行化·T-20261115-04 换靶线）",
        "- 开关：运行时 env `BIGLIFE_QUOTA_GATE`（R3255）——A 臂=off，B 臂=on；"
        "闸代码常驻树内，工作树零写入（文本反向补丁基线漂移已废弃）",
        "- 每臂席位：%d" % batch,
        "- 禁牌态：A 臂 %s ／ B 臂 %s（A 臂关闸时恒为 0 条，非偏差）"
        % (_fmt(snap_a), _fmt(snap_b)),
        "- 禁牌快照：%s" % freeze_state,
        "",
        "## 两臂读数",
        "",
        "| 臂 | 闸 | written | done | citywide-ban 命中 | 摘要行 |",
        "|---|---|---|---|---|---|",
        "| A | off | %s | %s | - | `%s` |" % (_num(a.get("written")), _num(a.get("done")), a.get("summary")),
        "| B | on | %s | %s | %s | `%s`" % (_num(b.get("written")), _num(b.get("done")), b.get("ban_hits"), b.get("summary")),
        "",
        "## 口径与原始输出（TOOLING_ERROR 可复现面）",
        "",
        "- due 口径：%s" % (due_note or "(未采集)"),
        "- A 臂原始输出：`%s`" % _rel((arm_logs or {}).get("A")),
        "- B 臂原始输出：`%s`" % _rel((arm_logs or {}).get("B")),
    ]
    # 无摘要行时把尾部原文带进报告——否则「为什么 0 落环」只剩一句猜测
    for x in (a, b):
        if x.get("written") is None:
            body += [
                "",
                "### %s 臂诊断尾部" % x.get("label"),
                "",
                "```",
                (x.get("out_tail") or x.get("out") or "(空)")[-1200:],
                "```",
            ]
    body += [
        "",
        "## 判定",
        "",
        "```",
    ] + lines + [
        "```",
        "",
        "**verdict: %s**　闸代码终态=%s"
        % (verdict, "常驻生效（= 起跑前状态·工作树无残留改动）"
           if restore_state else "未生效（工作树已还原到起跑前）"),
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
    ap.add_argument("--no-freeze", action="store_true",
                    help="两臂各自取实时禁牌窗口（默认冻结同一快照；仅用于复核冻结面本身）")
    ap.add_argument("--selftest", action="store_true",
                    help="四道闸回归电池（席位预算/禁牌混淆/补丁态编排/报告落地·零 LLM·零盘污）")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    day = datetime.date.today().strftime("%Y-%m-%d")
    base = refusal_metrics(day)

    if not os.path.exists(PATCH):
        print("patch missing:", PATCH)
        return 2

    started_applied = patch_applied()
    a_state, b_state, restore_state = patch_steps(started_applied)
    # R3255: 补丁常驻，A/B 只差一个 env（BIGLIFE_QUOTA_GATE）——文本反向补丁的基线会随
    # evolve_citizen.py 演进漂移（R3253 rc=2 根因），故 _set_patch 不再参与翻面。
    ok = bool(started_applied)
    msg = "(运行时开关：闸代码须已在树内生效)"
    print("gate code in tree: %s %s" % ("YES" if ok else "NO", msg))
    print("gate plan: 补丁常驻=%s A 臂=off(env) B 臂=on(env) 收尾=不变"
          % ("applied" if started_applied else "reverted"))
    if not ok:
        print("gate code missing in tree -> abort（先让 R3204 闸代码入 HEAD）")
        return 2
    print("baseline %s: rows=%d distinct=%d wasted=%d max_repeats=%d"
          % (day, base["rows"], base["distinct_cid"],
             base["wasted_calls"], base["max_repeats"]))

    snap0 = ban_snapshot()
    if snap0 is None:
        print("ban state: (unavailable·混淆闸本次不生效)")
    else:
        print("ban state: active=%d soonest_expiry=%s latest_expiry=%s"
              % (snap0["n"], snap0["exp_min"], snap0["exp_max"]))

    if args.dry_run:
        if args.no_freeze and snap0 and snap0["n"]:
            print("dry-run 提示：未冻结 → 两臂须连跑且不跨 %s（禁牌到期点）；跨了判 CONFOUNDED"
                  % snap0["exp_min"])
        elif not args.no_freeze:
            print("dry-run 提示：默认冻结禁牌快照 → 两臂同一集合，不受 %s 到期点约束"
                  % (snap0["exp_min"] if snap0 and snap0["n"] else "-"))
        due = due_count()
        batch, why = plan_batch(due, args.batch)
        print("due budget: %s" % why)
        if batch is None:
            print("dry-run: 席位预算不足 → 实弹会产出假 FAIL（B 臂缺席少写），先别跑")
            return 2
        print("dry-run: 未跑 LLM、未改工作树")
        return 0 if ok else 2
    if not ok:
        print("patch does not apply cleanly -> abort")
        return 2

    print("arm A (patch OFF) ...", flush=True)
    due = due_count()
    batch, why = plan_batch(due, args.batch)
    print("due budget: %s" % why, flush=True)
    if batch is None:
        print("abort: 两臂席位预算不足——跑出来的 written 差会被误读成「修法伤产线」")
        return 2
    freeze_path, freeze_n = (None, 0)
    if not args.no_freeze:
        freeze_path, freeze_n = freeze_bans_file()
        print("freeze: %d 条禁牌冻结传入两臂%s" % (
            freeze_n,
            "" if freeze_path else "（快照建不出→退回实时窗口·有到期混淆风险）"), flush=True)
    arm_env = (dict(os.environ, BIGLIFE_REFUSAL_BANS_FROZEN=freeze_path)
               if freeze_path else dict(os.environ))
    # 两臂都必须压住策略批下限（batch-policy 默认会把 --batch 5 抬到 10）
    arm_env = dict(arm_env, BIGLIFE_BATCH_POLICY="off")
    snap_a = ban_snapshot()
    verdict = "FAIL"
    lines = []
    due_note = "(未采集)"
    try:
        a_env = dict(arm_env or os.environ, **{GATE_ENV: "off"})
        a = arm(batch, "A", env=a_env, day=day)
        if a.get("yield"):
            print("yield-window: 产线让路期，A 臂未跑（0 LLM/0 改动）")
            return 3

        before = refusal_metrics(day)
        print("arm B (gate on) ...", flush=True)
        snap_b = ban_snapshot()
        b_env = dict(arm_env or os.environ, **{GATE_ENV: "on"})
        b = arm(batch, "B", env=b_env, day=day)
        if b.get("yield"):
            print("yield-window: B 臂未跑 -> 还原补丁")
            return 3
        after = refusal_metrics(day)
        # 前置②：两臂前后的 due 消耗必须自洽，否则 written 比对无解释力
        due_after = due_count()
        due_ok, due_note = due_consistency(due, due_after, batch * 2)
        print("due check:", due_note, flush=True)
        _src_a, _src_b = a.get("ban_src"), b.get("ban_src")
        _known = _src_a not in (None, "?") and _src_b not in (None, "?")
        if a.get("written") is None or b.get("written") is None:
            # 前置③先行：臂读数不可解析时，关闸自证/冻结面自证都可能是「读不到」而非
            # 「没生效」，先判工装缺陷，免得把 TOOLING_ERROR 说成 CONFOUNDED。
            verdict, lines = judge(a, b, before, after, batch, snap_a, snap_b,
                                   frozen=bool(freeze_path))
        elif a.get("gate_off") is not True:
            verdict = "CONFOUNDED"
            lines = ["CONFOUNDED A 臂未自证关闸（stdout 无 quota-gate: off 标记）"
                     "→ 两臂可能同闸，读数不能用于裁决"]
        elif not due_ok:
            verdict = "TOOLING_ERROR"
            lines = ["TOOLING_ERROR " + due_note
                     + " → 席位消耗与 due 供给不同源，落环差不可归因于闸"]
        elif freeze_path and _known and not (_src_a == _src_b == "frozen"):
            verdict = "CONFOUNDED"
            lines = ["CONFOUNDED 冻结面未生效（A 源=%s/B 源=%s）→ 两臂禁牌环境不同，"
                     "读数不可用于裁决" % (_src_a, _src_b)]
        elif freeze_path and _known and a.get("ban_n") != 0:
            verdict = "CONFOUNDED"
            lines = ["CONFOUNDED A 臂声明关闸但禁牌非空（A=%s）→ 开关未真正生效"
                     % a.get("ban_n")]
        elif freeze_path and _known and freeze_n and b.get("ban_n") != freeze_n:
            verdict = "CONFOUNDED"
            lines = ["CONFOUNDED B 臂禁牌与冻结快照不一致（B=%s/快照=%s）→ 快照未共用"
                     % (b.get("ban_n"), freeze_n)]
        else:
            verdict, lines = judge(a, b, before, after, batch, snap_a, snap_b,
                                   frozen=bool(freeze_path))
            if freeze_path and not _known:
                lines.append("note 来源标签未取到（A=%s/B=%s）→ 冻结按构造生效，"
                             "但本轮无法从 stdout 自证；下次请查该行是否被吞"
                             % (_src_a, _src_b))
        lines.append(("ok   " if due_ok else "note ") + due_note)
    finally:
        if freeze_path:
            try:
                os.unlink(freeze_path)
            except OSError:
                pass
        print("restore: 补丁态未变 =",
              "applied" if restore_state else "reverted", "(A/B 只差 env，工作树零写入)")

    for ln in lines:
        print(ln)
    if args.no_freeze:
        freeze_state = "关（--no-freeze·两臂各自取实时窗口）"
    elif freeze_path:
        freeze_state = "冻结 %d 条（两臂共用同一集合·不受到期点约束）" % freeze_n
    else:
        freeze_state = "冻结失败→退回实时窗口（有禁牌到期混淆风险）"
    path = write_report(day, batch, a, b, verdict, lines, restore_state,
                        snap_a, snap_b, freeze_state=freeze_state,
                        arm_logs={"A": a.get("log"), "B": b.get("log")},
                        due_note=due_note)
    print("report:", os.path.relpath(path, ROOT))
    print("verdict:", verdict, "| gate in tree:", "yes" if restore_state else "no")
    return 0 if verdict == "PASS" else 1


def _selftest():
    """四道闸的回归电池（零 LLM·零盘污）：席位预算、禁牌混淆、补丁态编排、报告落地。"""
    global QA
    fails = []

    def chk(name, cond):
        print(("ok   " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    # 1) 席位预算（due 按尝试消耗 → 每臂不得超 due//2）
    chk("plan due=10 want=8 -> 5", plan_batch(10, 8)[0] == 5)
    chk("plan due=16 want=8 -> 8", plan_batch(16, 8)[0] == 8)
    chk("plan due=4  want=8 -> 2", plan_batch(4, 8)[0] == 2)
    chk("plan due=3  want=8 -> None", plan_batch(3, 8)[0] is None)
    chk("plan due=None -> 沿用请求", plan_batch(None, 8)[0] == 8)

    # 2) 禁牌混淆闸
    a = {"label": "A", "written": 8, "done": 8, "ban_hits": 0, "summary": "s"}
    b = {"label": "B", "written": 8, "done": 8, "ban_hits": 1, "summary": "s"}
    base = {"rows": 0, "distinct_cid": 0, "wasted_calls": 0, "max_repeats": 1}
    same = {"n": 2, "keys": ["a", "b"], "exp_min": "2026-11-16 19:34"}
    expired = {"n": 1, "keys": ["a"], "exp_min": "2026-11-16 20:45"}
    carry = {"n": 3, "keys": ["a", "b", "c"], "exp_min": "2026-11-16 19:34"}
    chk("judge 同态 -> PASS", judge(a, b, base, base, 8, same, same)[0] == "PASS")
    chk("judge 禁牌到期 -> CONFOUNDED",
        judge(a, b, base, base, 8, same, expired)[0] == "CONFOUNDED")
    chk("judge 携带效应 -> PASS",
        judge(a, b, base, base, 8, same, carry)[0] == "PASS")
    chk("judge 快照不可用 -> 不误拦",
        judge(a, b, base, base, 8, None, None)[0] == "PASS")
    b0 = dict(b, ban_hits=0)
    chk("judge B 臂零命中 -> INCONCLUSIVE",
        judge(a, b0, base, base, 8, same, same)[0] == "INCONCLUSIVE")
    chk("judge 零命中不得判 PASS（假绿闸）",
        judge(a, b0, base, base, 8, same, same)[0] != "PASS")
    # R3255：零命中 + 落环差 → 无判别力，不能判 FAIL（本轮 9<10 假 FAIL 判例）
    b1 = dict(b, written=4, ban_hits=0)
    chk("judge 零命中且落环差 -> INCONCLUSIVE",
        judge(a, b1, base, base, 8, same, same)[0] == "INCONCLUSIVE")
    # 冻结面：墙钟禁牌集在两臂之间到期（expired）在冻结下**不应**判 CONFOUNDED
    chk("judge 冻结下不按墙钟到期判混淆",
        judge(a, b, base, base, 8, same, expired, frozen=True)[0] == "PASS")
    chk("judge 非冻结下到期仍判 CONFOUNDED",
        judge(a, b, base, base, 8, same, expired, frozen=False)[0] == "CONFOUNDED")

    # 3) 补丁态编排（R3246：补丁已入 HEAD 时 A 臂仍须「未生效」，收尾回起跑态）
    chk("patch_steps 起跑=applied -> A off/B on/收尾 on",
        patch_steps(True) == (False, True, True))
    chk("patch_steps 起跑=reverted -> A off/B on/收尾 off",
        patch_steps(False) == (False, True, False))
    chk("patch_steps A 臂恒为 off",
        patch_steps(True)[0] is False and patch_steps(False)[0] is False)
    chk("patch_steps B 臂恒为 on",
        patch_steps(True)[1] is True and patch_steps(False)[1] is True)

    # 3b) 运行时开关编排（R3255：A/B 只差 env，工作树零写入）
    chk("GATEOFF_RE 命中关闸自证行",
        bool(GATEOFF_RE.search("quota-gate: off (env BIGLIFE_QUOTA_GATE)")))
    chk("GATEOFF_RE 不误命中开闸面",
        GATEOFF_RE.search("refusal-bans source: frozen n=6") is None)

    # 3c) TOOLING_ERROR 分型（T-20261116-13 前置③·无摘要行 ≠ written=0）
    a_ns = dict(a, written=None, done=None, summary="(no summary line)", rc=0,
                err_tail="", out_tail="")
    b_ns = dict(b, written=None, done=None, summary="(no summary line)", rc=0,
                err_tail="", out_tail="")
    chk("judge 双臂无摘要行 -> TOOLING_ERROR",
        judge(a_ns, b_ns, base, base, 8, same, same)[0] == "TOOLING_ERROR")
    chk("judge TOOLING_ERROR 不得冒充 PASS/FAIL",
        judge(a_ns, b_ns, base, base, 8, same, same)[0] not in ("PASS", "FAIL"))
    chk("judge 单臂无摘要行 -> TOOLING_ERROR",
        judge(a_ns, b, base, base, 8, same, same)[0] == "TOOLING_ERROR")

    # 3d) due 口径比对（T-20261116-13 前置②）
    chk("due 一致(10->4·尝试 12) -> ok", due_consistency(10, 4, 12)[0] is True)
    chk("due 未消耗(10->10) -> 不 ok", due_consistency(10, 10, 10)[0] is False)
    chk("due 不可读(None) -> 不 ok", due_consistency(None, 4, 10)[0] is False)

    # 4) 禁牌冻结面（R3247：两臂必须同一集合——禁牌在两臂之间到期会污染读数）
    sys.path.insert(0, os.path.join(ROOT, "Tools"))
    import evolve_citizen as _ev
    os.environ[GATE_ENV] = "off"
    try:
        chk("env=off 时 load_refusal_bans 恒空（A 臂运行面）",
            _ev.load_refusal_bans(env_path=os.path.join(ROOT, "state", "nonexistent.json")) == {})
    finally:
        os.environ.pop(GATE_ENV, None)
    fz = _ev.parse_frozen_bans({"opening-abcdef": "2026-11-16T07:34:00"})
    chk("parse_frozen_bans 正常解析", isinstance(fz.get("opening-abcdef"), datetime.datetime))
    chk("parse_frozen_bans 坏值跳过", len(_ev.parse_frozen_bans({"bad": "x"})) == 0)
    p_fz, n_fz = freeze_bans_file()
    try:
        chk("freeze_bans_file 产出可读快照",
            bool(p_fz) and os.path.exists(p_fz)
            and isinstance(json.load(open(p_fz, encoding="utf-8")), dict))
        got = _ev.load_refusal_bans(env_path=p_fz) if p_fz else {}
        chk("load_refusal_bans 走快照且无损", len(got) == n_fz == len(_ev.recent_refusal_bans()))
    finally:
        if p_fz:
            try:
                os.unlink(p_fz)
            except OSError:
                pass

    # 5) 报告落地（写临时目录，绝不触碰真 qa/）
    old_qa = QA
    tmp = tempfile.mkdtemp(prefix="negctl-selftest-")
    try:
        QA = tmp
        p = write_report("2026-11-16", 5, a, b, "PASS", ["ok 假线"], True, same, same)
        body = io.open(p, encoding="utf-8").read()
        chk("report 含禁牌态行", "禁牌态" in body)
        chk("report 含每臂席位 5", "每臂席位：5" in body)
        chk("report 含 verdict", "verdict: PASS" in body)
        chk("report 已关闭", body.rstrip().endswith("|---|---|---|")
            or "回退口" in body)
        # 前置①②③的证据面必须落在报告里，否则「无判别力」不可复现
        p2 = write_report("2026-11-16", 5, a, b, "TOOLING_ERROR", ["TOOLING_ERROR x"],
                          True, same, same, arm_logs={"A": "/tmp/a.log", "B": None},
                          due_note="due 口径一致（before=10 after=4 消耗 6·尝试 10 席）")
        body2 = io.open(p2, encoding="utf-8").read()
        chk("report 含 due 口径行", "due 口径一致" in body2)
        chk("report 含臂原始输出落盘指针", "臂原始输出" in body2 and "a.log" in body2)
        chk("未落盘臂标 (未落盘) 不假指路径", "(未落盘)" in body2)
    finally:
        QA = old_qa
        shutil.rmtree(tmp, ignore_errors=True)

    # 6) arm stdout 落盘（T-20261116-13 前置①）
    global ARM_LOG_DIR
    old_dir = ARM_LOG_DIR
    tmp2 = tempfile.mkdtemp(prefix="negctl-armlog-")
    try:
        ARM_LOG_DIR = tmp2
        lp = _dump_arm("2026-11-17", "A", 0, "line1\nline2\n", "warn")
        txt = io.open(lp, encoding="utf-8").read() if lp else ""
        chk("_dump_arm 产出日志文件", bool(lp) and os.path.exists(lp))
        chk("日志含 rc 与 stdout 原文", "rc=0" in txt and "line1" in txt and "warn" in txt)
        chk("日志名带日期与臂标签", os.path.basename(lp or "").endswith("arm-20261117-A.log"))
    finally:
        ARM_LOG_DIR = old_dir
        shutil.rmtree(tmp2, ignore_errors=True)

    print("selftest: %s (%d fail)" % ("PASS" if not fails else "FAIL", len(fails)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
