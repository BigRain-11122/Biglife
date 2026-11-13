# -*- coding: utf-8 -*-
"""年轮开头族仪表（确定性·零 LLM·幂等）。

读 census/registry 的年轮行，产出 census/export/city-ring-openings.html：
  1) KPI：近 14 生产日总环 / 当日环数 / 当前应禁族 / 未归族占比
  2) 逐日表：总环、各族计数与占比、越线标红、未归族占比
  3) 全期 top 开头句式（人数 + 所属族），回应「重复/品质」关切
  4) 口径说明（前 12 字、8 字下限、min_denom=8、quota=25%）

为什么要单开这一面：T-20261112-04 验收线（开口族 >25% 拒稿）此前只有 CLI
读数（ring_open_family.py --check），R2781/R2783 两轮归因全在终端里，CEO
在页面上看不到「今天哪些族越线、越多少、哪些句式在重复」。city-ring-trend
管缺陷率走势、city-ring-quality 管质量分布，都不给族归属明细。

用法: python -X utf8 Tools/build_ring_openings.py
注意：直接跑本脚本会覆盖页面、连带抹掉 build_export_index 注入的导航条
（<!--bl-nav:index-->）——改完页面必须随之跑 build_export_index.py，
否则该页丢失「回到总目录」入口（正常轮内走 round_daily --run 时索引层自动补）。
"""
import collections
import datetime
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
OUT_HTML = os.path.join(EXP, "city-ring-openings.html")
DAYS = 14
TOP_N = 20
UNC_TOP = 12  # 当日未归族实文样本条数（盲区可读面·R2792）

sys.path.insert(0, os.path.join(ROOT, "Tools"))
import ring_open_family as rof  # noqa: E402

CSS = """
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--line:#21262d;--acc:#4f9cf9;--warm:#f0a35e;--red:#e5605c;--ok:#3fb950}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:22px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--dim);font-size:12px;margin-bottom:28px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
.kpi{background:#161b22;border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.2}
.kpi span{color:var(--dim);font-size:12px}
.kpi.warn b{color:var(--warm)}
.kpi.bad b{color:var(--red)}
.kpi.good b{color:var(--ok)}
section{margin-bottom:28px}
h2{font-size:15px;color:var(--dim);font-weight:600;letter-spacing:.4px;margin:0 0 12px;text-transform:uppercase}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px}
td{font-variant-numeric:tabular-nums}
td.over{color:var(--red);font-weight:600}
td.blank{color:var(--dim)}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid var(--line)}
.pill.ban{border-color:#5c2b2a;background:#2a1716;color:#f08b87}
.pill.ok{border-color:#1f4429;background:#132218;color:#6fcf86}
.bar{display:inline-block;height:6px;border-radius:3px;background:#3d7dd6;vertical-align:middle;margin-right:6px}
.bar.hot{background:#c9762f}
.bar.cold{background:#a13c39}
.note{color:var(--dim);font-size:12.5px;line-height:1.8;margin:10px 0 0}
.note b{color:var(--fg);font-weight:600}
"""

RING_RE = re.compile(r"- (\d{4}-\d{2}-\d{2}) 「([^」]{8,})」")


def read_rings(registry=None):
    """扫 registry → [(day, body)]。与 ring_open_family 同正则同 8 字下限。"""
    root = registry or rof.REGISTRY
    rows = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            rows.extend(RING_RE.findall(s))
    return rows


