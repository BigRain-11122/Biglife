#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""interchat_ledger.py v0 - 互聊内容台账派生器 (T-20260926-18 步⑨分步①·升华律 v1.3 令文⑨).

契约 = 任务板 R425 立契行（判据预注册 R99 范式）:
  数据面 = cognition/interchat-ledger.jsonl 数据行制（append-only 永不删改·原文保全）.
  一事件一行 {date, kind, source_ref, participants, text}:
    kind 闭集 v0:
      meet_ring  = 相遇互引环（census 卡面「与 C-xxxxx 相遇：…」行·卡面原文逐字·
                   source_ref=文件:L行号 真实指针）;
      rumor_hop  = 流言链跳（rumor_chain.py 实跑产物·--feed-rumor 采集·
                   字符集 ⊆ 事件原文 ∪ 垫话闭集〔听说/好像/几〕=RUMOR-CHAIN 判据 4 同律·
                   source_ref=确定性复现指针 event_id+seed+at+hop）.
  源指针律内嵌: 无 source_ref 行 QC 拒收（city-chronicle 同律）;
  荣席零入: C-00001~03 恒排除（reserved 面不扫·feed 拒收）;
  纯确定性零 LLM: 扫描序=sorted(glob)+行序·同输入双跑逐字节一致·复跑幂等（增量去重）.

