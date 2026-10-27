# -*- coding: utf-8 -*-
"""库覆盖缺口面板（确定性·零 LLM·幂等）

读 census/export/citizens-light.jsonl（户籍）+ census/export/growth-archives/（成长档案）
+ census/registry 卡面（相遇留痕），产出：
  1) census/export/city-coverage.html —— 可管四维覆盖率 + 分街区覆盖表 + 缺口名单 + 相遇容量面
  2) census/export/coverage-backlog.jsonl —— 缺口清单（夜间年轮批可直接照单开工）

可管四维（管线欠账·逐人可补）：人设信条 creed / 认知摘要 brain_digest / 年轮 recent_ring / 成长档案
容量维度（不计个人缺口）：相遇留痕——受每日相遇轮上限（3 对/日）硬约束，属城市级稀缺指标；
把它算进每人缺口会让「齐备」恒为 0、清单一万行全红而不可操作（2026-10-27 口径勘正）。
用法: python -X utf8 Tools/build_coverage.py
"""
import datetime
import glob
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
SRC = os.path.join(EXP, "citizens-light.jsonl")
ARCH = os.path.join(EXP, "growth-archives")
OUT_HTML = os.path.join(EXP, "city-coverage.html")
OUT_JSONL = os.path.join(EXP, "coverage-backlog.jsonl")
TOP = 240

sys.path.insert(0, os.path.join(ROOT, "Tools"))
from build_city_meets import DISTRICT_CN, load_cards  # noqa: E402

# 可管四维：由管线逐人补齐，缺=欠账
DIMS = [
    ("creed", "人设信条"),
    ("brain", "认知摘要"),
    ("ring", "年轮"),
    ("growth", "成长档案"),
]
MEET_LABEL = "相遇留痕"
MEET_PER_DAY = 3  # 相遇轮每日上限（轮 prompt 步 4 · meet-cap）
# 补齐优先级：年轮是其余维度的入口，先年轮再认知/信条，成长档案随年轮批自动生成
ACTION_ORDER = ["ring", "brain", "creed", "growth"]


def load_rows():
    rows = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def growth_ids():
    ids = set()
    for p in glob.glob(os.path.join(ARCH, "growth-C-*.json")):
        ids.add(os.path.basename(p)[len("growth-"):-len(".json")])
    return ids


def esc(s):
    return html.escape(str(s or ""), quote=True)


def bar(label, cnt, total, extra=""):
    pct = cnt / total * 100 if total else 0
    return (
        '<div class="row"><span class="lab">%s</span>'
        '<span class="track"><i style="width:%.1f%%"></i></span>'
        '<span class="num">%d · %.1f%%%s</span></div>'
        % (esc(label), pct, cnt, pct, extra)
    )


def main():
    rows = load_rows()
    total = len(rows)
    arch = growth_ids()
    _people, meets = load_cards()
    meet_n = {}
    for _date, frm, to, _line in meets:
        meet_n[frm] = meet_n.get(frm, 0) + 1
        meet_n[to] = meet_n.get(to, 0) + 1

    gaps = []
    dim_cnt = {k: 0 for k, _ in DIMS}
    by_dist = {}
    reserved = 0
    meet_people = 0
    for r in rows:
        cid = r.get("id") or ""
        # 荣誉席（T0 人设权·CEO 保留面）不参与缺口统计：其内容由 CEO 亲定，非管线欠账
        if r.get("faction") == "honored":
            reserved += 1
            continue
        have = {
            "creed": bool((r.get("creed") or "").strip()),
            "brain": bool((r.get("brain_digest") or "").strip()),
            "ring": bool((r.get("recent_ring") or "").strip()),
            "growth": cid in arch,
            "meet": meet_n.get(cid, 0) > 0,
        }
        if have["meet"]:
            meet_people += 1
        for k, _ in DIMS:
            if have[k]:
                dim_cnt[k] += 1
        miss = [k for k, _ in DIMS if not have[k]]
        d = r.get("district") or ""
        bk = d or "(未落区)"
        cell = by_dist.setdefault(bk, [0, 0])
        cell[0] += 1
        cell[1] += len(miss)
        if miss:
            gaps.append(
                {
                    "id": cid,
                    "name": r.get("name") or "",
                    "district": d,
                    "missing": miss,
                    "gaps": len(miss),
                    "has_ring": have["ring"],
                    # 相遇不计个人缺口，仅作旁注供选人参考
                    "met": have["meet"],
                    "next_action": next(k for k in ACTION_ORDER if not have[k]),
                }
            )

    gaps.sort(key=lambda g: (-g["gaps"], g["id"]))
    with open(OUT_JSONL, "w", encoding="utf-8", newline="\n") as f:
        for g in gaps:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")

    scope = total - reserved
    full = scope - len(gaps)
    bars = "\n".join(
        bar(lab, dim_cnt[k], scope, " · 缺 %d" % (scope - dim_cnt[k])) for k, lab in DIMS
    )
    dist_rows = []
    for bk, (n, miss_sum) in sorted(by_dist.items(), key=lambda kv: -kv[1][0]):
        avg = miss_sum / n if n else 0
        dist_rows.append(
            "<tr><td>%s</td><td>%d</td><td>%.2f</td></tr>" % (esc(bk), n, avg)
        )

    cards = []
    for g in gaps[:TOP]:
        miss_cn = "、".join(lab for k, lab in DIMS if k in g["missing"])
        cards.append(
            '<article class="card"><header><b>%s</b><time>%s</time></header>'
            '<p class="meta">%s · 缺 %d 维</p><p class="ring">待补：%s</p></article>'
            % (esc(g["name"] or g["id"]), esc(g["id"]),
               esc(DISTRICT_CN.get(g["district"], g["district"]) or "未落区"),
               g["gaps"], esc(miss_cn))
        )

    gen = datetime.datetime.fromtimestamp(os.path.getmtime(SRC)).strftime("%Y-%m-%d %H:%M")
    meet_eta = ((scope - meet_people) / (MEET_PER_DAY * 2.0)) if scope > meet_people else 0
    doc = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>硅基城市库覆盖 · 缺口面板</title>
