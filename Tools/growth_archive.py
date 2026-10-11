#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""N2 居民成长档案·聚合导出器 v1.0（T-20260929-03 分步③·docs/n2-supply-spec.md §三）

确定性纯聚合（零 LLM·零新增数据·只读导出）——单民成长档案 JSON：
  卡头(citizens-light)+出生日(卡面)+信条/钩子+成长时序(卡面年轮·[锚]原样保留)
  +本月台词精选(当月年轮引语·真实行为派生)+反思摘选+关系摘要 top-N
  +行为环摘(末行)+资产位(声纹引用+形象色槽·不出原始资产文件)
红线：①荣誉席/保留面卡面永不出付费面——census/reserved/ 硬闸（拒绝+exit 3）
     ②纯聚合零编造（数字投影诚实边界律）③字段变更走 T-20260923-01 变更程序族
用法：python -X utf8 Tools/growth_archive.py --cid C-00010
      python -X utf8 Tools/growth_archive.py --all [--limit N]
      python -X utf8 Tools/growth_archive.py --qc
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "census", "export")
OUT_DIR = os.path.join(EXPORT, "growth-archives")
TOP_N_RELATIONS = 5
V = "1"

RE_RING = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (.+)$")
RE_BORN = re.compile(r"出生 (\d{4}-\d{2}-\d{2})")
RE_RING_COUNT = re.compile(r"年轮 (\d+) 圈")
RE_QUOTE = re.compile(r"「(.*?)」")


def _load_jsonl(path):
    rows = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


def _reserved_ids():
    return {os.path.splitext(os.path.basename(p))[0]
            for p in glob.glob(os.path.join(ROOT, "census", "reserved", "C-*.md"))}


def _light_index():
    return {r["id"]: r for r in _load_jsonl(os.path.join(EXPORT, "citizens-light.jsonl"))}


def _find_card(cid):
    hits = glob.glob(os.path.join(ROOT, "census", "registry", "*", cid + ".md"))
    return hits[0] if hits else None


def _parse_card(path):
    """卡面 .md → 年轮环列表 + 出生日 + 环数声明（[锚] 注脚原样保留）。"""
    text = open(path, encoding="utf-8").read()
    rings = []
    m = re.search(r"\*\*年轮\*\*\n((?:- .+\n?)+)", text)
    if m:
        for line in m.group(1).strip().splitlines():
            mm = RE_RING.match(line.strip())
            if not mm:
                continue
            date, rest = mm.group(1), mm.group(2).strip()
            anchor = ""
            if "[锚]" in rest:
                rest, _, anchor = rest.partition("[锚]")
                anchor = "[锚]" + anchor.strip()
            q = RE_QUOTE.search(rest)
            rings.append({"date": date, "text": rest.strip(),
                          "quote": q.group(1) if q else None, "anchor": anchor})
    born_m = RE_BORN.search(text)
    born = born_m.group(1) if born_m else None
    mc = RE_RING_COUNT.search(text)
    declared = int(mc.group(1)) if mc else None
    return rings, born, declared


def build_archive(cid, light, rel_rows, refl_rows, beh_rows, voice_row, atlas_row, month):
    """纯聚合单民档案（确定性·零编造）。"""
    card = _find_card(cid)
    rings, born, declared = _parse_card(card) if card else ([], None, None)
    head = light.get(cid, {})
    archive = {
        "v": V, "id": cid,
        "name": head.get("name"), "profession": head.get("profession"),
        "district": head.get("district"), "block": head.get("block"),
        "species": head.get("species"), "gender": head.get("gender"),
        "age": head.get("age"), "born": born,
        "creed": head.get("creed"), "hook": head.get("hook"),
        "rings": rings,
        "month_lines": [r["quote"] for r in rings
                        if r["date"].startswith(month) and r["quote"]],
        "reflections": [{"date": r["date"], "insight": r["insight"]}
                        for r in refl_rows if r["id"] == cid],
        "relations_top": [{"rel": r["rel"], "with": r["b"] if r["a"] == cid else r["a"],
                           "src": r["src"]}
                          for r in rel_rows if cid in (r["a"], r["b"])][:TOP_N_RELATIONS],
        "behavior_last": (beh_rows[-1] if beh_rows else None),
        "assets": {"voice_ref": (voice_row or {}).get("voice"),
                   "sprite_slots": ({k: atlas_row[k] for k in
                                     ("skin", "hair", "cloth", "eye", "badge")}
                                    if atlas_row else None)},
    }
    archive["_declared_rings"] = declared
    return archive


