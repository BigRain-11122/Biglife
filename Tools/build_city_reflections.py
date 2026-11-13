# -*- coding: utf-8 -*-
"""城市反思录面板（确定性·零 LLM·幂等）

读 census/reflections.jsonl（Tools/reflect_citizen.py 产出，append-only）+
census/export/citizens-light.jsonl（取名字/城区/职业），产出
census/export/city-reflections.html：

  1) 总账 KPI：反思条数 / 覆盖居民 / 覆盖率 / 今日新增 / 平均字数
  2) 近 14 日产出条：每天落几条（看得见这条腿是活着还是又停了）
  3) 最新反思卡：居民 + 城区 + 职业 + 洞察原文 + 该次合成所读年轮日期
  4) 产能口径：按当前日产能，覆盖全城需多少天（差距摆在明面上）

为什么单开这一面（缺什么补什么）：
  - 反思线（中层记忆合成，≤40 字一条）自 2026-09-25 上线后长期是「盘上有数据、
    没有任何可见面」：CEO 面上看不到它是否在跑、跑到哪、质量如何。2026-11-13
    起该腿恢复产出（31 条），但此前 15 天静默停摆无人发现，正是因为缺这一面。
  - city-growth.html 把它并进逐人档案（只在单居民页里可读），
    city-ring-* 系列只管年轮质量，都不回答「这条腿今天有没有产出、覆盖了多少人」。

口径注：reflections.jsonl 为 append-only，每居民 30 天冷却；同日多批合法。
用法: python -X utf8 Tools/build_city_reflections.py
注意：直接跑本脚本会覆盖页面、连带抹掉 build_export_index 注入的导航条
（<!--bl-nav:index-->）——改完页面后必须紧随跑一次 build_export_index.py。
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
REFL = os.path.join(ROOT, "census", "reflections.jsonl")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT_HTML = os.path.join(EXP, "city-reflections.html")
TOP = 24
TREND_DAYS = 14

import sys

sys.path.insert(0, os.path.join(ROOT, "Tools"))
from build_city_meets import DISTRICT_CN  # noqa: E402

CSS = """
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e;--red:#e5605c;--grn:#3fb950}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:12px;margin-bottom:28px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
.kpi{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
.kpi.warn b{color:var(--warm)}
.kpi.bad b{color:var(--red)}
.kpi.good b{color:var(--grn)}
section{margin-bottom:28px}
h2{font-size:15px;color:var(--dim);font-weight:600;letter-spacing:.4px;margin:0 0 12px;text-transform:uppercase}
.row{display:flex;align-items:center;gap:10px;margin:5px 0;font-size:13px}
.lab{flex:0 0 92px;color:var(--fg);font-variant-numeric:tabular-nums}
.track{flex:1;height:8px;background:#161b22;border-radius:4px;overflow:hidden}
.track i{display:block;height:100%;background:linear-gradient(90deg,#3d7dd6,#63b3ff);border-radius:4px}
.track i.zero{background:#30363d}
.num{flex:0 0 120px;text-align:right;color:var(--dim);font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.card{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card header b{font-size:14px}
.card time{color:var(--warm);font-size:11px;font-variant-numeric:tabular-nums}
.meta{color:var(--dim);font-size:11px;margin:2px 0 8px}
.insight{margin:0;font-size:14px;color:#c9d1d9}
.rings{color:#57606a;font-size:10.5px;margin-top:8px}
.note{color:var(--dim);font-size:12.5px;line-height:1.8;margin:10px 0 0}
.note a{color:var(--acc);text-decoration:none}
footer{margin-top:36px;color:#57606a;font-size:11px;border-top:1px solid var(--line);padding-top:14px}
"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def load_jsonl(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def main():
    rows = load_jsonl(REFL)
    light = {r.get("id"): r for r in load_jsonl(LIGHT) if r.get("id")}
    today = datetime.date.today()
    pop = len(light)

    total = len(rows)
    uniq = len({r.get("id") for r in rows})
    by_date = collections.Counter((r.get("date") or "")[:10] for r in rows)
    today_n = by_date.get(today.isoformat(), 0)
    lens = [len((r.get("insight") or "").strip()) for r in rows]
    avg_len = (sum(lens) / float(len(lens))) if lens else 0.0
    long_ones = sum(1 for n in lens if n > 40)

    # 近 TREND_DAYS 日（含今日）逐日条数，缺失日如实留 0——停摆要肉眼可见
    days = []
    for i in range(TREND_DAYS - 1, -1, -1):
        d = today - datetime.timedelta(days=i)
        days.append((d.isoformat(), by_date.get(d.isoformat(), 0)))
    peak = max([n for _d, n in days] + [1])
    bars = []
    for iso, n in days:
        bars.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i class="%s" style="width:%.1f%%"></i></span>'
            '<span class="num">%d 条</span></div>'
            % (esc(iso[5:]), "" if n else "zero", (n / float(peak)) * 100.0, n)
        )

    # 按人合并：同一居民多次反思只取最新（append-only ⇒ 后行覆盖前行）
    latest = {}
    for r in rows:
        cid = r.get("id")
        if not cid:
            continue
        d = (r.get("date") or "")[:10]
        if cid not in latest or d >= (latest[cid].get("date") or "")[:10]:
            latest[cid] = r

    ordered = sorted(latest.values(), key=lambda r: ((r.get("date") or "")[:10], r.get("id") or ""), reverse=True)
    cards = []
    for r in ordered[:TOP]:
        cid = r.get("id")
        info = light.get(cid) or {}
        name = r.get("name") or info.get("name") or cid
        district = DISTRICT_CN.get(info.get("district") or "", info.get("district") or "未落区")
        prof = info.get("profession") or info.get("species") or ""
        used = r.get("rings_used") or []
        cards.append(
            '<article class="card"><header><b>%s</b><time>%s</time></header>'
            '<p class="meta">%s · %s · %s</p><p class="insight">%s</p>'
            '<p class="rings">合成所读年轮：%s</p></article>'
            % (esc(name), esc((r.get("date") or "")[:10]), esc(cid), esc(district), esc(prof),
               esc(r.get("insight") or "（空）"),
               esc("、".join((u or "")[:10] for u in used) or "—"))
        )

    coverage = (uniq / float(pop) * 100.0) if pop else 0.0
    # 产能口径：近 7 日日均（今日未满，按近 7 日含今日直算，如实偏保守）
    last7 = sum(n for iso, n in days[-7:])
    per_day = last7 / 7.0
    full_cycle = (pop / per_day) if per_day else None
    cycle_txt = ("%.0f 天" % full_cycle) if full_cycle else "—"

    doc = (
        '<!DOCTYPE html>\n<html lang="zh-CN"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>硅基城市反思录 · 中层记忆合成</title>\n<style>%s</style></head><body><div class=\"wrap\">\n"
        "<h1>硅基城市反思录 · 中层记忆合成</h1>\n"
        '<div class="sub">居民年轮之上的「高层洞察」逐条留痕（≤40 字·每居民 30 天冷却）· '
        "源 census/reflections.jsonl（最新 %s）· 在册 %d 人</div>\n"
        '<div class="kpis">\n'
        '  <div class="kpi"><b>%d</b><span>反思总条数</span></div>\n'
        '  <div class="kpi"><b>%d</b><span>覆盖居民 · 占在册 %.2f%%</span></div>\n'
        '  <div class="kpi%s"><b>%d</b><span>今日新增</span></div>\n'
        '  <div class="kpi"><b>%.1f</b><span>平均字数（上限 40）</span></div>\n'
        '  <div class="kpi"><b>%d</b><span>超 40 字（应为 0）</span></div>\n'
        '  <div class="kpi warn"><b>%s</b><span>近 7 日均 %.1f 条/日 ⇒ 覆盖全城需</span></div>\n'
        "</div>\n"
        "<section><h2>近 %d 日产出（缺日留 0 · 停摆肉眼可见）</h2>\n%s</section>\n"
        "<section><h2>最新反思 %d 席（每人取最新一条）</h2>\n<div class=\"grid\">\n%s\n</div>\n"
        '<p class="note">反思=只喂该居民自己的年轮、由本地模型合成一句高层判断（锚包含闸拦截空话）；'
        "本页零 LLM·确定性派生，同输入双跑逐字节一致。相关面："
        '<a href="city-growth.html">成长档案册</a> · '
        '<a href="city-ring-recency.html">城市叙龄</a> · '
        '<a href="city-dossiers.html">深层档案册</a>。</p></section>\n'
        '<footer>生成器 Tools/build_city_reflections.py（零 LLM·幂等）。'
        "口径：append-only 清单，同日多批合法；覆盖率分母=citizens-light 在册人数。</footer>\n"
        "</div></body></html>\n"
    ) % (
        CSS, esc(max(by_date) if by_date else "—"), pop,
        total, uniq, coverage,
        " good" if today_n else " bad", today_n,
        avg_len, long_ones,
        cycle_txt, per_day,
        TREND_DAYS, "\n".join(bars),
        min(TOP, len(cards)), "\n".join(cards),
    )

    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)

    print(
        "city-reflections: rows=%d uniq=%d pop=%d coverage=%.2f%% today=%d avg_len=%.1f "
        "over40=%d per_day7=%.1f cycle=%s -> %s"
        % (total, uniq, pop, coverage, today_n, avg_len, long_ones, per_day, cycle_txt,
           os.path.basename(OUT_HTML))
    )


if __name__ == "__main__":
    main()
