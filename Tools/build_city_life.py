# -*- coding: utf-8 -*-
"""城市日常面生成器（确定性·零 LLM·幂等）

读 census/export/citizen-behavior.jsonl + citizen-needs.jsonl + citizens-light.jsonl，
产出 census/export/city-life.html：此刻全城在做什么 / 四轴需求 / 好奇缺口 / 怪癖横截面 / 可见面。
数据内嵌为聚合与抽样，单文件零依赖，可离线打开。

用法: python -X utf8 Tools/build_city_life.py
"""
import collections
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
BEH = os.path.join(EXP, "citizen-behavior.jsonl")
NEED = os.path.join(EXP, "citizen-needs.jsonl")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-life.html")

STATE_CN = {
    "work": "在岗",
    "home": "居家",
    "school": "在学",
    "leisure_park": "游憩",
    "idle": "闲逛",
}
NEED_CN = {"anwen": "安稳", "shengji": "生计", "shejiao": "社交", "haoqi": "好奇"}
QUIRK_CN = {"slow": "慢性子", "umbrella": "随身带伞", "night_run": "夜跑习惯"}
SAMPLE_N = 30


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def bar(items, total, limit=None):
    items = items[:limit] if limit else items
    out = []
    for name, cnt in items:
        pct = (cnt / total * 100) if total else 0
        out.append(
            '<div class="row"><span class="lab">%s</span>'
            '<span class="track"><i style="width:%.1f%%"></i></span>'
            '<span class="num">%d · %.0f%%</span></div>'
            % (html.escape(str(name)), pct, cnt, pct)
        )
    return "\n".join(out)


def card(title, cnt, note=""):
    return (
        '<div class="card"><div class="k">%s</div>'
        '<div class="v">%s</div><div class="n">%s</div></div>'
        % (html.escape(title), html.escape(str(cnt)), html.escape(note))
    )


def person_line(name, district, extra):
    return (
        '<li><b>%s</b><span class="d">%s</span><span class="x">%s</span></li>'
        % (html.escape(name), html.escape(district), html.escape(extra))
    )


