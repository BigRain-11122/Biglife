# -*- coding: utf-8 -*-
"""rewrite_persona.py — 重写人设里两个高重复字段（现状 / 思想），一次一张卡。

CEO 2026-11-20「无所谓 你可以重写，我要的是高质量」。

为什么只动这两个字段
-------------------
出身（127 句撑一万人）、现状（123 句）、思想（511 句）是千人一面的三个固定池。
但**出身绑着源流设定**（origin_matrix 给每个人定的人种/省份/域外），重写会与
地域块冲突；而现状与思想是"这个人此刻怎么看自己的日子"，重写不破坏设定。

高质量怎么保证（不靠模型自觉，靠闸）
--------------------------------
① 长度 22–60 字（现状）/ 18–50 字（思想），超了不收；
② **必须带一件他自己的东西**：从卡面「钩子」里取连续 4 字以上原词，写不进去就退回；
③ 与「信条」连续 6 字重合即判照抄，退回；
④ 不许出现"人生""道理""命运""意义"这类空词（格言腔）；
⑤ 全失败保留原文——宁可不动，不写次品。

回滚档：state/persona-rewrite-backup.json（cid → {现状, 思想} 原文）

用法：
  python -X utf8 Tools/rewrite_persona.py --limit 20 [--dry-run] [--only 现状|思想]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evolve_citizen as ec  # noqa: E402

CO = ec.CO
REG = os.path.join(CO, "census", "registry")
BACKUP = os.path.join(CO, "state", "persona-rewrite-backup.json")

# 现状在卡面是「经历」段落里的 `现状：…`，**没有** **现状** 这个标签——
# 第一版按标签找，结果一张卡都匹配不上（试跑 0 张）。这里按行内标签定位。
NOW_RE = re.compile(r"(\u73b0\u72b6\uff1a)(.+?)(?:\n|$)")
IDEA_RE = re.compile(r"(\*\*\u601d\u60f3\*\*\s*)(.+?)(?:\n|$)")
HOOK_RE = re.compile(r"\*\*\u94a9\u5b50\*\*\s*(.+?)(?:\n|$)")
CREED_RE = re.compile(r"\*\*\u4fe1\u6761\*\*\s*\u300c(.+?)\u300d")
EMP = pc = re.compile(r"\u4eba\u751f|\u9053\u7406|\u547d\u8fd0|\u610f\u4e49|\u771f\u8c1b|\u609f\u51fa")


def _chinese_grams(text, n=4):
    t = re.sub(r"[^\u4e00-\u9fa5]", "", text or "")
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def _gate(new, old, hook, creed, lo, hi):
    n = len(new)
    if not (lo <= n <= hi):
        return "len"
    if new == old:
        return "same"
    if EMP.search(new):
        return "empty-talk"
    if creed:
        cg = _chinese_grams(creed, 6)
        if any(g in new for g in cg):
            return "creed"
    hg = _chinese_grams(hook, 4)
    if hg and not any(g in new for g in hg):
        return "no-hook"
    return ""


def _prompt(cid, p, cur_now, cur_idea, hook):
    return (
        "\u4f60\u662f\u8d85\u4f53\u5b87\u5b99\u57ce\u7684\u5c45\u6c11\u300c%s\u300d\u3002"
        "\u4f60\u7684\u8d44\u6599\uff1a%s\uff0c%d \u5c81\uff0c\u804c\u4e1a\u662f%s\uff0c\u6027\u683c %s\u3002"
        "\u4f60\u6709\u4e00\u4ef6\u53ea\u5c5e\u4e8e\u4f60\u7684\u4e8b\uff1a%s\n"
        "\u73b0\u5728\u8bf7\u4f60\u5199\u4e24\u53e5\u8bdd\uff08\u5404\u81ea\u4e00\u884c\uff0c\u4e0d\u8981\u6807\u7b7e\u3001\u4e0d\u8981\u5f15\u53f7\u3001\u4e0d\u8981\u89e3\u91ca\uff09\uff1a\n"
        "1) \u73b0\u72b6\uff0822\u201360 \u5b57\uff09\uff1a\u4f60\u773c\u4e0b\u65e5\u5b50\u91cc\u5177\u4f53\u5728\u5fd9\u7684\u4e00\u4ef6\u4e8b\uff0c\u8981\u5e26\u4e0a\u201c%s\u201d\u91cc\u7684\u4e1c\u897f\uff1b\n"
        "2) \u601d\u60f3\uff0818\u201350 \u5b57\uff09\uff1a\u4f60\u81ea\u5df1\u7684\u4e00\u4e2a\u5224\u65ad\uff0c\u50cf\u8ddf\u719f\u4eba\u8bf4\u7684\u90a3\u79cd\uff0c"
        "\u4e0d\u8bb8\u5199\u4eba\u751f\u9053\u7406\u3001\u4e0d\u8bb8\u50cf\u683c\u8a00\u3002\n"
        "\u53c2\u8003\uff08\u4e0d\u8981\u7167\u6284\uff09\uff1a\u73b0\u72b6\u201c%s\u201d\uff1b\u601d\u60f3\u201c%s\u201d"
        % (cid, p.get("species", "")[:20], 0, p.get("prof", "")[:20],
           p.get("traits", "")[:30], hook[:40], hook[:8], cur_now[:30], cur_idea[:30]))


def _cards(fresh_skip=120, shard=0, shards=1):
    """遍历居民卡；跳过最近 fresh_skip 秒内被动过的（泵正在写，避免互相覆盖）。

    shard/shards：按 cid 取模分片，供车道并行起多条（每条一个进程）。
    判据用 md5 而不是末尾数字，避免连续 cid 全落到同一片。
    """
    import hashlib
    import time
    now = time.time()
    for root, _, fs in os.walk(REG):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            cid = f[:-3]
            if shards > 1:
                h = int(hashlib.md5(cid.encode("utf-8")).hexdigest()[:8], 16)
                if h % shards != shard:
                    continue
            p = os.path.join(root, f)
            try:
                if now - os.path.getmtime(p) < fresh_skip:
                    continue
            except OSError:
                continue
            yield cid, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    a = ap.parse_args()
    # 2026-11-20 夜 CEO「游戏开发在并行，排单排队，不要互相杀进程」：
    # 重写是纯 GPU 活，游戏车道（团结/Unity 编辑器）在跑时直接让路，
    # 不抢显存、不烧推理，等下一个窗口。只让路，不杀任何进程。
    try:
        import subprocess as _sp
        _r = _sp.run(["tasklist"], capture_output=True, text=True,
                     encoding="utf-8", errors="replace", timeout=30)
        _low = (_r.stdout or "").lower()
        if any(_p in _low for _p in ("unity.exe", "tuanjie.exe", "unityhub.exe")):
            # CEO 2026-11-20 夜更正：「不是让路，是共用大模型、排队」。
            # 所以不停产：只把每轮张数压到 6 张、单分片，请求照常进 ollama 队列，
            # 退到低优先级——游戏车道要卡时先到先得。
            a.limit = min(a.limit, 6)
            a.shards = 1
            print("shared-mode: game lane active -> limit 6, single shard")
    except Exception:  # noqa: BLE001
        pass
    done = tried = 0
    backup = {}
    for cid, p in _cards(shard=a.shard, shards=max(1, a.shards)):
        if tried >= a.limit:
            break
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        mn, mi, mh = NOW_RE.search(t), IDEA_RE.search(t), HOOK_RE.search(t)
        mc = CREED_RE.search(t)
        if not (mn and mi and mh):
            continue
        tried += 1
        age = re.search(r"\u6027\u522b\u00b7\u5e74\u9f84\*\*\s*\S+\s*\u00b7\s*(\d+)", t)
        per = ec.persona_digest(t)
        per["age"] = age.group(1) if age else ""
        hook, creed = mh.group(1), (mc.group(1) if mc else "")
        try:
            raw = ec.llm(_prompt(cid, per, mn.group(2), mi.group(2), hook))
        except Exception:  # noqa: BLE001
            continue
        lines = [x.strip() for x in raw.split("\n") if x.strip()]
        if len(lines) < 2:
            continue
        new_now, new_idea = lines[0], lines[1]
        if a.only == "\u73b0\u72b6":
            new_idea = mi.group(2)
        if a.only == "\u601d\u60f3":
            new_now = mn.group(2)
        if _gate(new_now, mn.group(2), hook, creed, 22, 60):
            new_now = mn.group(2)
        if _gate(new_idea, mi.group(2), hook, creed, 18, 50):
            new_idea = mi.group(2)
        if new_now == mn.group(2) and new_idea == mi.group(2):
            continue
        if a.dry_run:
            print("%s\n  现状→ %s\n  思想→ %s" % (cid, new_now, new_idea))
            done += 1
            continue
        backup[cid] = {"now": mn.group(2), "idea": mi.group(2)}
        t = NOW_RE.sub("\u73b0\u72b6\uff1a" + new_now, t, count=1)
        t = IDEA_RE.sub("**\u601d\u60f3** " + new_idea, t, count=1)
        try:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(t)
            done += 1
        except OSError:
            backup.pop(cid, None)
    if not a.dry_run and backup:
        try:
            with open(BACKUP, "w", encoding="utf-8") as fh:
                json.dump(backup, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass
    print("\u91cd\u5199 %d 张卡 / 尝试 %d 张%s" % (done, tried, "（dry-run）" if a.dry_run else "，回滚档 persona-rewrite-backup.json"))


if __name__ == "__main__":
    raise SystemExit(main())
