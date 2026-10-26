# -*- coding: utf-8 -*-
"""成长档案册生成器（零 LLM·确定性）——把 census/export/growth-archives/ 的档案收成一册可浏览名册。

用法：python -X utf8 Tools/build_growth_gallery.py [--limit N] [--shard-size N]
输出：census/export/city-growth.html（总目录）+ census/export/city-growth-pNN.html（分页正文）

口径：
- 覆盖 = 已出档案 / 全体居民（census/export/citizens-light.jsonl 行数）
- 只读档案 JSON，不改任何正本；字面原样呈现，不做二次改写
- 排序 = 年轮条数降序（故事厚的在前），同条数按编号升序
- 分页 = 按排序切页（默认 1000 席/页），单页体积从 7.5MB 降到 <1MB，浏览器可即开即搜
"""
from __future__ import annotations

import argparse
import glob
import html
import io
import json
import math
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

CSS = """
:root{--bg:#0f1115;--fg:#e6e8ee;--dim:#8b93a7;--line:#232735;--acc:#7ad1c8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 "Microsoft YaHei",system-ui,sans-serif}
header.top{padding:26px 24px 14px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:22px}
h1 a{color:inherit;text-decoration:none}
.meta{color:var(--dim);font-size:13px}
.bar{display:flex;gap:10px;flex-wrap:wrap;padding:14px 24px;position:sticky;top:0;background:rgba(15,17,21,.94);border-bottom:1px solid var(--line);z-index:5}
input,select{background:#171a22;border:1px solid var(--line);color:var(--fg);padding:8px 10px;border-radius:8px;font-size:14px}
input{min-width:260px;flex:1}
main{padding:18px 24px 60px;display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(360px,1fr))}
.c{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#14171e}
.c header{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.c header b{font-size:17px;color:var(--acc)}
.c header span{color:var(--dim);font-size:12px}
.c header i{margin-left:auto;color:var(--dim);font-size:12px;font-style:normal}
.creed{margin:8px 0 2px;color:#cfd5e4}
.hook{margin:2px 0 10px;color:var(--dim);font-size:13px}
.rings{margin:0;padding-left:18px}
.rings li{margin:6px 0;font-size:13.5px}
.rings em{display:block;color:var(--dim);font-style:normal;font-size:11.5px;letter-spacing:.4px}
.mon{margin-top:10px;border-top:1px dashed var(--line);padding-top:8px}
.mon p{margin:4px 0;font-size:13px;color:#a9b1c6}
nav.pg{display:flex;gap:8px;flex-wrap:wrap;padding:6px 24px 18px;align-items:center}
nav.pg a{padding:6px 12px;border:1px solid var(--line);border-radius:8px;color:var(--acc);text-decoration:none;font-size:13px}
nav.pg a.cur{background:#1b2130;color:var(--fg)}
nav.pg a.off{color:var(--dim);pointer-events:none}
nav.pg span{color:var(--dim);font-size:13px}
.toc{padding:18px 24px 60px;display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.toc a{display:block;border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#14171e;color:var(--fg);text-decoration:none}
.toc a:hover{border-color:var(--acc)}
.toc a h3{margin:0 0 6px;font-size:16px;color:var(--acc)}
.toc a p{margin:0;color:var(--dim);font-size:13px}
.dist{padding:0 24px 18px;color:var(--dim);font-size:13px}
"""


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


def shard_name(idx: int) -> str:
    return f"city-growth-p{idx:02d}.html"


def shell(title: str, body: str) -> str:
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n<style>{CSS}</style></head>\n<body>\n{body}\n</body></html>\n"
    )


