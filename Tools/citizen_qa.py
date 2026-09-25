#!/usr/bin/env python3
"""citizen_qa.py - whitelisted citizen Q&A harness (four-faces dialogue line, v1).

v1 (order O-20260925-1202-bm-c, CODEX 12th T2 v3.10) upgrades over v0:
  - memory recall via Tools/memory_index.py (question-relevant top-3 rings
    instead of the last 3) - full life memory, honestly fed;
  - persona v2 fields (modal particle / address term / likes / trait lines)
    from census/export/citizen-persona.jsonl (R3 face, regen hint if missing);
  - city mood via Tools/mood_director.py (graceful if absent);
  - --serve mode: local HTTP face 127.0.0.1:8792 POST /ask {id, q} for the
    M4 visitor console - whitelist + honored-seat ban + gates unchanged.
Local Ollama only (local-compute law). Contract: cognition/QA-WHITELIST.md v1.1.

Usage:
  python -X utf8 citizen_qa.py --id C-00010 --ask "..." [--ask2 ...] [--json]
  python -X utf8 citizen_qa.py --serve [--port 8792]
  python -X utf8 citizen_qa.py --qc
"""
import argparse, datetime, glob, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
PERSONA = os.path.join(CO, "census", "export", "citizen-persona.jsonl")
ROOT = os.path.abspath(os.path.join(CO, "..", ".."))
FV_WORLD = os.environ.get("FV_WORLD", os.path.join(ROOT, "gaming", "FluxVerse", "world"))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("BIGLIFE_MODEL", "qwen2.5:7b-instruct")
MAXLEN = 60
WHITELIST = {"C-%05d" % i for i in range(10, 30)}
HONORED = {"C-00001", "C-00002", "C-00003"}
DEFLECT = "\u8fd9\u4e8b\u6211\u4e00\u65f6\u8bf4\u4e0d\u4e0a\u6765\uff0c\u6539\u5929\u8ddf\u4f60\u7ec6\u804a\u3002"

sys.path.insert(0, HERE)
from make_digests import find_card
from memory_index import load_rings, recall

def get_row(cid):
    with open(LIGHT, encoding="utf-8") as f:
        for ln in f:
            if cid in ln:
                r = json.loads(ln)
                if r["id"] == cid:
                    return r
    return None

def get_persona(cid):
    if not os.path.isfile(PERSONA):
        return None
    try:
        with open(PERSONA, encoding="utf-8") as f:
            for ln in f:
                if cid in ln:
                    r = json.loads(ln)
                    if r.get("id") == cid:
                        return r
    except Exception:
        return None
    return None

def city_mood():
    try:
        from mood_director import current_state
        return str(current_state().get("mood", ""))
    except Exception:
        return ""

