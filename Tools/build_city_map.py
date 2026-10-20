# -*- coding: utf-8 -*-
"""城市空间地图生成器（确定性·零 LLM·幂等）。

读 census/export/citizen-anchors.jsonl + citizen-behavior.jsonl，产出
census/export/city-map.html：居民住/工/社交三锚点地理分布 + 此刻行为层。

用法: python -X utf8 Tools/build_city_map.py
"""
import collections
import datetime
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
SRC_ANCHORS = os.path.join(EXP, "citizen-anchors.jsonl")
SRC_BEHAVIOR = os.path.join(EXP, "citizen-behavior.jsonl")
SRC_LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-map.html")

DISTRICT_CN = {
    "GM": "中央市集 GM",
    "QT": "低语巷 QT",
    "MD": "机房区 MD",
    "NS": "北槐街区 NS",
    "OR": "旧站台 OR",
    "RV": "河岸 RV",
    "": "(荣誉席)",
}
STATE_CN = {
    "work": "在岗",
    "school": "上学",
    "home": "在家",
    "rest_nap": "小憩",
    "indoors": "室内",
    "shelter": "檐下避雨",
    "social": "社交",
    "night": "夜行",
    "sleep": "睡眠",
}
# 行为状态 → 此刻坐标取哪个锚点
STATE_ANCHOR = {
    "work": "work",
    "school": "work",
    "home": "home",
    "rest_nap": "home",
    "sleep": "home",
    "indoors": "home",
    "shelter": "work",
    "social": "social",
    "night": "social",
}


def load(path):
    with io.open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    anchors = load(SRC_ANCHORS)
    behavior = {r["id"]: r for r in load(SRC_BEHAVIOR)}
    light = {r["id"]: r for r in load(SRC_LIGHT)}

    dist_codes = sorted({(a.get("district") or "") for a in anchors})
    dist_idx = {c: i for i, c in enumerate(dist_codes)}
    state_codes = sorted({(b.get("state") or "") for b in behavior.values()})
    state_idx = {c: i for i, c in enumerate(state_codes)}

    rows = []
    dist_count = collections.Counter()
    state_count = collections.Counter()
    ctx = ""
    for a in sorted(anchors, key=lambda r: r["id"]):
        h, w, s = a.get("home"), a.get("work"), a.get("social")
        if not h or not w:
            continue
        cid = a["id"]
        b = behavior.get(cid) or {}
        st = b.get("state") or ""
        ctx = b.get("ctx") or ctx
        lt = light.get(cid) or {}
        d = a.get("district") or ""
        rows.append([
            cid,
            lt.get("name") or a.get("profession") or cid,
            dist_idx[d],
            state_idx.get(st, -1),
            round(h["x"], 2), round(h["z"], 2),
            round(w["x"], 2), round(w["z"], 2),
            round(s["x"], 2) if s else None, round(s["z"], 2) if s else None,
            a.get("profession") or "",
        ])
        dist_count[d] += 1
        state_count[st] += 1

    xs = [r[4] for r in rows] + [r[6] for r in rows]
    zs = [r[5] for r in rows] + [r[7] for r in rows]
    bounds = [min(xs), min(zs), max(xs), max(zs)]

    kept = [c for c in dist_codes if dist_count[c]]
    remap = {c: i for i, c in enumerate(kept)}
    for r in rows:
        r[2] = remap[dist_codes[r[2]]]

    data = {
        "districts": [{"code": c, "cn": DISTRICT_CN.get(c, c), "n": dist_count[c]} for c in kept],
        "states": [{"code": c, "cn": STATE_CN.get(c, c), "n": state_count[c]} for c in state_codes],
        "anchorOf": STATE_ANCHOR,
        "bounds": bounds,
        "rows": rows,
    }

    src_mtime = max(os.path.getmtime(SRC_ANCHORS), os.path.getmtime(SRC_BEHAVIOR))
    gen_at = datetime.datetime.fromtimestamp(src_mtime).strftime("%Y-%m-%d %H:%M:%S")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城市空间地图 · %(total)d 位居民</title>
