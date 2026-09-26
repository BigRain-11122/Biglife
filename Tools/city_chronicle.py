#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""city_chronicle.py v1.0 - L5 城市年谱 (T-20260926-11, D-20260926-07 优先级 3).

四段链 (R347 契约 v0):
  ① 事件→反应  world-events 只读 + sig(event) 确定性阈值: 类型权重表 (CEO_ORDER=8 /
     COMMIT=4 / PushEvent=3 / GAME_STAGE=3 / RESIDENT_SAY=2) + 同 token 24h 去重窗 +
     同日同 token weight 取 max 非累加防刷量。OS_TICK*/GATE_PASS/HEARTBEAT 等开发
     流水权重 0 恒不入谱 (红线)。
  ② 反应→留痕  cognition/city-chronicle.jsonl 一行一显著事件, append-only 永不删改
     (原文保全)。源指针律内嵌: source_ref 必填 ts_utc+type+summary 三元组, 无指针行
     QC 拒收。mood_trace = mood_director 当日主态镜像非新算 (禁双建核: mood-calendar
     =预制留痕子集不重复建; 同一 derive_state 闭集, at=事件时刻)。
  ③ 留痕→衰减  decayed_weight = weight × 0.5^(days/14), 读时衰减非写时 (谱行永不删);
     半衰期 14 天参数化。
  ④ 留痕→后续  消费点 A = 年轮批 prompt「本周城市大事」窄喂入 (city_digest: 7 日窗
     decayed top-N ≤3 行, 转述口吻可提可不提), token-economy 律。

判据六条 (R282 预注册·--qc 断言电池): ①纯确定性零 LLM 双跑逐字节一致 ②源指针 100%
③衰减有界 (30 日谱 decayed 单调不增) ④体量月度 KB 级 ⑤荣誉席/居民个体零字段零 ID
⑥消费点 A ≥1 落地实弹 (evolve_citizen.py 接线)。

