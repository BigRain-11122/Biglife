# -*- coding: utf-8 -*-
"""build_city_goals.py v1.0 — 居民目标志（goals 面首个可浏览页·确定性零 LLM）

契约：
  输入 = census/export/citizen-goals.jsonl（goals.py 派生面·只读）+ citizens-light.jsonl（只读姓名/城区/职业）
  输出 = census/export/city-goals.html（单页·总目录 build_export_index.py 自动收录）
  口径 = 只做加总与罗列，不改写任何目标文本、不发明居民事实；覆盖率分母=light 面行数。
  排序 = 四型固定序（出师/攒物/守望/安家）→ 步数降序 → 编号升序。
  确定性 = 同输入双跑逐字节一致（无随机、无时间戳入正文，生成时间只写页脚）。
"""
import html
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
GOALS = os.path.join(EXP, "citizen-goals.jsonl")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-goals.html")

TYPE_CN = {"mastery": "出师型（好奇轴）", "collect": "攒物型（生计轴）",
           "guard": "守望型（安稳轴）", "settle": "安家型（社交轴）"}
TYPE_ORDER = ["mastery", "collect", "guard", "settle"]
PHASE_CN = {"pending": "未启", "active": "进行中", "done": "达成"}
DISTRICT_CN = {"GM": "中央市集", "QT": "低语巷", "MD": "机房区",
               "NS": "北槐街区", "OR": "旧站台", "RV": "河岸"}

CSS = """
:root{--bg:#0f1115;--fg:#e6e8ee;--dim:#8b93a7;--line:#232735;--acc:#7ad1c8;--warn:#e0b155}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.65 "Microsoft YaHei",system-ui,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:28px 20px 60px}
h1{font-size:24px;margin:0 0 6px}
h2{font-size:17px;margin:32px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line);color:var(--acc)}
.sub{color:var(--dim);font-size:13px;margin:0 0 18px}
.metrics{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}
.m{background:#161923;border:1px solid var(--line);border-radius:8px;padding:12px 16px;min-width:150px}
.m b{display:block;font-size:22px;color:var(--acc);font-weight:600}
.m span{font-size:12px;color:var(--dim)}
.bar{display:flex;align-items:center;gap:10px;margin:7px 0;font-size:14px}
.bar .n{width:130px;color:var(--dim)}
.bar .t{flex:1;background:#1b1f2a;border-radius:4px;height:16px;position:relative}
.bar .t i{display:block;height:16px;background:linear-gradient(90deg,#3f8f88,#7ad1c8);border-radius:4px}
.bar .c{width:44px;text-align:right;color:var(--fg)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:500;font-size:12px}
tr:hover td{background:#151922}
.gp{display:inline-block;padding:1px 7px;border-radius:3px;background:#1e2530;color:var(--acc);font-size:12px}
.axis{color:var(--warn);font-size:12px}
footer{margin-top:40px;color:var(--dim);font-size:12px}
a{color:var(--acc);text-decoration:none}
"""


def load_jsonl(path):
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows


def bar(label, count, total, cls=""):
    pct = (count / total * 100) if total else 0
    return (f'<div class="bar"><div class="n">{html.escape(label)}</div>'
            f'<div class="t"><i style="width:{pct:.1f}%"></i></div>'
            f'<div class="c">{count}</div></div>')


def main():
    goals = load_jsonl(GOALS)
    light = {r["id"]: r for r in load_jsonl(LIGHT) if r.get("id")}
    total_citizens = len(light)
    n = len(goals)

    types = Counter(g.get("type", "?") for g in goals)
    phases = Counter(g.get("phase", "?") for g in goals)
    months = sorted({g.get("month", "") for g in goals})
    steps = Counter(g.get("steps_total", 0) for g in goals)
    dist = Counter(light.get(g["id"], {}).get("district", "") for g in goals)

    rows = sorted(goals, key=lambda g: (
        TYPE_ORDER.index(g["type"]) if g.get("type") in TYPE_ORDER else 99,
        -int(g.get("steps_done", 0)), g.get("id", "")))

    out = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width,initial-scale=1">'
           f'<title>居民目标志 · BigLife</title><style>{CSS}</style></head><body><div class="wrap">',
           '<h1>居民目标志</h1>',
           '<p class="sub">L4 目标系统试点面 · 一行一民的目标、进度与达成状态（纯派生确定性记账，非卡面写入）</p>',
           '<div class="metrics">',
           f'<div class="m"><b>{n}</b><span>试点居民（md5 试点门）</span></div>',
           f'<div class="m"><b>{total_citizens}</b><span>全库居民</span></div>',
           f'<div class="m"><b>{(n / total_citizens * 100) if total_citizens else 0:.2f}%</b><span>目标面覆盖率</span></div>',
           f'<div class="m"><b>{phases.get("done", 0)}</b><span>达成态</span></div>',
           f'<div class="m"><b>{months[0] if months else "-"}</b><span>记账月份</span></div>',
           '</div>']

    out.append('<h2>四型分布</h2>')
    for t in TYPE_ORDER:
        out.append(bar(TYPE_CN[t], types.get(t, 0), n))

    out.append('<h2>达成进度（步数总幅）</h2>')
    for s in sorted(steps):
        done = sum(1 for g in goals if g.get("steps_total") == s and g.get("phase") == "done")
        out.append(bar(f"{s} 步目标", done, n))

    out.append('<h2>状态分布</h2>')
    for p in ["pending", "active", "done"]:
        out.append(bar(PHASE_CN[p], phases.get(p, 0), n))

    out.append('<h2>城区分布</h2>')
    for code, cnt in dist.most_common():
        name = DISTRICT_CN.get(code, code or "未标注")
        out.append(bar(name, cnt, n))

    out.append('<h2>试点名册</h2>')
    out.append('<table><thead><tr><th>编号</th><th>居民</th><th>城区</th><th>职业</th>'
               '<th>目标</th><th>型</th><th>进度</th></tr></thead><tbody>')
    for g in rows:
        c = light.get(g.get("id", ""), {})
        out.append('<tr>'
                   f'<td>{html.escape(str(g.get("id", "")))}</td>'
                   f'<td>{html.escape(str(c.get("name", "—")))}</td>'
                   f'<td>{html.escape(DISTRICT_CN.get(c.get("district", ""), c.get("district", "") or "—"))}</td>'
                   f'<td>{html.escape(str(c.get("profession", "—") or "—"))}</td>'
                   f'<td>{html.escape(str(g.get("goal_token", "")))}</td>'
                   f'<td><span class="gp">{html.escape(g.get("type", ""))}</span> '
                   f'<span class="axis">{html.escape(str(g.get("axis", "")))}</span></td>'
                   f'<td>{g.get("steps_done", 0)}/{g.get("steps_total", 0)} '
                   f'{html.escape(PHASE_CN.get(g.get("phase"), g.get("phase", "")))}</td>'
                   '</tr>')
    out.append('</tbody></table>')

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    out.append(f'<footer>数据源 census/export/citizen-goals.jsonl（{n} 行）+ citizens-light.jsonl（{total_citizens} 行）'
               f' · 生成 {ts} · <a href="index.html">返回产物总目录</a></footer>')
    out.append('</div></body></html>')

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    print(f"OK city-goals.html goals={n} citizens={total_citizens} types={dict(types)}")


if __name__ == "__main__":
    main()