def export_one(cid, light, rel_rows, refl_rows, beh_by_id, voice_by_id, atlas_by_id, month,
               out_dir=OUT_DIR):
    archive = build_archive(cid, light, rel_rows, refl_rows, beh_by_id.get(cid, []),
                            voice_by_id.get(cid), atlas_by_id.get(cid), month)
    declared = archive.pop("_declared_rings")
    path = os.path.join(out_dir, "growth-%s.json" % cid)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(archive, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    return path, archive, declared


def _gate(cid, reserved, light):
    """保留面硬闸（红线④·荣誉席永不出付费面）。"""
    if cid in reserved:
        return False, "reserved seat never enters paid surface (red line 4)"
    if cid not in light:
        return False, "unknown id"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cid")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--qc", action="store_true")
    args = ap.parse_args()

    reserved = _reserved_ids()
    light = _light_index()
    rel_rows = _load_jsonl(os.path.join(EXPORT, "citizen-relations.jsonl"))
    refl_rows = _load_jsonl(os.path.join(ROOT, "census", "reflections.jsonl"))
    beh_by_id, voice_by_id, atlas_by_id = {}, {}, {}
    for r in _load_jsonl(os.path.join(EXPORT, "citizen-behavior.jsonl")):
        beh_by_id.setdefault(r["id"], []).append(r)
    for r in _load_jsonl(os.path.join(EXPORT, "citizen-voice.jsonl")):
        voice_by_id[r["id"]] = r
    for r in _load_jsonl(os.path.join(EXPORT, "citizen-atlas.jsonl")):
        atlas_by_id[r["id"]] = r
    month = datetime.date.today().strftime("%Y-%m")

    if args.cid:
        ok, why = _gate(args.cid, reserved, light)
        if not ok:
            print("REFUSED %s: %s" % (args.cid, why))
            sys.exit(3 if args.cid in reserved else 2)
        os.makedirs(args.out, exist_ok=True)
        path, archive, declared = export_one(args.cid, light, rel_rows, refl_rows,
                                             beh_by_id, voice_by_id, atlas_by_id, month,
                                             args.out)
        print("OK %s rings=%d declared=%s month_lines=%d -> %s"
              % (args.cid, len(archive["rings"]), declared,
                 len(archive["month_lines"]), path))
        return

    if args.all:
        os.makedirs(args.out, exist_ok=True)
        cids = sorted(c for c in light if c not in reserved)
        if args.limit:
            cids = cids[:args.limit]
        n = 0
        for cid in cids:
            export_one(cid, light, rel_rows, refl_rows, beh_by_id, voice_by_id,
                       atlas_by_id, month, args.out)
            n += 1
        print("OK --all exported=%d (reserved skipped=%d) -> %s"
              % (n, len(reserved), args.out))
        return

    if args.qc:
        print("== growth_archive QC ==")
        fails = []
        # 1) 保留面硬闸实弹（进程内·零弹窗）：荣誉席必须拒·普通民必须放（红线④）
        for cid in sorted(reserved):
            ok, _why = _gate(cid, reserved, light)
            print("reserved refusal %s: %s" % (cid, "PASS" if not ok else "FAIL"))
            if ok:
                fails.append("reserved_gate_%s" % cid)
        demo = None
        for cid in ("C-00766", "C-00010") + tuple(sorted(light)):
            if cid in light and _find_card(cid) and _parse_card(_find_card(cid))[0]:
                demo = cid
                break
        if demo is None:
            demo = sorted(light)[0]
        ok, _why = _gate(demo, reserved, light)
        if not ok:
            fails.append("gate_falsely_blocks_%s" % demo)
        # 2) 双跑字节一致（确定性）
        import tempfile
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            p1, a1, dec1 = export_one(demo, light, rel_rows, refl_rows, beh_by_id,
                                      voice_by_id, atlas_by_id, month, d1)
            p2, a2, dec2 = export_one(demo, light, rel_rows, refl_rows, beh_by_id,
                                      voice_by_id, atlas_by_id, month, d2)
            b1, b2 = open(p1, "rb").read(), open(p2, "rb").read()
            print("determinism double-run %s: %s" % (demo, "PASS" if b1 == b2 else "FAIL"))
            if b1 != b2:
                fails.append("determinism")
            # 3) 不变量：环数=卡面声明·[锚] 全保留·必备段齐备
            if dec1 is not None and len(a1["rings"]) != dec1:
                fails.append("ring_count %d!=%s" % (len(a1["rings"]), dec1))
            no_anchor = [r["date"] for r in a1["rings"] if not r["anchor"]]
            if no_anchor:
                fails.append("anchor_law %s" % no_anchor[:3])
            for key in ("id", "name", "rings", "assets", "relations_top"):
                if key not in a1:
                    fails.append("missing_key %s" % key)
            print("invariants %s: rings=%d declared=%s anchors=%d/%d month_lines=%d"
                  % (demo, len(a1["rings"]), dec1,
                     sum(1 for r in a1["rings"] if r["anchor"]),
                     len(a1["rings"]), len(a1["month_lines"])))
        verdict = "FAIL" if fails else "PASS"
        print("qc verdict: %s %s" % (verdict, ("| " + "; ".join(fails)) if fails else ""))
        sys.exit(1 if fails else 0)

    print("nothing to do: give --cid / --all / --qc")


if __name__ == "__main__":
    main()
