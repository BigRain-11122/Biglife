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
  data   派生物面（惊奇日志…）——输出在仓内非 export 目录，同样按当日判新鲜

用法:
  python -X utf8 Tools/round_daily.py --check            # 只体检，不重建
  python -X utf8 Tools/round_daily.py --run              # 重建陈旧面
  python -X utf8 Tools/round_daily.py --run --all        # 全部重建（含当日已新）
  python -X utf8 Tools/round_daily.py --run --only rumors,today
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
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
    # v0.3 (2026-11-12 R2573): 补登记三个「有生成器、有页面、无任何轮次引用」的沉默断供面。
    # 病根同 T-20261112-02：city-lexicon.html 停更 15.7 天无人发现；
    # city-ring-quality / city-ring-trend 只靠偶发手工跑活着，断供只是时间问题。
    # 三者均确定性零 LLM，可直接纳入日更闸。
    ("lexicon",     "faces", "city_lexicon.py",           ["city-lexicon.html"]),
    ("ring_quality", "faces", "ring_simile_audit.py",     ["city-ring-quality.html"]),
    ("ring_trend",  "daily", "ring_quality_trend.py",     ["city-ring-trend.html"]),
    # v0.7 (2026-11-12 R2606): 覆盖面核查抓出两个「被可见面链接、却无任何轮次引用」的面
    # ——同 T-20261112-02 病根第四/五例。判据=逐个 Tools 生成器 × export html 反查，
    # 不看 mtime（mtime 只会告诉你已经烂了，不会告诉你会烂）。
    #   a) 社交图谱：index.html 卡片直接展示「10-27 10:15 更新」，停更 17 天；
    #      且默认输出在 census/ 根而非 export/，故用 ROOT 相对路径。
    #   b) 相遇候选单：city-coverage / city-ops / index 三处链接，今晚相遇轮要照单开工，
    #      断了等于让居民反复配同一批人。
    ("social_graph", "rootface", "build_social_graph.py",   ["census/city-social-graph.html"]),
    ("meet_candidates", "daily", "meet_candidates.py",      ["meet-candidates.jsonl", "meet-candidates.html"]),
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
    # v0.3 (2026-11-12 R2573): 派生物面 —— 从 FluxVerse world-events 只读派生，
    # 确定性零 LLM，却因无任何轮次引用而停更 16.8 天（至 10-26 的最后一行）。
    # 输出在 cognition/ 而非 census/export/，故走 data 档（base=ROOT，判当日）。
    ("surprise", "data", "surprise_log.py",               ["cognition/surprise-log.jsonl"], ["--feed"]),
    # v0.4 (2026-11-12): 互聊台账接线（T-20261112-03 修法②）——同 surprise 病根，
    # 另有「需外部喂源」一层：daily_interchat.py 取当日 rumors 首条链作源，
    # 无源即 SKIP 且不刷 mtime（源断供仍如实 stale）。
    ("interchat", "data", "daily_interchat.py",           ["cognition/interchat-ledger.jsonl"]),
    # v0.5 (2026-11-12): 派生数据面 = 「页面新鲜但数据陈旧」更深一层病灶。
    # 病根实证：goals 面当日重建（10:06），但它读的 census/export/citizen-goals.jsonl
    # 停在 10-26（16.8 天）——CEO 看到的「目标系统」整页是上月口径（55 行 month=2026-10），
    # 页面 mtime 天天新，内容却没人校验。故把派生数据本身纳入日更闸：
    # goals.py --regen 确定性零 LLM（同 (cid, month, date) 双跑逐字节一致），
    # 每日再生 → 跨月自动换 target/steps，页面随之反映当月。
    ("citizen_goals", "data", "goals.py",                 ["census/export/citizen-goals.jsonl"], ["--regen"]),
    # v0.6 (2026-11-12 R2595): 派生面漂移审计 —— 把 v0.5 只覆盖 goals 的病根补全。
    # 实证：七个 R3 派生面停在 10-26/10-27（16-17 天），而 city-map/relations/ops/
    # life/growth 每天照常重建 ⇒ 页面 mtime 是今天、数据是半个月前。
    # 判据用内容漂移而非 mtime：md5(id) 确定性派生，输入不变再生逐字节相同，
    # 按「当日必新」判等于每天白写 190MB（relations 2.85M 行）却零信息。
    # 漂移时才重建 dependents；稳定日仅 16s 盘读零页面动作。
    ("derive_audit", "data", "derive_audit.py",           ["state/derive-audit.json"], ["--run"]),
]

