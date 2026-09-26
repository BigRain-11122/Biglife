#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""surprise_log.py v0 - 预测机 FEP-lite 惊奇日志派生件
(T-20260926-19 V3 城市议员·分步②切片②c; 契约=cognition/PROPOSALS.md §三;
数据面已 T2 登记 CODEX §十二 v3.33 — 先登记后产出律已满足)。

面: cognition/surprise-log.jsonl 每日一行 {date, events:[{token, surprise}], day_max}。
派生 (纯确定性·零 LLM·零云端·L1):
  - 事件源 = city_chronicle 同源只读 (world-events 流 + 同一显著滤律: TYPE_W>0 且
    dev-id/C-id 零命中 — 单源复用 import city_chronicle, 禁双建核);
  - 类目 token = city_chronicle.coarse_token 同款粗化 (系列粒度·城市聚合面);
  - 档位表 (md5(date) 派生): 表对 (date, 全历史流) 纯函数派生零状态, canonical 序列化
    取 md5 指纹入双跑一致断言 — 首见=3 (token 全流首现日==当日) / 罕见=2 (历史
    ≤2 个不同日) / 少现=1 (3..5 日) / 常见=0 (≥6 日);
  - 跨日冻结·当日活线: 历史 date 行永不重写 (谱语义同 chronicle append-only);
    当日行 upsert (日中事件增长如实刷新)。
判据 (--qc 断言电池): ①全流双跑逐字节一致 ②档位四档夹具实弹 (3/2/1/0)+空日行
  ③md5(date) 档位表指纹双跑一致 ④零 dev 流水类型/零 C-##### (源滤继承断言)
  ⑤surprise 域 0..3+day_max 一致 ⑥存档面 schema 三键+date 唯一+跨日行稳定
  (存档 date 重派生逐字节一致)。