def build(rows, today=None):
    today = today or datetime.date.today().isoformat()
    by_day = collections.OrderedDict()
    openings = collections.Counter()
    for day, body in rows:
        if day > today:
            continue
        by_day.setdefault(day, []).append(body)
        openings[rof.norm(body)] += 1

    days = sorted(by_day)[-DAYS:]
    daily = []
    for d in days:
        bodies = by_day[d]
        total = len(bodies)
        fam = collections.Counter()
        for b in bodies:
            f = rof.family_of(b)
            if f:
                fam[f] += 1
        over = rof.over_quota(total, dict(fam))
        unc_n, unc_pct = rof.unclassified(total, dict(fam))
        daily.append({
            "day": d, "total": total, "fam": dict(fam),
            "over": over, "unclassified": (unc_n, unc_pct),
        })

    ban = rof.ban_set_from_openings(dict(openings))
    total_all = sum(len(v) for v in by_day.values())
    # R2792: 当日未归族实文样本——盲区里到底写了什么，让读者/CEO 直接判「要不要立新族」
    unc_samples = []
    unc_day = days[-1] if days else "-"
    if days:
        c = collections.Counter()
        for b in by_day[days[-1]]:
            if rof.family_of(b) is None:
                c[rof.norm(b)] += 1
        unc_samples = c.most_common(UNC_TOP)
    return {
        "today": today,
        "daily": daily,
        "openings": openings,
        "ban": sorted(ban),
        "total_all": total_all,
        "total_window": sum(r["total"] for r in daily),
        "days": len(by_day),
        "unc_samples": unc_samples,
        "unc_day": unc_day,
    }


def pct(n, d):
    return 0.0 if not d else 100.0 * n / float(d)


def render(model):
    daily = model["daily"]
    last = daily[-1] if daily else {"total": 0, "fam": {}, "over": [], "unclassified": (0, 0.0)}
    unc_n, unc_pct = last["unclassified"]
    fam_names = set()
    for r in daily:
        fam_names.update(r["fam"].keys())
    fam_names = sorted(fam_names)

    kpis = [
        ("近 %d 生产日总环" % len(daily), "%d" % model["total_window"], ""),
        ("最近一日 %s" % (last.get("day", "-")), "%d" % last["total"], ""),
        ("当日越线族", "%d" % len(last["over"]), "bad" if last["over"] else "good"),
        ("全期应禁族", "%d" % len(model["ban"]), "bad" if model["ban"] else "good"),
        ("当日未归族", "%.1f%%" % unc_pct, "warn" if unc_pct > 15 else ""),
    ]

    kpi_html = "".join(
        '<div class="kpi %s"><b>%s</b><span>%s</span></div>' % (cls, html.escape(v), html.escape(k))
        for k, v, cls in kpis)

    head = ["日期", "总环"] + fam_names + ["未归族", "判定"]
    thead = "".join("<th>%s</th>" % html.escape(h) for h in head)

    trs = []
    for r in reversed(daily):
        tds = ['<td>%s</td>' % r["day"], '<td>%d</td>' % r["total"]]
        for f in fam_names:
            c = r["fam"].get(f, 0)
            if not c:
                tds.append('<td class="blank">-</td>')
                continue
            p = pct(c, r["total"])
            cls = "over" if f in r["over"] else ""
            w = max(3, min(46, int(p * 0.46)))
            barcls = "cold" if f in r["over"] else ""
            tds.append('<td class="%s"><i class="bar %s" style="width:%dpx"></i>%d · %.1f%%</td>'
                       % (cls, barcls, w, c, p))
        n, pc = r["unclassified"]
        tds.append('<td class="%s">%d · %.1f%%</td>' % ("over" if pc > 40 else "", n, pc))
        if r["over"]:
            tds.append('<td><span class="pill ban">越线 %s</span></td>' % html.escape("、".join(r["over"])))
        else:
            tds.append('<td><span class="pill ok">在配额内</span></td>')
        trs.append("<tr>%s</tr>" % "".join(tds))

    top_rows = []
    for op, c in model["openings"].most_common(TOP_N):
        f = rof.family_of(op)
        top_rows.append(
            "<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (
                html.escape(op), c,
                ('<span class="pill ban">%s</span>' % html.escape(f)) if f in model["ban"]
                else (html.escape(f) if f else '<span class="pill">未归族</span>')))
    top_html = "".join(top_rows)

    bans = "、".join(html.escape(b) for b in model["ban"]) or "无"
    day_over = "、".join(html.escape(b) for b in last["over"]) or "无"

    unc_rows = []
    for body, c in model.get("unc_samples", []):
        unc_rows.append("<tr><td>%s</td><td>%d</td></tr>" % (html.escape(body[:40]), c))
    unc_html = "".join(unc_rows) or '<tr><td colspan="2" class="blank">当日无未归族开头</td></tr>'

    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市·年轮开头族仪表</title>