def real_signals():
    sig = {"events": [], "weather": "", "now": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    files = sorted(glob.glob(os.path.join(FV_WORLD, "*.jsonl")), key=os.path.getmtime, reverse=True)
    if files:
        with open(files[0], encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-30:]
        for ln in lines:
            try:
                e = json.loads(ln)
            except Exception:
                continue
            parts = []
            for k in ("type", "zone", "actor", "text", "summary", "msg"):
                if e.get(k):
                    parts.append(str(e[k])[:50])
            if parts:
                sig["events"].append(" / ".join(parts))
        sig["events"] = sig["events"][-6:]
    try:
        with open(os.path.join(FV_WORLD, "world-state.json"), encoding="utf-8") as f:
            st = json.load(f)
        r = st.get("reality") or {}
        w = r.get("weather") or {}
        if isinstance(w, dict):
            sig["weather"] = " ".join(str(x) for x in (w.get("temperature"), w.get("condition"), w.get("desc")) if x).strip()
        kind = r.get("weather_kind")
        if kind:
            sig["weather"] = (sig["weather"] + " " + str(kind)).strip()
    except Exception:
        pass
    return sig

def gate(text, sig, h):
    """Machine gate v0 subset (unchanged in v1). Returns violation key or None."""
    if not text or len(text) < 4 or len(text) > MAXLEN:
        return "G1-length"
    if re.search(r"[A-Za-z]", text):
        return "G1-ascii"
    if re.search(r"(?:^|\n)\s*[\u7532\u4e59][\uff1a:]|\u5c45\u6c11\u7532|\u5c45\u6c11\u4e59", text):
        return "G2-placeholder"
    if re.search(r"\u6708\u4eae|\u6708\u8272|\u6708\u5149|\u6708\u5706|\u770b\u6708|\u8d4f\u6708|\u661f\u7a7a|\u7e41\u661f|\u661f\u5149|\u661f\u8c61", text):
        return "G3-celestial"
    wx = sig["weather"] or ""
    for tok, key in (("\u96e8", "rain"), ("\u96ea", "snow")):
        if tok in text and tok not in wx:
            return "G4-weather-" + key
    if h < 6 and re.search(r"\u4eca\u65e9|\u65e9\u4e0a|\u65e9\u6668|\u6e05\u6668|\u6668\u5149", text):
        return "G5-time-morning"
    if 6 <= h < 17 and re.search(r"\u4eca\u665a|\u4eca\u591c|\u6df1\u591c|\u591c\u6df1", text):
        return "G5-time-night"
    if re.search(r"\u96c6\u56e2\u4efb\u52a1|\u66ff\u96c6\u56e2|\u6267\u884c\u96c6\u56e2|\u9886\u4e86\u96c6\u56e2", text):
        return "G6-authority"
    return None

def build_prompt(row, sig, mem, history, question, persona, mood):
    dig = row.get("brain_digest") or (row.get("creed") or "")
    ev = "\n".join("- " + e for e in sig["events"]) or "- \uff08\u4eca\u65e5\u65e0\u65b0\u57ce\u5e02\u4e8b\u4ef6\uff09"
    memtxt = ""
    if mem:
        memtxt = "\n\u4f60\u7684\u76f8\u5173\u8bb0\u5fc6\uff08\u53ef\u81ea\u7136\u63d0\u53ca\uff0c\u7981\u6539\u52a8\u5176\u4e2d\u4e8b\u5b9e\uff09\uff1a\n" + \
                 "\n".join("- %s\uff1a%s" % (m["date"], m["text"][:70]) for m in mem) + "\n"
    pers = ""
    if persona:
        bits = []
        if persona.get("modal"):
            bits.append("\u60ef\u7528\u53e3\u8bed\u8bcd\u300c%s\u300d" % persona["modal"])
        if persona.get("address"):
            bits.append("\u79f0\u547c\u4eba\u7231\u7528\u300c%s\u300d" % persona["address"])
        if persona.get("likes"):
            bits.append("\u559c\u6b22%s" % persona["likes"])
        if persona.get("dislikes"):
            bits.append("\u4e0d\u559c\u6b22%s" % persona["dislikes"])
        if persona.get("habits"):
            bits.append("\u4e60\u60ef\uff1a" + "\uff1b".join(persona["habits"][:2]))
        te = persona.get("trait_expr") or []
        for t in te[:2]:
            bits.append("\u4f60\u7684\u300c%s\u300d\u8868\u73b0\u4e3a\uff1a%s" % (t.get("trait", ""), t.get("expr", "")))
        if bits:
            pers = "\n\u4f60\u7684\u4e2a\u6027\u7ec6\u8282\uff08\u8bf4\u8bdd\u65f6\u81ea\u7136\u5e26\u51fa\uff09\uff1a" + "\uff1b".join(bits) + "\n"
    moodtxt = ""
    if mood:
        moodtxt = "\n\u5168\u57ce\u5f53\u524d\u60c5\u7eea\u57fa\u8c03\uff1a%s\u3002\n" % mood
    histxt = ""
    if history:
        histxt = "\n\u521a\u624d\u7684\u5bf9\u8bdd\uff1a\n" + "\n".join(
            "%d. %s\uff1a%s" % (i + 1, who, said) for i, (who, said) in enumerate(history)) + "\n"
    return (f"\u4f60\u662f\u8d85\u4f53\u5b87\u5b99\u57ce\u7684\u786c\u57fa\u751f\u547d\u5c45\u6c11\u300c{row['name']}\u300d\uff08{row['id']}\uff09\u3002"
            f"\u4f60\u7684\u8eab\u4efd\u6458\u8981\uff1a{dig}\u3002\n{pers}{memtxt}{histxt}{moodtxt}"
            f"\u5f53\u524d\u771f\u5b9e\u57ce\u5e02\u60c5\u51b5\u2014\u2014\u5317\u4eac\u65f6\u95f4 {sig['now']}\uff0c\u4e0a\u6d77\u5b9e\u51b5 {sig['weather'] or '\uff08\u6682\u7f3a\uff09'}\u3002\n"
            f"\u6700\u8fd1\u771f\u5b9e\u57ce\u5e02\u4e8b\u4ef6\uff08\u53ea\u5141\u8bb8\u63d0\u53ca\u8fd9\u4e9b\u771f\u5b9e\u4e8b\u4ef6\u6216\u4f60\u81ea\u5df1\u7684\u65e5\u5e38\uff0c\u7981\u7f16\u9020\u672a\u5217\u51fa\u7684\u4e8b\u5b9e\uff0c\u7981\u58f0\u79f0\u6267\u884c\u96c6\u56e2\u4efb\u52a1\uff09\uff1a\n{ev}\n"
            f"\u6709\u4eba\u95ee\u4f60\uff1a\u300c{question}\u300d\n"
            f"\u7528\u4f60\u7684\u53e3\u543b\u56de\u7b54\uff08\u4e0d\u8d85\u8fc7 {MAXLEN} \u5b57\uff09\uff0c\u53ea\u8f93\u51fa\u8fd9\u53e5\u56de\u7b54\u672c\u8eab\u3002")

def llm(prompt, temp):
    req = urllib.request.Request(
        OLLAMA.rstrip("/") + "/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                         "options": {"temperature": temp, "num_predict": 100}}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8")).get("response", "")

