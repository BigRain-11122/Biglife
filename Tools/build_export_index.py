# -*- coding: utf-8 -*-
"""产物总目录：把 census/export 下可打开的单页汇总成一张索引页。

确定性零 LLM：只扫目录里的 .html，读体积与修改时间，输出 census/export/index.html。
不做任何内容解读，避免索引与正本说法不一致。
"""
from __future__ import annotations

import html
import os
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
OUT = os.path.join(EXP, "index.html")

TITLE = {
    "city-dashboard.html": ("城市看板", "全城一人一卡的分布面：物种 / 派系 / 城区 / 代际 / 六轴"),
    "resident-gallery.html": ("居民图谱", "万人名册可搜索：按物种筛选、看最近年轮"),
    "city-map.html": ("城市地图", "七城区分布 + 人口密度与社交锚"),
    "city-social-graph.html": ("社交图谱", "关系网的图形化切片"),
    "city-chronicle.html": ("城市编年史", "全部年轮按日编排的分章长卷"),
    "city-lexicon.html": ("城市语言志", "六轴句 / 像素灵 / 问候 / 问答 / 负面脸语料正本"),
    "city-objects.html": ("城市风物志", "以钩子物件为主角：承载人数 / 主聚城区 / 登记未落册缺口"),
}
ORDER = list(TITLE)


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def rows() -> tuple[str, int]:
    files = [(f, f) for f in os.listdir(EXP) if f.endswith(".html") and f != "index.html"]
    # 社交图谱落在 census/ 根下（历史位置），以相对路径一并收进目录
    if os.path.exists(os.path.join(ROOT, "census", "city-social-graph.html")):
        files.append(("city-social-graph.html", "../city-social-graph.html"))
    files.sort(key=lambda x: (ORDER.index(x[0]) if x[0] in ORDER else 99, x[0]))
    out = []
    for f, href in files:
        p = os.path.join(EXP, f) if f != "city-social-graph.html" else os.path.join(ROOT, "census", f)
        st = os.stat(p)
        size = st.st_size / 1024.0
        ts = datetime.fromtimestamp(st.st_mtime).strftime("%m-%d %H:%M")
        name, desc = TITLE.get(f, (f[:-5], "单页产物"))
        out.append(
            f'<a class="card" href="{esc(href)}"><h3>{esc(name)}<em>{size:.0f} KB</em></h3>'
            f'<p>{esc(desc)}</p><span class="ts">{esc(ts)} 更新 · {esc(f)}</span></a>'
        )
    return "".join(out), len(files)


def main() -> int:
    body, n = rows()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市产物目录 · 硅基生命</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header{{padding:30px 22px 14px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
main{{padding:18px 22px 70px;max-width:1000px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}}
.card{{display:block;background:#14181e;border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:5px;padding:12px 14px;text-decoration:none;color:inherit}}
.card:hover{{background:#171c23}}
.card h3{{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;
align-items:baseline;color:#e6e3dc}}
.card h3 em{{font-style:normal;font:11px/1 ui-monospace,monospace;color:#6a7078}}
.card p{{margin:0 0 8px;font-size:12.5px;color:#b3b0a8;line-height:1.6}}
.ts{{font:11px/1 ui-monospace,monospace;color:#5f656d}}
footer{{padding:18px 22px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
</style></head><body>
<header><h1>城市产物目录</h1>
<div class="sub">{n} 张单页 · 全部由本仓 Tools/ 下的确定性脚本生成（零 LLM）· 目录更新 {now}</div></header>
<main><div class="grid">{body}</div></main>
<footer>本页由 Tools/build_export_index.py 扫描 census/export/ 生成，只读文件名、体积与修改时间。
新增产物页后重跑本脚本即可入目录。</footer>
</body></html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"export-index: {os.path.relpath(OUT, ROOT)}  {len(page.encode('utf-8')) / 1024:.1f} KB  pages={n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())