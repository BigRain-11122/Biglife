#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evolve_citizen.py v0.1 - BigLife citizen evolution engine.

Grows citizen cards by feeding REAL city signals into a LOCAL LLM (Ollama
qwen2.5:7b-instruct, zero token, local-first L2). Honesty law (docs/CODEX.md 9):
every new ring line carries an [anchor] note pointing at the real event.
Ollama down => silent skip exit 0 (probe contract #4). Targeted git commits
only (governance 6.2 - never add -A).

Usage:
  python -X utf8 evolve_citizen.py --batch 3          # evolve N due citizens
  python -X utf8 evolve_citizen.py --force C-00010     # ignore cooldown
  python -X utf8 evolve_citizen.py --meet C-00010 C-00025   # two-citizen encounter
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
    sig = {"events": [], "weather": "", "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
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
                    sig["events"].append(" / ".join(parts))
            sig["events"] = sig["events"][-8:]
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

def persona_digest(text):
    """Pull key persona fields from a card for the LLM prompt."""
    def grab(label, limit=140):
        m = re.search(r"\*\*" + label + r"\*\*\s*(.+)", text)
        return m.group(1).strip()[:limit] if m else ""
    return {
        "species": grab("物种", 40), "prof": grab("职业", 80), "traits": grab("性格", 100),
        "creed": grab("信条", 60), "language": grab("语言", 80), "behavior": grab("行为", 90),
    }

def build_prompt(cid, text, sig):
    p = persona_digest(text)
    ev = "\n".join("- " + e for e in sig["events"]) or "- （今日无新城市事件）"
    wx = sig["weather"] or "（天气数据暂缺）"
    return (f"你是超体宇宙城（一座赛博像素数字城市）的叙事市民「{cid}」。"
            f"你的人设：{p['species']}；职业：{p['prof']}；性格：{p['traits']}；信条：「{p['creed']}」；"
            f"语言风格：{p['language']}；日常：{p['behavior']}。\n"
            f"你只能谈论以下真实发生的事（城市实况），禁止编造未列出的集团大事，禁止声称自己执行了集团任务：\n{ev}\n"
            f"现在真实北京时间 {sig['now']}，上海实况天气：{wx}。\n"
            f"硬约束（锚定律从严）：年轮中提及的具体事必须逐字来自上面的事件清单——只可截取清单原文短语，不得改写事实，不得添加清单之外的任何具体事（时间/人名/事件名）；泛泛的日常动作（开档、收摊、出摊）不算具体事；提及天气只许描述此刻实况亲历（如「天阴着」），提及风必须严格按喂入风速量级描述（喂入风速≤3m/s 只许写「风轻轻的/风不大」，喂入风速>3m/s 只许写「风不小/风挺大」类如实量级措辞（此时严禁写「风不大/风轻轻的」），风速数据缺失则完全不提风）；只有喂入天气串明确含雨（rain/drizzle/showers/雨字样）才许提及雨，天气串无雨时严禁出现任何「雨」字，禁止出现「天气预报说/预报/听说」等消息源归属字样。人设里带条件触发的行为（如『月圆夜必…』『节前…』），条件未被事件清单或实况坐实时严禁触发该场景，只能写无条件的人设日常；提及时间只许锚定喂入的当前时刻，严禁编造开工/收班/时刻表/『再过几小时』等时间细节，严禁使用与当前时刻不符的时段词（如凌晨时辰写『今早/早晨/晨光/清晨』、白天写『今晚/深夜』）。\n"
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--force", nargs="*", default=None)
    ap.add_argument("--meet", nargs=2, default=None)
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
                  f"硬约束（锚定律从严）：台词中提及的具体事必须逐字来自事件清单原文短语，不得添加清单外的具体事实。台词中禁止出现「居民甲」「居民乙」字样，直接以台词本身呈现；提及天气只许描述此刻实况亲历，提及风必须严格按喂入风速量级描述（喂入风速≤3m/s 只许「风轻轻的/风不大」，喂入风速>3m/s 只许「风不小/风挺大」类如实量级措辞（此时严禁「风不大/风轻轻的」），缺风速则不提风）；只有喂入天气串明确含雨（rain/drizzle/showers/雨字样）才许提及雨，天气串无雨时严禁出现任何「雨」字，禁止「天气预报说/预报/听说」等消息源归属字样；禁止编造开工/收班/时刻表/『再过几小时』等时间细节，禁止使用与当前时刻不符的时段词（如凌晨时辰写『今早/早晨/晨光/清晨』）。\n"
                  f"围绕其中一件真实事件，写两句话：甲对乙说的一句（20-40字），乙回的一句（20-40字）。输出两行，每行一句，不要序号。")
        try:
            resp = llm(prompt)
        except Exception:
            print("ollama down; meet skipped"); return
        lines = [l.strip() for l in resp.splitlines() if l.strip()][:2]
        while len(lines) < 2:
            lines.append("（那天的桥上风大，谁也没多说什么。）")
        paths = []
        for cid, line in zip(ids, lines):
            p = find_card(cid)
            other = ids[1] if cid == ids[0] else ids[0]
            add_ring(p, cid, f"与 {other} 相遇：{line}", anchor_note)
            paths.append(p)
        commit_files(paths, "citizen evolution: encounter " + " ".join(ids) + via)
        sync_light(args.via)
        print("OK meet:", " ".join(ids))
        return

    due = due_citizens(cursor, args.batch, args.force)
    if not due:
        print("no due citizens; cooldown healthy")
        return
    n = 0
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
            line = llm(build_prompt(cid, text, sig))
        except Exception:
            print("ollama down; batch paused at", n)
            break
        line = re.sub(r"\s+", " ", line).strip().strip('「」"“”')[:90]
        if len(line) < 8:
            line = "今天照常出摊/上岗，江上的光点还是那么多。"
        add_ring(p, cid, line, anchor_note)
        paths.append(p)
        cursor[cid] = {"v": 1, "last": today(),
                       "next": (datetime.date.today() + datetime.timedelta(days=COOLDOWN_DAYS)).isoformat(),
                       "n": cursor.get(cid, {}).get("n", 0) + 1}
        n += 1
    if paths:
        commit_files(paths, "citizen evolution: %s (%s)%s" % (", ".join(due[:n]), today(), via))
        save_cursor(cursor)  # before sync: sync_rings mirrors only cursor-listed citizens
        sync_light(args.via)
    else:
        save_cursor(cursor)
    print("OK evolved=%d of %d due" % (n, len(due)))

if __name__ == "__main__":
    main()
