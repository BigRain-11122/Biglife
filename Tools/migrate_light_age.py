#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot (T-20260926-04, law-4 age-band fix): normalize the light face's
generated rows from age=display-string ("37 岁" / "编译纪 12 年" / "第 41 数据季")
to age=int + age_note=label — the handwritten-anchor / v1.2 schema type
(generate_census L541 emitted the label into `age` at P-0; behavior.py band()
and needs.py elder/child gates are int-typed, so 9980 generated citizens fell
to "mid" and law-4 age-band differentiation was dead since P-0).
Rows with int age (handwritten anchors) / None (honored seats, undisclosed
anchors) are byte-untouched. Parses the first integer in the label; rows whose
label has no digits are skipped untouched and counted (honest skip, no guess).
Idempotent: re-run = zero changes, byte-identical. Deterministic, zero LLM,
zero network. Not part of the OS loop rotation."""
import io, json, os, re, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")

NUM = re.compile(r"(\d+)")

# behavior.py band() semantics, inlined for the post-run recount evidence
def band(age):
    if not isinstance(age, int):
        return "mid"
    if age <= 17:
        return "child"
    if age <= 25:
        return "young"
    if age < 60:
        return "mid"
    return "elder"

def main():
    with io.open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    migrated = Counter()
    untouched = Counter()
    skipped = []
    out = []
    for r in rows:
        a = r.get("age")
        if a is None or isinstance(a, int):
            untouched["int" if isinstance(a, int) else "none"] += 1
            out.append(r)
            continue
        if not isinstance(a, str):
            untouched["other"] += 1
            out.append(r)
            continue
        m = NUM.search(a)
        if not m:
            skipped.append((r.get("id"), a))
            untouched["nolabel"] += 1
            out.append(r)
            continue
        n = int(m.group(1))
        nr = {}
        for k, v in r.items():
            nr[k] = v
            if k == "age":
                nr["age"] = n
                nr["age_note"] = a
        out.append(nr)
        migrated[r.get("species", "?")] += 1

    with io.open(LIGHT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # post-run evidence: band distribution + per-species age ranges
    bands = Counter()
    rng = {}
    for r in out:
        a = r.get("age")
        bands[band(a)] += 1
        if isinstance(a, int):
            sp = r.get("species", "?")
            lo, hi = rng.get(sp, (a, a))
            rng[sp] = (min(lo, a), max(hi, a))
    print("rows=%d migrated=%s untouched=%s skipped=%d"
          % (len(out), dict(migrated), dict(untouched), len(skipped)))
    print("bands=%s" % dict(bands))
    print("age_ranges=%s" % {k: list(v) for k, v in sorted(rng.items())})
    for sid, lbl in skipped:
        print("skip %s label=%r" % (sid, lbl))
    return 0

if __name__ == "__main__":
    sys.exit(main())
