# -*- coding: utf-8 -*-
"""居民图谱单页生成器（确定性·零 LLM）。

读 census/export/citizens-light.jsonl，产出可离线打开的 census/export/resident-gallery.html：
搜索（姓名/编号/职业/街区）+ 阵营筛选 + 居民卡（年轮最新一条）。数据内嵌，单文件零依赖。
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(ROOT, "census", "export", "resident-gallery.html")

FIELDS = ("id", "name", "species", "faction", "district", "block", "profession",
          "creed", "hook", "recent_ring_date", "recent_ring")

SPECIES_LABEL = {
    "carbon": "碳基",
    "silicon": "硅基",
    "sprite": "精灵",
    "artifact-spirit": "器物灵",
    "memory-spirit": "记忆灵",
    "imagery-spirit": "影像灵",
}

FACTION_LABEL = {
    "newcomer": "新住民",
    "lilong": "里弄人",
    "commuter": "通勤者",
    "native": "原乡人",
    "compiled": "编译体",
    "photonsoul": "光子灵",
    "elf": "林中灵",
    "radiocat": "电波猫",
    "finch": "雀灵",
    "nightlamp": "夜灯人",
    "koi": "鲤灵",
    "rainfrog": "雨蛙",
    "chimefly": "铃虫",
    "spirit": "灵体",
    "honored": "荣誉席",
    "copperfox": "铜狐",
}

TEMPLATE = u"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城居民图谱 · BigLife</title>
<style>
:root{{--bg:#0e1116;--card:#171c24;--line:#242c38;--fg:#e6ebf2;--dim:#8b97a8;--acc:#5fb8a6}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:20px 24px 12px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}}
h1{{margin:0 0 4px;font-size:18px;font-weight:600;letter-spacing:.5px}}
.meta{{color:var(--dim);font-size:12px}}
.bar{{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}}
input[type=search]{{flex:1;min-width:240px;padding:8px 12px;border-radius:6px;border:1px solid var(--line);background:#11161d;color:var(--fg);outline:none}}
input[type=search]:focus{{border-color:var(--acc)}}
.chip{{padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:#11161d;color:var(--dim);cursor:pointer;font-size:12px}}
.chip.on{{border-color:var(--acc);color:var(--acc)}}
main{{padding:16px 24px 64px;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}}
.top{{display:flex;justify-content:space-between;gap:8px;align-items:baseline}}
.name{{font-size:15px;font-weight:600}}
.cid{{color:var(--dim);font-size:11px;font-variant-numeric:tabular-nums}}
.row{{color:var(--dim);font-size:12px;margin-top:2px}}
.ring{{margin-top:8px;padding-top:8px;border-top:1px dashed var(--line);font-size:12.5px;color:#c9d3e0}}
.ringdate{{color:var(--acc);font-size:11px;margin-right:6px}}
.empty{{color:var(--dim);padding:40px;text-align:center;grid-column:1/-1}}
.more{{grid-column:1/-1;text-align:center;padding:20px}}
.more button{{padding:9px 22px;border-radius:6px;border:1px solid var(--line);background:#11161d;color:var(--fg);cursor:pointer}}
</style>
</head>
<body>
<header>
  <h1>硅基城居民图谱</h1>
  <div class="meta">共 <b id="total">{total}</b> 位居民 · 有年轮 {evolved} 位 · 生成 {stamp}</div>
  <div class="bar">
    <input id="q" type="search" placeholder="搜索 姓名 / 编号 / 职业 / 街区 / 年轮关键词…">
    <span class="chip on" data-f="*">全部</span>
    {chips}
  </div>
</header>
<main id="grid"></main>
<script>
const DATA = {data};
const PAGE = 120;
const grid = document.getElementById('grid');
const q = document.getElementById('q');
let faction = '*', shown = 0, hits = [];

function match(c){{
  const kw = q.value.trim().toLowerCase();
  if (faction !== '*' && (c.s || '') !== faction) return false;
  if (!kw) return true;
  return (c.n + ' ' + c.i + ' ' + (c.p||'') + ' ' + (c.d||'') + ' ' + (c.f||'') + ' ' + (c.r||'')).toLowerCase().includes(kw);
}}
function card(c){{
  const el = document.createElement('article');
  el.className = 'card';
  const parts = [];
  parts.push('<div class="top"><span class="name"></span><span class="cid"></span></div>');
  el.innerHTML = parts.join('');
  el.querySelector('.name').textContent = c.n;
  el.querySelector('.cid').textContent = c.i;
  const meta = [c.p, c.d || c.b, c.f].filter(Boolean).join(' · ');
  if (meta) {{ const r = document.createElement('div'); r.className='row'; r.textContent = meta; el.appendChild(r); }}
  if (c.r) {{
    const r = document.createElement('div'); r.className = 'ring';
    const d = document.createElement('span'); d.className='ringdate'; d.textContent = c.rd || '';
    r.appendChild(d);
    r.appendChild(document.createTextNode(c.r));
    el.appendChild(r);
  }}
  return el;
}}
function render(reset){{
  if (reset) {{ grid.textContent=''; shown = 0; }}
  const slice = hits.slice(shown, shown + PAGE);
  if (!slice.length && shown === 0) {{
    const e = document.createElement('div'); e.className='empty'; e.textContent='没有匹配的居民';
    grid.appendChild(e);
  }}
  slice.forEach(c => grid.appendChild(card(c)));
  shown += slice.length;
  const old = grid.querySelector('.more'); if (old) old.remove();
  if (shown < hits.length) {{
    const wrap = document.createElement('div'); wrap.className='more';
    const btn = document.createElement('button');
    btn.textContent = `继续加载（${{shown}} / ${{hits.length}}）`;
    btn.onclick = () => render(false);
    wrap.appendChild(btn); grid.appendChild(wrap);
  }}
}}
function apply(){{ hits = DATA.filter(match); render(true); }}
q.addEventListener('input', apply);
document.querySelectorAll('.chip').forEach(ch => ch.onclick = () => {{
  document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
  ch.classList.add('on'); faction = ch.dataset.f; apply();
}});
apply();
</script>
</body>
</html>
"""


