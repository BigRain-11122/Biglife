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
T-20260924-16d step 2 (contract cognition/NEEDS-CRASH.md): crash overlay -
needs-face crash rows map to three visible negative states by axis;
recovering rows keep state + flag; law-8.3 caps truncate deterministically.
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
          "charge"} | {"slump", "grumble", "fumble"}
QUIRKS = ("", "slow", "umbrella", "night_run")

# T-20260924-16d step 2 (contract cognition/NEEDS-CRASH.md §二.2 + §四.5):
# axis -> negative state map; caps per SILICON-LIFE law-8.3 - whole-city
# crash population <= CITY_CAP, per-district visible crash <= CRASH_CAP;
# overflow truncates deterministically by (axis strength, hash(id)). Both
# thresholds parameterized = CEO one-line retune face.
NEG_STATES = {"slump", "grumble", "fumble"}
NEG_OF_AXIS = {"anwen": "fumble", "shengji": "slump",
               "shejiao": "grumble", "haoqi": "slump"}
CRASH_CAP = 0.05   # same-district same-clock visible crash residents
CITY_CAP = 0.03    # whole-city crash population (anti Oblivion cascade)


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


def derive(r, nk, top, sig, w, weekend, crash=None, cax=None, vis_ok=True):
    """Law 1/2/4 -> (state, slot, visible); law 3 weather override last;
    T-16d crash overlay after weather law (negative visibility is deliberate,
    density bounded by CRASH_CAP - QC rain-ratio counts non-crash rows only)."""
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

    o = {"id": r.get("id"), "state": st, "slot": slot, "visible": vis,
         "quirk": q, "v": 1,
         "ctx": "tw=%s,wx=%s,wd=%d" % (w, wx or "na", 1 if weekend else 0)}
    # T-20260924-16d: crash overlay (contract §二.2). grumble = visible at
    # stall/plaza; slump/fumble keep the (weather-adjusted) base slot with a
    # tag; recovering keeps state, adds flag only. vis_ok=False = district
    # CRASH_CAP truncation -> stay crash-state but visible=0.
    if crash == "crash" and cax in NEG_OF_AXIS \
       and str(r.get("id")) not in needs.HONORED_IDS:
        st2 = NEG_OF_AXIS[cax]
        o["state"] = st2
        o["crash_axis"] = cax
        if st2 == "grumble":
            o["slot"] = "摊位/广场·抱怨"
            o["visible"] = 1 if vis_ok else 0
        else:
            o["slot"] = slot + ("·带错" if st2 == "fumble" else "·怠工")
            if not vis_ok:
                o["visible"] = 0
    elif crash == "recovering" and cax in NEG_OF_AXIS \
         and str(r.get("id")) not in needs.HONORED_IDS:
        o["recovering"] = cax
    return o


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
            return (o["needs"], o.get("top") or "anwen",
                    o.get("crash"), o.get("crash_axis"))
        # same-snapshot fallback; derive_full with default reg_rows keeps the
        # legacy needs values byte-identical while exposing the crash pair
        return needs.derive_full(r, sig, hb)
    return get


def crash_caps(rows, getn, sig, w, weekend):
    """Law-8.3 truncation plan (pure): returns (city_keep, dist_vis_ok) id
    sets. City overflow (CITY_CAP) reverts to base behavior in final_row;
    district visible overflow (CRASH_CAP) keeps the crash state at visible=0.
    Order key = (axis strength desc, hash(id)) - deterministic."""
    cands = []
    for r in rows:
        nk, _top, crash, cax = getn(r)
        if crash == "crash" and cax in NEG_OF_AXIS \
           and str(r.get("id")) not in needs.HONORED_IDS:
            cands.append((r, nk, _top, cax))
    if not cands:
        return set(), set()
    kmax = int(CITY_CAP * len(rows))
    if len(cands) > kmax:
        cands = sorted(cands, key=lambda t: (-t[1].get(t[3], 0),
                                             shash(t[0].get("id") or "")))[:kmax]
    city_keep = {str(t[0].get("id")) for t in cands}
    dist_pop = {}
    for r in rows:
        d = r.get("district") or "?"
        dist_pop[d] = dist_pop.get(d, 0) + 1
    vis_by_d = {}
    for r, nk, top, cax in cands:
        if NEG_OF_AXIS[cax] != "grumble":
            base = derive(r, nk, top, sig, w, weekend)
            if base["visible"] != 1:
                continue  # slump/fumble inherit base visibility only
        vis_by_d.setdefault(r.get("district") or "?", []).append(
            (-nk.get(cax, 0), shash(r.get("id") or ""), str(r.get("id"))))
    dist_vis_ok = set()
    for d, lst in vis_by_d.items():
        lst.sort()
        dist_vis_ok.update(x[2] for x in lst[:int(CRASH_CAP * dist_pop.get(d, 0))])
    return city_keep, dist_vis_ok


