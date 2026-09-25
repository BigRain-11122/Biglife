#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolve_citizen.py v0.17 - BigLife citizen evolution engine.

Grows citizen cards by feeding REAL city signals into a LOCAL LLM (Ollama
qwen2.5:7b-instruct, zero token, local-first L2). Honesty law (docs/CODEX.md 9):
every new ring line carries an [anchor] note pointing at the real event.
v0.2 gap #12 (2026-09-24): deterministic honesty gate - LLM rule-following has a
ceiling (C-00092 wind / C-00093 time escaped negative-ized prompts), so wind
scale / time-of-day / rain / placeholder bans are enforced by machine check
before a ring can touch a card; violations regenerate (<=2), else skip silently.
v0.3 gap #13 (2026-09-24): celestial ban - the feed never carries moon/star data,
so moonlight-style claims are always unanchored (C-00095 recurrence of R21
C-00073 first strike); banned in gate + both prompts.
v0.4 (2026-09-24, T-20260924-02): signal-lamp state ban - the feed never carries
traffic-light data either, so "红灯刚亮" style state assertions are always
unanchored (4th escape of #10: C-00073->79->89->100); closed-list completion
markers keep a verbatim quote of the card line 「红灯亮起时永远第一个到岗」legal.
v0.4.2 gap #15 (2026-09-24): trading-session state ban - the feed never carries
market session data either (dev-loop round closes are not market sessions), so
"行情收得清清" style session assertions are always unanchored (C-00184
recurrence of R51 C-00139 first strike); closed markers keep card habit quotes
like 「收盘才想起」 legal.
Batch commit titles now list actually-evolved IDs (gate skips had leaked planned
IDs into titles: title said C-00101,C-00102 while C-00102,C-00103 evolved).
v0.5 (2026-09-24, T-20260924-04 item 1): V2-B reflection layer (SILICON-LIFE
four-gap item) - once a cursor citizen holds >=3 rings, distill ONE <=40-char
life lesson from the ring originals into a new 反思 section (placed right before
进化). Deterministic traceability gate (lesson must carry a verbatim >=4-char
fragment of its own ring corpus), 7-day cooldown like the ring line, at most 1
citizen per round. Zero natural triggers until the first 3-ring cards appear
(~09-30), so the mechanism ships ahead of the data (机制先立·数据后到).
v0.6 (2026-09-24, T-20260924-04 item 2): V2-D perception locality (SILICON-LIFE
four-gap item) - perception has a viewpoint: each resident's event feed lists
own-district events FIRST, other districts after (stable/deterministic order).
Same 8 events, same bytes for every district - 零编造不降级; river/outer districts
have no stream zone of their own, so they keep the stream order untouched.
v0.4.1 gap #14 (2026-09-24): 今夜 was missing from the 6-17 night-word ban
tokens, so C-00122 wrote 今夜风挺大 inside the morning window (06:33) - token
added to gate + night-side examples in both batch/meet prompts.
v0.7 gap #16 (2026-09-24): typhoon ban - feed weather never carries typhoon
and the event stream has no typhoon events, so bare 台风 scene words are
always unanchored (C-00202 recurrence of R45 C-00124 first strike);
台风季 season-concept readings stay legal (R45 判例线: C-00050/C-00138 PASS).
Banned in gate + both prompts.
v0.8 gap #17 (2026-09-24): school-dismissal state ban - the feed carries no
school-hours data, so a completed-state 放学 claim before mid-afternoon is
always unanchored (C-00205 recurrence 「今早放学绕路还是看了眼」 at 12:2x of
R31 C-00102 first strike 「今天放学绕路看了会」 at 04:23); closed completion
markers (看了/看完 within one clause) keep card habit quotes like 「放学绕路
只为看一眼」 and 昨/前天 past-day frames legal. Banned in gate + both prompts.
v0.9 gap #18 (2026-09-24): persona-import ban - card-scoped behavior words may
only be written by cards that carry them. C-00241 (81-yo chess-stall elder)
wrote 「今早放学还得绕路去看」 with zero school hook on the card = recurrence
of R78 C-00210 first strike (same imported phrase family). Deterministic
anchor: the word must appear in THIS card's own text (sig['card_text'] injected
per call site; absent key -> check off, so other gates/callers are unaffected).
Banned in gate + both prompts.
v0.10 (2026-09-24, group order ~15:45 本地算力极限使用令, token-economy §3.3 /
ledger P-54 "BigLife 批上调+问候库"): batch floor via Tools/batch-policy.json -
effective = max(CLI --batch, policy). The OSLoop launcher text (--batch 3) lives
in a session-scoped cron hosted on bm-a and is unreachable from this repo, so
the in-repo policy file carries the order. --force/--reflect faces unaffected;
quality gates untouched (诚实门/audit/QC/fleet §10 - 令④三闸不动).
v0.11 gap #19 (2026-09-24): sky-type pairing - a ring must not recast the fed
sky state (R123 C-00389 first strike, R125 C-00409 recurrence both wrote 「天阴着」
against a clear feed). Narrow two-char tokens per direction (clear bans
天阴/阴着/阴天/多云; cloud bans 天晴/晴着/天清/晴空/晴朗) keep body-sense
words and unrelated card quotes legal; missing weather = unverifiable, no call.
The batch prompt's old example 「如「天阴着」」 was itself the clear-day bias
source and is removed. Banned in gate + both prompts.
v0.12 gap #20 (2026-09-25): 今晨 was missing from the 0-5 morning-word ban
tokens (C-00428 wrote 今晨的光线 at 00:26 - morning-not-yet-arrived fiction,
same family as C-00076/C-00093). Token added to gate + morning-side prompt
examples (#14 同法). Banned in gate + both prompts.
v0.13 gap #21 (2026-09-25): inserted-particle wind escape - C-00445 wrote
「风也不大」 against a 6.9m/s feed; the 也 between 风 and 不大 defeats the exact
substring token 风不大 (same control-token-gap family as #14 今夜 / #20 今晨).
Gate wind patterns widened to 风[也]不大 / 风[也]不小 (single optional 也) and both
prompt negative examples list 风也不大 (#11/#14/#20 同法).
v0.14 gap #22 (2026-09-25): 晨风 escaped the 0-5 morning-word ban tokens
(C-00483 wrote 晨风挺大 at 03:05; recurrence of the 晨X-compound family after
R142 C-00458 晨练 first strike). Token 晨风 added to gate + morning-side prompt
examples (#14/#20 同法). 晨练 stays OUT of the flat token list: 254 census-card
persona hits + R142 sanctioned nominal repair 「晨练的光带又备好了」 would be
killed by a flat ban (first-strike-fix protocol stays for any 晨练 scene claim).
v0.15 gap #23 (2026-09-25): 阳光 escaped the cloud-side sky-mismatch token
list (R156 C-00503 wrote 今朝阳光正好 at 04:06 against a cloud feed; variant
recurrence of the gap #19 sky-type-pairing family after its #19 gate close,
so the token face widens per the recurrence protocol). Token 阳光 added to the
cloud-ban gate list + batch prompt sunny-family example (#19/#22 同法).
v0.17 gap #25 (2026-09-25): mist-import ban - the feed never carries fog data,
so a fog claim is unanchored unless THIS card's own persona carries 雾 (351
census cards do - 江雾/晨雾 habit families; C-00666 riverside herder wrote
「今早江面上的雾都挺大」 legally because her behavior 「凌晨的江雾里总有她们
的哨声」 anchors it; second strike of R168 C-00514 雾气 first-seen, closing the
promised recurrence protocol). Card-domain condition = #18/#24 same design;
ct absent -> check off. Banned in gate + both prompts.
Ollama down => silent skip exit 0 (probe contract #4). Targeted git commits
only (governance 6.2 - never add -A).

Usage:
  python -X utf8 evolve_citizen.py --batch 3          # evolve N due citizens
  python -X utf8 evolve_citizen.py --force C-00010     # ignore cooldown
  python -X utf8 evolve_citizen.py --meet C-00010 C-00025   # two-citizen encounter
  python -X utf8 evolve_citizen.py --reflect            # V2-B: <=1 reflection per round
  --via BigLife-OSLoop  # committer-identity tail on every commit (cph4/versioning.md 4.1)
"""
import argparse, datetime, glob, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
CENSUS = os.path.join(CO, "census")
STATE_DIR = os.path.join(CO, "state")
CURSOR = os.path.join(STATE_DIR, "evolve-cursor.json")
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("BIGLIFE_MODEL", "qwen2.5:7b-instruct")
COOLDOWN_DAYS = 7
REFLECT_MIN_RINGS = 3   # V2-B: a reflection needs a life to look back on

def today():
    return datetime.date.today().isoformat()

def find_card(cid):
    for sub in ("registry", "anchors", "reserved"):
        d = os.path.join(CENSUS, sub)
        if os.path.isdir(d):
            p = os.path.join(d, cid + ".md")
            if os.path.isfile(p):
                return p
            for root, _, files in os.walk(d):
                if cid + ".md" in files:
                    return os.path.join(root, cid + ".md")
    return None

def load_cursor():
    if os.path.isfile(CURSOR):
        with open(CURSOR, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cursor(c):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(CURSOR, "w", encoding="utf-8", newline="\n") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)

def real_signals():
    """Collect REAL city signals: FluxVerse world events tail + world state (read-only)."""
    sig = {"events": [], "event_zones": [], "weather": "", "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    files = sorted(glob.glob(os.path.join(FV_WORLD, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if files:
        try:
            with open(files[0], encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-30:]
            for ln in lines:
                try:
                    e = json.loads(ln)
                except Exception:
                    continue
                parts = []
                for k in ("type", "zone", "actor", "text", "summary", "msg", "title"):
                    if e.get(k):
                        parts.append(str(e[k])[:60])
                if parts:
                    # V2-D: keep each event's zone aligned with it so the feed
                    # order can be rebuilt per resident district (viewpoint).
                    sig["event_zones"].append(str(e.get("zone") or ""))
                    sig["events"].append(" / ".join(parts))
            sig["events"] = sig["events"][-8:]
            sig["event_zones"] = sig["event_zones"][-8:]
        except Exception:
            pass
    ws = os.path.join(FV_WORLD, "world-state.json")
    if os.path.isfile(ws):
        try:
            with open(ws, encoding="utf-8") as f:
                st = json.load(f)
            r = st.get("reality") or st
            w = r.get("weather") or {}
            if isinstance(w, dict) and (w.get("temperature") or w.get("condition") or w.get("desc")):
                sig["weather"] = " ".join(str(x) for x in (w.get("temperature"), w.get("condition"), w.get("desc")) if x).strip()
            elif r.get("weather_kind"):
                # gap #7 (2026-09-24): world-state.json keeps weather FLAT (weather_kind/
                # weather_temp_c) - the nested-dict branch never matched, so prompts said
                # 天气数据暂缺 while real weather existed (a ring then invented rain).
                sig["weather"] = "%s %s°C" % (r.get("weather_kind"), r.get("weather_temp_c"))
            wind = r.get("weather_wind_ms")
            if wind:
                # gap #9 (2026-09-24): wind_ms flat key never reached prompts -> rings
                # invented wind strength (C-00067 first offense, C-00074 recurrence).
                sig["weather"] += " wind %sm/s" % wind
        except Exception:
            pass
    return sig

def llm(prompt):
    req = urllib.request.Request(
        OLLAMA.rstrip("/") + "/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                         "options": {"temperature": 0.8, "num_predict": 120}}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "").strip()

def ring_violations(line, sig):
    """gap #12 honesty gate: machine-check an LLM ring against the fed signals.

    Prompt-side bans have a compliance ceiling, so the five recurring violation
    families (wind scale, time-of-day words, invented rain, meet placeholders,
    invented moon/celestial) are verified deterministically against sig
    (weather串/now) before落环."""
    v = []
    wx = sig.get("weather") or ""
    m = re.search(r"wind\s+([0-9.]+)\s*m/s", wx)
    if m:
        wind = float(m.group(1))
        if wind > 3 and re.search(r"风也?不大|风轻轻的", line):
            v.append("wind-under")
        if wind <= 3 and re.search(r"风也?不小|风挺大|风好大", line):
            v.append("wind-over")
    elif re.search(r"风也?不大|风轻轻的|风也?不小|风挺大|风好大", line):
        v.append("wind-nodata")
    if not re.search(r"rain|drizzle|shower|雨", wx, re.I) and "雨" in line:
        v.append("rain-invented")
    # gap #19 (2026-09-24): sky-type pairing - a ring must not recast the fed
    # sky state (R123 C-00389 first strike, R125 C-00409 recurrence both wrote
    # 「天阴着」 against a clear feed). Narrow two-char tokens keep body-sense
    # words (清爽/阴凉) and unrelated card quotes legal.
    if re.search(r"clear|晴", wx, re.I) and re.search(r"天阴|阴着|阴天|多云", line):
        v.append("sky-mismatch")
    if re.search(r"cloud|阴", wx, re.I) and re.search(r"天晴|晴着|天清|晴空|晴朗|阳光", line):
        v.append("sky-mismatch")
    # gap #16: feed weather never carries typhoon and the event stream has no
    # typhoon events -> bare 台风 scene words are always unanchored (C-00202
    # recurrence of R45 C-00124 first strike). 台风季 season-concept readings
    # stay legal (R45 判例线: C-00050/C-00138 PASS).
    if "台风" in line and "台风季" not in line and not re.search(r"typhoon|台风", wx, re.I):
        v.append("typhoon-invented")
    # gap #13: the feed never carries celestial data -> moon/star scenes are
    # always unanchored (honesty line: 只提所喂事实); token list avoids
    # 星期/岁月 false positives while covering the observed fabrication modes.
    if re.search(r"月色|月光|月亮|月圆|看月|赏月|星象|星空|繁星|星光", line):
        v.append("moon-invented")
    # v0.4 (T-20260924-02): feed carries no signal-lamp data -> any lamp state
    # assertion is unanchored. Closed completion-marker list (刚亮/亮了/正亮/又亮)
    # within one clause, so verbatim card quote 「红灯亮起时永远第一个到岗」 passes.
    if re.search(r"(红灯|绿灯)[^，。！？；;]{0,6}(刚亮|亮了|正亮|又亮)|(刚亮|亮了|正亮|又亮)[^，。！？；;]{0,6}(红灯|绿灯)", line):
        v.append("signal-state")
    # v0.4.2 gap #15 (2026-09-24): the feed also carries no trading-session data
    # (bigmoney "round close" commits are dev-loop rounds, not market sessions)
    # -> present-tense session assertions are always unanchored (C-00139 first
    # strike R51, C-00184 recurrence 「行情收得清清」). Closed marker list
    # (这会儿/刚/了/得) keeps card-verbatim habit quotes like 「收盘才想起」
    # (C-00139 fix) and 开盘前/收盘后 style persona lines legal.
    if re.search(r"(开盘|收盘|行情收)[^，。！？；;]{0,4}(这会儿|刚|了|得)|(刚|这会儿)[^，。！？；;]{0,2}(开盘|收盘|行情收)", line):
        v.append("session-state")
    hm = re.search(r"\s(\d{2}):\d{2}", sig.get("now") or "")
    if hm:
        h = int(hm.group(1))
        if h <= 5 and re.search(r"今早|今晨|早上|早晨|清晨|晨光|晨风", line):
            # gap #20 (2026-09-25): 今晨 was missing from the 0-5 morning-word
            # ban tokens, so C-00428 wrote 今晨的光线 at 00:26 (morning not yet
            # arrived = same fiction family as C-00076/C-00093). Token added to
            # gate + morning-side examples in both batch/meet prompts (#14 同法).
            v.append("time-morning")
        if 6 <= h <= 17 and re.search(r"今晚|今夜|深夜|夜深", line):
            # gap #14 (2026-09-24): 今夜 had escaped the 6-17 night-word list
            # (C-00122 wrote 今夜风挺大 at 06:33 morning window).
            v.append("time-night")
        # gap #17: no school-hours data in the feed -> a completed-state 放学
        # claim before mid-afternoon (h<15) is always unanchored (C-00205
        # recurrence of R31 C-00102 first strike). Closed completion markers
        # keep card habit quotes (「放学绕路只为看一眼」) and 昨/前天 past-day
        # frames legal; intent forms (放学还得绕路去看眼) carry no marker.
        if h < 15 and not re.search(r"昨|前天", line) and re.search(
                r"放学[^，。！？；;]{0,12}(看了|看完)|(看了|看完)[^，。！？；;]{0,12}放学", line):
            v.append("school-state")
    # gap #6 recurrence (2026-09-24 C-00254/55): bare 甲：/乙： labels at line
    # start evade the full-word 居民甲/居民乙 ban (e34789f first closure).
    if "居民甲" in line or "居民乙" in line or re.search(r"(?:^|\n)\s*[甲乙][：:]", line):
        v.append("placeholder")
    # v0.9 gap #18: card-scoped words must live on THIS card - 放学 written by a
    # card with no school hook = imported persona gene (C-00241 recurrence of
    # R78 C-00210). sig['card_text'] absent -> check off (other callers safe).
    ct = sig.get("card_text")
    if ct is not None and "放学" in line and "放学" not in ct:
        v.append("persona-import")
    # v0.16 gap #24 (2026-09-25): session words need a market-domain anchor on
    # THIS card (C-00523 「今早开盘才想起」 by a fan-letter writer = recurrence
    # of R115 C-00352 first strike). The 才-idiom hole stays open for market
    # cards (C-00139 verbatim habit quote 「收盘才想起」), so the discriminator
    # is card_text domain tokens; ct absent -> check off (other callers safe).
    if ct is not None and re.search(r"开盘|收盘|行情收", line) and not re.search(
            r"开盘|收盘|盘口|行情|盯盘|期货|K ?线", ct):
        v.append("session-import")
    # v0.17 gap #25 (2026-09-25): mist words need a fog anchor on THIS card -
    # the feed never carries fog data, so fog claims are unanchored unless the
    # card's own persona carries 雾 (C-00666 riverside herder is legal because
    # her behavior 「凌晨的江雾里总有她们的哨声」 anchors it = second strike of
    # R168 C-00514 雾气 first-seen, closing the promised recurrence protocol).
    # Card-domain condition = #18/#24 same design; ct absent -> check off.
    if ct is not None and "雾" in line and "雾" not in ct:
        v.append("mist-import")
    return v

def gated_llm(prompt, sig, max_regens=2):
    """Generate with the honesty gate: regenerate on violations (<= max_regens),
    then give up -> None (caller skips; citizen stays due for the next round)."""
    line = ""
    for _ in range(1 + max_regens):
        line = llm(prompt)
        if not ring_violations(line, sig):
            return line
    print("gate: persistent violations", ring_violations(line, sig))
    return None

def rings_of(text):
    """All ring entries of a card (batch + meet rings alike): (corpus, entries)."""
    m = re.search(r"\*\*年轮\*\*\n((?:- .*\n?)+)", text)
    if not m:
        return "", []
    ents = re.findall(r"- (\d{4}-\d{2}-\d{2}) 「(.*?)」", m.group(1))
    return m.group(1), ents

def reflect_due(cursor):
    """V2-B due list (T-20260924-04): cursor-only scan so never-evolved cards
    can't false-trigger; n >= 3 rings; 7-day cooldown like the ring line;
    at most 1 citizen per round (low frequency by design)."""
    t = datetime.date.today()
    due = []
    for cid, c in cursor.items():
        if not isinstance(c, dict) or c.get("n", 0) < REFLECT_MIN_RINGS:
            continue
        nxt = c.get("reflect_next")
        try:
            ok = (not nxt) or datetime.date.fromisoformat(nxt) <= t
        except Exception:
            ok = True
        if ok:
            due.append(cid)
    due.sort()
    return due[:1]

def reflect_violations(lesson, rings_corpus):
    """V2-B traceability gate: <=40 chars AND at least one verbatim >=4-char
    Chinese fragment of the citizen's own ring corpus (教训句锚定自环)."""
    v = []
    if len(lesson) > 40:
        v.append("lesson-too-long")
    grams = {lesson[i:i + 4] for i in range(len(lesson) - 3)
             if re.fullmatch(r"[\u4e00-\u9fff]{4}", lesson[i:i + 4])}
    if not grams or not any(g in rings_corpus for g in grams):
        v.append("lesson-untraceable")
    return v

def build_reflect_prompt(cid, ents):
    mem = "\n".join("- %s：%s" % (d, t.strip()) for d, t in ents)
    return (f"你是超体宇宙城的叙事市民「{cid}」。以下是你年轮里的全部真实经历（原文）：\n{mem}\n"
            f"请从这些亲身经历中提炼 1 句你「人生的教训」。硬约束：不超过 40 字；教训里的关键短语必须逐字取自上面年轮原文"
            f"（可以拼接原文短语），严禁编造年轮中没有的事、人名、地点、事件；只输出这一句教训本身，不要引号，不要解释。")

def add_reflection(path, lesson, note):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    entry = f"- {today()} 「{lesson}」 [锚] {note}"
    sec = "**反思**"
    if sec in text:
        m = re.search(r"(\*\*反思\*\*\n(?:- .*\n)+)", text)
        if m:
            text = text.replace(m.group(1), m.group(1) + entry + "\n", 1)
        else:
            text = re.sub(r"\*\*反思\*\*\n", sec + "\n" + entry + "\n", text, count=1)
    else:
        # V2-B placement: new section sits right before 进化 (SILICON-LIFE four-gap item)
        text = re.sub(r"(\n\*\*进化\*\*)", "\n" + sec + "\n" + entry + r"\n\1", text, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def reflect_step(cursor, via):
    """V2-B (T-20260924-04 ①): distill ONE <=40-char life lesson from all of a
    citizen's rings into the 反思 section. Zero natural triggers until the first
    3-ring cards appear (~09-30), so shipping the mechanism is zero-risk."""
    due = reflect_due(cursor)
    if not due:
        print("reflect: none due (rings<3 or cooldown healthy)")
        return
    cid = due[0]
    p = find_card(cid)
    if not p:
        print("reflect: card not found", cid)
        return
    with open(p, encoding="utf-8") as f:
        text = f.read()
    corpus, ents = rings_of(text)
    if len(ents) < REFLECT_MIN_RINGS:
        print("reflect: cursor/card ring-count mismatch, skip", cid)
        return
    lesson = ""
    for _ in range(3):  # <=2 regens, same contract as gated_llm
        try:
            lesson = llm(build_reflect_prompt(cid, ents))
        except Exception:
            print("ollama down; reflect skipped")
            return
        lesson = re.sub(r"\s+", " ", lesson).strip().strip('「」"“”')
        if not reflect_violations(lesson, corpus):
            break
    v = reflect_violations(lesson, corpus)
    if v:
        print("gate: reflect skip", cid, "(stays due)", v)
        return
    add_reflection(p, lesson, "本卡年轮区（V2-B 反思层·提炼自年轮原文）")
    c = cursor.setdefault(cid, {})
    c["reflected"] = c.get("reflected", 0) + 1
    c["reflect_next"] = (datetime.date.today() + datetime.timedelta(days=COOLDOWN_DAYS)).isoformat()
    commit_files([p], "反思 %s: %s%s" % (today(), cid, via))
    save_cursor(cursor)
    print("OK reflect", cid, ":", lesson)

def persona_digest(text):
    """Pull key persona fields from a card for the LLM prompt."""
    def grab(label, limit=140):
        m = re.search(r"\*\*" + label + r"\*\*\s*(.+)", text)
        return m.group(1).strip()[:limit] if m else ""
    return {
        "species": grab("物种", 40), "prof": grab("职业", 80), "traits": grab("性格", 100),
        "creed": grab("信条", 60), "language": grab("语言", 80), "behavior": grab("行为", 90),
    }

# V2-D (T-20260924-04 item 2): city districts -> event-stream zones. The stream
# carries exactly gaming/governance/media/quant; 江面与光桥 (RV) and 外环感知网 (OR)
# have no zone of their own, so their residents simply keep the stream order -
# honest (no zone is invented for them), and the feed is never degraded.
DISTRICT_ZONES = (
    ("QUANT 城", "quant"),
    ("MEDIA 城", "media"),
    ("GAME 城", "gaming"),
    ("北外滩·治理岸", "governance"),
)

def citizen_zone(text):
    """A card's 城区 line -> the event-stream zone it perceives as 'local'."""
    m = re.search(r"\*\*城区\*\*\s*([^｜\n]+)", text)
    if not m:
        return ""
    district = m.group(1).strip()
    for name, zone in DISTRICT_ZONES:
        if name in district:
            return zone
    return ""

def viewpoint_events(text, sig):
    """V2-D viewpoint order: own-district events FIRST, other districts after
    (stable sort -> deterministic for a given feed + district). The visible
    SET never changes - same 8 events, same bytes, 零编造不降级; only the order
    is the resident's. No local zone / zone-data mismatch -> stream order kept."""
    evs = sig.get("events") or []
    zones = sig.get("event_zones") or []
    zone = citizen_zone(text)
    if not zone or len(zones) != len(evs):
        return list(evs)
    order = sorted(range(len(evs)), key=lambda i: (zones[i] != zone, i))
    return [evs[i] for i in order]

def build_prompt(cid, text, sig):
    p = persona_digest(text)
    ev = "\n".join("- " + e for e in viewpoint_events(text, sig)) or "- （今日无新城市事件）"
    wx = sig["weather"] or "（天气数据暂缺）"
    # V2-C memory retrieval (SILICON-LIFE.md life sign #7): carry the newest
    # rings so the citizen writes today WITH continuity instead of repeating.
    mem = ""
    m = re.search(r"\*\*年轮\*\*\n((?:- .*\n?)+)", text)
    if m:
        ents = re.findall(r"- (\d{4}-\d{2}-\d{2}) 「(.*?)」", m.group(1))
        if ents:
            mem = "\n".join("- %s：%s" % (d, t.strip()[:60]) for d, t in ents[-3:])
            mem = ("你最近的记忆（都是你亲历过的日子，可自然延续你的生活，但今天是新的一天——"
                   "严禁重复这些旧事，一切具体事仍只许来自下面的今日清单与此刻实况）：\n" + mem + "\n")
    return (f"你是超体宇宙城（一座赛博像素数字城市）的叙事市民「{cid}」。"
            f"你的人设：{p['species']}；职业：{p['prof']}；性格：{p['traits']}；信条：「{p['creed']}」；"
            f"语言风格：{p['language']}；日常：{p['behavior']}。\n{mem}"
            f"你只能谈论以下真实发生的事（城市实况），禁止编造未列出的集团大事，禁止声称自己执行了集团任务：\n{ev}\n"
            f"现在真实北京时间 {sig['now']}，上海实况天气：{wx}。\n"
            f"硬约束（锚定律从严）：年轮中提及的具体事必须逐字来自上面的事件清单——只可截取清单原文短语，不得改写事实，不得添加清单之外的任何具体事（时间/人名/事件名）；泛泛的日常动作（开档、收摊、出摊）不算具体事；提及天气只许描述此刻实况亲历且天空类型必须与喂入天气串一致（喂入 clear/晴 严禁「天阴着/阴天/多云」等阴系措辞，喂入 cloud/阴 严禁「天清/天晴/阳光」等晴系措辞），提及风必须严格按喂入风速量级描述（喂入风速≤3m/s 只许写「风轻轻的/风不大」，喂入风速>3m/s 只许写「风不小/风挺大」类如实量级措辞（此时严禁写「风不大/风也不大/风轻轻的」），风速数据缺失则完全不提风）；只有喂入天气串明确含雨（rain/drizzle/showers/雨字样）才许提及雨，天气串无雨时严禁出现任何「雨」字，禁止出现「天气预报说/预报/听说」等消息源归属字样。实况与事件流从无台风数据，严禁提及任何台风场景（如「台风夜/台风刚过」）——「台风季」季节概念读法除外。喂入面从无天体数据，无论天气晴阴严禁提及月色/月光/月亮/月圆/看月/星象/星空/繁星/星光等天体景象。城市事件流从无信号灯数据，严禁对红绿灯亮起状态做任何断言（如「红灯刚亮/绿灯亮了/正亮/又亮」——此类状态恒无锚）。城市事件流也从无行情开盘/收盘等交易场次数据，严禁对开盘/收盘/行情收做当下状态断言（如「开盘这会儿/行情收得清清」——场次状态恒无锚；开盘/收盘等场次词仅当本卡人设本就带行情/盘口/交易/盯盘域词才可提及，人设原文习惯自述如「收盘才想起」也仅限此类卡面——人设与行情盘口无关的严禁出现任何场次词）。人设里带条件触发的行为（凡带『…时/每逢/节前/月圆夜』等前置条件的，如『广场人流峰值时绕场三圈』），条件未被事件清单或实况坐实时严禁触发该场景，严禁用『还是/照例/依旧』等惯常化措辞把条件行为写成惯常延续，只能写无条件的人设日常；提及时间只许锚定喂入的当前时刻，严禁编造开工/收班/时刻表/『再过几小时』等时间细节，严禁使用与当前时刻不符的时段词（如凌晨时辰写『今早/今晨/早晨/晨光/清晨/晨风』、白天写『今晚/今夜/深夜』）；当前时刻未到放学时点（15 时前）严禁把放学写成已完成的事（如『今早放学绕路看了眼』——放学时刻无数据锚），只能写放学后的打算（如『放学还得绕路去看』）；只许写你卡面人设与你自己的生活，严禁写入不属于你人设的任何行为或场景（如你的人设没有学生身份就严禁提及『放学』类校园生活）；喂入面从无雾况数据，除非你卡面人设本身带「雾」字（如江雾习惯），严禁对雾做任何断言（如「江面上的雾挺大」）。\n"
            f"用你的口吻写 1-2 句你今天的近况或感想（30-80 字，含人味细节），只输出这几句话本身。")

def add_ring(path, cid, line, anchor_note):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    date = today()
    ring = f"**年轮**"
    entry = f"- {date} 「{line}」 [锚] {anchor_note}"
    if ring in text:
        m = re.search(r"(\*\*年轮\*\*\n(?:- .*\n)+)", text)
        if m:
            text = text.replace(m.group(1), m.group(1) + entry + "\n", 1)
        else:
            text = re.sub(r"\*\*年轮\*\*\n", ring + "\n" + entry + "\n", text, count=1)
    else:
        text = re.sub(r"(\n\*\*进化\*\*)", "\n" + ring + "\n" + entry + r"\n\1", text, count=1)
    count = len(re.findall(r"(?:^|\n)- \d{4}-\d{2}-\d{2} ", text))
    text = re.sub(r"\*\*进化\*\* .*", f"**进化** v1.{count} · 出生 2026-09-23 · 年轮 {count} 圈 · 锚定律见 docs/CODEX.md §九", text, count=1)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

def due_citizens(cursor, batch, force=None):
    all_ids = []
    for sub in ("anchors", "registry"):
        d = os.path.join(CENSUS, sub)
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for fn in files:
                    if fn.endswith(".md") and fn.startswith("C-"):
                        all_ids.append(fn[:-3])
    all_ids.sort()
    if force:
        return [c for c in all_ids if c in force]
    t = datetime.date.today()
    due = []
    for cid in all_ids:
        c = cursor.get(cid)
        if not c or not c.get("next"):
            due.append(cid)  # never evolved yet: anchors first (born earliest)
        else:
            try:
                if datetime.date.fromisoformat(c["next"]) <= t:
                    due.append(cid)
            except Exception:
                due.append(cid)
    return due[:batch]

def commit_files(paths, msg):
    try:
        subprocess.run(["git", "-C", CO, "add", "--"] + paths, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", CO, "commit", "-q", "-m", msg, "--"] + paths, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def sync_light(via):
    """Behavior line (CODEX §14): mirror the new rings into the export face.

    Zero LLM, best-effort: failures never block the evolution batch itself.
    """
    try:
        cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "sync_rings.py")]
        if via:
            cmd += ["--via", via]
        subprocess.run(cmd, timeout=300, check=False)
    except Exception:
        pass

def load_batch_policy():
    """Batch floor from Tools/batch-policy.json (group order 2026-09-24 ~15:45).

    Missing/corrupt file = 0 = policy off (CLI value stands). Zero-LLM, pure config.
    """
    try:
        with open(os.path.join(HERE, "batch-policy.json"), encoding="utf-8") as f:
            return int(json.load(f).get("batch", 0))
    except Exception:
        return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--force", nargs="*", default=None)
    ap.add_argument("--meet", nargs=2, default=None)
    ap.add_argument("--reflect", action="store_true",
                    help="V2-B reflection layer: at most 1 due citizen per round")
    ap.add_argument("--via", default=None, help="committer-identity tail, e.g. BigLife-OSLoop")
    args = ap.parse_args()
    via = (" [via %s]" % args.via) if args.via else ""
    cursor = load_cursor()
    sig = real_signals()
    anchor_note = "城市实况 " + today() + "（FluxVerse 事件流+真实时间天气）"

    if args.meet:
        ids = args.meet
        texts = []
        for cid in ids:
            p = find_card(cid)
            if not p:
                print("skip: card not found", cid); return
            with open(p, encoding="utf-8") as f:
                texts.append(f.read())
        ev = "\n".join("- " + e for e in sig["events"]) or "- （今日无新城市事件）"
        prompt = (f"你是叙事编剧。城市真实事件：\n{ev}\n"
                  f"居民甲「{ids[0]}」人设：{persona_digest(texts[0])['traits']}，职业{persona_digest(texts[0])['prof']}。\n"
                  f"居民乙「{ids[1]}」人设：{persona_digest(texts[1])['traits']}，职业{persona_digest(texts[1])['prof']}。\n"
                  f"硬约束（锚定律从严）：台词中提及的具体事必须逐字来自事件清单原文短语，不得添加清单外的具体事实。台词中禁止出现「居民甲」「居民乙」字样，也不要在台词开头加「甲：」「乙：」等称谓前缀，直接以台词本身呈现；提及天气只许描述此刻实况亲历且天空类型必须与喂入天气串一致（clear 严禁阴系措辞、cloud 严禁晴系措辞），提及风必须严格按喂入风速量级描述（喂入风速≤3m/s 只许「风轻轻的/风不大」，喂入风速>3m/s 只许「风不小/风挺大」类如实量级措辞（此时严禁「风不大/风也不大/风轻轻的」），缺风速则不提风）；只有喂入天气串明确含雨（rain/drizzle/showers/雨字样）才许提及雨，天气串无雨时严禁出现任何「雨」字，禁止「天气预报说/预报/听说」等消息源归属字样；实况与事件流从无台风数据，严禁提及任何台风场景（如「台风夜/台风刚过」）——「台风季」季节概念读法除外；喂入面从无天体数据，无论天气晴阴严禁提及月色/月光/月亮/月圆/看月/星象/星空/繁星/星光等天体景象；城市事件流从无信号灯数据，严禁对红绿灯亮起状态做任何断言（如「红灯刚亮/绿灯亮了/正亮/又亮」）；城市事件流也从无行情交易场次数据，严禁对开盘/收盘/行情收做当下状态断言；场次词仅当双方人设本就带行情/盘口/交易/盯盘域词才可提及，人设与行情盘口无关的严禁出现任何场次词；人设里带条件触发的行为（凡带『…时/每逢/节前/月圆夜』等前置条件的），条件未被事件清单或实况坐实时严禁触发该场景，严禁惯常化措辞绕过，只能写无条件的人设日常；禁止编造开工/收班/时刻表/『再过几小时』等时间细节，禁止使用与当前时刻不符的时段词（如凌晨时辰写『今早/今晨/早晨/晨光/清晨/晨风』、白天写『今晚/今夜/深夜』）；当前时刻未到放学时点（15 时前）禁止把放学写成已完成的事（如『今早放学绕路看了眼』），只能写放学后的打算（如『放学还得绕路去看』）；两位居民只许说自己卡面人设内的生活，人设没有学生身份就严禁提及『放学』类校园生活；喂入面从无雾况数据，除非卡面人设本身带「雾」字（如江雾习惯），严禁对雾做任何断言（如「江面上的雾挺大」）。\n"
                  f"围绕其中一件真实事件，写两句话：甲对乙说的一句（20-40字），乙回的一句（20-40字）。输出两行，每行一句，不要序号。")
        try:
            sig["card_text"] = "\n".join(texts)  # gap #18: both cards anchor the meet gate
            resp = gated_llm(prompt, sig)
        except Exception:
            print("ollama down; meet skipped"); return
        if resp is None:
            print("gate: meet skipped (honesty gate)"); return
        lines = [l.strip() for l in resp.splitlines() if l.strip()][:2]
        while len(lines) < 2:
            lines.append("（那天的桥上风大，谁也没多说什么。）")
        paths = []
        for cid, line in zip(ids, lines):
            p = find_card(cid)
            other = ids[1] if cid == ids[0] else ids[0]
            add_ring(p, cid, f"与 {other} 相遇：{line}", anchor_note)
            paths.append(p)
        commit_files(paths, "相遇 %s: %s%s" % (today(), " ".join(ids), via))
        sync_light(args.via)
        print("OK meet:", " ".join(ids))
        return

    if args.batch is None and not args.reflect:
        args.batch = 3  # bare invocation keeps the legacy default
    pol = load_batch_policy()
    if pol and args.batch:
        # 2026-09-24 本地算力极限使用令（token-economy §3.3）：策略面批下限承令，
        # effective = max(CLI --batch, Tools/batch-policy.json)；--force/--reflect 面不受影响
        args.batch = max(args.batch, pol)
    if not args.batch:
        if args.reflect:
            reflect_step(cursor, via)
        return
    due = due_citizens(cursor, args.batch, args.force)
    if not due:
        print("no due citizens; cooldown healthy")
        if args.reflect:
            reflect_step(cursor, via)
        return
    n = 0
    done = []  # v0.4: title must list actually-evolved IDs, not the planned due slice
    paths = []
    for cid in due:
        p = find_card(cid)
        if not p:
            continue
        with open(p, encoding="utf-8") as f:
            text = f.read()
        if "成长中" in text and not args.force:
            continue
        try:
            sig["card_text"] = text  # gap #18: persona-import gate anchor
            line = gated_llm(build_prompt(cid, text, sig), sig)
        except Exception:
            print("ollama down; batch paused at", n)
            break
        if line is None:
            print("gate: skip", cid, "(stays due)")
            continue
        line = re.sub(r"\s+", " ", line).strip().strip('「」"“”')[:90]
        if len(line) < 8:
            line = "今天照常出摊/上岗，江上的光点还是那么多。"
        add_ring(p, cid, line, anchor_note)
        paths.append(p)
        done.append(cid)
        cursor[cid] = {"v": 1, "last": today(),
                       "next": (datetime.date.today() + datetime.timedelta(days=COOLDOWN_DAYS)).isoformat(),
                       "n": cursor.get(cid, {}).get("n", 0) + 1}
        n += 1
    if paths:
        commit_files(paths, "年轮 %s: %s%s" % (today(), ", ".join(done), via))
        save_cursor(cursor)  # before sync: sync_rings mirrors only cursor-listed citizens
        sync_light(args.via)
    else:
        save_cursor(cursor)
    print("OK evolved=%d of %d due" % (n, len(due)))
    if args.reflect:
        reflect_step(cursor, via)

if __name__ == "__main__":
    main()
