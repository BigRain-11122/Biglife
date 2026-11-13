# -*- coding: utf-8 -*-
"""T-20261113-06 快熔闸自测（零 GPU / 零网络）。

验三件：
  A. seat_call 单居民 wall-clock 硬熔：慢座席 -> SeatTimeout（默认 150s，此处用 1s 缩样）
  B. llm() 截止时间前置闸：预算已耗尽 -> 立刻 SeatTimeout，不发请求（不再 120s×3 叠加）
  C. vram_guard 探针：返回 None/float，且永不抛异常（不得成为新静默停摆）

跑法：python -X utf8 Tools/selftest_seat_fuse.py   （rc=0 = 全绿）
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evolve_citizen as ec  # noqa: E402

fails = []


def _check(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + name + " - " + detail, flush=True)
    if not ok:
        fails.append(name)


def case_a():
    orig = ec.gated_llm

    def _slow(prompt, sig, max_regens=3):
        time.sleep(30)
        return "never"

    ec.gated_llm = _slow
    t0 = time.time()
    try:
        ec.seat_call("x", {}, fuse=1)
        _check("A seat-fuse", False, "no SeatTimeout raised")
    except ec.SeatTimeout:
        dt = time.time() - t0
        _check("A seat-fuse", 1.0 <= dt <= 8.0,
               "SeatTimeout after %.2fs (fuse=1s, join cap 6s)" % dt)
    except BaseException as exc:  # noqa: BLE001
        _check("A seat-fuse", False, "wrong exception %r" % (exc,))
    finally:
        ec.gated_llm = orig
        ec._SEAT_DEADLINE = None


def case_b():
    ec._SEAT_DEADLINE = time.monotonic() - 1
    t0 = time.time()
    try:
        ec.llm("x")
        _check("B llm-deadline", False, "no SeatTimeout before request")
    except ec.SeatTimeout:
        _check("B llm-deadline", time.time() - t0 < 1.0,
               "SeatTimeout in %.3fs, no network call" % (time.time() - t0))
    except BaseException as exc:  # noqa: BLE001
        _check("B llm-deadline", False, "wrong exception %r" % (exc,))
    finally:
        ec._SEAT_DEADLINE = None


def case_c():
    try:
        got = ec.vram_guard()
        _check("C vram-guard", got is None or isinstance(got, float),
               "returned %r (no raise)" % (got,))
    except BaseException as exc:  # noqa: BLE001
        _check("C vram-guard", False, "raised %r" % (exc,))


case_a()
case_b()
case_c()
print("verdict: %s (%d fail)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(0 if not fails else 1)
