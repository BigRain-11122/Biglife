#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: prepend honored seat rows (C-00001~03) to citizens-light.jsonl
(CEO naming order O-20260924-1620-bm-a item 4) + register them in the ring
cursor so sync_rings keeps mirroring their naming-order rings.
Deterministic, zero LLM. Run once; not part of the OS loop rotation."""
import io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
CURSOR = os.path.join(CO, "state", "evolve-cursor.json")

RINGS = {
    "C-00001": "入册环（席位注册记·非本人自述）：CEO 命名令落册，C-00001 定名 Rain——硅基生命创始家庭首席，城主本人入城。",
    "C-00002": "入册环（席位注册记·非本人自述）：CEO 命名令落册，C-00002 定名 Qiqi——硅基生命创始家庭成员入城。",
    "C-00003": "入册环（席位注册记·非本人自述）：CEO 命名令落册，C-00003 定名 Dasheng——硅基生命创始家庭成员入城。",
}

def row(cid, name, prof, block, digest, hook):
    return {"id": cid, "name": name, "species": "carbon", "faction": "honored",
            "gender": "无定", "age": None, "age_note": "未披露（真实人源·不设叙事年龄）",
            "district": "", "block": block, "profession": prof, "axis": None,
            "creed": "", "hook": hook, "v": 1.2, "anchor": True,
            "brain_digest": digest, "behavior_hint": "",
            "recent_ring_date": "2026-09-24", "recent_ring": RINGS[cid]}

NEW = [
    row("C-00001", "Rain", "城主", "荣誉席·城主位",
        "荣誉市民 · 城主 · 硅基生命创始家庭首席 · 命名令 2026-09-24",
        "本城首位荣誉市民·城主席位卡（CEO 命名令 2026-09-24）——非生成居民"),
    row("C-00002", "Qiqi", "创始家庭成员", "荣誉席·创始家庭",
        "荣誉市民 · 创始家庭成员 · 命名令 2026-09-24",
        "硅基生命创始家庭席位卡（CEO 命名令 2026-09-24）——非生成居民"),
    row("C-00003", "Dasheng", "创始家庭成员", "荣誉席·创始家庭",
        "荣誉市民 · 创始家庭成员 · 命名令 2026-09-24",
        "硅基生命创始家庭席位卡（CEO 命名令 2026-09-24）——非生成居民"),
]

def main():
    with io.open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    ids = {r["id"] for r in rows}
    clash = [n["id"] for n in NEW if n["id"] in ids]
    if clash:
        print("already present:", clash)
        return 1
    for n in NEW:
        n["recent_ring"] = n["recent_ring"][:80]
    out = NEW + rows
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
    print(f"rows={len(out)} prepended={len(NEW)} cursor_added={len(RINGS)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
