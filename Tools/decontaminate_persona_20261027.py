# -*- coding: utf-8 -*-
"""R2437 persona feed decontamination (one-off, re-runnable/idempotent).

R2433 established the two-sided fix for the latin-machine-word leak:
feed-side scrub + birth-station gate.  R2436/R2437 showed the gate alone
cannot help three citizens (C-01624 skipped two rounds running) because the
words live in the *gene templates* themselves: `genes/professions.json`
carries the profession rhythm 「放学绕路只为看一眼今日 commit 光点过江」
and the name 「bug 猎人」, `genes/personality.json`/`lives.json`/`anchors.json`
carry 「commit 光点过江」.  Those strings are baked into every card born from
them and are fed to the prompt verbatim as 职业/行为, so the model reproduces
them and the gate rejects the ring forever — a permanent due-loop.

Fix at the birth place: rewrite the templates, then normalize the persona
head (everything before **年轮**) of cards already born.  Rings are history
and stay untouched (#41 前朝不追溯).
"""
import io
import glob
import re
import sys

REPLACEMENTS = [
    ("commit 光点", "信号光点"),
    ("bug 猎人", "捉虫人"),
    # second sweep: the same templates carry three more latin tokens in the
    # prompt-fed fields (职业/行为).  `sprite` as a species id in genes stays
    # untouched - only the profession twist sentence is rewritten.
    ("手作 sprite 城里独一份", "手作像素画 城里独一份"),
    ("夜里的 bug 最爱出来透气", "夜里的虫子最爱出来透气"),
    ("全城 commit 编目", "全城光点编目"),
]

GENE_FILES = [
    "genes/anchors.json",
    "genes/lives.json",
    "genes/personality.json",
    "genes/professions.json",
]

# tool fixtures that name the same strings (test corpus + profession allowlist)
TOOL_FILES = [
    "Tools/political_redline.py",
    "Tools/sublimate_audit.py",
]


def rewrite(path, text):
    out = text
    n = 0
    for old, new in REPLACEMENTS:
        c = out.count(old)
        if c:
            out = out.replace(old, new)
            n += c
    if n:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(out)
    return n


def main():
    dry = "--dry-run" in sys.argv
    total = {"genes": 0, "tools": 0, "cards": 0, "cards_touched": 0}

    for path in GENE_FILES + TOOL_FILES:
        try:
            text = io.open(path, encoding="utf-8").read()
        except IOError:
            print("MISSING", path)
            continue
        if dry:
            n = sum(text.count(old) for old, _ in REPLACEMENTS)
        else:
            n = rewrite(path, text)
        key = "genes" if path.startswith("genes") else "tools"
        total[key] += n
        if n:
            print("%s %s (%d)" % ("WOULD-FIX" if dry else "FIXED", path, n))

    for path in sorted(glob.glob("census/registry/**/C-*.md", recursive=True)):
        text = io.open(path, encoding="utf-8").read()
        if "**年轮**" in text:
            head, tail = text.split("**年轮**", 1)
            tail = "**年轮**" + tail
        else:
            head, tail = text, ""
        hits = sum(head.count(old) for old, _ in REPLACEMENTS)
        if not hits:
            continue
        if dry:
            total["cards"] += hits
            total["cards_touched"] += 1
            continue
        new_head = head
        for old, new in REPLACEMENTS:
            new_head = new_head.replace(old, new)
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_head + tail)
        total["cards"] += hits
        total["cards_touched"] += 1

    print("SUMMARY genes=%d tools=%d cards_touched=%d phrases=%d"
          % (total["genes"], total["tools"], total["cards_touched"], total["cards"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())