<style>%s</style></head><body><div class="wrap">
<h1>城市·年轮开头族仪表</h1>
<div class="sub">生成于 %s · 口径＝年轮正文前 12 字 · 只读观测面 · 阈值 25%%（T-20261112-04）</div>
<div class="kpis">%s</div>

<section>
<h2>两个分母：当日越线 vs 全期禁集</h2>
<table><thead><tr><th>口径</th><th>分母</th><th>命中族</th></tr></thead><tbody>
<tr><td>当日（最近一日）</td><td>%d 环</td><td>%s</td></tr>
<tr><td>全期（%d 个生产日）</td><td>%d 环</td><td>%s</td></tr>
</tbody></table>
<div class="note">两者不等是<b>分母差异</b>造成的，不是判定矛盾：当日密集使用会把当日占比推过 25%%，而放进 %d 天全期后占比被摊薄。
所以「当日越线」与「全期禁集为空」可以同时成立——这正是 11-12～11-13 两轮归因读到的现象，
也是「闸开着却仍越线」这一新病症的可视佐证。当前禁集按全期台账生成，落环时按此集合避让。</div>
</section>

<section>
<h2>逐日族构成</h2>
<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>
<div class="note">条形长度为占比视觉刻度。判定列按当日 total 与 quota 现算（total&lt;8 不判，返回「在配额内」）。</div>
</section>

<section>
<h2>全期重复开头 Top %d</h2>
<table><thead><tr><th>开头 12 字</th><th>环数</th><th>所属族</th></tr></thead><tbody>%s</tbody></table>
<div class="note">同一开头被多名居民共用＝读者体感「像同一个人写的」，是 CEO 品质关切的可数面之一。</div>
</section>

<section>
<h2>%s 未归族实文 Top %d</h2>
<table><thead><tr><th>开头（前 40 字）</th><th>环数</th></tr></thead><tbody>%s</tbody></table>
<div class="note">这是盲区里真实写出的句子：不属任何已登记骨架族，因此既不被闸拦截、也不进族构成统计。
逐日读这一栏可判断「要不要立新族」——只有同一形状成规模复现（新生吸引子）才立族；
零散多形状混在一起属于正常语言多样性，硬立族会把闸改成误杀源（承 T-20261112-04 判据）。</div>
</section>

<section>
<h2>口径与边界</h2>
<div class="note">
<b>只读</b>：本页不改任何年轮、不改闸判定、不回写台账。<br>
<b>未归族</b>：不属任何已知骨架族的开头占比——新句式出现时会隐身，故单独列出做族表覆盖率的看守读数。<br>
<b>判定</b>：族占比 &gt; 25%% 即越线（当日环数 ≥ 8 才判）。越线只表示该句式开头密集，不等于语义违法。<br>
<b>已知边界</b>：族覆盖表由人工登记，新族需先立族再统计；未立族前的历史环不回改（承 R2760 判例）。
</div>
</section>
</div></body></html>
""" % (CSS, model["today"], kpi_html,
       last["total"], day_over, model["days"], model["total_all"], bans,
       model["days"], thead, "".join(trs), TOP_N, top_html,
       html.escape(model.get("unc_day", "-")), UNC_TOP, unc_html)


def main():
    rows = read_rings()
    model = build(rows)
    os.makedirs(EXP, exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(model))
    last = model["daily"][-1] if model["daily"] else None
    print("rings=%d days=%d today=%s over=%s unclassified=%.1f%% ban=%s"
          % (model["total_all"], model["days"],
             last["day"] if last else "-",
             (last["over"] if last else []),
             (last["unclassified"][1] if last else 0.0),
             model["ban"]))
    print("wrote %s" % os.path.relpath(OUT_HTML, ROOT))
    # 立族后必跑本脚本重建 → 顺手登记当前族表版本。R2790：R2789 15:38 立族
    # v1.4 后漏跑 note_epoch，当日纪元只剩 12:09 一条，混口径提示因此不触发。
    # note_epoch 自身落盘失败吞异常，不阻塞重建。
    print("epoch logged: %s (n=%d)" % (rof.TABLE_EPOCH, len(rof.note_epoch())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
