# -*- coding: utf-8 -*-
"""生产泵：一次触发内把时间窗口喂满，产到 due 用尽或预算到点。

Why（CEO 2026-11-17「把居民生成排满 7x24」）：OSLoop 每 10 分钟触发一轮，
但一轮里 agent 通常只跑一次 `--batch 3`（约 1 分钟），剩下 9 分钟空转，
利用率约 10%。本泵在单次触发内循环跑批，把窗口吃满；每批之间重新过资源门，
swap/显存/内存任何一项掉线立刻收手（不硬撑到把机器拖慢）。

与 agent 的分工：
  - 本泵 = 确定性生产面（年轮批），不看心情、不烧 agent token
  - agent = 判断面（决策/修复/池轮/反思），频率可降低

用法：
  python -X utf8 Tools/produce_pump.py --minutes 8 --batch 3
退出码：0=正常收手（含 due 用尽），1=资源门中断
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "state")
RECEIPT = os.path.join(STATE, "pump-receipt.json")
PY = sys.executable
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

sys.path.insert(0, HERE)
import resident_loop as rl  # noqa: E402 - 复用资源门与日志（单一判据来源）

WRITTEN_RE = re.compile(r"written=(\d+)")
DUE_RE = re.compile(r"evolved=(\d+) of (\d+) due")
SKIP_RE = re.compile(r"gate: skip (C-\d+)")
SOFT_RE = re.compile(r"soft-concession")


def run_batch(batch):
    env = os.environ.copy()
    env.setdefault("BIGLIFE_MODEL", "qwen3.5:9b")
    env.setdefault("BIGLIFE_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    env.setdefault("BIGLIFE_VRAM_LIMIT", "0.85")
    env.setdefault("BIGLIFE_IGNORE_YIELD_WINDOW", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    cmd = [PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
           "--batch", str(batch), "--via", "BigLife-Pump"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                           cwd=ROOT, env=env, creationflags=NO_WINDOW)
        out = (r.stdout or "") + (r.stderr or "")
        rc = r.returncode
    except subprocess.TimeoutExpired:
        out, rc = "timeout 30min", 124
    el = time.time() - t0

    written, due = 0, None
    skipped, soft = 0, 0
    m = WRITTEN_RE.search(out)
    if m:
        written = int(m.group(1))
    m = DUE_RE.search(out)
    if m:
        due = int(m.group(2))
    # 质量面计量（2026-11-17 CEO「保持好质量」）：拒写与软让步分开记。
    # 批席放大（10->15）会让同批反模板约束更紧，写入率可能下降——
    # 只有把 pass_rate 记进回执，才分得清「提速」和「提了速但净产出没涨」。
    skipped = len(SKIP_RE.findall(out))
    soft = len(SOFT_RE.findall(out))
    pass_rate = round(written / due, 3) if due else None
    tail = "\n".join(out.strip().splitlines()[-6:])
    return {"rc": rc, "written": written, "due": due, "skipped": skipped,
            "soft": soft, "pass_rate": pass_rate,
            "seconds": round(el, 1), "tail": tail}


def refresh_index():
    """每批前增量刷新语料索引（约 0.25 秒），保证选人面与磁盘一致。

    2026-11-17：due_citizens 改读索引后，每批省下 10-15 秒的全库 walk；
    代价是索引可能滞后（新档案/新锚定卡）。0.25 秒的增量刷新把这个窗口
    压到一批之内，比整批 slow-path 便宜 40-60 倍。
    """
    try:
        r = subprocess.run([PY, "-X", "utf8", os.path.join(HERE, "corpus_index.py"), "--build"],
                           capture_output=True, text=True, timeout=180,
                           creationflags=NO_WINDOW)
        return r.returncode == 0
    except Exception:  # noqa: BLE001 - 索引刷新失败不阻断（due_citizens 会退回步行）
        return False


def warm_probe(budget=90):
    """一轮开始前用 1 token 确认模型能应答。

    2026-11-17：模型加载失败时（显存不足/服务未就绪），整轮 9 分钟会白白耗在
    每批 150 秒的 fuse 超时上。先花 90 秒确认能答，答不了就直接收手，
    把窗口让给下一轮——比闷头烧掉 9 分钟便宜得多。
    """
    import urllib.request
    model = os.environ.get("BIGLIFE_MODEL", "qwen3.5:9b")
    try:
        body = json.dumps({"model": model, "prompt": "ping", "stream": False,
                           "think": False, "options": {"num_predict": 1}}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=budget) as r:
            r.read(64)
        return True
    except Exception:  # noqa: BLE001 - 探测失败就是信号，不是崩溃
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=9.0, help="本轮时间预算")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--max-batches", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    started = time.time()
    deadline = started + args.minutes * 60
    rounds = []
    total_written = 0
    gate_reason = "budget"

    if args.dry_run:
        ok, why = rl.admit()
        print("dry-run admit: %s (%s)" % (ok, why), flush=True)
        return 0 if ok else 1

    if not warm_probe():
        rl.log("pump stop: warm-probe failed (model cannot answer) - yield window")
        print("PUMP warm-probe-failed", flush=True)
        return 1

    while len(rounds) < args.max_batches:
        if time.time() >= deadline:
            gate_reason = "budget"
            break
        ok, why = rl.admit()
        if not ok:
            gate_reason = "gate:" + why
            rl.log("pump stop: %s" % why)
            break
        refresh_index()          # 0.25s：让选人面与磁盘同步（省下每批 10-15s 的 walk）
        res = run_batch(args.batch)
        rounds.append(res)
        total_written += res["written"]
        rl.log("pump batch %d: wrote=%d due=%s rc=%d %.0fs" % (
            len(rounds), res["written"], res["due"], res["rc"], res["seconds"]))
        # 收手判据（2026-11-17 审查加固）：
        #   rc!=0 且 written=0  = 整批失败（模型超时/异常），不是"due 用尽"，
        #   必须如实记成 batch-failed，否则运维看回执会以为今天已经写完。
        #   rc==0 且 written=0  = 今天剩余的卡全被质量闸 defer（+1d），再跑也是拒，
        #   这才是真正的 no-progress。
        if res["due"] is not None and res["written"] == 0:
            gate_reason = "no-progress" if res["rc"] == 0 else "batch-failed"
            break
        time.sleep(2)

    # 自审（与 resident_loop 对齐）：本批真的写了卡，就跑一次净增核验。
    # 零 LLM、失败不阻断（下一轮照跑），只留痕供追溯。
    if total_written > 0:
        try:
            ra = rl._run([PY, "-X", "utf8", os.path.join(HERE, "ring_batch_audit.py")],
                         timeout=300)
            rl.log("pump audit batch_audit rc=%d" % ra.returncode)
        except Exception as exc:  # noqa: BLE001 - 审查失败不能停线
            rl.log("pump audit failed: %s" % exc)
        # 消费接口（CEO「一定用的上」）：把今日年轮导出成下游可读流，约 0.3 秒。
        # 下游 = Unity 居民气泡 / HTML 看板 / 短视频取材，统一读 today-rings.jsonl。
        try:
            er = rl._run([PY, "-X", "utf8", os.path.join(HERE, "export_rings.py")],
                         timeout=180)
            rl.log("pump export today-rings rc=%d" % er.returncode)
        except Exception as exc:  # noqa: BLE001
            rl.log("pump export failed: %s" % exc)

    el = round(time.time() - started, 1)
    payload = {
        "at": datetime.datetime.now().isoformat(timespec="seconds"),
        "rounds": len(rounds), "written": total_written,
        "seconds": el, "stop": gate_reason,
        "detail": rounds,
    }
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
            json.dump({"updated": payload["at"], "history": hist}, f,
                      ensure_ascii=False, indent=2)
    except OSError:
        pass

    rl.log("pump done: %d rounds, %d written, %.0fs, stop=%s" % (
        len(rounds), total_written, el, gate_reason))
    print("PUMP %s rounds=%d written=%d %.0fs" % (
        gate_reason, len(rounds), total_written, el), flush=True)
    return 0 if gate_reason in ("budget", "no-progress") else 1


if __name__ == "__main__":
    sys.exit(main())