def nav_html(idx: int, total: int) -> str:
    links = ['<a href="city-growth.html">总目录</a>']
    if idx > 1:
        links.append(f'<a href="{shard_name(idx - 1)}">← 上一页</a>')
    else:
        links.append('<a class="off">← 上一页</a>')
    links.append(f'<span>第 {idx} / {total} 页</span>')
    if idx < total:
        links.append(f'<a href="{shard_name(idx + 1)}">下一页 →</a>')
    else:
        links.append('<a class="off">下一页 →</a>')
    return '<nav class="pg">' + "".join(links) + "</nav>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only render first N after sorting (0 = all)")
    ap.add_argument("--shard-size", type=int, default=1000, help="cards per page (default 1000)")
    args = ap.parse_args()

    items, total_files = cards(args.limit)
    pop = population()
    cover = (total_files * 100.0 / pop) if pop else 0.0
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    size = max(50, args.shard_size)
    total = max(1, math.ceil(len(items) / size))
    opts = "".join(f'<option value="{k}">{esc(v)}</option>' for k, v in DISTRICT_CN.items())

    written = []
    for idx in range(1, total + 1):
        chunk = items[(idx - 1) * size : idx * size]
        lo = (idx - 1) * size + 1
        hi = lo + len(chunk) - 1
        body = (
            '<header class="top"><h1><a href="city-growth.html">成长档案册</a>'
            f"<span class=\"meta\"> · 第 {idx} 页</span></h1>"
            f'<div class="meta">已出档案 <b>{total_files}</b> 席 / 全体居民 <b>{pop}</b> 席 · '
            f"覆盖 <b>{cover:.1f}%</b> · 本页第 <b>{lo}-{hi}</b> 席（按年轮厚薄排序） · 生成 {esc(now)}</div></header>\n"
            f'{nav_html(idx, total)}\n'
            '<div class="bar"><input id="q" type="search" placeholder="本页内搜 编号 / 姓名 / 职业 / 街区">'
            f'<select id="d"><option value="">全部城区</option>{opts}</select></div>\n'
            '<main id="m">' + "".join(render_card(d) for d in chunk) + "</main>\n"
            '<script>\n'
            "const q=document.getElementById('q'),d=document.getElementById('d');\n"
            "function f(){const t=q.value.trim().toLowerCase(),v=d.value;\n"
            "for(const c of document.querySelectorAll('#m .c')){\n"
            "const ok=(!t||c.dataset.q.includes(t))&&(!v||c.dataset.d===v);\n"
            "c.style.display=ok?'':'none';}}\n"
            "q.addEventListener('input',f);d.addEventListener('change',f);\n"
            "</script>"
        )
        path = os.path.join(EXP, shard_name(idx))
        with io.open(path, "w", encoding="utf-8") as fh:
            fh.write(shell(f"成长档案册 第 {idx} 页 · 硅基城市", body))
        written.append((shard_name(idx), len(chunk)))

    dist_count: dict[str, int] = {}
    for d in items:
        k = d.get("district", "") or "—"
        dist_count[k] = dist_count.get(k, 0) + 1
    dist_line = " · ".join(
        f"{esc(DISTRICT_CN.get(k, k))} {v} 席" for k, v in sorted(dist_count.items(), key=lambda kv: -kv[1])
    )
    toc = []
    for idx in range(1, total + 1):
        lo = (idx - 1) * size + 1
        hi = lo + len(items[(idx - 1) * size : idx * size]) - 1
        head = items[(idx - 1) * size]
        toc.append(
            f'<a href="{shard_name(idx)}"><h3>第 {idx} 页 · 第 {lo}-{hi} 席</h3>'
            f'<p>{esc(len(items[(idx - 1) * size : idx * size]))} 席 · 年轮最深：'
            f'{esc(head.get("name", ""))}（{esc(head.get("id", ""))}·{len(head.get("rings") or [])} 圈）</p></a>'
        )
    body = (
        '<header class="top"><h1>成长档案册</h1>'
        f'<div class="meta">已出档案 <b>{total_files}</b> 席 / 全体居民 <b>{pop}</b> 席 · '
        f"覆盖 <b>{cover:.1f}%</b> · 共 <b>{len(items)}</b> 席分 {total} 页 · 生成 {esc(now)}</div></header>\n"
        f'<div class="dist">城区分布：{dist_line}</div>\n'
        '<div class="toc">' + "".join(toc) + "</div>\n"
    )
    with io.open(OUT, "w", encoding="utf-8") as fh:
        fh.write(shell("成长档案册 · 硅基城市", body))

    stats = " ".join(f"{n}={c}" for n, c in written)
    print(
        f"OK city-growth.html pages={total} cards={len(items)} archives={total_files} "
        f"population={pop} coverage={cover:.1f}% [{stats}]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())