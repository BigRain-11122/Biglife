#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（R1830）：把 state/gene-cand-b25.txt 的 5 钩子+5 转折点
追加进 genes/lives.json，保留原排版（文本插入，不做整体 dump）。"""
import io
import json
import re

P = "genes/lives.json"
SRC = "state/gene-cand-b25.txt"
with io.open(SRC, encoding="utf-8") as f:
    raw = f.read().splitlines()
hos = [l.split("|", 1)[1].strip() for l in raw if l.startswith("ho|")]
tps = [l.split("|", 1)[1].strip() for l in raw if l.startswith("tp|")]
assert len(hos) == 5 and len(tps) == 5

with io.open(P, encoding="utf-8") as f:
    t = f.read()


def append(key, items):
    global t
    m = re.search(r'("%s":\s*\[)(.*?)(\n\s*\])' % key, t, re.S)
    if not m:
        raise SystemExit("no array found: " + key)
    add = "".join(",\n      " + json.dumps(x, ensure_ascii=False) for x in items)
    t = t[:m.end(2)] + add + t[m.end(2):]
    print("appended", len(items), "->", key)


append("hook_objects", hos)
append("turning_points", tps)
with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write(t)

with io.open(P, encoding="utf-8") as f:
    g = json.load(f)
print("counts hook=%d tp=%d" % (len(g["hook_objects"]), len(g["turning_points"])))
print("ho741:", g["hook_objects"][740][:24])
print("tp568:", g["turning_points"][567][:24])