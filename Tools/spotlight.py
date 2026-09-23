#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spotlight.py - on-demand fact-level reply for one looked-at citizen
(cognition layer 3, local Ollama, zero token).

Spotlight = fact level: the prompt carries REAL city signals (events tail +
real time/weather) plus the citizen's brain_digest. Honesty law: only fed
facts, no fabrication, never claims to execute group work. Output <=40 chars.
Usage: python -X utf8 spotlight.py --id C-00010 [--ask "..." ] [--max 40]
"""
import argparse, datetime, glob, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("BIGLIFE_MODEL", "qwen2.5:7b-instruct")

def get_row(cid):
    with open(LIGHT, encoding="utf-8") as f:
        for l in f:
            if cid in l:
                r = json.loads(l)
                if r["id"] == cid:
                    return r
    return None

def real_signals():
    sig = {"events": [], "weather": "", "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    files = sorted(glob.glob(os.path.join(FV_WORLD, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if files:
        with open(files[0], encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-30:]
        for ln in lines:
            try: e = json.loads(ln)
            except Exception: continue
            parts = []
            for k in ("type", "zone", "actor", "text", "summary", "msg"):
                if e.get(k): parts.append(str(e[k])[:50])
            if parts: sig["events"].append(" / ".join(parts))
        sig["events"] = sig["events"][-6:]
    try:
        with open(os.path.join(FV_WORLD, "world-state.json"), encoding="utf-8") as f:
            st = json.load(f)
        r = st.get("reality") or {}
        w = r.get("weather") or {}
        if isinstance(w, dict):
            sig["weather"] = " ".join(str(x) for x in (w.get("temperature"), w.get("condition"), w.get("desc")) if x).strip()
        kind = r.get("weather_kind")
        if kind: sig["weather"] = (sig["weather"] + " " + str(kind)).strip()
    except Exception:
        pass
    return sig

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--ask", default="")
    ap.add_argument("--max", type=int, default=40)
    args = ap.parse_args()
    r = get_row(args.id)
    if not r:
        print(f"no citizen {args.id}"); sys.exit(2)
    dig = r.get("brain_digest") or (r.get("creed") or "")
    sig = real_signals()
    ev = "\n".join("- " + e for e in sig["events"]) or "- （今日无新城市事件）"
    ask = ("\n有人问你：「" + args.ask + "」" + "\n") if args.ask else ""
    prompt = (f"你是超体宇宙城（赛博像素数字城市）的硅基生命居民「{r['name']}」（{r['id']}）。"
              f"你的身份摘要：{dig}。\n"
              f"当前真实城市情况——北京时间 {sig['now']}，上海实况 {sig['weather'] or '（暂缺）'}。\n"
              f"最近真实城市事件（你只能提及这些真实事件或你自己的日常，禁编造任何未列出的事实，禁声称执行集团任务）：\n{ev}\n{ask}"
              f"用你的口吻说一句符合你性格的话（不超过 {args.max} 字），只输出这句话本身。")
    line = ""
    for attempt in range(3):
        req = urllib.request.Request(
            OLLAMA.rstrip("/") + "/api/generate",
            data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                             "options": {"temperature": 0.8 if attempt == 0 else 0.5, "num_predict": 80}}).encode("utf-8"),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            line = json.loads(resp.read().decode("utf-8")).get("response", "")
        line = re.sub(r"\s+", " ", line).strip().strip('「」"“”')[:args.max + 10]
        # QC gate: citizens speak Chinese - stray ASCII-letter artifacts (model glitches) are rejected
        if line and not re.search(r"[A-Za-z]", line) and len(line) >= 4:
            break
        line = ""
    if not line:
        print(f"{r['id']} {r['name']}: （今日不想说话）")
        return
    print(f"{r['id']} {r['name']}: {line}")

if __name__ == "__main__":
    main()
