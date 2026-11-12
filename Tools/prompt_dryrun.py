#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""提示词出生站体检器（离线·零 LLM·零 GPU）。

为什么存在
----------
R2588/R2589 在 `evolve_citizen.build_prompt` 里修了两处「提示词自伤」
（禁族当天仍教模型从手写起 / 尾区渲染成「身上、身上的」）。但两次修复都
只做了代码审读与局部断言，**从未把今晚真实会送进模型的整段提示词渲染出来
看一眼**。4B 模型对提示词尾区权重最高，任何一处矛盾都会在 19:00 首批变成
零产出（席位留 due）或文本污染。

本工具复刻 `evolve_citizen.main()` 的 sig 构造链（只读本地盘，不连 Ollama、
不写生产文件），把 due 席位的提示词逐段渲染，然后机器扫描四类自伤：

  R1 相邻重复词：`身上、身上` / `手上、手上` / `身上身上的`
  R2 禁族矛盾：today_ban_families 非空时，仍出现「从你此刻手上……」这类鼓励
  R3 骨架泄漏：opening_seed_block 给出的骨架落在当天被禁的族
  R4 提示词尾部自伤：最后 400 字内命中 R1/R2

用法
----
    python -X utf8 Tools/prompt_dryrun.py              # 预演 due 前 3 席 → qa/ 报告
    python -X utf8 Tools/prompt_dryrun.py --batch 5    # 指定席数
    python -X utf8 Tools/prompt_dryrun.py --cid C-00010 --stdout   # 单席打印全文
    python -X utf8 Tools/prompt_dryrun.py --selftest   # 自检（内置样本过四检）
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import evolve_citizen as E  # noqa: E402  (需要 Tools/ 在 sys.path)

REPEAT_RE = re.compile(r"([\u4e00-\u9fff]{2})[、，,]?\1")
# 「从/写 …… 此刻手上」：禁族当天任何鼓励位都不许出现（R2590 漏网形态）
HAND_ENCOURAGE_RE = re.compile(r"[从写][^。；，：]{0,10}?此刻手上")
# 禁族当天把部位词拼进「此刻__正在做」句式 → 病句（身体不能做动作）
HAND_PHRASE_BUG_RE = re.compile(r"此刻身上正在做")
LEAD_HAND_RE = re.compile(r"第一个短句不要从「手」字起")


def _render(cid, text, sig):
    """渲染单席提示词（与 main 同一入口，不改任何状态）。"""
    import importlib
    importlib.reload  # noqa: F841  (显式表明不重载模块，保持与进程内一致)
    sig = dict(sig)  # 浅拷贝：build_prompt 会写 event_norm 等键
    sig["card_text"] = text
    sig["cid"] = cid
    try:
        sig["pool_advice"] = ""
        sig["rumor"] = ""
        sig.setdefault("goal", "")
        if "city_digest" not in sig:
            sig["city_digest"] = ""
    except Exception:  # noqa: BLE001
        pass
    return E.build_prompt(cid, text, sig)


def _scan(prompt, cid, banned_families):
    """四类自伤扫描，返回 [(code, detail)]。"""
    hits = []
    for m in REPEAT_RE.finditer(prompt):
        hits.append(("R1", "相邻重复词「%s」@%d" % (m.group(0), m.start())))
    if banned_families and "HAND_DEICTIC" in banned_families:
        if HAND_ENCOURAGE_RE.search(prompt):
            hits.append(("R2", "禁 HAND_DEICTIC 却仍教「…此刻手上…」: %s"
                         % HAND_ENCOURAGE_RE.search(prompt).group(0)))
        if HAND_PHRASE_BUG_RE.search(prompt):
            hits.append(("R2c", "禁族当天「此刻身上正在做」病句"))
        if not LEAD_HAND_RE.search(prompt):
            hits.append(("R2b", "禁 HAND_DEICTIC 但缺「第一个短句不要从手字起」硬句"))
    for m in REPEAT_RE.finditer(prompt[-400:]):
        hits.append(("R4", "尾区重复词「%s」" % m.group(0)))
    # R3：骨架泄漏——重算 opening_seed_block 抽出的那句，判其族是否被禁
    m = re.search(r"「([^」]{6,60})」——严禁原样照抄这句", prompt)
    if m and E._ring_family_of is not None and banned_families:
        fam = E._ring_family_of(m.group(1))
        if fam and fam in banned_families:
            hits.append(("R3", "开场骨架「%s」属于被禁族 %s" % (m.group(1)[:18], fam)))
    return hits


