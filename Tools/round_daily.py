# -*- coding: utf-8 -*-
"""确定性日更聚合器（零 LLM·幂等·单轮至多一次）。

病根（T-20261112-02）：本仓 23 个可见面构建器各自为战，没有任何轮次规程
引用它们——city-rumors 自 2026-10-27 起静默停更 16 天，同批 city-voices /
city-ops / city-relations / city-chronicle / resident-gallery 等 18 个面
同样是 10-27 的旧图，CEO 看到的是半个月前的城市。修法=把「哪些面必须当日
新鲜」写成唯一登记表，轮末一次调用即知其陈旧并就地重建。

两个档：
  daily  当日必新（日报/流言/城市生活/看板/索引）——输出 mtime 非当日即陈旧
  faces  结构性面（城区志/名人录/物件志/居民陈列…）——输出 mtime 超 1 日即陈旧
  input  生成器当日喂料（街区母题/流言链）——dated 文件缺失或非当日即补建

用法:
  python -X utf8 Tools/round_daily.py --check            # 只体检，不重建
  python -X utf8 Tools/round_daily.py --run              # 重建陈旧面
  python -X utf8 Tools/round_daily.py --run --all        # 全部重建（含当日已新）
  python -X utf8 Tools/round_daily.py --run --only rumors,today
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
STATE_OUT = os.path.join(ROOT, "state", "round-daily.json")

# key, tier, script, outputs
REGISTRY = [
    ("today",      "daily", "build_daily_issue.py",       ["city-today.html"]),
    ("rumors",     "daily", "build_rumors.py",            ["city-rumors.html"]),
    ("life",       "daily", "build_city_life.py",         ["city-life.html"]),
    ("dashboard",  "daily", "build_city_dashboard.py",    ["city-dashboard.html"]),
    ("voices",     "faces", "build_city_voices.py",       ["city-voices.html"]),
    ("coverage",   "faces", "build_coverage.py",          ["city-coverage.html"]),
    ("ops",        "faces", "build_city_ops.py",          ["city-ops.html"]),
    ("relations",  "faces", "build_city_relations.py",    ["city-relations.html"]),
    ("chronicle",  "faces", "build_chronicle.py",         ["city-chronicle.html"]),
    ("districts",  "faces", "build_district_chronicle.py", ["city-districts.html"]),
    ("dossiers",   "faces", "build_city_dossiers.py",     ["city-dossiers.html"]),
    ("objects",    "faces", "build_object_atlas.py",      ["city-objects.html"]),
    ("map",        "faces", "build_city_map.py",          ["city-map.html"]),
    ("gallery",    "faces", "build_resident_gallery.py",  ["resident-gallery.html"]),
    ("goals",      "faces", "build_city_goals.py",        ["city-goals.html"]),
    ("gene_ledger", "faces", "build_gene_ledger.py",      ["gene-ledger.html"]),
    ("ring_picks", "faces", "build_ring_picks.py",        ["city-ring-picks.html"]),
    ("growth",     "faces", "build_growth_gallery.py",    ["city-growth.html"]),
    ("meets",      "faces", "build_city_meets.py",        ["city-meets.html"]),
    # 索引必须最后跑：它登记的是本轮重建后的文件清单
    ("index",      "index", "build_export_index.py",      ["index.html"]),
]

# v0.2 (2026-11-12 R2571): 输入档 —— 面新鲜不等于喂料新鲜。
# 病根补记（T-20261112-01/02）：面重建了，但年轮线要吃的「当日文件」可能不存在
# （换日第一批、让路窗内年轮不跑、跨机首跑都常见），居民就只剩天气可锚。
# 输入档判据=当日 dated 文件存在且 mtime 是今天；缺失即调确定性生成器补（零 LLM）。
INPUTS = [
    ("life_motifs", "input", "city_life_events.py",       ["events/life/{date}.jsonl"]),
    ("rumor_chain", "input", "build_rumors.py",           ["cognition/rumors/rumors-{date}.jsonl"]),
]

TIMEOUT_SEC = 240


def _out_paths(entry) -> list[str]:
    _key, tier, _script, names = entry
    base = ROOT if tier == "input" else EXP
    day = datetime.date.today().isoformat()
    return [os.path.join(base, n.replace("{date}", day)) for n in names]


def _age_days(path: str) -> float | None:
    if not os.path.exists(path):
        return None
    return (time.time() - os.path.getmtime(path)) / 86400.0


def _is_stale(entry, now_date: datetime.date, out_paths: list[str]) -> tuple[bool, str]:
    _key, tier, _script, _names = entry
    ages = []
    for p in out_paths:
        if not os.path.exists(p):
            return True, "missing:" + os.path.basename(p)
        ages.append(_age_days(p) or 0.0)
    age = max(ages)
    mdate = datetime.date.fromtimestamp(
        max(os.path.getmtime(p) for p in out_paths))
    if tier in ("daily", "input"):
        stale = mdate != now_date
        return stale, ("outdated:%sd" % int(age) if stale else "fresh")
    stale = age > 1.0
    return stale, ("outdated:%sd" % int(age) if stale else "fresh")


def _run_one(script: str) -> tuple[int, str]:
    cmd = [sys.executable, "-X", "utf8", os.path.join(ROOT, "Tools", script)]
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return 124, "timeout>%ds" % TIMEOUT_SEC
    tail = (proc.stdout or "").strip().splitlines()
    msg = tail[-1][:160] if tail else ""
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        msg = (err[-1][:160] if err else msg) or "rc=%d" % proc.returncode
    return proc.returncode, msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只体检（默认行为）")
    ap.add_argument("--run", action="store_true", help="重建陈旧面")
    ap.add_argument("--all", action="store_true", help="重建全部（含已新鲜）")
    ap.add_argument("--only", default=None, help="只处理这些 key（逗号分隔）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    only = set(x.strip() for x in args.only.split(",") if x.strip()) if args.only else None
    today = datetime.date.today()
    # 输入档在前：年轮线要吃的当日文件优先补齐，再重建可见面
    entries = [e for e in (INPUTS + REGISTRY) if (only is None or e[0] in only)]

    plan = []
    for e in entries:
        outs = _out_paths(e)
        stale, why = _is_stale(e, today, outs)
        plan.append({"key": e[0], "tier": e[1], "script": e[2],
                     "outputs": e[3], "stale": stale, "why": why})

    results = []
    ran = 0
    for item in plan:
        if not args.run:
            results.append(dict(item, action="skipped-check", rc=None, msg=""))
            continue
        if item["tier"] == "index":
            # 索引登记的是本轮重建后的文件清单：只有真有面重建时才需要重排
            if not (args.all or any(r.get("action") == "rebuilt" for r in results)):
                results.append(dict(item, action="skipped-nochange", rc=None, msg=""))
                continue
        elif not (args.all or item["stale"]):
            results.append(dict(item, action="skipped-fresh", rc=None, msg=""))
            continue
        rc, msg = _run_one(item["script"])
        ran += 1
        results.append(dict(item, action="rebuilt" if rc == 0 else "failed",
                            rc=rc, msg=msg))

    payload = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "run" if args.run else "check",
        "ran": ran,
        "stale": [r["key"] for r in results if r["stale"]],
        "failed": [r["key"] for r in results if r["action"] == "failed"],
        "items": results,
    }
    os.makedirs(os.path.dirname(STATE_OUT), exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")

    if args.json:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
        return 0 if not payload["failed"] else 1

    print("== round_daily (%s) ==" % payload["mode"])
    for r in results:
        print("  %-12s %-7s %-9s %s" % (r["key"], r["tier"], r["action"], r["why"]))
    print("stale=%d ran=%d failed=%d" % (len(payload["stale"]), ran, len(payload["failed"])))
    if payload["failed"]:
        print("FAILED: " + ",".join(payload["failed"]))
        return 1
    print("verdict: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
