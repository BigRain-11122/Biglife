#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mood_director.py v1.0 — 城市情绪导演引擎（T-20260924-16c·契约=cognition/MOOD-DIRECTOR.md v1.0）

按时段+事件密度确定性编排全城情绪曲线（纪念日/坏消息日）——城市有了集体心情，
个体台词桶与聚光灯上限随之偏移。导演态只调城市面参数，永不改个体人设（人设权 CEO 保留席零触碰）。
零 LLM 零 API 纯确定性：mood=f(日期,时段,事件密度)，桶抽签全 md5 派生
（python hash() 进程随机化禁用=behavior.py/rumor_chain.py 同律）。
按需调用面（非 R3 再生面·不入 census/export）·FluxVerse 事件流只读零写回。
法源=cph4/research/R-20260924-silicon-aliveness §四增量 4+集团 P-75 ~21:45 点名（消费面向）。
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))
DEFAULT_CALENDAR = os.path.join(CO, "cognition", "mood-calendar.json")

ENGINE_V = "v1.0"
MOODS = ("steady", "lively", "festive", "somber", "hushed")
SOMBER_KINDS = ("typhoon", "gale", "storm")
DENSE_DEFAULT = 12
SPOT_MIN, SPOT_TOP = 24, 40      # 聚光灯浮动带 [24,40]·上顶 40=正典聚光灯律·只可收紧永不越顶
W_MIN, W_MAX = 0.5, 2.0          # 权重乘子闭集有界（契约 §三.1）

# 消费参数一：每态一张语境桶权重表（键域=draw.py CONTEXTS 12 桶·乘子∈[0.5,2.0]·全参数化留 CEO 一句话翻案面）
WEIGHTS = {
    "steady":  {},                                    # 平日基调=零漂移（无桶升权→抽签恒返事实桶）
    "lively":  {"market_open": 2.0},                  # 事件密集=市集喧嚣感
    "festive": {"festival": 2.0, "market_open": 2.0}, # 纪念日（契约 §三.1 示例）
    "somber":  {"night": 2.0, "market_open": 0.5},    # 坏消息日（契约 §三.1 示例·夜桶升/市集桶降）
    "hushed":  {"night": 2.0},                       # 深夜静城
}
# 消费参数二：聚光灯上限浮动（每态一值·∈[24,40]·只可收紧永不越顶）
SPOTLIGHT_MAX = {"steady": SPOT_TOP, "lively": SPOT_TOP, "festive": SPOT_TOP,
                 "somber": 32, "hushed": SPOT_MIN}


def m_int(*parts):
    return int(hashlib.md5("|".join(str(p) for p in parts).encode("utf-8")).hexdigest(), 16)


def load_calendar(path=None):
    """纪念日表（cognition/mood-calendar.json）：表行必带法源指针，缺=拒收（禁编造纪念日·诚实律）。"""
    with open(path or DEFAULT_CALENDAR, encoding="utf-8") as f:
        cal = json.load(f)
    rows = cal.get("festivals") if isinstance(cal, dict) else cal
    if not isinstance(rows, list):
        sys.exit("error: mood-calendar 须为对象含 festivals 数组")
    out = []
    for row in rows:
        date, src = str(row.get("date") or "").strip(), str(row.get("source") or "").strip()
        if not date or not src:
            sys.exit("error: 纪念日表行缺 date/source 法源指针（拒收）：%s" % json.dumps(row, ensure_ascii=False))
        out.append({"date": date, "name": str(row.get("name") or date), "source": src})
    return out


def hit_festival(at, rows):
    """日期命中：MM-DD 行年年如约 / YYYY-MM-DD 行年度专属。"""
    md, full = at.strftime("%m-%d"), at.strftime("%Y-%m-%d")
    for row in rows:
        if row["date"] == full or row["date"] == md:
            return row
    return None


def read_world():
    """只读实况：weather_kind+尾 24h 事件数+WEATHER_ALERT 命中
    （ts_utc 不可解析行不计——数据缺席不可核验=诚实律，不猜）。"""
    kind, count, alert = "", 0, False
    try:
        with open(os.path.join(FV_WORLD, "world-state.json"), encoding="utf-8") as f:
            st = json.load(f)
        kind = str((st.get("reality") or {}).get("weather_kind") or "")
    except Exception:
        pass
    try:
        now = datetime.now(timezone.utc)
        cut = now - timedelta(hours=24)
        with open(os.path.join(FV_WORLD, "world-events.jsonl"), encoding="utf-8", errors="replace") as f:
            for ln in f:
                try:
                    e = json.loads(ln)
                except Exception:
                    continue
                ts = str(e.get("ts_utc") or "")
                try:
                    t = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except ValueError:
                    try:
                        t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                if t >= cut:
                    count += 1
                    if str(e.get("type")) == "WEATHER_ALERT":
                        alert = True
    except Exception:
        pass
    return kind, count, alert


