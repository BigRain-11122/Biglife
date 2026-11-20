# -*- coding: utf-8 -*-
"""居民产线值守席（Steward）：按既定决策宪章自己判、自己动手、全程留台账。

为什么要有它
------------
2026-11-18 这一天暴露的问题全是「有人看见才修」：
  - 男穿旗袍 150 份 / <40 岁戴老花镜 318 份，靠 CEO 抽看才发现；
  - 口头禅复读 58%，提示词里写着「开场句优先取口头禅」；
  - 孤儿 index.lock 让 16 分钟年轮写了没进库，日志却写 commit ok；
  - 813 人日记停摆 25-32 天，游标还显示 next=明天。
本席的职责就是把「我已经想清楚的判据」变成每 10 分钟执行一次的确定性动作，
不再等下一次有人抽看。

决策宪章（硬边界，违反即视为缺陷）
----------------------------------
1. 只动数据与运维态，**绝不改源码**（.py/.ps1/.json 规则表以外的代码）。
   源码缺陷 → 写 STEWARD-ALERT.md 交主控，产线不停。
2. 修人设前必须先有全谱审计数字（避免只修一类再来一轮）。
3. 真实天气顶上去的指标（如大风天的「风」覆盖率）**改阈值不改文案**。
4. 结论一律以子进程返回码为判据，不看「有没有抛异常」。
5. 不删除任何居民数据；写回一律先落回滚档。
6. 不 push git、不改闸门阈值、不启用 CEO 手动禁用的任务、不碰其他公司仓库。
7. 每一次判断与动作都写进 state/STEWARD-LEDGER.md（证据→决定→动作→结果）。

用法
----
  python -X utf8 Tools/resident_steward.py --status     # 只看证据与结论，不动作
  python -X utf8 Tools/resident_steward.py --decide     # 按宪章执行（默认）
  python -X utf8 Tools/resident_steward.py --decide --dry-run
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
CO = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(CO))
STATE = os.path.join(CO, "state")
LEDGER = os.path.join(STATE, "STEWARD-LEDGER.md")
ALERT = os.path.join(STATE, "STEWARD-ALERT.md")
ST = os.path.join(STATE, "steward-state.json")
POLICY = os.path.join(HERE, "batch-policy.json")
LOOPLOG = os.path.join(STATE, "resident-loop.log")
TIMEOUT = 240

# 预授权边界（超出即只报不做）。批大小沿革 6→8→10→15→20（2026-11-17 夜 CEO
# 「放开给你用」定 20），所以上界跟着现有策略走，**绝不擅自把 20 压回 10**——
# 那等于用运维规则去覆盖 CEO 的排产令。
BATCH_MIN, BATCH_MAX = 6, 20
THROUGHPUT_FLOOR = 400.0     # 条/小时
THROUGHPUT_CEIL = 1100.0     # 超过它就不再加批
PASS_FLOOR = 0.80            # 批成功率下限
SCORE_FLOOR = 45.0
STALE_DAYS = 15
TIC_CEIL = 0.35              # 近 7 天口头禅复读上限
AUDIT_EVERY = 3600           # 人设/停更全扫间隔（秒）
SCORE_EVERY = 1800


def _now():
    return datetime.datetime.now()


def _ts():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _run(cmd, timeout=TIMEOUT):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout, cwd=CO)
    except Exception as exc:  # noqa: BLE001
        class R:
            returncode = -1
            stdout = ""
            stderr = str(exc)
        return R()


def load_state():
    try:
        with open(ST, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(st):
    try:
        os.makedirs(STATE, exist_ok=True)
        tmp = ST + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, ST)
    except OSError:
        pass


# ---------------------------------------------------------------- 证据面
def ev_git_lock():
    """孤儿 index.lock：锁存在但无本仓 git 进程持有时才算孤儿。"""
    lk = os.path.join(CO, ".git", "index.lock")
    if not os.path.exists(lk):
        return {"lock": False}
    age = time.time() - os.path.getmtime(lk)
    holders = 0
    try:
        ps = _run(["powershell", "-NoProfile", "-Command",
                   "(Get-CimInstance Win32_Process -Filter \"name='git.exe'\" | "
                   "Where-Object { $_.CommandLine -like '*BigLife*' }).Count"], timeout=60)
        holders = int((ps.stdout or "0").strip() or 0)
    except (ValueError, TypeError):
        holders = 0
    return {"lock": True, "age": int(age), "holders": holders}


def ev_throughput():
    """从运行日志尾算最近一小时产能与成功率。"""
    try:
        with open(LOOPLOG, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()[-400:]
    except OSError:
        return {}
    pat = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] pump batch (\d+): "
                     r"wrote=(\d+) due=(\S+) rc=(-?\d+)")
    cut = _now() - datetime.timedelta(hours=1)
    wrote = due = 0
    last_pump = None
    zero = 0
    fails = []
    for ln in lines:
        m = pat.search(ln)
        if not m:
            continue
        try:
            t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        last_pump = t if last_pump is None or t > last_pump else last_pump
        if t >= cut:
            w = int(m.group(3))
            wrote += w
            # rc≠0 = 整批死掉（不是空池）。游标损坏就是这么被漏掉的。
            try:
                if int(m.group(5)) != 0:
                    fails.append(t)
            except (ValueError, IndexError):
                pass
            try:
                due += int(m.group(4))
            except ValueError:
                pass          # due=None = 当批没有可跑席位（供给空）
            zero = zero + 1 if w == 0 else 0
    if last_pump is None:
        return {"last_pump_min": None}
    return {"wrote": wrote, "due": due,
            "pass": (wrote / due) if due else 0.0,
            "zero_batches": zero,
            "fail_batches": len(fails),
            "last_pump_min": int((_now() - last_pump).total_seconds() // 60)}


def ev_policy():
    try:
        # utf-8-sig：策略文件历史上带过 BOM，用 utf-8 读会 JSONDecodeError
        # 并被吞掉 → 批大小静默回落到 8（CEO 定的 20 一直没生效）。
        with open(POLICY, encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def ev_persona(st, force=False):
    """人设矛盾 + 口头禅复读（全库扫，约 8 秒；按 AUDIT_EVERY 节流）。"""
    last = st.get("last_audit_ts", 0)
    if not force and time.time() - last < AUDIT_EVERY and st.get("audit"):
        return st["audit"]
    r = _run([sys.executable, "-X", "utf8", os.path.join(HERE, "fix_persona_consistency.py"),
              "--audit", "--json"], timeout=600)
    if r.returncode != 0:
        return {"error": (r.stderr or "")[:120]}
    try:
        return json.loads((r.stdout or "").strip())
    except ValueError:
        return {"error": "audit json unparsable"}


def ev_stale(st, force=False):
    """停更 ≥15 天人数（全库扫，节流同审计）。"""
    last = st.get("last_audit_ts", 0)
    if not force and time.time() - last < AUDIT_EVERY and "stale" in st:
        return st["stale"]
    r = _run([sys.executable, "-X", "utf8", os.path.join(HERE, "diag_stale.py"),
              "--days", str(STALE_DAYS), "--top", "0"], timeout=600)
    m = re.search(r"(\d+)\s*人", r.stdout or "")
    return {"stale": int(m.group(1)) if m else None}


def ev_score(st, force=False):
    last = st.get("last_score_ts", 0)
    if not force and time.time() - last < SCORE_EVERY and "score" in st:
        return st["score"]
    r = _run([sys.executable, "-X", "utf8", os.path.join(HERE, "ring_score.py"),
              "--last", "30", "--json"], timeout=300)
    if r.returncode != 0:
        return {"error": (r.stderr or "")[:120]}
    try:
        return json.loads((r.stdout or "").strip())
    except ValueError:
        return {"error": "score json unparsable"}


def ev_ollama():
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as rs:
            return {"up": rs.status == 200}
    except Exception:  # noqa: BLE001
        return {"up": False}


# ---------------------------------------------------------------- 决策面
def decide(ev, policy):
    """返回 [(rule, verdict, action, detail)]。action=None 表示只判不动。"""
    out = []

    # R1 孤儿锁（最危险：会静默吃掉所有提交）
    lk = ev.get("git_lock") or {}
    if lk.get("lock"):
        if lk.get("holders", 0) == 0 and lk.get("age", 0) > 600:
            out.append(("R1 孤儿git锁", "需清", "rm_lock",
                        "锁龄 %ds 且无本仓 git 进程" % lk.get("age", 0)))
        else:
            out.append(("R1 孤儿git锁", "在途", None,
                        "锁龄 %ds，持锁进程 %s 个" % (lk.get("age", 0), lk.get("holders", 0))))
    else:
        out.append(("R1 孤儿git锁", "健康", None, "无锁"))

    # R2 人设硬矛盾（数据层，宪章允许直接修）
    pa = ev.get("persona") or {}
    if pa.get("error"):
        out.append(("R2 人设矛盾", "读不到", None, pa["error"]))
    else:
        n = int(pa.get("cloth_contradictions") or 0)
        if n > 0:
            out.append(("R2 人设矛盾", "需修", "fix_persona", "%d 份硬矛盾" % n))
        else:
            out.append(("R2 人设矛盾", "健康", None, "0 份"))

    # R3 口头禅复读（回归即说明提示词诱因回潮；源码不改，报警给主控）
    if not pa.get("error"):
        ratio = float(pa.get("tic_recent_ratio") or 0)
        if ratio > TIC_CEIL:
            out.append(("R3 口头禅复读", "回潮", "alert",
                        "近 7 天 %.0f%% > %.0f%%（提示词诱因可能回来了）"
                        % (ratio * 100, TIC_CEIL * 100)))
        else:
            out.append(("R3 口头禅复读", "健康", None, "近 7 天 %.1f%%" % (ratio * 100)))

    # R4 停更（自愈已在 due_citizens；这里只判趋势，异常才报）
    sl = ev.get("stale") or {}
    if sl.get("stale") is not None:
        prev = (ev.get("stale_prev") or {}).get("stale")
        cur = sl["stale"]
        if cur == 0:
            out.append(("R4 停更", "健康", None, "0 人"))
        elif prev is not None and cur >= prev and prev > 0:
            out.append(("R4 停更", "不降", "alert",
                        "%d 人（上轮 %d，未下降——自愈可能没生效）" % (cur, prev)))
        else:
            out.append(("R4 停更", "在收", None, "%d 人（上轮 %s）" % (cur, prev)))

    # R5 产能与配比
    tp = ev.get("throughput") or {}
    # 2026-11-20 夜 CEO「巡查频率高一点，不要很久才发现」：判据从 25 分钟收到
    # **12 分钟**＝一个触发周期。漏掉一轮就报，不再等三轮回合。
    if tp.get("last_pump_min") is not None and tp["last_pump_min"] > 12:
        out.append(("R5 泵停摆", "疑似停", "start_task",
                    "最近一批在 %d 分钟前" % tp["last_pump_min"]))
    batch = int((policy.get("batch") or 8))
    zero_batches = int(tp.get("zero_batches") or 0)
    if zero_batches >= 5 and tp.get("wrote", 0) == 0:
        # 2026-11-18 傍晚实锚：due 池被拒稿顺延掏空时，泵会连续 wrote=0 空转。
        # 这是供给面问题，不是配比问题——加批只会更空，必须报出来。
        out.append(("R5 供给", "池空", "alert",
                    "近一轮 %d 批全部 wrote=0（due 池被掏空，查顺延/自愈）" % zero_batches))
    elif tp.get("due") and zero_batches == 0:
        # 只有「最近没有空批」时才调配比：有空批说明是供给问题，加批会更空。
        if tp["pass"] < PASS_FLOOR and batch > BATCH_MIN:
            out.append(("R5 配比", "降批", "set_batch",
                        "成功率 %.0f%% < %.0f%%，批 %d→%d"
                        % (tp["pass"] * 100, PASS_FLOOR * 100, batch, max(BATCH_MIN, batch - 2))))
        elif tp["pass"] >= 0.95 and tp["wrote"] < THROUGHPUT_FLOOR and batch < BATCH_MAX:
            out.append(("R5 配比", "加批", "set_batch",
                        "成功率 %.0f%% 而产能 %d/h 偏低，批 %d→%d"
                        % (tp["pass"] * 100, tp["wrote"], batch, min(BATCH_MAX, batch + 2))))
        else:
            out.append(("R5 配比", "合适", None,
                        "批 %d，成功率 %.0f%%，产能 %d/h"
                        % (batch, tp["pass"] * 100, tp["wrote"])))
    elif tp.get("due"):
        out.append(("R5 配比", "观望", None,
                    "有空批 %d 次，先看供给恢复（批 %d 不动）" % (zero_batches, batch)))

    # R6 质量分
    sc = ev.get("score") or {}
    if sc.get("error"):
        out.append(("R6 质量分", "读不到", None, sc["error"]))
    elif float(sc.get("avg_total") or 0) < SCORE_FLOOR:
        out.append(("R6 质量分", "偏低", "alert",
                    "近 30 条均分 %.1f < %.0f" % (sc.get("avg_total", 0), SCORE_FLOOR)))
    else:
        out.append(("R6 质量分", "达标", None,
                    "近 30 条 %.1f（动词 %.1f）"
                    % (sc.get("avg_total", 0), sc.get("verb_avg", 0))))

    # R7 依赖：ollama 是本线自己的依赖，不是 CEO 禁用的那批 MiniGame 任务。
    # 2026-11-18 晚实锚：三个 ollama 任务全 Disabled，服务挂着没人拉起，
    # 产线整段空转；CLI 里起的子进程又会随会话退出被连坐 —— 故改用 WMI 独立创建。
    if not (ev.get("ollama") or {}).get("up"):
        out.append(("R7 ollama", "不可达", "start_ollama", "11434 无响应，尝试自启"))
    else:
        out.append(("R7 ollama", "健康", None, "11434 在线"))

    # R8 批次连续失败（2026-11-20 16:4x 实锚）：游标被并发写坏时，每一批都在
    # 0 秒内 rc≠0 死掉，而 last_pump 是"刚刚"，R5 判「在跑」——真实停摆 2 小时
    # 无人发现。判据＝最近 5 批里 ≥3 批 rc≠0，动作＝体检并自愈数据面。
    tp2 = ev.get("throughput") or {}
    if int(tp2.get("fail_batches") or 0) >= 3:
        out.append(("R8 批连续失败", "需修", "repair_data",
                    "近 5 批有 %d 批 rc≠0（多为游标/索引损坏）" % tp2["fail_batches"]))
    return out


# ---------------------------------------------------------------- 执行面
def ensure_ollama(timeout_s=45):
    """确保 11434 可用；不可用就用 WMI 起**无头** `ollama.exe serve` 并等到就绪。

    为什么是无头 serve 而不是 `ollama app.exe`：2026-11-18 晚实测托盘版
    两小时内两次死掉（无桌面/资源清理都会带走它），而 serve 是纯服务器进程，
    不依赖 Explorer 与托盘生命周期。
    WMI 创建的意义：父进程是 WmiPrvSE，不在任何计划任务或 CLI 会话的 job
    object 里，任务结束 / 会话退出都不会连坐（本机实测有效）。
    引号必须用 [char]34 拼——PS 5.1 多层引号会把 \\" 吃掉并抛 UnexpectedToken。
    """
    if (ev_ollama() or {}).get("up"):
        return True, "已在线"
    base = os.path.join(os.environ.get("LOCALAPPDATA") or "", "Programs", "Ollama")
    exe = os.path.join(base, "ollama.exe")
    if not os.path.exists(exe):
        return False, "找不到 %s" % exe
    # 2026-11-20 12:5x 实锚：自愈起的 serve **不带任何环境变量**，于是
    # OLLAMA_NUM_PARALLEL 回落到默认、ctx 回到 8192——等于每次自愈都偷偷降级，
    # 而进程还在、模型还驻留，看板只显示"显存占满、GPU 20%"。所以自启必须
    # 复刻调优参数（并行 2、ctx 6144、常驻 30m），否则恢复=掉档。
    ps = ("$e = Join-Path $env:LOCALAPPDATA 'Programs\\Ollama\\ollama.exe'; "
          "if (Test-Path $e) { $q = [char]34 + $e + [char]34 + ' serve'; "
          "$env:OLLAMA_NUM_PARALLEL='2'; $env:OLLAMA_NUM_CTX='6144'; "
          "$env:OLLAMA_KEEP_ALIVE='30m'; $env:OLLAMA_MAX_LOADED_MODELS='1'; "
          "$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create "
          "-Arguments @{ CommandLine = $q }; $r.ReturnValue } else { -2 }")
    r = _run(["powershell", "-NoProfile", "-Command", ps], timeout=120)
    if r.returncode != 0 or (r.stdout or "").strip() not in ("0",):
        return False, "启动失败 rc=%s out=%s" % (r.returncode, (r.stdout or r.stderr or "")[:80])
    waited = 0.0
    while waited < timeout_s:
        time.sleep(1.5)
        waited += 1.5
        if (ev_ollama() or {}).get("up"):
            return True, "已用无头 serve 拉起并就绪（%.0fs）" % waited
    return False, "进程已起但 %.0fs 内 11434 仍未监听" % timeout_s


def act(kind, detail, dry=False):
    """按宪章执行。返回 (ok, 结果说明)。"""
    if kind is None:
        return True, "仅判不动"
    if dry:
        return True, "dry-run 未执行"

    if kind == "rm_lock":
        lk = os.path.join(CO, ".git", "index.lock")
        try:
            os.remove(lk)
            return True, "已删孤儿锁，下一批提交可恢复"
        except OSError as exc:
            return False, "删锁失败：%s" % exc

    if kind == "start_ollama":
        return ensure_ollama()

    if kind == "repair_data":
        # 数据面体检：load_cursor 自带"解析失败→切第一份完整对象→另存损坏件"的自愈，
        # 这里只是把它触发一次，并回读条数确认可用。
        r = _run([sys.executable, "-X", "utf8", "-c",
                  "import sys;sys.path.insert(0,%r);import evolve_citizen as e;"
                  "print(len(e.load_cursor()))" % HERE], timeout=300)
        out = (r.stdout or "").strip()
        if r.returncode == 0 and out.isdigit() and int(out) > 0:
            return True, "数据面自愈完成，游标 %s 条" % out
        return False, "数据面自愈失败 rc=%s %s" % (r.returncode, (r.stderr or "")[:80])

    if kind == "fix_persona":
        r = _run([sys.executable, "-X", "utf8",
                  os.path.join(HERE, "fix_persona_consistency.py"), "--apply"], timeout=900)
        m = re.search(r"扫描 (\d+) 份，需修 (\d+) 份", r.stdout or "")
        if r.returncode == 0 and m:
            return True, "已修 %s 份（回滚档 state/persona-fix-backup.json）" % m.group(2)
        return False, "修复失败 rc=%s %s" % (r.returncode, (r.stderr or "")[:80])

    if kind == "set_batch":
        m = re.search(r"批 \d+→(\d+)", detail)
        if not m:
            return False, "解析新批大小失败"
        newb = int(m.group(1))
        if not (BATCH_MIN <= newb <= BATCH_MAX):
            return False, "超出预授权边界 %d..%d" % (BATCH_MIN, BATCH_MAX)
        try:
            pol = ev_policy()
            old = pol.get("batch")
            pol["batch"] = newb
            with open(POLICY, "w", encoding="utf-8") as fh:
                json.dump(pol, fh, ensure_ascii=False, indent=1)
            return True, "batch %s→%d（下批生效）" % (old, newb)
        except (OSError, ValueError) as exc:
            return False, "写策略失败：%s" % exc

    if kind == "start_task":
        r = _run(["powershell", "-NoProfile", "-Command",
                  "Start-ScheduledTask -TaskName 'BigLife-OSLoop'"], timeout=120)
        if r.returncode == 0:
            return True, "已启动 BigLife-OSLoop"
        return False, "启动失败 %s" % (r.stderr or "")[:80]

    if kind == "alert":
        return True, "已记入 STEWARD-ALERT.md"

    return False, "未知动作 %s" % kind


def write_alert(lines):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(ALERT, "w", encoding="utf-8") as fh:
            fh.write("# STEWARD-ALERT · %s\n\n主控需介入（值守席不做源码改动）：\n\n" % _ts())
            for ln in lines:
                fh.write("- %s\n" % ln)
    except OSError:
        pass


def clear_alert():
    try:
        if os.path.exists(ALERT):
            os.remove(ALERT)
    except OSError:
        pass


def log_ledger(rows, note=""):
    try:
        os.makedirs(STATE, exist_ok=True)
        # 台账轮转：每轮 7 行、10 分钟一次 ≈ 1000 行/天，不轮转会无限长。
        try:
            if os.path.getsize(LEDGER) > 400_000:
                os.replace(LEDGER, os.path.join(
                    STATE, "STEWARD-LEDGER-%s.md" % _now().strftime("%Y%m")))
        except OSError:
            pass
        new = not os.path.exists(LEDGER)
        with open(LEDGER, "a", encoding="utf-8") as fh:
            if new:
                fh.write("# 值守席台账（证据 → 决定 → 动作 → 结果）\n\n"
                         "| 时间 | 规则 | 判定 | 动作 | 结果 |\n|---|---|---|---|---|\n")
            for rule, verdict, kind, detail, res in rows:
                fh.write("| %s | %s | %s | %s | %s |\n"
                         % (_ts(), rule, verdict, kind or "-", res or detail))
            if note:
                fh.write("| %s | 汇总 | - | - | %s |\n" % (_ts(), note))
    except OSError:
        pass


def ev_cadence(n=4):
    """窗口节拍：最近 n 次「pump done」的间隔。

    2026-11-19 13:1x 实锚：只看「最后一批几分钟前」判不出来——窗口本身是活的，
    但**每隔一轮被 MultipleInstances=IgnoreNew 吃掉**（窗口 10-11 分钟 > 10 分钟
    触发间隔），产能腰斩而判活显示「在跑」。所以节拍必须单独成一项证据。
    正常应 ≈600s；>780s 视为隔轮丢失。
    """
    pat = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] pump done")
    ts = []
    try:
        with open(LOOPLOG, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = pat.match(ln)
                if m:
                    try:
                        ts.append(datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                    except ValueError:
                        pass
    except OSError:
        return {"gaps": [], "bad": False}
    ts = ts[-n:]
    gaps = [int((b - a).total_seconds()) for a, b in zip(ts, ts[1:])]
    return {"gaps": gaps, "bad": any(g > 780 for g in gaps), "last": ts[-1] if ts else None}


def night_report(force=False):
    """夜间报告：每天早上自动写 state/NIGHT-REPORT.md，人不在也看得见。

    由值守席写而不是另起任务：CEO 早上只想知道三件事——昨晚断没断、产了多少、
    有没有乱改东西。台账是排查用的流水，这份是给眼睛看的摘要。
    """
    st = load_state()
    today = _now().date().isoformat()
    if not force and st.get("night_report_date") == today:
        return ""
    pat = re.compile(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}):\d{2}:\d{2}\] pump batch \d+: wrote=(\d+)")
    per, last = {}, None
    try:
        with open(LOOPLOG, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = pat.match(ln)
                if not m:
                    continue
                per[m.group(2)] = per.get(m.group(2), 0) + int(m.group(3))
                last = m.group(1) + " " + m.group(2) + ":00"
    except OSError:
        return ""
    gaps = []
    try:
        with open(LOOPLOG, encoding="utf-8", errors="replace") as fh:
            done = [datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                    for m in (re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] pump done", l)
                              for l in fh) if m]
        done = done[-14:]
        gaps = [int((b - a).total_seconds()) for a, b in zip(done, done[1:])]
    except OSError:
        pass
    bad = [g for g in gaps if g > 780]
    rows = ["# 夜间报告 · %s" % _now().strftime("%Y-%m-%d %H:%M"), "",
            "## 一句话", "",
            "- 累计产出 **%d** 条；最后一批 %s" % (sum(per.values()), last or "无"),
            "- 窗口节拍：%s 秒%s" % (
                "/".join(str(g) for g in gaps[-5:]) or "无记录",
                "（%d 次 >780s，触发被丢弃过）" % len(bad) if bad else "（正常）"),
            "", "## 逐小时产量", "", "| 小时 | 条数 |", "|---|---|"]
    for h in sorted(per)[-14:]:
        rows.append("| %s:00 | %d |" % (h, per[h]))
    rows += ["", "## 值守席", ""]
    try:
        with open(LEDGER, encoding="utf-8") as fh:
            tail = [l for l in fh if l.startswith("| 2026-")]
        acts = [l for l in tail[-400:] if l.count("|") >= 5 and "| - |" not in l]
        rows.append("- 台账 %d 行，有动作 %d 条（明细 STEWARD-LEDGER.md）" % (len(tail), len(acts)))
    except OSError:
        rows.append("- 台账读取失败")
    if os.path.exists(ALERT):
        rows.append("- **有告警未清**：%s" % ALERT)
    out = os.path.join(STATE, "NIGHT-REPORT.md")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
    except OSError:
        return ""
    st["night_report_date"] = today
    save_state(st)
    return out


def brief():
    tp = ev_throughput()
    today = _now().date().isoformat()
    pat = re.compile(r"^\[%s \d{2}:\d{2}:\d{2}\] pump batch \d+: wrote=(\d+)" % today)
    total = 0
    try:
        with open(LOOPLOG, encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                m = pat.match(ln)
                if m:
                    total += int(m.group(1))
    except OSError:
        pass
    # 覆盖率：今日有环的居民数
    covered = tot = 0
    rx = re.compile(r"^- %s " % today, re.M)
    reg = os.path.join(CO, "census", "registry")
    try:
        for root, _, fs in os.walk(reg):
            for f in fs:
                if not (f.startswith("C-") and f.endswith(".md")):
                    continue
                tot += 1
                try:
                    with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                        if rx.search(fh.read()):
                            covered += 1
                except OSError:
                    pass
    except OSError:
        pass
    up = (ev_ollama() or {}).get("up")
    age = tp.get("last_pump_min")
    cad = ev_cadence()
    state = "在跑" if (age is not None and age <= 12 and up) else "停摆"
    if state == "在跑" and cad.get("bad"):
        state = "在跑但节拍掉了一轮"
    print("值守席判读：%s%s" % (state, "" if up else "（ollama 不可达）"))
    print("  最后一批：%s" % ("%d 分钟前" % age if age is not None else "无记录"))
    if cad.get("gaps"):
        print("  窗口节拍：%s 秒（正常 ≈600；>780 = 有触发被丢弃）"
              % "/".join(str(g) for g in cad["gaps"][-3:]))
    print("  今日产量：%d 条（覆盖 %d/%d = %.1f%%）"
          % (total, covered, tot, 100.0 * covered / max(1, tot)))
    if tp.get("due"):
        print("  近一小时：%d/%d 成功（%.0f%%），%d 条" % (
            tp.get("wrote", 0), tp["due"], tp["pass"] * 100, tp.get("wrote", 0)))
    print("  提示：完整体检 = python -X utf8 Tools/health_sweep.py")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decide", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--brief", action="store_true")
    ap.add_argument("--night-report", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force-audit", action="store_true")
    a = ap.parse_args()
    if a.brief:
        return brief()
    if a.night_report:
        p = night_report(force=True)
        print(p or "夜间报告生成失败")
        return 0
    live = a.decide and not a.status
    st = load_state()
    # 早上 6–9 点自动出昨夜报告（每天一次），人不在也留一份可读的东西。
    if live and 6 <= _now().hour <= 9:
        try:
            night_report()
        except Exception:  # noqa: BLE001
            pass

    policy = ev_policy()
    ev = {
        "git_lock": ev_git_lock(),
        "throughput": ev_throughput(),
        "policy": policy,
        "persona": ev_persona(st, force=a.force_audit),
        "stale": ev_stale(st, force=a.force_audit),
        "stale_prev": {"stale": st.get("stale_prev_value")},
        "score": ev_score(st, force=a.force_audit),
        "ollama": ev_ollama(),
    }
    rows = decide(ev, policy)

    if not live:
        print("=== 值守席判读 %s ===" % _ts())
        for rule, verdict, kind, detail in rows:
            print("  %-14s %-6s %s" % (rule, verdict, detail))
        return 0

    alerts = []
    out_rows = []
    for rule, verdict, kind, detail in rows:
        ok, res = act(kind, detail, dry=a.dry_run)
        if kind == "alert":
            alerts.append("%s：%s" % (rule, detail))
        out_rows.append((rule, verdict, kind, detail, res if kind else ""))
        if kind and not ok:
            print("! %s %s -> %s" % (rule, kind, res), flush=True)

    if alerts:
        write_alert(alerts)
    else:
        clear_alert()
    log_ledger(out_rows)

    # 节流时间戳与上轮对比值
    st["last_audit_ts"] = time.time() if not ev["persona"].get("error") else st.get("last_audit_ts", 0)
    st["last_score_ts"] = time.time() if not ev["score"].get("error") else st.get("last_score_ts", 0)
    st["audit"] = ev["persona"]
    st["score"] = ev["score"]
    if ev["stale"].get("stale") is not None:
        st["stale_prev_value"] = st.get("stale", {}).get("stale")
        st["stale"] = ev["stale"]
    save_state(st)

    acted = sum(1 for r in out_rows if r[2] and not r[2] == "alert")
    print("[%s] steward: %d 项判定，%d 项动作，%d 条告警"
          % (_ts(), len(out_rows), acted, len(alerts)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
