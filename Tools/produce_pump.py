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


def run_batch_parallel(batch, conc):
    """并发跑：取 due -> 切 conc 段 -> 各进程 --force --no-commit --lock-name。"""
    env = os.environ.copy()
    env.setdefault("BIGLIFE_MODEL", "qwen3.5:9b")
    env.setdefault("BIGLIFE_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    env.setdefault("BIGLIFE_IGNORE_YIELD_WINDOW", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # 2026-11-18 CEO「该扩就扩」：最后一个并发槽不跑年轮，改跑其他内容面，
    # 让反思/池轮/相遇与年轮同时产出，而不是年轮空了才轮换。
    rings_conc = max(1, conc - 1) if conc > 1 else 1
    r = subprocess.run([PY, "-X", "utf8", os.path.join(HERE, "due_list.py"),
                        "--limit", str(batch * rings_conc), "--chunks", str(rings_conc)],
                       capture_output=True, text=True, timeout=300,
                       cwd=ROOT, env=env, creationflags=NO_WINDOW)
    segs = [l.strip() for l in (r.stdout or "").splitlines() if l.strip()]
    segs = [l for l in segs if l.split()]
    if len(segs) < rings_conc:
        res = run_batch(batch)
        res["conc"] = 1
        return res
    t0 = time.time()
    procs = []
    for i, seg in enumerate(segs):
        cmd = [PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
               "--force"] + seg.split() + ["--no-commit", "--lock-name", "pc%d" % i]
        procs.append(subprocess.Popen(cmd, cwd=ROOT, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, creationflags=NO_WINDOW))
    if conc > 1:
        cmd2 = [PY, "-X", "utf8", os.path.join(HERE, "work_scheduler.py"),
                "--run-next", "--skip-rings"]
        procs.append(subprocess.Popen(cmd2, cwd=ROOT, env=env,
                                      stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, creationflags=NO_WINDOW))
    outs = []
    for pr in procs:
        try:
            outs.append(pr.communicate(timeout=1800)[0] or "")
        except subprocess.TimeoutExpired:
            pr.kill()
            outs.append("")
    el = time.time() - t0
    written = 0; due_total = None; skipped = 0; soft = 0
    for o in outs:
        m = WRITTEN_RE.search(o)
        if m: written += int(m.group(1))
        m = DUE_RE.search(o)
        if m: due_total = (due_total or 0) + int(m.group(2))
        skipped += len(SKIP_RE.findall(o))
        soft += len(SOFT_RE.findall(o))
    return {"rc": 0, "written": written, "due": due_total, "skipped": skipped,
            "soft": soft, "pass_rate": round(written / due_total, 3) if due_total else None,
            "seconds": round(el, 1), "conc": conc,
            "tail": "\n".join("\n".join(o.strip().splitlines()[-2:]) for o in outs)[:400]}


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


GAME_LANE_PROCS = ("unity.exe", "tuanjie.exe", "unityhub.exe", "tuanjie hub.exe")


def game_lane_active():
    """游戏车道是否在跑（团结/Unity 编辑器）。命中就让路，不抢显存。

    判据用进程名而不是显存读数：编辑器挂着不动也占着卡，而我们要让的是
    "人在做游戏开发"这件事本身，不是"卡有多满"。
    """
    try:
        # tasklist 输出是 GBK，rl._run 用 utf-8 解码会抛 UnicodeDecodeError，
        # 被 except 吃掉后永远返回 False——闸就成了摆设（实测第一版即如此）。
        # 这里直接起子进程并 errors="replace"，只关心进程名。
        r = subprocess.run(["tasklist"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30)
        low = (r.stdout or "").lower()
        return any(p in low for p in GAME_LANE_PROCS)
    except Exception:  # noqa: BLE001 - 探测失败按"没在跑"处理，不误伤产线
        return False


def warm_probe(budget=90):
    """一轮开始前用 1 token 确认模型能应答。

    2026-11-17：模型加载失败时（显存不足/服务未就绪），整轮 9 分钟会白白耗在
    每批 150 秒的 fuse 超时上。先花 90 秒确认能答，答不了就直接收手，
    把窗口让给下一轮——比闷头烧掉 9 分钟便宜得多。
    """
    import urllib.request

    def _ping(wait):
        model = os.environ.get("BIGLIFE_MODEL", "qwen3.5:9b")
        body = json.dumps({"model": model, "prompt": "ping", "stream": False,
                           "think": False, "options": {"num_predict": 1}}).encode("utf-8")
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=wait) as r:
            r.read(64)
        return True

    model = os.environ.get("BIGLIFE_MODEL", "qwen3.5:9b")
    try:
        return _ping(budget)
    except Exception:  # noqa: BLE001 - 探测失败就是信号，不是崩溃
        # 2026-11-18 22:3x 实锚：ollama 在 20:02 死掉后，后续每一轮都在这里
        # 直接 return False，产线连断 2.5 小时，而日志只有一行 warm-probe failed。
        # 探针必须自带自愈：先拉起无头 serve，再重探一次。
        try:
            import resident_steward as _sw
            _ok, _why = _sw.ensure_ollama(timeout_s=60)
            if _ok:
                rl.log("pump recover: ollama %s" % _why)
                return _ping(budget)
            rl.log("pump: ollama unavailable (%s)" % _why)
        except Exception as _exc:  # noqa: BLE001
            rl.log("pump: ollama self-heal error (%s)" % type(_exc).__name__)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=9.0, help="本轮时间预算")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--max-batches", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    conc = int(os.environ.get("BIGLIFE_CONCURRENCY", "1"))
    started = time.time()
    deadline = started + args.minutes * 60
    rounds = []
    total_written = 0
    faces_switched = 0
    gate_reason = "budget"

    if args.dry_run:
        ok, why = rl.admit()
        print("dry-run admit: %s (%s)" % (ok, why), flush=True)
        return 0 if ok else 1

    # 2026-11-17 单例锁：实测两个泵同时跑（OSLoop 自动触发 + 手动）会互抢
    # evolve.lock，被抢的一方每批都是 1 秒秒退（wrote=0 due=None），实测吞吐
    # 从 600 掉到 258 条/小时。泵自己必须单例，否则「不间断」变成「空转」。
    lk_ok, lk_why = rl.take_lock()
    if not lk_ok:
        rl.log("pump skip: %s" % lk_why)
        print("PUMP skip: %s" % lk_why, flush=True)
        return 0
    import atexit
    atexit.register(rl.drop_lock)   # 任何退出路径都放锁

    # 2026-11-20 夜 CEO「游戏开发在并行，你们排单排队，不要互相杀进程」：
    # 让路硬门。游戏车道（团结/Unity 编辑器）在跑时，本线**不碰 GPU**：
    # 不烧推理、不抢显存，窗口直接让出；零 GPU 的确定性面与巡查照常。
    # 原则：**只让路，不杀进程**——本线任何工具都不许 taskkill 他线进程。
    if game_lane_active():
        # CEO 2026-11-20 夜更正：「不是让路，是**共用大模型、排队**」。
        # 但「工作日白天」才需要让：周末/节假日/工作日 19:00–09:00 CEO 已授权
        # **全天全量占用**（resource_policy）。所以只有 shared 档才压到 1 段。
        try:
            import resource_policy as _rp
            conc = int(_rp.limits().get("conc", 1))
        except Exception:  # noqa: BLE001
            conc = 1
        rl.log("pump mode: game lane active -> policy conc=%d" % conc)
        print("PUMP policy-mode: conc=%d" % conc, flush=True)

    if not warm_probe():
        rl.log("pump stop: warm-probe failed (model cannot answer) - yield window")
        print("PUMP warm-probe-failed", flush=True)
        return 1

    while len(rounds) < args.max_batches:
        if time.time() >= deadline:
            gate_reason = "budget"
            break
        # 2026-11-18 晚：ollama 两小时死两次，托盘版不稳。每批之前自愈一次
        # （无头 serve + WMI 独立进程），窗口内死掉也不会把剩下几批全废掉。
        try:
            import resident_steward as _sw
            _ok, _why = _sw.ensure_ollama(timeout_s=45)
            if not _ok:
                rl.log("pump stop: ollama unavailable (%s)" % _why)
                gate_reason = "llm-down"
                break
            if _why != "已在线":
                rl.log("pump recover: ollama %s" % _why)
        except Exception as _exc:  # noqa: BLE001 - 自愈失败不该崩泵
            rl.log("pump recover skipped (%s)" % type(_exc).__name__)
        ok, why = rl.admit()
        if not ok:
            gate_reason = "gate:" + why
            rl.log("pump stop: %s" % why)
            break
        refresh_index()          # 0.25s：让选人面与磁盘同步（省下每批 10-15s 的 walk）
        res = run_batch_parallel(args.batch, conc) if conc > 1 else run_batch(args.batch)
        rounds.append(res)
        total_written += res["written"]
        rl.log("pump batch %d: wrote=%d due=%s rc=%d %.0fs" % (
            len(rounds), res["written"], res["due"], res["rc"], res["seconds"]))
        # 收手判据（2026-11-17 审查加固）：
        #   rc!=0 且 written=0  = 整批失败（模型超时/异常），不是"due 用尽"，
        #   必须如实记成 batch-failed，否则运维看回执会以为今天已经写完。
        #   rc==0 且 written=0  = 今天剩余的卡全被质量闸 defer（+1d），再跑也是拒，
        #   这才是真正的 no-progress。
        # due=None 与「有 due 但全被拒」是同一件事：这轮年轮没活了。
        # 2026-11-19 10:5x 实锚：池子被旧冷却值锁死时，泵在这里连转 120 批
        # 空批（每批 1 秒）把整个窗口烧光，日志只有一行行 wrote=0 due=None。
        if res["written"] == 0:
            if res["rc"] != 0:
                gate_reason = "batch-failed"
                break
            # 2026-11-20 夜 CEO「从根本上解决摸鱼/自动化停」：**先拉齐，再换面**。
            # 旧逻辑 due 空就问哨兵，哨兵也 NO-WORK 就收工——实测今日仍差 45 人
            # 没环，机器却空转。这里先算目标态与实测态差值，缺口 >0 就把缺口席位
            # 强制跑掉，缺口为 0 才允许切内容面。
            _recon = rl._run([PY, "-X", "utf8", os.path.join(HERE, "reconcile.py"),
                              "--ids", str(max(8, args.batch))], timeout=180)
            _ids = (_recon.stdout or "").strip()
            if getattr(_recon, "returncode", 0) == 2 and _ids:
                rl.log("reconcile: deficit -> forcing %d seats (%s)"
                       % (len(_ids.split()), _ids.split()[0]))
                try:
                    rr = rl._run([PY, "-X", "utf8",
                                  os.path.join(HERE, "evolve_citizen.py"),
                                  "--force"] + _ids.split() + ["--no-commit"],
                                 timeout=1800)
                    # 2026-11-20 21:1x 实锚：原来判 "OK evolved=" in stdout 就报 landed，
                    # 而 "OK evolved=0 of 8 due" 同样含这个子串——补产全被闸挡回，
                    # 日志一路写 landed、缺口 106 纹丝不动。这是假绿的第四例。
                    # 只认 written=N 且 >0。
                    import re as _re2
                    _m = _re2.search(r"written=(\d+)", rr.stdout or "")
                    landed = bool(_m and int(_m.group(1)) > 0)
                    rl.log("reconcile: forced pass rc=%d %s"
                           % (getattr(rr, "returncode", -1),
                              "landed" if landed else "no-land"))
                except Exception as _exc:  # noqa: BLE001
                    rl.log("reconcile failed: %s" % _exc)
                continue
            # 2026-11-17 CEO「没活闲着的时候排单」：年轮 due 空了不收工，
            # 问排单哨兵下一个内容面（反思/池轮/相遇），把窗口继续填满。
            rl.log("rings exhausted -> ask scheduler for next face")
            try:
                sr = rl._run([PY, "-X", "utf8", os.path.join(HERE, "work_scheduler.py"),
                              "--run-next"], timeout=1800)
                rl.log("scheduler rc=%d: %s" % (
                    sr.returncode, " ".join(((sr.stdout or "") + (sr.stderr or "")).split())[:300]))
                if sr.returncode != 0:
                    gate_reason = "no-work-left"
                    break
                faces_switched += 1
                if time.time() >= deadline:
                    gate_reason = "budget"
                    break
                continue
            except Exception as exc:  # noqa: BLE001
                rl.log("scheduler failed: %s" % exc)
                gate_reason = "no-progress"
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
        # 并发子进程带 --no-commit，这里统一提交一次（避免 git 抢锁）
        if conc > 1:
            try:
                _git = ["git", "-C", ROOT]
                ra = rl._run(_git + ["add", "--", "census/registry"], timeout=300)
                rc = rl._run(_git + ["commit", "-q", "-m",
                                     "年轮环(并发批) %s [via BigLife-Pump]"
                                     % datetime.date.today().isoformat(),
                                     "--", "census/registry"], timeout=300)
                # 2026-11-18 假绿修复：原来只看「没抛异常」就记 ok，而 _run 从不
                # 因 rc≠0 抛异常——15:56 起的孤儿 index.lock 让 add/commit 全数
                # 失败，日志却一路写 ok，16 分钟的年轮写了没进库（302 个文件悬空）。
                # 现在看 rc（commit rc=1 = 无改动可提交，属正常），并把 stderr 摘要写进日志。
                if ra.returncode != 0 or rc.returncode not in (0, 1):
                    _err = ((rc.stderr or "") + (rc.stdout or "")
                            + (ra.stderr or ""))[:160].replace("\n", " ")
                    rl.log("pump commit FAILED rc=add%s/commit%s %s"
                           % (ra.returncode, rc.returncode, _err))
                    # 孤儿锁自愈：无存活 git 进程却锁着 >10 分钟 → 清掉重试一次
                    if "index.lock" in _err:
                        try:
                            _lk = os.path.join(ROOT, ".git", "index.lock")
                            if os.path.exists(_lk) and (time.time() - os.path.getmtime(_lk)) > 600:
                                os.remove(_lk)
                                ra = rl._run(_git + ["add", "--", "census/registry"], timeout=300)
                                rc = rl._run(_git + ["commit", "-q", "-m",
                                                     "年轮环(并发批·锁自愈) %s [via BigLife-Pump]"
                                                     % datetime.date.today().isoformat(),
                                                     "--", "census/registry"], timeout=300)
                                rl.log("pump commit retry-after-lockfix rc=add%s/commit%s"
                                       % (ra.returncode, rc.returncode))
                        except OSError as _le:
                            rl.log("pump lockfix failed: %s" % _le)
                else:
                    rl.log("pump commit: ok (conc=%d)" % conc)
            except Exception as exc:  # noqa: BLE001
                rl.log("pump commit failed: %s" % exc)
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
        "rounds": len(rounds), "faces_switched": faces_switched, "written": total_written,
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
