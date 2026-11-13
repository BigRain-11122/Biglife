#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""v1.0 (2026-11-12 R2581, T-20261112-04): 年轮开头骨架族配额闸（源头出生站）。

病根（qa/RING-OPENING-SKELETON-20261112.md R2580 实证）：修掉抽象天气族
（雨还在下/檐下，10-24 峰值 1011 → 11-12 32）之后，模型把开头换成了具象
骨架「手在X／手上的X／我正把X」，占当日产出 10-19 0.0% → 11-12 42.2% 单调
爬升。1663/2143 高频开头（76.2%）无法用口头禅库解释 = 模型自创句法，不是
人设。

裁决（同审计 §五）：**不做首 12 字跨卡永久去重硬闸**（会误杀 135 卡共用
口头禅的合法人设）；改为**骨架族配额闸**——按族统计当日占比，>25% 即拒稿
重写。禁的是配额不是词：一次「手心的汗」合法，全天四成居民都从手开讲才
是病。

设计边界（gate-rigor 六问）：
  标定依据 = R2580 全库 16249 环按日实测（本模块 --scan 可复现）；
  唯一判据 = 开头（去空白后前 12 字）命中族正则的数量／当日环数 > 25%；
  负控 = --selftest 四探针（口头禅正例必须不被拦 / 句中身体描写不算开头）；
  能力边界 = 只判开头骨架位置，不评正文中后段品质，不判词面好坏；
  失效条件 = registry 缺失 → 返回空统计、闸关闭（零漂移，同 evolve_citizen
             gap #70/#71 law）；
  验证记录 = qa/RING-FAMILY-GATE-20261112.md。