红线: world-events 只读 (铁律④); 零 LLM; 荣誉席/居民个体零字段零 ID (源滤继承)。
消费: --propose (分步②b 待接线) 读本面当日惊奇分高事件加权议员候选 (§二);
本件不接新循环 (city-lab 三不条款)。"""

import datetime
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
SLOG = os.path.join(CO, "cognition", "surprise-log.jsonl")

import city_chronicle as cc  # 同源单源复用 (stream_events/weight_for/coarse_token/滤律)

RARE_MAX_DAYS = 2      # 罕见上界: 历史不同日 ≤2 → 2
UNCOMMON_MAX_DAYS = 5  # 少现上界: 3..5 → 1; ≥6 → 0 常见
DEV_TYPES = {"OS_TICK_START", "OS_TICK_DONE", "OS_TICK", "GATE_PASS", "HEARTBEAT", "WEATHER_ALERT"}


def beijing_today():
    return (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).date().isoformat()


def visible_events():
    """同源滤律 (city_chronicle 段① 同款): 显著事件=weight>0 且零 dev-id/C-id。只读。"""
    out = []
    for dt, e in cc.stream_events():
        if cc.weight_for(e) <= 0:
            continue
        s = str(e.get("summary") or "")
        if cc.DEV_ID_RE.search(s) or cc.C_ID_RE.search(s):
            continue
        out.append((dt, e))
    return out


def token_str(e):
    return "|".join(str(x) for x in cc.coarse_token(e))[:48]


def derive_all(events=None):
    """全流单遍派生: {date: (row, table_md5)} — 每日一行 (纯函数, 零时钟依赖)。"""
    events = visible_events() if events is None else events
    first_day, days, present = {}, {}, {}
    for dt, e in events:
        tok = token_str(e)
        d = dt.date().isoformat()
        if tok not in first_day or d < first_day[tok]:
            first_day[tok] = d  # 全流最小日 (事件序无关·纯函数强化)
        days.setdefault(tok, set()).add(d)
        present.setdefault(d, set()).add(tok)
    out = {}
    for d in sorted(present):
        table = {}
        for tok in present[d]:
            if first_day[tok] == d:
                table[tok] = 3  # 首见
            else:
                n = len([x for x in days[tok] if x < d])
                table[tok] = 2 if n <= RARE_MAX_DAYS else (1 if n <= UNCOMMON_MAX_DAYS else 0)
        canon = json.dumps({k: table[k] for k in sorted(table)}, ensure_ascii=False)
        md5 = hashlib.md5((d + "|" + canon).encode("utf-8")).hexdigest()
        ev = [{"token": k, "surprise": table[k]} for k in sorted(table, key=lambda k: (-table[k], k))]
        out[d] = ({"date": d, "events": ev, "day_max": max(table.values()) if table else 0}, md5)
    return out


def derive_day(target, events=None):
    """单日惊奇行 (空日=诚实零行 {events:[], day_max:0})。"""
    allr = derive_all(events)
    if target in allr:
        return allr[target]
    empty_md5 = hashlib.md5((target + "|{}").encode("utf-8")).hexdigest()
    return ({"date": target, "events": [], "day_max": 0}, empty_md5)


def row_bytes(row):
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def load_log():
    if not os.path.isfile(SLOG):
        return []
    with open(SLOG, encoding="utf-8") as f:
        return f.readlines()  # 原文行保全


def cmd_feed():
    """当日活线 upsert: 无行→append; 已有→仅当日行刷新 (历史行原文零触碰)。"""
    target = beijing_today()
    row, _ = derive_day(target)
    lines = load_log()
    out, replaced = [], False
    for ln in lines:
        try:
            if json.loads(ln).get("date") == target:
                out.append(row_bytes(row) + "\n")
                replaced = True
                continue
        except Exception:
            pass
        out.append(ln)
    if not replaced:
        out.append(row_bytes(row) + "\n")
    os.makedirs(os.path.dirname(SLOG), exist_ok=True)
    with open(SLOG, "w", encoding="utf-8", newline="\n") as f:
        f.writelines(out)
    print("feed date=%s tokens=%d day_max=%d (upsert=%s)" % (
        target, len(row["events"]), row["day_max"], "replace" if replaced else "append"))
    return 0


def cmd_show(target):
    row, md5 = derive_day(target)
    print(row_bytes(row))
    print("table_md5=" + md5)
    return 0


def qc():
    """--qc 断言电池: 判据①-⑥+红线。任一不过 → 非 0 退出零写盘。"""
    fails = []

    def chk(name, ok):
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            fails.append(name)

    today = beijing_today()

    # ① 全流双跑逐字节一致 (真实流)
    a1, a2 = derive_all(), derive_all()
    chk("1 double-run byte-identical (real stream)",
        json.dumps(a1, ensure_ascii=False, sort_keys=True) == json.dumps(a2, ensure_ascii=False, sort_keys=True))

    # ② 档位四档夹具 (首见3/罕见2/少现1/常见0) + 空日诚实零行
    T = datetime.date(2026, 9, 27)

    def mk(d, s):
        return (datetime.datetime.combine(d, datetime.time(8, 0)),
                {"type": "CEO_ORDER", "actor": "CEO", "repo": "hq", "summary": s, "ts_utc": "x"})
    fx = [mk(T, "建立甲"), mk(T, "建立乙"), mk(T, "建立丙"), mk(T, "建立丁")]  # 四档均当日在册
    fx += [mk(datetime.date(2026, 9, d), "建立乙") for d in (24, 25)]  # 罕见: 历史 2 日
    fx += [mk(datetime.date(2026, 9, d), "建立丙") for d in (20, 21, 22, 23)]  # 少现: 4 日
    fx += [mk(datetime.date(2026, 9, d), "建立丁") for d in range(1, 8)]
    row, md5 = derive_day("2026-09-27", fx)
    got = {ev["token"].split("|")[-1]: ev["surprise"] for ev in row["events"]}
    chk("2 tier fixtures 3/2/1/0 + day_max=3", got.get("建立甲") == 3 and got.get("建立乙") == 2
        and got.get("建立丙") == 1 and got.get("建立丁") == 0 and row["day_max"] == 3)
    empty, _ = derive_day("2026-09-27", [])
    chk("2b empty-day honest zero row", empty["events"] == [] and empty["day_max"] == 0)

    # ③ md5(date) 档位表指纹: 双跑一致
    _, md5b = derive_day("2026-09-27", fx)
    chk("3 table_md5 stable across double-run", md5 == md5b)

    # ④ 零 dev 流水类型 + 零 C-##### (源滤继承·真实流全量)
    r_all = json.dumps(a1, ensure_ascii=False, sort_keys=True)
    chk("4 zero dev-stream types in derived rows", not any(t + "|" in r_all for t in DEV_TYPES))
    chk("4b zero citizen IDs in derived rows", not cc.C_ID_RE.search(r_all))

    # ⑤ surprise 域 0..3 + day_max 一致 (真实流全日)
    ok5 = True
    for d, (rw, _) in a1.items():
        vals = [ev["surprise"] for ev in rw["events"]]
        if not all(0 <= v <= 3 for v in vals) or rw["day_max"] != (max(vals) if vals else 0):
            ok5 = False
    chk("5 surprise domain 0..3 + day_max consistent (all days)", ok5)

    # ⑥ 存档面: schema 三键 + date 唯一 + 跨日行稳定 (存档 date 重派生逐字节一致)
    lines = load_log()
    seen, ok_schema, stable = set(), True, True
    for ln in lines:
        try:
            r = json.loads(ln)
        except Exception:
            ok_schema = False
            break
        if set(r.keys()) != {"date", "events", "day_max"} or r["date"] in seen:
            ok_schema = False
        seen.add(r["date"])
        if r["date"] < today:
            rr, _ = derive_day(r["date"])
            if row_bytes(rr) != ln.rstrip("\n"):
                stable = False
    chk("6 log schema 3-keys + unique dates", ok_schema)
    chk("6b past-date lines stable under re-derivation", stable)

    print("QC %s (%d fails)" % ("PASS" if not fails else "FAIL", len(fails)))
    return 1 if fails else 0


def main():
    if "--qc" in sys.argv:
        return qc()
    if "--feed" in sys.argv:
        return cmd_feed()
    if "--date" in sys.argv:
        i = sys.argv.index("--date")
        if i + 1 < len(sys.argv):
            return cmd_show(sys.argv[i + 1])
    print(__doc__.splitlines()[0])
    print("usage: surprise_log.py --qc | --feed | --date YYYY-MM-DD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
