# -*- coding: utf-8 -*-
"""城市编年史生成器（确定性·零 LLM·幂等）.

读 census/registry/*/*.md 居民卡里的「年轮」条目，按日期编排成一部可读的城市编年史
单页（census/export/city-chronicle.html）：每日一章——当日环数、参与者数、
样本引文（确定性抽样，按编号哈希取前 N），并可全文检索姓名/编号/引文。

口径：只做汇总与抽样呈现，不改任何卡片；缺年轮/格式异常的行计入 skipped 并在页脚如实标注。
用法：python -X utf8 Tools/build_chronicle.py
"""
import datetime
import glob
import hashlib
import html
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "census", "registry")
OUT = os.path.join(ROOT, "census", "export", "city-chronicle.html")
SAMPLE_PER_DAY = 12

CARD_RE = re.compile(r"^# (C-\d+) · (.+)$")
DIST_RE = re.compile(r"城区\*\*\s*([^｜|]+)")
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「(.+)」\s*\[锚\]")

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城市编年史 · 居民年轮</title>
<style>
:root{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}
header{padding:28px 20px 12px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}
.sub{color:var(--dim);font-size:13px}
.kpi{display:flex;gap:22px;flex-wrap:wrap;padding:14px 20px;border-bottom:1px solid var(--line)}
.kpi div{font-size:13px;color:var(--dim)}
.kpi b{display:block;font-size:20px;color:var(--fg);font-weight:600}
.search{padding:12px 20px;border-bottom:1px solid var(--line)}
input{width:100%;max-width:420px;padding:8px 10px;background:#151a20;border:1px solid var(--line);
color:var(--fg);border-radius:4px;font:14px/1.4 inherit}
.wrap{display:grid;grid-template-columns:170px 1fr;align-items:start}
nav{position:sticky;top:0;max-height:100vh;overflow:auto;padding:14px 10px;border-right:1px solid var(--line)}
nav a{display:flex;justify-content:space-between;padding:4px 8px;color:var(--dim);text-decoration:none;
font:12px/1.5 ui-monospace,monospace;border-radius:3px}
nav a:hover{background:#161b22;color:var(--fg)}
nav a em{font-style:normal;color:var(--acc)}
main{padding:10px 26px 60px;max-width:980px}
.ch{padding:18px 0;border-bottom:1px dashed var(--line)}
.ch h2{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 8px;font-size:16px}
.dt{font:13px/1 ui-monospace,monospace;letter-spacing:.1em;color:var(--acc)}
.meta{font-size:12px;color:var(--dim);font-weight:400}
ol{margin:0;padding-left:0;list-style:none}
li{padding:5px 0;display:grid;grid-template-columns:126px 84px 1fr;gap:10px;font-size:14px}
.who{font:12px/1.9 ui-monospace,monospace;color:var(--dim)}
.d{font-size:12px;color:#6a7078;padding-top:2px}
.q{color:#dedbd4}
.more{margin:6px 0 0;font-size:12px;color:#6a7078}
.hide{display:none}
footer{padding:18px 26px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}
@media(max-width:720px){.wrap{grid-template-columns:1fr}
nav{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:4px}nav a{padding:2px 6px}li{grid-template-columns:1fr}.d{display:none}}
</style></head><body>
<header><h1>硅基城市编年史</h1>
<div class="sub">居民年轮按日编排 · 数据源 census/registry（只读汇总·确定性抽样）· 生成 {{ts}}</div></header>
<div class="kpi">
<div><b>{{rings}}</b>年轮总条数</div><div><b>{{days}}</b>个有记录的日子</div>
<div><b>{{avg}}</b>日均环数</div><div><b>{{cards}}</b>张居民卡</div>
<div><b>{{skipped}}</b>格式异常行（已跳过）</div></div>
<div class="search"><input id="q" placeholder="检索姓名 / 编号 / 引文…" autocomplete="off"></div>
<div class="wrap"><nav id="nav">{{nav}}</nav><main id="main">{{chapters}}</main></div>
<footer>本页由 Tools/build_chronicle.py 确定性生成（零 LLM·幂等）·锚定律见 docs/CODEX.md §九 · 年轮原文见 census/registry/</footer>
<script>
(function(){
 var q=document.getElementById('q'),chs=[].slice.call(document.querySelectorAll('.ch'));
 function run(){
  var k=q.value.trim().toLowerCase(),hit=0;
  chs.forEach(function(c){
   var ok=!k||c.textContent.toLowerCase().indexOf(k)>=0;
   c.classList.toggle('hide',!ok); if(ok)hit++;
  });
  document.title='硅基城市编年史 · '+hit+' 章';
 }
 q.addEventListener('input',run);
})();
</script>
</body></html>
"""


def parse_cards():
    days = {}
    total_rings = 0
    skipped = 0
    cards = sorted(glob.glob(os.path.join(CARDS, "*", "*.md")))
    for path in cards:
        try:
            text = io.open(path, encoding="utf-8").read()
        except Exception:
            skipped += 1
            continue
        first = text.split("\n", 1)[0]
        head = CARD_RE.match(first)
        if head:
            cid, cname = head.group(1), head.group(2).strip()
        else:
            base = os.path.splitext(os.path.basename(path))[0]
            cid, cname = base.split("_")[0], base
            skipped += 1
        m = DIST_RE.search(text)
        dist = m.group(1).strip() if m else ""
        for line in text.splitlines():
            if not line.startswith("- "):
                continue
            r = RING_RE.match(line)
            if not r:
                continue
            date, quote = r.group(1), r.group(2).strip()
            if not quote:
                skipped += 1
                continue
            total_rings += 1
            days.setdefault(date, []).append(
                {"cid": cid, "name": cname, "dist": dist, "q": quote}
            )
    return days, total_rings, skipped, len(cards)


def sample(entries, n=SAMPLE_PER_DAY):
    """确定性抽样：按编号哈希排序，避免每日总是同一批头部居民出镜。"""

    def key(e):
        return hashlib.sha1(e["cid"].encode("utf-8")).hexdigest()

    return sorted(entries, key=key)[:n]


def main():
    days, total, skipped, ncards = parse_cards()
    if not days:
        print("no rings found")
        return 2
    dates = sorted(days, reverse=True)
    chapters = []
    for d in dates:
        entries = days[d]
        picked = sample(entries)
        quotes = "".join(
            '<li><span class="who">%s %s</span><span class="d">%s</span><span class="q">%s</span></li>'
            % (
                html.escape(e["cid"]),
                html.escape(e["name"]),
                html.escape((e["dist"].split("·")[-1].strip() if e["dist"] else "")),
                html.escape(e["q"]),
            )
            for e in picked
        )
        more = (
            '<p class="more">（当日共 %d 环 · 此处抽样 %d 环）</p>' % (len(entries), len(picked))
            if len(entries) > len(picked)
            else ""
        )
        chapters.append(
            '<section class="ch" id="d-%s"><h2><span class="dt">%s</span><span class="meta">'
            "%d 环 · %d 位居民</span></h2><ol>%s</ol>%s</section>"
            % (d, d, len(entries), len({e["cid"] for e in entries}), quotes, more)
        )
    nav = "".join(
        '<a href="#d-%s" data-k="%s">%s<em>%d</em></a>' % (d, d, d[5:], len(days[d])) for d in dates
    )
    avg = round(total / len(dates), 1)
    # 模板用 {{key}} 占位（CSS 里的 % 不能走 % 格式化）
    doc = TEMPLATE
    for _k, _v in (
        ("rings", total),
        ("days", len(dates)),
        ("avg", avg),
        ("cards", ncards),
        ("skipped", skipped),
        ("nav", nav),
        ("chapters", "".join(chapters)),
        ("ts", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
    ):
        doc = doc.replace("{{" + _k + "}}", str(_v))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(doc)
    print(
        json.dumps(
            {
                "out": os.path.relpath(OUT, ROOT).replace("\\", "/"),
                "cards": ncards,
                "rings": total,
                "days": len(dates),
                "avg_per_day": avg,
                "span": [dates[-1], dates[0]],
                "skipped": skipped,
                "sample_per_day": SAMPLE_PER_DAY,
                "bytes": len(doc.encode("utf-8")),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())