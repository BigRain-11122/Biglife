# -*- coding: utf-8 -*-
"""城市产线实况页（确定性·零 LLM·幂等）。

读本仓既成事实：state/heartbeat.txt（轮次心跳）、git log（最近提交）、
census/export 页面表（新鲜度）、census/registry 居民卡（体量）、
tasks/TASKS.md（最近轮记），产出 census/export/city-ops.html。

只搬运盘上已有的事实，不做推断：取不到的字段写「未取到」，页龄超阈值的标「陈旧」。
用法: python -X utf8 Tools/build_city_ops.py
"""
from __future__ import annotations

import html
import os
import re
import subprocess
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
OUT = os.path.join(EXP, "city-ops.html")
HEARTBEAT = os.path.join(ROOT, "state", "heartbeat.txt")
TASKS = os.path.join(ROOT, "tasks", "TASKS.md")
REGISTRY = os.path.join(ROOT, "census", "registry")
EVENTS = os.path.join(ROOT, "events")
CITIZENS = os.path.join(EXP, "citizens-light.jsonl")
GATE_LEDGER = os.path.join(ROOT, "state", "vram-gate.jsonl")

HEARTBEAT_SHOW = 10
COMMIT_SHOW = 12
NOTE_SHOW = 5
STALE_MIN = 180
PAGED_PREFIX = "city-growth-p"
RING_PAT = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ")
NOTE_PAT = re.compile(r"R(\d{3,5})")
# 无时间戳但确实是状态行的特征（T-20261113-01：R2734 行以 %s 开头、无日期，被解析层静默丢弃）
ORPHAN_PAT = re.compile(r"^(?!\d{4}-\d{2}-\d{2} )\S.*(?:round=R\d+|当前活=|最近实物=|lane=)")


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def parse_heartbeat_text(text: str) -> tuple[list[tuple[datetime, str]], int]:
    """解析心跳文本 → (有效行, 无时间戳状态行条数)。

    无时间戳的状态行会被渲染层丢弃，这里显式计数，让「丢了一条」在页面上看得见
    （T-20261113-01：R2734 行格式串漏参、无日期，静默消失）。
    """
    out = []
    orphans = 0
    for line in text.splitlines():
        s = line.strip().lstrip("\ufeff").strip()
        if not s:
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)$", s)
        if not m:
            if ORPHAN_PAT.match(s):
                orphans += 1
            continue
        try:
            ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        out.append((ts, m.group(2)))
    return out, orphans


def heartbeats() -> tuple[list[tuple[datetime, str]], int]:
    return parse_heartbeat_text(read_text(HEARTBEAT))


