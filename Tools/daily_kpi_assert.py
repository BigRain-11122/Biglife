# -*- coding: utf-8 -*-
"""当日面 KPI 数字一致性断言（零 LLM·确定性·只读）—— T-20261117-02 的验收载体。

病根（2026-11-17 R336x 实测）：round_daily 的两道闸都管不到「数字落后」——
  · _is_stale 只比 mtime：页面在 13:09 生成，13:2x 又有 6 条年轮落盘，
    页面 mtime 仍是今日，判 fresh；
  · --values 的 A1-A4 只问「非空壳/带当日/有记录/可返回」：数字错了照样全过。
于是 city-today.html 显示「489 今日年轮」而 registry 实算 495 时，两闸全绿。
与 2026-10-27 的「12 面静默停更」同族病根：闸问的是「有没有生」，不问「生得对不对」。

本工具把 KPI 摊成机器判据：直接 import build_daily_issue 复用 load/card_paths
（口径单一，不重复实现相遇行/三源卡的判定），把页面四个 KPI 与实算逐个比对。

用法：
  python -X utf8 Tools/daily_kpi_assert.py             # 只断言
  python -X utf8 Tools/daily_kpi_assert.py --rebuild   # 不一致则重建再复验
  python -X utf8 Tools/daily_kpi_assert.py --page X    # 指定面（负控用）
退出码：0=PASS / 1=FAIL(数字不一致) / 2=面缺失
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import build_daily_issue as bdi  # noqa: E402  口径唯一来源

PAGE = os.path.join(ROOT, "census", "export", "city-today.html")


def grab(text: str, label: str):
    m = re.search(r"<b>([^<]*)</b>\s*" + re.escape(label), text)
    return m.group(1) if m else None


def data_kpis(day: str) -> dict:
    by_day, cards = bdi.load(day)
    rows = by_day.get(day, [])
    n_ring = len([r for r in rows if not bdi.MEET_RE.match(r[4])])
    return {
        "今日年轮": n_ring,
        "今日相遇": len(rows) - n_ring,
        "今日开口的居民": len({r[0] for r in rows}),
        "居民卡总数": cards,
        "城区": len({r[2] for r in rows}),
    }


def check(day: str, page: str = PAGE) -> tuple[int, list]:
    if not os.path.exists(page):
        print("FAIL: page missing -> %s" % page)
        return 2, []
    with open(page, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    want = data_kpis(day)
    print("== daily_kpi_assert (%s) ==" % day)
    print("page : %s (mtime %s, %dB)" % (
        os.path.relpath(page, ROOT).replace("\\", "/"),
        time.strftime("%m-%d %H:%M", time.localtime(os.path.getmtime(page))),
        os.path.getsize(page)))
    bad = []
    for label, exp in want.items():
        got = grab(text, label)
        ok = (got is not None and str(got).strip() == str(exp))
        print("%-8s page=%s data=%s %s" % (label, got, exp, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append((label, got, exp))
    if bad:
        print("verdict: FAIL n=%d  (正法: python -X utf8 Tools/build_daily_issue.py)" % len(bad))
        return 1, bad
    print("verdict: PASS")
    return 0, []


def rebuild() -> int:
    print("rebuilding: Tools/build_daily_issue.py")
    rc = subprocess.call([sys.executable, "-X", "utf8", os.path.join(HERE, "build_daily_issue.py")])
    print("rebuild rc=%d" % rc)
    return rc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--page", default=PAGE, help="目标面（负控/自测用）")
    ap.add_argument("--rebuild", action="store_true", help="不一致则重建再复验")
    args = ap.parse_args()
    rc, _bad = check(args.date, args.page)
    if rc == 1 and args.rebuild and os.path.abspath(args.page) == os.path.abspath(PAGE):
        if rebuild() == 0:
            rc, _bad = check(args.date, args.page)
    return rc


if __name__ == "__main__":
    sys.exit(main())
