# -*- coding: utf-8 -*-
"""resource_policy.py — 按 CEO 授权的时间窗决定占多少算力。

CEO 2026-11-20 夜：「节假日和周末你可以全天占用，工作日晚上」。

档位（返回 conc / 重写张数 / 重写分片数）：
  full   工作日 19:00–09:00、周末、节假日  -> 6 / 60 / 3（吃满）
  shared 工作日 09:00–19:00               -> 1 / 6  / 1（共用排队，别卡工作与游戏开发）

节假日来源：state/holidays.txt，每行一个 YYYY-MM-DD。没维护就是空表——
**周末自动识别，节假日需要写进那个文件**（不猜日历，宁可少占不误占）。
"""
from __future__ import annotations

import datetime
import os

CO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLIDAYS = os.path.join(CO, "state", "holidays.txt")

FULL = {"conc": 6, "rq_limit": 60, "rq_shards": 3}
SHARED = {"conc": 1, "rq_limit": 6, "rq_shards": 1}


def _holidays():
    out = set()
    try:
        with open(HOLIDAYS, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if len(ln) >= 10:
                    out.add(ln[:10])
    except OSError:
        pass
    return out


def mode(now=None):
    now = now or datetime.datetime.now()
    if now.date().isoformat() in _holidays():
        return "full"
    if now.weekday() >= 5:          # 周六日
        return "full"
    return "full" if (now.hour >= 19 or now.hour < 9) else "shared"


def limits(now=None):
    return FULL if mode(now) == "full" else SHARED


if __name__ == "__main__":
    m = mode()
    print("mode=%s %s" % (m, limits()))