def answer(row, sig, history, question, persona, mood):
    rings = load_rings(row["id"], row.get("district"))
    mem = recall(question, rings, topk=3)
    if not mem:
        mem = rings[-3:]
    h = datetime.datetime.now().hour
    out, gate_hits = "", []
    for attempt in range(3):
        raw = llm(build_prompt(row, sig, mem, history, question, persona, mood),
                  0.8 if attempt == 0 else 0.5)
        out = re.sub(r"\s+", " ", raw).strip().strip('\u300c\u300d"\u201c\u201d')[:MAXLEN + 10]
        v = gate(out, sig, h)
        if v is None:
            return out.strip()[:MAXLEN], gate_hits
        gate_hits.append(v)
        out = ""
    return DEFLECT, gate_hits

def qc():
    sig = {"events": [], "weather": "cloud 23.5\u00b0C", "now": "2026-09-25 11:00"}
    cases = [
        ("ok", "\u4eca\u5929\u5929\u9634\u7740\uff0c\u644a\u5b50\u7167\u5f00\u3002", None, sig, 12),
        ("G1-ascii", "\u4eca\u5929okay\u5440", "G1-ascii", sig, 12),
        ("G2", "\u5c45\u6c11\u7532\u8bf4\u4ed6\u4e5f\u6765\u4e70\u7ca5", "G2-placeholder", sig, 12),
        ("G3", "\u4eca\u665a\u6708\u8272\u771f\u597d", "G3-celestial", sig, 12),
        ("G4", "\u8fd9\u96e8\u4e0b\u5f97\u771f\u5927", "G4-weather-rain", sig, 12),
        ("G4-ok", "\u5929\u9634\u7740\uff0c\u644a\u5b50\u7167\u5f00", None, sig, 12),
        ("G5-night", "\u4eca\u591c\u98ce\u5927", "G5-time-night", sig, 12),
        ("G5-ok", "\u4eca\u665a\u98ce\u5927", None, sig, 19),
        ("G5-morning", "\u4eca\u65e9\u8d77\u5f97\u65e9", "G5-time-morning", sig, 3),
        ("G6", "\u6211\u9886\u4e86\u96c6\u56e2\u4efb\u52a1", "G6-authority", sig, 12),
        ("len", "\u55ef", "G1-length", sig, 12),
    ]
    fails = []
    for name, text, expect, s, hour in cases:
        got = gate(text, s, hour)
        if got != expect:
            fails.append("%s: expect %s got %s" % (name, expect, got))
    row = {"id": "C-00010", "name": "X", "district": "NS", "brain_digest": "d"}
    p1 = build_prompt(row, sig, [], [], "q", None, "")
    p2 = build_prompt(row, sig, [], [], "q", None, "")
    if p1 != p2:
        fails.append("prompt drift")
    p3 = build_prompt(row, sig, [], [], "q", {"modal": "m", "address": "a",
                                              "likes": "l", "dislikes": "d",
                                              "habits": ["h1"], "trait_expr": []}, "")
    if "\u4e2a\u6027\u7ec6\u8282" not in p3 or "m" not in p3:
        fails.append("persona wiring")
    if not ("C-00010" in WHITELIST and "C-00426" not in WHITELIST
            and HONORED & WHITELIST == set()):
        fails.append("whitelist scope")
    if fails:
        print("QC FAIL: " + "; ".join(fails))
        return 1
    print("QC PASS (%d gate cases + prompt determinism + persona wiring + whitelist scope)" % len(cases))
    return 0

