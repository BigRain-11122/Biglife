# -*- coding: utf-8 -*-
"""产物总目录：把 census/export 下可打开的单页汇总成一张索引页。

确定性零 LLM：只扫目录里的 .html，读体积与修改时间，输出 census/export/index.html。
不做任何内容解读，避免索引与正本说法不一致。
"""
from __future__ import annotations

import html
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
OUT = os.path.join(EXP, "index.html")

TITLE = {
    "city-coverage.html": ("库覆盖缺口", "可管四维覆盖（信条/认知/年轮/成长）+ 缺口名单 + 相遇容量面 + 机器清单 coverage-backlog.jsonl"),
    "city-dashboard.html": ("城市看板", "全城一人一卡的分布面：物种 / 派系 / 城区 / 代际 / 六轴"),
    "resident-gallery.html": ("居民图谱", "万人名册可搜索：按物种筛选、看最近年轮"),
    "city-map.html": ("城市地图", "七城区分布 + 人口密度与社交锚"),
    "city-social-graph.html": ("社交图谱", "关系网的图形化切片"),
    "city-chronicle.html": ("城市编年史", "全部年轮按日编排的分章长卷"),
    "city-lexicon.html": ("城市语言志", "六轴句 / 像素灵 / 问候 / 问答 / 负面脸语料正本"),
    "city-objects.html": ("城市风物志", "以钩子物件为主角：承载人数 / 主聚城区 / 登记未落册缺口"),
    "city-districts.html": ("城区志", "六城区逐区人口 / 物种 / 派系 / 职业 / 街区 / 六轴聚合与代表居民"),
    "city-life.html": ("城市日常面", "此刻全城在做什么 / 四轴需求 / 好奇缺口名单 / 怪癖与可见面"),
    "city-voices.html": ("城市声音馆", "八席试点三档试听对照：参数档 / Kokoro fp32 / int8 体积与时长"),
    "gene-ledger.html": ("基因总账", "全类别登记 vs 在册承载 / 覆盖率 / 未落册选题池"),
    "city-relations.html": ("城市人情志", "关系边总数 / 类型与来源 / 枢纽人物 / 城区互往 / 相逢录"),
    "city-meets.html": ("相遇编年史", "全库相遇留痕按日编排：同一幕双向对读 / 单面留痕 / 跨城区一幕"),
    "meet-candidates.html": ("相遇候选单", "今晚该让谁遇见谁：同城区 + 双方已有年轮 + 从未相遇，每人最多进一对（确定性选人）"),
    "city-today.html": ("今日日报", "当天全量年轮（不抽样）+ 城区分布 + 与昨日对比"),
    "city-dossiers.html": ("深层档案册", "深年轮居民逐人档案：全部年轮原文 / 信条 / 钩子 / 进化史"),
    "city-growth.html": ("成长档案册", "逐人成长档案：年轮原文 / 当月心声 / 档案覆盖进度（分页 · 单页 <1.1MB）"),
    "city-rumors.html": ("城市流言录", "当天年轮经口耳相传的变形长链：源起居民 / 每一跳怎么说 / 走街时间（RUMOR-CHAIN v1.0 确定性引擎）"),
    "city-ops.html": ("产线实况页", "轮次心跳 / 最近提交 / 页面新鲜度 / 库体量：产线正在跑什么摊成一张表（确定性读盘·零 LLM）"),
    "city-ring-quality.html": ("年轮品质透视", "相邻复读 / 偏短空洞 / 全局模板句三查：按居民排出的重写队列（确定性·零 LLM），对应 state/ring-quality-queue.json"),
}
# 成长档案册的分页正文不入总目录（总目录只收册子的入口页，避免一册被拆成十几张卡）
PAGED_PREFIX = "city-growth-p"
ORDER = list(TITLE)


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def rows() -> tuple[str, int]:
    files = [
        (f, f)
        for f in os.listdir(EXP)
        if f.endswith(".html") and f != "index.html" and not f.startswith(PAGED_PREFIX)
    ]
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


NAV_MARK = "<!--bl-nav:index-->"
NAV_TMPL = (
    NAV_MARK
    + '<div style="position:fixed;left:12px;top:12px;z-index:9999">'
      '<a href="{href}" style="display:inline-block;padding:5px 10px;background:rgba(20,24,30,.86);'
      'border:1px solid #303740;border-radius:4px;color:#c8a06a;'
      'font:12px/1 \'Songti SC\',Georgia,serif;text-decoration:none">← 产物目录</a></div>'
)


def ensure_nav() -> int:
    """给每张产物页补一个回总目录的固定入口（幂等，只认标记行）。

    页面各自由不同脚本生成、样式互不相通，故导航条自带内联样式，插在 <body> 之后。
    索引页自己跳过；链接一律按目标页到 index.html 的相对层级给出。
    """
    targets: list[tuple[str, str]] = []
    for f in sorted(os.listdir(EXP)):
        if f.endswith(".html") and f != "index.html":
            targets.append((os.path.join(EXP, f), "index.html"))
    social = os.path.join(ROOT, "census", "city-social-graph.html")
    if os.path.exists(social):
        targets.append((social, "export/index.html"))

    patched = 0
    for path, href in targets:
        with open(path, encoding="utf-8", errors="replace") as fh:
            page = fh.read()
        if NAV_MARK in page:
            continue
        m = re.search(r"<body[^>]*>", page, re.I)
        if not m:
            continue
        page = page[: m.end()] + NAV_TMPL.format(href=href) + page[m.end() :]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(page)
        patched += 1
    return patched


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
    nav = ensure_nav()
    print(f"export-index: {os.path.relpath(OUT, ROOT)}  {len(page.encode('utf-8')) / 1024:.1f} KB  pages={n}  nav_patched={nav}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())