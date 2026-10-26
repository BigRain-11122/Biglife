# -*- coding: utf-8 -*-
"""城市相遇编年史生成器（确定性·零 LLM·幂等）

扫 census/registry/*/*.md 的年轮行，抽取「与 C-xxxxx 相遇：…」记录，
按日期编排成双向对读页 census/export/city-meets.html。

与 city-relations.html 的「相逢录」区别：那边只看 recent_ring（每人最近一圈、
单向近 30 条），本页是全库全量相遇、并被成对拼成一幕。

用法: python -X utf8 Tools/build_city_meets.py
"""
import collections
import datetime
import glob
import html
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
OUT = os.path.join(EXP, "city-meets.html")

MEET_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「与 (C-\d+) 相遇：(.+?)」", re.M)
HEAD_RE = re.compile(r"^# (C-\d+) · (.+)$", re.M)
DISTRICT_CN = {
    "GM": "中央市集",
    "QT": "低语巷",
    "MD": "机房区",
    "NS": "北槐街区",
    "OR": "旧站台",
    "RV": "河岸",
}


def esc(s):
    return html.escape(str(s), quote=True)


def load_cards():
    people = {}
    meets = []  # (date, from_id, to_id, text)
    for p in glob.glob(os.path.join(ROOT, "census", "registry", "*", "*.md")):
        text = io.open(p, encoding="utf-8", errors="replace").read()
        hid = HEAD_RE.search(text)
        cid = hid.group(1) if hid else os.path.basename(p)[:-3]
        name = hid.group(2).strip() if hid else cid
        district = os.path.basename(os.path.dirname(p))
        prof = ""
        mprof = re.search(r"^\*\*职业\*\* (.+)$", text, re.M)
        if mprof:
            prof = mprof.group(1).strip()
        people[cid] = {
            "name": name,
            "district": district,
            "district_cn": DISTRICT_CN.get(district, district),
            "profession": prof,
        }
        for date, other, line in MEET_RE.findall(text):
            meets.append((date, cid, other, line.strip()))
    return people, meets


def pair_up(meets):
    """同日期 + 同二人 → 一幕；两侧都留痕则成对。"""
    scenes = collections.OrderedDict()
    for date, a, b, line in meets:
        key = (date, tuple(sorted((a, b))))
        side = scenes.setdefault(key, {"date": date, "pair": key[1], "sides": {}})
        # 同一人同日同对象可能有多次留痕，保留首条即可（幂等稳定）
        side["sides"].setdefault(a, line)
    return list(scenes.values())


def person_html(pid, people):
    p = people.get(pid) or {}
    name = p.get("name", pid)
    d = p.get("district_cn", "—")
    prof = p.get("profession", "")
    return (
        '<div class="who"><b>%s</b><span class="tag">%s</span>%s</div>'
        % (esc(name), esc(d), '<span class="prof">%s</span>' % esc(prof) if prof else "")
    )