<style>
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:12px;margin-bottom:28px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
.kpi{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
section{margin-bottom:28px}
h2{font-size:15px;color:var(--dim);font-weight:600;letter-spacing:.4px;margin:0 0 12px;text-transform:uppercase}
.row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}
.lab{flex:0 0 130px;color:var(--fg)}
.track{flex:1;height:8px;background:#161b22;border-radius:4px;overflow:hidden}
.track i{display:block;height:100%%;background:linear-gradient(90deg,#3d7dd6,#63b3ff);border-radius:4px}
.num{flex:0 0 140px;text-align:right;color:var(--dim);font-variant-numeric:tabular-nums}
table{width:100%%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:600;font-size:12px}
td{font-variant-numeric:tabular-nums}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:12px}
.card{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card header{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.card header b{font-size:14px}
.card time{color:var(--warm);font-size:11px;font-variant-numeric:tabular-nums}
.meta{color:var(--dim);font-size:11px;margin:2px 0 8px}
.ring{margin:0;font-size:13px;color:#c9d1d9}
.note{color:var(--dim);font-size:12.5px;line-height:1.8;margin:10px 0 0}
.note a{color:var(--acc);text-decoration:none}
footer{margin-top:36px;color:#57606a;font-size:11px;border-top:1px solid var(--line);padding-top:14px}
</style></head><body><div class="wrap">
<h1>硅基城市库覆盖 · 缺口面板</h1>
<div class="sub">可管四维覆盖与缺口清单 + 相遇容量面 · 数据截至 %(gen)s · 源 census/export/citizens-light.jsonl + growth-archives + registry 卡面</div>

<div class="kpis">
  <div class="kpi"><b>%(total)d</b><span>在册居民（含荣誉席 %(res)d · 不计缺口）</span></div>
  <div class="kpi"><b>%(full)d</b><span>四维齐备 · 占管线圈 %(fullpct).1f%%</span></div>
  <div class="kpi"><b>%(gapn)d</b><span>有缺口席 · 占管线圈 %(gappct).1f%%</span></div>
  <div class="kpi"><b>%(meetp)d</b><span>有相遇留痕 · 城市级稀缺面</span></div>
</div>

<section><h2>可管四维覆盖（缺=管线欠账·逐人可补）</h2>
%(bars)s
</section>

<section><h2>相遇容量面（不计个人缺口）</h2>
<div class="row"><span class="lab">%(meetlab)s</span><span class="track"><i style="width:%(meetpct).1f%%"></i></span><span class="num">%(meetp)d · %(meetpct).1f%%</span></div>
<p class="note">相遇受每日相遇轮上限 %(cap)d 对/日 硬约束：留痕人数 %(meetp)d ≈ 相遇对数 × 2。
按当前产能覆盖全员需约 <b>%(meeteta)s</b> 天——这是容量问题不是欠账，故不进缺口清单、不占「齐备」判定。
想看今晚该让谁遇见谁：<a href="meet-candidates.html">相遇候选单</a> · 已发生的：<a href="city-meets.html">相遇编年史</a>。</p>
</section>

<section><h2>分街区缺口均值（每位居民平均缺几维）</h2>
<table><thead><tr><th>街区</th><th>居民数</th><th>平均缺口</th></tr></thead>
<tbody>
%(dist)s
</tbody></table>
</section>

<section><h2>缺口名单（按缺口维度数排序 · 前 %(top)d 席）</h2>
<div class="grid">
%(cards)s
</div>
</section>

<footer>机器清单：census/export/coverage-backlog.jsonl（%(gapn)d 行·夜间年轮批可照单开工）· 生成器 Tools/build_coverage.py（零 LLM·幂等）</footer>
</div></body></html>
""" % {
        "gen": gen,
        "total": total,
        "res": reserved,
        "gappct": (len(gaps) / scope * 100 if scope else 0),
        "full": full,
        "fullpct": (full / scope * 100 if scope else 0),
        "gapn": len(gaps),
        "meetp": meet_people,
        "meetpct": (meet_people / scope * 100 if scope else 0),
        "meetlab": MEET_LABEL,
        "cap": MEET_PER_DAY,
        "meeteta": "%.0f 天（≈%.1f 年）" % (meet_eta, meet_eta / 365.0),
        "bars": bars,
        "dist": "\n".join(dist_rows),
        "top": min(TOP, len(gaps)),
        "cards": "\n".join(cards),
    }
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)

    print(
        "coverage: people=%d reserved=%d scope=%d full=%d gaps=%d meet_people=%d (%d 条留痕) backlog=%s"
        % (total, reserved, scope, full, len(gaps), meet_people, len(meets),
           os.path.basename(OUT_JSONL))
    )
    for k, lab in DIMS:
        print("  %s %d/%d %.1f%%" % (lab, dim_cnt[k], scope, dim_cnt[k] / scope * 100))


if __name__ == "__main__":
    main()