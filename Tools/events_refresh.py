#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Refresh event shards from cards, then run the replay gate in one step.

Why (R-20261023-scan-silicon-city action 1): cards are the source of truth and
`events/` is regenerable, but nothing re-derives the shards after a ring batch,
so `events_replay.py` reports stale mismatches (first live run: 700 mismatches
on 10091 cards). This tool closes that loop so the gate measures correctness
instead of staleness.

Usage:
  python -X utf8 Tools/events_refresh.py           # derive + replay
  python -X utf8 Tools/events_refresh.py --gate    # same, exit 1 on replay FAIL
"""
import argparse, datetime, json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent


RESERVED_OK = ("C-00001", "C-00002", "C-00003")  # 荣誉席：CODEX §十二 4 明规不进叙事事件流

CHRONICLE = ROOT / "cognition" / "city-chronicle.jsonl"
CHRONICLE_MAX_GAP_DAYS = 1


def chronicle_freshness():
    """城谱新鲜度自愈：断供 > 1 天就补 feed 一次。

    Why: 城市年谱的写入只挂在人工/特定轮的 `city_chronicle.py --feed` 上，没有任何
    每轮必跑的钩子；2026-10-26 → 11-12 静默断供 15 天，集团复盘按「零当日新行」
    计违例，而所有闸仍绿。把补喂挂到本工具（协议每轮必跑）让缺席自己变成产物，
    而不是等下一次人眼发现。失败不阻断回放闸（返回 rc 仅供日志）。
    """
    try:
        if not CHRONICLE.exists():
            return 0, "chronicle: absent"
        last = ""
        with open(CHRONICLE, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    last = json.loads(line).get("date") or last
                except Exception:
                    pass
        today = datetime.date.today()
        if last:
            gap = (today - datetime.date.fromisoformat(last)).days
            if gap <= CHRONICLE_MAX_GAP_DAYS:
                return 0, f"chronicle: fresh last={last} gap={gap}d"
        rc, out, err = run("city_chronicle.py", "--feed")
        tail = (out or err).splitlines()[-1] if (out or err) else "-"
        return rc, f"chronicle: fed last={last or '-'} -> {tail}"
    except Exception as exc:  # 自愈面永不阻断主闸
        return 0, f"chronicle: skip ({type(exc).__name__})"


def coverage():
    """卡全集口径闸：导出卡 = 派生卡 + 荣誉席，且missing只允许荣誉席。

    Why: 派生面(registry+anchors)与导出面(citizens-light)分属两条生成链，
    任何一侧静默丢卡都会让事件流悄悄少掉居民而两闸仍绿（R2398 实锚：
    10114 导出 vs 10111 派生，差 3 = 荣誉席，属设计口径；此断言把该口径固化）。
    """
    reg = pathlib.Path(ROOT / "census" / "registry").rglob("C-*.md")
    anch = pathlib.Path(ROOT / "census" / "anchors").rglob("C-*.md")
    derived = {p.stem for p in reg} | {p.stem for p in anch}
    res = {p.stem for p in pathlib.Path(ROOT / "census" / "reserved").rglob("C-*.md")}
    exp = pathlib.Path(ROOT / "census" / "export" / "citizens-light.jsonl")
    exported = set()
    if exp.exists():
        for line in exp.read_text(encoding="utf-8").splitlines():
            if line.strip():
                import json
                exported.add(json.loads(line).get("id"))
    missing = exported - derived
    bad = sorted(missing - res)
    print(f"coverage: derived={len(derived)} reserved={len(res)} exported={len(exported)} "
          f"unexpected_missing={len(bad)}")
    if bad:
        print("coverage DRIFT: " + ", ".join(bad[:20]))
        return 1
    return 0


def run(script, *args):
    cmd = [sys.executable, "-X", "utf8", str(HERE / script), *args]
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true", help="exit non-zero when the replay gate fails")
    args = ap.parse_args()

    rc_d, out_d, err_d = run("events_derive.py")
    if rc_d != 0:
        print(f"derive FAIL rc={rc_d} {err_d[-300:]}")
        return 2
    rc_c, out_c, err_c = run("events_replay.py")
    rc_cov = coverage()
    rc_ch, msg_ch = chronicle_freshness()
    print(f"derive: {out_d.splitlines()[-1] if out_d else '-'}")
    print(f"replay: {out_c or err_c[-300:]}")
    print(msg_ch)
    if args.gate and (rc_c != 0 or rc_cov != 0):
        return rc_c or rc_cov
    return 0


if __name__ == "__main__":
    sys.exit(main())