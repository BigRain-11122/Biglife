# -*- coding: utf-8 -*-
"""基因总账：把基因库全类别的「登记 vs 在册承载」算成一张只读单页 + 内容缺口选题单。

确定性零 LLM：只读 genes/lives.json（正本）与 census/registry/<城区>/*.md（户卡正文，只读不改），
输出 census/export/gene-ledger.html。

口径：
- 登记 = genes/lives.json 里该类别的条目数（登记在先，使用在后）
- 在册 = 至少一张户卡正文出现该条目整串的条目数（一卡计一次）
- 覆盖率 = 在册 / 登记
- 未落册 = 登记了但没有任何户卡写到 —— 下一批 intake 的内容选题池
- origins 为模板族（含 {year}/{region} 占位），不计覆盖，只报条目数
"""
from __future__ import annotations

import html
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENES = ROOT / "genes" / "lives.json"
META = ROOT / "genes" / "meta.json"
REGISTRY = ROOT / "census" / "registry"
OUT = ROOT / "census" / "export" / "gene-ledger.html"

LINE_CLEAN = re.compile(r"[#*_>`]|^-+\s*", re.M)

# (键, 显示名, 说明)
CATS = [
    ("hook_objects", "钩子物件", "随身之物 / 场景焦点物"),
    ("turning_points", "转折点", "经历段里的那道弯"),
    ("presents", "心愿", "现状段里的下一步"),
    ("habits", "习惯", "行为段里的日常循环"),
    ("hook_scopes", "徽记语境", "钩子的收尾用法"),
    ("sprite_habits", "精灵习惯", "硅基物种的日常"),
]
# 生成期模板族：含 {obj}/{year}/{region} 占位，用于生成时填空，不落正文整串，故不计覆盖
TEMPLATE_CATS = [
    ("origins", "出身模板族", "含占位 · 不计覆盖"),
    ("origin_regions", "地域池", "填空取值 · 不计覆盖"),
    ("origin_years", "年代池", "填空取值 · 不计覆盖"),
    ("hook_actions", "钩子动作模板", "生成期填空 · 不落正文"),
    ("sprite_hook_actions", "精灵动作模板", "生成期填空 · 不落正文"),
]


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


def load_cards():
    texts: list[tuple[str, str]] = []  # (城区码, 正文)
    cards = 0
    for code in sorted(os.listdir(REGISTRY)):
        dpath = REGISTRY / code
        if not dpath.is_dir():
            continue
        for fn in sorted(os.listdir(dpath)):
            if not fn.endswith(".md"):
                continue
            cards += 1
            texts.append((code, (dpath / fn).read_text(encoding="utf-8", errors="ignore")))
    return texts, cards


def extract_line(text: str, gene: str) -> str:
    for raw in text.splitlines():
        if gene not in raw:
            continue
        line = LINE_CLEAN.sub("", raw).strip()
        if not line:
            continue
        if len(line) > 74:
            idx = line.find(gene)
            start = max(0, idx - 24)
            line = ("…" if start else "") + line[start:start + 72] + "…"
        return line
    return ""


