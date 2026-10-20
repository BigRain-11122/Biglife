#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性登记工具（R1826）：把 state/gene-cand-b24.txt 的 5 钩子+5 转折点
追加进 genes/lives.json，保留原排版（文本插入，不做整体 dump）。"""
import io
import json
import re

P = "genes/lives.json"
raw = io.open("state/gene-cand-b24.txt", encoding="utf-8").read().splitlines()
cand = [l.split("|", 1)[1].strip() for l in raw if l.strip()]
hos = [c for l in raw if l.startswith("ho|") for c in [l.split("|", 1)[1].strip()]]
tps = [c for l in raw if l.startswith("tp|") for c in [l.split("|", 1)[1].strip()]]
assert len(hos) == 5 and len(tps) == 5

t = io.open(P, encoding="utf-8").read()


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
io.open(P, "w", encoding="utf-8", newline="\n").write(t)

g = json.load(io.open(P, encoding="utf-8"))
print("counts hook=%d tp=%d" % (len(g["hook_objects"]), len(g["turning_points"])))
print("ho736:", g["hook_objects"][735][:24])
print("tp563:", g["turning_points"][562][:24])