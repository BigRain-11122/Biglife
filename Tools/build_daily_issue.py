# -*- coding: utf-8 -*-
"""城市今日日报生成器（确定性·零 LLM·幂等）.

读 census/registry 居民卡里「今天」的年轮，按城区编成一张可读当日报纸单页
（census/export/city-today.html）：今日环数 / 参与居民 / 城区分布 / 与昨日对比 /
逐城区引文长卷 + 检索。

与 city-chronicle.html 的区别：编年史是全部日期的抽样长卷（每日 12 条），
本页只做「今天」且不抽样（全量），是每天都会长出新品的一页。

用法：python -X utf8 Tools/build_daily_issue.py [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import html
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "census", "registry")
# 荣誉席与锚定席不落 registry，但同属真实居民（创始家庭三席即在此）。
# 口径与 qc_census 对齐：registry ** + anchors ** + reserved，按编号去重。
EXTRA_CARD_DIRS = (
    os.path.join(ROOT, "census", "anchors"),
    os.path.join(ROOT, "census", "reserved"),
)
OUT = os.path.join(ROOT, "census", "export", "city-today.html")
BEHAVIOR = os.path.join(ROOT, "census", "export", "citizen-behavior.jsonl")
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
BEHAVIOR_LAST = os.path.join(ROOT, "state", "behavior-last.json")

BUCKET_CN = {"day": "白天", "eve": "傍晚", "night": "深夜", "morn": "清晨"}
WEATHER_CN = {"clear": "晴", "cloud": "多云", "rain": "雨", "fog": "雾", "snow": "雪"}
SOUND_CN = {"fest": "节日声景", "alarm": "警报声景", "": "静默"}

CARD_RE = re.compile(r"^# (C-\d+) · (.+)$", re.M)
DIST_RE = re.compile(r"城区\*\*\s*([^｜|\n]+)")
JOB_RE = re.compile(r"\*\*职业\*\*\s*([^｜|\n]+)")
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「(.+)」\s*\[锚\]", re.M)


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def dist_label(d: str) -> str:
    """英文代号城区补「城」字（GAME→GAME城），中文地名原样呈现。"""
    if d.endswith(("城", "区", "网", "桥")):
        return d
    return d + "城" if d.isascii() else d


def card_paths() -> list[str]:
    """全部居民卡片：registry 一层 + anchors/reserved 递归（去重按编号）。"""
    paths = sorted(glob.glob(os.path.join(CARDS, "*", "C-*.md")))
    for d in EXTRA_CARD_DIRS:
        paths += sorted(glob.glob(os.path.join(d, "**", "C-*.md"), recursive=True))
    return paths


def load(target: str):
    """返回 {date: [(id, name, dist, job, text), ...], ...} 与居民总数."""
    by_day: dict[str, list[tuple]] = {}
    seen: set[str] = set()
    for path in card_paths():
        with io.open(path, encoding="utf-8") as f:
            txt = f.read()
        head = CARD_RE.search(txt)
        if not head:
            continue
        cid, name = head.group(1), head.group(2).strip()
        if cid in seen:  # 同一编号多份卡（锚定席/荣誉席与 registry 重叠）只计一次
            continue
        seen.add(cid)
        dm = DIST_RE.search(txt)
        # 城区字段有两种写法：「GAME 城 · X026 城门区」与老卡「北外滩·治理岸 · 档案馆区」
        # 取首段统称（城/区名）作为分组键，两种写法都得到同一层级的城区名。
        dist = re.split(r"[·・]", dm.group(1))[0].strip() if dm else "未标城区"
        dist = dist.replace(" ", "") or "未标城区"
        jm = JOB_RE.search(txt)
        job = (jm.group(1).strip() if jm else "").split("：")[0][:28]
        for m in RING_RE.finditer(txt):
            day, text = m.group(1), m.group(2).strip()
            by_day.setdefault(day, []).append((cid, name, dist, job, text))
    return by_day, len(seen)


def live_block(limit_slots: int = 6, samples: int = 3) -> str:
    """此刻城市面：读行为导出面（R3 再生面）与居民轻量面，零推断。

    导出面缺位时返回空串（页面不留占位假数据）。取样=按编号排序取前 N 位，
    同一天同一数据面重跑逐字节一致。
    """
    if not os.path.exists(BEHAVIOR):
        return ""
    names: dict[str, tuple[str, str, bool]] = {}
    if os.path.exists(LIGHT):
        with io.open(LIGHT, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                names[r.get("id", "")] = (
                    r.get("name", ""),
                    r.get("profession", ""),
                    r.get("faction") == "honored",
                )
    counts: collections.Counter = collections.Counter()
    members: dict[str, list[str]] = {}
    total = 0
    with io.open(BEHAVIOR, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            total += 1
            slot = r.get("slot") or ("（未标槽位）")
            counts[slot] += 1
            members.setdefault(slot, []).append(r.get("id", ""))

    meta: dict = {}
    if os.path.exists(BEHAVIOR_LAST):
        try:
            with io.open(BEHAVIOR_LAST, encoding="utf-8") as f:
                meta = json.load(f)
        except (ValueError, OSError):
            meta = {}
    face_ts = str(meta.get("ts", ""))[:16].replace("T", " ")
    ctx = " · ".join(
        x for x in (
            BUCKET_CN.get(meta.get("time_bucket", ""), meta.get("time_bucket", "")),
            WEATHER_CN.get(meta.get("weather_kind", ""), meta.get("weather_kind", "")),
            SOUND_CN.get(meta.get("sound", ""), meta.get("sound", "")),
        ) if x
    )

    order = sorted(counts, key=lambda s: (-counts[s], s))
    top = order[:limit_slots]
    maxn = max((counts[s] for s in top), default=1)
    rows = []
    for slot in top:
        n = counts[slot]
        w = max(2, int(round(n * 100.0 / maxn)))
        who = []
        for cid in sorted(members[slot]):
            nm, job, honored = names.get(cid, ("", "", False))
            if honored:  # 荣誉席（CEO 家人三席）不作代表样本（身份细节脱敏律）
                continue
            tag = nm or cid
            if job:
                tag += "·" + job
            who.append(f'<span class="who">{esc(cid)} {esc(tag)}</span>')
            if len(who) >= samples:
                break
        rows.append(
            f'<div class="lrow"><span class="lslot">{esc(slot)}</span>'
            f'<span class="lbar"><span class="lbf" style="width:{w}%"></span></span>'
            f'<span class="ln">{n}</span></div>'
            f'<div class="lwho">{"".join(who)}</div>'
        )

    head = f"行为面 {esc(total)} 位居民" + (f" · {esc(ctx)}" if ctx else "")
    if face_ts:
        head += f" · 面生成 {esc(face_ts)}"
    return (
        '<section class="now"><h2>此刻城市<em>' + esc(head) + "</em></h2>"
        '<p class="nnote">当下各槽位人数与代表居民（槽位来自行为导出面 R3 再生面；'
        "代表=按编号取前 3 位，非抽样推断）。</p>"
        + "".join(rows)
        + "</section>"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="目标日期，默认今天")
    args = ap.parse_args()
    today = args.date or datetime.date.today().isoformat()
    prev = (datetime.date.fromisoformat(today) - datetime.timedelta(days=1)).isoformat()

    by_day, cards = load(today)
    rows = by_day.get(today, [])
    n_prev = len(by_day.get(prev, []))

    people = sorted({r[0] for r in rows})
    dists: dict[str, list[tuple]] = {}
    for r in rows:
        dists.setdefault(r[2], []).append(r)
    order = sorted(dists, key=lambda d: (-len(dists[d]), d))

    delta = len(rows) - n_prev
    delta_txt = "持平" if delta == 0 else ("多 %d 条" % delta if delta > 0 else "少 %d 条" % -delta)

    # KPI
    kpi = (
        f"<div><b>{len(rows)}</b>今日年轮</div>"
        f"<div><b>{len(people)}</b>今日开口的居民</div>"
        f"<div><b>{len(dists)}</b>城区</div>"
        f"<div><b>{n_prev}</b>昨日年轮</div>"
        f"<div><b>{delta_txt}</b>较昨日</div>"
        f"<div><b>{cards}</b>居民卡总数</div>"
    )

    # 城区条
    maxn = max((len(v) for v in dists.values()), default=1)
    bars = []
    for d in order:
        n = len(dists[d])
        w = max(2, int(round(n * 100.0 / maxn)))
        bars.append(
            f'<a class="bar" href="#d-{esc(d)}"><span class="bl">{esc(d)}</span>'
            f'<span class="bt"><span class="bf" style="width:{w}%"></span></span>'
            f"<span class=\"bn\">{n}</span></a>"
        )

    # 城区长卷
    secs = []
    for d in order:
        items = []
        for cid, name, _d, job, text in dists[d]:
            items.append(
                f'<li data-k="{esc(cid + " " + name + " " + job + " " + text)}">'
                f'<span class="who">{esc(cid)}</span>'
                f'<span class="nm">{esc(name)}</span>'
                f'<span class="jb">{esc(job)}</span>'
                f'<span class="q">{esc(text)}</span></li>'
            )
        secs.append(
            f'<section id="d-{esc(d)}"><h2>{esc(dist_label(d))}'
            f'<em>{len(dists[d])} 条年轮 · {len({r[0] for r in dists[d]})} 位居民</em></h2>'
            f"<ol>{''.join(items)}</ol></section>"
        )

    empty = (
        '<p class="empty">今日尚无年轮。年轮线只在非让路窗生产（工作日 09:00-19:00 停批），'
        "19:00 后随夜窗自动补写。</p>"
        if not rows
        else ""
    )

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    now_html = live_block()
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市今日日报 · {esc(today)} · 硅基生命</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header{{padding:28px 20px 12px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
.kpi{{display:flex;gap:22px;flex-wrap:wrap;padding:14px 20px;border-bottom:1px solid var(--line)}}
.kpi div{{font-size:12.5px;color:var(--dim)}}
.kpi b{{display:block;font-size:20px;color:var(--fg);font-weight:600}}
.bars{{padding:12px 20px 16px;border-bottom:1px solid var(--line)}}
.bar{{display:grid;grid-template-columns:64px 1fr 46px;gap:10px;align-items:center;
padding:3px 0;color:inherit;text-decoration:none;font:12.5px/1.6 ui-monospace,monospace}}
.bl{{color:var(--dim)}}
.bt{{display:block;height:8px;background:#171c23;border-radius:2px;overflow:hidden}}
.bf{{display:block;height:100%;background:var(--acc);opacity:.55}}
.bn{{text-align:right;color:var(--acc)}}
.search{{padding:12px 20px;border-bottom:1px solid var(--line)}}
.now{{padding:14px 20px 16px;border-bottom:1px solid var(--line)}}
.now h2{{margin:0 0 4px}}
.nnote{{margin:0 0 10px;color:var(--dim);font-size:12px}}
.lrow{{display:grid;grid-template-columns:150px 1fr 46px;gap:10px;align-items:center;padding:3px 0;
font:12.5px/1.6 ui-monospace,monospace}}
.lslot{{color:#c9c4ba}}
.lbar{{display:block;height:7px;background:#171c23;border-radius:2px;overflow:hidden}}
.lbf{{display:block;height:100%;background:#7fa8c8;opacity:.6}}
.ln{{text-align:right;color:#7fa8c8}}
.lwho{{padding:0 0 6px;font-size:12px;color:#6f757d}}
.lwho .who{{margin-right:14px}}
input{{width:100%;max-width:420px;padding:8px 10px;background:#151a20;border:1px solid var(--line);
color:var(--fg);border-radius:4px;font:14px/1.4 inherit}}
main{{padding:8px 24px 60px;max-width:1000px}}
section{{padding:16px 0;border-bottom:1px dashed var(--line)}}
h2{{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 8px;font-size:16px}}
h2 em{{font-style:normal;font:12px/1.5 ui-monospace,monospace;color:var(--dim)}}
ol{{margin:0;padding:0;list-style:none}}
li{{display:grid;grid-template-columns:76px 84px 148px 1fr;gap:10px;padding:5px 0;font-size:14px;align-items:start}}
.who{{font:12px/1.9 ui-monospace,monospace;color:var(--dim)}}
.nm{{font-size:13px;color:#e6e3dc}}
.jb{{font-size:11.5px;color:#6a7078;padding-top:2px}}
.q{{color:#dedbd4}}
.hide{{display:none}}
.empty{{padding:20px;color:var(--dim)}}
footer{{padding:18px 24px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
@media(max-width:760px){{li{{grid-template-columns:1fr}}.jb{{display:none}}}}
</style></head><body>
<header><h1>城市今日日报 · {esc(today)}</h1>
<div class="sub">当天全量年轮（不抽样）· 数据源 census/registry 只读 · 生成 {esc(ts)}</div></header>
<div class="kpi">{kpi}</div>
<div class="bars">{''.join(bars)}</div>
{now_html}
<div class="search"><input id="q" placeholder="检索姓名 / 编号 / 职业 / 引文…" autocomplete="off"></div>
<main>{empty}{''.join(secs)}</main>
<footer>本页由 Tools/build_daily_issue.py 确定性生成（零 LLM·幂等）·锚定律见 docs/CODEX.md §九 ·
年轮原文见 census/registry/ · 全日期长卷见 city-chronicle.html</footer>
<script>
(function(){{
var q=document.getElementById('q');
q.addEventListener('input',function(){{
  var v=q.value.trim().toLowerCase();
  document.querySelectorAll('li').forEach(function(li){{
    li.classList.toggle('hide', v!=='' && li.dataset.k.toLowerCase().indexOf(v)<0);
  }});
  document.querySelectorAll('section').forEach(function(s){{
    var vis=s.querySelectorAll('li:not(.hide)').length;
    s.classList.toggle('hide', vis===0);
  }});
}});
}})();
</script>
</body></html>
"""
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("WROTE %s rings=%d people=%d districts=%d prev=%d cards=%d"
          % (os.path.relpath(OUT, ROOT), len(rows), len(people), len(dists), n_prev, cards))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())