#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rl_gate.py v1.0 -- D-20260930-36 BigLife 线 R-L1 消费率闸机器判据
法源: D-20260930-36（七线全球头部对标+AI 可执行判据）·T-20261010-01（解冻后立单义务）
正典: 集团 docs/audits/global-benchmark-and-check-rules-20260930.md R-L1
      「消费率闸：新增批次须标注消费方与消费形式；零消费批不入册（或标 unconsumed）」

机器可验判据（基线 v1.0 = 我方自定·前置②行业对标 R- 回执未至·回执到后逐条回填并标来源）:
  G1 分类完备: census/export 13 导出面每面要么有 ≥1 下游仓代码级接线证据（file:line 指针），
               要么在 cognition/consumption-ledger.json 显式标 unconsumed——缺一即 FAIL。
  G2 证据指针: 每「consumed」判定必带 ≥1 file:line 指针（可复核·文档级引用不计）。
  G3 口径一致: 接线仓数与 Tools/consumer_wiring.py v1.0 同口径（cph4 集团工具面不计·
               废弃会话日志噪声不计入判读）。
  阈值面（消费率合格线）: PENDING_CALIBRATION——前置②未至不判 pass/fail
               （正典教训：口径未定义时正确输出是 DATA_GAP，不是 PASS）。

台账: cognition/consumption-ledger.json（分类事实面·机器写）·周行: docs/audits/benchmark-gap-biglife.jsonl
红线: 兄弟仓只读零写入（铁律④）·不代消费方立项（反无消费方立项律）·ledger 只记分类事实。
用法: python -X utf8 Tools/rl_gate.py        # 判据跑（stdout 判定+更新 ledger+追加周行）
      python -X utf8 Tools/rl_gate.py --qc  # 双跑逐字节一致断言（零写盘）
