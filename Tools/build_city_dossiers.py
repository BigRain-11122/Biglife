# -*- coding: utf-8 -*-
"""城市深层档案册生成器（零 LLM·确定性）——解析 census/registry 卡片，挑深年轮居民成册。

用法：python -X utf8 Tools/build_city_dossiers.py [--top 240] [--min-rings 4]
输出：census/export/city-dossiers.html
"""
from __future__ import annotations

import argparse
import glob
import html
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "census", "export", "city-dossiers.html")

LABEL_RE = re.compile(r"\*\*(.+?)\*\*[ \t]*([^｜\n*]*)")
RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})[ \t]+(.+)$", re.M)
DIST_RE = re.compile(r"城区\**\s*([^｜\n]+)")


def parse_card(path: str) -> dict:
    text = io.open(path, encoding="utf-8").read()
    head = text.splitlines()[0] if text else ""
    m = re.match(r"^#\s*(C-\d+)\s*·\s*(.+)$", head)
    cid, name = (m.group(1), m.group(2).strip()) if m else ("", head.strip())

    fields: dict[str, str] = {}
    for label, value in LABEL_RE.findall(text):
        value = value.strip()
        if value and label not in fields:
            fields[label] = value
    # 物种行里带城区
    dist = ""
    dm = re.search(r"\*\*城区\*\*\s*([^｜\n*]+)", text)
    if dm:
        dist = dm.group(1).strip()

    rings = []
    if "**年轮**" in text:
        block = text.split("**年轮**", 1)[1].split("**进化**", 1)[0]
        for date, body in RING_RE.findall(block):
            body = body.replace("[锚]", "").strip()
            rings.append((date, body))

    return {
        "id": cid,
        "name": name,
        "dist": dist,
        "prof": fields.get("职业", ""),
        "species": fields.get("物种", ""),
        "creed": fields.get("信条", ""),
        "hook": fields.get("钩子", ""),
        "lang": fields.get("语言", ""),
        "evo": fields.get("进化", ""),
        "rings": rings,
    }


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render(rows: list[dict], total_cards: int) -> str:
    cards = []
    for r in rows:
        ring_html = "\n".join(
            '<li><time>%s</time><p>%s</p></li>' % (esc(d), esc(b)) for d, b in r["rings"]
        )
        cards.append(
            """<article class="card" data-k="{k}">
  <h2>{name}<span class="id">{id}</span></h2>
  <p class="meta">{dist} · {prof}</p>
  <p class="creed">{creed}</p>
  <p class="hook">{hook}</p>
  <ol class="rings">{rings}</ol>
  <p class="evo">{evo}</p>
</article>""".format(
                k=esc((r["name"] + " " + r["dist"] + " " + r["prof"]).lower()),
                name=esc(r["name"]),
                id=esc(r["id"]),
                dist=esc(r["dist"]),
                prof=esc(r["prof"]),
                creed=esc(r["creed"]),
                hook=esc(r["hook"]),
                rings=ring_html,
                evo=esc(r["evo"]),
            )
        )

    template = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市深层档案册 · BigLife</title>
<style>
:root{--bg:#12141a;--fg:#e6e6e6;--dim:#8d94a3;--line:#262a33;--accent:#7fb0d8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "Noto Sans SC","Microsoft YaHei",sans-serif}
header{padding:28px 20px 12px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:20px;font-weight:600}
.sub{color:var(--dim);font-size:13px}
.tools{padding:12px 20px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;border-bottom:1px solid var(--line)}
input{background:#1a1d25;border:1px solid var(--line);color:var(--fg);padding:7px 10px;border-radius:4px;min-width:240px;font:inherit}
.count{color:var(--dim);font-size:13px}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:14px;padding:18px 20px 60px}
.card{border:1px solid var(--line);border-radius:6px;padding:14px 16px;background:#171a21}
.card h2{margin:0 0 4px;font-size:16px;font-weight:600}
.id{color:var(--dim);font-size:12px;margin-left:8px;font-weight:400}
.meta{margin:0 0 8px;color:var(--dim);font-size:13px}
.creed{margin:0 0 6px;color:var(--accent)}
.hook{margin:0 0 10px;color:var(--dim);font-size:13px}
.rings{margin:0;padding-left:18px}
.rings li{margin:0 0 8px}
.rings time{color:var(--dim);font-size:12px;display:block}
.rings p{margin:2px 0 0}
.evo{margin:10px 0 0;color:var(--dim);font-size:12px;border-top:1px solid var(--line);padding-top:6px}
footer{padding:16px 20px 40px;color:var(--dim);font-size:12px;border-top:1px solid var(--line)}
</style></head>
<body>
<header>
<h1>城市深层档案册</h1>
<p class="sub">深年轮居民 __N__ 位 / 全城卡片 __TOTAL__ 张 · 每位附全部年轮原文（[锚] 实锚城市实况）</p>
</header>
<div class="tools">
<input id="q" type="search" placeholder="搜姓名 / 城区 / 职业">
<span class="count" id="c">显示 __N__ / __N__</span>
</div>
<main id="grid">
__CARDS__
</main>
<footer>本页由 Tools/build_city_dossiers.py 确定性生成（零 LLM），锚定律见 docs/CODEX.md §九。</footer>
<script>
var q=document.getElementById('q'),c=document.getElementById('c'),cards=[].slice.call(document.querySelectorAll('.card'));
q.addEventListener('input',function(){var v=q.value.trim().toLowerCase(),n=0;
cards.forEach(function(el){var hit=!v||el.dataset.k.indexOf(v)>=0;el.style.display=hit?'':'none';if(hit)n++;});
c.textContent='显示 '+n+' / '+cards.length;});
</script>
</body></html>
"""
    return (template
            .replace("__N__", str(len(rows)))
            .replace("__TOTAL__", str(total_cards))
            .replace("__CARDS__", "\n".join(cards)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=240)
    ap.add_argument("--min-rings", type=int, default=4)
    args = ap.parse_args()

    paths = glob.glob(os.path.join(ROOT, "census", "registry", "*", "C-*.md"))
    rows = []
    for p in paths:
        try:
            r = parse_card(p)
        except Exception:
            continue
        if r["id"] and len(r["rings"]) >= args.min_rings:
            rows.append(r)

    rows.sort(key=lambda r: (-len(r["rings"]), r["id"]))
    rows = rows[: args.top]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(rows, len(paths)))

    size = os.path.getsize(OUT) / 1024.0
    print("city-dossiers: %s  %.1f KB  residents=%d  cards=%d  min_rings=%d"
          % (os.path.relpath(OUT, ROOT), size, len(rows), len(paths), args.min_rings))
    if rows:
        print("rings_total=%d  top=%s(%d)" % (sum(len(r["rings"]) for r in rows),
                                              rows[0]["name"], len(rows[0]["rings"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())