def final_row(r, getn, city_keep, dist_vis_ok, sig, w, weekend):
    """Write-face row: base derive + crash overlay under the caps plan."""
    nk, top, crash, cax = getn(r)
    eff, vis_ok = crash, True
    if crash == "crash":
        cid = str(r.get("id"))
        if cid in city_keep:
            vis_ok = cid in dist_vis_ok
        else:
            eff = None  # CITY_CAP overflow -> base behavior, no crash state
    return derive(r, nk, top, sig, w, weekend, eff, cax, vis_ok)


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
        city_keep, dist_vis_ok = crash_caps(rows, getn, sig, w, weekend)
        out = []
        for r in rows:
            out.append(final_row(r, getn, city_keep, dist_vis_ok, sig, w, weekend))
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
        # T-16d: crash overlay schema (crash_axis pairing + honored exclusion)
        st = o.get("state")
        if st in NEG_STATES:
            if o.get("crash_axis") not in NEG_OF_AXIS:
                bad += 1
            if str(r.get("id")) in needs.HONORED_IDS:
                bad += 1
        rec = o.get("recovering")
        if rec is not None:
            if rec not in NEG_OF_AXIS or st in NEG_STATES:
                bad += 1
            if str(r.get("id")) in needs.HONORED_IDS:
                bad += 1
    # determinism: rebuild a spread sample through the same pure pipeline
    if not qc_only:
        getn = load_needs(sig, hb, rows)
        city_keep, dist_vis_ok = crash_caps(rows, getn, sig, w, weekend)
        for i in range(0, len(rows), 97):
            r = rows[i]
            if json.dumps(final_row(r, getn, city_keep, dist_vis_ok, sig, w, weekend),
                          ensure_ascii=False) != json.dumps(brows[i], ensure_ascii=False):
                bad += 1
    # law 3 invariant: rainy road-visible (non-shelter) <= ~30% of cover-bound
    # (crash overlay rows are a separate bounded population - excluded)
    if sig["weather"] in RAIN_KINDS:
        shelter = sum(1 for o in brows if o["state"] == "shelter")
        road = sum(1 for o in brows if o["visible"] == 1
                   and o["state"] != "shelter" and o["state"] not in NEG_STATES)
        bound = shelter + road
        if bound and road / bound > 0.31:
            print("QC FAIL rain road ratio %.2f" % (road / bound))
            bad += 1
    # T-16d law-8.3 caps self-check on the written face
    ncrash = sum(1 for o in brows if o["state"] in NEG_STATES)
    nrec = sum(1 for o in brows if o.get("recovering") is not None)
    if ncrash > int(CITY_CAP * len(rows)):
        print("QC FAIL crash city cap %d" % ncrash)
        bad += 1
    dist_pop = {}
    for r in rows:
        d = r.get("district") or "?"
        dist_pop[d] = dist_pop.get(d, 0) + 1
    vis_crash_d = {}
    for r, o in zip(rows, brows):
        if o.get("state") in NEG_STATES and o.get("visible") == 1:
            d = r.get("district") or "?"
            vis_crash_d[d] = vis_crash_d.get(d, 0) + 1
    for d, n in vis_crash_d.items():
        if n > int(CRASH_CAP * dist_pop.get(d, 0)):
            print("QC FAIL crash district cap %s %d" % (d, n))
            bad += 1
    dist = {}
    for o in brows:
        dist[o["state"]] = dist.get(o["state"], 0) + 1
    top3 = sorted(dist.items(), key=lambda kv: -kv[1])[:3]
    print("rows=%d bad=%d tw=%s wx=%s wd=%d top3=%s crash=%d recovering=%d" %
          (len(brows), bad, w, sig["weather"] or "na", sig["now"].weekday(), top3,
           ncrash, nrec))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
