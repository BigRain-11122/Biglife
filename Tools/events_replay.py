#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Replay event shards into per-citizen vitals and diff against census cards.

Mechanical gate (R-20261023-scan-silicon-city 动作 1):
  schema errors == 0  and  replay(cards) mismatch == 0

Vitals checked: ring_count, last_ring_date, relations, household_id.
Exit code 0 only when both are zero; report written to
qa/EVENTS-REPLAY-REPORT.md (evidence face) and state/events-replay.json.
"""
import io, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from events_derive import parse_card, decode  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
EV = ROOT / "events"
REG = ROOT / "census" / "registry"
REQUIRED = ("ts", "citizen", "household_id", "type", "payload")


def replay():
    state = {}
    schema_errors = []
    n = 0
    for f in sorted(EV.glob("*.jsonl")):
        with io.open(f, encoding="utf-8") as fh:
            for i, ln in enumerate(fh, 1):
                ln = ln.strip()
                if not ln:
                    continue
                n += 1
                try:
                    e = json.loads(ln)
                except Exception as exc:
                    schema_errors.append(f"{f.name}:{i} json={exc}")
                    continue
                miss = [k for k in REQUIRED if k not in e]
                if miss:
                    schema_errors.append(f"{f.name}:{i} missing={miss}")
                    continue
                s = state.setdefault(e["citizen"], {
                    "ring_count": 0, "last_ring_date": "", "relations": set(),
                    "household_id": e["household_id"],
                })
                if e["type"] == "ring":
                    s["ring_count"] += 1
                    d = e["ts"][:10]
                    if d > s["last_ring_date"]:
                        s["last_ring_date"] = d
                elif e["type"] == "relation":
                    s["relations"].add(e["payload"].get("peer", ""))
                elif e["type"] != "birth":
                    schema_errors.append(f"{f.name}:{i} unknown type={e['type']}")
    return state, schema_errors, n


def compare(state):
    mism = []
    cards = 0
    for p in sorted(REG.rglob("C-*.md")):
        c = parse_card(p)
        cards += 1
        s = state.get(c["citizen"])
        if not s:
            mism.append(f"{c['citizen']}: no events")
            continue
        if s["ring_count"] != c["rings_declared"]:
            mism.append(f"{c['citizen']}: ring_count {s['ring_count']} != {c['rings_declared']}")
        last = c["ring_lines"][-1][0] if c["ring_lines"] else ""
        if s["last_ring_date"] != last:
            mism.append(f"{c['citizen']}: last_ring {s['last_ring_date']} != {last}")
        if set(c["relations"]) != s["relations"]:
            mism.append(f"{c['citizen']}: relations {sorted(s['relations'])} != {c['relations']}")
        if c["household_id"] and s["household_id"] != c["household_id"]:
            mism.append(f"{c['citizen']}: household {s['household_id']} != {c['household_id']}")
    return cards, mism


def main():
    state, schema_errors, n = replay()
    cards, mism = compare(state)
    ok = not schema_errors and not mism
    report = [
        "# 事件流回放验收报告（events → vitals）",
        "",
        "- 生成器：Tools/events_derive.py → events/YYYY-MM.jsonl（可重建数据面）",
        "- 回放器：Tools/events_replay.py（本次运行）",
        f"- 事件总数：{n}｜居民卡：{cards}｜回放居民：{len(state)}",
        f"- schema 错误：{len(schema_errors)}｜回放-卡片不一致：{len(mism)}",
        f"- 判定：{'PASS' if ok else 'FAIL'}",
        "",
        "## 校验口径",
        "逐居民比对：年轮条数=卡「年轮 N 圈」、末次年轮日期、关系对端集合、家户号。",
        "",
    ]
    if schema_errors[:20]:
        report += ["## schema 错误样例", *[f"- {x}" for x in schema_errors[:20]], ""]
    if mism[:20]:
        report += ["## 不一致样例", *[f"- {x}" for x in mism[:20]], ""]
    (ROOT / "qa").mkdir(exist_ok=True)
    (ROOT / "qa" / "EVENTS-REPLAY-REPORT.md").write_text("\n".join(report), encoding="utf-8")
    (ROOT / "state").mkdir(exist_ok=True)
    (ROOT / "state" / "events-replay.json").write_text(json.dumps({
        "events": n, "cards": cards, "replayed": len(state),
        "schema_errors": len(schema_errors), "mismatch": len(mism), "pass": ok,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"events={n} cards={cards} replayed={len(state)} schema_errors={len(schema_errors)} mismatch={len(mism)} -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())