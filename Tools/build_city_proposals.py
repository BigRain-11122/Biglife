# -*- coding: utf-8 -*-
"""build_city_proposals.py v1.0 — 城市议会提案面（proposals 首个可浏览页·确定性零 LLM）

契约：
  输入 = cognition/proposals.jsonl（提案台账·只读）+ census/export/citizens-light.jsonl（只读姓名/城区/职业）
  输出 = census/export/city-proposals.html（单页·总目录 build_export_index.py 自动收录）
  口径 = 只做加总与罗列，不改写任何提案文本、不发明议员事实。
  早期行 = 2026-11-12 机读串门禁（MACHINE_TOKEN_ALT 并入 EVENT_CODE_RE）之前落的行：
           按现行判据实测带机读串者不展示原文（存量不回改·只标注），判据从
           evolve_citizen 直接 import ＝单源。
  确定性 = 无随机；排序按 (created_at desc, proposal_id)；生成时间只写页脚。
  用法 = python -X utf8 Tools/build_city_proposals.py
"""
import html
import json
import os
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
PROPOSALS = os.path.join(ROOT, "cognition", "proposals.jsonl")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-proposals.html")
PROPOSE_CAP = 3  # 与 evolve_citizen.PROPOSE_CAP 同值（珍稀律·契约 PROPOSALS.md §一）

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
.note{background:#1a1d27;border-left:3px solid var(--warn);border-radius:6px;padding:12px 14px;margin:16px 0;font-size:13.5px}
.note b{color:var(--warn)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:500;font-size:12px}
tr:hover td{background:#151922}
.id{color:var(--acc);font-size:12px;white-space:nowrap}
.dim{color:var(--dim)}
.muted{color:#6d7488;font-style:italic}
.tag{display:inline-block;padding:1px 7px;border-radius:3px;background:#1e2530;color:var(--acc);font-size:12px}
.tag.warn{background:#2a2318;color:var(--warn)}
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
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def load_people():
    people = {}
    for r in load_jsonl(LIGHT):
        cid = r.get("id")
        if cid:
            people[cid] = r
    return people


def machine_hits(text):
    """现行门禁口径实测（判据单源：从 evolve_citizen 直接 import）。"""
    try:
        import evolve_citizen as ev
    except Exception:
        return 0
    n = 1 if ev.has_event_code(text) else 0
    n += 1 if ev.CHINESE_TECH_RE.search(text or "") else 0
    for w in ev.TECH_WORD_RE.findall(text or ""):
        if w.lower() not in ev.RING_LATIN_WHITELIST:
            n += 1
            break
    return n


def main():
    rows = load_jsonl(PROPOSALS)
    people = load_people()
    today = date.today()

    rows.sort(key=lambda r: (r.get("created_at", ""), r.get("proposal_id", "")), reverse=True)
    dirty = {r.get("proposal_id"): machine_hits(r.get("text", "")) for r in rows}
    early = [r for r in rows if dirty.get(r.get("proposal_id"))]
    clean = [r for r in rows if not dirty.get(r.get("proposal_id"))]

    last_at = rows[0].get("created_at", "") if rows else ""
    gap_days = 0.0
    if last_at:
        try:
            gap_days = (datetime.now() - datetime.strptime(last_at, "%Y-%m-%d %H:%M")).total_seconds() / 86400.0
        except ValueError:
            gap_days = 0.0
    today_rows = [r for r in rows if str(r.get("created_at", "")).startswith(today.isoformat())]

    parts = []
    parts.append("<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
                 "<title>城市议会·提案志 | 超体宇宙城</title>"
                 "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                 f"<style>{CSS}</style></head><body><div class=\"wrap\">")
    parts.append("<h1>城市议会 · 提案志</h1>")
    parts.append("<p class=\"sub\">好奇位达标的叙事市民轮值出任议员，依托当日真实城市事件向城里提一条建议。"
                 f"每日上限 {PROPOSE_CAP} 条（珍稀律）。数据源 <code>cognition/proposals.jsonl</code>。</p>")

    parts.append("<div class=\"metrics\">")
    for big, small in [
        (str(len(rows)), "提案总数"),
        (str(len({r.get("citizen_id") for r in rows})), "出过议员的居民"),
        (str(len(today_rows)), "今日新增"),
        (("%.1f 天" % gap_days) if last_at else "—", "距最近一条"),
    ]:
        parts.append(f"<div class=\"m\"><b>{html.escape(big)}</b><span>{html.escape(small)}</span></div>")
    parts.append("</div>")

    if gap_days >= 2:
        parts.append(
            "<div class=\"note\"><b>供给实况</b>：提案台账最近一条是 "
            f"{html.escape(last_at or '—')}，距今 {gap_days:.1f} 天。根因＝<code>--propose</code> 是年轮批的"
            "附加旗标，而轮值批只调 <code>--batch</code>，开关长期无人按下（脚本本身可用）。"
            f"2026-11-13 已从源码侧改为默认开启（保留 <code>--no-propose</code> 逃生口，日上限 {PROPOSE_CAP} 不变），"
            "当日晚间批次起自动恢复出提案。账见 <code>tasks/TASKS.md</code> T-20261113-02。</div>")

    parts.append("<h2>提案名册</h2>")
    if not rows:
        parts.append("<p class=\"dim\">尚无提案记录。</p>")
    else:
        parts.append("<table><thead><tr><th>时间</th><th>议员</th><th>提案</th><th>咬合人设</th></tr></thead><tbody>")
        for r in rows:
            cid = r.get("citizen_id", "")
            p = people.get(cid, {})
            who = "·".join(x for x in [
                html.escape(cid),
                html.escape(p.get("name", "")),
                html.escape(DISTRICT_CN.get(p.get("district", ""), p.get("district", "") or "")),
                html.escape(p.get("profession", "") or ""),
            ] if x)
            n = dirty.get(r.get("proposal_id"), 0)
            if n:
                body = ("<span class=\"muted\">原文触现行门禁词（早期落账）——"
                        "按存量不回改口径此处只标注、不展示原文；原行见台账 jsonl。</span>")
            else:
                body = html.escape(r.get("text", ""))
            hit = "<span class=\"tag\">是</span>" if r.get("face_hit") else "<span class=\"dim\">否</span>"
            parts.append("<tr>"
                         f"<td class=\"id\">{html.escape(str(r.get('created_at', '')))}</td>"
                         f"<td>{who}</td><td>{body}</td><td>{hit}</td></tr>")
        parts.append("</tbody></table>")

    parts.append("<h2>口径</h2><ul class=\"dim\">")
    parts.append(f"<li>展示行 {len(clean)} 条（过现行机读串判据）；标注行 {len(early)} 条（早期落账，原文不回改）。</li>")
    parts.append("<li>「咬合人设」＝提案文本与本人卡面人设域有 4 字以上重合（契约 §一 face_hit 标记）。</li>")
    parts.append("<li>本页只读罗列，不改写提案文本、不补写未发生的提案。</li>")
    parts.append("</ul>")

    parts.append(f"<footer>数据源：cognition/proposals.jsonl（{len(rows)} 行）· "
                 f"数据截止：{html.escape(last_at or '—')} · BigLife 城市议会</footer>")
    parts.append("</div></body></html>")

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts))
    print("wrote %s (%d proposals, %d clean, %d early, gap=%.1fd)"
          % (os.path.relpath(OUT, ROOT), len(rows), len(clean), len(early), gap_days))


if __name__ == "__main__":
    main()