零 LLM / 零 GPU / 确定性：同一 registry 双跑输出逐字节一致。
"""
import argparse
import collections
import datetime
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, "census")
REGISTRY = os.path.join(CENSUS, "registry")

OPENING_LEN = 12          # 与 evolve_citizen.today_ring_openings 同口径
FAMILY_QUOTA = 0.25       # T-20261112-04 验收线：>25% 触发拒稿
FAMILY_MIN_DENOM = 8      # 当日 <8 环不判（小样本噪声）

# v1.2（2026-11-13 R2786, T-20261113-03）：跨口径日守卫。
# 判例：11-13 全日读到 HAND 40.0%「越线」，但用当日生产时真正生效的族表
# （无 ^手里、无 PROP_DEICTIC 族，二者 12:09 才立）回算是 138/552=25.0%——
# 天然生产的 254 环里 83 条「手里…」+171 条「那台/这把…」生来就不在族表里。
# 即「已开仍越线」是**立族时点在当日之后**造成的追溯重分类，不是闸被绕过。
# 病根：族表是代码常量、没有生效时间，改一次正则就等于把过去的日子重判一遍，
# 读数和当日决策各看各的口径。此处只加"读得出来"的守卫（不改阈值、不改闸）：
# 每次族表（FAMILIES 结构或其正则集合）变更必须 bump TABLE_EPOCH，批起登记。
TABLE_EPOCH = "2026-11-13T15:38"   # 族表最后一次变更（=RAIN_SETTING_DEICTIC 立族·v1.4）
EPOCH_LOG = os.path.join(ROOT, "state", "ring-family-epochs.json")

# 族定义：锚定开头位置（^），只认句式骨架不认词义。
# 每族 = (说明, 正则列表)。扩展新族=fail-safe（未命中即不算）。
FAMILIES = collections.OrderedDict([
    ("HAND_DEICTIC", (
        "手部指示+第一人称进行时骨架（手在X／手上X／手边X／我正把X）——"
        "R2580 实证单调爬升族；裸「我正+动词」同源（我正低头磨…／我正对着…），"
        "今日 8 条，计入同族。R2608 补「手边/手头/手上+指示词」盲区："
        "旧式只认「手上的」（要求「的」），而 2026-11-12 实测 49 条"
        "「手边那截旧护缆…」「手边这几样我都过了一遍…」同形不同助词，"
        "全部漏判逃过配额闸——族定义本文早已写「手上的X」，故此处属"
        "补全既有定义而非新增族（改前 200/467=42.8%，改后 249/467=53.3%）",
        [r"^手在", r"^手上", r"^手边", r"^手头", r"^手底下", r"^手心",
         r"^手掌", r"^手肘", r"^手背", r"^手里", r"^手中的",
         r"^我正", r"^我把手[边头上下]"],
    )),
    ("TIME_OPEN", (
        "时点开场骨架（这会儿／今早／天还黑着）——时间状语不承接前文",
        [r"^这会儿", r"^今早", r"^天还黑着", r"^天刚亮", r"^天还没亮",
         r"^天擦黑", r"^这会儿天", r"^这阵子", r"^这年头"],
    )),
    ("WEATHER_ABSTRACT", (
        "抽象天气开场（雨还在下／檐下／风里）——10-24 峰值 1011 已压住，"
        "留族防回流",
        [r"^雨还在下", r"^檐下", r"^雨停了", r"^风里", r"^天阴沉",
         r"^云压得低"],
    )),
    ("PROP_DEICTIC", (
        "器物指示开场（那台／那口／那架／这把 + 物件状态）——2026-11-13 实测"
        "154/552=27.9% 已越 25% 配额且无闸。出生地可追：HAND 族被压住后，同提示词"
        "的逃生示例正是「写一件物的状态（那口锅底又薄了一层）」，模型照抄示例形状"
        "（今日「那口锅底又薄」18 条、「那台老收音机」24 条）。族按形状判，不按词义："
        "一句「那口锅」合法，全天近三成居民从指示代词起句才是病（R2581 同判据）。",
        [r"^那[台口架把扇盏辆本件个只座棵张块根条片串副支]",
         r"^这[台口架把扇盏辆本件个只座棵张块根条片串副支]"],
    )),
    ("BOOK_LEDGER_DEICTIC", (
        "账簿翻页开场（账本／账簿 + 翻到第X页）——v1.3 2026-11-13 R2787 实测"
        "新生吸引子：2026-11-12 首现 33/729=4.5%、11-13 31/552=5.6%，且 31 条里"
        "30 条逐字同句「账本翻到第三页，」。曲线与 HAND 族同形（10-19 0.0% →"
        "11-12 42.2%），按 T-20261112-04 判据在其出生日截获，不等到占三成再回溯。"
        "族按形状判：一句翻账本合法，全天多人从同一页起句才是病。",
        [r"^账本", r"^账簿"],
    )),
    ("RAIN_SETTING_DEICTIC", (
        "雨天具象布景开场（雨水顺着X／檐口的水线／雨脚／雨敲窗棂）——v1.4 "
        "2026-11-13 R2789 实测新生吸引子：11-12 5/729=0.7% → 11-13 15/552=2.7%，"
        "一日 3 倍。与 WEATHER_ABSTRACT 的分界＝抽象天气断言（雨还在下／风里／天阴沉）"
        "由旧族承担，本族只收「降水落到具体物件上」的布景形状；单句合法，"
        "全天多人在开头搭同一套雨景才是病（与 HAND/PROP 同判据）。"
        "15 条实测分布：檐口的水线 5／雨水顺着瓦沟 3／雨脚细细密密 2／雨敲在窗棂上 2／"
        "雨点没停 1——同形状不同词，故按「物件+降水共现」判，不按整句锁。",
        [r"^雨水", r"^雨脚", r"^雨敲", r"^雨点", r"^雨丝", r"^雨声",
         r"^雨幕", r"^细雨", r"^小雨", r"^檐口.{0,8}(水|滴|雨)",
         r"^瓦沟.{0,8}(水|雨)", r"^窗棂.{0,8}(雨|水|响)"],
    )),
])

_COMPILED = collections.OrderedDict(
    (name, [re.compile(p) for p in pats]) for name, (_, pats) in FAMILIES.items())

# 第二句吸引子（只读探针·不入闸）：开头族被压住后模型通常把吸引子往
# 后一段迁移，R2581 的 20 条人读已实证（风…掀/灌/扑 + 像谁在…）。
# 只观测不拒稿——先有读数再谈立法（避免修一个生一个的连环闸）。
SECOND_ATTRS = collections.OrderedDict([
    ("WIND_ACTION", ("风+掀/灌/扑/刮/撞/扯/吹（第二句起）",
                     [r"风[^。]{0,8}(掀|灌|扑|刮|撞|扯|吹)"])),
    ("SIMILE_WHO", ("比况从句「像谁在…」（第二句起）",
                    [r"像谁在"])),
])

_SECOND_COMPILED = collections.OrderedDict(
    (name, [re.compile(p) for p in pats]) for name, (_, pats) in SECOND_ATTRS.items())

# T-20261112-05 (2026-11-12 R2586): 第二句面从「只观测」升到「软引导」。
# 依据 R2582 实测 WIND_ACTION 3.3%(10-20)→49.9%(11-12)，与开头族 42.8% 同量级，
# 即开头被压住后吸引子后移一格。两条刻意保留的区别：
#   ① 只走提示词（prompt steering），不拒稿——第二句面误杀代价远高于开头
#      （合法天气描写、合法比况都会命中），R2581 立的「先有读数再谈立法」也未到期；
#   ② 线定 40% 而非开头族的 25%——软引导只需在明显越线时点名，避免每轮碎碎念
#      把模型逼成不敢写天气。
SECOND_QUOTA = 0.40
SECOND_LABELS = collections.OrderedDict([
    ("WIND_ACTION", "用风来带出动作（风掀／风灌／风扑／风刮／风撞／风扯／风吹…）"),
    ("SIMILE_WHO", "「像谁在…」式的比况从句"),
])


def second_ban_set(total, hits, quota=SECOND_QUOTA, min_denom=FAMILY_MIN_DENOM):
    """第二句吸引子软引导集合：返回越线族名（只喂提示词，永不用于拒稿）。

    total 不足 min_denom -> 空集（小样本噪声保护，与开头族同口径）。
    """
    if int(total or 0) < min_denom:
        return set()
    return {f for f, c in (hits or {}).items()
            if c / float(total) > quota}


def second_label(name):
    """族名 -> 提示词里可直接点名的一句人话（未知族退化为族名本身）。"""
    return SECOND_LABELS.get(name, name)


def norm(text):
    """去空白后取前 12 字，与 evolve_citizen 的开头口径一致。"""
    return re.sub(r"\s+", "", text or "")[:OPENING_LEN]


def family_of(text):
    """返回开头所属骨架族名；不属于任何族 → None。

    只匹配开头（norm 后的前 12 字），所以「她把信折好，手心的汗」这类
    句中合法身体描写永不命中——这是负控探针 2 的契约。
    """
    op = norm(text)
    if len(op) < 2:
        return None
    for name, pats in _COMPILED.items():
        for p in pats:
            if p.match(op):
                return name
    return None


def _ring_pat(day):
    return re.compile(r"- " + re.escape(day) + r" 「([^」]{8,})」")


def scan_day(day, registry=None):
    """扫描某日全部年轮 → (总数, {族: 命中数})。

    registry 缺失或为空 → (0, {})，调用方据此关闭闸（零漂移）。
    """
    root = registry or REGISTRY
    pat = _ring_pat(day)
    total = 0
    fam = collections.Counter()
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            for m in pat.finditer(s):
                body = m.group(1)
                if len(re.sub(r"\s+", "", body)) < 8:
                    continue
                total += 1
                f = family_of(body)
                if f:
                    fam[f] += 1
    return total, dict(fam)


# v1.1 (2026-11-13 R2685, T-20261112-01 归因面): 年轮来源拆分。
# R2586 记「247 环按来源（evolve 批/meet/reflect）拆分开口族归属」待办；
# 实读 evolve_citizen 后改正口径：reflect 写的是卡面「反思」段（add_reflection），
# 不落年轮行，故年轮来源只有两类——批量日更（--batch）与相遇（--meet，行首
# 固定「与 C-xxxxx 相遇：」）。归因只读、确定性，不改任何闸判定。
MEET_RE = re.compile(r"与\s*C-\d+\s*相遇[：:]")
SOURCE_ORDER = ("batch", "meet")


def source_of(body):
    """年轮正文 → 来源名（meet／batch）。meet 行首由 evolve_citizen 固定拼出。"""
    return "meet" if MEET_RE.search(body or "") else "batch"


def scan_day_by_source(day, registry=None):
    """按来源拆分某日年轮 → {来源: {"total": n, "families": {族: n}}}。

    与 scan_day 同口径（同正则、同 8 字下限），故各来源 total 之和恒等于
    scan_day 的 total——调用方可据此自校验（_selftest 有断言）。
    """
    root = registry or REGISTRY
    pat = _ring_pat(day)
    out = collections.OrderedDict(
        (s, {"total": 0, "families": collections.Counter()}) for s in SOURCE_ORDER)
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            for m in pat.finditer(s):
                body = m.group(1)
                if len(re.sub(r"\s+", "", body)) < 8:
                    continue
                slot = out[source_of(body)]
                slot["total"] += 1
                f = family_of(body)
                if f:
                    slot["families"][f] += 1
    return collections.OrderedDict(
        (k, {"total": v["total"], "families": dict(v["families"])})
        for k, v in out.items())


def second_attrs_of(text):
    """返回正文「开头 12 字之后」命中的第二句吸引子集合（只读探针用）。"""
    tail = re.sub(r"\s+", "", text or "")[OPENING_LEN:]
    return [name for name, pats in _SECOND_COMPILED.items()
            if any(p.search(tail) for p in pats)]


def second_scan(day, registry=None):
    """按日统计「第二句起」的吸引子占比 → (环总数, {族: 命中数})。

    只取开头 12 字之后的正文，故开头位置命中不计入（与 scan_day 分工不重叠）。
    只读观测：不参与 any ban 判定，失败不影响生产。
    """
    root = registry or REGISTRY
    pat = _ring_pat(day)
    total = 0
    hits = collections.Counter()
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            for m in pat.finditer(s):
                body = re.sub(r"\s+", "", m.group(1))
                if len(body) < 8:
                    continue
                total += 1
                for name in second_attrs_of(body):
                    hits[name] += 1
    return total, dict(hits)


def scan_days(days, registry=None):
    """批量按日扫描 → [(day, total, {fam: n})]。"""
    return [(d,) + scan_day(d, registry) for d in days]


def production_days(limit=14, registry=None, today=None):
    """registry 内有年轮产出的最近 limit 个日期（升序）。"""
    root = registry or REGISTRY
    seen = set()
    pat = re.compile(r"- (\d{4}-\d{2}-\d{2}) 「[^」]{8,}」")
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            try:
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    s = f.read()
            except (IOError, OSError):
                continue
            seen.update(pat.findall(s))
    out = sorted(seen)
    if today:
        out = [d for d in out if d <= today]
    return out[-limit:]


def over_quota(total, fam, quota=FAMILY_QUOTA, min_denom=FAMILY_MIN_DENOM):
    """返回超过配额的族列表（total 不足 min_denom 时一律空=不判）。"""
    if total < min_denom:
        return []
    return sorted(f for f, c in (fam or {}).items() if c / float(total) > quota)


def unclassified(total, fam):
    """未归族环数与占比 → (n, pct)。只读观测，不参与任何闸判定。

    判例 R2760/R2762（2026-11-13）：PROP_DEICTIC 立族前，「那台老收音机…」
    「这把旧扳手…」起句 87 条全部落进 family_of=None，配额闸看不见它们——
    当日手部族真占比 40.0% 被读成 25%。补族表是对症，但下一种新句式出现时
    同样会隐身，故把盲区份额做成每轮可读的读数（族表覆盖率的回归看守），
    而非等人眼再发现一次。
    """
    if not total or total <= 0:
        return 0, 0.0
    known = sum((fam or {}).values())
    n = max(0, int(total) - int(known))
    return n, n / float(total) * 100


def ban_set_from_openings(openings, quota=FAMILY_QUOTA, min_denom=FAMILY_MIN_DENOM):
    """由 {opening12: count} 台账算出应禁族集合（evolve_citizen 批内直接消费）。

    复用当日开头台账，避免二次扫盘（~1.9s/10k 卡）。
    """
    total = 0
    fam = collections.Counter()
    for op, c in (openings or {}).items():
        try:
            c = int(c)
        except (TypeError, ValueError):
            continue
        if c <= 0:
            continue
        total += c
        f = family_of(op)
        if f:
            fam[f] += c
    return set(over_quota(total, dict(fam), quota=quota, min_denom=min_denom))


def note_epoch(day=None, epoch=None, ts=None):
    """批起登记「当日生产用的是哪版族表」→ state/ring-family-epochs.json。

    幂等：同日同 epoch 只记一行（值=首见时间戳）。只记账面，不参与闸判定；
    落盘失败一律吞掉（观测面失败不阻塞生产，同 evolve_citizen 观测面律）。
    返回既有 epoch 列表（升序）。
    """
    day = day or datetime.date.today().isoformat()
    epoch = epoch or TABLE_EPOCH
    ts = ts or datetime.datetime.now().isoformat(timespec="seconds")
    data = {}
    try:
        with open(EPOCH_LOG, encoding="utf-8") as f:
            data = json.load(f) or {}
    except (IOError, OSError, ValueError):
        data = {}
    rows = data.setdefault(day, [])
    if not any(r.get("epoch") == epoch for r in rows):
        rows.append({"epoch": epoch, "first_seen": ts})
    try:
        os.makedirs(os.path.dirname(EPOCH_LOG), exist_ok=True)
        with open(EPOCH_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    except (IOError, OSError, ValueError):
        pass
    return [r.get("epoch") for r in rows]


def epochs_of(day):
    """某日生产期用过的族表版本列表（无记录 → []，早于守卫上线）。"""
    try:
        with open(EPOCH_LOG, encoding="utf-8") as f:
            data = json.load(f) or {}
    except (IOError, OSError, ValueError):
        return []
    return [r.get("epoch") for r in (data.get(day) or []) if r.get("epoch")]


def epoch_mix_state(day_epochs, current_epoch=None):
    """某日纪元面与当前族表的口径关系（纯函数·只读·供 --check 与自测）。

    'none'         当日无登记（守卫上线前，或立族后漏跑 note_epoch）
    'multi'        当日登记 ≥2 个版本（确定跨口径：读数混有立族前出生的环）
    'curr-missing' 当日有登记但当前族表版本不在其中（旧表出生＋新表立族/漏记）
    'single'       当日只用一版且正合当前表（同口径，可直接与配额线对账）

    为何要与 'multi' 分开：只按「登记数 > 1」判会漏掉「立族后忘记登记」这一类——
    当日登记仍是一条旧版本，占比却已混入新表重分类，正是 R2789 立族后的实况。
    """
    eps = [e for e in (day_epochs or []) if e]
    if not eps:
        return "none"
    if len(eps) > 1:
        return "multi"
    cur = current_epoch or TABLE_EPOCH
    return "single" if cur in eps else "curr-missing"


def check_verdict(mix_state, over):
    """--check 三态判定（纯函数·供 --check 与自测）。

    混口径日（multi／curr-missing／none）的占比跨两版族表，报 OVER 会把
    「历史环被新表重分类」误植成「本轮生产越线」→ 一律 CROSS-EPOCH（不可比、不阻断）。
    只有同口径（single）才允许判 OVER／PASS。
    """
    if mix_state != "single":
        return "CROSS-EPOCH"
    return "OVER" if over else "PASS"


def _production(registry=None):
    root = registry or REGISTRY
    pat = re.compile(r"- (\d{4}-\d{2}-\d{2}) 「([^」]{8,})」")
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
            for m in pat.finditer(s):
                rows.append((m.group(1), m.group(2)))
    return sorted(rows)


def _selftest():
    """负控四探针 + 正控两探针。任一不符 → rc=1。"""
    probes = [
        # (标签, 文本, 期望族)
        ("neg-catchphrase", "这城里好玩的东西一天比一天多，我在巷口又碰见老周。", None),
        ("neg-body-midsentence", "她把信折好放进铁盒，手心的汗把纸洇了一小块。", None),
        ("neg-legit-hand-detail", "第三道钉星的路还留着昨夜的汗。", None),
        ("neg-hand-not-at-opening", "灯芯爆了一下，手在灯罩上停了停。", None),
        ("pos-hand-skeleton", "手在楼梯扶手上摩挲，木头被磨得发亮。", "HAND_DEICTIC"),
        ("pos-time-skeleton", "今早的天还没亮透，江面就起了雾。", "TIME_OPEN"),
        # R2760（2026-11-13）：^手里 盲区补全——实测「手里/手中的」起句 87 条，
        # 旧族只认 手上/手边/手头/手心，与 R2608 的「手边」漏判同型。
        ("pos-hand-in-palm", "手里的铁夹还带着余温，我把它放回工具箱。", "HAND_DEICTIC"),
        # 器物指示族（PROP_DEICTIC）三探针：开头正例／句中不误伤／非首句位置不误伤。
        ("pos-prop-deictic", "那台老收音机搁在门板上，铜皮边角已磨出毛边。", "PROP_DEICTIC"),
        ("pos-prop-this", "这把旧扳手我用了九年，柄上的胶布换过三回。", "PROP_DEICTIC"),
        ("neg-prop-midsentence", "灯芯爆了一下，那台老收音机又跳了个台。", None),
        ("neg-prop-body", "我把信折好放进铁盒，那口锅还在灶上咕嘟着。", None),
        # 账簿族（BOOK_LEDGER_DEICTIC·v1.3）两组探针：开头正例 / 句中不误伤。
        ("pos-book-ledger", "账本翻到第三页，雨声在铁皮上敲得急。", "BOOK_LEDGER_DEICTIC"),
        ("neg-book-midsentence", "她把账本合上，第三页的墨迹还没干透。", None),
        # 雨天布景族（RAIN_SETTING_DEICTIC·v1.4）四探针：物件+降水正例 /
        # 抽象天气旧族不被抢（^雨还在下 仍归 WEATHER_ABSTRACT）/ 句中不误伤 /
        # 无降水的檐口描写不误伤（檐口的蜘蛛网）。
        ("pos-rain-eaves", "檐口的水线一直往下淌，风把雨棚掀得啪啪响。", "RAIN_SETTING_DEICTIC"),
        ("pos-rain-gutter", "雨水顺着瓦沟流，我正把一件件货往里头挪。", "RAIN_SETTING_DEICTIC"),
        ("pos-rain-abstract-keeps", "雨还在下，铁皮棚上的动静一天没停。", "WEATHER_ABSTRACT"),
        ("neg-rain-midsentence", "她把伞收好，雨水顺着瓦沟流到脚边。", None),
        ("neg-rain-eaves-norain", "檐口的蜘蛛网挂了一整年，没人上去扫。", None),
    ]
    bad = 0
    for label, text, want in probes:
        got = family_of(text)
        ok = got == want
        print("%-24s got=%-16s want=%-16s %s" % (label, got, want, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # 台账口径正控：42% 手族当日必须判 over
    fake = {"手在楼梯扶手上摩挲": 42, "今早的天还没亮透": 8, "这城里好玩的东西一天比一天多": 50}
    bans = ban_set_from_openings(fake)
    live = "HAND_DEICTIC" in bans
    print("%-24s bans=%s %s" % ("pos-ledger-quota", sorted(bans), "OK" if live else "FAIL"))
    if not live:
        bad += 1
    # 小样本不判：3 环全手族仍应放行（噪声保护）
    tiny = ban_set_from_openings({"手在楼梯扶手上摩挲": 3, "手上的老茧": 1})
    ok = not tiny
    print("%-24s bans=%s %s" % ("neg-tiny-denominator", sorted(tiny), "OK" if ok else "FAIL"))
    if not ok:
        bad += 1
    # 第二句探针：只认开头 12 字之后的正文（与开头口径不重叠）
    sec_probes = [
        ("pos-second-wind", "手在灯管上蹭了蹭，抬手抹了下额角，风把门帘整个掀起来，巷子里全是油烟。", ["WIND_ACTION"]),
        ("pos-second-simile", "手心还攥着旧扳手，风把檐下的灯笼摇个不停，像谁在背后推我。",
         ["SIMILE_WHO"]),
        ("neg-wind-at-opening", "风把门帘整个掀起来，我赶紧把窗关好，热气散了一半。", []),
    ]
    for label, text, want in sec_probes:
        got = second_attrs_of(text)
        ok = got == want
        print("%-24s got=%-24s want=%-24s %s"
              % (label, ",".join(got) or "None", ",".join(want) or "None",
                 "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # T-20261112-05 软引导配额三探针：越线点名／未越线沉默／小样本不判
    quota_probes = [
        ("pos-second-quota-over", 100, {"WIND_ACTION": 50}, {"WIND_ACTION"}),
        ("neg-second-quota-under", 100, {"WIND_ACTION": 20}, set()),
        ("neg-second-tiny-denom", 4, {"WIND_ACTION": 4}, set()),
    ]
    for label, tot, hits, want in quota_probes:
        got = second_ban_set(tot, hits)
        ok = got == want
        print("%-24s bans=%-20s want=%-20s %s"
              % (label, ",".join(sorted(got)) or "None",
                 ",".join(sorted(want)) or "None", "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # R2762 盲区读数探针：未归族 = total - 已归族之和；只读，不进 any 闸判定。
    _uc_probes = [
        ("pos-unclass-none", 100, {"HAND_DEICTIC": 40}, (60, 60.0)),
        ("pos-unclass-partial", 552, {"HAND_DEICTIC": 221, "PROP_DEICTIC": 171}, (160, 29.0)),
        ("neg-unclass-empty", 0, {}, (0, 0.0)),
    ]
    for label, tot, fam, want in _uc_probes:
        _n, _p = unclassified(tot, fam)
        got = (_n, round(_p, 1))
        ok = got == want
        print("%-24s got=%-18s want=%-18s %s" % (label, got, want, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # T-20261112-01 归因面探针：meet 行识别正例／日更行不误判；
    # 且按来源拆分之和必须与 scan_day 同口径守恒。
    src_probes = [
        ("pos-source-meet", "与 C-00044 相遇：我们在旧站台聊了半宿，雨声替我们数着话头。", "meet"),
        ("neg-source-batch", "手在楼梯扶手上摩挲，木头被磨得发亮。", "batch"),
        ("neg-source-meet-in-body", "她说起与 C-07991 相遇那晚，灯一直没熄。", "batch"),
    ]
    for label, text, want in src_probes:
        got = source_of(text)
        ok = got == want
        print("%-24s got=%-12s want=%-12s %s" % (label, got, want, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # R2790 纪元口径四态探针（纯函数·定值·不碰真件）：
    # 只按「登记数>1」判的老写法会漏掉「立族后漏记」——当日仅一条旧版本，
    # 读数却已混入新表重分类（R2789 15:38 v1.4 立族实况）。
    _ep_probes = [
        ("neg-epoch-none", [], "2026-11-13T15:38", "none"),
        ("pos-epoch-multi", ["2026-11-13T12:09", "2026-11-13T15:38"], "2026-11-13T15:38", "multi"),
        ("pos-epoch-curr-missing", ["2026-11-13T12:09"], "2026-11-13T15:38", "curr-missing"),
        ("neg-epoch-single", ["2026-11-13T15:38"], "2026-11-13T15:38", "single"),
    ]
    for label, eps, cur, want in _ep_probes:
        got = epoch_mix_state(eps, cur)
        ok = got == want
        print("%-24s got=%-14s want=%-14s %s" % (label, got, want, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    # 三态判定探针：混口径一律 CROSS-EPOCH（不阻断），同口径才按越线判 OVER/PASS。
    _vd_probes = [
        ("pos-verdict-over", "single", ["HAND_DEICTIC"], "OVER"),
        ("neg-verdict-pass", "single", [], "PASS"),
        ("pos-verdict-cross-multi", "multi", ["HAND_DEICTIC"], "CROSS-EPOCH"),
        ("pos-verdict-cross-missing", "curr-missing", ["HAND_DEICTIC"], "CROSS-EPOCH"),
        ("neg-verdict-cross-none", "none", ["HAND_DEICTIC"], "CROSS-EPOCH"),
    ]
    for label, mix, over, want in _vd_probes:
        got = check_verdict(mix, over)
        ok = got == want
        print("%-24s got=%-14s want=%-14s %s" % (label, got, want, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    days = production_days(3)
    if days:
        d = days[-1]
        per = scan_day_by_source(d)
        total, _fam = scan_day(d)
        s = sum(v["total"] for v in per.values())
        ok = s == total
        print("%-24s %d==%d %s" % ("pos-source-sum-" + d, s, total, "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    print("selftest: %s (%d fail)" % ("PASS" if bad == 0 else "FAIL", bad))
    return 0 if bad == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="年轮开头骨架族配额闸（确定性·零 LLM）")
    ap.add_argument("--scan", action="store_true", help="按生产日打印各族占比表")
    ap.add_argument("--days", type=int, default=14, help="扫描最近 N 个生产日")
    ap.add_argument("--check", metavar="DATE", help="判某日是否超配额（PASS/OVER）")
    ap.add_argument("--json", action="store_true", help="--scan/--check 输出 JSON")
    ap.add_argument("--sample", type=int, metavar="N", help="抽 N 条某族年轮供人读")
    ap.add_argument("--second", action="store_true",
                    help="第二句吸引子只读探针（只观测不拒稿）")
    ap.add_argument("--family", default="HAND_DEICTIC", help="--sample 的族名")
    ap.add_argument("--day", help="--sample 限定日期")
    ap.add_argument("--seed", type=int, default=0, help="--sample 抽样种子（默认按日期）")
    ap.add_argument("--by-source", metavar="DATE",
                    help="按来源（batch 日更／meet 相遇）拆分某日开口族占比")
    ap.add_argument("--selftest", action="store_true", help="负控/正控探针")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.by_source:
        per = scan_day_by_source(args.by_source)
        total, fam = scan_day(args.by_source)
        if args.json:
            print(json.dumps({"date": args.by_source, "total": total,
                              "families": {f: fam.get(f, 0) for f in FAMILIES},
                              "by_source": per, "quota": FAMILY_QUOTA,
                              "verdict": "OVER" if over_quota(total, fam) else "PASS"},
                             ensure_ascii=False, indent=1))
            return 0
        print("date=%s rings=%d (by source, quota=%.0f%%)"
              % (args.by_source, total, FAMILY_QUOTA * 100))
        for src, d in per.items():
            t = d["total"]
            cells = []
            for f in FAMILIES:
                c = d["families"].get(f, 0)
                cells.append("%s=%d(%.1f%%)" % (f, c, c / t * 100 if t else 0.0))
            _su, _sup = unclassified(t, d["families"])
            print("  %-6s rings=%4d  %s  unclass=%d(%.1f%%)"
                  % (src, t, "  ".join(cells), _su, _sup))
        sum_src = sum(d["total"] for d in per.values())
        print("  sum(by source)=%d vs scan_day=%d %s"
              % (sum_src, total, "OK" if sum_src == total else "MISMATCH"))
        over = over_quota(total, fam)
        print("verdict: %s" % (("OVER:" + ",".join(over)) if over else "PASS"))
        return 0

    if args.check:
        total, fam = scan_day(args.check)
        over = over_quota(total, fam)
        _ep = epochs_of(args.check)
        _mix = epoch_mix_state(_ep)
        # 混口径日（立族当天的环跨越两版族表）→ 占比不可与 25% 线对账：
        # 报 OVER 会把「历史环被新表重分类」误植成「本轮生产越线」（R2789 实况）。
        # 故三态：PASS／OVER／CROSS-EPOCH；CROSS-EPOCH 不阻断（rc=0）但明标不可比。
        _comparable = _mix == "single"
        _verdict = check_verdict(_mix, over)
        detail = {f: (fam.get(f, 0), round(fam.get(f, 0) / total * 100, 1) if total else 0.0)
                  for f in FAMILIES}
        _uc_n, _uc_pct = unclassified(total, fam)
        if args.json:
            print(json.dumps({"date": args.check, "total": total, "families": detail,
                              "over": over, "quota": FAMILY_QUOTA,
                              "unclassified": {"n": _uc_n, "pct": round(_uc_pct, 1)},
                              "table_epoch": TABLE_EPOCH, "epochs": _ep,
                              "epoch_mix": _mix, "quota_comparable": _comparable,
                              "verdict": _verdict},
                             ensure_ascii=False, indent=1))
        else:
            print("date=%s rings=%d quota=%.0f%%" % (args.check, total, FAMILY_QUOTA * 100))
            for f, (c, pct) in detail.items():
                _mark = ""
                if f in over:
                    _mark = "  <- OVER" if _comparable else "  <- 越线(跨口径·不可比)"
                print("  %-18s %5d  %5.1f%%%s" % (f, c, pct, _mark))
            print("  %-18s %5d  %5.1f%%  (盲区：未被任何族识别)" % ("unclassified", _uc_n, _uc_pct))
            if _mix == "multi":
                print("  口径：族表当日变更 %d 次 %s → 占比跨口径，"
                      "勿与配额线直接对账（本日读数混有立族前出生的环）"
                      % (len(_ep), ",".join(_ep)))
            elif _mix == "curr-missing":
                print("  口径：当前族表 %s 未在本日生产期登记（当日登记 %s）→ "
                      "读数含立族前出生的环（或立族后漏跑 note_epoch），"
                      "勿与配额线直接对账" % (TABLE_EPOCH, ",".join(_ep)))
            elif _mix == "none":
                print("  口径：本日无族表版本登记（守卫 v1.2 之前的日子）→ 与当前族表同口径不可假设")
            print("verdict: %s" % _verdict)
        return 2 if (_comparable and over) else 0

    if args.scan:
        days = production_days(args.days)
        rows = scan_days(days)
        names = list(FAMILIES)
        if args.json:
            print(json.dumps([{"date": d, "total": t, "families": f,
                               "over": over_quota(t, f),
                               "unclassified": {"n": unclassified(t, f)[0],
                                                "pct": round(unclassified(t, f)[1], 1)}}
                              for d, t, f in rows],
                             ensure_ascii=False, indent=1))
            return 0
        print("date        rings  " + "  ".join("%-18s" % n for n in names))
        for d, t, f in rows:
            cells = []
            for n in names:
                c = f.get(n, 0)
                cells.append("%-18s" % ("%d(%.1f%%)" % (c, c / t * 100 if t else 0.0)))
            flag = "  OVER:" + ",".join(over_quota(t, f)) if over_quota(t, f) else ""
            _un, _up = unclassified(t, f)
            print("%s  %5d  %s%s  unclass=%d(%.1f%%)"
                  % (d, t, "  ".join(cells), flag, _un, _up))
        return 0

    if args.second:
        days = [args.day] if args.day else production_days(args.days)
        rows = [(d,) + second_scan(d) for d in days]
        names = list(SECOND_ATTRS)
        if args.json:
            print(json.dumps([{"date": d, "rings": t, "second": h} for d, t, h in rows],
                             ensure_ascii=False, indent=1))
            return 0
        print("second-position attractors (read-only, no gate)")
        print("date        rings  " + "  ".join("%-22s" % n for n in names))
        for d, t, h in rows:
            cells = ["%-22s" % ("%d(%.1f%%)" % (h.get(n, 0), h.get(n, 0) / t * 100 if t else 0.0))
                     for n in names]
            print("%s  %5d  %s" % (d, t, "  ".join(cells)))
        return 0

    if args.sample:
        rows = _production()
        if args.day:
            rows = [r for r in rows if r[0] == args.day]
        pool = [r for r in rows if family_of(r[1]) == args.family]
        seed = args.seed or (int(args.day.replace("-", "")) if args.day else 0)
        rnd = random.Random(seed)
        pick = pool if len(pool) <= args.sample else rnd.sample(pool, args.sample)
        print("family=%s pool=%d sampled=%d" % (args.family, len(pool), len(pick)))
        for i, (d, body) in enumerate(pick, 1):
            print("%2d. %s  %s" % (i, d, body))
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