def main():
    people, meets = load_cards()
    scenes = pair_up(meets)
    full = [s for s in scenes if len(s["sides"]) == 2]
    half = [s for s in scenes if len(s["sides"]) == 1]
    cross = [
        s
        for s in scenes
        if len({(people.get(s["pair"][0]) or {}).get("district"),
                (people.get(s["pair"][1]) or {}).get("district")}) == 2
    ]
    by_date = collections.OrderedDict()
    for s in scenes:
        by_date.setdefault(s["date"], []).append(s)
    dates = sorted(by_date, reverse=True)

    hot = collections.Counter()
    for s in scenes:
        for pid in s["pair"]:
            hot[pid] += 1

    blocks = []
    for date in dates:
        items = []
        for s in by_date[date]:
            a, b = s["pair"]
            rows = []
            for pid in (a, b):
                line = s["sides"].get(pid)
                if line:
                    rows.append(
                        '<div class="side">%s<q>%s</q></div>' % (person_html(pid, people), esc(line))
                    )
                else:
                    rows.append(
                        '<div class="side mute">%s<q class="none">（这一侧没有留痕）</q></div>'
                        % person_html(pid, people)
                    )
            items.append('<div class="scene">%s</div>' % "".join(rows))
        blocks.append(
            '<section><h2>%s<span class="cnt">%d 幕</span></h2>%s</section>'
            % (esc(date), len(items), "".join(items))
        )

    hot_rows = "".join(
        '<div class="row"><span class="lab">%s · %s</span><span class="num">%d 次</span></div>'
        % (esc((people.get(pid) or {}).get("name", pid)), esc(pid), cnt)
        for pid, cnt in hot.most_common(10)
    )

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>城市相遇编年史</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0f1113;--fg:#e7e3dc;--mut:#8d8a84;--line:#26292d;--acc:#c8a165}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.75 "PingFang SC","Microsoft YaHei",system-ui,sans-serif}
header{padding:34px 24px 18px;border-bottom:1px solid var(--line)}
h1{margin:0 0 6px;font-size:26px;letter-spacing:.06em;font-weight:600}
.sub{color:var(--mut);font-size:13px}
.stats{display:flex;flex-wrap:wrap;gap:10px;padding:18px 24px}
.card{flex:1 1 132px;border:1px solid var(--line);border-radius:8px;padding:12px 14px;background:#14171a}
.card .k{color:var(--mut);font-size:12px}
.card .v{font-size:22px;color:var(--acc);font-weight:600;margin-top:2px}
main{padding:8px 24px 60px;max-width:900px;margin:0 auto}
section{margin:26px 0;border-top:1px solid var(--line);padding-top:14px}
h2{font-size:16px;color:var(--acc);font-weight:600;margin:0 0 12px}
h2 .cnt{color:var(--mut);font-size:12px;font-weight:400;margin-left:10px}
.scene{border:1px solid var(--line);border-left:3px solid #3a4048;border-radius:6px;
padding:10px 14px;margin:0 0 10px;background:#13161a}
.side{padding:4px 0}
.side + .side{border-top:1px dashed #23272c}
.who{font-size:13px;color:#cfcabf}
.who b{color:var(--fg);margin-right:6px}
.tag{font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:3px;padding:0 5px;margin-right:6px}
.prof{color:var(--mut);font-size:12px}
q{display:block;quotes:none;margin:3px 0 0;color:#ded9d0}
.none{color:#5f636a;font-style:italic}
.mute{opacity:.62}
.hot{border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin-bottom:26px}
.hot h3{margin:0 0 8px;font-size:14px;color:var(--acc)}
.row{display:flex;justify-content:space-between;font-size:13px;padding:3px 0}
.row .lab{color:#cfcabf}.row .num{color:var(--mut)}
footer{color:#54585e;font-size:12px;text-align:center;padding:24px}
</style></head><body>
<header>
<h1>城市相遇编年史</h1>
<div class="sub">全库「与 X 相遇」留痕按日编排 · 同一幕双向对读 · 数据源 census/registry · 生成 %s</div>
</header>
<div class="stats">
<div class="card"><div class="k">相遇留痕</div><div class="v">%d</div></div>
<div class="card"><div class="k">成幕（双向齐）</div><div class="v">%d</div></div>
<div class="card"><div class="k">单面留痕</div><div class="v">%d</div></div>
<div class="card"><div class="k">涉事居民</div><div class="v">%d</div></div>
<div class="card"><div class="k">跨城区幕</div><div class="v">%d</div></div>
</div>
<main>
<div class="hot"><h3>相遇最多的居民</h3>%s</div>
%s
</main>
<footer>BigLife · 确定性管线（零 LLM）· 每次生成内容由 registry 唯一决定</footer>
</body></html>
""" % (
        esc(stamp),
        len(meets),
        len(full),
        len(half),
        len(people),
        len(cross),
        hot_rows,
        "".join(blocks),
    )

    io.open(OUT, "w", encoding="utf-8", newline="\n").write(page)
    print(
        "city-meets: meets=%d scenes=%d full=%d half=%d dates=%d people=%d bytes=%d"
        % (len(meets), len(scenes), len(full), len(half), len(dates), len(people), len(page.encode("utf-8")))
    )


if __name__ == "__main__":
    main()