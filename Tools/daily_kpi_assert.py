# -*- coding: utf-8 -*-
"""当日面 KPI 数字一致性断言（零 LLM·确定性·只读）—— T-20261117-02 的验收载体。

病根（2026-11-17 R336x 实测）：round_daily 的两道闸都管不到「数字落后」——
  · _is_stale 只比 mtime：页面在 13:09 生成，13:2x 又有 6 条年轮落盘，
    页面 mtime 仍是今日，判 fresh；
  · --values 的 A1-A4 只问「非空壳/带当日/有记录/可返回」：数字错了照样全过。
于是 city-today.html 显示「489 今日年轮」而 registry 实算 495 时，两闸全绿。
与 2026-10-27 的「12 面静默停更」同族病根：闸问的是「有没有生」，不问「生得对不对」。

勘误（2026-11-17 14:3x 实证）：上段的 489/495 归因说反了。卡面 495 行 = 489 纯年轮
+ 6 相遇行（相遇轮双方各写一句年轮式互动，行格式与年轮相同）。build_daily_issue 排除
相遇行得 489（正确口径）；build_city_dashboard 的逐日曲线只按 `^- YYYY-MM-DD ` 计数，
把 6 条相遇计成年轮得 495（错）。两闸全绿的原因是断言件只验 city-today，而错的是看板。
故本工具同时断言两面的「今日年轮」口径，任一面漂移即 FAIL。

本工具把 KPI 摊成机器判据：直接 import build_daily_issue 复用 load/card_paths
（口径单一，不重复实现相遇行/三源卡的判定），把页面 KPI 与实算逐个比对。

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
DASH = os.path.join(ROOT, "census", "export", "city-dashboard.html")


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
        return 1, bad
    return 0, []


def check_dashboard(day: str) -> tuple[int, list]:
    """看板「今日新增年轮」必须与 city-today 同口径（排除相遇行）。

    2026-11-17 实测：逐日曲线曾把 6 条相遇行计成年轮（495 vs 真值 489），
    而断言件只验 city-today，属「被测件之外的错」。此断言把看板纳入射程。
    """
    if not os.path.exists(DASH):
        print("FAIL: page missing -> %s" % DASH)
        return 2, []
    with open(DASH, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    exp = data_kpis(day)["今日年轮"]
    m = re.search(r"<b>([^<]*)</b>\s*<span>\s*今日新增年轮", text)
    got = m.group(1) if m else None
    ok = got is not None and str(got).strip() == str(exp)
    print("看板今日年轮 page=%s data=%s %s" % (got, exp, "OK" if ok else "MISMATCH"))
    if ok:
        return 0, []
    return 1, [("今日新增年轮(看板)", got, exp)]


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
    same_page = os.path.abspath(args.page) == os.path.abspath(PAGE)
    rc, bad = check(args.date, args.page)
    if same_page:
        drc, dbad = check_dashboard(args.date)
        rc = drc if rc == 0 else rc
        bad = bad + dbad
    if rc == 1 and args.rebuild and same_page:
        if rebuild() == 0:
            rc, bad = check(args.date, args.page)
            drc, dbad = check_dashboard(args.date)
            rc = drc if rc == 0 else rc
            bad = bad + dbad
    if rc == 1:
        print("verdict: FAIL n=%d  (正法: python -X utf8 Tools/build_daily_issue.py "
              "+ build_city_dashboard.py)" % len(bad))
    elif rc == 2:
        print("verdict: MISSING")
    else:
        print("verdict: PASS")
    return rc


if __name__ == "__main__":
    sys.exit(main())