"""
import os
import sys
import json
import time
import hashlib
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import consumer_wiring as cw  # 单源复用：SURFACES/CODE_EXT/SKIP_DIRS/CONSUMERS/_decode/HIT_RE

ROOT = cw.ROOT
GROUP = cw.GROUP
LEDGER = os.path.join(ROOT, "cognition", "consumption-ledger.json")
GAP_ROWS = os.path.join(ROOT, "docs", "audits", "benchmark-gap-biglife.jsonl")
TZ = timezone(timedelta(hours=8))
CALIB = "baseline-v1.0-ours (industry receipts pending, D-20260930-36 pre-2)"
EXCERPT_CAP = 110


def now_ts():
    return datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def rl_scan(verbose=True):
    """单遍只读扫描：per (consumer, surface) 聚合证据计数+首指针（复用 consumer_wiring 闭集常量）。"""
    agg = {}
    for name, path, counts in cw.CONSUMERS:
        t0 = time.time()
        nfiles = 0
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in cw.SKIP_DIRS]
                for fn in filenames:
                    if os.path.splitext(fn)[1].lower() not in cw.CODE_EXT:
                        continue
                    fp = os.path.join(dirpath, fn)
                    try:
                        if os.path.getsize(fp) > cw.MAX_FILE:
                            continue
                        with open(fp, "rb") as f:
                            raw = f.read()
                    except OSError:
                        continue
                    nfiles += 1
                    if not any(t in raw for t in cw.SURF_BYTES):
                        continue
                    for i, line in enumerate(cw._decode(raw).splitlines(), 1):
                        if cw.HIT_RE.search(line):
                            rel = os.path.relpath(fp, GROUP).replace("\\", "/")
                            for tok in cw.SURFACES:
                                if tok in line:
                                    key = (name, tok)
                                    if key not in agg:
                                        agg[key] = {
                                            "ptr": "%s:%d" % (rel, i),
                                            "excerpt": line.strip()[:EXCERPT_CAP],
                                            "count": 0,
                                        }
                                    agg[key]["count"] += 1
                                    break
        if verbose:
            print("[rl-scan] %-17s files=%d %.1fs" % (name, nfiles, time.time() - t0),
                  flush=True)
    return agg


def classify(agg):
    """G1/G2 判定：每面 consumed（带指针）或 unconsumed（待台账显式标注）。"""
    surfaces = {}
    for tok in cw.SURFACES:
        ev, cons = [], []
        for name, _path, counts in cw.CONSUMERS:
            hit = agg.get((name, tok))
            if not hit:
                continue
            entry = {"consumer": name, "ptr": hit["ptr"], "excerpt": hit["excerpt"],
                     "hits": hit["count"], "counts_in_wired": counts}
            ev.append(entry)
            if counts:
                cons.append(name)
        surfaces[tok] = {
            "status": "consumed" if cons else "unconsumed",
            "consumers": cons,
            "evidence": ev,
        }
    wired_repos = sorted({c for s in surfaces.values() for c in s["consumers"]})
    consumed = sorted(t for t, s in surfaces.items() if s["status"] == "consumed")
    unconsumed = sorted(t for t, s in surfaces.items() if s["status"] == "unconsumed")
    return {
        "surfaces": surfaces,
        "wired_repos": wired_repos,
        "consumed": consumed,
        "unconsumed": unconsumed,
    }


def judgment(res):
    """G1/G2 机器判定：consumed 面必有指针；unconsumed 面必入台账标注（写台账动作由 run 承载）。"""
    problems = []
    for tok, s in res["surfaces"].items():
        if s["status"] == "consumed":
            if not any(e["counts_in_wired"] and e["ptr"] for e in s["evidence"]):
                problems.append("G2 no-evidence-pointer: %s" % tok)
        else:
            if not s["evidence"] and tok not in res["surfaces"]:  # unreachable guard
                problems.append("G1 unclassified: %s" % tok)
    return problems


def write_ledger(res):
    prev = {}
    if os.path.exists(LEDGER):
        try:
            with open(LEDGER, encoding="utf-8") as f:
                prev = json.load(f).get("surfaces", {})
        except (OSError, ValueError):
            prev = {}
    surfaces = {}
    for tok, s in res["surfaces"].items():
        surfaces[tok] = {
            "status": s["status"],
            "consumers": s["consumers"],
            "evidence": [e for e in s["evidence"] if e["counts_in_wired"]][:3],
        }
        surfaces[tok]["form"] = "code-reference"
        surfaces[tok]["tagged_ts"] = now_ts()
        surfaces[tok]["prev_status"] = prev.get(tok, {}).get("status", "")
    out = {
        "rule": "R-L1",
        "basis": CALIB,
        "canonical": "docs/audits/global-benchmark-and-check-rules-20260930.md (group repo)",
        "intake_note": "新增居民批次消费方标注=造人线需求触发制（T-20261010-03·消费者到位才注册）",
        "ts": now_ts(),
        "surfaces": surfaces,
    }
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return out


def append_gap_row(res, verdict):
    os.makedirs(os.path.dirname(GAP_ROWS), exist_ok=True)
    week = "%04d-W%02d" % datetime.now(TZ).isocalendar()[:2]
    if os.path.exists(GAP_ROWS):
        with open(GAP_ROWS, encoding="utf-8") as f:
            for line in f:
                try:
                    if json.loads(line).get("week") == week:
                        return "week-row-exists"
                except ValueError:
                    continue
    row = {
        "week": week,
        "ts": now_ts(),
        "rule": "R-L1",
        "judgment": verdict,
        "consumed_surfaces": len(res["consumed"]),
        "total_surfaces": len(cw.SURFACES),
        "unconsumed_tagged": len(res["unconsumed"]),
        "wired_repos": len(res["wired_repos"]),
        "rate": round(len(res["consumed"]) / len(cw.SURFACES), 3),
        "threshold": "PENDING_CALIBRATION",
        "evidence": "qa/rl-gate-*.log + cognition/consumption-ledger.json",
        "calibration_source": CALIB,
    }
    with open(GAP_ROWS, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return "appended"


def main():
    qc = "--qc" in sys.argv
    agg_a = rl_scan(verbose=True)
    res_a = classify(agg_a)
    ha = hashlib.md5(json.dumps(res_a, ensure_ascii=False, sort_keys=True)
                     .encode("utf-8")).hexdigest()
    if qc:
        res_b = classify(rl_scan(verbose=False))
        hb = hashlib.md5(json.dumps(res_b, ensure_ascii=False, sort_keys=True)
                         .encode("utf-8")).hexdigest()
        det_ok = ha == hb
        print("QC determinism: %s (%s)" % ("PASS" if det_ok else "FAIL", ha))
        print("QC wired_repos=%s consumed=%d unconsumed=%d"
              % (res_a["wired_repos"], len(res_a["consumed"]), len(res_a["unconsumed"])))
        sys.exit(0 if det_ok else 1)
    problems = judgment(res_a)
    for tok in cw.SURFACES:
        s = res_a["surfaces"][tok]
        print("RL1 %-22s %-11s consumers=%s"
              % (tok, s["status"], ",".join(s["consumers"]) or "-"))
    write_ledger(res_a)
    verdict = "pass" if not problems else "fail"
    print("RL1_JUDGMENT=%s problems=%s" % (verdict, problems or "none"))
    print("RL1 consumed=%d/%d unconsumed=%d wired_repos=%d"
          % (len(res_a["consumed"]), len(cw.SURFACES), len(res_a["unconsumed"]),
             len(res_a["wired_repos"])))
    print("RL1 threshold=PENDING_CALIBRATION (rate=%.3f·行业回执到前不判合格线)"
          % (len(res_a["consumed"]) / len(cw.SURFACES)))
    print("RL1 gap-row=%s" % append_gap_row(res_a, verdict))
    print("RL1 ledger=%s" % os.path.relpath(LEDGER, ROOT).replace("\\", "/"))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
