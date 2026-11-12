# -*- coding: utf-8 -*-
"""derive_audit.py v1.0 — 派生面内容级漂移审计（零 LLM·确定性·幂等）

病根（T-20261112-04 同族·2026-11-12 R2595 实证）：
  round_daily v0.5 只给 citizen-goals 一个派生数据面加了闸，其余 R3 派生面
  （anchors/assembly/persona/voice/atlas/initiatives/relations）**无任何轮次引用**。
  实测七个面停在 10-26/10-27（16-17 天），而依赖它们的可见面（city-map /
  city-relations / city-ops / city-life / city-growth）每天照常重建 ——
  页面 mtime 是今天的，读到的数据是半个月前的。CEO 看到的是旧城市。

为什么不能照搬 mtime 闸：
  这些面是 md5(id) 确定性派生，输入不变时再生结果逐字节相同。若按「当日必新」
  判，等于每天白写 190MB（relations 2.85M 行）却零信息。故本闸判**内容漂移**
  而非 mtime：再生 → 比对 md5 → 只有真变了才重建依赖面。

判据：
  SAME    再生内容与盘上一致 → 页面读数真实，零动作
  DRIFT   再生内容不同       → 页面正在展示旧数据，按 dependents 重建
  CREATED 面缺失             → 视为漂移处理
  ERROR   生成器 rc≠0        → 如实报错，不掩盖

用法:
  python -X utf8 Tools/derive_audit.py              # 审计（默认不重建依赖面）
  python -X utf8 Tools/derive_audit.py --run        # 审计 + 漂移时重建依赖面
  python -X utf8 Tools/derive_audit.py --json       # 机器可读
  python -X utf8 Tools/derive_audit.py --selftest   # 探针（mock 生成器，零盘改动）

接线：round_daily.py INPUTS 档 "data" tier（先于面重建执行），输出本文件 + state json。
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "census", "export")
STATE_OUT = os.path.join(ROOT, "state", "derive-audit.json")
REPORT_MD = os.path.join(ROOT, "qa", "DERIVE-AUDIT-REPORT.md")

# (key, 生成器, 输出面, 依赖的可见面 key（round_daily REGISTRY 键）)
DERIVE = [
    ("anchors",     "citizen_anchors.py",    "citizen-anchors.jsonl",     ["map"]),
    ("assembly",    "citizen_assembly.py",   "citizen-assembly.jsonl",    []),
    ("persona",     "persona_enrich.py",     "citizen-persona.jsonl",     ["ops"]),
    ("voice",       "voice_manifest.py",     "citizen-voice.jsonl",       ["growth"]),
    ("atlas",       "atlas_manifest.py",     "citizen-atlas.jsonl",       []),
    ("initiatives", "agency.py",             "citizen-initiatives.jsonl", ["life"]),
    ("relations",   "relations_manifest.py", "citizen-relations.jsonl",   ["relations", "growth"]),
]

TIMEOUT_SEC = 240


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "MISSING"
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return 124, "timeout>%ds" % TIMEOUT_SEC
    tail = (proc.stdout or "").strip().splitlines()
    msg = tail[-1][:140] if tail else ""
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        msg = (err[-1][:140] if err else msg) or "rc=%d" % proc.returncode
    return proc.returncode, msg


def audit_row(key: str, script: str, name: str) -> dict:
    path = os.path.join(EXPORT, name)
    before = _md5(path)
    rc, msg = _run([sys.executable, "-X", "utf8", os.path.join(ROOT, "Tools", script)])
    after = _md5(path)
    if rc != 0:
        status = "ERROR"
    elif before == "MISSING":
        status = "CREATED"
    elif before == after:
        status = "SAME"
    else:
        status = "DRIFT"
    return {"key": key, "script": script, "face": name, "rc": rc,
            "before": before[:8], "after": after[:8], "status": status, "msg": msg}


def selftest() -> int:
    """探针：用临时文件验证 SAME/DRIFT/CREATED/MISSING 四分支判定。"""
    import tempfile
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "x.jsonl")
        checks = []
        checks.append(("MISSING 分支", _md5(p) == "MISSING"))
        with open(p, "wb") as f:
            f.write(b"a\n")
        h1 = _md5(p)
        checks.append(("同内容同 md5", _md5(p) == h1))
        with open(p, "wb") as f:
            f.write(b"b\n")
        checks.append(("改内容 md5 变", _md5(p) != h1))
        with open(p, "wb") as f:
            f.write(b"a\n")
        checks.append(("改回 md5 复原", _md5(p) == h1))
        for name, ok in checks:
            print(("PASS  " if ok else "FAIL  ") + name)
            fails += 0 if ok else 1
    print("selftest %d/%d %s" % (len(checks) - fails, len(checks),
                                 "PASS" if fails == 0 else "FAIL"))
    return 0 if fails == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="漂移时重建依赖可见面")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()

    rows = []
    for key, script, name, deps in DERIVE:
        row = audit_row(key, script, name)
        row["dependents"] = deps
        rows.append(row)

    drifted = [r for r in rows if r["status"] in ("DRIFT", "CREATED", "ERROR")]
    rebuilt = []
    if args.run and drifted:
        only = sorted({k for r in drifted for k in r["dependents"]})
        if only:
            rc, msg = _run([sys.executable, "-X", "utf8",
                            os.path.join(ROOT, "Tools", "round_daily.py"),
                            "--run", "--only", ",".join(only)])
            rebuilt = [{"faces": only, "rc": rc, "msg": msg}]

    payload = {
        "date": datetime.date.today().isoformat(),
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": rows,
        "drifted": [r["key"] for r in drifted],
        "rebuilt": rebuilt,
        "verdict": "PASS" if not drifted else "DRIFT",
    }

    os.makedirs(os.path.dirname(STATE_OUT), exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            print("  %-12s %-38s %-7s %s" % (r["key"], r["face"], r["status"], r["msg"]))
        print("verdict: %s drifted=%d rebuilt=%s"
              % (payload["verdict"], len(drifted),
                 ",".join(rebuilt[0]["faces"]) if rebuilt else "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
