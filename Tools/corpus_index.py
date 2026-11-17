# -*- coding: utf-8 -*-
"""语料索引：把 10191 份居民档案建成可秒查的本地库（CEO 2026-11-17「模型调用语料要能快速找到」）。

现状痛点：
  1. `due_citizens()` 每批都 os.walk 全库（10191 文件）→ 这是每批 10-15 秒固定开销的大头；
  2. 检索只能靠 `memory_index.py --id`（单居民）；没有"按主题/城区/职业快速找语料"的入口。

本索引用内置 sqlite3，零新依赖、零 LLM：
  - `citizens` 表：id / 城区 / 物种 / 职业 / 最后年轮日 / 年轮数 / 文件 mtime
  - `rings`    表：cid / date / text（每条年轮一行，供关键词检索）
  - 增量：只重扫 mtime 变化的文件，之后每次更新约 1-3 秒

用法：
  python -X utf8 Tools/corpus_index.py --build          # 增量构索引
  python -X utf8 Tools/corpus_index.py --rebuild        # 全量重建
  python -X utf8 Tools/corpus_index.py --id C-01222     # 查单个居民
  python -X utf8 Tools/corpus_index.py --q 风铃 --limit 10   # 全文检索年轮
  python -X utf8 Tools/corpus_index.py --district RV --stale 3  # 城区/欠写筛选
  python -X utf8 Tools/corpus_index.py --stats
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")
DB = os.path.join(CO, "state", "corpus.db")

RING_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (.+)$")
HEAD_RE = re.compile(r"^\*\*物种\*\*\s*([^｜|]+)")
PROF_RE = re.compile(r"职业\*\*\s*(.+)$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS citizens (
  id TEXT PRIMARY KEY, district TEXT, species TEXT, prof TEXT,
  last_ring TEXT, ring_count INTEGER, mtime REAL
);
CREATE INDEX IF NOT EXISTS ix_citizens_district ON citizens(district);
CREATE INDEX IF NOT EXISTS ix_citizens_last ON citizens(last_ring);
CREATE TABLE IF NOT EXISTS rings (
  cid TEXT, date TEXT, text TEXT
);
CREATE INDEX IF NOT EXISTS ix_rings_cid ON rings(cid);
CREATE INDEX IF NOT EXISTS ix_rings_date ON rings(date);
"""


def _db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    return con


def _parse(path):
    """返回 (district, species, prof, rings[(date, text)])。"""
    district = os.path.basename(os.path.dirname(path))
    species = prof = ""
    rings = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                s = line.rstrip("\n")
                m = RING_RE.match(s)
                if m:
                    # 去掉 [锚] 注脚，只留正文
                    body = m.group(2)
                    body = re.sub(r"\s*\[锚\].*$", "", body)
                    rings.append((m.group(1), body))
                    continue
                if not species:
                    m = HEAD_RE.match(s)
                    if m:
                        species = m.group(1).strip()[:40]
                if not prof:
                    m = PROF_RE.search(s)
                    if m:
                        prof = m.group(1).strip()[:60]
    except OSError:
        pass
    return district, species, prof, rings


def build(force=False):
    t0 = time.time()
    con = _db()
    cur = con.cursor()
    have = {}
    if not force:
        for cid, mt in cur.execute("SELECT id, mtime FROM citizens"):
            have[cid] = mt
    seen = set()
    updated = 0
    reg = os.path.join(CENSUS, "registry")
    # anchors 目录也要入索引：due_citizens 的 id 全集原本同时扫 anchors+registry，
    # 索引若只含 registry 会让 521 张 anchor 卡从选人面消失。
    for root, _, files in os.walk(reg):
        for fn in files:
            if not (fn.endswith(".md") and fn.startswith("C-")):
                continue
            p = os.path.join(root, fn)
            cid = fn[:-3]
            seen.add(cid)
            try:
                mt = os.path.getmtime(p)
            except OSError:
                continue
            if not force and have.get(cid) and abs(have[cid] - mt) < 1e-6:
                continue
            district, species, prof, rings = _parse(p)
            last = max((d for d, _ in rings), default="")
            cur.execute(
                "INSERT INTO citizens(id,district,species,prof,last_ring,ring_count,mtime)"
                " VALUES(?,?,?,?,?,?,?)"
                " ON CONFLICT(id) DO UPDATE SET district=excluded.district,"
                " species=excluded.species, prof=excluded.prof,"
                " last_ring=excluded.last_ring, ring_count=excluded.ring_count,"
                " mtime=excluded.mtime",
                (cid, district, species, prof, last, len(rings), mt))
            cur.execute("DELETE FROM rings WHERE cid=?", (cid,))
            if rings:
                cur.executemany("INSERT INTO rings(cid,date,text) VALUES(?,?,?)",
                                [(cid, d, t) for d, t in rings])
            updated += 1
    # anchors 目录（521 张，due_citizens 的 id 全集包含它们）
    anc = os.path.join(CENSUS, "anchors")
    if os.path.isdir(anc):
        for root, _, files in os.walk(anc):
            for fn in files:
                if not (fn.endswith(".md") and fn.startswith("C-")):
                    continue
                p = os.path.join(root, fn)
                cid = fn[:-3]
                seen.add(cid)
                try:
                    mt = os.path.getmtime(p)
                except OSError:
                    continue
                if not force and have.get(cid) and abs(have[cid] - mt) < 1e-6:
                    continue
                district, species, prof, rings = _parse(p)
                last = max((d for d, _ in rings), default="")
                cur.execute(
                    "INSERT INTO citizens(id,district,species,prof,last_ring,ring_count,mtime)"
                    " VALUES(?,?,?,?,?,?,?)"
                    " ON CONFLICT(id) DO UPDATE SET district=excluded.district,"
                    " species=excluded.species, prof=excluded.prof,"
                    " last_ring=excluded.last_ring, ring_count=excluded.ring_count,"
                    " mtime=excluded.mtime",
                    (cid, district, species, prof, last, len(rings), mt))
                cur.execute("DELETE FROM rings WHERE cid=?", (cid,))
                if rings:
                    cur.executemany("INSERT INTO rings(cid,date,text) VALUES(?,?,?)",
                                    [(cid, d, t) for d, t in rings])
                updated += 1
    # 清掉已删除的档案
    gone = [c for c in have if c not in seen]
    for cid in gone:
        cur.execute("DELETE FROM citizens WHERE id=?", (cid,))
        cur.execute("DELETE FROM rings WHERE cid=?", (cid,))
    con.commit()
    n = cur.execute("SELECT COUNT(*) FROM citizens").fetchone()[0]
    rn = cur.execute("SELECT COUNT(*) FROM rings").fetchone()[0]
    con.close()
    print("index built: citizens=%d rings=%d updated=%d removed=%d %.1fs"
          % (n, rn, updated, len(gone), time.time() - t0))


