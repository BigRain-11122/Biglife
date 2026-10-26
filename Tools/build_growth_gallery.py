# -*- coding: utf-8 -*-
"""成长档案册生成器（零 LLM·确定性）——把 census/export/growth-archives/ 的档案收成一页可浏览名册。

用法：python -X utf8 Tools/build_growth_gallery.py [--limit N]
输出：census/export/city-growth.html

口径：
- 覆盖 = 已出档案 / 全体居民（census/export/citizens-light.jsonl 行数）
- 只读档案 JSON，不改任何正本；字面原样呈现，不做二次改写
- 排序 = 年轮条数降序（故事厚的在前），同条数按编号升序
"""
from __future__ import annotations

import argparse
import glob
import html
import io
import json
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
ARCH = os.path.join(EXP, "growth-archives")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-growth.html")

DISTRICT_CN = {
    "GM": "中央市集 GM",
    "QT": "低语巷 QT",
    "MD": "机房区 MD",
    "NS": "北槐街区 NS",
    "OR": "旧站台 OR",
    "RV": "河岸 RV",
}


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def load(path: str) -> dict:
    try:
        return json.load(io.open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def cards(limit: int) -> tuple[list[dict], int]:
    files = sorted(glob.glob(os.path.join(ARCH, "growth-*.json")))
    items = []
    for p in files:
        d = load(p)
        if not d.get("id"):
            continue
        items.append(d)
    items.sort(key=lambda d: (-len(d.get("rings") or []), d.get("id", "")))
    if limit > 0:
        items = items[:limit]
    return items, len(files)


def population() -> int:
    n = 0
    with io.open(LIGHT, encoding="utf-8") as fh:
        for _ in fh:
            n += 1
    return n


def render_card(d: dict) -> str:
    rings = d.get("rings") or []
    lines = d.get("month_lines") or []
    dist = DISTRICT_CN.get(d.get("district", ""), d.get("district", "") or "—")
    ring_html = "".join(
        f'<li><em>{esc(r.get("date", ""))}</em>{esc(r.get("quote", ""))}</li>' for r in rings
    )
    line_html = "".join(f"<p>{esc(t)}</p>" for t in lines[:2])
    search = " ".join(
        [d.get("id", ""), d.get("name", ""), d.get("profession", ""), d.get("block", ""), dist]
    ).lower()
    return (
        f'<article class="c" data-q="{esc(search)}" data-d="{esc(d.get("district", ""))}">'
        f'<header><b>{esc(d.get("name", ""))}</b><span>{esc(d.get("id", ""))}</span>'
        f'<i>{esc(d.get("profession", ""))} · {esc(dist)} · {esc(d.get("age", ""))}岁</i></header>'
        f'<p class="creed">{esc(d.get("creed", ""))}</p>'
        f'<p class="hook">{esc(d.get("hook", ""))}</p>'
        f'<ol class="rings">{ring_html}</ol>'
        f'<div class="mon">{line_html}</div></article>'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only render first N after sorting (0 = all)")
    args = ap.parse_args()

    items, total_files = cards(args.limit)
    pop = population()
    cover = (total_files * 100.0 / pop) if pop else 0.0
    body = "".join(render_card(d) for d in items)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    opts = "".join(
        f'<option value="{k}">{esc(v)}</option>' for k, v in DISTRICT_CN.items()
    )
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>成长档案册 · 硅基城市</title>
<style>
:root{{--bg:#0f1115;--fg:#e6e8ee;--dim:#8b93a7;--line:#232735;--acc:#7ad1c8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 "Microsoft YaHei",system-ui,sans-serif}}
header.top{{padding:26px 24px 14px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px}}
.meta{{color:var(--dim);font-size:13px}}
.bar{{display:flex;gap:10px;flex-wrap:wrap;padding:14px 24px;position:sticky;top:0;background:rgba(15,17,21,.94);border-bottom:1px solid var(--line);z-index:5}}
input,select{{background:#171a22;border:1px solid var(--line);color:var(--fg);padding:8px 10px;border-radius:8px;font-size:14px}}
input{{min-width:260px;flex:1}}
main{{padding:18px 24px 60px;display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(360px,1fr))}}
.c{{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#14171e}}
.c header{{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}}
.c header b{{font-size:17px;color:var(--acc)}}
.c header span{{color:var(--dim);font-size:12px}}
.c header i{{margin-left:auto;color:var(--dim);font-size:12px;font-style:normal}}
.creed{{margin:8px 0 2px;color:#cfd5e4}}
.hook{{margin:2px 0 10px;color:var(--dim);font-size:13px}}
.rings{{margin:0;padding-left:18px}}
.rings li{{margin:6px 0;font-size:13.5px}}
.rings em{{display:block;color:var(--dim);font-style:normal;font-size:11.5px;letter-spacing:.4px}}
.mon{{margin-top:10px;border-top:1px dashed var(--line);padding-top:8px}}
.mon p{{margin:4px 0;font-size:13px;color:#a9b1c6}}
</style></head>
<body>
<header class="top">
<h1>成长档案册</h1>
<div class="meta">已出档案 <b>{total_files}</b> 席 / 全体居民 <b>{pop}</b> 席 · 覆盖 <b>{cover:.1f}%</b> · 本页呈现 {len(items)} 席 · 生成 {esc(now)}</div>
</header>
<div class="bar">
<input id="q" type="search" placeholder="搜 编号 / 姓名 / 职业 / 街区">
<select id="d"><option value="">全部城区</option>{opts}</select>
</div>
<main id="m">{body}</main>
<script>
const q=document.getElementById('q'),d=document.getElementById('d');
function f(){{const t=q.value.trim().toLowerCase(),v=d.value;
for(const c of document.querySelectorAll('#m .c')){{
const ok=(!t||c.dataset.q.includes(t))&&(!v||c.dataset.d===v);
c.style.display=ok?'':'none';}}}}
q.addEventListener('input',f);d.addEventListener('change',f);
</script>
</body></html>
"""
    io.open(OUT, "w", encoding="utf-8").write(page)
    print(f"OK city-growth.html cards={len(items)} archives={total_files} population={pop} coverage={cover:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())