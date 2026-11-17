# -*- coding: utf-8 -*-
"""稳定性闸：连续采样多轮，全部达标才允许生成（CEO 2026-11-17 令）。

Why：单次快照会骗人——16:07 那次训练崩溃前，内存与 swap 指标在采样窗口内
都是"正常"的，真正的问题是模型加载把训练挤掉。所以判定必须是**连续 N 轮
全部通过**，任何一轮不达标就整体判不稳定。

检测项（每轮）：
  1. swap 写出速率  `\\Memory\\Pages Output/sec` 必须 < SWAP_MAX（硬门，用户最在意）
  2. 物理内存可用  > MEM_MIN_GB
  3. GPU 空闲      > VRAM_MIN_MB
  4. 无外部模型调用方（11434 上没有非 ollama 连接）
  5. 训练进程      不在跑（训练期间不许生成）
  6. ollama 驻留   为空（避免别的模型占着卡）

通过：打印 PASS 摘要，退出码 0
不通过：打印每轮失败项，退出码 1

用法：
  python -X utf8 Tools/stability_gate.py --rounds 5 --interval 8
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

NO_WINDOW = 0x08000000 if __import__("os").name == "nt" else 0

SWAP_MAX = 50.0        # Pages Output/sec；>50 视为有实质写盘
MEM_MIN_GB = 20.0
VRAM_MIN_MB = 5000     # 4B@16K 约 4-5G，留余量


def probe():
    """一次采集全部指标（单次 PowerShell 往返，减少开销）。"""
    ps = r"""
$o = [ordered]@{}
try {
  $c = Get-Counter '\Memory\Pages Output/sec' -SampleInterval 1 -MaxSamples 1 -ErrorAction Stop
  $o.swap_out = [math]::Round($c.CounterSamples[0].CookedValue, 2)
} catch { $o.swap_out = -1 }
$os = Get-CimInstance Win32_OperatingSystem
$o.mem_free_gb = [math]::Round($os.FreePhysicalMemory/1MB, 2)
try {
  $g = & nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits
  $p = ($g -split ',')
  $o.vram_free_mb = [int]$p[1] - [int]$p[0]
} catch { $o.vram_free_mb = -1 }
$o.model = ''
try { $o.model = (& ollama ps 2>$null | Select-Object -Skip 1 | ForEach-Object { ($_ -split '\s+')[0] } | Where-Object { $_ } ) -join ',' } catch {}
$o.training = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'train_network' }).Count
$o.caller = @(Get-NetTCPConnection -RemotePort 11434 -State Established -ErrorAction SilentlyContinue).Count
$o | ConvertTo-Json -Compress
"""
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True, timeout=120,
                       creationflags=NO_WINDOW)
    try:
        return json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception:  # noqa: BLE001 - 探测失败=不稳定，宁可拦
        return None


def judge(m):
    """返回失败原因列表（空=本轮通过）。"""
    bad = []
    if m is None:
        return ["probe-failed"]
    if m.get("swap_out", -1) < 0:
        bad.append("swap-probe-failed")
    elif m["swap_out"] > SWAP_MAX:
        bad.append("swap-out %.1f > %.0f" % (m["swap_out"], SWAP_MAX))
    if m.get("mem_free_gb", 0) < MEM_MIN_GB:
        bad.append("mem %.1fG < %.0fG" % (m.get("mem_free_gb", 0), MEM_MIN_GB))
    if m.get("vram_free_mb", 0) < VRAM_MIN_MB:
        bad.append("vram %dM < %dM" % (m.get("vram_free_mb", 0), VRAM_MIN_MB))
    if (m.get("model") or "").strip():
        bad.append("model loaded: %s" % m["model"])
    if m.get("training", 0) > 0:
        bad.append("training running (%d)" % m["training"])
    if m.get("caller", 0) > 0:
        bad.append("external caller (%d)" % m["caller"])
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--interval", type=float, default=8.0)
    args = ap.parse_args()

    rounds_bad = 0
    for i in range(1, args.rounds + 1):
        m = probe()
        bad = judge(m)
        stamp = time.strftime("%H:%M:%S")
        if bad:
            rounds_bad += 1
            print("[%s] round %d/%d FAIL: %s | raw=%s" % (
                stamp, i, args.rounds, "; ".join(bad), json.dumps(m, ensure_ascii=False)), flush=True)
        else:
            print("[%s] round %d/%d OK   swap=%.1f mem=%.1fG vram=%dM" % (
                stamp, i, args.rounds, m["swap_out"], m["mem_free_gb"], m["vram_free_mb"]), flush=True)
        if i < args.rounds:
            time.sleep(args.interval)

    if rounds_bad == 0:
        print("STABILITY PASS (%d/%d rounds clean)" % (args.rounds, args.rounds), flush=True)
        return 0
    print("STABILITY FAIL (%d/%d rounds bad)" % (rounds_bad, args.rounds), flush=True)
    return 1


if __name__ == "__main__":
    sys.exit(main())