def deep_night(at):
    """深夜窗 00:00–05:00（含 05:00 整点·契约 §四.6 边界）。"""
    return at.hour < 5 or (at.hour == 5 and at.minute == 0)


def derive_state(at=None, events=None, dense_at=DENSE_DEFAULT, alert=False,
                 weather_kind="", calendar_rows=None, cal_path=None):
    """mood = f(日期, 时段, 事件密度)——闭集五态·优先序 somber>festive>lively>hushed>steady（负面信号优先）。"""
    at = at or datetime.now().replace(second=0, microsecond=0)
    if calendar_rows is None:
        calendar_rows = load_calendar(cal_path)
    ev = int(events) if events is not None else 0
    if alert:
        mood, source = "somber", "event:WEATHER_ALERT"
    elif weather_kind in SOMBER_KINDS:
        mood, source = "somber", "weather:%s" % weather_kind
    else:
        fest = hit_festival(at, calendar_rows)
        if fest:
            mood, source = "festive", "calendar:%s" % fest["name"]
        elif ev >= int(dense_at):
            mood, source = "lively", "density:%d>=%d" % (ev, dense_at)
        elif deep_night(at):
            mood, source = "hushed", "night-window"
        else:
            mood, source = "steady", "baseline"
    return {
        "at": at.strftime("%Y-%m-%d %H:%M"),
        "mood": mood,
        "source": source,
        "event_density": ev,
        "dense_at": int(dense_at),
        "spotlight_max": SPOTLIGHT_MAX[mood],
        "weights": dict(sorted(WEIGHTS[mood].items())),
        "engine_v": ENGINE_V,
    }


def current_state(at=None, events=None, dense_at=DENSE_DEFAULT, cal_path=None):
    """真实缺省面：真实时刻+只读实数（weather/24h 密度/警报）——消费方（draw/spotlight/回放）统一入口。
    --at/--events 注入档专供测试与消费方回放（CLI 同门）。"""
    kind, count, alert = read_world()
    return derive_state(at=at, events=(events if events is not None else count),
                       dense_at=dense_at, alert=alert, weather_kind=kind, cal_path=cal_path)


def mood_ctx_lottery(ctx, src, weights, seed_key):
    """draw --auto 桶选择加权（消费参数一接线）：只在 clock 档抽签——事件/天气/手动语境=事实门
    优先，导演不改写。候选=事实桶（承自权重·下限 0.5）+升权桶（>1.0）；抽中桶 ⊆ CONTEXTS
    12 桶=选词域 ⊆ 原桶零编造；同 seed 恒同桶。线级确定性不动：同 (id,日期,ctx)→逐字节同句。"""
    if src != "clock" or not weights:
        return ctx
    cands = [(ctx, max(float(weights.get(ctx, 1.0)), W_MIN))]
    for b in sorted(weights):
        w = float(weights[b])
        if b != ctx and w > 1.0:
            cands.append((b, w))
    if len(cands) == 1:
        return ctx
    total = sum(w for _, w in cands)
    roll = m_int("mood-lottery", seed_key) % 100000 / 100000.0 * total
    acc = 0.0
    for b, w in cands:
        acc += w
        if roll < acc:
            return b
    return ctx