def show_id(cid):
    con = _db()
    row = con.execute("SELECT id,district,species,prof,last_ring,ring_count "
                      "FROM citizens WHERE id=?", (cid,)).fetchone()
    if not row:
        print("not found:", cid)
        con.close()
        return 1
    print("id=%s district=%s species=%s prof=%s last=%s rings=%d" % row)
    for d, t in con.execute("SELECT date,text FROM rings WHERE cid=? ORDER BY date DESC LIMIT 5",
                            (cid,)):
        print("  %s %s" % (d, t[:100]))
    con.close()
    return 0


def search(q, limit=10):
    con = _db()
    like = "%" + q + "%"
    rows = con.execute(
        "SELECT r.cid, r.date, r.text, c.district, c.prof FROM rings r "
        "JOIN citizens c ON c.id = r.cid WHERE r.text LIKE ? "
        "ORDER BY r.date DESC LIMIT ?", (like, limit)).fetchall()
    print("q=%s hits=%d" % (q, len(rows)))
    for cid, d, t, dist, prof in rows:
        print("  [%s/%s] %s %s" % (dist, (prof or "")[:10], d, t[:90]))
    if not rows:
        # 退化为按职业/城区找
        rows2 = con.execute(
            "SELECT id, district, prof, last_ring FROM citizens "
            "WHERE prof LIKE ? OR species LIKE ? LIMIT ?", (like, like, limit)).fetchall()
        if rows2:
            print("  (no ring hit; by profile)")
            for r in rows2:
                print("   ", r)
    con.close()
    return 0


def by_district(district=None, stale_days=None, limit=20):
    con = _db()
    sql = ("SELECT id,district,prof,last_ring,ring_count FROM citizens WHERE 1=1")
    args = []
    if district:
        sql += " AND district=?"
        args.append(district)
    if stale_days:
        cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - stale_days * 86400))
        sql += " AND (last_ring='' OR last_ring < ?)"
        args.append(cutoff)
    sql += " ORDER BY last_ring ASC LIMIT ?"
    args.append(limit)
    rows = con.execute(sql, args).fetchall()
    print("rows=%d" % len(rows))
    for r in rows:
        print("  %s | %s | %s | last=%s | n=%d" % r)
    con.close()
    return 0


def stats():
    con = _db()
    print("citizens:", con.execute("SELECT COUNT(*) FROM citizens").fetchone()[0])
    print("rings:", con.execute("SELECT COUNT(*) FROM rings").fetchone()[0])
    print("--- by district ---")
    for d, n in con.execute("SELECT district,COUNT(*) FROM citizens GROUP BY district ORDER BY 2 DESC"):
        print("  %-6s %d" % (d, n))
    print("--- 最近 7 天有年轮的居民 ---")
    cutoff = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7 * 86400))
    print(" ", con.execute("SELECT COUNT(*) FROM citizens WHERE last_ring >= ?", (cutoff,)).fetchone()[0])
    con.close()
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--q")
    ap.add_argument("--district")
    ap.add_argument("--stale", type=int)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.rebuild:
        return build(force=True) or 0
    if a.build:
        return build() or 0
    if a.id:
        return show_id(a.id)
    if a.q:
        return search(a.q, a.limit)
    if a.district or a.stale:
        return by_district(a.district, a.stale, a.limit)
    if a.stats:
        return stats()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