<style>
:root{--bg:#0b0f14;--fg:#e6edf3;--dim:#7d8590;--line:#1c2430;--acc:#4f9cf9;
--home:#4f9cf9;--work:#f0a35e;--social:#5fd39b;--now:#e05c7a}
*{box-sizing:border-box}
html,body{margin:0;height:100%%;background:var(--bg);color:var(--fg);
font:13px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.layout{display:flex;height:100%%;min-height:640px}
#stage{flex:1;min-width:0;position:relative;background:radial-gradient(circle at 50%% 45%%,#111a24,#080b10 70%%)}
#cv{display:block;width:100%%;height:100%%;cursor:crosshair}
.head{position:absolute;left:20px;top:16px;pointer-events:none}
.head h1{font-size:17px;margin:0 0 2px;letter-spacing:.4px}
.head p{margin:0;color:var(--dim);font-size:11px}
.hint{position:absolute;left:20px;bottom:14px;color:#4d5761;font-size:11px}
#tip{position:absolute;pointer-events:none;background:#161b22ee;border:1px solid #2a3441;
border-radius:8px;padding:7px 10px;font-size:12px;display:none;max-width:280px;line-height:1.5}
#tip b{display:block;color:#fff;font-weight:600}
#tip span{color:var(--dim)}
#tip em{color:var(--now);font-style:normal}
aside{width:300px;flex:0 0 300px;border-left:1px solid var(--line);padding:18px 16px;
overflow:auto;background:#0d1319}
h2{font-size:11px;letter-spacing:.9px;text-transform:uppercase;color:var(--dim);
margin:20px 0 8px;font-weight:600}
h2:first-of-type{margin-top:0}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;
border:1px solid var(--line);background:#121a22;color:var(--dim);cursor:pointer;font-size:12px;
user-select:none}
.chip.on{color:var(--fg);border-color:#35455a;background:#17212c}
.chip i{width:8px;height:8px;border-radius:50%%;display:block}
.chip em{color:#5c6773;font-style:normal;font-variant-numeric:tabular-nums}
.legend{display:grid;gap:6px;font-size:12px;color:var(--dim)}
.legend div{display:flex;align-items:center;gap:8px}
.legend i{width:9px;height:9px;border-radius:50%%;display:block}
.legend b{color:var(--fg);font-weight:500;font-variant-numeric:tabular-nums;margin-left:auto}
footer{margin-top:22px;padding-top:12px;border-top:1px solid var(--line);color:#4d5761;font-size:11px}
</style></head><body>
<div class="layout">
<div id="stage">
  <canvas id="cv"></canvas>
  <div class="head"><h1>硅基城市空间地图</h1>
  <p>%(total)d 位居民 · 三锚点地理分布 + 此刻行为层 · 快照 %(gen)s</p></div>
  <div class="hint">滚轮缩放 · 拖拽平移 · 悬停看人 · 双击复位</div>
  <div id="tip"></div>
</div>
<aside>
  <h2>图层</h2>
  <div class="chips" id="layers"></div>
  <h2>此刻在做什么</h2>
  <div class="legend" id="states"></div>
  <h2>街区人口</h2>
  <div class="legend" id="dists"></div>
  <footer>确定性生成 · 生成器=Tools/build_city_map.py · 无 LLM 参与 · 幂等重跑覆盖本文件<br>
  数据源=census/export/citizen-anchors.jsonl + citizen-behavior.jsonl（快照上下文 %(ctx)s）</footer>
</aside>
</div>
<script>
const D = %(payload)s;
const LAYERS = [
  {k:'home', cn:'住址', color:'#4f9cf9', hx:4, hz:5},
  {k:'work', cn:'工位', color:'#f0a35e', hx:6, hz:7},
  {k:'social', cn:'社交', color:'#5fd39b', hx:8, hz:9},
  {k:'now', cn:'此刻', color:'#e05c7a', now:true}
];
const on = {home:true, work:true, social:false, now:false};
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const tip = document.getElementById('tip'), stage = document.getElementById('stage');
let W=0,H=0,DPR=1;
let view = {cx:0, cz:0, scale:1};

function resize(){
  const r = stage.getBoundingClientRect();
  DPR = window.devicePixelRatio || 1;
  W = r.width; H = r.height;
  cv.width = Math.round(W*DPR); cv.height = Math.round(H*DPR);
  cv.style.width = W+'px'; cv.style.height = H+'px';
  ctx.setTransform(DPR,0,0,DPR,0,0);
  draw();
}
function fit(){
  const [x0,z0,x1,z1] = D.bounds;
  const pad = 46;
  const sx = (W-pad*2)/Math.max(1,(x1-x0)), sz = (H-pad*2)/Math.max(1,(z1-z0));
  view.scale = Math.min(sx,sz);
  view.cx = (x0+x1)/2; view.cz = (z0+z1)/2;
}
function proj(x,z){
  return [W/2 + (x-view.cx)*view.scale, H/2 + (z-view.cz)*view.scale];
}
function draw(){
  ctx.clearRect(0,0,W,H);
  // 网格
  const g = 40*view.scale;
  if (g > 6){
    ctx.strokeStyle = '#131c26'; ctx.lineWidth = 1;
    const ox = (W/2 - view.cx*view.scale) %% g, oz = (H/2 - view.cz*view.scale) %% g;
    ctx.beginPath();
    for(let x=ox;x<W;x+=g){ctx.moveTo(x,0);ctx.lineTo(x,H);}
    for(let z=oz;z<H;z+=g){ctx.moveTo(0,z);ctx.lineTo(W,z);}
    ctx.stroke();
  }
  const states = D.states, anchorOf = D.anchorOf;
  for (const L of LAYERS){
    if (!on[L.k]) continue;
    ctx.fillStyle = L.color;
    const r = L.k==='now' ? Math.max(1.4, Math.min(3.2, view.scale*1.6)) : Math.max(0.8, Math.min(2.4, view.scale*1.2));
    for (let i=0;i<D.rows.length;i++){
      const row = D.rows[i];
      let x, z;
      if (L.now){
        const st = states[row[3]];
        if (!st) continue;
        const a = anchorOf[st.code] || 'home';
        if (a==='social' && row[8]===null) continue;
      }
      if (L.now){
        const a = anchorOf[states[row[3]].code] || 'home';
        x = a==='work'?row[6]:a==='social'?row[8]:row[4];
        z = a==='work'?row[7]:a==='social'?row[9]:row[5];
      } else {
        x = row[L.hx]; z = row[L.hz];
      }
      const p = proj(x,z);
      if (p[0]<-8||p[0]>W+8||p[1]<-8||p[1]>H+8) continue;
      ctx.fillRect(p[0]-r/2, p[1]-r/2, r, r);
    }
  }
  // 街区名标签
  ctx.font = '11px -apple-system,"Microsoft YaHei",sans-serif';
  ctx.fillStyle = '#3d4854';
  ctx.textAlign = 'center';
  for (let d=0; d<D.districts.length; d++){
    let sx=0, sz=0, n=0;
    for (const row of D.rows){ if (row[2]===d){ sx+=row[4]; sz+=row[5]; n++; } }
    if (!n) continue;
    const p = proj(sx/n, sz/n);
    ctx.fillText(D.districts[d].cn, p[0], p[1]);
  }
}
function nearest(mx,my){
  let best=null, bd=1e9;
  const states=D.states, anchorOf=D.anchorOf;
  for (const row of D.rows){
    let x = row[4], z = row[5];
    if (on.now && row[3]>=0){
      const a = anchorOf[states[row[3]].code] || 'home';
      if (a==='work'){x=row[6];z=row[7];}
      else if (a==='social' && row[8]!==null){x=row[8];z=row[9];}
    }
    const p = proj(x,z);
    const dx=p[0]-mx, dy=p[1]-my, d=dx*dx+dy*dy;
    if (d<bd){bd=d;best=row;}
  }
  return bd < 100 ? best : null;
}
cv.addEventListener('mousemove', e=>{
  const r = cv.getBoundingClientRect();
  const mx = e.clientX-r.left, my = e.clientY-r.top;
  const row = nearest(mx,my);
  if (!row){ tip.style.display='none'; return; }
  const st = D.states[row[3]] || {cn:'-'};
  tip.innerHTML = '<b>'+row[1]+'</b><span>'+row[0]+' · '+D.districts[row[2]].cn+' · '+row[10]+'</span><br><em>此刻：'+st.cn+'</em>';
  tip.style.display='block';
  tip.style.left = Math.min(mx+14, W-290)+'px';
  tip.style.top = Math.min(my+14, H-90)+'px';
});
cv.addEventListener('mouseleave', ()=>{ tip.style.display='none'; });
cv.addEventListener('wheel', e=>{
  e.preventDefault();
  const f = e.deltaY < 0 ? 1.15 : 1/1.15;
  view.scale = Math.max(0.3, Math.min(60, view.scale*f));
  draw();
}, {passive:false});
let drag=null;
cv.addEventListener('mousedown', e=>{ drag={x:e.clientX,y:e.clientY,cx:view.cx,cz:view.cz}; });
window.addEventListener('mouseup', ()=>{ drag=null; });
window.addEventListener('mousemove', e=>{
  if (!drag) return;
  view.cx = drag.cx - (e.clientX-drag.x)/view.scale;
  view.cz = drag.cz - (e.clientY-drag.y)/view.scale;
  draw();
});
cv.addEventListener('dblclick', ()=>{ fit(); draw(); });

// 侧栏
const layers = document.getElementById('layers');
LAYERS.forEach(L=>{
  const d = document.createElement('div');
  d.className = 'chip' + (on[L.k]?' on':'');
  d.innerHTML = '<i style="background:'+L.color+'"></i>'+L.cn;
  d.onclick = ()=>{ on[L.k]=!on[L.k]; d.classList.toggle('on', on[L.k]); draw(); };
  layers.appendChild(d);
});
const stateBox = document.getElementById('states');
D.states.forEach(s=>{
  const el = document.createElement('div');
  el.innerHTML = '<i style="background:#e05c7a"></i>'+s.cn+'<b>'+s.n+'</b>';
  stateBox.appendChild(el);
});
const distBox = document.getElementById('dists');
D.districts.forEach(s=>{
  const el = document.createElement('div');
  el.innerHTML = '<i style="background:#4f9cf9"></i>'+s.cn+'<b>'+s.n+'</b>';
  distBox.appendChild(el);
});
window.addEventListener('resize', ()=>{ resize(); });
resize(); fit(); draw();
</script>
</body></html>
""" % {"total": len(rows), "gen": gen_at, "payload": payload, "ctx": ctx or "-"}

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    print("OK rows=%d districts=%d states=%d out=%s bytes=%d"
          % (len(rows), len(dist_codes), len(state_codes), OUT, len(doc.encode("utf-8"))))


if __name__ == "__main__":
    main()