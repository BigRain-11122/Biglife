# -*- coding: utf-8 -*-
"""年轮拒稿归因面板（确定性·零 LLM·幂等）

读 state/ring-refusals.jsonl（Tools/evolve_citizen.py L2038 _note_refusal 写出，
append-only）产出 census/export/city-ring-refusals.html + city-ring-refusals.json：

  1) 总账 KPI：拒稿总数 / 今日 / 覆盖天数 / 日均
  2) 闸组合分布：哪些闸同时在拒（回答「真实拒稿源是族配额还是精确去重」）
  3) 开口族分布 + 同一开口重复次数榜（精确去重面实锤）
  4) 逐日 / 逐小时产出（看得见闸是白天紧还是夜里紧）
  5) 最近 20 条拒稿原文（人读面）

为什么单开这一面：拒稿台账自 2026-11-15 接线后只有 jsonl，没有任何可见面；
T-20261115-04「年轮同质化」的换靶步（族配额 vs 精确去重谁是真实拒稿源）
此前只能人肉翻台账。本面把两个分母并列，使归因可看。

口径注：台账只记被拒席（不记通过席），故本面回答「为什么被拒」，不回答
「拒稿率」——分母在 evolve-cursor / 批日志里，不在此处混算。

用法: python -X utf8 Tools/build_ring_refusals.py
注意：直接跑本脚本会覆盖页面、连带抹掉 build_export_index 注入的导航条
（<!--bl-nav:index-->）——改完页面后必须紧随跑一次 build_export_index.py。
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
SRC = os.path.join(ROOT, "state", "ring-refusals.jsonl")
OUT_HTML = os.path.join(EXP, "city-ring-refusals.html")
OUT_JSON = os.path.join(EXP, "city-ring-refusals.json")
RECENT = 20

CSS = """
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e;--red:#e5605c;--grn:#3fb950}
*{box-sizing:border-box}
body{margin:0;padding:28px 20px 60px;background:var(--bg);color:var(--fg);font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:28px 0 10px;color:var(--acc)}
.sub{color:var(--dim);font-size:12px;margin-bottom:18px}
.kpi{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 4px}
.kpi div{background:#161b22;border:1px solid var(--line);border-radius:8px;padding:10px 14px;min-width:112px}
.kpi b{display:block;font-size:20px}.kpi span{color:var(--dim);font-size:11px}
table{border-collapse:collapse;width:100%;margin-top:6px;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px}
.bar{background:#21262d;border-radius:3px;height:9px;min-width:1px;display:inline-block;vertical-align:middle}
.hot{color:var(--red)}.ok{color:var(--grn)}.warm{color:var(--warm)}
.mono{font-family:Consolas,monospace;font-size:12px;color:var(--dim)}
.empty{color:var(--dim);padding:12px 0}
"""


def load():
    rows = []
    if not os.path.exists(SRC):
        return rows
    with open(SRC, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def day_of(ts):
    return (ts or "")[:10]


def bars(count, total, width=120):
    if not total:
        return ""
    w = max(1, int(round(width * count / total)))
    return '<span class="bar" style="width:%dpx"></span>' % w


def main():
    rows = load()
    today = datetime.date.today().isoformat()
    days = sorted({day_of(r.get("ts")) for r in rows if day_of(r.get("ts"))})
    today_rows = [r for r in rows if day_of(r.get("ts")) == today]

    combo = collections.Counter("+".join(sorted(r.get("gate") or [])) for r in rows)
    single = collections.Counter()
    for r in rows:
        for g in (r.get("gate") or []):
            single[g] += 1
    family = collections.Counter(r.get("family") or "(none)" for r in rows)
    opening = collections.Counter((r.get("opening12") or "").strip() for r in rows)
    opening.pop("", None)
    by_day = collections.Counter(day_of(r.get("ts")) for r in rows)
    by_hour = collections.Counter((r.get("ts") or "")[11:13] for r in rows)

    # R3201 (2026-11-16): T-20261115-05 / R3115 的回归守卫面。
    # R3200 用「11-15+11-16 两日 n=80」得出「精确去重占 84% 才是主因」——但 11-15
    # 的 55 条里有 15 条来自同一居民 C-03117 同一句（16:59→18:54 每 ~10 分钟一次），
    # 那是顺延修复上线**之前**的重写循环，不是全局分布问题；11-16 实读 25 条分属
    # 25 位居民、零重复＝修复已生效。故此处按日分解重试结构：同一日同一 cid 被拒
    # >1 次＝重试未被熔断；同日同 cid 同 opening12 >=3 次＝修复前的 livelock（每轮
    # 白烧一次 LLM 调用）。只读统计，不改任何闸阈值/窗口/族表（T-20261115-04 约束）。
    per_day_cid = {}
    per_day_cidop = {}
    for r in rows:
        d = day_of(r.get("ts"))
        if not d:
            continue
        per_day_cid.setdefault(d, collections.Counter())[r.get("cid") or ""] += 1
        per_day_cidop.setdefault(d, collections.Counter())[
            (r.get("cid") or "", (r.get("opening12") or "").strip())] += 1
    livelock = {}
    for d in sorted(per_day_cid):
        cnt = per_day_cid[d]
        rep = {k: v for k, v in cnt.items() if v > 1}
        stuck = {k: v for k, v in per_day_cidop.get(d, {}).items() if v >= 3}
        livelock[d] = {
            "rows": sum(cnt.values()),
            "distinct_citizens": len(cnt),
            "repeated_citizens": len(rep),
            "max_repeats": max(rep.values()) if rep else 1,
            "stuck_same_opening": ["%s|%s x%d" % (k[0], k[1], v)
                                   for k, v in sorted(stuck.items(),
                                                      key=lambda x: -x[1])],
            "wasted_calls": sum(v - 1 for v in rep.values()),
        }

    parts = []
    a = parts.append
    a("<!doctype html><html lang=zh-CN><meta charset=utf-8>")
    a("<title>年轮拒稿归因</title><style>%s</style>" % CSS)
    a("<h1>年轮拒稿归因</h1>")
    a('<div class="sub">数据源 state/ring-refusals.jsonl（append-only·只记被拒席）·'
      '生成 %s·零 LLM 确定性面</div>' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))

    a('<div class="kpi">')
    for label, val in (
        ("拒稿总数", len(rows)),
        ("今日", len(today_rows)),
        ("覆盖天数", len(days)),
        ("日均", round(len(rows) / len(days), 1) if days else 0),
        ("涉及开口族", len(family)),
        ("闸种类", len(single)),
    ):
        a('<div><b>%s</b><span>%s</span></div>' % (val, label))
    a("</div>")

    if not rows:
        a('<div class="empty">台账为空：尚无拒稿记录（或 evolve 未在写）。</div>')
    else:
        # 闸组合
        a("<h2>闸组合分布（谁在拒）</h2>")
        a("<table><tr><th>闸组合</th><th>次数</th><th></th><th>占比</th></tr>")
        for k, v in combo.most_common():
            a("<tr><td class=mono>%s</td><td>%d</td><td>%s</td><td>%.0f%%</td></tr>"
              % (html.escape(k or "(unknown)"), v, bars(v, len(rows)), 100.0 * v / len(rows)))
        a("</table>")

        a("<h2>单闸命中次数（并集口径）</h2>")
        a("<table><tr><th>闸</th><th>命中</th><th></th><th>占拒稿席</th></tr>")
        for k, v in single.most_common():
            a("<tr><td class=mono>%s</td><td>%d</td><td>%s</td><td>%.0f%%</td></tr>"
              % (html.escape(k), v, bars(v, len(rows)), 100.0 * v / len(rows)))
        a("</table>")

        # 开口族
        a("<h2>开口族分布（被拒的句子长什么样）</h2>")
        a("<table><tr><th>族</th><th>次数</th><th></th><th>占拒稿</th></tr>")
        for k, v in family.most_common():
            cls = " class=hot" if "HAND" in k or "TIME" in k else ""
            a("<tr><td%s>%s</td><td>%d</td><td>%s</td><td>%.0f%%</td></tr>"
              % (cls, html.escape(k), v, bars(v, len(rows)), 100.0 * v / len(rows)))
        a("</table>")

        # 精确重复开口榜
        a("<h2>同一开口重复次数榜（精确去重面实锤）</h2>")
        dup = [(k, v) for k, v in opening.most_common(15) if v > 1]
        if dup:
            a("<table><tr><th>开口前 12 字</th><th>被拒次数</th></tr>")
            for k, v in dup:
                a("<tr><td>%s</td><td class=warm>%d</td></tr>" % (html.escape(k), v))
            a("</table>")
        else:
            a('<div class="empty">无重复开口（%d 条互不相同）——精确去重面未构成主因。</div>'
              % len(opening))

        # 逐日
        a("<h2>逐日</h2>")
        a("<table><tr><th>日期</th><th>拒稿</th><th></th></tr>")
        for k in reversed(days[-14:]):
            a("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (k, by_day[k], bars(by_day[k], max(by_day.values()))))
        a("</table>")

        # 逐小时
        a("<h2>逐小时（24h·闸在哪个时段更紧）</h2>")
        a("<table><tr><th>时</th><th>拒稿</th><th></th></tr>")
        for h in range(24):
            k = "%02d" % h
            if by_hour.get(k):
                a("<tr><td>%s</td><td>%d</td><td>%s</td></tr>"
                  % (k, by_hour[k], bars(by_hour[k], max(by_hour.values()) if by_hour else 1)))
        a("</table>")

        # 重试熔断面（R3115 回归守卫）
        a("<h2>重试熔断面（R3115 拒稿顺延 +1d 是否生效）</h2>")
        a('<div class="sub">判据：同一日同一居民被拒 &gt;1 次＝重试未被熔断；'
          '同日同居民同开口 ≥3 次＝修复前的重写循环（每轮白烧一次 LLM 调用）。</div>')
        a("<table><tr><th>日期</th><th>拒稿</th><th>涉及居民</th><th>重复居民</th>"
          "<th>最大重试</th><th>白烧调用</th><th>判定</th></tr>")
        for _d in sorted(livelock)[-14:]:
            _v = livelock[_d]
            if _v["repeated_citizens"] == 0:
                _tag = "PASS·已熔断"
            elif _v["max_repeats"] >= 3:
                _tag = "FAIL·重写循环"
            else:
                _tag = "WARN·有重试"
            a("<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td>"
              "<td>%d</td><td>%s</td></tr>"
              % (_d, _v["rows"], _v["distinct_citizens"], _v["repeated_citizens"],
                 _v["max_repeats"], _v["wasted_calls"], _tag))
        a("</table>")
        if livelock:
            _last = sorted(livelock)[-1]
            if livelock[_last]["repeated_citizens"] == 0:
                a('<div class="empty">最近一日 %s：%d 条拒稿分属 %d 位居民，零重复——'
                  'R3115 顺延修复生效。</div>'
                  % (_last, livelock[_last]["rows"],
                     livelock[_last]["distinct_citizens"]))
            else:
                a('<div class="empty">最近一日 %s：%d 条拒稿中 %d 位居民被拒 >1 次'
                  '（最大 %d 次）——检查顺延是否被绕过。</div>'
                  % (_last, livelock[_last]["rows"],
                     livelock[_last]["repeated_citizens"],
                     livelock[_last]["max_repeats"]))

        # 最近
        a("<h2>最近 %d 条拒稿原文</h2>" % RECENT)
        a("<table><tr><th>时间</th><th>居民</th><th>闸</th><th>族</th><th>开口</th></tr>")
        for r in rows[-RECENT:][::-1]:
            a("<tr><td class=mono>%s</td><td class=mono>%s</td><td class=mono>%s</td>"
              "<td>%s</td><td>%s</td></tr>")
        a("</table>")

    a("</html>")

    # 最近行单独重写（避免格式化串串味）
    if rows:
        body = "".join(parts)
        start = body.rfind("<table><tr><th>时间</th>")
        end = body.rfind("</table>")
        tbl = ["<table><tr><th>时间</th><th>居民</th><th>闸</th><th>族</th><th>开口</th></tr>"]
        for r in rows[-RECENT:][::-1]:
            tbl.append("<tr><td class=mono>%s</td><td class=mono>%s</td><td class=mono>%s</td><td>%s</td><td>%s</td></tr>" % (
                html.escape(str(r.get("ts") or "")),
                html.escape(str(r.get("cid") or "")),
                html.escape("+".join(r.get("gate") or [])),
                html.escape(str(r.get("family") or "")),
                html.escape(str(r.get("opening12") or "")),
            ))
        tbl.append("</table>")
        body = body[:start] + "".join(tbl) + body[end + len("</table>"):]
    else:
        body = "".join(parts)

    os.makedirs(EXP, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(body)

    summary = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(rows),
        "today": len(today_rows),
        "days": days,
        "gate_combos": combo.most_common(),
        "gates": single.most_common(),
        "families": family.most_common(),
        "repeated_openings": [(k, v) for k, v in opening.most_common(20) if v > 1],
        "by_day": dict(sorted(by_day.items())),
        "retry_livelock": livelock,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    print("ring-refusals: total=%d today=%d days=%d gates=%d families=%d"
          % (len(rows), len(today_rows), len(days), len(single), len(family)))
    print("wrote: %s / %s" % (os.path.relpath(OUT_HTML, ROOT), os.path.relpath(OUT_JSON, ROOT)))


if __name__ == "__main__":
    main()