TIMEOUT_SEC = 240


def _out_paths(entry) -> list[str]:
    _key, tier, _script, names = entry[:4]
    base = ROOT if tier in ("input", "data") else EXP
    day = datetime.date.today().isoformat()
    out = []
    for n in names:
        n = n.replace("{date}", day)
        # v0.7 (2026-11-12): 少数面故意落在 export 之外（社交图谱=census/ 根），
        # 索引里按 ../ 相对链接。带目录分隔符的名字一律按 ROOT 相对解析，
        # 否则会被拼成 export/census/... 的幻影路径而永远判 missing。
        out.append(os.path.join(ROOT, n) if "/" in n else os.path.join(base, n))
    return out


def _age_days(path: str) -> float | None:
    if not os.path.exists(path):
        return None
    return (time.time() - os.path.getmtime(path)) / 86400.0


# 页面内嵌「数据截至」必须等于来源文件 mtime。mtime 判据只看页面重写时间，
# 源头未刷新时页面会被误判为当日新鲜（2026-11-12 看板 456 vs 真值 465 实锚）。
SNAPSHOT_SOURCES = {"city-dashboard.html": "citizens-light.jsonl"}
SNAPSHOT_TS_RE = re.compile(r"数据截至\s*(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)")


def _content_stale(out_paths: list[str]) -> str | None:
    for p in out_paths:
        src_name = SNAPSHOT_SOURCES.get(os.path.basename(p))
        if not src_name:
            continue
        src = os.path.join(EXP, src_name)
        if not (os.path.exists(p) and os.path.exists(src)):
            continue
        try:
            with io.open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        m = SNAPSHOT_TS_RE.search(text)
        if not m:
            continue
        want = datetime.datetime.fromtimestamp(
            os.path.getmtime(src)).strftime("%Y-%m-%d %H:%M:%S")
        if m.group(1) != want:
            return "content-stale:src=%s" % want
    return None


def _is_stale(entry, now_date: datetime.date, out_paths: list[str]) -> tuple[bool, str]:
    _key, tier, _script, _names = entry[:4]
    ages = []
    for p in out_paths:
        if not os.path.exists(p):
            return True, "missing:" + os.path.basename(p)
        ages.append(_age_days(p) or 0.0)
    age = max(ages)
    mdate = datetime.date.fromtimestamp(
        max(os.path.getmtime(p) for p in out_paths))
    if tier in ("daily", "input", "data"):
        stale = mdate != now_date
        if not stale:
            drift = _content_stale(out_paths)
            if drift:
                return True, drift
        return stale, ("outdated:%sd" % int(age) if stale else "fresh")
    stale = age > 1.0
    return stale, ("outdated:%sd" % int(age) if stale else "fresh")


def _run_one(script: str, extra=None) -> tuple[int, str]:
    cmd = [sys.executable, "-X", "utf8", os.path.join(ROOT, "Tools", script)]
    cmd.extend(extra or [])
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
                     "outputs": e[3], "stale": stale, "why": why,
                     "extra": (list(e[4]) if len(e) > 4 else [])})

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
        rc, msg = _run_one(item["script"], item.get("extra"))
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
    # v0.7 (2026-11-12): 体检必须诚实——上面那行 stale= 是「跑之前」的口径，
    # 旧版无论剩多少陈旧都印 verdict: PASS（社交图谱就是这样烂了 17 天没人发现：
    # 索引卡片写着 10-27，而闸每次都说 PASS）。改为跑完后再判一次真实余量，
    # 余量为零才 PASS；否则 STALE + rc=2（同 ring_material_check 的未达码约定）。
    remaining = []
    for e in entries:
        still, why = _is_stale(e, today, _out_paths(e))
        if still:
            remaining.append("%s(%s)" % (e[0], why))
    if remaining:
        print("verdict: STALE remaining=%d %s" % (len(remaining), ",".join(remaining)))
        return 2
    print("verdict: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