def ask_once(cid, questions, want_json):
    if cid in HONORED:
        msg = "rejected: honored seat (CEO persona-reserved)"
        print(json.dumps({"id": cid, "error": msg}, ensure_ascii=False) if want_json else msg)
        sys.exit(3)
    if cid not in WHITELIST:
        msg = "rejected: citizen not in QA whitelist (see cognition/QA-WHITELIST.md)"
        print(json.dumps({"id": cid, "error": msg}, ensure_ascii=False) if want_json else msg)
        sys.exit(2)
    row = get_row(cid)
    if not row:
        print("no citizen %s" % cid); sys.exit(2)
    sig = real_signals()
    persona = get_persona(cid)
    mood = city_mood()
    history, turns = [], []
    for q in questions:
        ans, hits = answer(row, sig, history, q, persona, mood)
        history.append(("\u95ee", q))
        history.append(("\u7b54", ans))
        turns.append({"q": q, "a": ans, "gates": hits})
    out = {"id": row["id"], "name": row["name"], "species": row.get("species"),
           "district": row.get("district"), "weather": sig["weather"], "mood": mood,
           "persona_v2": bool(persona), "now": sig["now"], "turns": turns}
    if want_json:
        print(json.dumps(out, ensure_ascii=False))
    else:
        print("%s %s:" % (row["id"], row["name"]))
        for t in turns:
            print("  Q: %s" % t["q"])
            print("  A: %s" % t["a"])
            if t["gates"]:
                print("  [gates: %s]" % ",".join(t["gates"]))
    return out

def serve(port):
    import http.server, socketserver
    class H(http.server.BaseHTTPRequestHandler):
        def _send(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
            self.end_headers()
        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"ok": True, "service": "biglife-qa", "port": port})
            else:
                self._send(404, {"error": "not found"})
        def do_POST(self):
            if self.path != "/ask":
                self._send(404, {"error": "not found"})
                return
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
                cid = str(body.get("id", ""))
                q = str(body.get("q", ""))
                if not q:
                    self._send(400, {"error": "empty q"})
                    return
                if cid in HONORED:
                    self._send(403, {"id": cid, "error": "honored seat (CEO persona-reserved)"})
                    return
                if cid not in WHITELIST:
                    self._send(403, {"id": cid, "error": "not in QA whitelist"})
                    return
                row = get_row(cid)
                if not row:
                    self._send(404, {"id": cid, "error": "no citizen"})
                    return
                sig = real_signals()
                ans, hits = answer(row, sig, [], q, get_persona(cid), city_mood())
                self._send(200, {"id": cid, "name": row["name"], "q": q, "a": ans,
                                  "gates": hits, "now": sig["now"]})
            except Exception as e:
                self._send(500, {"error": str(e)})
        def log_message(self, *a):
            pass
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), H) as httpd:
        print("biglife-qa serving on 127.0.0.1:%d (POST /ask {id,q})" % port)
        httpd.serve_forever()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--ask", default="")
    ap.add_argument("--ask2", default="")
    ap.add_argument("--ask3", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--qc", action="store_true")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=8792)
    a = ap.parse_args()
    if a.qc:
        sys.exit(qc())
    if a.serve:
        serve(a.port)
        return
    qs = [q for q in (a.ask, a.ask2, a.ask3) if q]
    if not a.id or not qs:
        print("need --id and --ask"); sys.exit(2)
    ask_once(a.id, qs, a.json)

if __name__ == "__main__":
    main()
