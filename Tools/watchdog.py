# -*- coding: utf-8 -*-
"""看门狗：判断 BigLife 生产链是否还活着，异常写告警（CEO 2026-11-17「你自己决策」）。

Why：今天的实证——OSLoop 每 10 分钟触发、任务状态显示 Ready/Running，但
  ① 训练分支在 Beat() 定义前 exit，心跳假死 65 分钟没人发现；
  ② 任务结果码 2147946720 却实际在跑；
  ③ 训练崩过两次，靠人肉发现。
没有独立判活机制，整条链可以静默停摆几小时。

判据（任一不过 = ALERT）：
  1. 心跳 heartbeat.txt 距今 < STALE_MIN（默认 45 分钟；OSLoop 单轮上限 25 分钟
     + 触发间隔 10 分钟，45 分钟足以容纳一次长轮）
  2. os-loop 最新 run_*.log 距今 < STALE_MIN
  3. 若有训练在跑：允许心跳更久（训练分支现在也写心跳，但长轮仍可能超时）
  4. pump-receipt.json 若存在，最近 6 小时应有更新（仅在无训练时要求）

行为：
  - 全部正常 → 静默，退出 0（供计划任务高频调用，不制造噪音）
  - 异常 → 写 state/ALERT.md（含逐项判定与建议动作），退出 1

用法：
  python -X utf8 Tools/watchdog.py
  python -X utf8 Tools/watchdog.py --quiet     # 只写 ALERT，不打印
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
STATE = os.path.join(CO, "state")
ALERT = os.path.join(STATE, "ALERT.md")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

STALE_MIN = 45
PUMP_STALE_H = 6


def _age_min(path):
    try:
        return (datetime.datetime.now().timestamp() - os.path.getmtime(path)) / 60.0
    except OSError:
        return None


def training_running():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object { $_.CommandLine -match 'train_network' } | "
          "Measure-Object | Select-Object -ExpandProperty Count")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=90,
                           creationflags=NO_WINDOW)
        return int((r.stdout or "0").strip() or 0) > 0
    except Exception:  # noqa: BLE001
        return False


def latest_run_log():
    d = os.path.join(CO, "logs", "os-loop")
    best, best_mt = None, 0.0
    try:
        for fn in os.listdir(d):
            if not fn.startswith("run_"):
                continue
            p = os.path.join(d, fn)
            mt = os.path.getmtime(p)
            if mt > best_mt:
                best, best_mt = p, mt
    except OSError:
        pass
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    train = training_running()
    problems = []
    notes = []

    hb = os.path.join(STATE, "heartbeat.txt")
    hb_age = _age_min(hb)
    if hb_age is None:
        problems.append("heartbeat.txt 不存在（判活依据缺失）")
    elif hb_age > STALE_MIN:
        problems.append("heartbeat 已 %.0f 分钟未更新（阈值 %d）" % (hb_age, STALE_MIN))
    else:
        notes.append("heartbeat %.0f 分钟前" % hb_age)

    rl = latest_run_log()
    rl_age = _age_min(rl) if rl else None
    if rl_age is None:
        problems.append("logs/os-loop 下没有 run_*.log")
    elif rl_age > STALE_MIN:
        problems.append("最新 run 日志已 %.0f 分钟未更新（阈值 %d）" % (rl_age, STALE_MIN))
    else:
        notes.append("run 日志 %.0f 分钟前" % rl_age)

    pr = os.path.join(STATE, "pump-receipt.json")
    pr_age_h = None
    if os.path.exists(pr):
        try:
            with open(pr, encoding="utf-8") as f:
                data = json.load(f)
            hist = data.get("history", [])
            if hist:
                last = hist[-1].get("at") or data.get("updated")
                if last:
                    dt = datetime.datetime.fromisoformat(last)
                    pr_age_h = (datetime.datetime.now() - dt).total_seconds() / 3600.0
                    notes.append("泵上次产出 %.1f 小时前（%d 条）" % (
                        pr_age_h, hist[-1].get("written", 0)))
        except (OSError, ValueError):
            pass
        if pr_age_h is not None and pr_age_h > PUMP_STALE_H and not train:
            problems.append("泵已 %.1f 小时没有产出，且无训练在跑（阈值 %d 小时）"
                            % (pr_age_h, PUMP_STALE_H))

    if train:
        notes.append("训练运行中（生产让路属预期）")

    # 2026-11-18 居民产线值守席：按既定决策宪章自己判、自己动手（只动数据与
    # 运维态，绝不改源码）。独立子进程 + 超时 + 吞异常——值守席自身故障
    # 绝不能影响这里的存活判定；它的判断与动作全部落 state/STEWARD-LEDGER.md。
    try:
        _sw = subprocess.run([sys.executable, "-X", "utf8",
                              os.path.join(HERE, "resident_steward.py"), "--decide"],
                             timeout=900, capture_output=True, text=True,
                             encoding="utf-8", errors="replace",
                             creationflags=0x08000000 if os.name == "nt" else 0)
        if not a.quiet and _sw.stdout:
            notes.append("值守席：" + _sw.stdout.strip().splitlines()[-1])
    except Exception as _exc:  # noqa: BLE001 - 值守席挂了不进告警
        notes.append("值守席未完成（%s）" % type(_exc).__name__)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not problems:
        if not a.quiet:
            print("[%s] OK | %s" % (stamp, " / ".join(notes)))
        # 恢复正常时清掉旧告警，避免滞留噪音
        if os.path.exists(ALERT):
            try:
                os.remove(ALERT)
            except OSError:
                pass
        return 0

    lines = ["# ALERT · %s" % stamp, "",
             "BigLife 生产链判定异常：", ""]
    for p in problems:
        lines.append("- %s" % p)
    lines += ["", "## 现状", ""]
    for n in notes:
        lines.append("- %s" % n)
    lines += ["", "## 建议动作", "",
              "1. `Get-ScheduledTask BigLife-OSLoop | Select State` 看任务是否 Ready/Running",
              "2. `Get-ScheduledTaskInfo BigLife-OSLoop | Select LastRunTime,LastTaskResult` 看最近一次",
              "3. 手动跑一轮：`powershell -NoProfile -ExecutionPolicy Bypass -File "
              "life\\BigLife\\Tools\\iteration_loop.ps1` 看输出",
              "4. 检查 ollama：`ollama ps` / `Invoke-RestMethod http://127.0.0.1:11434/api/version`",
              "5. 检查显存：`nvidia-smi --query-gpu=memory.used,memory.free --format=csv`",
              ""]
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(ALERT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        print("ALERT write failed: %s" % exc, file=sys.stderr)
    if not a.quiet:
        print("[%s] ALERT: %s" % (stamp, "; ".join(problems)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