红线: census 卡面零写入（只读派生）; 荣誉席/人设权零触碰; 台账只追加不改写
（修卡后复扫=新文本落新行·旧行存史=append-only 语义）.
消费面: BigStream 素材接口（步⑨分步②·点单制）/ M2 互聊（T-20260923-01 知会族）.
"""
import argparse
import glob
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "cognition", "interchat-ledger.jsonl")
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
SCAN_DIRS = ("census/registry/*", "census/anchors")  # reserved 面法定不扫（荣席零入）
KINDS = ("meet_ring", "rumor_hop")
RESERVED = ("C-00001", "C-00002", "C-00003")  # 荣誉市民席（CEO 保留面·恒不入台账）
MEET_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) 「与 (C-\d{5}) 相遇：(.*?)」 \[锚\]")

# 单源复用 rumor_chain 常量（零双建）: 垫话闭集/数字模糊/引擎版本号
sys.path.insert(0, HERE)
try:
    import rumor_chain as RC
    PADDING_CHARS = set(RC.PADDING[0] + RC.PADDING[1] + RC.FUZZ)
    RC_ENGINE_V = RC.ENGINE_V
except Exception:  # rumor_chain 不可导入 → 拒跑（禁双建闭集副本）
    sys.exit("error: rumor_chain.py 不可导入（垫话闭集单源律）")


def row_json(r):
    """行序固定 date,kind,source_ref,participants,text（canonical 序列化）."""
    return json.dumps(r, ensure_ascii=False, separators=(",", ":"))


def build_row(kind, date, source_ref, participants, text):
    """行构造器（唯一入口）: kind 闭集/源指针律/荣席零入/ID 在册 四门不过=拒."""
    if kind not in KINDS:
        raise ValueError("kind 闭集外: %r" % kind)
    if not source_ref:
        raise ValueError("源指针律: source_ref 必填（无指针行 QC 拒收）")
    if not date or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise ValueError("date 非法: %r" % date)
    if len(participants) != 2 or not all(p for p in participants):
        raise ValueError("participants 须二元非空")
    for p in participants:
        if p in RESERVED:
            raise ValueError("荣席零入: %s" % p)
    if not text:
        raise ValueError("text 空")
    return {"date": date, "kind": kind, "source_ref": source_ref,
            "participants": list(participants), "text": text}


def scan_meet_rings():
    """全库扫 meet 互引环（registry 六城区+anchors·sorted 序=确定性）.

    text=「与 C-x 相遇：」后段卡面原文逐字; 判据=「与 <p> 相遇：<text>」为源行逐字子串.
    """
    rows = []
    for pattern in SCAN_DIRS:
        paths = sorted(glob.glob(os.path.join(ROOT, pattern, "C-*.md")))
        for path in paths:
            rel = os.path.relpath(path, ROOT).replace("\\", "/")
            cid = os.path.splitext(os.path.basename(path))[0]
            with open(path, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    m = MEET_RE.match(line.rstrip("\r\n"))
                    if not m:
                        continue
                    date, partner, text = m.group(1), m.group(2), m.group(3)
                    if cid in RESERVED or partner in RESERVED:
                        continue  # 荣席零入（防御面·reserved 目录本就不扫）
                    rows.append(build_row("meet_ring", date, "%s:L%d" % (rel, i),
                                          [cid, partner], text))
    return rows


def load_light_ids():
    ids = set()
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("id"):
                ids.add(o["id"])
    return ids


def rumor_rows(run_obj, event_text):
    """rumor_chain 实跑产物 → rumor_hop 行族（charset 门+荣席门+在册门）."""
    if run_obj.get("engine_v") != RC_ENGINE_V:
        raise ValueError("engine_v 不符本仓 rumor_chain (%r)" % run_obj.get("engine_v"))
    hops = run_obj.get("hops") or []
    if not hops:
        raise ValueError("空链（hops=0）零行")
    allowed = set(event_text) | PADDING_CHARS  # 字符集 ⊆ 事件原文 ∪ 垫话闭集
    eid = run_obj.get("event_id") or ""
    seed = run_obj.get("seed") or ""
    at = run_obj.get("at") or ""
    rows = []
    for h in hops:
        text = h.get("text") or ""
        if not set(text) <= allowed:
            raise ValueError("字符集越界（零编造门）: %r" % text[:20])
        date = (h.get("ts") or "").split(" ")[0]
        src = "rumor_chain:%s:event_id=%s:seed=%s:at=%s:hop=%s" % (
            RC_ENGINE_V, eid, seed, at, h.get("hop"))
        rows.append(build_row("rumor_hop", date, src,
                              [h.get("from"), h.get("to")], text))
    return rows


def append_rows(rows, quiet=False):
    """增量追加（幂等）: 既有行集合去重·前缀字节零改写·只 append."""
    existing = set()
    if os.path.exists(LEDGER):
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                existing.add(line.rstrip("\n"))
    fresh = []
    for r in rows:
        j = row_json(r)
        if j not in existing:
            fresh.append(j)
            existing.add(j)
    if fresh:
        with open(LEDGER, "a", encoding="utf-8", newline="\n") as f:
            f.write("".join(j + "\n" for j in fresh))
    if not quiet:
        print("rows_total=%d appended=%d skipped=%d" %
              (len(existing), len(fresh), len(rows) - len(fresh)))
    return len(fresh)


def qc():
    """断言电池（判据=契约款·夹具内存态·跑后零残留）."""
    results = []

    def check(name, ok):
        results.append((name, bool(ok)))

    # 1 meet_ring 解析: registry 形/anchors 形（嵌套引号『』+CEO_ORDER 锚尾）双夹具
    reg_line = "- 2026-09-27 「与 C-02271 相遇：追光：听说今天天气不错，蒸笼里的暖光也特别柔和。」 [锚] 城市实况 2026-09-27（FluxVerse 事件流+真实时间天气）\n"
    anc_line = "- 2026-09-23 「与 C-00013 相遇：我顺口问他：『新令牌 O-20260923-2245-bm-a 誊好了伐？』」 [锚] CEO_ORDER O-20260923-2245-bm-a（09-23 22:45）\n"
    m1 = MEET_RE.match(reg_line)
    m2 = MEET_RE.match(anc_line)
    check("parse registry form", bool(m1) and m1.group(1) == "2026-09-27"
          and m1.group(2) == "C-02271"
          and m1.group(3) == "追光：听说今天天气不错，蒸笼里的暖光也特别柔和。")
    check("parse anchors form", bool(m2) and m2.group(2) == "C-00013"
          and m2.group(3) == "我顺口问他：『新令牌 O-20260923-2245-bm-a 誊好了伐？』")
    check("non-meet line not matched", MEET_RE.match("- 2026-09-27 「今早的天气真不错。」 [锚] 城市实况 2026-09-27\n") is None)

    # 2 卡面原文逐字: 「与 <p> 相遇：<text>」为源行逐字子串
    inner = m1.group(3)
    check("verbatim substring",
          ("与 %s 相遇：%s" % (m1.group(2), inner)) in reg_line)

    # 3 kind 闭集 + 4 源指针律（无指针行拒收）+ date 形
    try:
        build_row("meet_ring", "2026-09-27", "", ["C-00010", "C-00013"], "x")
        check("no-pointer refused", False)
    except ValueError:
        check("no-pointer refused", True)
    try:
        build_row("gossip", "2026-09-27", "s", ["C-00010", "C-00013"], "x")
        check("kind closed set", False)
    except ValueError:
        check("kind closed set", True)
    try:
        build_row("meet_ring", "09-27", "s", ["C-00010", "C-00013"], "x")
        check("date form refused", False)
    except ValueError:
        check("date form refused", True)

    # 5 荣席零入: 行构造拒 + meet 扫描防御（reserved 双侧）
    for bad in (("C-00001", "C-00010"), ("C-00010", "C-00002")):
        try:
            build_row("meet_ring", "2026-09-27", "s:L1", list(bad), "x")
            check("reserved refused %s" % bad[0], False)
        except ValueError:
            check("reserved refused %s" % bad[0], True)

    # 6 rumor_hop 字符集门: 合法垫话/模糊过·越界新事实拒
    ev = "G16 U184输入链急件修复。round 78: monitoring WQ 71/82。"
    run = {"engine_v": RC_ENGINE_V, "event_id": "QC-EV", "seed": "C-00010",
           "at": "2026-09-27 09:00",
           "hops": [{"hop": 1, "from": "C-00010", "to": "C-00050",
                     "ts": "2026-09-27 09:20", "text": "听说G16 U184输入链急件修复。", "op": "pad"},
                    {"hop": 2, "from": "C-00050", "to": "C-00100",
                     "ts": "2026-09-27 10:30", "text": "好像G16 U184输入链急件修复。round 几: monitoring WQ 71/82。", "op": "fuzz"}]}
    try:
        rr = rumor_rows(run, ev)
        check("rumor rows 2", len(rr) == 2 and rr[0]["kind"] == "rumor_hop"
              and rr[0]["participants"] == ["C-00010", "C-00050"]
              and rr[1]["date"] == "2026-09-27"
              and rr[0]["source_ref"].endswith("hop=1"))
    except ValueError:
        check("rumor rows 2", False)
    bad_run = {"engine_v": RC_ENGINE_V, "event_id": "QC-EV", "seed": "C-00010",
               "at": "2026-09-27 09:00",
               "hops": [{"hop": 1, "from": "C-00010", "to": "C-00050",
                         "ts": "2026-09-27 09:20", "text": "听说明天有大台风要来。", "op": "pad"}]}
    try:
        rumor_rows(bad_run, ev)
        check("charset violation refused", False)
    except ValueError:
        check("charset violation refused", True)
    try:
        rumor_rows({"engine_v": "v9.9", "hops": run["hops"]}, ev)
        check("engine_v mismatch refused", False)
    except ValueError:
        check("engine_v mismatch refused", True)

    # 7 确定性: 同输入双扫逐字节一致 + canonical 行序
    fx = []
    for txt, tag in ((reg_line, "a"), (anc_line, "b")):
        m = MEET_RE.match(txt)
        fx.append(build_row("meet_ring", m.group(1), "fx:%s:L1" % tag,
                            ["C-00010", m.group(2)], m.group(3)))
    j1 = [row_json(r) for r in fx]
    j2 = [row_json(build_row("meet_ring", m.group(1), "fx:%s:L1" % tag,
                             ["C-00010", m.group(2)], m.group(3)))
          for txt, tag in ((reg_line, "a"), (anc_line, "b"))
          for m in [MEET_RE.match(txt)]]
    check("deterministic serialization", j1 == j2 and
          all(list(json.loads(x).keys()) == ["date", "kind", "source_ref",
                                             "participants", "text"] for x in j1))

    # 8 append-only 前缀保全 + 幂等（temp 台账·跑后零残留）
    tmpdir = tempfile.mkdtemp(prefix="interchat_qc_")
    global LEDGER
    saved = LEDGER
    try:
        LEDGER = os.path.join(tmpdir, "ledger.jsonl")
        append_rows(fx, quiet=True)
        with open(LEDGER, "rb") as f:
            prefix = f.read()
        more = [build_row("rumor_hop", "2026-09-27", "fx:c:hop=1",
                          ["C-00010", "C-00050"], "听说")]
        append_rows(more, quiet=True)
        with open(LEDGER, "rb") as f:
            after = f.read()
        check("append-only prefix preserved", after.startswith(prefix)
              and after == prefix + row_json(more[0]).encode("utf-8") + b"\n")
        append_rows(fx + more, quiet=True)
        with open(LEDGER, "rb") as f:
            third = f.read()
        check("re-feed idempotent", third == after)
    finally:
        LEDGER = saved
        for fn in os.listdir(tmpdir):
            os.unlink(os.path.join(tmpdir, fn))
        os.rmdir(tmpdir)

    # 9 实库只读复核（存在时）: 全行 kind/source_ref/荣席 三门 100%
    if os.path.exists(LEDGER):
        bad = 0
        n = 0
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                o = json.loads(line)
                n += 1
                if (o.get("kind") not in KINDS or not o.get("source_ref")
                        or any(p in RESERVED for p in o.get("participants", []))):
                    bad += 1
        check("live ledger 3-gate 100%% (n=%d)" % n, bad == 0)

    fails = [n for n, ok in results if not ok]
    print("== interchat_ledger --qc（契约款断言·%d 项）==" % len(results))
    print("PASS %d / FAIL %d" % (len(results) - len(fails), len(fails)))
    if fails:
        print("FAILED:", ", ".join(fails))
        sys.exit(1)
    print("QC PASS")


def main():
    global LEDGER
    ap = argparse.ArgumentParser(description="互聊内容台账派生器 v0（契约=T-20260926-18 步⑨分步①）")
    ap.add_argument("--feed-rumor", default=None, help="rumor_chain 实跑产物 JSON 文件路径")
    ap.add_argument("--event-text", default=None, help="流言源事件文本（--feed-rumor 必随·字符集门用）")
    ap.add_argument("--qc", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="只报增量行数零写盘")
    args = ap.parse_args()
    if args.qc:
        qc()
        return
    rows = scan_meet_rings()
    n_meet = len(rows)
    if args.feed_rumor:
        if not args.event_text:
            sys.exit("error: --feed-rumor 须随 --event-text（字符集零编造门）")
        with open(args.feed_rumor, encoding="utf-8") as f:
            run_obj = json.load(f)
        rows += rumor_rows(run_obj, args.event_text)
    ids = load_light_ids()
    for r in rows:
        for p in r["participants"]:
            if p not in ids:
                sys.exit("error: 参与者不在 census 导出面: %s" % p)
    if args.dry_run:
        existing = set()
        if os.path.exists(LEDGER):
            with open(LEDGER, encoding="utf-8") as f:
                existing = {l.rstrip("\n") for l in f}
        fresh = [j for j in (row_json(r) for r in rows) if j not in existing]
        print("dry-run: meet_ring=%d rumor_hop=%d fresh=%d" %
              (n_meet, len(rows) - n_meet, len(fresh)))
        return
    append_rows(rows)
    print("meet_ring=%d rumor_hop=%d" % (n_meet, len(rows) - n_meet))


if __name__ == "__main__":
    main()