def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ring = (d.get("recent_ring") or "").strip().replace("\n", " ")
            if len(ring) > 180:
                ring = ring[:180] + "…"
            rows.append({
                "i": d.get("id", ""),
                "n": d.get("name", ""),
                "p": d.get("profession") or "",
                "d": d.get("district") or "",
                "b": d.get("block") or "",
                "s": d.get("species") or "",
                "f": FACTION_LABEL.get(d.get("faction") or "", d.get("faction") or ""),
                "rd": d.get("recent_ring_date") or "",
                "r": ring,
            })
    return rows


def build(rows):
    counts = {}
    for r in rows:
        counts[r["s"]] = counts.get(r["s"], 0) + 1
    order = ["carbon", "silicon", "sprite"] + sorted(k for k in counts if k not in ("carbon", "silicon", "sprite"))
    chips = []
    for k in order:
        if k not in counts:
            continue
        label = SPECIES_LABEL.get(k, k or "未标")
        chips.append(u'<span class="chip" data-f="%s">%s %d</span>' % (k, label, counts[k]))
    data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    evolved = sum(1 for r in rows if r["r"])
    stamp = "—"
    try:
        import datetime
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    html = TEMPLATE.format(total=len(rows), evolved=evolved, stamp=stamp,
                           chips="\n    ".join(chips), data=data)
    # TEMPLATE 里 CSS/JS 的 {{ }} 已转义，这里只还原未参与 format 的占位差异
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()
    if not os.path.exists(args.src):
        print("FAIL: source missing %s" % args.src)
        return 2
    rows = load(args.src)
    html = build(rows)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    size = os.path.getsize(args.out)
    print("OK residents=%d size=%.2fMB out=%s" % (len(rows), size / 1048576.0, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())