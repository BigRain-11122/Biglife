# -*- coding: utf-8 -*-
"""optimize_corpus.py — 把新标准回填到**存量**内容上。

CEO 2026-11-20「把已有的都重新优化一遍」。

两档，都带回滚档：
  --rings    全库年轮收口（所有日期）：悬空引号回退 + 句末补全。
             只修标点形状，不改内容、不重写、不裁长度（历史不缩水）。
  --reflect  重写**过不了新闸**的旧反思（旧的 40 字压缩包，如「风扯得旗子猎…」）。
             逐条走本地 9B，最长 50–160 字第一人称回看。

用法：
  python -X utf8 Tools/optimize_corpus.py --rings [--dry-run]
  python -X utf8 Tools/optimize_corpus.py --reflect [--limit 200] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import evolve_citizen as ec  # noqa: E402

CO = ec.CO
REG = os.path.join(CO, "census", "registry")
BACKUP_R = os.path.join(CO, "state", "corpus-rings-backup.json")
BACKUP_F = os.path.join(CO, "state", "corpus-reflect-backup.json")
RING_LINE = re.compile(r"^(- (\d{4}-\d{2}-\d{2}) \u300c)(.+?)(\u300d)", re.M)
# 反思行真实形态：- 2026-11-19 「…」 [锚] 本卡年轮区（V2-B 反思层·提炼自年轮原文）
# 锚记是**英文方括号** [锚]（不是【锚】），用 [^\n]* 跳过，免得再踩一次。
REFL_LINE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) \u300c(.+?)\u300d[^\n]*\u53cd\u601d[^\n]*$", re.M)
LEGAL = "\u3002\uff01\uff1f\u2026\u300d\u201d"


def _cards(fresh_skip=180):
    """遍历居民卡；跳过最近 fresh_skip 秒内被动过的（泵正在写，避免互相覆盖）。"""
    now = time.time()
    for root, _, fs in os.walk(REG):
        for f in fs:
            if not (f.startswith("C-") and f.endswith(".md")):
                continue
            p = os.path.join(root, f)
            try:
                if now - os.path.getmtime(p) < fresh_skip:
                    continue
            except OSError:
                continue
            yield f[:-3], p


def fix_rings(dry=False):
    fixed = touched = 0
    backup = {}
    for cid, p in _cards():
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        changed = False
        out = []
        last = 0
        for m in RING_LINE.finditer(t):
            body = m.group(3)
            bad_end = body and body[-1] not in LEGAL
            unbal = body.count("\u300c") != body.count("\u300d") \
                or body.count("\u201c") != body.count("\u201d")
            if not (bad_end or unbal):
                continue
            new = ec.fit_ring_line(body, limit=999)   # 不裁长度，只收口
            if not new or new == body:
                continue
            backup.setdefault(cid, []).append(body)
            out.append((m.start(3), m.end(3), new))
            fixed += 1
            changed = True
        if not changed:
            continue
        touched += 1
        if dry:
            continue
        for s, e, new in reversed(out):
            t = t[:s] + new + t[e:]
        try:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(t)
        except OSError:
            backup.pop(cid, None)
            touched -= 1
    if not dry and backup:
        try:
            old = {}
            if os.path.exists(BACKUP_R):
                try:
                    old = json.load(open(BACKUP_R, encoding="utf-8"))
                except (OSError, ValueError):
                    old = {}
            old.update(backup)
            with open(BACKUP_R, "w", encoding="utf-8") as fh:
                json.dump(old, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return fixed, touched


def fix_reflect(limit=200, dry=False):
    """重写上不了新闸的旧反思。返回 (重写数, 尝试数)。"""
    done = tried = 0
    backup = {}
    for cid, p in _cards(fresh_skip=15):
        if tried >= limit:
            break
        try:
            t = open(p, encoding="utf-8").read()
        except OSError:
            continue
        ms = list(REFL_LINE.finditer(t))
        if not ms:
            continue
        corpus, ents = ec.rings_of(t)
        if len(ents) < ec.REFLECT_MIN_RINGS:
            continue
        creed = ec.persona_digest(t).get("creed", "")
        # 逐条扫（今天之前写的是 40 字压缩包，需要重写；今天之后的已经合格）。
        # 一张卡最多改 3 条，避免个别居民把预算吃光；倒序改，偏移不会错位。
        fixed_here = 0
        for m in reversed(ms):
            if fixed_here >= 3:
                break
            old = m.group(2)
            if not ec.reflect_violations(old, corpus, creed):
                continue
            tried += 1
            if dry:
                continue
            try:
                new = ec.llm(ec.build_reflect_prompt(cid, ents, creed))
            except Exception:  # noqa: BLE001
                continue
            new = re.sub(r"\s+", " ", new).strip().strip("\u300c\u300d\"\u201c\u201d")
            if ec.reflect_violations(new, corpus, creed):
                continue
            backup.setdefault(cid, []).append(old)
            t = t[:m.start(2)] + new + t[m.end(2):]
            done += 1
            fixed_here += 1
        if not fixed_here:
            backup.pop(cid, None)
            continue
        try:
            with open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(t)
        except OSError:
            pass
    if not dry and backup:
        try:
            with open(BACKUP_F, "w", encoding="utf-8") as fh:
                json.dump(backup, fh, ensure_ascii=False, indent=1)
        except OSError:
            pass
    return done, tried


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rings", action="store_true")
    ap.add_argument("--reflect", action="store_true")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.rings:
        f, c = fix_rings(dry=a.dry_run)
        print("年轮收口：修 %d 处，涉及 %d 张卡%s"
              % (f, c, "（dry-run）" if a.dry_run else "，回滚档 corpus-rings-backup.json"))
    if a.reflect:
        d, tr = fix_reflect(limit=a.limit, dry=a.dry_run)
        print("旧反思重写：合格重写 %d 条（扫描待修 %d 条）%s"
              % (d, tr, "（dry-run）" if a.dry_run else "，回滚档 corpus-reflect-backup.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
