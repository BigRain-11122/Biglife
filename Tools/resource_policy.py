# -*- coding: utf-8 -*-
"""resource_policy.py — 按 CEO 授权决定占多少算力。

CEO 2026-11-20：「节假日和周末你可以全天占用，工作日晚上」+「我说下班了你就可以
全面满负荷」。三条规则按优先级：

1. **手动满负荷开关**（最高优先）：state/full-load.flag 里写一个到期时间
   （ISO 时间）。CEO 说「我下班了」时由会话写入「次日 09:00」，期间一律 full；
   说「我要工作/我要打游戏」时删掉该文件立即降档。
2. 节假日（state/holidays.txt，一行一个 YYYY-MM-DD）→ full
3. 周末 → full；工作日 19:00–09:00 → full；工作日 09:00–19:00 → shared

档位返回 conc / 重写张数 / 重写分片数。
"""
from __future__ import annotations

import datetime
import os

CO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLIDAYS = os.path.join(CO, "state", "holidays.txt")
OVERRIDE = os.path.join(CO, "state", "full-load.flag")

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


def _override_active(now):
    """CEO 下班开关：文件存在且未过期 = 满负荷。"""
    if not os.path.exists(OVERRIDE):
        return False
    try:
        raw = open(OVERRIDE, encoding="utf-8").read().strip()
    except OSError:
        return True
    if not raw:
        return True
    try:
        return now < datetime.datetime.fromisoformat(raw)
    except ValueError:
        return True


def mode(now=None):
    now = now or datetime.datetime.now()
    if _override_active(now):
        return "full"
    if now.date().isoformat() in _holidays():
        return "full"
    if now.weekday() >= 5:
        return "full"
    return "full" if (now.hour >= 19 or now.hour < 9) else "shared"


def limits(now=None):
    return FULL if mode(now) == "full" else SHARED


def set_offwork(until=None):
    """CEO 说「下班了」时调用：写入满负荷并返回到期时间。"""
    if until is None:
        n = datetime.datetime.now()
        d = n + datetime.timedelta(days=1)
        until = datetime.datetime(d.year, d.month, d.day, 9, 0)
        while until.weekday() >= 5:                       # 撞周末就顺延到周一 09:00
            until += datetime.timedelta(days=1)
            until = until.replace(hour=9, minute=0)
    os.makedirs(os.path.dirname(OVERRIDE), exist_ok=True)
    with open(OVERRIDE, "w", encoding="utf-8") as fh:
        fh.write(until.isoformat(timespec="minutes"))
    return until


def clear_offwork():
    try:
        os.remove(OVERRIDE)
    except OSError:
        pass


if __name__ == "__main__":
    print("mode=%s %s" % (mode(), limits()))
