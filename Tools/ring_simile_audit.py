# -*- coding: utf-8 -*-
"""年轮复读/空洞审计（零 LLM·确定性）——品质闸的计量面。

背景（2026-10-27 R2380）：QC 只查结构与锚注脚，查不出「同一居民相邻年轮换词
不换意」的复读病（抽样 C-00033 三圈同讲「一句话就够，翻篇」），这是 CEO
2026-09-29「品质也很差」的直接来源之一。本工具把复读与空洞量化成可执行队列，
供夜班重写按序回炉。

判据（全部确定性、可复算）：
  sim   = 同一居民相邻两圈 core 文本的字符 3-gram Jaccard ≥ SIM_TH
  short = 年轮 core（去掉 [锚] 注脚）字数 < SHORT_CHARS
  tmpl  = 该圈含全局模板句（8-gram 被 ≥ TMPL_CITIZENS 位居民共用）

产物：
  qa/RING-SIMILE-REPORT.md          人读报告（分布 / 模板句榜 / 复读最重样本）
  state/ring-quality-queue.json     夜班重写队列（按严重度排序，落盘不入库）
  census/export/city-ring-quality.html  可视化页

用法：
  python -X utf8 Tools/ring_simile_audit.py
  python -X utf8 Tools/ring_simile_audit.py --since 2026-10-20
"""
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import html
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT = os.path.join(ROOT, "qa", "RING-SIMILE-REPORT.md")
QUEUE = os.path.join(ROOT, "state", "ring-quality-queue.json")
PAGE = os.path.join(ROOT, "census", "export", "city-ring-quality.html")

RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})[ \t]*(.+)$", re.M)
HEAD_RE = re.compile(r"^#\s*(C-\d+)\s*·\s*(.+)$")
ANCHOR_RE = re.compile(r"\s*\[锚\].*$")
PUNCT_RE = re.compile(r"[\s\u3000，。、；：！？“”‘’（）《》—…·,.;:!?()\[\]\"'-]+")

SIM_TH = 0.40
SHORT_CHARS = 20  # 全库正文字数 p5=20（中位 38）——取尾部 5% 作空洞线
TMPL_GRAM = 10
TMPL_CITIZENS = 20
QUEUE_CAP = 400


def core(body: str) -> str:
    """去掉 [锚] 注脚后的正文。"""
    return ANCHOR_RE.sub("", body).strip()


def grams(text: str, n: int = 3) -> set[str]:
    s = PUNCT_RE.sub("", text)
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def parse(path: str) -> tuple[str, str, list[tuple[str, str]]]:
    with io.open(path, encoding="utf-8") as fh:
        text = fh.read()
    head = text.splitlines()[0] if text else ""
    m = HEAD_RE.match(head)
    cid, name = (m.group(1), m.group(2).strip()) if m else ("", head.strip())
    rings: list[tuple[str, str]] = []
    if "**年轮**" in text:
        block = text.split("**年轮**", 1)[1].split("**进化**", 1)[0]
        rings = [(d, b) for d, b in RING_RE.findall(block)]
    return cid, name, rings


