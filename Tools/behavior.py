#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""behavior.py - P-75 behavior derivation layer (SILICON-LIFE sign #8 extension).

V2-A sibling of needs.py: deterministic behavior states for ALL citizens.
Input: census/export/citizen-needs.jsonl (auto-regen via needs.py if missing)
+ real time window + weather -> output census/export/citizen-behavior.jsonl
(R3 regenerable face - gitignored; consumed by FluxVerse M2 NPC engine).
Four laws = cph4/research/R-20260924-resident-behavior.md section 1:
1) needs->behavior chain  2) population rhythm  3) weather reaction
4) personality split (species / age band / hash(id) quirks).
Zero LLM, zero API. Same (persona, time window, weather, needs snapshot)
=> byte-identical output. Usage: python -X utf8 behavior.py [--qc]
"""
import hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import needs  # V2-A sibling: LIGHT / OUT / NEED_KEYS / city_signals() / derive()

OUT_BEH = os.path.join(needs.CO, "census", "export", "citizen-behavior.jsonl")

RAIN_KINDS = ("rain", "snow", "shower", "drizzle", "typhoon")
TRADER_RE = re.compile(r"交易|量化|风控|行情|回测|操盘|盘口|瞭望|对冲|期货")
STATES = {"sleep", "home", "work", "commute", "school", "meal", "social", "explore",
          "exercise", "run", "shelter", "indoors", "night_shift", "night_light",
          "charge"}
QUIRKS = ("", "slow", "umbrella", "night_run")


def shash(cid):
    # stable per-id hash (python hash() is process-randomized - never use it)
    return int(hashlib.md5(str(cid).encode("utf-8")).hexdigest()[:8], 16)


def quirk_of(h):
    r = h % 100
    if r < 5:
        return "slow"        # 5% slow walker
    if r < 10:
        return "umbrella"    # 5% umbrella-always
    if r < 13:
        return "night_run"   # 3% night runner
    return ""


def window(m):
    """minute-of-day -> rhythm window (law 2)."""
    if m < 390:
        return "night"       # 00:00-06:29 street ~= 0 (night duty only)
    if m < 450:
        return "dawn"        # 06:30-07:29
    if m < 570:
        return "empk"        # 07:30-09:29 morning peak
    if m < 690:
        return "day"
    if m < 780:
        return "meal"        # 11:30-13:00 lunch
    if m < 1050:
        return "day"         # work hours / at home
    if m < 1140:
        return "meal"        # 17:30-19:00 dinner
    if m < 1200:
        return "evpk"        # 19:00-20:00 evening peak tail
    if m < 1380:
        return "eve"         # 20:00-23:00 low-mid (social high out)
    return "night"           # 23:00-23:59


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


def derive(r, nk, top, sig, w, weekend):
    """Law 1/2/4 -> (state, slot, visible); law 3 weather override last."""
    sp = r.get("species") or ""
    b = band(r.get("age"))
    d = r.get("district") or ""
    prof = r.get("profession") or ""
    h = shash(r.get("id") or "")
    q = quirk_of(h)
    wx = sig["weather"]

    if sp == "silicon":
        # silicon: machine-room cold grey + night-shift lean; strain -> charge
        if w == "night" or (w in ("dawn", "day", "empk", "evpk", "eve") and nk["anwen"] >= 1):
            st, slot, vis = "charge", "机房/充电位", 0
        elif w in ("empk", "evpk"):
            st, slot, vis = "commute", "通勤街面", 1
        else:
            st, slot, vis = "work", "机房·工位", 0
    elif sp == "sprite":
        # sprite: night-running light spots at riverside/plaza; day roost
        if w in ("night", "eve", "evpk"):
            st, slot, vis = "night_light", "江边/广场·光点", 1
        else:
            st, slot, vis = "home", "栖位", 0
    else:
        trader = d == "QT" and bool(TRADER_RE.search(prof)) and b in ("mid", "young")
        if w == "night":
            if trader and nk["shengji"] >= 1:
                st, slot, vis = "night_shift", "夜盘岗位", 0      # QUANT night session
            elif q == "night_run" and b in ("young", "mid"):
                st, slot, vis = "run", "夜跑路线", 1
            else:
                st, slot, vis = "sleep", "家户·就寝", 0
        elif w == "dawn":
            if b == "elder":
                st, slot, vis = "exercise", "广场·晨练", 1
            else:
                st, slot, vis = "home", "宅户", 0
        elif w == "empk":
            if b == "child":
                st, slot, vis = "commute", "通学路上", 1
            elif b == "elder":
                st, slot, vis = "exercise", "广场·晨练", 1
            else:
                st, slot, vis = "commute", "通勤街面", 1
        elif w == "day":
            if not weekend and b == "child":
                st, slot, vis = "school", "学堂", 0
            elif b == "elder":
                st, slot, vis = "home", "宅户·白天", 0
            elif not weekend and b in ("mid", "young") and nk["shengji"] >= 1:
                st, slot, vis = "work", "工位/楼内窗影", 0
            elif nk["haoqi"] >= 2:
                st, slot, vis = "explore", "探索位·新街区", 1
            elif nk["shejiao"] >= 1:
                st, slot, vis = "social", "广场聚集", 1
            else:
                st, slot, vis = "home", "宅户", 0
        elif w == "meal":
            slot = "餐饮街·软食铺" if b == "elder" else "餐饮街"
            st, slot, vis = "meal", slot, 1
        elif w == "evpk":
            if b == "child":
                st, slot, vis = "home", "家户", 0
            elif b == "elder":
                st, slot, vis = "home", "宅户", 0
            elif h % 2 == 0:
                st, slot, vis = "meal", "餐饮街", 1
            else:
                st, slot, vis = "commute", "通勤街面", 1
        else:  # eve 20:00-23:00
            if b == "child":
                st, slot, vis = "home", "家户", 0
            elif b == "elder":
                st, slot, vis = "home", "宅户", 0
            elif b == "young" or nk["shejiao"] >= 1:
                st, slot, vis = "social", "广场/江边", 1
            elif nk["haoqi"] >= 2:
                st, slot, vis = "explore", "探索位·新街区", 1
            elif nk["anwen"] >= 2:
                st, slot, vis = "home", "宅户", 0
            else:
                st, slot, vis = "home", "宅户", 0

    # law 3: rain/snow drives street-visible citizens under cover;
    # road-visible keeps <=30% of clear-same-clock (umbrella quirk only),
    # sheltered spots stay visible
    if wx in RAIN_KINDS and vis == 1:
        if q == "umbrella":
            st, slot, vis = "shelter", "街面·伞", 1
        elif h % 10 < 3:
            st, slot, vis = "shelter", "骑楼/檐下", 1
        else:
            st, slot, vis = "indoors", "窗后/廊道内", 0

    return {"id": r.get("id"), "state": st, "slot": slot, "visible": vis,
            "quirk": q, "v": 1,
            "ctx": "tw=%s,wx=%s,wd=%d" % (w, wx or "na", 1 if weekend else 0)}


def load_needs(sig, hb, rows):
    """citizen-needs.jsonl input face; same-snapshot in-process fallback."""
    if not os.path.exists(needs.OUT):
        try:
            subprocess.run([sys.executable, "-X", "utf8",
                            os.path.join(HERE, "needs.py")], cwd=HERE, timeout=120)
        except Exception:
            pass
    nmap = {}
    if os.path.exists(needs.OUT):
        try:
            with open(needs.OUT, encoding="utf-8") as f:
                for ln in f:
                    if ln.strip():
                        o = json.loads(ln)
                        nmap[o.get("id")] = o
        except Exception:
            nmap = {}
    def get(r):
        o = nmap.get(r.get("id"))
        if o and set((o.get("needs") or {}).keys()) == set(needs.NEED_KEYS):
            return o["needs"], o.get("top") or "anwen"
        return needs.derive(r, sig, hb)  # deterministic same-snapshot fallback
    return get


def main():
    qc_only = "--qc" in sys.argv
    sig = needs.city_signals()
    now = sig["now"]
    w = window(now.hour * 60 + now.minute)
    weekend = now.weekday() >= 5
    hb = now.hour // 3

    if not qc_only:
        with open(needs.LIGHT, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        getn = load_needs(sig, hb, rows)
        out = []
        for r in rows:
            nk, top = getn(r)
            out.append(derive(r, nk, top, sig, w, weekend))
        tmp = OUT_BEH + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            for o in out:
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
        os.replace(tmp, OUT_BEH)

    # QC pass (always): id order, schema, determinism sample, rain road-ratio
    with open(needs.LIGHT, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    with open(OUT_BEH, encoding="utf-8") as f:
        brows = [json.loads(l) for l in f if l.strip()]
    bad = 0
    if len(brows) != len(rows):
        print("QC FAIL rows %d != light %d" % (len(brows), len(rows)))
        bad += 1
    for i, (r, o) in enumerate(zip(rows, brows)):
        if o.get("id") != r.get("id") or o.get("state") not in STATES \
           or o.get("visible") not in (0, 1) or o.get("quirk") not in QUIRKS:
            bad += 1
    # determinism: rebuild a spread sample through the same pure pipeline
    if not qc_only:
        getn = load_needs(sig, hb, rows)
        for i in range(0, len(rows), 97):
            r = rows[i]
            nk, top = getn(r)
            if json.dumps(derive(r, nk, top, sig, w, weekend),
                          ensure_ascii=False) != json.dumps(brows[i], ensure_ascii=False):
                bad += 1
    # law 3 invariant: rainy road-visible (non-shelter) <= ~30% of cover-bound
    if sig["weather"] in RAIN_KINDS:
        shelter = sum(1 for o in brows if o["state"] == "shelter")
        road = sum(1 for o in brows if o["visible"] == 1 and o["state"] != "shelter")
        bound = shelter + road
        if bound and road / bound > 0.31:
            print("QC FAIL rain road ratio %.2f" % (road / bound))
            bad += 1
    dist = {}
    for o in brows:
        dist[o["state"]] = dist.get(o["state"], 0) + 1
    top3 = sorted(dist.items(), key=lambda kv: -kv[1])[:3]
    print("rows=%d bad=%d tw=%s wx=%s wd=%d top3=%s" %
          (len(brows), bad, w, sig["weather"] or "na", sig["now"].weekday(), top3))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
