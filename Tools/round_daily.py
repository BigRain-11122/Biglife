# -*- coding: utf-8 -*-
"""确定性日更聚合器（零 LLM·幂等·单轮至多一次）。

病根（T-20261112-02）：本仓 23 个可见面构建器各自为战，没有任何轮次规程
引用它们——city-rumors 自 2026-10-27 起静默停更 16 天，同批 city-voices /
city-ops / city-relations / city-chronicle / resident-gallery 等 18 个面
同样是 10-27 的旧图，CEO 看到的是半个月前的城市。修法=把「哪些面必须当日
新鲜」写成唯一登记表，轮末一次调用即知其陈旧并就地重建。

两个档：
  daily  当日必新（日报/流言/城市生活/看板/索引）——输出 mtime 非当日即陈旧
  faces  结构性面（城区志/名人录/物件志/居民陈列…）——输出 mtime 超 1 日即陈旧
  input  生成器当日喂料（街区母题/流言链）——dated 文件缺失或非当日即补建
  data   派生物面（惊奇日志…）——输出在仓内非 export 目录，同样按当日判新鲜

用法:
  python -X utf8 Tools/round_daily.py --check            # 只体检，不重建
  python -X utf8 Tools/round_daily.py --run              # 重建陈旧面
  python -X utf8 Tools/round_daily.py --run --all        # 全部重建（含当日已新）
  python -X utf8 Tools/round_daily.py --run --only rumors,today
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
STATE_OUT = os.path.join(ROOT, "state", "round-daily.json")
SCRIPT_HASHES = os.path.join(ROOT, "state", "round-daily-script-hashes.json")
DEP_SNAPSHOT = os.path.join(ROOT, "state", "round-daily-deps.json")

# key, tier, script, outputs
REGISTRY = [
    ("today",      "daily", "build_daily_issue.py",       ["city-today.html"]),
    ("rumors",     "daily", "build_rumors.py",            ["city-rumors.html"]),
    ("life",       "daily", "build_city_life.py",         ["city-life.html"]),
    ("dashboard",  "daily", "build_city_dashboard.py",    ["city-dashboard.html"]),
    ("voices",     "faces", "build_city_voices.py",       ["city-voices.html"]),
    ("coverage",   "faces", "build_coverage.py",          ["city-coverage.html"]),
    ("ops",        "faces", "build_city_ops.py",          ["city-ops.html"]),
    ("relations",  "faces", "build_city_relations.py",    ["city-relations.html"]),
    ("chronicle",  "faces", "build_chronicle.py",         ["city-chronicle.html"]),
    ("districts",  "faces", "build_district_chronicle.py", ["city-districts.html"]),
    ("dossiers",   "faces", "build_city_dossiers.py",     ["city-dossiers.html"]),
    ("objects",    "faces", "build_object_atlas.py",      ["city-objects.html"]),
    ("map",        "faces", "build_city_map.py",          ["city-map.html"]),
    ("gallery",    "faces", "build_resident_gallery.py",  ["resident-gallery.html"]),
    ("goals",      "faces", "build_city_goals.py",        ["city-goals.html"]),
    ("gene_ledger", "faces", "build_gene_ledger.py",      ["gene-ledger.html"]),
    ("ring_picks", "faces", "build_ring_picks.py",        ["city-ring-picks.html"]),
    ("growth",     "faces", "build_growth_gallery.py",    ["city-growth.html"]),
    ("meets",      "faces", "build_city_meets.py",        ["city-meets.html"]),
    # v0.16 (2026-11-13 R2770): 议会提案面补入口 —— proposals.jsonl 自 10-24 起
    # 停供 19.6 天（T-20261113-02：旗标无人按），此前连「看得见」的页面都没有，
    # 断供只能靠人肉翻 jsonl 才发现。本页确定性零 LLM，同时把供给缺口（距最近一条
    # 几天）、早期机读串行标注、日上限口径摆在一屏。纳入 faces 档隨日更闸自发重建。
    ("proposals",  "faces", "build_city_proposals.py",    ["city-proposals.html"]),
    # v0.19 (2026-11-13 R2780): 叙龄面新立 —— 趋势页管质量、覆盖页管结构欠账，
    # 但「多少居民多久没说过话」此前没有任何可见面。实测 10111 席中 72.9% 叙龄
    # 14-29 天、14.4% 超 30 天，而当日只落 551 环（覆盖一轮 17.4 天）——产能真相
    # 只能人肉读导出才发现。faces 档：叙龄是日粒度量，不必逐轮重写。
    ("ring_recency", "faces", "build_ring_recency.py",    ["city-ring-recency.html"]),
    # v0.20 (2026-11-13 R2784): 年轮开头族仪表新立 —— T-20261112-04 验收线（开口族
    # >25% 拒稿）此前只有 CLI 读数，R2781/R2783 两轮归因全在终端，CEO 在页面上看不到
    # 「今天哪些族越线、越多少、哪些句式在重复」。trend 页管缺陷率走势、quality 页管
    # 质量分布，均不给族归属明细。本页把「当日越线族」与「全期禁集」两个分母并列，
    # 使「闸开着却仍越线」这一新病症可见（当日 40%/31% vs 全期 25.0% 的同一数据两面）。
    ("ring_openings", "faces", "build_ring_openings.py",  ["city-ring-openings.html"]),
    # v0.21 (2026-11-14 R2843): 反思录面新立 —— 中层记忆合成（reflect_citizen.py，
    # ≤40 字一条/30 天冷却）自 2026-09-25 上线起就是「盘上有数据、零可见面」：
    # 停 17.6 天与恢复产出都只有人肉读 jsonl 才知道（T-20261113-05 同病根）。
    # growth 页把它并进逐人档案，看不出「这条腿今天产没产、覆盖多少人」。
    ("reflections", "faces", "build_city_reflections.py", ["city-reflections.html"]),
    # v0.3 (2026-11-12 R2573): 补登记三个「有生成器、有页面、无任何轮次引用」的沉默断供面。
    # 病根同 T-20261112-02：city-lexicon.html 停更 15.7 天无人发现；
    # city-ring-quality / city-ring-trend 只靠偶发手工跑活着，断供只是时间问题。
    # 三者均确定性零 LLM，可直接纳入日更闸。
    ("lexicon",     "faces", "city_lexicon.py",           ["city-lexicon.html"]),
    ("ring_quality", "faces", "ring_simile_audit.py",     ["city-ring-quality.html"]),
    ("ring_trend",  "daily", "ring_quality_trend.py",     ["city-ring-trend.html"]),
    # v0.7 (2026-11-12 R2606): 覆盖面核查抓出两个「被可见面链接、却无任何轮次引用」的面
    # ——同 T-20261112-02 病根第四/五例。判据=逐个 Tools 生成器 × export html 反查，
    # 不看 mtime（mtime 只会告诉你已经烂了，不会告诉你会烂）。
    #   a) 社交图谱：index.html 卡片直接展示「10-27 10:15 更新」，停更 17 天；
    #      且默认输出在 census/ 根而非 export/，故用 ROOT 相对路径。
    #   b) 相遇候选单：city-coverage / city-ops / index 三处链接，今晚相遇轮要照单开工，
    #      断了等于让居民反复配同一批人。
    ("social_graph", "rootface", "build_social_graph.py",   ["census/city-social-graph.html"]),
    ("meet_candidates", "daily", "meet_candidates.py",      ["meet-candidates.jsonl", "meet-candidates.html"]),
    # v0.22 (2026-11-14 R2864): 名册统计面接线 —— census/INDEX.md 是 generate_census.py
    # 的「出生批次快照」，只在整库重生成时写一次；此后复产批/影射册/荣誉席各通道入册，
    # 卡片照落盘、INDEX 无人再写：实测停更 24.6 天，总人口仍写 10109（light 面实为 10114，
    # 差 5 席）。与 T-20261112-02 同病根（有产物、有读者、无任何轮次引用）。rootface 档，
    # 确定性零 LLM，数据变即重建、内容不变则逐字节相同（幂等）。T-20261114-01 接线。
    ("census_index", "rootface", "refresh_census_index.py", ["census/INDEX.md"]),
    # 索引必须最后跑：它登记的是本轮重建后的文件清单
    ("index",      "index", "build_export_index.py",      ["index.html"]),
]

# v0.2 (2026-11-12 R2571): 输入档 —— 面新鲜不等于喂料新鲜。
# 病根补记（T-20261112-01/02）：面重建了，但年轮线要吃的「当日文件」可能不存在
# （换日第一批、让路窗内年轮不跑、跨机首跑都常见），居民就只剩天气可锚。
# 输入档判据=当日 dated 文件存在且 mtime 是今天；缺失即调确定性生成器补（零 LLM）。
INPUTS = [
    ("life_motifs", "input", "city_life_events.py",       ["events/life/{date}.jsonl"]),
    ("rumor_chain", "input", "build_rumors.py",           ["cognition/rumors/rumors-{date}.jsonl"]),
    # v0.3 (2026-11-12 R2573): 派生物面 —— 从 FluxVerse world-events 只读派生，
    # 确定性零 LLM，却因无任何轮次引用而停更 16.8 天（至 10-26 的最后一行）。
    # 输出在 cognition/ 而非 census/export/，故走 data 档（base=ROOT，判当日）。
    ("surprise", "data", "surprise_log.py",               ["cognition/surprise-log.jsonl"], ["--feed"]),
    # v0.4 (2026-11-12): 互聊台账接线（T-20261112-03 修法②）——同 surprise 病根，
    # 另有「需外部喂源」一层：daily_interchat.py 取当日 rumors 首条链作源，
    # 无源即 SKIP 且不刷 mtime（源断供仍如实 stale）。
    ("interchat", "data", "daily_interchat.py",           ["cognition/interchat-ledger.jsonl"]),
    # v0.5 (2026-11-12): 派生数据面 = 「页面新鲜但数据陈旧」更深一层病灶。
    # 病根实证：goals 面当日重建（10:06），但它读的 census/export/citizen-goals.jsonl
    # 停在 10-26（16.8 天）——CEO 看到的「目标系统」整页是上月口径（55 行 month=2026-10），
    # 页面 mtime 天天新，内容却没人校验。故把派生数据本身纳入日更闸：
    # goals.py --regen 确定性零 LLM（同 (cid, month, date) 双跑逐字节一致），
    # 每日再生 → 跨月自动换 target/steps，页面随之反映当月。
    ("citizen_goals", "data", "goals.py",                 ["census/export/citizen-goals.jsonl"], ["--regen"]),
    # v0.6 (2026-11-12 R2595): 派生面漂移审计 —— 把 v0.5 只覆盖 goals 的病根补全。
    # 实证：七个 R3 派生面停在 10-26/10-27（16-17 天），而 city-map/relations/ops/
    # life/growth 每天照常重建 ⇒ 页面 mtime 是今天、数据是半个月前。
    # 判据用内容漂移而非 mtime：md5(id) 确定性派生，输入不变再生逐字节相同，
    # 按「当日必新」判等于每天白写 190MB（relations 2.85M 行）却零信息。
    # 漂移时才重建 dependents；稳定日仅 16s 盘读零页面动作。
    ("derive_audit", "data", "derive_audit.py",           ["state/derive-audit.json"], ["--run"]),
    # v0.14 (2026-11-13): 任务候选项面同病根第八例（T-20261112-02 同族）。
    # needs.py --tasks 产 census/export/citizen-tasks.jsonl（消费方按 axis→face 领活），
    # 有生成器、有 schema（Tools/schemas/citizen-tasks.schema.json）、有 QC 挂点，
    # 却无任何轮次引用：实测停在 09-26（48 天），而 needs 侧 10-28 改过 AXIS_NEED 口径
    # ⇒ 下游拿到的是上月「动机→任务」映射。纳入 data 档每日再生：
    # 确定性零 LLM（同日同输入双跑 28536 行逐字节一致），单跑秒级。
    ("citizen_tasks", "data", "needs.py",                 ["census/export/citizen-tasks.jsonl"], ["--tasks"]),
    # v0.13 (2026-11-13 R2734): QC 证据面同病根第七例 —— ring_lint.py 有脚本、
    # 有产出、无任何轮次引用，qa/RING-LINT-REPORT.md 静默停更 17 天（生成日 10-27，
    # 期间 10-28/11-12/11-13 三批共 1778 条年轮从未被内部码巡检覆盖）。
    # 手工补跑实证修复稳固：7451 条里 coded=766 全部落在 ≤10-26 旧段，
    # 10-28 起的三个批次 coded=0（0.0%）——违规面已被历史修复切断，无需再修卡。
    # 故只接巡检不断供（faces 档=>1 日才重建，避免零变化的逐日 churn）；
    # 真出回归时距离上次巡检 ≤2 日即可被看见。
    ("ring_lint", "faces", "ring_lint.py",                ["qa/RING-LINT-REPORT.md"]),
    # v0.15 (2026-11-13 R2738): 面覆盖自动发现 —— 登记表本身也要被看住。
    # 病根续例：REGISTRY 是人手表，于是「有生成器、有产物、无轮次引用」的面
    # 只能一轮发现一个（10-27 起 12 面 15 天、lexicon 15.7 天、social-graph 17 天、
    # ring_lint 17 天、citizen-tasks 48 天，同一病理的连续个案）。
    # face_coverage.py 自动扫 Tools 产物字面量 × 本登记表做差集（零 LLM 只读），
    # 报告按 faces 档保持 ≤1 日新鲜 —— 下一批漏登记面在烂掉之前就会出现在报告首屏。
    ("face_coverage", "faces", "face_coverage.py",        ["qa/FACE-COVERAGE-REPORT.md"],
     ["--write"]),
    # v0.17 (2026-11-13 R2771): 「有生成器、有产物、无轮次引用」第十例 ——
    # meet_asymmetry_scan.py 的 qa/MEET-SYMMETRY-REPORT.md 停在 11-12 11:08（1.1 天），
    # 而相遇轮每日最多落 3 对：写面闸（T-20261027-01）只保「写时对称」，
    # 卡面被后续改写/重排后的单边缺失只能靠这个扫描发现，它断了就没人看。
    # 用 daily 档（非 faces）——相遇是日更产品，同日新增的不对称当日就该现形；
    # 扫描只走有相遇行的百来位居民，秒级、零 LLM，逐日重建成本可忽略。
    ("meet_symmetry", "daily", "meet_asymmetry_scan.py",  ["qa/MEET-SYMMETRY-REPORT.md"]),
    # v0.23 (2026-11-14 R2899): 「有生成器、有产物、无轮次引用」第十一例 ——
    # cognition/city-chronicle.jsonl 的唯一写入口是 city_chronicle.py --feed，
    # 而该命令不在任何轮次规程里：本轮实测台账停在 11-13、--qc 仍报 fresh
    # （CHRONICLE_MAX_GAP_DAYS=1 容差吃掉「今天还没写」），页面 build_chronicle.py
    # 却照常重建 ⇒ 页面 mtime 天天新、年谱内容冻在上一天（v0.5/v0.6 同构）。
    # 实测 --feed 零 LLM、同日双跑 appended=0（幂等），data 档每日至多一次；
    # 源断供时如实 stale，不会假装新鲜。
    ("chronicle_feed", "data", "city_chronicle.py",       ["cognition/city-chronicle.jsonl"],
     ["--feed"]),
]

# v0.11 (2026-11-12 · T-20261112-09 收单): faces 档 stale 判据补「依赖源 mtime」面。
# 病根=日期粒度只问「产物是不是今天写的」，不问「喂它的源今天改过没有」。
# 实证=18:37 写 11 条基因（genes/language.json + lives.json）后，--run 仍判
# gene_ledger/lexicon fresh 零重建——那一步靠人手补跑生成器才对上；人手缺席时
# CEO 面静默停在写入前口径。判据=任一登记源 mtime > 产物 mtime 即 stale。
# 源缺失不在此处判（源断供归 data/input 档如实报），故 only-existing 语义。
DEPENDS = {
    # build_gene_ledger.py 只读这两处：基因正本 + 户卡正文目录
    "gene_ledger": ["genes/lives.json", "census/registry"],
    # city_lexicon.py 读三个 cognition 池面 + 基因口头禅正本（v0.2 R2933 第六节）
    "lexicon": ["cognition/pools.json", "cognition/greetings.json",
                "cognition/pools-negative.json", "genes/language.json"],
    # 环依赖面（v0.12 2026-11-12）：年轮批落进户卡后，这些面同日不再刷新。
    # 源信号取 evolve-cursor（每批年轮必写）+ registry 目录（新注册卡）。
    # 目录 mtime 只反映增删不反映内容改写，故 cursor 才是环落地的主信号。
    "today": ["state/evolve-cursor.json", "census/registry"],
    "dossiers": ["state/evolve-cursor.json", "census/registry"],
    "gallery": ["state/evolve-cursor.json", "census/registry"],
    "relations": ["state/evolve-cursor.json", "census/registry"],
    "districts": ["state/evolve-cursor.json", "census/registry"],
    "ring_picks": ["state/evolve-cursor.json", "census/registry"],
    "ring_quality": ["state/evolve-cursor.json", "census/registry"],
    "ring_trend": ["state/evolve-cursor.json", "census/registry"],
    # v0.19 (2026-11-13 R2780): 叙龄同时吃户籍轻量导出（行为线每轮重写）与环落地信号，
    # 两者任一更新都会改变分档，故双源登记。
    "ring_recency": ["census/export/citizens-light.jsonl", "state/evolve-cursor.json",
                     "census/registry"],
    # v0.22 (2026-11-14 R2864): 名册统计的唯一数据源就是 light 面 —— 新居民入册
    # （复产批/影射册/荣誉席）即改写行数，INDEX.md 必须跟着变。
    "census_index": ["census/export/citizens-light.jsonl"],
    # v0.20 (2026-11-13 R2784): 开头族仪表全量扫 registry 年轮行，源=registry 目录 +
    # 环落地主信号 evolve-cursor（与其余环依赖面同口径）。
    "ring_openings": ["state/evolve-cursor.json", "census/registry"],
    # v0.17 (2026-11-13 R2760): 看板的三行实况取自 docs/status-export.json，
    # 主数据取自 citizens-light.jsonl，但登记表只比「构建脚本 vs 产物」mtime。
    # 实证：R2760 刷新 top_text 后 --run 仍判 dashboard fresh、ran=0，CEO 面继续
    # 显示上一轮的三行（R2743 dep-mtime 同族第二例，那次补的是 gene_ledger 依赖）。
    # v0.18 (2026-11-13): 看板逐日曲线改从卡面数圈（全部圈），故 registry 也是数据源。
    "dashboard": ["docs/status-export.json", "census/export/citizens-light.jsonl",
                  "census/registry"],
    # v0.21 (2026-11-13 R2791): append-only 台账被补跑后，其消费者面仍按「当日 mtime」
    # 判 fresh——台账当日已被改写、页面停在改写前。实证：16:13 city_chronicle --feed
    # 补 59 行（2183 总计），city-chronicle.html（10:09 版）仍判 fresh、ran=0。
    # 同族第五面（前四：gene_ledger R2743 / dashboard R2760 / ring 面 v0.12 / 伪新 v0.9）。
    "chronicle": ["cognition/city-chronicle.jsonl"],
    # 提案台账 19:00 年轮批恢复供给后同类问题：页面不重建则 CEO 面停在旧提案。
    "proposals": ["cognition/proposals.jsonl"],
    # 城市生活页吃两张 append-only 台账（惊奇曲线 + 互聊），同为补跑型源。
    "life": ["cognition/surprise-log.jsonl", "cognition/interchat-ledger.jsonl"],
    # v0.24 (2026-11-14 R2906): 目标页 = 「页面新鲜、数据旧」的未登记依赖又一例。
    # 实证：census/export/citizen-goals.jsonl 由 citizen_goals 数据面每日 --regen
    # （11-14 00:07 版），而 city-goals.html 停在 11-13 15:09——页面比它读的数据旧
    # 9.7h，round_daily 反判 fresh（DEPENDS 无 goals 键 ⇒ faces 档只按 age>1.0 判，
    # 19.7h 未越线；数据日更而页面在 24h 内永远「看起来新」）。
    # 源按 build_city_goals.py 契约取两处：goals 派生面 + 姓名/城区/职业轻量导出。
    "goals": ["census/export/citizen-goals.jsonl", "census/export/citizens-light.jsonl"],
    # v0.25 (2026-11-14 R2908): faces/daily 档「读源未登记」全量收口（T-20261112-04 同族
    # 第 11-20 面，R2905 诚实边界留下的普查活）。病根同 goals：tier 判据只问产物自身
    # 年龄，不问喂它的源改没改。本轮实测十面全部陈旧于其源——coverage/objects -21.4h、
    # social_graph -18.8h、growth -17.3h、ops -17.5h、meets -10.2h、reflections -9.5h、
    # meet_candidates -1.7h，而 --run 逐面判 fresh，CEO 面停在上一批环/行为线之前的口径。
    # 源三分：①citizens-light.jsonl=行为线每轮重写；②*每日 --regen 派生面（persona/
    # anchors/behavior/relations）；③append-only 台账（reflections/coverage-backlog）。
    "voices": ["census/export/citizens-light.jsonl"],
    "coverage": ["census/export/citizens-light.jsonl",
                 "census/export/coverage-backlog.jsonl"],
    "ops": ["census/export/citizen-persona.jsonl",
            "census/export/citizens-light.jsonl", "state/ring-quality-queue.json"],
    "map": ["census/export/citizen-anchors.jsonl",
            "census/export/citizen-behavior.jsonl", "census/export/citizens-light.jsonl"],
    "growth": ["census/export/citizens-light.jsonl"],
    "reflections": ["census/reflections.jsonl", "census/export/citizens-light.jsonl"],
    # objects/meets 扫 registry 年轮行：目录 mtime 只反映增删，故并补 cursor 主信号
    # （与 v0.12 环依赖面同口径）。
    "objects": ["genes/lives.json", "state/evolve-cursor.json", "census/registry"],
    "meets": ["state/evolve-cursor.json", "census/registry"],
    "social_graph": ["census/export/citizen-relations.jsonl",
                     "census/export/citizens-light.jsonl"],
    "meet_candidates": ["census/export/citizens-light.jsonl", "census/registry"],
    # rumors 页与其同日台账由同一脚本产出（rumors-YYYY-MM-DD.jsonl 是产物非源），
    # 真源只有 light 面与 RUMOR-CHAIN 契约。
    "rumors": ["census/export/citizens-light.jsonl", "cognition/RUMOR-CHAIN.md"],
}

# 环依赖面的重建下限间隔（分钟）。年轮批约每轮落地一次，若按 mtime 逐次重建，
# 2.9MB 的陈列面会每 5 分钟刷新一次并被 commit，违反 REPO-SLIM 律；60 分钟
# 冷却=同日新环最迟 1 小时内进 CEO 面，同时把日更面写入量压到可接受水位。
DEPENDS_FLOOR_MIN = 60

# v0.16 (2026-11-13): 小面不设冷却。DEPENDS_FLOOR_MIN 是给 2.9MB 环依赖大面防 churn
# 用的（今天重建过就别再写），但 gene_ledger/lexicon 是百 KB 级台账面，且它们的源
# 恰恰会被「补数据」类动作改写（gene_adopt 写既有卡正文）——按 60 分钟冷却会让人
# 刚补的经历行在台账上最多压一小时看不见。这两面逐次重建成本 <1s，冷却归零。
# v0.17 (2026-11-13 R2760): dashboard 同理且更硬——它的三行实况是 CEO 过程可见面，
# 每轮更新一次 top_text 就必须当轮可见；63KB 重建 <1s，60 分钟冷却等于让 CEO 看旧话。
DEPENDS_FLOOR_OVERRIDE = {"gene_ledger": 0, "lexicon": 0, "dashboard": 0,
                          # v0.21: 台账消费者三面同为百 KB 级、重建 <1s，且源由
                          # 补跑型动作改写（chronicle --feed / proposal 批）——
                          # 冷却会让补进去的内容压一小时看不见。
                          "chronicle": 0, "proposals": 0, "life": 0,
                          # v0.24: 目标页 76KB、重建 <1s，且其源每日 00:0x 由数据面
                          # 重生——冷却会让当天的目标变更压一小时看不见。
                          "goals": 0,
                          # v0.25 (R2908): 新登记十面里除 map(864KB)/social_graph(1.6MB)
                          # 外均 ≤95KB、重建 <1s，且源为每轮重写的行为线——保留 60min
                          # 冷却等于让 CEO 每轮看的行为线落后一小时。大面两面不归零
                          # （每轮 2.4MB churn 违反 REPO-SLIM 律，60min 冷却照旧）。
                          "voices": 0, "coverage": 0, "ops": 0, "growth": 0,
                          "reflections": 0, "objects": 0, "meets": 0,
                          "meet_candidates": 0, "rumors": 0}

TIMEOUT_SEC = 240


def _out_paths(entry) -> list[str]:
    _key, tier, _script, names = entry[:4]
    base = ROOT if tier in ("input", "data") else EXP
    day = datetime.date.today().isoformat()
    out = []
    for n in names:
        n = n.replace("{date}", day)
        # v0.7 (2026-11-12): 少数面故意落在 export 之外（社交图谱=census/ 根），
        # 索引里按 ../ 相对链接。带目录分隔符的名字一律按 ROOT 相对解析，
        # 否则会被拼成 export/census/... 的幻影路径而永远判 missing。
        out.append(os.path.join(ROOT, n) if "/" in n else os.path.join(base, n))
    return out


def _age_days(path: str) -> float | None:
    if not os.path.exists(path):
        return None
    return (time.time() - os.path.getmtime(path)) / 86400.0


# 页面内嵌的源时点必须与来源文件 mtime 对上。mtime 判据只看页面重写时间，
# 源头未刷新时页面会被误判为当日新鲜（2026-11-12 看板 456 vs 真值 465 实锚）。
# 只登记「页面正文展示的就是该源的数据」的面；时点纯属装饰的面不登记——否则
# 源每刷一次就触发一次零信息量重建（meet-candidates / coverage 属此类，勿加）。
SNAPSHOT_SPECS = [
    # (页面名, 来源绝对路径, 时点正则, 页面时间精度)
    ("city-dashboard.html", os.path.join(EXP, "citizens-light.jsonl"),
     re.compile(r"数据截至\s*(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)"), "sec"),
    # v0.8 (2026-11-12 R2607):「此刻城市」页正文（槽位人数/时段/天气）全部取自
    # state/behavior-last.json，此前只有 mtime 判据 ⇒ 该源 15:13 刷新、页面停在
    # 10:06 仍判 fresh，CEO 读到「面生成 09:38」差 5.5 小时（T-20261112-04 同族）。
    ("city-today.html", os.path.join(ROOT, "state", "behavior-last.json"),
     re.compile(r"面生成\s*(\d{4}-\d\d-\d\d \d\d:\d\d)"), "min"),
]


def _fmt_mtime(path: str, precision: str) -> str:
    fmt = "%Y-%m-%d %H:%M" if precision == "min" else "%Y-%m-%d %H:%M:%S"
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime(fmt)


# v0.9 (2026-11-12): mtime 自身也会说谎——git 提交/检出会把文件 mtime 刷成当日，
# 内容却停在半个月前。实证：city-growth.html / city-meets.html 页脚自报
# 「生成 2026-10-28」，mtime 却是 11-12 01:12（R2513 提交刷新），faces 档按
# age>1.0 判 fresh ⇒ 日更闸永久跳过 15 天（T-20261112-04 同族第三面）。
# 判据=页面自报生成时点 vs 该页自身 mtime：自报旧于 mtime 超 1 天即「mtime 被伪造」。
# 只比页面内部两处口径、不与源文件比 ⇒ 源频繁刷新不会诱发零信息量重建。
_SELF_TS = re.compile(r"(?:生成|更新|快照|数据截至)(?:于)?\s*(\d{4}-\d\d-\d\d[ T]\d\d:\d\d)")


def _self_ts_stale(out_paths: list[str]) -> str | None:
    for p in out_paths:
        if not p.endswith(".html") or not os.path.exists(p):
            continue
        try:
            with io.open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        m = _SELF_TS.search(text)
        if not m:
            continue
        try:
            claimed = datetime.datetime.strptime(
                m.group(1).replace("T", " "), "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        actual = datetime.datetime.fromtimestamp(
            os.path.getmtime(p)).replace(second=0, microsecond=0)
        if (actual - claimed).total_seconds() > 86400:
            return "mtime-faked:%s claimed=%s mtime=%s" % (
                os.path.basename(p),
                claimed.strftime("%Y-%m-%d %H:%M"),
                actual.strftime("%Y-%m-%d %H:%M"))
    return None


def _content_stale(out_paths: list[str]) -> str | None:
    by_name = {os.path.basename(p): p for p in out_paths}
    for page, src, ts_re, precision in SNAPSHOT_SPECS:
        p = by_name.get(page)
        if not p or not (os.path.exists(p) and os.path.exists(src)):
            continue
        try:
            with io.open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        m = ts_re.search(text)
        if not m:
            continue
        want = _fmt_mtime(src, precision)
        if m.group(1) != want:
            return "content-stale:%s src=%s" % (page, want)
    return None


# v0.10 (2026-11-12 R2610): 生成器脚本「内容」变了而输出未重建。
# round_daily 原先只比输出 mtime ⇒ 判据模块升级后页面照旧算 fresh。
# 实锚：R2608 改族识别后 city-ring-trend.html 仍报 HAND_DEICTIC 42.8%(200/467)，
# 而与它同源的探针已读 55.0%(257/467)——CEO 可见面低报 12 个百分点。
# 判据用 sha256 而非 mtime：git checkout 会把 Tools/*.py 的 mtime 刷成当日（v0.9 同坑），
# 只有内容真变才重建，免疫 mtime 说谎。
# 基线：首跑无历史时只登记不重建（prev 缺失 ⇒ None），避免一次全量误重建。
def _load_script_hashes() -> dict:
    try:
        with io.open(SCRIPT_HASHES, encoding="utf-8") as f:
            got = json.load(f)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _script_sha(script: str) -> str | None:
    try:
        with open(os.path.join(ROOT, "Tools", script), "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def _script_changed(script: str, known_sha: dict | None) -> str | None:
    if not script or known_sha is None:
        return None
    sha = _script_sha(script)
    prev = known_sha.get(script)
    if sha and prev and prev != sha:
        return "script-changed:%s" % script
    return None


_MTIME_CACHE: dict[str, float | None] = {}


def _newest_mtime(path: str) -> float | None:
    """源的最新 mtime：文件取自身，目录取子树内最新文件。

    v0.16 (2026-11-13): 此前对目录直接 os.path.getmtime()，而目录 mtime 只在
    增删条目时变、不改写内容——实证 gene_adopt 改写 5 张既有居民卡的「经历」行后，
    gene_ledger 仍被判 fresh 零重建，台账与正文脱钩（T-20261112-02 同族第九例）。
    目录源（census/registry 含一万余卡）按子树遍历，进程内缓存避免 8 个环依赖面重复扫。
    """
    if path in _MTIME_CACHE:
        return _MTIME_CACHE[path]
    newest = None
    if os.path.isfile(path):
        try:
            newest = os.path.getmtime(path)
        except OSError:
            newest = None
    elif os.path.isdir(path):
        for root, _dirs, files in os.walk(path):
            for fn in files:
                try:
                    m = os.path.getmtime(os.path.join(root, fn))
                except OSError:
                    continue
                if newest is None or m > newest:
                    newest = m
    _MTIME_CACHE[path] = newest
    return newest


_DEP_SNAP: dict | None = None
_DEP_FP_CACHE: dict[str, str | None] = {}


def _load_dep_snapshot() -> dict:
    global _DEP_SNAP
    if _DEP_SNAP is None:
        try:
            with io.open(DEP_SNAPSHOT, encoding="utf-8") as f:
                _DEP_SNAP = json.load(f)
        except (OSError, ValueError):
            _DEP_SNAP = {}
    return _DEP_SNAP


def _dep_fingerprint(key: str) -> str | None:
    """依赖源的内容指纹：文件取 sha256，目录取 (相对路径, 字节数) 清单哈希。

    v0.26 (2026-11-14 R2921): dep-mtime 判据会被「同内容重写」刷假——行为线每轮
    重写 state/evolve-cursor.json（内容不变、mtime 前进），七个环依赖大面因此每轮
    被选中重建，relations 单面 240s 超时（2.85M 行），日更面清零而产物零变化。
    修法=指纹一致即视作已对齐，mtime 只做粗筛（与 _script_sha 同思路）。
    """
    if key in _DEP_FP_CACHE:
        return _DEP_FP_CACHE[key]
    srcs = DEPENDS.get(key) or []
    h = hashlib.sha256()
    seen = False
    for rel in srcs:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            try:
                with open(p, "rb") as f:
                    for chunk in iter(lambda: f.read(1 << 20), b""):
                        h.update(chunk)
                seen = True
            except OSError:
                continue
        elif os.path.isdir(p):
            rows = []
            for root, _dirs, files in os.walk(p):
                for fn in files:
                    fp = os.path.join(root, fn)
                    try:
                        rows.append((os.path.relpath(fp, p),
                                     os.path.getsize(fp)))
                    except OSError:
                        continue
            rows.sort()
            for name, size in rows:
                h.update(("%s\t%d\n" % (name, size)).encode("utf-8"))
            seen = True
    _DEP_FP_CACHE[key] = h.hexdigest() if seen else None
    return _DEP_FP_CACHE[key]


def _dep_mtime_stale(key: str, out_paths: list[str]) -> str | None:
    """依赖源比产物新即 stale（同日内的源变更，日期粒度看不见）。"""
    srcs = DEPENDS.get(key)
    if not srcs:
        return None
    newest, newest_rel = None, None
    for rel in srcs:
        p = os.path.join(ROOT, rel)
        m = _newest_mtime(p)
        if m is None:
            continue
        if newest is None or m > newest:
            newest, newest_rel = m, rel
    if newest is None:
        return None
    oldest_out = min(os.path.getmtime(p) for p in out_paths)
    if newest > oldest_out:
        # 冷却下限：刚重建过的面不因下一批年轮立刻再刷（防 5 分钟级大面 churn）
        floor_min = DEPENDS_FLOOR_OVERRIDE.get(key, DEPENDS_FLOOR_MIN)
        if (time.time() - oldest_out) < floor_min * 60:
            return None
        # v0.26: mtime 前进但内容未变（同内容重写）= 假信号，不重建
        fp = _dep_fingerprint(key)
        if fp is not None and _load_dep_snapshot().get(key) == fp:
            return None
        return "dep-mtime:%s" % newest_rel
    return None


def _is_stale(entry, now_date: datetime.date, out_paths: list[str],
              known_sha: dict | None = None) -> tuple[bool, str]:
    _key, tier, _script, _names = entry[:4]
    ages = []
    for p in out_paths:
        if not os.path.exists(p):
            return True, "missing:" + os.path.basename(p)
        ages.append(_age_days(p) or 0.0)
    age = max(ages)
    mdate = datetime.date.fromtimestamp(
        max(os.path.getmtime(p) for p in out_paths))
    if tier in ("daily", "input", "data"):
        stale = mdate != now_date
        if not stale:
            drift = (_content_stale(out_paths) or _self_ts_stale(out_paths)
                     or _script_changed(_script, known_sha)
                     or _dep_mtime_stale(_key, out_paths))
            if drift:
                return True, drift
        return stale, ("outdated:%sd" % int(age) if stale else "fresh")
    stale = age > 1.0
    if not stale:
        faked = (_self_ts_stale(out_paths) or _script_changed(_script, known_sha)
                 or _dep_mtime_stale(_key, out_paths))
        if faked:
            return True, faked
    return stale, ("outdated:%sd" % int(age) if stale else "fresh")


def _run_one(script: str, extra=None) -> tuple[int, str]:
    cmd = [sys.executable, "-X", "utf8", os.path.join(ROOT, "Tools", script)]
    cmd.extend(extra or [])
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        return 124, "timeout>%ds" % TIMEOUT_SEC
    tail = (proc.stdout or "").strip().splitlines()
    msg = tail[-1][:160] if tail else ""
    if proc.returncode != 0:
        err = (proc.stderr or "").strip().splitlines()
        msg = (err[-1][:160] if err else msg) or "rc=%d" % proc.returncode
    return proc.returncode, msg


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只体检（默认行为）")
    ap.add_argument("--run", action="store_true", help="重建陈旧面")
    ap.add_argument("--all", action="store_true", help="重建全部（含已新鲜）")
    ap.add_argument("--only", default=None, help="只处理这些 key（逗号分隔）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args()

    only = set(x.strip() for x in args.only.split(",") if x.strip()) if args.only else None
    today = datetime.date.today()
    known_sha = _load_script_hashes()
    # 输入档在前：年轮线要吃的当日文件优先补齐，再重建可见面
    entries = [e for e in (INPUTS + REGISTRY) if (only is None or e[0] in only)]

    plan = []
    for e in entries:
        outs = _out_paths(e)
        stale, why = _is_stale(e, today, outs, known_sha)
        plan.append({"key": e[0], "tier": e[1], "script": e[2],
                     "outputs": e[3], "stale": stale, "why": why,
                     "extra": (list(e[4]) if len(e) > 4 else [])})

    results = []
    ran = 0
    for item in plan:
        if not args.run:
            results.append(dict(item, action="skipped-check", rc=None, msg=""))
            continue
        if item["tier"] == "index":
            # 索引登记的是本轮重建后的文件清单：只有真有面重建时才需要重排
            if not (args.all or any(r.get("action") == "rebuilt" for r in results)):
                results.append(dict(item, action="skipped-nochange", rc=None, msg=""))
                continue
        elif not (args.all or item["stale"]):
            results.append(dict(item, action="skipped-fresh", rc=None, msg=""))
            continue
        rc, msg = _run_one(item["script"], item.get("extra"))
        ran += 1
        results.append(dict(item, action="rebuilt" if rc == 0 else "failed",
                            rc=rc, msg=msg))

    payload = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "run" if args.run else "check",
        "ran": ran,
        "stale": [r["key"] for r in results if r["stale"]],
        "failed": [r["key"] for r in results if r["action"] == "failed"],
        "items": results,
    }

    # 只有「确认新鲜」或「重建成功」的面才登记新哈希；失败面保留旧值，
    # 下一轮仍会因 script-changed 再次选中（不把失败伪装成已对齐）。
    if args.run:
        nxt = dict(known_sha)
        for r in results:
            if r["action"] in ("skipped-fresh", "skipped-nochange", "rebuilt"):
                sha = _script_sha(r["script"])
                if sha:
                    nxt[r["script"]] = sha
        try:
            os.makedirs(os.path.dirname(SCRIPT_HASHES), exist_ok=True)
            with open(SCRIPT_HASHES, "w", encoding="utf-8", newline="\n") as f:
                json.dump(nxt, f, ensure_ascii=False, indent=1, sort_keys=True)
                f.write("\n")
        except OSError:
            pass
        known_sha = nxt  # 收尾复检必须用同一口径，否则会把自己刚重建的面误报 STALE
        # v0.26: 依赖源内容快照——只有「确认新鲜」或「重建成功」的面才登记，
        # 失败面保留旧指纹，下轮仍会因 dep-mtime 再次选中（不把失败伪装成已对齐）。
        global _DEP_SNAP
        snap = dict(_load_dep_snapshot())
        for r in results:
            if r["action"] in ("skipped-fresh", "skipped-nochange", "rebuilt"):
                if DEPENDS.get(r["key"]):
                    fp = _dep_fingerprint(r["key"])
                    if fp:
                        snap[r["key"]] = fp
        try:
            with open(DEP_SNAPSHOT, "w", encoding="utf-8", newline="\n") as f:
                json.dump(snap, f, ensure_ascii=False, indent=1, sort_keys=True)
                f.write("\n")
        except OSError:
            pass
        _DEP_SNAP = snap
    os.makedirs(os.path.dirname(STATE_OUT), exist_ok=True)
    with open(STATE_OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write("\n")

    if args.json:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=1) + "\n")
        return 0 if not payload["failed"] else 1

    print("== round_daily (%s) ==" % payload["mode"])
    for r in results:
        print("  %-12s %-7s %-9s %s" % (r["key"], r["tier"], r["action"], r["why"]))
    print("stale=%d ran=%d failed=%d" % (len(payload["stale"]), ran, len(payload["failed"])))
    if payload["failed"]:
        print("FAILED: " + ",".join(payload["failed"]))
        return 1
    # v0.7 (2026-11-12): 体检必须诚实——上面那行 stale= 是「跑之前」的口径，
    # 旧版无论剩多少陈旧都印 verdict: PASS（社交图谱就是这样烂了 17 天没人发现：
    # 索引卡片写着 10-27，而闸每次都说 PASS）。改为跑完后再判一次真实余量，
    # 余量为零才 PASS；否则 STALE + rc=2（同 ring_material_check 的未达码约定）。
    remaining = []
    # v0.8 (2026-11-14 T-20261114-01 补): 幂等构建器在「内容与输入已一致」时逐字节相同、
    # 不重写文件，mtime 停留在旧值——此时 mtime 代理会永久红灯（census_index 每轮都报
    # dep-mtime 而实为已对齐）。判据改：本轮已成功重建（rc=0）的面即视为与当前输入对齐。
    just_rebuilt = set(r["key"] for r in results if r["action"] == "rebuilt")
    for e in entries:
        if e[0] in just_rebuilt:
            continue
        still, why = _is_stale(e, today, _out_paths(e), known_sha)
        if still:
            remaining.append("%s(%s)" % (e[0], why))
    if remaining:
        print("verdict: STALE remaining=%d %s" % (len(remaining), ",".join(remaining)))
        return 2
    print("verdict: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