def main():
    beh = load_jsonl(BEH)
    need = load_jsonl(NEED)
    light = load_jsonl(LIGHT)

    total = len(beh)
    who = {r["id"]: r for r in light}
    need_by = {r["id"]: r for r in need}

    state_cnt = collections.Counter(r["state"] for r in beh)
    state_slots = collections.defaultdict(collections.Counter)
    for r in beh:
        state_slots[r["state"]][r.get("slot") or "—"] += 1

    top_cnt = collections.Counter(r["top"] for r in need)
    axis_sum = collections.Counter()
    for r in need:
        for k, v in (r.get("needs") or {}).items():
            axis_sum[k] += v or 0
    crash_rows = [r for r in need if r.get("crash")]
    crash_cnt = len(crash_rows)

    quirk_cnt = collections.Counter(r["quirk"] for r in beh if r.get("quirk"))
    visible_rows = [r for r in beh if r.get("visible")]

    def district_of(cid):
        w = who.get(cid) or {}
        return w.get("district") or "—"

    crash_by_district = collections.Counter(district_of(r["id"]) for r in crash_rows)
    visible_by_district = collections.Counter(district_of(r["id"]) for r in visible_rows)

    # 抽样：稳定排序（按编号），避免每轮变动
    crash_sample = sorted(crash_rows, key=lambda r: r["id"])[:SAMPLE_N]
    crash_sample_html = "\n".join(
        person_line(
            (who.get(r["id"]) or {}).get("name", r["id"]),
            district_of(r["id"]),
            "缺口·%s｜%s" % (
                NEED_CN.get(r.get("crash_axis"), r.get("crash_axis") or "—"),
                (who.get(r["id"]) or {}).get("profession") or "—",
            ),
        )
        for r in crash_sample
    )

    quirk_blocks = []
    for q in ("slow", "umbrella", "night_run"):
        rows = sorted((r for r in beh if r.get("quirk") == q), key=lambda r: r["id"])[:5]
        items = "\n".join(
            person_line(
                (who.get(r["id"]) or {}).get("name", r["id"]),
                district_of(r["id"]),
                "%s｜%s" % (STATE_CN.get(r["state"], r["state"]), r.get("slot") or "—"),
            )
            for r in rows
        )
        quirk_blocks.append(
            '<div class="qbox"><h4>%s <em>%d 人</em></h4><ul>%s</ul></div>'
            % (QUIRK_CN[q], quirk_cnt.get(q, 0), items)
        )

    slot_html = []
    for st, cnt in state_cnt.most_common():
        slots = state_slots[st].most_common(4)
        slot_html.append(
            '<div class="stbox"><h4>%s <em>%d 人</em></h4>%s</div>'
            % (
                STATE_CN.get(st, st),
                cnt,
                bar(slots, cnt),
            )
        )

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    ctx = (beh[0].get("ctx") if beh else "") or ""
    crash_pct = crash_cnt / total * 100 if total else 0
    visible_pct = len(visible_rows) / total * 100 if total else 0
    axis_label = [NEED_CN.get(k, k) for k, _ in axis_sum.most_common()]
    silent_axes = [NEED_CN[k] for k in ("anwen", "shengji", "shejiao", "haoqi") if axis_sum.get(k, 0) == 0]

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市日常面 · 硅基城市</title>
<style>
:root{{--bg:#0f1216;--fg:#e8ecf1;--dim:#8b97a6;--line:#232a33;--acc:#6fb3ff;--warn:#e0a45e}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 "Microsoft YaHei",system-ui,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-size:26px;margin:0 0 6px}}
.sub{{color:var(--dim);font-size:13px;margin-bottom:24px}}
h2{{font-size:17px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.card{{background:#151a21;border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.card .k{{color:var(--dim);font-size:12px}}
.card .v{{font-size:24px;font-weight:600;margin:4px 0 2px}}
.card .n{{color:var(--dim);font-size:12px}}
.row{{display:flex;align-items:center;gap:10px;margin:6px 0}}
.lab{{width:150px;flex:none;color:#c9d4e0;font-size:13px}}
.track{{flex:1;height:8px;background:#1c232c;border-radius:5px;overflow:hidden}}
.track i{{display:block;height:100%;background:linear-gradient(90deg,#4a86c8,#6fb3ff)}}
.num{{width:104px;flex:none;text-align:right;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}}
.stbox,.qbox{{background:#151a21;border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}}
.stbox h4,.qbox h4{{margin:0 0 10px;font-size:14px;font-weight:600}}
h4 em{{font-style:normal;color:var(--dim);font-weight:400;font-size:12px;margin-left:6px}}
ul{{margin:0;padding-left:0;list-style:none}}
li{{display:flex;gap:12px;padding:5px 0;border-top:1px solid #1b222b;font-size:13px}}
li:first-child{{border-top:0}}
li b{{width:150px;flex:none;font-weight:500}}
li .d{{width:110px;flex:none;color:var(--dim)}}
li .x{{color:#a9b6c4}}
.note{{background:#1a1712;border:1px solid #3a3020;border-radius:10px;padding:14px 16px;color:#c9bb9f;font-size:13px}}
.note b{{color:var(--warn)}}
.foot{{margin-top:40px;color:#5f6b7a;font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>城市日常面</h1>
<div class="sub">此刻全城在做什么 · 生成 {now} · 快照上下文 <code>{html.escape(ctx)}</code> · 数据源 census/export/citizen-behavior.jsonl + citizen-needs.jsonl</div>

<div class="cards">
{card("在册居民", total, "behavior+needs 双档齐备")}
{card("此刻在岗", state_cnt.get("work", 0), "全城第一大状态")}
{card("需求缺口", crash_cnt, "好奇轴未被满足 · %.1f%%" % crash_pct)}
{card("可见面", len(visible_rows), "落在他人视线内 · %.1f%%" % visible_pct)}
</div>

<h2>一 · 此刻在做什么</h2>
{"".join(slot_html)}

<h2>二 · 四轴需求</h2>
{bar([(NEED_CN.get(k, k), c) for k, c in top_cnt.most_common()], total)}
<div class="sub" style="margin-top:10px">主导需求：{" / ".join(axis_label)}　·　轴累计值 {" / ".join("%s %d" % (NEED_CN.get(k, k), v) for k, v in axis_sum.most_common())}</div>
<div class="sub">现状：{" / ".join(silent_axes)} 轴当前无需求记录{"" if not silent_axes else "（行为模型缺口·非居民缺失）"}。</div>

<h2>三 · 好奇缺口名单</h2>
<div class="sub">全城 {crash_cnt} 位居民的好奇缺口未被满足（%.1f%%），按城区分布如下。抽样 {len(crash_sample)} 位（按编号稳定排序，非实时个体状态）。</div>
{bar(crash_by_district.most_common(), crash_cnt)}
<ul style="margin-top:14px">
{crash_sample_html}
</ul>

<h2>四 · 怪癖横截面</h2>
{"".join(quirk_blocks)}

<h2>五 · 可见面</h2>
<div class="sub">共 {len(visible_rows)} 人此刻落在他人视野里，是城市最先被看见的那一层。</div>
{bar(visible_by_district.most_common(), len(visible_rows))}

<h2>六 · 读法说明</h2>
<div class="note">
<p><b>这不是个体实时状态。</b>behavior / needs 为启发式生成档（v=1），全城共享同一时段快照（{html.escape(ctx)}），说话的是分布，不是某位居民此刻真的站在哪里。</p>
<p>抽样只为展示样式，按居民编号稳定排序取前 {SAMPLE_N} 位，不代表缺口最重的人。</p>
<p>社交轴（shejiao）当前累计为 0，属行为模型覆盖缺口，已如实标注，不作成片结论引用。</p>
</div>

<div class="foot">BigLife · 城市日常面 · 确定性生成（零 LLM） · 全部数据 offline 内嵌</div>
</div></body></html>
"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)

    kb = os.path.getsize(OUT) / 1024
    print("city-life: %s  %.1f KB  rows=%d states=%d quirk=%d crash=%d visible=%d"
          % (os.path.relpath(OUT, ROOT), kb, total, len(state_cnt), sum(quirk_cnt.values()), crash_cnt, len(visible_rows)))
    print("checks: silent_axes=%s  crash_sample=%d  page<300KB=%s"
          % (",".join(silent_axes) or "none", len(crash_sample), kb < 300))


if __name__ == "__main__":
    main()