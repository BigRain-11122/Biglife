# -*- coding: utf-8 -*-
"""等 GPU 空出来再开工居民内容生产（静默守护）。

Why（2026-11-17 实锚）：微信 PC 客户端白屏的根因不是防火墙，是显卡长期被压到
89-94%（state/vram-gate.jsonl 有全天空闲记录），其中 LoRA 训练独占约 7.5GB。
生产批若与训练同跑，两边都降速、桌面没有余量，用户自己的应用就会渲染失败。
本脚本只做一件事：静默等训练退出，再按 BIGLIFE_* 配置跑一批生成。

用法（无窗口）：
    pythonw Tools/wait_then_produce.py --batch 6

判据：
  1. 按命令行匹配 *_train_network.py；连续 3 次（间隔 60s）无匹配 = 训练结束
  2. 再等 120s 让显存释放；free < MIN_FREE_MIB 则退避 10 分钟重试（最多 8 次）
  3. 产完把 rc / 耗时 / 产出卡数写 state/wait-produce.json，日志落 state/wait-produce.log
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # ...\life\BigLife
STATE = os.path.join(ROOT, "state")
LOG = os.path.join(STATE, "wait-produce.log")
RECEIPT = os.path.join(STATE, "wait-produce.json")
PY = sys.executable

# 控制台窗口一律不弹（用户 2026-09-29「不要弹窗，静默工作」令）
NO_WINDOW = 0x08000000 if os.name == "nt" else 0
MIN_FREE_MIB = 6000        # 9B @8K 实测 6.1GB，留 6GB 才加载得进来
POLL_S = 60
QUIET_ROUNDS = 3           # 连续 3 轮无训练进程 = 真的结束了
RELEASE_WAIT_S = 120
BACKOFF_S = 600


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def _run(cmd, timeout=60, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          creationflags=NO_WINDOW, **kw)


def train_running():
    """命令行匹配训练进程；探测失败按"还在跑"处理（宁可等，不抢）。"""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object { $_.CommandLine -match 'train_network' } | "
          "Measure-Object | Select-Object -ExpandProperty Count")
    try:
        r = _run(["powershell", "-NoProfile", "-Command", ps], timeout=90)
        return int((r.stdout or "0").strip() or 0) > 0
    except Exception:  # noqa: BLE001 - 探测失败不能变成误开工
        return True


def free_mib():
    try:
        r = _run(["nvidia-smi", "--query-gpu=memory.free",
                  "--format=csv,noheader,nounits"], timeout=30)
        return int(float((r.stdout or "0").strip().splitlines()[0]))
    except Exception:  # noqa: BLE001
        return 0


def receipt(payload):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(RECEIPT, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=6)
    args = ap.parse_args()

    env = os.environ.copy()
    env.setdefault("BIGLIFE_MODEL", "qwen3.5:9b")
    env.setdefault("BIGLIFE_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    env.setdefault("BIGLIFE_VRAM_LIMIT", "0.82")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    log("守护启动 batch=%d model=%s limit=%s" % (
        args.batch, env["BIGLIFE_MODEL"], env["BIGLIFE_VRAM_LIMIT"]))

    # 阶段一：等训练结束
    quiet = 0
    while True:
        if train_running():
            quiet = 0
            time.sleep(POLL_S)
            continue
        quiet += 1
        log("未见训练进程（%d/%d）GPU free=%d MiB" % (quiet, QUIET_ROUNDS, free_mib()))
        if quiet >= QUIET_ROUNDS:
            break
        time.sleep(POLL_S)

    log("训练已结束，等 %ds 让驱动回收显存" % RELEASE_WAIT_S)
    time.sleep(RELEASE_WAIT_S)

    # 阶段二：显存够了才跑
    for attempt in range(1, 9):
        free = free_mib()
        if free >= MIN_FREE_MIB:
            log("显存就绪 free=%d MiB，开始生产" % free)
            break
        log("显存不足 free=%d MiB < %d，第 %d 次退避 %ds" % (
            free, MIN_FREE_MIB, attempt, BACKOFF_S))
        time.sleep(BACKOFF_S)
    else:
        log("退避 8 次仍不足，放弃本次（不硬挤）")
        receipt({"status": "give-up", "reason": "vram-short", "at": time.time()})
        return 2

    # 阶段三：跑一批
    t0 = time.time()
    cmd = [PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
           "--batch", str(args.batch), "--via", "BigLife-OSLoop"]
    log("执行: %s" % " ".join(cmd))
    try:
        r = _run(cmd, timeout=6 * 3600, cwd=ROOT, env=env)
        rc, out, err = r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        rc, out, err = 124, "", "timeout 6h"
    el = time.time() - t0

    tail = "\n".join((out + "\n" + err).strip().splitlines()[-40:])
    log("rc=%d 用时 %.1f 分钟\n%s" % (rc, el / 60.0, tail))
    receipt({"status": "done" if rc == 0 else "failed", "rc": rc,
             "batch": args.batch, "seconds": round(el, 1),
             "at": datetime.datetime.now().isoformat(timespec="seconds"),
             "tail": tail})
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