def parse_at(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit("error: --at 格式 YYYY-MM-DD HH:MM")


def qc():
    """契约 §四 判据 1-6 断言电池：全过才 PASS（全派生 md5·临时注入件跑后即删）。"""
    import tempfile
    results = []

    def check(name, ok):
        results.append((name, bool(ok)))

    # ---- 判据 6 边界与优先序（先立全态用例，判据 1 复用）----
    neutral = dict(weather_kind="", alert=False)
    steady_case = dict(at=datetime(2026, 9, 23, 14, 30), events=0, dense_at=12, **neutral)
    lively_case = dict(at=datetime(2026, 9, 23, 14, 30), events=12, dense_at=12, **neutral)
    lively_night = dict(at=datetime(2026, 9, 23, 2, 0), events=12, dense_at=12, **neutral)
    hushed_case = dict(at=datetime(2026, 9, 23, 2, 0), events=0, dense_at=12, **neutral)
    hushed_edge = dict(at=datetime(2026, 9, 23, 5, 0), events=0, dense_at=12, **neutral)
    steady_edge = dict(at=datetime(2026, 9, 23, 5, 1), events=0, dense_at=12, **neutral)
    festive_case = dict(at=datetime(2026, 10, 1, 12, 0), events=0, dense_at=12, **neutral)
    somber_ev = dict(at=datetime(2026, 10, 1, 12, 0), events=0, dense_at=12,
                     weather_kind="", alert=True)
    somber_wx = dict(at=datetime(2026, 10, 1, 12, 0), events=0, dense_at=12,
                     weather_kind="typhoon", alert=False)
    under_edge = dict(at=datetime(2026, 9, 23, 14, 30), events=11, dense_at=12, **neutral)
    cases = [("steady", steady_case, "steady"), ("lively", lively_case, "lively"),
             ("hushed", hushed_case, "hushed"), ("festive", festive_case, "festive"),
             ("somber-event", somber_ev, "somber"), ("somber-weather", somber_wx, "somber")]
    for name, kw, expect in cases:
        check("mood %s" % name, derive_state(**kw)["mood"] == expect)
    check("priority lively>hushed", derive_state(**lively_night)["mood"] == "lively")
    check("hushed at 05:00", derive_state(**hushed_edge)["mood"] == "hushed")
    check("steady at 05:01", derive_state(**steady_edge)["mood"] == "steady")
    check("density 11<12 not lively", derive_state(**under_edge)["mood"] == "steady")
    check("priority somber>festive(alert)", somber_ev and derive_state(**somber_ev)["mood"] == "somber")
    check("priority somber>festive(wx)", derive_state(**somber_wx)["mood"] == "somber")
    check("priority festive>lively",
          derive_state(at=datetime(2026, 10, 1, 12, 0), events=999, dense_at=12, **neutral)["mood"] == "festive")
    check("somber source=event", derive_state(**somber_ev)["source"] == "event:WEATHER_ALERT")
    check("somber source=weather:typhoon", derive_state(**somber_wx)["source"] == "weather:typhoon")
    check("festive source=calendar", derive_state(**festive_case)["source"].startswith("calendar:"))
    check("mood closed set", all(m in MOODS for m in
                                 [derive_state(**kw)["mood"] for _, kw, _ in cases]))
    # --at 注入档全态可回放（CLI 同门 parse_at）
    check("parse_at roundtrip", parse_at("2026-10-01 12:00") == datetime(2026, 10, 1, 12, 0))
    try:
        parse_at("bad-format")
        check("parse_at reject", False)
    except SystemExit:
        check("parse_at reject", True)
    replayed = {derive_state(**kw)["mood"] for _, kw, _ in cases}
    check("--at replay covers all 5 moods", replayed == set(MOODS))

    # ---- 判据 1 确定性：全态+边界 双跑逐字节一致 ----
    all_cases = cases + [("lively-night", lively_night, "lively"), ("hushed-edge", hushed_edge, "hushed"),
                         ("steady-edge", steady_edge, "steady"), ("under-edge", under_edge, "steady")]
    for name, kw, _ in all_cases:
        a = json.dumps(derive_state(**kw), ensure_ascii=False, sort_keys=True)
        b = json.dumps(derive_state(**kw), ensure_ascii=False, sort_keys=True)
        check("determinism %s" % name, a == b)

    # ---- 判据 2 纯函数零 LLM（静态断言：生产面源码零网络调用——扫描截至 qc 段前，防自指）----
    with open(os.path.join(HERE, "mood_director.py"), encoding="utf-8") as f:
        src = f.read().split("def qc(")[0]
    for tok in ("import urllib", "from urllib", "import requests", "from requests",
                "urllib.request", "import socket", "import http"):
        check("no-network %s" % tok.strip(), tok not in src)
    check("pure fn steady==steady", derive_state(**steady_case) == derive_state(**steady_case))

    # ---- 判据 3 权重闭集有界 + 抽签双跑一致 + 选词域⊆原桶 ----
    for mood in MOODS:
        for b, w in WEIGHTS[mood].items():
            check("weight-bound %s/%s" % (mood, b), W_MIN <= float(w) <= W_MAX)
    sys.path.insert(0, HERE)
    import draw  # 惰性（draw 主径不 import 本件→零环）
    for mood in MOODS:
        check("weight-keys in CONTEXTS %s" % mood, set(WEIGHTS[mood]) <= set(draw.CONTEXTS))
        for i in range(20):
            key = "C-%05d|2026-09-23|%s" % (i, mood)
            a = mood_ctx_lottery("morning", "clock", WEIGHTS[mood], key)
            b = mood_ctx_lottery("morning", "clock", WEIGHTS[mood], key)
            check("lottery double-run %s#%d" % (mood, i), a == b)
            allowed = {"morning"} | {x for x, w in WEIGHTS[mood].items() if float(w) > 1.0}
            check("lottery domain %s#%d" % (mood, i), a in allowed and a in draw.CONTEXTS)
    # 事实门优先：event/weather/manual 档不抽签
    for src_name in ("event", "weather", "manual"):
        check("fact-gate keep %s" % src_name,
              mood_ctx_lottery("morning", src_name, WEIGHTS["festive"], "k") == "morning")
    # steady 态零漂移：无升权桶→抽签恒返事实桶
    check("steady zero-drift", all(mood_ctx_lottery(c, "clock", WEIGHTS["steady"], "k%d" % i) == c
                                  for i, c in enumerate(draw.CONTEXTS)))
    # 下限 0.5 生效：somber 态 market_open 事实桶承 0.5 权重（弱于升权桶）
    s = mood_ctx_lottery("market_open", "clock", WEIGHTS["somber"], "seed-x")
    check("somber fact-bucket weak", s in ("market_open", "night"))

    # ---- 判据 4 阈值浮动有界 ----
    for mood in MOODS:
        v = SPOTLIGHT_MAX[mood]
        check("spotlight-bound %s" % mood, SPOT_MIN <= v <= SPOT_TOP)
    check("spotlight top=40 canonical", SPOTLIGHT_MAX["steady"] == 40)
    for name, kw, _ in all_cases:
        st = derive_state(**kw)
        check("spotlight wired %s" % name, st["spotlight_max"] == SPOTLIGHT_MAX[st["mood"]])

    # ---- 判据 5 纪念日法源指针律 ----
    rows = load_calendar()
    check("calendar all-sourced", all(r["source"].strip() for r in rows))
    check("calendar 10-01 hit", (hit_festival(datetime(2026, 10, 1, 12, 0), rows) or {}).get("name") == "国庆节")
    # 年度专属行：YYYY-MM-DD 只当年命中
    yr = [{"date": "2026-05-01", "name": "测试节", "source": "测试法源"}]
    check("year-row hits own year", hit_festival(datetime(2026, 5, 1, 9, 0), yr) is not None)
    check("year-row not other year", hit_festival(datetime(2027, 5, 1, 9, 0), yr) is None)
    # 注入无指针行=拒收（QC 注入实证）
    bad_rows = ({"date": "01-01", "name": "x"}, {"date": "01-02", "name": "y", "source": " "})
    for i, bad in enumerate(bad_rows):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
            json.dump({"festivals": [bad]}, tf)
            tmp = tf.name
        try:
            load_calendar(tmp)
            check("calendar reject-no-source #%d" % i, False)
        except SystemExit:
            check("calendar reject-no-source #%d" % i, True)
        finally:
            os.unlink(tmp)

    fails = [n for n, ok in results if not ok]
    print("== mood_director --qc（契约判据 1-6 电池·%d 断言）==" % len(results))
    print("PASS %d / FAIL %d" % (len(results) - len(fails), len(fails)))
    if fails:
        print("FAILED:", ", ".join(fails))
        sys.exit(1)
    print("QC PASS")


def main():
    ap = argparse.ArgumentParser(description="城市情绪导演 v1.0（契约=cognition/MOOD-DIRECTOR.md）")
    ap.add_argument("--at", default=None, help="YYYY-MM-DD HH:MM 注入档；缺省=真实时刻")
    ap.add_argument("--events", type=int, default=None, help="24h 事件数注入档；缺省=只读实数")
    ap.add_argument("--dense-at", type=int, default=DENSE_DEFAULT)
    ap.add_argument("--calendar", default=None)
    ap.add_argument("--qc", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if args.qc:
        qc()
        return
    if args.dense_at < 1:
        sys.exit("error: --dense-at 有效域 ≥1（得 %s）" % args.dense_at)
    st = current_state(at=(parse_at(args.at) if args.at else None),
                       events=args.events, dense_at=args.dense_at,
                       cal_path=args.calendar)
    blob = json.dumps(st, ensure_ascii=False, separators=(",", ":")) + "\n"
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(blob)
        print("written:", args.out)
    else:
        sys.stdout.write(blob)


if __name__ == "__main__":
    main()
