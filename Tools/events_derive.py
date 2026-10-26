#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Derive append-only event shards from census cards (R-20261023-scan-silicon-city 动作 1).

Output: events/YYYY-MM.jsonl, one record per line:
  {"ts": iso8601, "citizen": "C-xxxxx", "household_id": "H-XXXX", "type": "birth|ring|relation", "payload": {...}}

Cards are the source of truth; event shards are regenerable (gitignored data face).
"""
import argparse, io, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REG = ROOT / "census" / "registry"
ANCH = ROOT / "census" / "anchors"  # 手写展示锚居民（CODEX §十二 4·展示级锚覆盖全物种派系×城区）
OUT = ROOT / "events"


def card_paths():
    """可派生卡全集=生成卡（registry）+ 手写锚卡（anchors）。reserved 荣誉席不参与叙事事件流。"""
    return sorted(REG.rglob("C-*.md")) + sorted(ANCH.rglob("C-*.md"))

RE_ID = re.compile(r"C-\d{5}")
RE_HH = re.compile(r"H-[A-Z]{2}\d{4}")
RE_BIRTH = re.compile(r"出生\s*(\d{4}-\d{2}-\d{2})")
RE_RINGS = re.compile(r"年轮\s*(\d+)\s*圈")


def decode(p):
    b = p.read_bytes()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("gbk")


def parse_card(path):
    text = decode(path)
    lines = text.splitlines()
    cid = path.stem
    district = ""
    household = ""
    birth = None
    rings_declared = None
    ring_lines = []
    relations = set()
    batch = ""
    in_rings = False

    for ln in lines:
        if ln.startswith("**物种**"):
            m = re.search(r"城区\*\*\s*([^｜]+)", ln)
            if m:
                district = m.group(1).strip()
        elif ln.startswith("**进化**"):
            mb = RE_BIRTH.search(ln)
            mr = RE_RINGS.search(ln)
            birth = mb.group(1) if mb else None
            rings_declared = int(mr.group(1)) if mr else 0
            in_rings = False
        elif ln.startswith("**年轮**"):
            in_rings = True
        elif ln.startswith("**") and in_rings:
            in_rings = False
        elif in_rings and ln.startswith("- "):
            m = re.match(r"- (\d{4}-\d{2}-\d{2})\s+(.*)", ln)
            if m:
                ring_lines.append((m.group(1), m.group(2).strip()))
        elif ln.startswith("**关系**"):
            household = (RE_HH.search(ln) or [""])[0] if RE_HH.search(ln) else ""
            relations.update(x for x in RE_ID.findall(ln) if x != cid)
        elif ln.startswith("**溯源**"):
            mb2 = re.search(r"生成批次\s*(\S+)", ln)
            if mb2:
                batch = mb2.group(1)

    if not birth:
        birth = "2026-09-23"
    return {
        "citizen": cid,
        "district": district,
        "household_id": household,
        "birth": birth,
        "rings_declared": rings_declared if rings_declared is not None else len(ring_lines),
        "ring_lines": ring_lines,
        "relations": sorted(relations),
        "batch": batch,
    }


def events_for(card):
    out = [{
        "ts": card["birth"] + "T00:00:00",
        "citizen": card["citizen"],
        "household_id": card["household_id"],
        "type": "birth",
        "payload": {"district": card["district"], "batch": card["batch"]},
    }]
    for date, text in card["ring_lines"]:
        out.append({
            "ts": date + "T00:00:00",
            "citizen": card["citizen"],
            "household_id": card["household_id"],
            "type": "ring",
            "payload": {"text": text, "anchor": "[锚]" in text},
        })
    for peer in card["relations"]:
        out.append({
            "ts": card["birth"] + "T00:00:00",
            "citizen": card["citizen"],
            "household_id": card["household_id"],
            "type": "relation",
            "payload": {"peer": peer},
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cards = card_paths()
    if args.limit:
        cards = cards[: args.limit]

    OUT.mkdir(exist_ok=True)
    shards = {}
    for p in cards:
        for ev in events_for(parse_card(p)):
            shards.setdefault(ev["ts"][:7], []).append(ev)

    total = 0
    for month, evs in sorted(shards.items()):
        evs.sort(key=lambda e: (e["ts"], e["citizen"], e["type"]))
        f = OUT / f"{month}.jsonl"
        with io.open(f, "w", encoding="utf-8", newline="\n") as fh:
            for e in evs:
                fh.write(json.dumps(e, ensure_ascii=False, separators=(",", ":")) + "\n")
        total += len(evs)
        print(f"wrote {f.relative_to(ROOT)} events={len(evs)}")
    print(f"OK cards={len(cards)} events={total} shards={len(shards)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())