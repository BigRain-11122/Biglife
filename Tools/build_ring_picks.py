# -*- coding: utf-8 -*-
"""今日年轮精选读本：把当天新写的年轮按可解释的质量信号排序，输出一页可读面。

确定性零 LLM：只用卡面事实（城区/职业/钩子/年轮原文）与字符 3-gram 相似度。
质量信号（逐条可解释，写在每条后面，不做无根据评分）：
  - short  文本 < 20 字（信息量不足）
  - sim    与同日另一条年轮 3-gram Jaccard >= 0.60（批量同质）
  - dup    与该居民此前年轮几乎重复（自重复，年轮没长）
排序分 = 100 - 45*short - 35*sim - 40*dup + 10*(24<=长度<=56)
读者面：每城区取分最高 6 条为「今日可读」，全城分最低 12 条列「该重写」，
两条清单都指向居民卡，便于回查到谁。
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "census", "export", "city-ring-picks.html")
STATE_OUT = os.path.join(ROOT, "state", "ring-picks-latest.json")

CARD_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})\s*[「“](.+?)[」”]\s*(\[锚\].*)?$")
DISTRICTS = {
    "GM": "GAME 城",
    "MD": "MEDIA 城",
    "NS": "NETSEC 城",
    "OR": "OPEN 城",
    "QT": "QUANT 城",
    "RV": "REVIEW 城",
}


def _field(text: str, name: str):
    m = re.search(r"\*\*%s\*\*\s*(.+)" % re.escape(name), text)
    return m.group(1).strip() if m else ""


def _grams(s: str) -> set:
    s = re.sub(r"[\s，。、；：「」“”（）!！?？…·]", "", s)
    if len(s) < 3:
        return {s} if s else set()
    return {s[i : i + 3] for i in range(len(s) - 2)}


def _jac(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_cards():
    cards = []
    for path in glob.glob(os.path.join(ROOT, "census", "registry", "*", "C-*.md")):
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        cid = os.path.basename(path)[:-3]
        dist_dir = os.path.basename(os.path.dirname(path))
        first = text.split("\n", 1)[0].strip()
        m_name = re.match(r"#\s*C-\d+\s*·\s*(.+)", first)
        rings = []
        for line in text.splitlines():
            m = CARD_RE.match(line.strip())
            if m:
                rings.append((m.group(1), m.group(2).strip()))
        cards.append(
            {
                "id": cid,
                "card": os.path.relpath(path, ROOT).replace("\\", "/"),
                "name": m_name.group(1).strip() if m_name else cid,
                "person": m_name.group(1).strip() if m_name else cid,
                "district": DISTRICTS.get(dist_dir, dist_dir),
                "occupation": _field(text, "职业").split("：")[0][:26],
                "hook": _field(text, "钩子")[:60],
                "rings": rings,
            }
        )
    return cards


def build(target_day: str | None = None):
    cards = load_cards()
    per_day = {}
    for c in cards:
        for d, t in c["rings"]:
            per_day[d] = per_day.get(d, 0) + 1
    day = target_day or max(per_day) if per_day else date.today().isoformat()

    items = []
    for c in cards:
        items_rings = [(d, t) for d, t in c["rings"] if d == day]
        if not items_rings:
            continue
        prior = [t for d, t in c["rings"] if d != day]
        for d, t in items_rings:
            items.append(
                {
                    "id": c["id"],
                    "card": c["card"],
                    "name": c["person"],
                    "district": c["district"],
                    "occupation": c["occupation"],
                    "hook": c["hook"],
                    "date": d,
                    "text": t,
                    "prior": prior,
                }
            )

    if not items:
        return {"day": day, "items": [], "per_day": per_day}

    grams = [_grams(i["text"]) for i in items]
    for i, it in enumerate(items):
        flags = []
        if len(it["text"]) < 20:
            flags.append("short")
        best = 0.0
        for j, other in enumerate(items):
            if j == i:
                continue
            s = _jac(grams[i], grams[j])
            if s > best:
                best = s
        it["sim"] = round(best, 3)
        if best >= 0.60:
            flags.append("sim")
        dup = max((_jac(grams[i], _grams(p)) for p in it["prior"]), default=0.0)
        it["dup"] = round(dup, 3)
        if dup >= 0.85:
            flags.append("dup")
        # 相遇句是固定句式，读起来最像模板，不该占到「可读」前排
        is_meet = bool(re.match(r"^与\s*C-\d+\s*相遇", it["text"]))
        if is_meet:
            flags.append("meet")
        it["flags"] = flags
        score = 100.0
        if "short" in flags:
            score -= 45
        if "sim" in flags:
            score -= 35
        if "dup" in flags:
            score -= 40
        if is_meet:
            score -= 30
        if 24 <= len(it["text"]) <= 56:
            score += 10
        # 具体度：有数字、有城市里的具体物/地标 —— 越具体越像一天里真发生的事
        # 编号（C-08226）不算具体度，只认正文里的真数字
        body = re.sub(r"C-\d+", "", it["text"])
        concrete = 0
        if re.search(r"\d", body):
            concrete += 1
        if re.search(r"[楼街巷桥站店摊灯雨风车河岸院窗茶饭鞋伞猫狗]", body):
            concrete += 1
        it["concrete"] = concrete
        score += 6 * concrete
        it["score"] = round(score, 1)
    return {"day": day, "items": items, "per_day": per_day}


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def render(data) -> str:
    day, items = data["day"], data["items"]
    per_day = data["per_day"]
    total = len(items)
    by_district: dict[str, list] = {}
    for it in items:
        by_district.setdefault(it["district"], []).append(it)
    picks = []
    for dist, lst in sorted(by_district.items()):
        lst.sort(key=lambda x: (-x["score"], x["id"]))
        picks.extend(lst[:6])
    picks.sort(key=lambda x: (-x["score"], x["district"], x["id"]))
    worst = sorted(items, key=lambda x: (x["score"], len(x["text"]), x["id"]))[:12]
    flagged_n = sum(1 for i in items if i["flags"])

    flag_zh = {"short": "偏短", "sim": "同质", "dup": "自重复", "meet": "相遇模板"}
    bad = sum(1 for i in items if i["flags"])

    rows = []
    for it in picks:
        tags = "".join("<em>%s</em>" % flag_zh.get(f, f) for f in it["flags"])
        rows.append(
            "<article><div class='meta'><b>%s</b> · %s · %s<span class='sc'>%s</span></div>"
            "<p>「%s」</p><div class='foot'><span>%s</span><span>%s</span></div></article>"
            % (
                esc(it["name"]),
                esc(it["district"]),
                esc(it["occupation"]),
                tags,
                esc(it["text"]),
                esc(it["hook"]),
                esc(it["id"]),
            )
        )

    badrows = []
    for it in worst:
        flags = "、".join(flag_zh.get(f, f) for f in it["flags"]) or "无标记"
        badrows.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s 字 / %s</td><td>%s</td></tr>"
            % (esc(it["id"]), esc(it["name"]), esc(it["district"]), len(it["text"]), flags, esc(it["text"]))
        )
    if flagged_n:
        watch_title = "末位 12 条 · 本日带标记 %d 条（相遇模板属可选优化，不算缺陷）" % flagged_n
    else:
        watch_title = "本日零质量标记 · 以下为最短 12 条（仅作观察，不排队）"

    daylist = "".join(
        "<li>%s · %d 圈</li>" % (d, n) for d, n in sorted(per_day.items())[-5:]
    )

    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>今日年轮精选 · BigLife %s</title>
<style>
:root{--bg:#12141a;--fg:#e6e6e6;--dim:#8d94a3;--line:#262a33;--accent:#7fb0d8;--warn:#d89a7f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.8 "Noto Sans SC","Microsoft YaHei",sans-serif}
header{padding:28px 20px 12px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:20px;font-weight:600}
.sub{color:var(--dim);font-size:13px}
.kpis{display:flex;gap:14px;flex-wrap:wrap;padding:16px 20px;border-bottom:1px solid var(--line)}
.kpi{border:1px solid var(--line);border-radius:6px;padding:10px 14px;background:#171a21;min-width:140px}
.kpi b{display:block;font-size:22px;font-weight:600}
.kpi span{color:var(--dim);font-size:12px}
h2.sec{padding:20px 20px 6px;font-size:16px;margin:0}
.wrap{padding:6px 20px 30px;display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(420px,1fr))}
article{border:1px solid var(--line);border-radius:6px;padding:12px 14px;background:#171a21}
article p{margin:8px 0;font-size:15px}
.meta{color:var(--dim);font-size:12.5px}
.meta b{color:var(--fg);font-weight:600}
.meta em{color:var(--warn);font-style:normal;margin-left:6px;border:1px solid #3a302b;border-radius:4px;padding:0 4px;font-size:11px}
.sc{float:right;color:var(--accent)}
.foot{color:var(--dim);font-size:12px;display:flex;justify-content:space-between;gap:10px}
.foot a{color:var(--accent);text-decoration:none}
table{border-collapse:collapse;margin:0 20px 24px;font-size:13.5px}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:500}
.note{padding:0 20px 18px;color:var(--dim);font-size:12.5px}
.note ul{margin:6px 0 0 18px;padding:0}
</style></head><body>
<header><h1>今日年轮精选 · %s</h1>
<div class="sub">当日新写年轮按可解释质量信号排序：每城区取 6 条可读 + 末尾 12 条观察位。确定性生成，零 LLM。</div></header>
<div class="kpis">
<div class="kpi"><b>%d</b><span>当日年轮</span></div>
<div class="kpi"><b>%d</b><span>带质量标记</span></div>
<div class="kpi"><b>%d</b><span>城区覆盖</span></div>
<div class="kpi"><b>%d</b><span>本页精选</span></div>
</div>
<h2 class="sec">可读的 %d 条</h2>
<div class="wrap">%s</div>
<h2 class="sec">%s</h2>
<table><tr><th>编号</th><th>居民</th><th>城区</th><th>长度 / 标记</th><th>原文</th></tr>%s</table>
<div class="note">评分口径：100 起，偏短 −45、与同日他人同质 −35、与自己旧圈重复 −40、相遇句式 −30、长度 24–56 字 +10；具体度（正文含数字、含城市具体物/地标）各 +6（编号不计）。标记为提示不是判决；标记者由 19:00 年轮批次或相遇轮按需处置（年轮改写必带 [锚] 注脚）。
<ul>%s</ul></div>
</body></html>
""" % (
        esc(day),
        esc(day),
        total,
        bad,
        len(by_district),
        len(picks),
        len(picks),
        "".join(rows),
        watch_title,
        "".join(badrows),
        daylist,
    )


def main():
    data = build()
    html_text = render(data)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html_text)
    summary = {
        "day": data["day"],
        "rings": len(data["items"]),
        "flagged": sum(1 for i in data["items"] if i["flags"]),
        "districts": len({i["district"] for i in data["items"]}),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    os.makedirs(os.path.dirname(STATE_OUT), exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(json.dumps(summary, ensure_ascii=False))
    print("OUT", os.path.relpath(OUT, ROOT), os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()