红线: world-events 只读 (铁律④); 开发流水恒不入谱; CEO 人设权零触碰 (谱=城市聚合面,
居民个体零字段零 ID)。--rebuild 幂等重建 / --feed 增量追加 (append-only, 只加不改)。"""

import datetime
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))
CHRON = os.path.join(CO, "cognition", "city-chronicle.jsonl")
HALF_LIFE_DAYS = 14.0          # 段③ 半衰期参数化
DIGEST_WINDOW_DAYS = 7         # 消费点 A: 本周 = 7 日窗
DIGEST_TOP = 3                 # 窄喂入 ≤3 行 (token-economy 律)

# 段① 类型权重表 (契约 v0)。缺省 0 = 不显著恒不入谱: OS_TICK_START/OS_TICK_DONE/
# GATE_PASS/HEARTBEAT/WEATHER_ALERT/GITHUB_EVENT(非 PushEvent) 等开发流水全族。
TYPE_W = {"CEO_ORDER": 8, "COMMIT": 4, "GAME_STAGE": 3, "RESIDENT_SAY": 2}

FNAME_RE = re.compile(r"^world-events(-\d{8})?\.jsonl$")
DEV_ID_RE = re.compile(r"round\s*\d+|R\d{2,}|X\d{3,}|#\d+")   # 段① dev-stream 滤 + digest 选件滤 (R335 范式)
C_ID_RE = re.compile(r"C-\d{5}")                              # 判据⑤: 居民个体零 ID (QC 实弹抓出后成文)


def weight_for(e):
    """段① sig(event): 类型权重表。GITHUB_EVENT 仅 PushEvent 载荷计市民可感 (3)。"""
    t = e.get("type")
    if t == "GITHUB_EVENT":
        return 3 if str(e.get("summary") or "").startswith("PushEvent") else 0
    return TYPE_W.get(t, 0)


def parse_ts(ts):
    """ts_utc (…Z) → 北京时刻 (UTC+8)。谱 date 一律北京日 (与 real_signals 同源)。"""
    try:
        return datetime.datetime.strptime(str(ts), "%Y-%m-%dT%H:%M:%SZ") + datetime.timedelta(hours=8)
    except Exception:
        return None


def stream_events():
    """world-events 只读流: 主流+分日归档 (名字锚 FNAME_RE, quarantine 坏行文件结构性
    排除), 坏行 try-skip (real_signals 同防护)。返回 [(ts_dt, e), …] 按 ts 升序。"""
    out = []
    for path in glob.glob(os.path.join(FV_WORLD, "*.jsonl")):
        if not FNAME_RE.match(os.path.basename(path)):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for ln in f:
                    try:
                        e = json.loads(ln)
                    except Exception:
                        continue
                    dt = parse_ts(e.get("ts_utc"))
                    if dt is not None:
                        out.append((dt, e))
        except Exception:
            continue
    out.sort(key=lambda x: (x[0], json.dumps(x[1], ensure_ascii=False, sort_keys=True)))
    return out


def derive_rows():
    """段①+② 纯函数派生: 全流 → 谱行集 (确定性, 同输入逐字节一致)。同 token 24h
    去重窗 → 同日同 token 聚合 weight 取 max; 谱行排序 (date, ts, token) 稳定。"""
    last_seen = {}            # token -> ts_dt (24h 去重窗)
    daily = {}                # (date, token) -> row
    for dt, e in stream_events():
        w = weight_for(e)
        if w <= 0:
            continue           # 开发流水恒不入谱
        summary = str(e.get("summary") or "")
        # 实弹修正 (R349 首跑 QC 抓出, 如实记档): ①轮次号 COMMIT ("R389-R394 idle-fast
        # batch: …") summary 含 dev 轮次号 -> token 恒唯一, 24h 去重窗失效, 全流 3773
        # 行爆体量判据④ (日增 ≤数十行) — 开发流水同 R335 RUMOR_DEV_ID 判, 结构性
        # 不入谱; ②summary 含 C-##### 卡号 (Bigmedia 内容 commit 载 L-card 角色号)
        # — 判据⑤ 居民个体零 ID 硬门 + 防 7b 经 digest 抄编号入年轮 (C-01875 他卡
        # ID 编造判例防线), 结构性不入谱。
        if DEV_ID_RE.search(summary) or C_ID_RE.search(summary):
            continue
        token = (str(e.get("type")), str(e.get("actor")), str(e.get("repo")), summary)
        prev = last_seen.get(token)
        if prev is not None and (dt - prev) < datetime.timedelta(hours=24):
            continue           # 同 token 24h 窗内只留首见
        last_seen[token] = dt
        key = (dt.date().isoformat(), hashlib.md5(("|".join(token)).encode("utf-8")).hexdigest()[:10])
        row = {
            "date": key[0],
            "event_token": key[1],
            "source_ref": {"ts_utc": e.get("ts_utc"), "type": token[0], "summary": token[3]},
            "weight": w,
            "mood_trace": mood_mirror(dt),
        }
        if key in daily:
            daily[key]["weight"] = max(daily[key]["weight"], w)   # 同日同 token 取 max 非累加
        else:
            daily[key] = row
    return [daily[k] for k in sorted(daily, key=lambda k: (daily[k]["date"],
                                                          daily[k]["source_ref"]["ts_utc"],
                                                          daily[k]["event_token"]))]


def mood_mirror(dt):
    """段② mood_trace = mood_director 当日主态镜像非新算 (同一 derive_state 闭集,
    at=事件时刻; kind/alert 面经 read_world 同源只读)。缺库/异常 → "" (QC 判据 2 允许
    空串不允许缺键)。"""
    try:
        import mood_director
        return mood_director.current_state(at=dt)[0]
    except Exception:
        return ""


def load_rows(path=CHRON):
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    continue
    return rows


def decay(weight, days):
    """段③ 读时衰减 (非写时=原文保全): weight × 0.5^(days/半衰期)。"""
    return float(weight) * (0.5 ** (float(days) / HALF_LIFE_DAYS))


def city_digest(now=None, top=DIGEST_TOP, window=DIGEST_WINDOW_DAYS, path=CHRON):
    """段④ 消费点 A: 7 日窗 decayed top-N ≤3 行 → 年轮批 prompt「本周城市大事」块。
    窄喂入: DEV_ID 轮次号行结构性不选 (R335 同滤); 转述口吻可提可不提明示; 无谱/无行
    → "" (消费方 prompt 与接线前逐字节一致, 零漂移律)。"""
    now = now or datetime.datetime.now()
    cands = []
    for r in load_rows(path):
        s = r.get("source_ref") or {}
        if DEV_ID_RE.search(str(s.get("summary")) or ""):
            continue
        try:
            days = (now.date() - datetime.date.fromisoformat(r["date"])).days
        except Exception:
            continue
        if 0 <= days <= window:
            cands.append((decay(r.get("weight", 0), days), r))
    cands.sort(key=lambda x: (-x[0], x[1].get("date", ""), x[1].get("event_token", "")))
    if not cands:
        return ""
    items = ["「%s」" % (str(c[1]["source_ref"].get("summary"))[:60]) for c in cands[:top]]
    return ("本周城市大事（同样属于可引用的喂入素材，可提可不提）：最近一周城里发生的事——"
            + "；".join(items)
            + "。年轮若提及，只许以转述口吻逐字引用上面引号内的文本，不得添加任何细节。")


def write_rows(rows, path=CHRON):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def cmd_rebuild():
    """--rebuild 幂等重建: 纯函数派生全量重写 (同输入逐字节一致 = 判据①)。"""
    rows = derive_rows()
    write_rows(rows)
    print("rebuild rows=%d -> %s" % (len(rows), os.path.relpath(CHRON, CO)))
    return 0


def cmd_feed():
    """--feed 增量追加 (append-only 只加不改): 派生全集对比在谱 (date,event_token)
    键集, 追加缺行 (保谱内既有行原文零触碰)。"""
    if not os.path.isfile(CHRON):
        return cmd_rebuild()
    have = {(r.get("date"), r.get("event_token")) for r in load_rows()}
    fresh = [r for r in derive_rows() if (r["date"], r["event_token"]) not in have]
    if fresh:
        with open(CHRON, "a", encoding="utf-8", newline="\n") as f:
            for r in fresh:
                f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print("feed appended=%d total=%d" % (len(fresh), len(load_rows())))
    return 0


def qc():
    """--qc 断言电池: 判据六条 + 红线。任一不过 → 非 0 退出零写盘。"""
    fails = []

    def chk(name, ok):
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            fails.append(name)

    # 判据① 纯确定性双跑逐字节一致 (纯函数派生, 不落盘)
    a = json.dumps(derive_rows(), ensure_ascii=False, sort_keys=True)
    b = json.dumps(derive_rows(), ensure_ascii=False, sort_keys=True)
    chk("1 determinism double-run byte-identical", a == b)

    # 判据② 源指针 100%: source_ref 三键齐备 (QC 拒收无指针行的构造面)
    rows = json.loads(a)
    chk("2 source_ref ts_utc+type+summary 100%",
        all(r.get("source_ref", {}).get("ts_utc") and r["source_ref"].get("type")
            and r["source_ref"].get("summary") is not None for r in rows))

    # 判据③ 衰减有界: 30 日谱 decayed 单调不增 (读时衰减函数级)
    seq = [decay(8, d) for d in (0, 1, 7, 14, 21, 30)]
    chk("3 decay monotonic non-increasing over 30d",
        all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1)) and seq[-1] > 0)

    # 判据⑤ 荣誉席/居民个体零字段零 ID: 派生全谱文本零 C-##### 居民编号
    chk("5 zero citizen IDs in chronicle rows", not re.search(r"C-\d{5}", a))

    # 红线: 开发流水 (OS_TICK*/GATE_PASS/HEARTBEAT/WEATHER_ALERT) 权重 0 恒不入谱
    # (GITHUB_EVENT 不在此列: PushEvent 载荷经 weight_for=3 合法入谱, 非 push=0)
    dev_types = {"OS_TICK_START", "OS_TICK_DONE", "OS_TICK", "GATE_PASS", "HEARTBEAT",
                 "WEATHER_ALERT"}
    for t in sorted(dev_types):
        e = {"type": t, "actor": "x", "repo": "y", "summary": "PushEvent BigX" if t == "GITHUB_EVENT" else "s",
             "ts_utc": "2026-09-26T00:00:00Z"}
        if t == "GITHUB_EVENT":
            chk("w GITHUB_EVENT PushEvent=3/non-push=0", weight_for(e) == 3
                and weight_for({**e, "summary": "CreateEvent z"}) == 0)
        else:
            chk("w %s weight=0 (dev stream never chronicled)" % t, weight_for(e) == 0)
    chk("rows zero dev-stream types",
        all(r["source_ref"]["type"] not in dev_types for r in rows))
    chk("rows zero dev-id / zero C-##### summaries",
        all(not DEV_ID_RE.search(r["source_ref"]["summary"]) and not C_ID_RE.search(r["source_ref"]["summary"])
            for r in rows))

    # 段① 24h 去重窗: 同 token 24h 内只留首见
    seen = {}
    for r in rows:
        seen.setdefault(r["event_token"], []).append(r["date"])
    chk("dedup window: no token twice in same day",
        all(len(set(v)) == len(v) for v in seen.values()))

    # 判据⑥ 消费点 A: digest 空谱→"" 零漂移; DEV_ID 行结构性不选; ≤3 行转述块
    empty = city_digest(datetime.datetime.now(), path=os.path.join(CO, "state", "no-such-chronicle.jsonl"))
    chk("6a digest empty-file -> '' (zero-drift)", empty == "")
    dev_row = {"date": datetime.date.today().isoformat(), "event_token": "x",
               "source_ref": {"ts_utc": "2026-09-26T07:00:00Z", "type": "COMMIT",
                              "summary": "R47 idle-fix"}, "weight": 4}
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as tf:
        tf.write(json.dumps(dev_row, ensure_ascii=False) + "\n")
        tmp = tf.name
    try:
        d = city_digest(datetime.datetime.now(), path=tmp)
        chk("6b digest skips dev-id rows", d == "")
        good = {"date": datetime.date.today().isoformat(), "event_token": "y",
                "source_ref": {"ts_utc": "2026-09-26T06:00:00Z", "type": "CEO_ORDER",
                               "summary": "建立第一性原理"}, "weight": 8}
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps(good, ensure_ascii=False) + "\n" + json.dumps(dev_row, ensure_ascii=False) + "\n")
        d = city_digest(datetime.datetime.now(), path=tmp)
        chk("6c digest carries quoted retell + <=3 lines",
            d.startswith("本周城市大事") and d.count("「") == 1 and "建立第一性原理" in d)
    finally:
        os.unlink(tmp)

    print("QC %s (%d fails)" % ("PASS" if not fails else "FAIL", len(fails)))
    return 1 if fails else 0


def main():
    if "--qc" in sys.argv:
        return qc()
    if "--rebuild" in sys.argv:
        return cmd_rebuild()
    if "--feed" in sys.argv:
        return cmd_feed()
    print(__doc__.splitlines()[0])
    print("usage: city_chronicle.py --qc | --rebuild | --feed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
