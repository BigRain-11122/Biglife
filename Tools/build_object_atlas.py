# -*- coding: utf-8 -*-
"""城市风物志：以「钩子物件」为主角，把基因库与户籍卡的物件承载面汇总成一张只读单页。

确定性零 LLM：只读 genes/lives.json（物件/钩子动作/转折点/心愿/习惯正本）与
census/registry/<城区>/*.md（户卡正文，只读不改），输出 census/export/city-objects.html。

口径：
- 物件基因 = genes/lives.json -> hook_objects（登记在先，使用在后）
- 在册承载 = 至少一张户卡正文里出现该物件名的物件数
- 提及次数 = 全部户卡里该物件名出现的卡数（一卡计一次）
- 未落册物件 = 基因已登记、但没有任何户卡提到——内容缺口，供后续批次补写
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENES = ROOT / "genes" / "lives.json"
META = ROOT / "genes" / "meta.json"
REGISTRY = ROOT / "census" / "registry"
OUT = ROOT / "census" / "export" / "city-objects.html"

LINE_CLEAN = re.compile(r"[#*_>`]|^-+\s*", re.M)


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load_json(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def district_labels() -> dict[str, str]:
    try:
        meta = load_json(META)
        return {d["id"]: d["name"] for d in meta.get("districts", [])}
    except Exception:
        return {}


def scan_registry(objects: list[str]):
    """扫户卡正文：每物件 -> 提及卡数 / 城区分布 / 一条例句。"""
    counts: Counter[str] = Counter()
    by_district: dict[str, Counter[str]] = defaultdict(Counter)
    sample: dict[str, str] = {}
    cards = 0
    for code in sorted(os.listdir(REGISTRY)):
        dpath = REGISTRY / code
        if not dpath.is_dir():
            continue
        for fn in sorted(os.listdir(dpath)):
            if not fn.endswith(".md"):
                continue
            cards += 1
            text = (dpath / fn).read_text(encoding="utf-8", errors="ignore")
            for obj in objects:
                if obj and obj in text:
                    counts[obj] += 1
                    by_district[obj][code] += 1
                    if obj not in sample:
                        sample[obj] = extract_line(text, obj)
    return counts, by_district, sample, cards


def extract_line(text: str, obj: str) -> str:
    for raw in text.splitlines():
        if obj not in raw:
            continue
        line = LINE_CLEAN.sub("", raw).strip()
        if not line:
            continue
        if len(line) > 78:
            idx = line.find(obj)
            start = max(0, idx - 30)
            line = ("…" if start else "") + line[start:start + 76] + "…"
        return line
    return ""


def tier(n: int) -> tuple[str, str]:
    if n >= 100:
        return ("top", "百人级")
    if n >= 30:
        return ("mid", "三十人级")
    if n >= 10:
        return ("low", "十人级")
    return ("rare", "孤本")


def bar(dcounts: Counter, labels: dict[str, str], total: int) -> str:
    if not total:
        return ""
    parts = []
    for code, n in dcounts.most_common():
        pct = n * 100.0 / total
        parts.append(f'<span class="d" style="width:{pct:.1f}%" title="{esc(labels.get(code, code))} {n} 人"></span>')
    return '<div class="bar">' + "".join(parts) + "</div>"


def main() -> int:
    lives = load_json(GENES)
    objects = list(dict.fromkeys(lives.get("hook_objects", [])))
    hook_actions = lives.get("hook_actions", [])
    hook_scopes = lives.get("hook_scopes", [])
    turning = lives.get("turning_points", [])
    presents = lives.get("presents", [])
    habits = lives.get("habits", [])
    labels = district_labels()

    counts, by_district, sample, cards = scan_registry(objects)
    carried = [o for o in objects if counts[o] > 0]
    carried.sort(key=lambda o: (-counts[o], o))
    missing = [o for o in objects if counts[o] == 0]
    mentions = sum(counts.values())

    # 一、主物卡（提及最多的前 12 件）
    top_cards = []
    for obj in carried[:12]:
        n = counts[obj]
        top_d = by_district[obj].most_common(1)[0][0] if by_district[obj] else ""
        top_cards.append(
            f'<div class="card obj"><h4>{esc(obj)}<em>{n} 人</em></h4>'
            f'<div class="who">主聚 {esc(labels.get(top_d, top_d or "—"))}</div>'
            f'{bar(by_district[obj], labels, n)}'
            f'<p class="say">{esc(sample.get(obj, ""))}</p></div>'
        )

    # 二、全册物件表（按提及量分档）
    tiers: dict[str, list[str]] = defaultdict(list)
    for obj in carried:
        tiers[tier(counts[obj])[0]].append(obj)
    rows = []
    for key, tname in (("top", "百人级"), ("mid", "三十人级"), ("low", "十人级"), ("rare", "孤本")):
        group = tiers.get(key, [])
        if not group:
            continue
        rows.append(f'<h3 class="axis">{tname}<span class="meta">{len(group)} 件</span></h3>')
        items = []
        for obj in group:
            n = counts[obj]
            d = by_district[obj].most_common(1)[0][0] if by_district[obj] else ""
            items.append(
                f'<div class="row"><span class="nm">{esc(obj)}</span>'
                f'<span class="ct">{n}</span><span class="ds">{esc(labels.get(d, d or "—"))}</span></div>'
            )
        rows.append('<div class="tbl">' + "".join(items) + "</div>")

    # 三、钩子动作模板（{obj} 占位）
    action_rows = "".join(f'<div class="qa"><span class="a">{esc(a)}</span></div>' for a in hook_actions)
    scope_rows = "".join(f'<div class="qa"><span class="a">{esc(s)}</span></div>' for s in hook_scopes)

    # 四、缺口：登记未使用的物件
    gap_rows = "".join(f'<span class="chip">{esc(o)}</span>' for o in missing)

    # 五、物件的另一面：转折点 / 心愿 / 习惯（各抽 8 条，作为物件的叙事土壤）
    def quotes(items, limit=8):
        return "".join(f'<q>{esc(x)}</q>' for x in items[:limit])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市风物志 · 硅基生命</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header{{padding:28px 20px 12px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
.kpi{{display:flex;gap:22px;flex-wrap:wrap;padding:14px 20px;border-bottom:1px solid var(--line)}}
.kpi div{{font-size:13px;color:var(--dim)}}
.kpi b{{display:block;font-size:20px;color:var(--fg);font-weight:600}}
.search{{padding:12px 20px;border-bottom:1px solid var(--line)}}
input{{width:100%;max-width:420px;padding:8px 10px;background:#151a20;border:1px solid var(--line);
color:var(--fg);border-radius:4px;font:14px/1.4 inherit}}
.wrap{{display:grid;grid-template-columns:190px 1fr;align-items:start}}
nav{{position:sticky;top:0;max-height:100vh;overflow:auto;padding:14px 10px;border-right:1px solid var(--line)}}
nav a{{display:block;padding:5px 8px;color:var(--dim);text-decoration:none;
font:12px/1.5 ui-monospace,monospace;border-radius:3px}}
nav a:hover{{background:#161b22;color:var(--fg)}}
main{{padding:10px 26px 60px;max-width:1080px}}
.sec{{padding:20px 0;border-bottom:1px dashed var(--line)}}
.sec h2{{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 14px;font-size:17px}}
.meta{{font-size:12px;color:var(--dim);font-weight:400}}
h3.axis{{margin:18px 0 8px;font-size:15px;color:var(--acc);font-weight:600;
display:flex;justify-content:space-between;align-items:baseline;border-left:3px solid var(--acc);padding-left:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.card{{background:#14181e;border:1px solid var(--line);border-radius:5px;padding:10px 12px}}
.card h4{{margin:0 0 6px;font-size:13.5px;display:flex;justify-content:space-between;
align-items:baseline;color:#cfcabf;font-weight:600}}
.card h4 em{{font-style:normal;font:11px/1 ui-monospace,monospace;color:#6a7078}}
.card.obj{{border-left:3px solid var(--acc)}}
.who{{font-size:11.5px;color:var(--dim);margin-bottom:4px}}
.bar{{display:flex;height:4px;border-radius:2px;overflow:hidden;background:#1b2027;margin:2px 0 6px}}
.bar .d{{display:block;height:100%;background:#7c6a4e}}
.say{{margin:4px 0 0;font-size:12.5px;color:#b3b0a8;line-height:1.6}}
.tbl{{border:1px solid var(--line);border-radius:5px;background:#14181e}}
.row{{display:grid;grid-template-columns:1fr 56px 190px;gap:10px;padding:4px 12px;
border-bottom:1px dotted #1e242c;font-size:13px}}
.row:last-child{{border-bottom:0}}
.nm{{color:#dedbd4}}
.ct{{text-align:right;font:12px/1.6 ui-monospace,monospace;color:#c8a06a}}
.ds{{font-size:12px;color:var(--dim);text-align:right}}
.qabox{{border:1px solid var(--line);border-radius:5px;padding:6px 12px;background:#14181e}}
.qa{{padding:4px 0;border-bottom:1px dotted #1e242c;font-size:13.5px}}
.qa:last-child{{border-bottom:0}}
.a{{color:#b3b0a8}}
.chip{{display:inline-block;padding:2px 8px;margin:3px 4px 3px 0;border:1px solid var(--line);
border-radius:10px;font-size:12px;color:#9aa0a6;background:#14181e}}
q{{display:block;font-size:13px;color:#dedbd4;padding:3px 0;quotes:none;line-height:1.65}}
q::before,q::after{{content:""}}
.hide{{display:none}}
footer{{padding:18px 26px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
@media(max-width:760px){{.wrap{{grid-template-columns:1fr}}
nav{{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:4px}}nav a{{padding:2px 6px}}
.row{{grid-template-columns:1fr 46px}}.ds{{display:none}}}}
</style></head><body>
<header><h1>城市风物志</h1>
<div class="sub">以物件为主角的城市切片 · 基因库 {len(objects)} 件登记 / {len(carried)} 件在册承载 ·
只读汇总，零 LLM · 生成 {now}</div></header>
<div class="kpi">
<div><b>{len(objects)}</b>物件基因</div>
<div><b>{len(carried)}</b>在册承载</div>
<div><b>{mentions}</b>卡片提及</div>
<div><b>{cards}</b>户卡扫描</div>
<div><b>{len(missing)}</b>登记未落册</div>
</div>
<div class="search"><input id="q" placeholder="按物件名检索：电波猫 / 手写信 / 邮筒 …" autocomplete="off"></div>
<div class="wrap">
<nav>
<a href="#top">一、主物</a>
<a href="#all">二、全册</a>
<a href="#acts">三、钩子动作</a>
<a href="#gap">四、缺口</a>
<a href="#soil">五、叙事土壤</a>
</nav>
<main>
<section class="sec" id="top"><h2>一、主物<span class="meta">提及最多的 {len(top_cards)} 件 · 按承载居民数排序</span></h2>
<div class="grid">{"".join(top_cards)}</div></section>

<section class="sec" id="all"><h2>二、全册物件<span class="meta">{len(carried)} 件在册承载 · 每行=物件 / 承载人数 / 主聚城区</span></h2>
{"".join(rows)}</section>

<section class="sec" id="acts"><h2>三、钩子动作与徽记语境<span class="meta">{len(hook_actions)} 条动作模板（{{obj}} 占位）+ {len(hook_scopes)} 条徽记</span></h2>
<h3 class="axis">动作模板<span class="meta">把物件写成可复用的行为</span></h3>
<div class="qabox">{action_rows}</div>
<h3 class="axis">徽记语境<span class="meta">钩子的收尾用法</span></h3>
<div class="qabox">{scope_rows}</div></section>

<section class="sec" id="gap"><h2>四、缺口：登记未落册<span class="meta">{len(missing)} 件 · 基因已登记但没有任何户卡写到——下一批内容的生产清单</span></h2>
<div class="qabox">{gap_rows}</div></section>

<section class="sec" id="soil"><h2>五、叙事土壤<span class="meta">物件的来处与去处：转折点 {len(turning)} / 心愿 {len(presents)} / 习惯 {len(habits)}（以下各抽 8 条）</span></h2>
<h3 class="axis">转折点<span class="meta">物件从哪来</span></h3>
<div class="qabox">{quotes(turning)}</div>
<h3 class="axis">心愿<span class="meta">物件要往哪去</span></h3>
<div class="qabox">{quotes(presents)}</div>
<h3 class="axis">习惯<span class="meta">物件怎么被用</span></h3>
<div class="qabox">{quotes(habits)}</div></section>
</main></div>
<footer>本页由 Tools/build_object_atlas.py 确定性生成，零 LLM；数据正本 genes/lives.json（物件/动作/转折点/心愿/习惯）
与 census/registry/&lt;城区&gt;/*.md（户卡正文，只读）。物件名按整串匹配计数，一卡计一次；未落册清单可直接用作下批内容选题。
</footer>
<script>
(function(){{
 var q=document.getElementById('q');
 var nodes=[].slice.call(document.querySelectorAll('.row,.card,.chip'));
 function run(){{
  var k=q.value.trim().toLowerCase(),hit=0;
  nodes.forEach(function(c){{
   var ok=!k||c.textContent.toLowerCase().indexOf(k)>=0;
   c.classList.toggle('hide',!ok); if(ok)hit++;
  }});
  document.title='城市风物志 · '+hit+' 件';
 }}
 q.addEventListener('input',run);
}})();
</script>
</body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"city-objects: {OUT.relative_to(ROOT)}  {len(page.encode('utf-8')) / 1024:.1f} KB")
    print(f"objects={len(objects)} carried={len(carried)} mentions={mentions} cards={cards} "
          f"missing={len(missing)} actions={len(hook_actions)}")
    if carried:
        print("top:", ", ".join(f"{o}={counts[o]}" for o in carried[:8]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())