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

HEARTBEAT_SHOW = 10
COMMIT_SHOW = 12
NOTE_SHOW = 5
STALE_MIN = 180
PAGED_PREFIX = "city-growth-p"
RING_PAT = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ")
NOTE_PAT = re.compile(r"R(\d{3,5})")


def esc(s: object) -> str:
    return html.escape(str(s), quote=True)


def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def heartbeats() -> list[tuple[datetime, str]]:
    out = []
    for line in read_text(HEARTBEAT).splitlines():
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (.*)$", line.strip())
        if not m:
            continue
        try:
            ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        out.append((ts, m.group(2)))
    return out


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


def age_text(delta: timedelta) -> str:
    mins = int(delta.total_seconds() // 60)
    if mins < 60:
        return f"{mins} 分钟前"
    if mins < 1440:
        return f"{mins // 60} 小时 {mins % 60} 分前"
    return f"{mins // 1440} 天 {mins % 1440 // 60} 小时前"


def main() -> int:
    now = datetime.now()
    hb = heartbeats()
    if hb:
        last_ts, last_line = hb[-1]
        hb_age = age_text(now - last_ts)
        hb_stale = (now - last_ts) > timedelta(minutes=STALE_MIN)
    else:
        last_ts, last_line, hb_age, hb_stale = None, "未取到", "未取到", True

    cm = commits(COMMIT_SHOW)
    pg = pages()
    vol = volumes()
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
<div class="kpi"><b>{vol['citizens']}</b><span>居民（轻量册）</span></div>
</div>

<h2>最近轮次心跳<em>state/heartbeat.txt 尾 {HEARTBEAT_SHOW} 条 · 最后一条：{esc(last_line)}</em></h2>
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
        "city-ops.html written: pages=%d commits=%d hb=%d citizens=%d rings=%d events=%d stale=%d"
        % (len(pg), len(cm), len(hb), vol["citizens"], vol["rings"], vol["events"], len(stale_pages))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())