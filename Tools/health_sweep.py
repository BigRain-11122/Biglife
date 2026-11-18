# -*- coding: utf-8 -*-
"""全面体检哨兵：不等 CEO 问，主动把「哪里可能坏」扫一遍。

Why（CEO 2026-11-18「总是让我来发现问题，你总是重复的解决问题」）：
  复盘结论：12 个问题全是 CEO 撞上才去看的，没有一次是我主动发现。
  根因是没有周期性体检机制。本哨兵把「我会不会坏」拆成五组自动检查，
  每 30 分钟跑一次，异常主动写 ALERT，不等问。

五组（每组独立，单项失败不阻断其他）：
  A 资源      显存/内存/swap/GPU 利用率
  B 生产      成功率/吞吐/失败原因分布（读 pump-receipt 与 os-loop 日志）
  C 质量      ring_score 六维 + 负控自检
  D 任务      BigLife-* 计划任务状态 + LogonType + 已知复活开关是否被启用
  E 依赖      ollama 服务健康 + 模型驻留

输出：state/HEALTH.md（每次覆盖，含逐项判定与建议）
退出码：0 全绿 / 1 有告警

用法：
  python -X utf8 Tools/health_sweep.py
  python -X utf8 Tools/health_sweep.py --quiet
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
STATE = os.path.join(CO, "state")
OUT = os.path.join(STATE, "HEALTH.md")
PY = sys.executable
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# 已知的「复活开关」——2026-11-18 实锚：WorkEnd 在 19:00 跑 resume，把白天禁用的任务全放回来了
REVIVE_SWITCHES = ["bm-a-AutoYield-WorkEnd", "bm-a-AutoYield-WorkStart"]


def _run(cmd, timeout=120):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              creationflags=NO_WINDOW)
    except Exception:  # noqa: BLE001
        class R:
            returncode = -1
            stdout = ""
            stderr = "exception"
        return R()


def _ps(script):
    return ( _run(["powershell", "-NoProfile", "-Command", script]) .stdout or "").strip()


def check_resources():
    out = {"group": "A 资源", "rows": [], "bad": []}
    r = _run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
              "--format=csv,noheader,nounits"])
    try:
        used, total, util = [float(x) for x in (r.stdout or "").strip().split(",")[:3]]
        out["rows"].append("显存 %d/%d MiB（余 %d）· 利用率 %d%%" % (used, total, total - used, util))
        if total - used < 400:
            out["bad"].append("显存余量仅 %d MiB（<400）" % (total - used))
    except Exception:  # noqa: BLE001
        out["bad"].append("nvidia-smi 读取失败")

    mf = _ps("(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory")
    try:
        fg = float(mf) / 1024 / 1024
        out["rows"].append("内存可用 %.1f GB" % fg)
        if fg < 8:
            out["bad"].append("内存可用仅 %.1f GB（<8）" % fg)
    except Exception:  # noqa: BLE001
        out["bad"].append("内存读取失败")

    so = _ps("(Get-Counter '\\Memory\\Pages Output/sec' -SampleInterval 1 -MaxSamples 1 -ErrorAction SilentlyContinue).CounterSamples[0].CookedValue")
    try:
        v = float(so)
        out["rows"].append("swap 写出 %.0f 页/秒" % v)
        if v > 800:
            out["bad"].append("swap 写出 %.0f 页/秒（>800，硬盘在读写）" % v)
    except Exception:  # noqa: BLE001
        out["rows"].append("swap 读取失败（非致命）")
    return out


def check_production():
    out = {"group": "B 生产", "rows": [], "bad": []}
    p = os.path.join(STATE, "pump-receipt.json")
    try:
        with open(p, encoding="utf-8") as f:
            hist = json.load(f).get("history", [])
    except (OSError, ValueError):
        out["bad"].append("pump-receipt.json 不可读")
        return out
    if not hist:
        out["bad"].append("泵从未产出过回执")
        return out
    last = hist[-1]
    rate = (last.get("written", 0) / max(1, last.get("seconds", 1)) * 3600)
    out["rows"].append("上轮 %s：写 %d 条 / %.0f 分钟 → **%.0f 条/小时**（stop=%s）" % (
        last.get("at", "?")[:16], last.get("written", 0),
        last.get("seconds", 0) / 60, rate, last.get("stop", "?")))
    if rate < 400:
        out["bad"].append("吞吐 %.0f 条/小时 低于 400" % rate)

    # 最近 3 轮成功率（written / 期望席数，期望席数≈rounds*4，粗估）
    recent = hist[-3:]
    tot_w = sum(x.get("written", 0) for x in recent)
    tot_r = sum(x.get("rounds", 0) for x in recent)
    if tot_r:
        out["rows"].append("近 3 轮合计 %d 条 / %d 批" % (tot_w, tot_r))

    # 失败原因分布（读最新 run 日志里的 gate 行）
    logs = os.path.join(CO, "logs", "os-loop")
    try:
        files = sorted((os.path.join(logs, f) for f in os.listdir(logs) if f.startswith("run_")),
                       key=os.path.getmtime, reverse=True)[:3]
        reasons = {}
        for fp in files:
            with open(fp, encoding="utf-8", errors="replace") as f:
                for line in f:
                    m = re.search(r"persistent violations \[([^\]]+)\]", line)
                    if m:
                        for v in m.group(1).split(","):
                            k = v.strip().strip("'\"")
                            reasons[k] = reasons.get(k, 0) + 1
        if reasons:
            top = sorted(reasons.items(), key=lambda kv: -kv[1])[:5]
            out["rows"].append("拒稿主因：" + "、".join("%s×%d" % kv for kv in top))
    except OSError:
        pass
    return out


def check_quality():
    out = {"group": "C 质量", "rows": [], "bad": []}
    r = _run([PY, "-X", "utf8", os.path.join(HERE, "ring_score.py"), "--last", "30", "--json"],
             timeout=180)
    try:
        s = json.loads((r.stdout or "").strip())
        out["rows"].append("近 30 条总分 **%.1f**（动词 %.1f / 专名 %.1f / 数字 %.1f）" % (
            s["avg_total"], s["verb_avg"], s["name_avg"], s["num_avg"]))
        if s["avg_total"] < 45:
            out["bad"].append("质量分 %.1f 低于 45" % s["avg_total"])
        if s["verb"] < 30:
            out["bad"].append("动词密度分 %.1f 偏低（「没有事情发生」）" % s["verb"])
    except Exception:  # noqa: BLE001
        out["bad"].append("ring_score 读取失败")

    # 2026-11-18: 120s 会在满载时超时 → stdout 空 → 误报「闸失去分辨力」
    # （15:16 实锚：手动跑 SELFTEST PASS，体检侧 FAIL）。超时放宽到 300s，
    # 失败时把 returncode 写进原因，区分「真 FAIL」与「没跑起来」。
    r2 = _run([PY, "-X", "utf8", os.path.join(HERE, "ring_score.py"), "--selftest"], timeout=300)
    ok = "SELFTEST PASS" in ((r2.stdout or "") + (r2.stderr or ""))
    out["rows"].append("评分器负控/正控自检：%s" % ("PASS" if ok else "**FAIL**"))
    if not ok:
        out["bad"].append("评分器自检 FAIL（rc=%s；rc≠0 多为满载超时，非闸失效）"
                          % getattr(r2, "returncode", "?"))
    # 2026-11-18 新增：人设跨字段矛盾 + 口头禅复读率。
    # 这两类问题此前只能靠人眼发现（男穿旗袍 150 份 / <40 岁戴老花镜 318 份 /
    # 58% 的年轮逐字复用本卡口头禅），必须进自动体检，否则修完又会长回来。
    r3 = _run([PY, "-X", "utf8", os.path.join(HERE, "fix_persona_consistency.py"),
               "--audit", "--json"], timeout=300)
    try:
        p = json.loads((r3.stdout or "").strip())
        out["rows"].append("人设矛盾 %d 份（男穿女装 %d / 幼龄老花镜 %d）" % (
            p["cloth_contradictions"], p["male_feminine"], p["presbyopia_under40"]))
        out["rows"].append("口头禅逐字复读：近 7 天 %.1f%%（全史 %.1f%%，复读≥2 次 %d 人）" % (
            100 * p["tic_recent_ratio"], 100 * p["tic_ratio"], p["tic_citizens_repeat2plus"]))
        if p["cloth_contradictions"] > 0:
            out["bad"].append("人设硬矛盾 %d 份（跑 fix_persona_consistency.py --apply）"
                              % p["cloth_contradictions"])
        if p["tic_recent_ratio"] > 0.35:
            out["bad"].append("近 7 天口头禅复读 %.0f%% 超 35%%（提示词里的口头禅诱因回潮）"
                              % (100 * p["tic_recent_ratio"]))
    except Exception:  # noqa: BLE001
        out["rows"].append("人设一致性检查：读取失败")
    return out


def check_tasks():
    out = {"group": "D 任务", "rows": [], "bad": []}
    for name in REVIVE_SWITCHES:
        st = _ps("(Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue).State" % name)
        if st and st != "Disabled":
            out["bad"].append("复活开关 %s 是 %s（会撤销手动禁用）" % (name, st))
        else:
            out["rows"].append("%s：%s" % (name, st or "不存在"))
    for name in ("BigLife-OSLoop", "BigLife-Watchdog", "BigLife-QualitySentinel"):
        st = _ps("(Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue).State" % name)
        lt = _ps("(Get-ScheduledTask -TaskName '%s' -ErrorAction SilentlyContinue).Principal.LogonType" % name)
        out["rows"].append("%s：%s（%s）" % (name, st or "缺失", lt or "?"))
        if st != "Ready" and st != "Running":
            out["bad"].append("%s 状态异常：%s" % (name, st or "缺失"))
        if lt and lt != "S4U":
            out["bad"].append("%s LogonType=%s（铁律要求 S4U）" % (name, lt))
    return out


def check_deps():
    out = {"group": "E 依赖", "rows": [], "bad": []}
    v = _ps("try { (Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 8).version } catch { '' }")
    if v:
        out["rows"].append("ollama 服务正常 v%s" % v)
    else:
        out["bad"].append("ollama 服务不可用")
    ps = _run(["ollama", "ps"])
    lines = [l for l in (ps.stdout or "").splitlines()[1:] if l.strip()]
    if lines:
        out["rows"].append("模型驻留：" + "；".join(l.split()[0] for l in lines))
    else:
        out["rows"].append("无模型驻留")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    groups = []
    for fn in (check_resources, check_production, check_quality, check_tasks, check_deps):
        try:
            groups.append(fn())
        except Exception as exc:  # noqa: BLE001 - 单组失败不阻断
            groups.append({"group": fn.__name__, "rows": [], "bad": ["检查组异常：%s" % exc]})

    bad_all = [(g["group"], b) for g in groups for b in g["bad"]]
    lines = ["# 全面体检 · %s" % stamp, ""]
    if not bad_all:
        lines += ["**全部通过**", ""]
    else:
        lines += ["**%d 项告警**" % len(bad_all), ""]
        for g, b in bad_all:
            lines.append("- [%s] %s" % (g, b))
        lines.append("")
    lines.append("## 明细")
    lines.append("")
    for g in groups:
        lines.append("### %s" % g["group"])
        for r in g["rows"]:
            lines.append("- %s" % r)
        if g["bad"]:
            for b in g["bad"]:
                lines.append("- ⚠️ %s" % b)
        lines.append("")
    lines.append("> 判不了：人设贴合 / 世界观自洽 / 情感真挚 / 地域方言（此四项交人眼）")
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except OSError as exc:
        print("write failed: %s" % exc, file=sys.stderr)
    if not a.quiet:
        print("HEALTH %s（%d 告警）" % ("OK" if not bad_all else "ALERT", len(bad_all)))
        for g, b in bad_all:
            print("  [%s] %s" % (g, b))
    return 0 if not bad_all else 1


if __name__ == "__main__":
    sys.exit(main())
