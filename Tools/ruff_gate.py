#!/usr/bin/env python3
"""ruff_gate.py -- T-20260929-07 ruff advisory incremental lint gate (OSS P-2026-09-26-08).

Advisory gate for pre-delivery .py files:
  version anchor  = uvx ruff@0.16.9 (temp exec, zero permanent dependency)
  curated rules   = F401,F811,F841,SIM115,RUF059 (dead-code/redef/unused-var/
                    open-without-with/unused-unpack -- real-signal classes)
  increment face  = new/changed .py in working tree vs HEAD; --since <date>
                    widens to .py files touched by commits since that date
  advisory policy = report hits for fix-or-log; NEVER blocks delivery (exit 0)
  determinism     = zero LLM, pure static; last run snap -> state/ruff-gate-last.json
"""
import datetime
import json
import pathlib
import subprocess
import sys

RULES = "F401,F811,F841,SIM115,RUF059"
RUFF_CMD = ["uvx", "ruff@0.16.9", "check", "--select", RULES, "--output-format", "concise"]
ROOT = pathlib.Path(__file__).resolve().parent.parent
LAST = ROOT / "state" / "ruff-gate-last.json"


def git(args):
    r = subprocess.run(["git", "-C", str(ROOT)] + args,
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout


def collect(since=None, explicit=None):
    if explicit:
        return sorted(f for f in explicit if f.endswith(".py") and (ROOT / f).exists())
    files = set()
    for line in git(["diff", "--name-only", "HEAD"]).splitlines():
        p = line.strip()
        if p.endswith(".py"):
            files.add(p)
    for line in git(["status", "--porcelain"]).splitlines():
        p = line[3:].strip().strip('"').split(" -> ")[-1]
        if p.endswith(".py"):
            files.add(p)
    if since:
        for line in git(["log", "--name-only", "--pretty=format:", "--since=" + since]).splitlines():
            p = line.strip()
            if p.endswith(".py"):
                files.add(p)
    return sorted(f for f in files if (ROOT / f).exists())


def main():
    args = sys.argv[1:]
    since = None
    explicit = []
    i = 0
    while i < len(args):
        if args[i] == "--since":
            since = args[i + 1]
            i += 2
        else:
            explicit.append(args[i])
            i += 1
    targets = collect(since, explicit or None)
    snap = {"ts": datetime.datetime.now().isoformat(timespec="seconds"),
            "since": since, "files": targets, "hits": [], "verdict": "SKIP"}
    if not targets:
        print("ruff_gate: incremental face empty (no new/changed .py) -- SKIP")
    else:
        r = subprocess.run(RUFF_CMD + targets, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(ROOT))
        # ruff exit semantics: 0 = no violations, 1 = findings; stdout line "All
        # checks passed!" on exit 0 must not be counted as a finding.
        hits = [l for l in (r.stdout or "").splitlines() if l.strip() and ":" in l]
        if r.returncode == 0:
            snap["verdict"] = "CLEAN"
            print(f"ruff_gate: {len(targets)} file(s) CLEAN (rules={RULES})")
        elif r.returncode == 1:
            snap["verdict"] = "ADVISORY"
            snap["hits"] = hits
            print(f"ruff_gate: ADVISORY {len(hits)} hit(s) over {len(targets)} file(s) -- fix or log, delivery not blocked")
            for h in hits:
                print("  " + h)
        else:
            snap["verdict"] = "ERROR"
            snap["stderr"] = (r.stderr or r.stdout or "").strip()
            print("ruff_gate: engine error -> " + snap["stderr"])
    LAST.parent.mkdir(exist_ok=True)
    LAST.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
