# -*- coding: utf-8 -*-
"""citizen_anchors.py v1.0 — census 住宅/工位分配表生成器（O-2026-0929-019 ⑥ 派工·T-20260929-06 step②）

契约（R3 再生面·gitignored·确定性零 LLM）:
  输入  = census/export/citizens-light.jsonl（只读·census 冻结面零触碰）
  输出  = census/export/citizen-anchors.jsonl（一行一居民：住宅/工位两锚点）
  派生  = md5(id::biglife-anchors-v1) 确定性 seed——同居民永远同锚点（禁随机·同输入双跑字节一致）
  对位  = district/block 字段逐行镜像 light 面（O-019「与 district/block 既有字段对位」）
  坐标  = 分区级先行米制包络 v1（1 格=5m 定标·城域核心 320m）：每城区一个二维包络，
          home=包络住宅带（x 向 0.08-0.42 分位）seeded 点位，work=包络工位带（x 向 0.58-0.92 分位）
          seeded 点位——住宅/工位结构性 disjoint。包络表=BigLife 单源先行草案，
          待 FluxVerse 主体施工 R0-R6 分区坐标系对账窗校准（对位后升 v2 再生全表即可，行内零手改）。
  荣誉席 = C-00001~03（faction=honored）= CEO 保留面：status=reserved，坐标零发明（home/work=null）。
  消费方 = FluxVerse 城市重构 R0-R6 居民流/走进建筑（O-019 三锚点生活空间事实源）。
  T2    = CODEX §十二 v3.54（新导出面·消费方通知走 T-20260923-01 字段变更程序族）。
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
OUT = os.path.join(ROOT, "census", "export", "citizen-anchors.jsonl")
BASIS = "biglife-anchors-v1"

# 分区级先行米制包络 v1（x0,z0)-(x1,z1)·城域核心 [-160,160]²·RV=江岸带(南)·OR=外环带(北)）
DISTRICT_ZONES = {
    "QT": (-160.0, 10.0, -10.0, 160.0),
    "GM": (10.0, 10.0, 160.0, 160.0),
    "MD": (-160.0, -160.0, -10.0, -10.0),
    "NS": (10.0, -160.0, 160.0, -10.0),
    "RV": (-160.0, -260.0, 160.0, -165.0),
    "OR": (-160.0, 165.0, 160.0, 260.0),
}


def _seed_point(cid, salt, zone, lo_frac, hi_frac):
    h = hashlib.md5(f"{cid}::{BASIS}::{salt}".encode("utf-8")).digest()
    x0, z0, x1, z1 = zone
    fx = lo_frac + (int.from_bytes(h[0:8], "big") / 2**64) * (hi_frac - lo_frac)
    fz = int.from_bytes(h[8:16], "big") / 2**64
    return round(x0 + fx * (x1 - x0), 2), round(z0 + fz * (z1 - z0), 2)


def build_rows():
    rows = []
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid, district, block = r["id"], r.get("district", ""), r.get("block", "")
            prof = r.get("profession", "")
            if not district or district not in DISTRICT_ZONES:
                rows.append({"id": cid, "district": district, "block": block,
                             "profession": prof,
                             "home": None, "work": None, "status": "reserved",
                             "note": "荣誉席=CEO 保留面·坐标零发明", "v": 1})
                continue
            zone = DISTRICT_ZONES[district]
            hx, hz = _seed_point(cid, "home", zone, 0.08, 0.42)
            wx, wz = _seed_point(cid, "work", zone, 0.58, 0.92)
            rows.append({"id": cid, "district": district, "block": block,
                         "profession": prof,
                         "home": {"x": hx, "z": hz},
                         "work": {"x": wx, "z": wz, "site": f"{prof}·{block}工位"},
                         "status": "ok", "v": 1})
    return rows


def write(rows, path=OUT):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def qc():
    with open(LIGHT, encoding="utf-8") as f:
        light = [json.loads(l) for l in f]
    rows = build_rows()
    errs = []
    if len(rows) != len(light):
        errs.append(f"rows {len(rows)} != light {len(light)}")
    for r, l in zip(rows, light):
        if r["id"] != l["id"]:
            errs.append(f"id mismatch {r['id']} != {l['id']}"); break
    reserved = 0
    for r, l in zip(rows, light):
        if r["district"] != l.get("district", "") or r["block"] != l.get("block", ""):
            errs.append(f"mirror fail {r['id']}"); break
        if r["status"] == "reserved":
            reserved += 1
            if l.get("faction") != "honored":
                errs.append(f"non-honored reserved {r['id']}"); break
            continue
        zone = DISTRICT_ZONES[r["district"]]
        for a in (r["home"], r["work"]):
            if not (zone[0] <= a["x"] <= zone[2] and zone[1] <= a["z"] <= zone[3]):
                errs.append(f"out-of-zone {r['id']}"); break
        if r["home"] == r["work"]:
            errs.append(f"home==work {r['id']}"); break
        if not r["work"].get("site"):
            errs.append(f"empty site {r['id']}"); break
    # 确定性：双跑逐字节一致 + 同 id 重派生稳定
    r2 = build_rows()
    b1 = [json.dumps(x, ensure_ascii=False) for x in rows]
    b2 = [json.dumps(x, ensure_ascii=False) for x in r2]
    if b1 != b2:
        errs.append("double-run mismatch")
    if errs:
        print("QC FAIL:"); [print(" -", e) for e in errs]; return 1
    print(f"QC PASS: rows={len(rows)} light={len(light)} reserved={reserved} "
          f"ok={len(rows)-reserved} zones={len(DISTRICT_ZONES)} double_run=identical")
    return 0


def main():
    if "--qc" in sys.argv:
        sys.exit(qc())
    rows = build_rows()
    write(rows)
    print(f"wrote {len(rows)} rows -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
