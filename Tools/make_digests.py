#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_digests.py - brain digest enrichment for citizens-light.jsonl (v1.1).

Adds brain_digest (<=200 chars: axis/creed/traits/profession/catchphrase/hook)
and behavior_hint (rhythm phrase <=60 chars) to every citizen, derived from
the census cards (read-only on cards; only the EXPORT face is rewritten).
Digest = innate identity only; rings (memory) are NOT in the digest by law
(cognition/README: digest=identity, rings=memory).
QC gate: 10000 lines, valid JSON, digest/hint present, length bounds.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")
LIGHT = os.path.join(CENSUS, "export", "citizens-light.jsonl")

def find_card(cid, district=None):
    if cid <= "C-00029":
        p = os.path.join(CENSUS, "anchors", cid + ".md")
        if os.path.isfile(p):
            return p
        p = os.path.join(CENSUS, "reserved", cid + ".md")  # honored seats C-00001~03
        if os.path.isfile(p):
            return p
    subs = ["anchors"] if cid <= "C-00029" else ["registry"]
    for sub in subs:
        d = os.path.join(CENSUS, sub)
        if not os.path.isdir(d): continue
        if district and sub == "registry":
            p = os.path.join(d, district, cid + ".md")
            if os.path.isfile(p):
                return p
        for root, _, files in os.walk(d):
            if cid + ".md" in files:
                return os.path.join(root, cid + ".md")
    return None

def grab(text, label):
    m = re.search(r"\*\*" + label + r"\*\* (.+)", text)
    return m.group(1).strip() if m else ""

def latest_ring(text):
    """Newest ring entry from a card: (date, inner text) or (None, None)."""
    m = re.search(r"\*\*年轮\*\*\n((?:- .*\n?)+)", text)
    if not m:
        return None, None
    entries = re.findall(r"- (\d{4}-\d{2}-\d{2}) 「(.*?)」", m.group(1))
    if not entries:
        return None, None
    d, t = entries[-1]
    return d, t.strip()

def main():
    with open(LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    out, bad = [], 0
    for r in rows:
        cid = r["id"]
        p = find_card(cid, r.get("district"))
        if not p:
            bad += 1
            r["brain_digest"] = ""
            r["behavior_hint"] = ""
            r["recent_ring_date"] = ""
            r["recent_ring"] = ""
            r["v"] = 1.2
            out.append(r)
            continue
        with open(p, encoding="utf-8") as fh:
            t = fh.read()
        traits = grab(t, "性格")
        # trait names only (first 3, strip notes in parens)
        tnames = []
        for seg in traits.split("·"):
            seg = seg.strip()
            name = re.sub(r"（.*?）", "", seg).strip()
            if name: tnames.append(name)
        tnames = tnames[:3]
        lang = grab(t, "语言")
        # first catchphrase in 「」 or first 20 chars of dialect base
        catch = ""
        m = re.search(r"口头禅「(.+?)」", lang)
        if m: catch = m.group(1)
        else:
            m2 = re.search(r"「(.+?)」", lang)
            if m2: catch = m2.group(1)
        prof = grab(t, "职业")
        prof = re.split(r"[：:——]", prof, 1)[0]
        behavior = grab(t, "行为")
        hint = re.split(r"[；;]", behavior)[0].strip()
        if len(hint) > 60: hint = hint[:60]
        hook = grab(t, "钩子")
        hook = re.sub(r"^全城唯一", "", hook).strip("。")
        parts = []
        if r.get("axis"): parts.append(r["axis"] + "轴")
        if tnames: parts.append("/".join(tnames))
        if prof: parts.append(prof)
        if catch: parts.append("口头禅「" + catch + "」")
        if hook: parts.append("独有：" + hook[:30])
        if r.get("creed"): parts.append("信条：「" + r["creed"] + "」")
        digest = " · ".join(parts)
        if len(digest) > 200: digest = digest[:200]
        r["brain_digest"] = digest
        r["behavior_hint"] = hint
        rd, rt = latest_ring(t)
        r["recent_ring_date"] = rd or ""
        r["recent_ring"] = (rt or "")[:80]
        r["v"] = 1.2
        out.append(r)
    with open(LIGHT, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    missing_digest = sum(1 for r in out if not r.get("brain_digest"))
    missing_hint = sum(1 for r in out if not r.get("behavior_hint"))
    overlong = sum(1 for r in out if len(r.get("brain_digest", "")) > 200)
    no_ringfield = sum(1 for r in out if "recent_ring" not in r or "recent_ring_date" not in r)
    ring_rows = sum(1 for r in out if r.get("recent_ring"))
    print(f"rows={len(out)} no_card={bad} missing_digest={missing_digest} "
          f"missing_hint={missing_hint} overlong={overlong} "
          f"no_ringfield={no_ringfield} ring_rows={ring_rows}")
    sys.exit(1 if (bad or missing_digest or overlong or no_ringfield) else 0)

if __name__ == "__main__":
    main()
