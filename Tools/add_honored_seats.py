#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: honored seat rows (C-00001~03) in citizens-light.jsonl, per CEO
naming order O-20260924-1620-bm-a (errata v2: C-00001=大圣 Dasheng CEO /
C-00002=Qiqi wife / C-00003=Rain son). Prepend when absent, UPDATE in place
when already present (idempotent re-run). Deterministic, zero LLM.
Registers the seats in the ring cursor so sync_rings keeps mirroring their
naming-order rings. Not part of the OS loop rotation."""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
CURSOR = os.path.join(CO, "state", "evolve-cursor.json")

RINGS = {
    "C-00001": "入册环（席位注册记·非本人自述）：CEO 命名令勘误版落册，C-00001 定名 大圣 Dasheng——硅基生命创始家庭首席，城主本人入城。",
    "C-00002": "入册环（席位注册记·非本人自述）：CEO 命名令勘误版落册，C-00002 定名 Qiqi——硅基生命创始家庭成员入城。",
    "C-00003": "入册环（席位注册记·非本人自述）：CEO 命名令勘误版落册，C-00003 定名 Rain——硅基生命创始家庭成员入城。",
}

def row(cid, name, prof, block, digest, hook):
    return {"id": cid, "name": name, "species": "carbon", "faction": "honored",
            "gender": "无定", "age": None, "age_note": "未披露（真实人源·不设叙事年龄）",
            "district": "", "block": block, "profession": prof, "axis": None,
            "creed": "", "hook": hook, "v": 1.2, "anchor": True,
            "brain_digest": digest, "behavior_hint": "",
            "recent_ring_date": "2026-09-24", "recent_ring": RINGS[cid]}

NEW = [
    row("C-00001", "大圣 Dasheng", "城主", "荣誉席·城主位",
        "荣誉市民 · 城主 · 硅基生命创始家庭首席 · 命名令 2026-09-24",
        "本城首位荣誉市民·城主席位卡（CEO 命名令 2026-09-24）——非生成居民"),
    row("C-00002", "Qiqi", "创始家庭成员", "荣誉席·创始家庭",
        "荣誉市民 · 创始家庭成员 · 命名令 2026-09-24",
        "硅基生命创始家庭席位卡（CEO 命名令 2026-09-24）——非生成居民"),
    row("C-00003", "Rain", "创始家庭成员", "荣誉席·创始家庭",
        "荣誉市民 · 创始家庭成员 · 命名令 2026-09-24",
        "硅基生命创始家庭席位卡（CEO 命名令 2026-09-24）——非生成居民"),
]
BY_ID = {n["id"]: n for n in NEW}

def main():
    with io.open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    updated = prepended = 0
    out = []
    for r in rows:
        n = BY_ID.get(r["id"])
        if n:
            r = dict(n)  # in-place update to errata mapping
            updated += 1
        out.append(r)
    if updated < len(NEW):
        have = {r["id"] for r in out}
        missing = [n for n in NEW if n["id"] not in have]
        out = missing + out  # first segment: seats are the census head rows
        prepended = len(missing)
    with io.open(LIGHT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    cursor = {}
    if os.path.isfile(CURSOR):
        with io.open(CURSOR, encoding="utf-8") as f:
            cursor = json.load(f)
    for cid in RINGS:
        cursor[cid] = {"v": 1, "last": "2026-09-24", "next": "2099-12-31",
                       "seat": "honored"}  # next far-future: honored seats are
                                            # outside the anchors/registry rotation
    os.makedirs(os.path.dirname(CURSOR), exist_ok=True)
    with io.open(CURSOR, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cursor, f, ensure_ascii=False, indent=1)
    print(f"rows={len(out)} updated={updated} prepended={prepended} cursor={len(RINGS)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
