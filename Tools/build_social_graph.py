#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成硅基城市社会关系图谱单页（确定性·零 LLM）。

数据源：
  census/export/citizen-relations.jsonl  (a,b,rel,src)
  census/export/citizens-light.jsonl     (id,name,district,profession,...)

只取真实社会关系（buddy/household/meet），block（街区相邻）不计入社交图谱，
但统计进总量。布局用固定种子力导向迭代，保证同输入同输出。

用法：
  python -X utf8 Tools/build_social_graph.py [--top 600] [--out census/city-social-graph.html]
"""
import argparse
import json
import math
import os
import random
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join(ROOT, "census", "export", "citizen-relations.jsonl")
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
SOCIAL_RELS = ("buddy", "household", "meet")
REL_CN = {"buddy": "好友", "household": "同居", "meet": "相遇"}


def load_people():
    people = {}
    if not os.path.exists(LIGHT):
        return people
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            people[d.get("id")] = {
                "n": (d.get("name") or "").strip(),
                "d": (d.get("district") or "").strip(),
                "p": (d.get("profession") or "").strip(),
            }
    return people


def load_graph():
    deg = {}
    rel_count = {}
    social_edges = []
    block_edges = 0
    total = 0
    district_pairs = {}
    with open(REL, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            total += 1
            a, b, r = d.get("a"), d.get("b"), d.get("rel")
            if not a or not b or a == b:
                continue
            rel_count[r] = rel_count.get(r, 0) + 1
            if r in SOCIAL_RELS:
                social_edges.append((a, b, r))
                deg[a] = deg.get(a, 0) + 1
                deg[b] = deg.get(b, 0) + 1
                key = r
                district_pairs.setdefault(key, []).append(d.get("src") or "")
            else:
                block_edges += 1
    return deg, rel_count, social_edges, block_edges, total


def layout(nodes, edges, w=1400, h=820, iters=180, seed=20261020):
    """确定性力导向：固定种子 + 固定迭代。"""
    rnd = random.Random(seed)
    cx, cy = w / 2.0, h / 2.0
    n = len(nodes)
    pos = {}
    for i, nid in enumerate(nodes):
        ang = i * 2.399963229728653  # 黄金角螺旋
        r = 12 + 11 * math.sqrt(i)
        pos[nid] = [cx + r * math.cos(ang) + rnd.uniform(-4, 4),
                    cy + r * math.sin(ang) + rnd.uniform(-4, 4)]
    if n < 2:
        return pos
    idx = {nid: i for i, nid in enumerate(nodes)}
    k = math.sqrt((w * h) / float(n)) * 0.55
    adj = [[] for _ in range(n)]
    for a, b, _t in edges:
        ia, ib = idx[a], idx[b]
        adj[ia].append(ib)
        adj[ib].append(ia)
    temp = k * 1.2
    for _ in range(iters):
        disp = [[0.0, 0.0] for _ in range(n)]
        # 斥力（网格近似：只算邻近）
        for i in range(n):
            xi, yi = pos[nodes[i]]
            for j in range(i + 1, n):
                xj, yj = pos[nodes[j]]
                dx, dy = xi - xj, yi - yj
                d2 = dx * dx + dy * dy
                if d2 < 1e-6:
                    dx, dy, d2 = rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1.0
                if d2 > (k * 3.2) ** 2:
                    continue
                f = (k * k) / d2
                d = math.sqrt(d2)
                ux, uy = dx / d, dy / d
                disp[i][0] += ux * f
                disp[i][1] += uy * f
                disp[j][0] -= ux * f
                disp[j][1] -= uy * f
        # 引力（边）
        for i in range(n):
            for j in adj[i]:
                if j <= i:
                    continue
                xi, yi = pos[nodes[i]]
                xj, yj = pos[nodes[j]]
                dx, dy = xi - xj, yi - yj
                d = math.sqrt(dx * dx + dy * dy) or 1.0
                f = (d * d) / k
                ux, uy = dx / d, dy / d
                disp[i][0] -= ux * f
                disp[i][1] -= uy * f
                disp[j][0] += ux * f
                disp[j][1] += uy * f
        # 向心力 + 位移限幅
        for i, nid in enumerate(nodes):
            p = pos[nid]
            disp[i][0] += (cx - p[0]) * 0.012 * k
            disp[i][1] += (cy - p[1]) * 0.012 * k
            dx, dy = disp[i]
            d = math.sqrt(dx * dx + dy * dy) or 1.0
            lim = min(d, temp)
            p[0] += dx / d * lim
            p[1] += dy / d * lim
            p[0] = max(24.0, min(w - 24.0, p[0]))
            p[1] = max(24.0, min(h - 24.0, p[1]))
        temp *= 0.972
    return pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=600)
    ap.add_argument("--out", default=os.path.join(ROOT, "census", "city-social-graph.html"))
    args = ap.parse_args()

    t0 = time.time()
    people = load_people()
    deg, rel_count, social_edges, block_edges, total = load_graph()

    ranked = sorted(deg.items(), key=lambda kv: (-kv[1], kv[0]))

    # 采样策略：社交图是稀疏多簇结构（平均度 3.8），按度数取前 N 会散成孤点。
    # 改为「最大若干连通簇内 BFS 采样」——保证图上有真实结构，且各簇块分明。
    adj = {}
    for a, b, _r in social_edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, comps = set(), []
    for start in adj:
        if start in seen:
            continue
        stack, comp = [start], []
        seen.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    big = comps[:4]
    total_big = sum(len(c) for c in big) or 1
    budget = args.top
    top_ids = []
    for comp in big:
        quota = max(40, int(round(budget * len(comp) / float(total_big))))
        comp_sorted = sorted(comp, key=lambda nid: (-deg[nid], nid))
        seed = comp_sorted[0]
        order, q, got = [seed], [seed], {seed}
        while q and len(order) < quota:
            u = q.pop(0)
            for v in sorted(adj[u], key=lambda nid: (-deg[nid], nid)):
                if v not in got:
                    got.add(v)
                    order.append(v)
                    q.append(v)
                    if len(order) >= quota:
                        break
        top_ids.extend(order)
    top_set = set(top_ids)
    top_edges = [(a, b, r) for a, b, r in social_edges if a in top_set and b in top_set]

    # 分簇布局后拼进 2x2 区域，避免不同簇互相压叠
    groups = []
    comp_of = {}
    for ci, comp in enumerate(big):
        ids = [nid for nid in top_ids if nid in set(comp)]
        for nid in ids:
            comp_of[nid] = ci
        if ids:
            groups.append(ids)
    boxes = [(0, 0), (700, 0), (0, 420), (700, 420)]
    pos = {}
    for gi, ids in enumerate(groups):
        sub_edges = [e for e in top_edges if e[0] in set(ids) and e[1] in set(ids)]
        lp = layout(ids, sub_edges, w=700, h=420, iters=140)
        dx, dy = boxes[gi % 4]
        for nid in ids:
            x, y = lp[nid]
            pos[nid] = (x + dx, y + dy)
    nodes_out = []
    for nid in top_ids:
        p = people.get(nid, {})
        x, y = pos[nid]
        nodes_out.append({
            "id": nid,
            "n": p.get("n") or nid,
            "d": p.get("d") or "",
            "p": p.get("p") or "",
            "x": round(x, 1),
            "y": round(y, 1),
            "g": deg[nid],
            "c": comp_of.get(nid, 0),
        })
    index = {nid: i for i, nid in enumerate(top_ids)}
    edges_out = [[index[a], index[b], r] for a, b, r in top_edges]

    # 全量社交节点（供搜索，含未进图的居民及其伙伴）
    partners = {}
    for a, b, r in social_edges:
        partners.setdefault(a, []).append([b, r])
        partners.setdefault(b, []).append([a, r])
    search = []
    for nid, lst in sorted(partners.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        p = people.get(nid, {})
        lst = sorted(lst, key=lambda t: (t[1], t[0]))
        search.append({
            "id": nid,
            "n": p.get("n") or nid,
            "d": p.get("d") or "",
            "p": p.get("p") or "",
            "g": len(lst),
            "k": [[x[0], x[1]] for x in lst[:24]],
        })

    meta = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "total_edges": total,
        "block_edges": block_edges,
        "social_edges": len(social_edges),
        "rel": {REL_CN.get(k, k): v for k, v in sorted(rel_count.items(), key=lambda kv: -kv[1])},
        "social_nodes": len(partners),
        "shown": len(nodes_out),
        "shown_edges": len(edges_out),
        "max_deg": ranked[0][1] if ranked else 0,
        "components": [len(c) for c in comps[:8]],
        "shown_components": len(groups),
        "top": [[nid, deg[nid], (people.get(nid, {}).get("n") or nid)] for nid, _ in ranked[:10]],
    }
    payload = {"meta": meta, "nodes": nodes_out, "edges": edges_out, "search": search}
    html = TPL.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print("written", args.out, "nodes=%d edges=%d social_nodes=%d total=%d sec=%.1f"
          % (len(nodes_out), len(edges_out), len(partners), total, time.time() - t0))


TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城市 · 社会关系图谱 | BigLife</title>
<style>
:root{--bg:#0b0f14;--panel:#131a23;--line:#22303f;--tx:#dce7f3;--dim:#8ea3b8;--buddy:#4fd1c5;--house:#f6ad55;--meet:#f472b6;}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 700px at 50% -10%,#16222f 0%,#0b0f14 60%);color:var(--tx);font:14px/1.6 "Segoe UI","Microsoft YaHei",system-ui,sans-serif}
header{padding:18px 22px 10px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:19px;font-weight:600;letter-spacing:.5px}
h1 small{font-weight:400;color:var(--dim);font-size:12px;margin-left:10px}
.stats{display:flex;flex-wrap:wrap;gap:10px;padding:12px 22px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 14px;min-width:104px}
.card b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.card span{font-size:11px;color:var(--dim)}
main{display:grid;grid-template-columns:1fr 320px;gap:14px;padding:14px 22px 24px;align-items:start}
#wrap{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
canvas{display:block;width:100%;height:auto;cursor:grab}
canvas.drag{cursor:grabbing}
#tip{position:absolute;pointer-events:none;background:#0b0f14ee;border:1px solid var(--line);border-radius:8px;padding:6px 9px;font-size:12px;opacity:0;transition:opacity .12s;white-space:nowrap}
aside{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
aside h2{margin:0 0 8px;font-size:13px;color:var(--dim);font-weight:500;letter-spacing:.5px}
input{width:100%;background:#0b0f14;border:1px solid var(--line);border-radius:8px;color:var(--tx);padding:8px 10px;font-size:13px;outline:none}
input:focus{border-color:#3b6f8f}
#hits{max-height:220px;overflow:auto;margin:8px 0 0;padding:0;list-style:none}
#hits li{padding:6px 8px;border-radius:6px;cursor:pointer;border:1px solid transparent}
#hits li:hover{background:#1a2633;border-color:var(--line)}
#hits li b{font-weight:500}
#hits li i{font-style:normal;color:var(--dim);font-size:11px;margin-left:6px}
#detail{margin-top:12px;border-top:1px solid var(--line);padding-top:10px;font-size:12.5px;color:var(--dim);min-height:120px}
#detail .who{color:var(--tx);font-size:14px;font-weight:600;margin-bottom:2px}
.chip{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:1px 8px;margin:3px 4px 0 0;font-size:11px;color:var(--tx)}
.legend{display:flex;gap:14px;padding:0 22px 4px;font-size:12px;color:var(--dim)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:-1px}
footer{padding:0 22px 22px;color:#5f7488;font-size:11.5px}
@media(max-width:900px){main{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>硅基城市 · 社会关系图谱 <small>BigLife · 数据面确定性生成（零 LLM）</small></h1>
</header>
<div class="stats" id="stats"></div>
<div class="legend">
  <span><i class="dot" style="background:var(--buddy)"></i>好友</span>
  <span><i class="dot" style="background:var(--house)"></i>同居</span>
  <span><i class="dot" style="background:var(--meet)"></i>相遇</span>
  <span style="color:#4a5f73">街区相邻关系不入图（仅统计）</span>
</div>
<main>
  <div id="wrap"><canvas id="cv"></canvas><div id="tip"></div></div>
  <aside>
    <h2>检索居民</h2>
    <input id="q" placeholder="输入编号或姓名，如 C-00123 / 大圣" autocomplete="off">
    <ul id="hits"></ul>
    <div id="detail">点击图上节点或检索居民，查看其社会关系。</div>
  </aside>
</main>
<footer id="ft"></footer>
<script>
const D = __DATA__;
const cv = document.getElementById('cv'), ctx = cv.getContext('2d'), wrap = document.getElementById('wrap');
const COL = {buddy:'#4fd1c5', household:'#f6ad55', meet:'#f472b6'};
const CN = {buddy:'好友', household:'同居', meet:'相遇'};
let W=1400,H=820,scale=1,ox=0,oy=0,sel=-1,hitIdx=-1,hover=-1;
const nb = D.nodes.map(()=>[]);
D.edges.forEach(([a,b,r])=>{nb[a].push(b); nb[b].push(a);});

function stats(){
  const m=D.meta, box=document.getElementById('stats');
  const cards=[
    [m.social_edges,'社会关系边'],
    [m.rel['好友']||0,'好友'], [m.rel['同居']||0,'同居'], [m.rel['相遇']||0,'相遇'],
    [m.social_nodes,'有社交关系的居民'],
    [m.total_edges,'关系总量（含街区）'],
    [m.max_deg,'最高关系度']
  ];
  box.innerHTML = cards.map(([v,k])=>`<div class="card"><b>${v.toLocaleString()}</b><span>${k}</span></div>`).join('');
  document.getElementById('ft').textContent =
    `生成 ${m.generated} · 图中展示 ${m.shown} 位居民 / ${m.shown_edges} 条社交边（按关系度取前 ${m.shown}） · 社交节点全量 ${m.social_nodes} 可检索 · 数据源 census/export/citizen-relations.jsonl`;
}

function resize(){
  const w = wrap.clientWidth; scale = w / W;
  cv.width = W * devicePixelRatio; cv.height = H * devicePixelRatio;
  cv.style.height = (H*scale)+'px';
  ctx.setTransform(devicePixelRatio*scale,0,0,devicePixelRatio*scale,0,0);
  draw(); stats();
}
function toCanvas(e){
  const r=cv.getBoundingClientRect();
  return [(e.clientX-r.left)/ (r.width/W), (e.clientY-r.top)/(r.height/H)];
}
function dist2(n,x,y){const dx=n.x-x,dy=n.y-y;return dx*dx+dy*dy;}

function draw(){
  ctx.clearRect(0,0,W,H);
  const base = Math.min(1, D.nodes.length ? 1 : 1);
  // edges
  D.edges.forEach(([a,b,r])=>{
    const A=D.nodes[a],B=D.nodes[b];
    const lit = sel<0 ? 0.30 : (a===sel||b===sel ? 0.95 : 0.06);
    ctx.strokeStyle = COL[r] || '#335';
    ctx.globalAlpha = lit;
    ctx.lineWidth = (r==='meet'?1.8:(r==='household'?1.2:0.7));
    ctx.beginPath(); ctx.moveTo(A.x,A.y); ctx.lineTo(B.x,B.y); ctx.stroke();
  });
  ctx.globalAlpha = 1;
  // nodes
  const maxg = D.meta.shown ? D.nodes.reduce((m,n)=>Math.max(m,n.g),1) : 1;
  D.nodes.forEach((n,i)=>{
    const rad = 2.2 + 5.4*Math.sqrt(n.g/maxg);
    const isSel = i===sel, isNb = sel>=0 && nb[sel].includes(i);
    ctx.beginPath(); ctx.arc(n.x,n.y,rad,0,6.2832);
    ctx.fillStyle = isSel ? '#ffffff' : (isNb ? '#9fe8dc' : '#5d8aa8');
    ctx.globalAlpha = sel<0 ? 0.9 : (isSel||isNb ? 1 : 0.25);
    ctx.fill();
    ctx.globalAlpha = 1;
    if(isSel){ ctx.strokeStyle='#4fd1c5'; ctx.lineWidth=2; ctx.beginPath(); ctx.arc(n.x,n.y,rad+4,0,6.2832); ctx.stroke(); }
  });
  // labels for top nodes
  ctx.font='11px "Segoe UI",sans-serif'; ctx.fillStyle='#93a9bd'; ctx.textAlign='center';
  D.nodes.slice(0,26).forEach((n,i)=>{ ctx.fillText(n.n, n.x, n.y-8); });
  // cluster captions
  const boxes=[[0,0],[700,0],[0,420],[700,420]];
  ctx.textAlign='left'; ctx.font='12px "Segoe UI",sans-serif'; ctx.fillStyle='#3f5568';
  for(let c=0;c<Math.min(D.meta.shown_components,4);c++){
    const b=boxes[c]; const size=D.meta.components[c];
    ctx.fillText(`关系簇 ${c+1} · ${size} 人 · 图中采样 ${D.nodes.filter(n=>n.c===c).length}`, b[0]+18, b[1]+24);
  }
}

function pick(x,y){
  let best=-1,bd=1e9;
  D.nodes.forEach((n,i)=>{const d=dist2(n,x,y); if(d<bd){bd=d;best=i;}});
  return bd < 900 ? best : -1;
}
cv.addEventListener('mousemove',e=>{
  const [x,y]=toCanvas(e); const i=pick(x,y);
  const tip=document.getElementById('tip');
  if(i>=0){ hover=i; const n=D.nodes[i];
    tip.innerHTML=`<b>${n.n}</b> <span style="color:#8ea3b8">${n.id}</span><br>${n.d}${n.p?' · '+n.p:''}<br>关系度 ${n.g}`;
    tip.style.opacity=1; tip.style.left=(e.offsetX+14)+'px'; tip.style.top=(e.offsetY+14)+'px';
  } else tip.style.opacity=0;
});
cv.addEventListener('click',e=>{
  const [x,y]=toCanvas(e); const i=pick(x,y);
  if(i>=0){ select(i); }
});
function select(i){
  sel=i; const n=D.nodes[i];
  const list = nb[i].map(j=>({n:D.nodes[j], r:(D.edges.find(([a,b])=> (a===i&&b===j)||(b===i&&a===j))||[0,0,''])[2]}));
  list.sort((a,b)=>a.r.localeCompare(b.r));
  document.getElementById('detail').innerHTML =
    `<div class="who">${n.n} <span style="color:#8ea3b8;font-size:11px">${n.id}</span></div>
     <div>${n.d}${n.p?' · '+n.p:''} · 图中关系度 ${n.g}</div>
     <div style="margin-top:6px">${list.length?list.slice(0,14).map(o=>`<span class="chip">${CN[o.r]||o.r}·${o.n.n}</span>`).join(''):'（该居民的社会关系对象不在前 '+D.meta.shown+' 位内）'}</div>`;
  draw();
}

// search
const q=document.getElementById('q'), hits=document.getElementById('hits');
function renderHits(){
  const s=q.value.trim().toLowerCase();
  if(!s){hits.innerHTML='';return;}
  const out=[];
  for(const p of D.search){
    if(out.length>=9) break;
    if(p.id.toLowerCase().includes(s)||(p.n&&p.n.toLowerCase().includes(s))) out.push(p);
  }
  hits.innerHTML = out.map(p=>`<li data-id="${p.id}"><b>${p.n}</b> <i>${p.id} · ${p.d} · 关系度 ${p.g}</i></li>`).join('')
    || '<li style="color:#5f7488;cursor:default">无匹配</li>';
  hits.querySelectorAll('li[data-id]').forEach(li=>li.onclick=()=>{
    const p=D.search.find(x=>x.id===li.dataset.id);
    const idx=D.nodes.findIndex(x=>x.id===li.dataset.id);
    if(idx>=0) { select(idx); }
    else {
      sel=-1; draw();
      document.getElementById('detail').innerHTML =
        `<div class="who">${p.n} <span style="color:#8ea3b8;font-size:11px">${p.id}</span></div>
         <div>${p.d}${p.p?' · '+p.p:''} · 社会关系度 ${p.g}（未进前 ${D.meta.shown} 位，不在图中）</div>
         <div style="margin-top:6px">${p.k.map(([id,r])=>{const o=D.search.find(x=>x.id===id)||{n:id}; return `<span class="chip">${CN[r]||r}·${o.n}</span>`}).join('')}</div>`;
    }
  });
}
q.addEventListener('input', renderHits);
window.addEventListener('resize', resize);
resize();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()