def build_page(stats: dict, tmpl: list[dict], heavy: list[dict]) -> str:
    e = html.escape
    rows = []
    for item in heavy:
        rings = "".join(
            "<li><time>%s</time><p>%s</p></li>" % (e(r["date"]), e(r["text"]))
            for r in item["rings"])
        rows.append(
            '<article class="card"><h2>%s<span class="id">%s</span></h2>'
            '<p class="meta">%s · 年轮 %d 圈 · 最重相邻相似 %.0f%%</p>'
            '<ul class="rings">%s</ul></article>'
            % (e(item["name"]), e(item["id"]), e(item["where"]),
               item["count"], item["worst"] * 100, rings))
    tmpl_rows = "".join(
        "<tr><td>%s</td><td>%d</td></tr>" % (e(t["text"]), t["citizens"]) for t in tmpl)

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>年轮品质透视 · BigLife</title>
<style>
:root{{--bg:#12141a;--fg:#e6e6e6;--dim:#8d94a3;--line:#262a33;--accent:#7fb0d8;--warn:#d89a7f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 "Noto Sans SC","Microsoft YaHei",sans-serif}}
header{{padding:28px 20px 12px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:20px;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;padding:16px 20px;border-bottom:1px solid var(--line)}}
.kpi{{border:1px solid var(--line);border-radius:6px;padding:10px 14px;background:#171a21;min-width:150px}}
.kpi b{{display:block;font-size:22px;font-weight:600}}
.kpi span{{color:var(--dim);font-size:12px}}
h2.sec{{padding:20px 20px 6px;font-size:16px;margin:0}}
table{{border-collapse:collapse;margin:0 20px 10px;font-size:14px}}
th,td{{border:1px solid var(--line);padding:6px 10px;text-align:left}}
th{{color:var(--dim);font-weight:500}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:14px;padding:14px 20px 60px}}
.card{{border:1px solid var(--line);border-radius:6px;padding:14px 16px;background:#171a21}}
.card h2{{margin:0 0 4px;font-size:16px;font-weight:600}}
.id{{color:var(--dim);font-size:12px;margin-left:8px;font-weight:400}}
.meta{{margin:0 0 8px;color:var(--warn);font-size:13px}}
.rings{{margin:0;padding-left:18px}}
.rings li{{margin:0 0 8px}}
.rings time{{color:var(--dim);font-size:12px;display:block}}
.rings p{{margin:2px 0 0}}
footer{{padding:16px 20px 40px;color:var(--dim);font-size:12px;border-top:1px solid var(--line)}}
</style></head>
<body><!--bl-nav:index--><div style="position:fixed;left:12px;top:12px;z-index:9999"><a href="index.html" style="display:inline-block;padding:5px 10px;background:rgba(20,24,30,.86);border:1px solid #303740;border-radius:4px;color:#c8a06a;font:12px/1 'Songti SC',Georgia,serif;text-decoration:none">← 城市目录</a></div>
<header>
<h1>年轮品质透视</h1>
<p class="sub">扫描面 {e(stats['since'])} 起 · 年轮 {stats['rings']} 圈 / 居民 {stats['citizens']} 位 ·
相邻复读 {stats['sim_rows']} 处 / 空洞偏短 {stats['short_rows']} 处 · 生成 {e(stats['day'])}（零 LLM·确定性可复算）</p>
</header>
<div class="kpis">
<div class="kpi"><b>{stats['sim_citizens']}</b><span>复读居民（相邻相似 ≥40%）</span></div>
<div class="kpi"><b>{stats['short_rows']}</b><span>偏短年轮（正文 &lt;45 字）</span></div>
<div class="kpi"><b>{stats['tmpl_rows']}</b><span>命中全局模板句的年轮</span></div>
<div class="kpi"><b>{stats['queue']}</b><span>夜班重写队列条数</span></div>
</div>
<h2 class="sec">被最多居民共用的句块（8 字窗口 · 前 20）</h2>
<table><tr><th>句块</th><th>涉及居民</th></tr>{tmpl_rows or '<tr><td colspan="2">（无）</td></tr>'}</table>
<h2 class="sec">复读最重的居民（按最重相邻相似排序 · 前 {len(heavy)} 位）</h2>
<main>{''.join(rows) or '<p class="meta">（无）</p>'}</main>
<footer>判据：同居民相邻年轮正文（去 [锚] 注脚）字符 3-gram Jaccard ≥ 0.40 记一处复读；正文 &lt; 45 字记偏短；
模板句=8 字窗口被 ≥ {TMPL_CITIZENS} 位居民共用。存量不回改（锚定律），只计量并进队列。
队列文件：state/ring-quality-queue.json</footer>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-09-01")
    ap.add_argument("--heavy", type=int, default=12)
    args = ap.parse_args()

    day = datetime.date.today().isoformat()
    gram_citizens: dict[str, set[str]] = collections.defaultdict(set)
    per_citizen: dict[str, dict] = {}
    sim_rows = short_rows = 0

    for path in sorted(glob.glob(os.path.join(ROOT, "census", "registry", "**", "*.md"),
                                 recursive=True)):
        cid, name, rings = parse(path)
        if not cid:
            continue
        rings = [(d, b) for d, b in rings if d >= args.since]
        if not rings:
            continue
        where = os.path.basename(os.path.dirname(path))
        prev = None
        worst = 0.0
        records = []
        for date, body in rings:
            c = core(body)
            clean = PUNCT_RE.sub("", c)
            g = grams(c)
            sh = {clean[i:i + TMPL_GRAM] for i in range(max(0, len(clean) - TMPL_GRAM + 1))}
            for x in sh:
                gram_citizens[x].add(cid)
            reasons = []
            if len(clean) < SHORT_CHARS:
                reasons.append("short")
                short_rows += 1
            if prev is not None:
                score = jaccard(prev, g)
                if score >= SIM_TH:
                    reasons.append("sim=%.0f%%" % (score * 100))
                    sim_rows += 1
                    worst = max(worst, score)
            records.append({"date": date, "text": c[:200], "sh": sh, "reasons": reasons})
            prev = g
        per_citizen[cid] = {
            "id": cid, "name": name, "where": where,
            "count": len(rings), "worst": worst,
            "rings_for_page": [{"date": d, "text": core(b)[:220]} for d, b in rings[-4:]],
            "records": records, "flags": [],
        }

    tmpl = [{"text": k, "citizens": len(v)}
            for k, v in sorted(gram_citizens.items(), key=lambda kv: -len(kv[1]))
            if len(v) >= TMPL_CITIZENS][:20]
    tmpl_set = {t["text"] for t in tmpl}
    tmpl_rows = 0
    for c in per_citizen.values():
        for r in c["records"]:
            hits = sorted(r["sh"] & tmpl_set)
            if hits:
                r["reasons"].append("tmpl")
                r["tmpl"] = hits[0]
                tmpl_rows += 1
            if r["reasons"]:
                c["flags"].append({"date": r["date"], "reason": "+".join(r["reasons"]),
                                   "text": r["text"],
                                   "card": "census/registry/%s/%s.md" % (c["where"], c["id"])})
        c.pop("records", None)

    queue = []
    for c in per_citizen.values():
        for f in c["flags"]:
            weight = ("sim" in f["reason"]) * 3 + ("short" in f["reason"]) * 2 + ("tmpl" in f["reason"])
            queue.append({"card": f["card"], "id": c["id"], "name": c["name"],
                          "date": f["date"], "reason": f["reason"], "text": f["text"],
                          "_w": weight})
    queue.sort(key=lambda r: r["date"], reverse=True)
    queue.sort(key=lambda r: -r["_w"])  # 稳定排序：同权重内保持日期倒序
    queue = queue[:QUEUE_CAP]
    for r in queue:
        r.pop("_w", None)

    heavy = sorted([c for c in per_citizen.values() if c["flags"]],
                   key=lambda c: (-c["worst"], -len(c["flags"]), c["id"]))[:args.heavy]
    heavy_page = [{"id": c["id"], "name": c["name"], "where": c["where"],
                   "count": c["count"], "worst": c["worst"],
                   "rings": [{"date": r["date"],
                              "text": ("[%s] " % next((f["reason"] for f in c["flags"]
                                                       if f["date"] == r["date"]), "")) + r["text"]}
                             for r in c["rings_for_page"]]} for c in heavy]

    stats = {"since": args.since, "day": day, "citizens": len(per_citizen),
             "rings": sum(c["count"] for c in per_citizen.values()),
             "sim_rows": sim_rows, "short_rows": short_rows,
             "sim_citizens": sum(1 for c in per_citizen.values() if c["worst"] > 0),
             "tmpl_rows": tmpl_rows, "queue": len(queue)}

    os.makedirs(os.path.join(ROOT, "qa"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "state"), exist_ok=True)
    with io.open(QUEUE, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"generated": day, "since": args.since, "cap": QUEUE_CAP,
                   "items": queue}, f, ensure_ascii=False, indent=1)

    lines = [
        "# 年轮复读/空洞审计报告",
        "",
        "扫描面：`census/registry/**/*.md` 年轮段（日期 ≥ %s）· 生成 %s · 零 LLM 确定性" % (args.since, day),
        "",
        "判据：同居民相邻年轮正文（去 `[锚]` 注脚）字符 3-gram Jaccard ≥ %.2f 记一处复读；"
        % SIM_TH,
        "正文 < %d 字记偏短；8 字窗口被 ≥ %d 位居民共用记模板句。" % (SHORT_CHARS, TMPL_CITIZENS),
        "",
        "## 总览",
        "",
        "| 指标 | 数值 |",
        "| --- | ---: |",
        "| 居民（有年轮） | %d |" % stats["citizens"],
        "| 年轮总数 | %d |" % stats["rings"],
        "| 相邻复读处 | %d |" % sim_rows,
        "| 复读居民数 | %d |" % stats["sim_citizens"],
        "| 偏短年轮 | %d |" % short_rows,
        "| 命中模板句年轮 | %d |" % tmpl_rows,
        "| 夜班重写队列 | %d（上限 %d） |" % (len(queue), QUEUE_CAP),
        "",
        "## 被最多居民共用的句块（前 20）",
        "",
        "| 句块 | 涉及居民 |",
        "| --- | ---: |",
    ]
    for t in tmpl:
        lines.append("| %s | %d |" % (t["text"], t["citizens"]))
    if not tmpl:
        lines.append("| （无） | 0 |")
    lines += ["", "## 复读最重的居民（前 %d 位）" % len(heavy_page), ""]
    for c in heavy_page:
        lines.append("### %s %s（%s · %d 圈 · 最重相似 %.0f%%）"
                     % (c["id"], c["name"], c["where"], c["count"], c["worst"] * 100))
        for r in c["rings"]:
            lines.append("- %s %s" % (r["date"], r["text"]))
        lines.append("")
    lines += [
        "## 处置口径",
        "",
        "- 存量年轮不回改（锚定律保全原文），只计量。",
        "- 队列 `state/ring-quality-queue.json` 供夜班 `evolve_citizen.py` 重写时优先取用；",
        "  重写须换事实锚（新事件/新天气），不得换词不换意。",
        "- 出生站闸建议：落环口对「与本卡上一圈相似 ≥ %.2f」判 REGEN（待立法窗授权）。" % SIM_TH,
        "",
        "可视化：`census/export/city-ring-quality.html`",
    ]
    with io.open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with io.open(PAGE, "w", encoding="utf-8", newline="\n") as f:
        f.write(build_page(stats, tmpl, heavy_page))

    print("rings=%d citizens=%d sim=%d short=%d tmpl=%d queue=%d report=%s page=%s"
          % (stats["rings"], stats["citizens"], sim_rows, short_rows, tmpl_rows,
             len(queue), os.path.relpath(REPORT, ROOT), os.path.relpath(PAGE, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())