def commits(n: int) -> list[tuple[str, str, str]]:
    try:
        proc = subprocess.run(
            ["git", "log", "-n", str(n), "--pretty=%h|%ad|%s", "--date=format:%m-%d %H:%M"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=25,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    rows = []
    for line in (proc.stdout or "").splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def pages() -> list[tuple[str, float, datetime]]:
    rows = []
    try:
        names = os.listdir(EXP)
    except OSError:
        return rows
    for name in names:
        if not name.endswith(".html") or name == "index.html":
            continue
        path = os.path.join(EXP, name)
        try:
            st = os.stat(path)
        except OSError:
            continue
        rows.append((name, st.st_size / 1024.0, datetime.fromtimestamp(st.st_mtime)))
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows


def volumes() -> dict:
    citizens = 0
    for line in read_text(CITIZENS).splitlines():
        if line.strip():
            citizens += 1

    cards = rings = ringed = 0
    for root, _dirs, files in os.walk(REGISTRY):
        for name in files:
            if not name.endswith(".md"):
                continue
            cards += 1
            hit = 0
            try:
                with open(os.path.join(root, name), encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if RING_PAT.match(line):
                            hit += 1
            except OSError:
                continue
            rings += hit
            if hit:
                ringed += 1

    events = 0
    try:
        ev_names = os.listdir(EVENTS)
    except OSError:
        ev_names = []
    for name in ev_names:
        if not name.endswith(".jsonl"):
            continue
        try:
            with open(os.path.join(EVENTS, name), encoding="utf-8", errors="replace") as f:
                events += sum(1 for line in f if line.strip())
        except OSError:
            continue

    return {
        "citizens": citizens,
        "cards": cards,
        "rings": rings,
        "ringed": ringed,
        "events": events,
    }


def notes(n: int) -> list[str]:
    """任务板里最近的轮记行（按轮号降序取 n 条），只截首行。"""
    found = {}
    for raw in read_text(TASKS).splitlines():
        line = raw.strip()
        if not line.startswith("[") and not line.startswith("- ["):
            continue
        m = NOTE_PAT.search(line)
        if not m:
            continue
        num = int(m.group(1))
        if num not in found:
            found[num] = line
    picked = sorted(found.items(), key=lambda kv: kv[0], reverse=True)[:n]
    return [line.lstrip("- ").strip() for _num, line in picked]


def persona_depth() -> dict:
    """人格深化面实读：citizen-persona.jsonl 的行数、习惯覆盖与语体覆盖。"""
    import json

    path = os.path.join(EXP, "citizen-persona.jsonl")
    rows = active = habit_slots = 0
    habits, dialects = set(), set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows += 1
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("blocked"):
                    continue
                active += 1
                hs = [h for h in (r.get("habits") or []) if isinstance(h, str) and h]
                habit_slots += len(hs)
                habits.update(hs)
                if r.get("dialect"):
                    dialects.add(r["dialect"])
    except OSError:
        return {"rows": 0, "active": 0, "habits": 0, "avg": 0.0, "dialects": 0}

    return {
        "rows": rows,
        "active": active,
        "habits": len(habits),
        "avg": (habit_slots / active) if active else 0.0,
        "dialects": len(dialects),
    }


def ring_quality() -> dict:
    """年轮质量待修队列实读：state/ring-quality-queue.json（ring_simile_audit 产出）。

    cap 封顶，队列本身是抽样工作单，不是全量缺陷数——页面须显式标注 cap。
    """
    import json

    path = os.path.join(ROOT, "state", "ring-quality-queue.json")
    empty = {"generated": "未取到", "since": "未取到", "cap": 0, "items": [], "tags": []}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return empty
    if not isinstance(data, dict):
        return empty
    items = [i for i in (data.get("items") or []) if isinstance(i, dict)]
    order, counted = [], {}
    for it in items:
        for tag in str(it.get("reason") or "").split("+"):
            tag = tag.strip()
            if not tag:
                continue
            key = "sim" if tag.startswith("sim=") else tag
            if key not in counted:
                order.append(key)
                counted[key] = 0
            counted[key] += 1
    return {
        "generated": str(data.get("generated") or "未取到"),
        "since": str(data.get("since") or "未取到"),
        "cap": int(data.get("cap") or 0),
        "items": items,
        "tags": [(k, counted[k]) for k in order],
    }


def age_text(delta: timedelta) -> str:
    mins = int(delta.total_seconds() // 60)
    if mins < 60:
        return f"{mins} 分钟前"
    if mins < 1440:
        return f"{mins // 60} 小时 {mins % 60} 分前"
    return f"{mins // 1440} 天 {mins % 1440 // 60} 小时前"


def read_gate_rows(path: str | None = None) -> list[dict]:
    """state/vram-gate.jsonl 实读（evolve_citizen.vram_guard 每次探针追加一行）。

    取不到/坏行一律跳过：闸台账是观测面，缺了不该让整页失败。
    """
    import json

    rows: list[dict] = []
    try:
        with open(path or GATE_LEDGER, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if isinstance(obj, dict) and obj.get("state") in ("ok", "yield", "degraded", "starved"):
                    rows.append(obj)
    except OSError:
        return []
    return rows


def gate_summary(rows: list[dict], now: datetime | None = None, window_hours: int = 24) -> dict:
    """纯函数：窗口内探针/让路计数 + 最近一次探针与最近一次让路（供 selftest 直喂）。"""
    now = now or datetime.now()
    since = now - timedelta(hours=window_hours)

    def ts_of(row):
        try:
            return datetime.strptime(str(row.get("ts") or ""), "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

    seen = []
    for row in rows:
        ts = ts_of(row)
        if ts is None:
            continue
        seen.append((ts, row))
    seen.sort(key=lambda x: x[0])

    probes = yields = starved = 0
    last_yield = None
    for ts, row in seen:
        if ts < since:
            continue
        probes += 1
        if row.get("state") == "yield":
            yields += 1
            last_yield = (ts, row)
        elif row.get("state") == "starved":
            starved += 1

    last = seen[-1] if seen else None
    return {
        "probes": probes,
        "yields": yields,
        "starved": starved,
        "share": ((yields + starved) / probes) if probes else 0.0,
        "window_hours": window_hours,
        "last_ts": last[0] if last else None,
        "last_state": (last[1].get("state") if last else ""),
        "last_rows": [r for _, r in seen[-8:]],
        "last_yield": last_yield,
    }


def main() -> int:
    now = datetime.now()
    hb, hb_orphans = heartbeats()
    if hb:
        last_ts, last_line = hb[-1]
        hb_age = age_text(now - last_ts)
        hb_stale = (now - last_ts) > timedelta(minutes=STALE_MIN)
    else:
        last_ts, last_line, hb_age, hb_stale = None, "未取到", "未取到", True

    cm = commits(COMMIT_SHOW)
    pg = pages()
    vol = volumes()
    pd = persona_depth()
    rq = ring_quality()
    gate = gate_summary(read_gate_rows(), now)
    nt = notes(NOTE_SHOW)

    stale_pages = [p for p in pg if (now - p[2]) > timedelta(minutes=STALE_MIN)]

    hb_rows = "\n".join(
        '<tr><td class="t">%s</td><td>%s</td></tr>' % (esc(ts.strftime("%m-%d %H:%M:%S")), esc(txt))
        for ts, txt in reversed(hb[-HEARTBEAT_SHOW:])
    )
    commit_rows = "\n".join(
        '<tr><td class="t">%s</td><td class="h">%s</td><td>%s</td></tr>' % (esc(t), esc(h), esc(s))
        for h, t, s in cm
    ) or '<tr><td colspan="3">未取到（git 不可用）</td></tr>'

    # 分页册（city-growth-p01..）折叠成一行，避免一册占满整张表
    page_rows_items = [
        (name, kb, ts, name) for name, kb, ts in pg if not name.startswith(PAGED_PREFIX)
    ]
    paged = [p for p in pg if p[0].startswith(PAGED_PREFIX)]
    if paged:
        page_rows_items.append(
            (
                f"{PAGED_PREFIX}*.html（{len(paged)} 页）",
                sum(p[1] for p in paged),
                max(p[2] for p in paged),
                f"{PAGED_PREFIX}01.html",
            )
        )
    page_rows = "\n".join(
        '<tr><td><a href="%s">%s</a></td><td class="n">%.0f KB</td>'
        '<td class="t">%s</td><td>%s</td></tr>'
        % (
            esc(href),
            esc(label),
            kb,
            esc(ts.strftime("%m-%d %H:%M")),
            "陈旧" if (now - ts) > timedelta(minutes=STALE_MIN) else "新",
        )
        for label, kb, ts, href in page_rows_items
    ) or '<tr><td colspan="4">未取到导出页</td></tr>'

    note_rows = "\n".join("<li>%s</li>" % esc(x) for x in nt) or "<li>未取到轮记</li>"

    rq_tags = " · ".join("%s %d" % (esc(k), n) for k, n in rq["tags"]) or "未取到"
    rq_rows = "\n".join(
        '<tr><td class="h">%s</td><td>%s</td><td class="t">%s</td><td>%s</td></tr>'
        % (esc(it.get("id") or "?"), esc(it.get("name") or "?"),
           esc(it.get("date") or "?"), esc(it.get("reason") or ""))
        for it in rq["items"][:8]
    ) or '<tr><td colspan="4">未取到待修队列</td></tr>'

    def _gate_label(row):
        return "让路（批未启动）" if row.get("state") == "yield" else "放行"

    def _gate_mem(row):
        try:
            return "%d%% · %d/%d MiB" % (
                int(round(float(row.get("frac") or 0) * 100)),
                int(row.get("used_mib") or 0),
                int(row.get("total_mib") or 0),
            )
        except (TypeError, ValueError):
            return "未取到"

    def _gate_holders(row):
        offs = [o for o in (row.get("offenders") or []) if isinstance(o, dict)]
        if not offs:
            return "未取到" if row.get("state") == "yield" else "—"
        parts = []
        for o in offs[:4]:
            mib = o.get("mib")
            parts.append("%s %dMiB" % (esc(o.get("name") or "?"), mib) if mib
                         else esc(o.get("name") or "?"))
        return " · ".join(parts)

    gate_rows = "\n".join(
        '<tr><td class="t">%s</td><td>%s</td><td class="n">%s</td><td>%s</td></tr>'
        % (esc(datetime.strptime(str(r.get("ts")), "%Y-%m-%dT%H:%M:%S").strftime("%m-%d %H:%M"))
           if str(r.get("ts") or "").count("-") == 2 else "未取到",
           esc(_gate_label(r)), esc(_gate_mem(r)), _gate_holders(r))
        for r in reversed(gate["last_rows"])
    ) or '<tr><td colspan="4">未取到排产闸台账（尚无 vram_guard 探针）</td></tr>'
    gate_last = ("%s（%s）" % ({"yield": "让路", "starved": "显存饥饿",
                               "degraded": "降级放行"}.get(gate["last_state"], "放行"),
                              age_text(now - gate["last_ts"]))) if gate["last_ts"] else "未取到"

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市产线实况 · BigLife</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a;--warn:#c96a5a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header{{padding:28px 22px 14px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
main{{padding:18px 22px 70px;max-width:1080px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px;margin-bottom:22px}}
.kpi{{background:#14181e;border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:5px;padding:12px 14px}}
.kpi b{{display:block;font-size:22px;font-weight:600;letter-spacing:.02em}}
.kpi span{{color:var(--dim);font-size:12px}}
.kpi.bad{{border-left-color:var(--warn)}}
h2{{font-size:16px;margin:26px 0 10px;font-weight:600;color:#e6e3dc}}
h2 em{{font-style:normal;color:var(--dim);font-size:12px;font-weight:400;margin-left:8px}}
table{{width:100%;border-collapse:collapse;background:#14181e;border:1px solid var(--line);border-radius:5px}}
th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}}
th{{color:var(--dim);font-weight:500;background:#12161b}}
tr:last-child td{{border-bottom:0}}
td.t{{font:12px/1.6 ui-monospace,monospace;color:#7f8690;white-space:nowrap}}
td.h{{font:12px/1.6 ui-monospace,monospace;color:var(--acc);white-space:nowrap}}
td.n{{font:12px/1.6 ui-monospace,monospace;color:#a9a59d;white-space:nowrap}}
a{{color:#cbb38a;text-decoration:none}}
a:hover{{text-decoration:underline}}
ul{{margin:0;padding-left:20px}}
li{{font-size:13px;color:#b9b6ae;margin:4px 0}}
.note{{color:var(--dim);font-size:12px;margin-top:10px}}
footer{{padding:18px 22px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
</style></head><body>
<header><h1>城市产线实况</h1>
<div class="sub">本页由 Tools/build_city_ops.py 确定性生成（零 LLM）· 生成于 {esc(now.strftime("%Y-%m-%d %H:%M"))} · 数据全部取自本仓盘上与 git</div></header>
<main>
<div class="kpis">
<div class="kpi{' bad' if hb_stale else ''}"><b>{esc(hb_age)}</b><span>最近一次轮次心跳</span></div>
<div class="kpi"><b>{esc(cm[0][1] if cm else '未取到')}</b><span>最近提交时间</span></div>
<div class="kpi{' bad' if stale_pages else ''}"><b>{len(stale_pages)}</b><span>超过 {STALE_MIN} 分钟未刷新的页</span></div>
<div class="kpi{' bad' if hb_orphans else ''}"><b>{hb_orphans}</b><span>无时间戳状态行（被丢弃，需修）</span></div>
<div class="kpi"><b>{vol['citizens']}</b><span>居民（轻量册）</span></div>
<div class="kpi{' bad' if rq['items'] else ''}"><b>{len(rq['items'])}</b><span>年轮待修队列（cap {rq['cap'] or '未取到'}）</span></div>
<div class="kpi{' bad' if gate['yields'] else ''}"><b>{gate['yields']}/{gate['probes']}</b><span>近 {gate['window_hours']}h 排产闸让路次数（探针数分母）</span></div>
</div>

<h2>最近轮次心跳<em>state/heartbeat.txt 尾 {HEARTBEAT_SHOW} 条 · 最后一条：{esc(last_line)} · 无时间戳状态行 <b>{hb_orphans}</b> 条（有时间戳才会进本表）</em></h2>
<table><thead><tr><th>时间</th><th>记录</th></tr></thead><tbody>
{hb_rows or '<tr><td colspan="2">未取到心跳</td></tr>'}
</tbody></table>

<h2>最近产物提交<em>git log 尾 {COMMIT_SHOW} 条</em></h2>
<table><thead><tr><th>时间</th><th>commit</th><th>说明</th></tr></thead><tbody>
{commit_rows}
</tbody></table>

<h2>页面新鲜度<em>census/export 下的单页 · 按更新时间倒序</em></h2>
<table><thead><tr><th>页面</th><th>体积</th><th>更新</th><th>状态</th></tr></thead><tbody>
{page_rows}
</tbody></table>

<h2>库体量<em>居民卡与事件流实读</em></h2>
<table><thead><tr><th>面</th><th>数值</th></tr></thead><tbody>
<tr><td>居民（citizens-light）</td><td class="n">{vol['citizens']}</td></tr>
<tr><td>居民卡文件</td><td class="n">{vol['cards']}</td></tr>
<tr><td>年轮条目</td><td class="n">{vol['rings']}</td></tr>
<tr><td>已有年轮的居民</td><td class="n">{vol['ringed']}</td></tr>
<tr><td>城市事件（events/*.jsonl）</td><td class="n">{vol['events']}</td></tr>
</tbody></table>

<h2>人格深化面<em>census/export/citizen-persona.jsonl 实读 · 确定性派生</em></h2>
<table><thead><tr><th>面</th><th>数值</th></tr></thead><tbody>
<tr><td>人格记录</td><td class="n">{pd['rows']}</td></tr>
<tr><td>参与居民（非荣誉席位）</td><td class="n">{pd['active']}</td></tr>
<tr><td>习惯基因实际覆盖</td><td class="n">{pd['habits']}</td></tr>
<tr><td>人均习惯条数</td><td class="n">{pd['avg']:.2f}</td></tr>
<tr><td>方言语体覆盖</td><td class="n">{pd['dialects']}</td></tr>
</tbody></table>

<h2>年轮质量面<em>state/ring-quality-queue.json 实读 · 抽样工作单 cap {rq['cap'] or '未取到'}（不是全量缺陷数）· 生成 {esc(rq['generated'])} · 回溯起点 {esc(rq['since'])}</em></h2>
<table><thead><tr><th>缺陷口径</th><th colspan="3">分类计数（同一条可计入多个口径）</th></tr></thead><tbody>
<tr><td>合计</td><td colspan="3" class="n">{rq_tags}</td></tr>
</tbody></table>
<table><thead><tr><th>席位</th><th>姓名</th><th>年轮日期</th><th>判负理由</th></tr></thead><tbody>
{rq_rows}
</tbody></table>
<div class="note">全量复读/过短/模板三段判负由 Tools/ring_simile_audit.py 产出；修复走 19:00 后让路窗的 evolve 批（LLM 复写），本页只呈现队列，不改写任何年轮文本。</div>

<h2>排产闸（显存）<em>state/vram-gate.jsonl 实读 · 阈值 {esc('%.0f%%' % (float(gate['last_rows'][-1].get('limit') or 0.9) * 100)) if gate['last_rows'] else '90%'} · 最近一次 {esc(gate_last)} · 近 {gate['window_hours']}h 让路 {gate['yields']}/{gate['probes']} 次 · 显存饥饿 {gate['starved']} 次</em></h2>
<table><thead><tr><th>探针时间</th><th>结果</th><th>显存占用</th><th>GPU 会话（WDDM 不报单进程显存·非诊断依据）</th></tr></thead><tbody>
{gate_rows}
</tbody></table>
<div class="note">「让路」＝GPU 被别的活占着，本轮年轮/相遇/反思批不启动（脚本自退，不是故障、也不计入零产出事故）；「显存饥饿」＝暖探针（1 token）无应答，整批零座席空烧退出（T-20261114-05）；「降级放行」＝桌面图形占卡但探针通过，批照跑；「放行」＝探针通过、批可开工。占用者取自 nvidia-smi compute-apps（Windows WDDM 不报单进程显存，故多数只见进程名）。</div>

<h2>最近轮记<em>tasks/TASKS.md 内的轮号行</em></h2>
<ul>
{note_rows}
</ul>
<div class="note">本页只汇总盘上既有事实，不写推断值；取不到的字段一律写「未取到」。</div>
</main>
<footer>BigLife · 硅基生命城市 · 产线实况页（确定性产物）</footer>
</body></html>
"""

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(
        "city-ops.html written: pages=%d commits=%d hb=%d orphans=%d citizens=%d rings=%d events=%d stale=%d"
        " persona=%d habit_genes=%d ring_queue=%d gate=%d/%d"
        % (
            len(pg), len(cm), len(hb), hb_orphans, vol["citizens"], vol["rings"], vol["events"],
            len(stale_pages), pd["active"], pd["habits"], len(rq["items"]),
            gate["yields"], gate["probes"],
        )
    )
    return 0


SELFTEST_CASES = [
    # (输入文本, 期望有效行数, 期望无时间戳状态行数)
    ("2026-11-13 10:19:56 os-loop: round done exit=0\n", 1, 0),
    ("%s | round=R2734 | lane=qc | 当前活=X\n", 0, 1),
    ("hello world\n", 0, 0),
    ("2026-11-13 10:29:28 os-loop: round done exit=0\n%s | round=R1 | lane=qc\n", 1, 1),
    ("2026-13-45 99:99:99 broken ts round=R9\n", 0, 0),
    ("\ufeff2026-11-13 03:15:13 round=R2675 | lane=product\n", 1, 0),
]


GATE_CASES = [
    # (台账行, 期望窗口内探针数, 期望窗口内让路数)
    ([], 0, 0),
    ([{"ts": "2026-11-14T14:23:49", "state": "yield", "frac": 0.97}], 1, 1),
    ([{"ts": "2026-11-14T10:00:00", "state": "ok", "frac": 0.4},
      {"ts": "2026-11-14T13:00:00", "state": "yield", "frac": 0.97},
      {"ts": "2026-11-14T14:00:00", "state": "ok", "frac": 0.5}], 3, 1),
    # 窗口外（>24h）不计入，但「最近一次」仍要有值
    ([{"ts": "2026-11-01T09:00:00", "state": "yield", "frac": 0.99}], 0, 0),
    # 坏时间戳整行跳过，不当成探针
    ([{"ts": "not-a-ts", "state": "yield", "frac": 0.99}], 0, 0),
]


def gate_selftest() -> int:
    now = datetime.strptime("2026-11-14T15:00:00", "%Y-%m-%dT%H:%M:%S")
    fails = 0
    for rows, want_probes, want_yields in GATE_CASES:
        got = gate_summary(rows, now)
        if (got["probes"], got["yields"]) != (want_probes, want_yields):
            fails += 1
            print("GATE FAIL probes=%d(want %d) yields=%d(want %d) :: %r"
                  % (got["probes"], want_probes, got["yields"], want_yields, rows[:1]))
    # 最近一次让路必须是窗口内那一条（窗口外的不许冒充）
    got = gate_summary(GATE_CASES[2][0], now)
    if not got["last_yield"] or got["last_yield"][0] != datetime(2026, 11, 14, 13, 0):
        fails += 1
        print("GATE FAIL last_yield dedup")
    return fails


def selftest() -> int:
    fails = 0
    for text, want_rows, want_orphans in SELFTEST_CASES:
        rows, orphans = parse_heartbeat_text(text)
        ok = (len(rows) == want_rows and orphans == want_orphans)
        if not ok:
            fails += 1
            print("FAIL rows=%d(want %d) orphans=%d(want %d) :: %r"
                  % (len(rows), want_rows, orphans, want_orphans, text[:60]))
    fails += gate_selftest()
    print("selftest: %d probes, %d fail" % (len(SELFTEST_CASES) + len(GATE_CASES) + 1, fails))
    return 1 if fails else 0


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    raise SystemExit(main())