def main() -> int:
    lives = load_json(GENES)
    labels = district_labels()
    texts, cards = load_cards()

    report = []
    for key, name, note in CATS:
        items = list(dict.fromkeys(lives.get(key, [])))
        counts: Counter[str] = Counter()
        by_district: dict[str, Counter[str]] = defaultdict(Counter)
        sample: dict[str, str] = {}
        for code, text in texts:
            for gene in items:
                if gene and gene in text:
                    counts[gene] += 1
                    by_district[gene][code] += 1
                    if gene not in sample:
                        sample[gene] = extract_line(text, gene)
        used = [g for g in items if counts[g] > 0]
        used.sort(key=lambda g: (-counts[g], g))
        report.append(
            {
                "key": key,
                "name": name,
                "note": note,
                "items": items,
                "counts": counts,
                "by_district": by_district,
                "sample": sample,
                "used": used,
                "unused": [g for g in items if counts[g] == 0],
            }
        )

    total_reg = sum(len(r["items"]) for r in report)
    total_used = sum(len(r["used"]) for r in report)
    total_mentions = sum(sum(r["counts"].values()) for r in report)
    total_unused = total_reg - total_used

    # 一、覆盖率总览
    def cov_bar(used: int, reg: int) -> str:
        pct = (used * 100.0 / reg) if reg else 0.0
        return (
            '<div class="cov"><div class="fill" style="width:{:.1f}%"></div></div>'
            '<span class="pct">{:.0f}%</span>'.format(pct, pct)
        )

    overview = "".join(
        f'<div class="row cov-row"><span class="nm">{esc(r["name"])}<em>{esc(r["note"])}</em></span>'
        f'<span class="ct">{len(r["used"])}/{len(r["items"])}</span>'
        f'<span class="ds">{cov_bar(len(r["used"]), len(r["items"]))}</span></div>'
        for r in report
    )

    templ = "".join(
        f'<div class="row"><span class="nm">{esc(name)}</span>'
        f'<span class="ct">{len(lives.get(key, []))}</span>'
        f'<span class="ds">{esc(note)}</span></div>'
        for key, name, note in TEMPLATE_CATS
    )

    # 二、缺口选题单（按类别，登记未落册）
    gap_sections = []
    for r in report:
        if not r["unused"]:
            gap_sections.append(
                f'<h3 class="axis">{esc(r["name"])}<span class="meta">全数落册 · 无缺口</span></h3>'
            )
            continue
        chips = "".join(f'<span class="chip">{esc(g)}</span>' for g in r["unused"])
        gap_sections.append(
            f'<h3 class="axis">{esc(r["name"])}<span class="meta">缺 {len(r["unused"])} 条 / 共登记 {len(r["items"])}</span></h3>'
            f'<div class="qabox">{chips}</div>'
        )

    # 三、使用热榜（每类 top 15）
    hot_sections = []
    for r in report:
        if not r["used"]:
            hot_sections.append(f'<h3 class="axis">{esc(r["name"])}<span class="meta">无落册</span></h3>')
            continue
        box = []
        for gene in r["used"][:15]:
            n = r["counts"][gene]
            d = r["by_district"][gene].most_common(1)[0][0] if r["by_district"][gene] else ""
            say = r["sample"].get(gene, "")
            say_html = '<p class="say">%s</p>' % esc(say) if say else ""
            box.append(
                f'<div class="hot"><div class="hrow"><span class="hn">{esc(gene)}</span>'
                f'<span class="hc">{n} 人</span></div>'
                f'<div class="hd">{esc(labels.get(d, d or "—"))}</div>'
                f'{say_html}</div>'
            )
        hot_sections.append(
            f'<h3 class="axis">{esc(r["name"])}<span class="meta">前 {min(15, len(r["used"]))} 条 / 在用 {len(r["used"])}</span></h3>'
            f'<div class="grid">{"".join(box)}</div>'
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>基因总账 · 硅基生命</title>
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
.tbl{{border:1px solid var(--line);border-radius:5px;background:#14181e;margin-bottom:8px}}
.row{{display:grid;grid-template-columns:1fr 90px 150px;gap:10px;padding:5px 12px;
border-bottom:1px dotted #1e242c;font-size:13px;align-items:center}}
.row:last-child{{border-bottom:0}}
.nm{{color:#dedbd4}}
.nm em{{font-style:normal;display:block;font-size:11.5px;color:#6a7078}}
.ct{{text-align:right;font:12px/1.6 ui-monospace,monospace;color:#c8a06a}}
.ds{{font-size:12px;color:var(--dim);text-align:right}}
.cov-row .ds{{text-align:left;display:flex;align-items:center;gap:8px}}
.cov{{flex:1;height:5px;border-radius:3px;background:#1b2027;overflow:hidden}}
.cov .fill{{display:block;height:100%;background:#7c6a4e}}
.pct{{font:11px/1 ui-monospace,monospace;color:#8b8f96;min-width:32px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.hot{{background:#14181e;border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:5px;padding:9px 12px}}
.hrow{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}}
.hn{{font-size:13px;color:#dedbd4;line-height:1.55}}
.hc{{font:11px/1 ui-monospace,monospace;color:#c8a06a;white-space:nowrap}}
.hd{{font-size:11.5px;color:var(--dim);margin-top:3px}}
.say{{margin:5px 0 0;font-size:12.5px;color:#b3b0a8;line-height:1.6}}
.qabox{{border:1px solid var(--line);border-radius:5px;padding:6px 12px;background:#14181e}}
.chip{{display:inline-block;padding:2px 8px;margin:3px 4px 3px 0;border:1px solid var(--line);
border-radius:10px;font-size:12px;color:#9aa0a6;background:#14181e}}
.hide{{display:none}}
footer{{padding:18px 26px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
@media(max-width:760px){{.wrap{{grid-template-columns:1fr}}
nav{{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:4px}}nav a{{padding:2px 6px}}
.row{{grid-template-columns:1fr 70px}}.ds{{display:none}}.cov-row .ds{{display:flex}}}}
</style></head><body>
<header><h1>基因总账</h1>
<div class="sub">全类别「登记 vs 在册承载」· 户卡 {cards} 张扫描 · 只读汇总，零 LLM · 生成 {now}</div></header>
<div class="kpi">
<div><b>{total_reg}</b>可计数基因</div>
<div><b>{total_used}</b>在册承载</div>
<div><b>{total_unused}</b>登记未落册</div>
<div><b>{total_mentions}</b>卡片提及</div>
<div><b>{total_used * 100 // max(total_reg, 1)}%</b>总覆盖率</div>
</div>
<div class="search"><input id="q" placeholder="按基因检索：电波猫 / 台风 / 记账本 …" autocomplete="off"></div>
<div class="wrap">
<nav>
<a href="#cov">一、覆盖率</a>
<a href="#gap">二、选题单</a>
<a href="#hot">三、使用热榜</a>
</nav>
<main>
<section class="sec" id="cov"><h2>一、覆盖率总览<span class="meta">在册 / 登记 · 一卡计一次</span></h2>
<div class="tbl">{overview}{templ}</div></section>

<section class="sec" id="gap"><h2>二、内容缺口选题单<span class="meta">{total_unused} 条登记未落册 · 按类别，可直接用作下一批 intake 的选题池</span></h2>
{"".join(gap_sections)}</section>

<section class="sec" id="hot"><h2>三、使用热榜<span class="meta">每类前 15 条 · 承载人数 / 主聚城区 / 卡内原句</span></h2>
{"".join(hot_sections)}</section>
</main></div>
<footer>本页由 Tools/build_gene_ledger.py 确定性生成，零 LLM；数据正本 genes/lives.json 与 census/registry/&lt;城区&gt;/*.md（只读）。
条目按整串匹配计数，一卡计一次。含 {{obj}}/{{year}}/{{region}} 占位的模板族（出身/地域/年代/动作模板）
在生成期填空、不落正文，只报条目数不计覆盖。
「登记未落册」= 基因已登记但没有任何户卡写到，是内容生产的选题池而非缺陷。</footer>
<script>
(function(){{
 var q=document.getElementById('q');
 var nodes=[].slice.call(document.querySelectorAll('.hot,.chip'));
 function run(){{
  var k=q.value.trim().toLowerCase(),hit=0;
  nodes.forEach(function(c){{
   var ok=!k||c.textContent.toLowerCase().indexOf(k)>=0;
   c.classList.toggle('hide',!ok); if(ok)hit++;
  }});
  document.title='基因总账 · '+hit+' 条';
 }}
 q.addEventListener('input',run);
}})();
</script>
</body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"gene-ledger: {OUT.relative_to(ROOT)}  {len(page.encode('utf-8')) / 1024:.1f} KB")
    print(f"cards={cards} registered={total_reg} used={total_used} unused={total_unused} mentions={total_mentions}")
    for r in report:
        print(f"  {r['key']}: {len(r['used'])}/{len(r['items'])}  unused={len(r['unused'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())