def build_sig():
    """复刻 evolve_citizen.main() 的 sig 构造链（只读盘）。"""
    sig = E.real_signals()
    sig["batch_openings"] = set()
    sig["batch_phrases"] = {}
    sig["batch_used"] = []
    sig["recent_open_ids"], sig["recent_grams"] = E.recent_ring_corpus()
    sig["recent_gram_min"] = E.RECENT_GRAM_MIN
    sig["recent_banned_phrases"] = E.city_banned_phrases(sig["recent_grams"])
    sig["recent_banned_openings"] = [
        k for k, ids in sorted(sig["recent_open_ids"].items(),
                               key=lambda kv: -len(kv[1]))[:8]
        if len(k) >= 8 and len(ids) >= 3]
    _tcount, _tgrams = E.today_ring_openings(with_grams=True)
    sig["today_open_ids"] = _tcount
    sig["today_ban_families"] = set()
    sig["today_family_counts"] = {}
    sig["today_family_total"] = 0
    if E._ring_family_ban is not None and isinstance(_tcount, dict):
        for _op, _c in _tcount.items():
            _f = E._ring_family_of(_op) if E._ring_family_of else None
            if _f:
                sig["today_family_counts"][_f] = sig["today_family_counts"].get(_f, 0) + int(_c)
            sig["today_family_total"] += int(_c)
        sig["today_ban_families"] = E._ring_family_ban(_tcount)
    sig["second_ban"] = set()
    sig["second_counts"] = {}
    sig["second_total"] = 0
    if E._ring_second_ban is not None and E._ring_second_scan is not None:
        try:
            _stot, _shit = E._ring_second_scan(E.today())
        except Exception:  # noqa: BLE001
            _stot, _shit = 0, {}
        sig["second_total"] = int(_stot or 0)
        sig["second_counts"] = dict(_shit or {})
        sig["second_ban"] = E._ring_second_ban(_stot, _shit)
    _tmin = max(E.TODAY_GRAM_MIN, len(_tcount) // 50)
    sig["today_ban_phrases"] = E.city_banned_phrases(
        {g: c for g, c in _tgrams.items() if c >= _tmin})
    sig["today_ban_openings"] = {k for k, c in _tcount.items()
                                 if c >= E.TODAY_OPEN_HARD and len(k) >= 8}
    return sig


def run(batch=3, only_cid=None, stdout=False):
    sig = build_sig()
    cursor = E.load_cursor()
    banned = sig.get("today_ban_families") or set()
    total = sig.get("today_family_total") or 0
    head = []
    head.append("# 提示词出生站体检 · %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    head.append("")
    head.append("- 今日年轮开头族：总 %d 条，占比 %s" % (
        total, "、".join("%s=%d(%.1f%%)" % (f, sig["today_family_counts"].get(f, 0),
                                          100.0 * sig["today_family_counts"].get(f, 0) / max(1, total))
                        for f in sorted(sig["today_family_counts"])) or "（无）"))
    head.append("- 当日禁族：%s" % ("、".join(sorted(banned)) if banned else "（无）"))
    head.append("- 第二句软禁：%s（样本 %d）" % (
        "、".join(sorted(sig.get("second_ban") or [])) or "（无）", sig.get("second_total") or 0))
    head.append("")

    if only_cid:
        cids = [only_cid]
    else:
        cids = E.due_citizens(cursor, batch, None)[:batch]

    rows = []
    all_hits = 0
    for cid in cids:
        p = E.find_card(cid)
        if not p:
            rows.append((cid, "MISSING", []))
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        prompt = _render(cid, text, sig)
        hits = _scan(prompt, cid, banned)
        all_hits += len(hits)
        rows.append((cid, prompt, hits))
        if stdout:
            print("=" * 70)
            print("CID", cid, "len", len(prompt), "hits", len(hits))
            for code, det in hits:
                print("  !!", code, det)
            print("-" * 70)
            print(prompt)

    lines = list(head)
    lines.append("## 逐席结果")
    lines.append("")
    lines.append("| 席位 | 提示词长度 | 自伤命中 | 明细 |")
    lines.append("|---|---|---|---|")
    for cid, prompt, hits in rows:
        if prompt == "MISSING":
            lines.append("| %s | - | MISSING | 找不到卡 |" % cid)
            continue
        lines.append("| %s | %d | %d | %s |" % (
            cid, len(prompt), len(hits),
            "；".join("%s:%s" % h for h in hits) if hits else "clean"))
    lines.append("")
    verdict = "PASS" if all_hits == 0 else "FAIL"
    lines.append("**verdict: %s**（席位 %d，自伤命中 %d）" % (verdict, len(rows), all_hits))
    report = "\n".join(lines)

    if stdout:
        print(report)
    return report, verdict, rows


def selftest():
    """三组内置样本：正常 / 尾区重复 / 禁族矛盾，验证判据不误杀也不漏杀。"""
    ok = True
    cases = [
        ("clean", "改从你此刻身上的具体细节写起，第一个短句不要从「手」字起。", set(), 0),
        ("repeat", "改从你此刻身上、身上的具体细节写起。", set(), 1),
        ("ban-miss", "改从你此刻手上的具体细节写起。", {"HAND_DEICTIC"}, 2),
        ("ban-ok", "改从你此刻身上的细节写起，第一个短句不要从「手」字起。", {"HAND_DEICTIC"}, 0),
        # R2590 漏网形态负控：模板「写你自己此刻手上的具体小动作」必须被拦
        ("ban-tail", "开场请写你自己此刻手上的具体小动作。第一个短句不要从「手」字起。",
         {"HAND_DEICTIC"}, 1),
        ("ban-bug", "请从你自己此刻身上正在做的具体小动作写起。第一个短句不要从「手」字起。",
         {"HAND_DEICTIC"}, 1),
    ]
    for name, text, banned, expect in cases:
        hits = _scan(text, "C-TEST", banned)
        if expect == 0:
            good = len(hits) == 0
        elif expect == 1:
            good = len(hits) >= 1
        else:
            good = len(hits) >= 2
        if not good:
            ok = False
        print("  %-10s expect=%d hits=%s %s" % (
            name, expect, [h[0] for h in hits], "OK" if good else "FAIL"))
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="提示词出生站体检（离线·零 LLM）")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--cid", default=None)
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    report, verdict, _rows = run(args.batch, args.cid, args.stdout)
    out_dir = os.path.join(ROOT, "qa")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "PROMPT-DRYRUN-%s.md" % datetime.date.today().isoformat())
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(report + "\n")
    print("report:", out)
    print("verdict:", verdict)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
