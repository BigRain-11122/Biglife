# -*- coding: utf-8 -*-
"""硅基居民内容生产闭环（7x24 无人值守，单次工作单元模式）。

由计划任务 BigLife-ResidentProduce 每 15 分钟拉起一次 `--once`：
一个工作单元 = 资源门 -> 生产一批 -> 自审两道 -> 写回执 -> 退出。
不用常驻进程：交互会话的子进程会被 Job Object 连坐杀掉（2026-10-16 判例），
计划任务才是不受会话生死影响的承载方式。

资源纪律（CEO 2026-11-17「不要触发 swap，留点资源给我工作」）：
  - 训练在跑（*_train_network.py）-> 让路
  - 显存空闲 < VRAM_MIN_FREE_MB -> 让路
  - 物理内存可用 < MEM_MIN_FREE_GB -> 让路（swap 前置闸）
  - 模型 keep_alive 短（跑完即退，不长期占卡）

自审（零 LLM 确定性，全部现成工具）：
  - ring_batch_audit.py  批净增核验（提交里 census/registry 改动数 = 声明居民数）
  - ring_lint.py --today-only  当日年轮内部码巡检

用法：
  python -X utf8 Tools/resident_loop.py --once
  python -X utf8 Tools/resident_loop.py --once --batch 10 --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # ...\life\BigLife
STATE = os.path.join(ROOT, "state")
LOG = os.path.join(STATE, "resident-loop.log")
RECEIPT = os.path.join(STATE, "resident-loop.json")
LOCK = os.path.join(STATE, "resident-loop.lock")
PY = sys.executable
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

VRAM_MIN_FREE_MB = 6500     # 9B @8K 实测 6.1G
MEM_MIN_FREE_GB = 8.0     # 2026-11-17 夜窗: CEO 下班放开 20->8
SWAP_OUT_MAX = 800.0      # Pages Output/sec 上限（写盘速率）      # 低于此不再加载（swap 前置闸）
LOCK_STALE_MIN = 12


def log(msg):
    line = "[%s] %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        # 日志过大时截断，避免无人值守下无限增长
        if os.path.getsize(LOG) > 4 * 1024 * 1024:
            with open(LOG, "r", encoding="utf-8", errors="replace") as f:
                tail = f.readlines()[-2000:]
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(tail)
    except OSError:
        pass


def _run(cmd, timeout=3600, cwd=ROOT, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          cwd=cwd, env=env, creationflags=NO_WINDOW)


def gpu():
    """(used, total) MiB，读不到返回 (None, None)。"""
    try:
        r = _run(["nvidia-smi", "--query-gpu=memory.used,memory.total",
                  "--format=csv,noheader,nounits"], timeout=30)
        used, total = [float(x) for x in (r.stdout or "").strip().splitlines()[0].split(",")[:2]]
        return used, total
    except Exception:  # noqa: BLE001 - 探测失败不阻断，交给下游 vram_guard
        return None, None


def mem_free_gb():
    try:
        r = _run(["powershell", "-NoProfile", "-Command",
                  "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"], timeout=60)
        return float((r.stdout or "0").strip()) / 1024.0 / 1024.0
    except Exception:  # noqa: BLE001
        return None


def training_running():
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
          "Where-Object { $_.CommandLine -match 'train_network' } | "
          "Measure-Object | Select-Object -ExpandProperty Count")
    try:
        r = _run(["powershell", "-NoProfile", "-Command", ps], timeout=90)
        return int((r.stdout or "0").strip() or 0) > 0
    except Exception:  # noqa: BLE001 - 探测失败按"在跑"处理，宁可让路
        return True


def _pid_alive(pid):
    """PID 是否还活着（Windows 用 tasklist，认命令行成本低）。"""
    try:
        r = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                           capture_output=True, text=True, timeout=15)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return True          # 探不到就当活着，宁可让路


def take_lock():
    """跨进程互斥（计划任务 MultipleInstances=IgnoreNew 之外的二道保险）。

    2026-11-20 11:1x 实锚：上一实例被杀掉后锁留在盘上，而旧实现只看**文件龄**
    （40 分钟才接管），于是产线白停 40 分钟——日志只有一行
    `pump skip: lock held 30.0 min`，看上去像在正常让路。
    现在锁里写 PID：**持有者进程已死就立刻接管**；文件龄 12 分钟只作兜底。
    """
    try:
        if os.path.exists(LOCK):
            raw = ""
            try:
                with open(LOCK, encoding="utf-8") as f:
                    raw = f.read().strip()
            except OSError:
                raw = ""
            pid = None
            if "|" in raw:
                try:
                    pid = int(raw.rsplit("|", 1)[1])
                except ValueError:
                    pid = None
            if pid and not _pid_alive(pid):
                try:
                    os.remove(LOCK)
                except OSError:
                    pass
            else:
                age_min = (datetime.datetime.now().timestamp() - os.path.getmtime(LOCK)) / 60.0
                if age_min < LOCK_STALE_MIN:
                    return False, "lock held %.1f min" % age_min
        with open(LOCK, "w", encoding="utf-8") as f:
            f.write("%s|%d" % (datetime.datetime.now().isoformat(), os.getpid()))
        return True, "ok"
    except OSError as exc:
        return True, "lock unreadable (%s), proceed" % exc


def drop_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def swap_out_rate(samples=3):
    """Pages Output/sec 的中位数（写盘速率）。

    CEO 2026-11-17：swap 是最关键的卡顿来源，但它有瞬时峰值——实测抓到过一次
    30403 页/秒的尖峰，把整轮泵误杀了，而前后两秒都是 0。单点采样必然误判，
    所以采 3 次取中位数：持续 swap 会三次数值都高（拦得住），瞬时尖峰只污染
    一次（拦不住，但无害）。
    """
    ps = (r"(Get-Counter '\Memory\Pages Output/sec' -SampleInterval 1 -MaxSamples 1 "
          r"-ErrorAction Stop).CounterSamples[0].CookedValue")
    vals = []
    for _ in range(max(1, samples)):
        try:
            r = _run(["powershell", "-NoProfile", "-Command", ps], timeout=60)
            vals.append(float((r.stdout or "").strip()))
        except Exception:  # noqa: BLE001 - 探测失败不阻断
            return None
    vals.sort()
    return vals[len(vals) // 2]


def models_loaded():
    """当前 ollama 驻留模型名列表（空=干净）。"""
    try:
        r = _run(["ollama", "ps"], timeout=60)
        names = []
        for line in (r.stdout or "").splitlines()[1:]:
            part = line.split()
            if part:
                names.append(part[0])
        return names
    except Exception:  # noqa: BLE001
        return []


def admit():
    """资源门：返回 (是否放行, 原因)。

    2026-11-17 加固：在原有「训练/显存/内存」之外，增加 swap 写出与模型驻留两项。
    实测教训：训练跑着的时候，qwen3:4b-instruct 被反复拉起到 8 GB（16K KV），
    显存只剩几百 MB 并溢出 CPU，用户体感就是卡顿。
    """
    if training_running():
        return False, "training-running"
    so = swap_out_rate()
    if so is not None and so > SWAP_OUT_MAX:
        return False, "swap-out %.1f pages/s > %.0f" % (so, SWAP_OUT_MAX)
    # 2026-11-17 修 BUG：原来只要「有任何模型驻留」就拒绝，结果是泵自己上一批
    # 加载的 9B（keep_alive 内）把下一轮挡死 —— gate 永远报
    # "model already loaded: qwen3.5:9b"，泵连续 0 rounds，生产实际停摆。
    # 正解：只拦「不是本项目要用的那个模型」，我们要用的那个驻留是正常状态。
    target = os.environ.get("BIGLIFE_MODEL", "qwen3.5:9b")
    others = [m for m in models_loaded() if m != target]
    if others:
        # 2026-11-17：不再让整轮空等。非目标模型（实测为 codely 自己的 flash 模型
        # qwen3.5:2b）占着卡时，主动卸载它把窗口拿回来——生产优先，flash 腿会在
        # 下次调用时自行重载。卸载失败才判定冲突让路。
        for m in others:
            try:
                _run(["ollama", "stop", m], timeout=90)
            except Exception:  # noqa: BLE001
                pass
        still = [m for m in models_loaded() if m != target]
        if still:
            return False, "other model loaded: %s" % ",".join(still)
    used, total = gpu()
    if used is not None and total:
        free = total - used
        # 2026-11-17 修 BUG：阈值必须区分「模型尚未加载」与「模型已在卡上」。
        # 原实现一律要求 6500 MiB 空闲，可 9B 自己就占 6.2G，加载完之后剩余
        # 只有 1.7G，于是下一轮永远判「vram 不足」——泵连续 0 rounds，生产停摆。
        need = 500 if target in models_loaded() else VRAM_MIN_FREE_MB   # 并发3实测余量~850MiB
        if free < need:
            return False, "vram %.0f MiB free < %d%s" % (
                free, need, " (model resident)" if need == 1200 else "")
    mf = mem_free_gb()
    # 2026-11-17 修 BUG（同类第三次）：模型驻留时 llama-server 自己就吃约 9 GB
    # 内存（模型 mmap + KV），加载后可用内存从 34G 掉到 20G，于是「需 20G」的闸
    # 把后续每一批都挡住。区分两态：未加载需 20G（够它张开），已驻留只需 12G
    # （安全线，防真正的内存枯竭）。
    if mf is not None:
        need_mem = 5.0 if target in models_loaded() else MEM_MIN_FREE_GB
        if mf < need_mem:
            return False, "mem %.1f GB free < %.0f%s" % (
                mf, need_mem, " (model resident)" if need_mem == 12.0 else "")
    return True, "ok"


def produce(batch, dry_run):
    env = os.environ.copy()
    env.setdefault("BIGLIFE_MODEL", "qwen3.5:9b")
    env.setdefault("BIGLIFE_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    env.setdefault("BIGLIFE_VRAM_LIMIT", "0.85")
    env.setdefault("BIGLIFE_IGNORE_YIELD_WINDOW", "1")   # CEO 要 7x24
    env.setdefault("PYTHONIOENCODING", "utf-8")
    cmd = [PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
           "--batch", str(batch), "--via", "BigLife-ResidentLoop"]
    if dry_run:
        cmd.append("--audit-due")
    log("exec: " + " ".join(cmd))
    t0 = datetime.datetime.now()
    try:
        r = _run(cmd, timeout=3000, env=env)
        rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        rc, out = 124, "timeout 50min"
    el = (datetime.datetime.now() - t0).total_seconds()
    tail = "\n".join(out.strip().splitlines()[-25:])
    log("produce rc=%d %.1f min\n%s" % (rc, el / 60.0, tail))
    return rc, el, tail


def audit():
    """自审两道：净增核验 + 内部码巡检。任一非零只记录，不阻断（下一轮照跑）。"""
    out = {}
    for name, cmd, timeout in (
        ("batch_audit", [PY, "-X", "utf8", os.path.join(HERE, "ring_batch_audit.py")], 300),
        ("ring_lint", [PY, "-X", "utf8", os.path.join(HERE, "ring_lint.py"), "--today-only"], 600),
    ):
        try:
            r = _run(cmd, timeout=timeout)
            out[name] = {"rc": r.returncode,
                         "tail": "\n".join(((r.stdout or "") + (r.stderr or "")).strip().splitlines()[-12:])}
            log("audit %s rc=%d" % (name, r.returncode))
        except Exception as exc:  # noqa: BLE001 - 审查失败要留痕，但不能停线
            out[name] = {"rc": -1, "tail": str(exc)}
            log("audit %s failed: %s" % (name, exc))
    return out


def write_receipt(payload):
    try:
        os.makedirs(STATE, exist_ok=True)
        hist = []
        if os.path.exists(RECEIPT):
            try:
                with open(RECEIPT, "r", encoding="utf-8") as f:
                    hist = json.load(f).get("history", [])[-19:]
            except (OSError, ValueError):
                hist = []
        hist.append(payload)
        with open(RECEIPT, "w", encoding="utf-8") as f:
            json.dump({"updated": datetime.datetime.now().isoformat(timespec="seconds"),
                       "history": hist}, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="单工作单元（计划任务用）")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--dry-run", action="store_true", help="只跑 --audit-due（零 LLM 审计面）")
    args = ap.parse_args()

    ok, why = admit()
    if not ok:
        log("yield: " + why)
        write_receipt({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                       "status": "yield", "reason": why})
        return 0

    ok, why = take_lock()
    if not ok:
        log("skip: " + why)
        return 0

    try:
        rc, el, tail = produce(args.batch, args.dry_run)
        audits = audit() if rc == 0 else {}
        write_receipt({"at": datetime.datetime.now().isoformat(timespec="seconds"),
                       "status": "done" if rc == 0 else "failed", "rc": rc,
                       "batch": args.batch, "seconds": round(el, 1),
                       "tail": tail[-800:], "audit": audits})
        return 0 if rc == 0 else 1
    finally:
        drop_lock()


if __name__ == "__main__":
    sys.exit(main())
