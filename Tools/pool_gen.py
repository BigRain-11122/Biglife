#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_gen.py - city speech pool generator (cognition layer 2).

Pre-generates bark lines for ALL citizens to share: 6 thought-axes x 12 real
contexts (+ sprite pool). Paid once, consumed forever at zero cost.
Honesty law (cognition/README): pool = context-flavored tone, zero concrete
facts - no digits, no names, no dates; facts enter only via spotlight/ring,
and pool contexts are only ACTIVATED by real data (the fact gate).
Local Ollama only (qwen2.5:7b-instruct, zero token).
Iteration (CODEX §14 language line): --target/--sprite-target set bucket depth;
buckets already at target are SKIPPED (self-terminating growth; floor/cap
enforced). Growth reopens only on new contexts / festivals / CEO order.
Single-instance lock: state/pool.lock (stale after 30 min).
Usage: python -X utf8 pool_gen.py [--append] [--target 15] [--sprite-target 10]
"""
import argparse, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
POOL = os.path.join(CO, "cognition", "pools.json")
LOCK = os.path.join(CO, "state", "pool.lock")
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("BIGLIFE_MODEL", "qwen2.5:7b-instruct")

AXES = {
    "烟火": "柴米油盐的踏实劲儿，像早点摊主、食堂师傅、菜场阿姨",
    "秩序": "规矩与风控的稳重劲儿，像风控员、守门人、校准师",
    "求新": "尝鲜与创造的活泼劲儿，像画匠、学徒、主播",
    "怀旧": "旧物与来处的温吞劲儿，像老克勒、档案馆员、修伞匠",
    "侠气": "江湖与义气的爽快劲儿，像信使、船长、调解阿姨",
    "逍遥": "看云钓鱼的自在劲儿，像江边钓手、茶室老板",
}
CONTEXTS = {
    "morning": "清晨，城刚醒来，出摊开店赶早班的时分",
    "dusk": "黄昏，江面反光，收工的时分",
    "night": "夜晚，灯亮着，夜市和值夜岗的时分",
    "weekend": "周末，不赶班的慢日子",
    "rain": "下雨天，街上有伞光",
    "typhoon": "台风警报的天气，风大，家家加固招牌",
    "heatwave": "大热天，超过三十五度的酷暑",
    "coldsnap": "大冷天，零下的寒潮",
    "market_open": "交易所刚开盘的钟声时分",
    "market_close": "交易所刚收盘的时分",
    "ceo_order": "脑塔顶白光亮起、城主发令的时刻",
    "festival": "城市节日，全城挂灯",
}
SPRITE_CONTEXTS = CONTEXTS

def llm(prompt, timeout=120):
    req = urllib.request.Request(
        OLLAMA.rstrip("/") + "/api/generate",
        data=json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                         "options": {"temperature": 0.9, "num_predict": 220}}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8")).get("response", "")

def clean_lines(raw):
    out = []
    for ln in raw.splitlines():
        s = ln.strip().strip("0123456789.、）) 「」“”\"'-*").strip()
        s = re.sub(r"^[0-9一二三四五六七八九十]+[、.．]?\s*", "", s).strip()
        s = s.strip("「」“”\"' 。．") 
        if not s: continue
        out.append(s)
    return out

def valid(line):
    if not (5 <= len(line) <= 24): return False
    if re.search(r"[0-9]", line): return False
    if re.search(r"(19|20)\d{2}年", line): return False
    banned = ["CEO", "Jason", "公司", "集团", "总部", "董事长", "经理"]
    if any(b in line for b in banned): return False
    return True

def gen_bucket(axis_desc, ctx_desc, n=6):
    prompt = (f"你是赛博像素城市「超体宇宙城」的市民台词生成器。这类市民的思想气质：{axis_desc}。"
              f"当前情境：{ctx_desc}。\n写 {n} 条这个情境下这类市民随口说的生活短句。硬规则：每条 5-16 字；"
              f"口语化、有烟火气，像真的会说出来的话；禁出现任何数字、人名、地名、日期、金额、公司名；"
              f"禁书面腔、禁口号、禁说教；市民只过自己的小日子，不谈公事不表功勋；每行一条共 {n} 行，行首不要编号。")
    raw = llm(prompt)
    lines = [l for l in clean_lines(raw) if valid(l)]
    # dedupe within bucket
    seen, uniq = set(), []
    for l in lines:
        if l not in seen:
            seen.add(l); uniq.append(l)
    return uniq

def gen_sprite_bucket(ctx_desc, n=4):
    prompt = (f"你是赛博像素城市里的小生灵（光猫、灯灵、光鸟这类像素精灵）。当前情境：{ctx_desc}。\n"
              f"写 {n} 条这类小生灵会发出的「话」——可以用拟声（喵呜/叮/啾）带一点短句意思，每条 4-16 字；"
              f"禁数字、禁人名地名；每行一条共 {n} 行，不要编号。")
    raw = llm(prompt)
    banned = ["CEO", "Jason", "公司", "集团", "总部", "董事长", "经理"]
    lines = [l for l in clean_lines(raw)
             if 4 <= len(l) <= 24 and not re.search(r"[0-9]", l)
             and not any(b in l for b in banned)]
    return lines

def save_pools(pools):
    """Atomic save, called per bucket: a budget-killed round keeps finished
    buckets on disk, so --append resumes instead of losing the whole run."""
    tmp = POOL + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pools, f, ensure_ascii=False, indent=1)
    os.replace(tmp, POOL)

def acquire_lock(max_age=1800):
    """Single pool-writer lock (stale after max_age seconds)."""
    try:
        if os.path.isfile(LOCK) and (time.time() - os.path.getmtime(LOCK)) < max_age:
            return False
        os.makedirs(os.path.dirname(LOCK), exist_ok=True)
        with open(LOCK, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True  # never block growth on a broken lock

# --- greetings face (T-20260924-06③; contract = cognition/GREETINGS.md v1.0) ---
GREET = os.path.join(CO, "cognition", "greetings.json")
GKEYS = {
    "first_meet": "初次见面，头一回打照面打招呼",
    "reunion": "老熟人重逢，久别再见的寒暄",
    "smalltalk": "街坊日常寒暄，碰面搭话闲聊",
    "farewell": "道别再见，回头见的那种告别",
}
ENV_CHARS = "雨风雪月星"
ENV_TOKENS = ("今早", "今晚", "今夜", "清晨", "早晨", "早上", "早安", "晚安",
              "晚上", "深夜", "夜深", "晨光", "黄昏", "傍晚", "凌晨", "半夜",
              "正午", "晌午", "中午")
GREET_TARGET, GREET_FLOOR = 10, 6
FAQ_TARGET, FAQ_FLOOR = 3, 2

def greet_valid(line):
    if not (4 <= len(line) <= 24): return False
    if re.search(r"[0-9]", line): return False
    if re.search(r"(19|20)\d{2}年", line): return False
    if any(b in line for b in ["CEO", "Jason", "公司", "集团", "总部", "董事长", "经理"]):
        return False
    if re.match(r"^[A-Za-z]+[\"'“”]", line): return False
    if re.search(r"(user|assistant|system)[\"'“”‘’]", line): return False
    if any(c in line for c in ENV_CHARS): return False
    if any(t in line for t in ENV_TOKENS): return False
    return True

def gen_greet_bucket(axis_desc, scene_desc, n=6, sprite=False):
    if sprite:
        prompt = (f"你是赛博像素城市里的小生灵（光猫、灯灵、光鸟这类像素精灵）。"
                  f"社交场景：{scene_desc}。\n写 {n} 条这类小生灵打招呼、寒暄或道别时会发出的「话」——"
                  f"可以用拟声（喵呜/叮/啾）带一点短句意思，每条 4-16 字；禁数字、禁人名地名；"
                  f"严禁天气词（雨、风、雪）、天体词（月、星）、时段问候词（今早、清晨、早上好、晚安这类）；"
                  f"每行一条共 {n} 行，行首不要编号。")
    else:
        prompt = (f"你是赛博像素城市「超体宇宙城」的市民台词生成器。这类市民的思想气质：{axis_desc}。"
                  f"社交场景：{scene_desc}。\n写 {n} 条这类市民在这个场景下打招呼、寒暄或道别的短句。"
                  f"硬规则：每条 4-16 字；口语化、有生活气；这是纯社交口气，不携带环境事实——"
                  f"严禁天气词（雨、风、雪）、天体词（月、星）、时段问候词（今早、清晨、早上好、晚安这类）；"
                  f"禁数字、人名、地名、日期、金额、公司名；每行一条共 {n} 行，行首不要编号。")
    raw = llm(prompt)
    return [l for l in clean_lines(raw) if greet_valid(l)]

def gen_faq_bucket(axis_desc, n=3, sprite=False):
    who = ("你是赛博像素城市里的小生灵（光猫、灯灵、光鸟这类像素精灵）"
           if sprite else
           f"你是赛博像素城市「超体宇宙城」的市民台词生成器。这类市民的思想气质：{axis_desc}")
    prompt = (who + f"。\n写 {n} 组「常问应答」——街坊或来参观的人常问的日常小问题，和口语化的回答。"
              f"硬规则：问句 4-16 字（真的会问的日常小问题，不谈公事），回答 4-20 字；"
              f"问答都不带环境词（雨、风、雪、月、星、今早、晚安这类），不带数字、人名、地名、公司名；"
              f"每组两行：一行以「问：」开头，一行以「答：」开头，共 {n} 组，不要其他说明。")
    raw = llm(prompt)
    pairs, q = [], None
    for ln in raw.splitlines():
        s = re.sub(r"^[0-9一二三四五六七八九十]+[、.．)）]?\s*", "", ln.strip())
        if s.startswith("问：") or s.startswith("问:"):
            q = s.split("：", 1)[-1].split(":", 1)[-1].strip(" 「」“”\"'")
        elif (s.startswith("答：") or s.startswith("答:")) and q is not None:
            a = s.split("：", 1)[-1].split(":", 1)[-1].strip(" 「」“”\"'")
            if 4 <= len(q) <= 20 and greet_valid(q) and greet_valid(a):
                pairs.append({"q": q, "a": a})
            q = None
    seen, uniq = set(), []
    for p in pairs:
        if p["q"] not in seen:
            seen.add(p["q"]); uniq.append(p)
    return uniq

def save_greetings(greets):
    tmp = GREET + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(greets, f, ensure_ascii=False, indent=1)
    os.replace(tmp, GREET)

def gen_greetings(all_lines, deadline=None, resume=False):
    greets = {"greet": {"axes": {}, "sprite": {}}, "faq": {}}
    if resume and os.path.isfile(GREET):
        with open(GREET, encoding="utf-8") as f:
            greets = json.load(f)
        for ax in greets.get("greet", {}).get("axes", {}).values():
            for b in ax.values(): all_lines.update(b)
        for b in greets.get("greet", {}).get("sprite", {}).values():
            all_lines.update(b)
        for b in greets.get("faq", {}).values():
            for p in b:
                all_lines.update((p.get("q", ""), p.get("a", "")))
    fails, stopped = [], False
    for axis, adesc in AXES.items():
        greets["greet"]["axes"].setdefault(axis, {})
        for gk, sdesc in GKEYS.items():
            if deadline and time.time() > deadline:
                stopped = True; break
            bucket = greets["greet"]["axes"][axis].setdefault(gk, [])
            got = [l for l in bucket if greet_valid(l)]
            if len(got) < GREET_TARGET:
                for _ in range(3):
                    fresh = [l for l in gen_greet_bucket(adesc, sdesc) if l not in all_lines]
                    got = got + fresh; all_lines.update(fresh)
                    if len(got) >= GREET_TARGET: break
                got = got[:GREET_TARGET]
                greets["greet"]["axes"][axis][gk] = got
                save_greetings(greets)
                if len(got) < GREET_FLOOR: fails.append(f"greet/{axis}/{gk}={len(got)}")
                print(f"greet {axis}/{gk}: {len(got)}")
            else:
                greets["greet"]["axes"][axis][gk] = got[:GREET_TARGET]
                print(f"greet {axis}/{gk}: {len(got)} (at target)")
        if stopped: break
    if not stopped:
        for gk, sdesc in GKEYS.items():
            if deadline and time.time() > deadline:
                stopped = True; break
            bucket = greets["greet"]["sprite"].setdefault(gk, [])
            got = [l for l in bucket if greet_valid(l)]
            if len(got) < GREET_TARGET:
                for _ in range(3):
                    fresh = [l for l in gen_greet_bucket(None, sdesc, sprite=True) if l not in all_lines]
                    got = got + fresh; all_lines.update(fresh)
                    if len(got) >= GREET_TARGET: break
                got = got[:GREET_TARGET]
                greets["greet"]["sprite"][gk] = got
                save_greetings(greets)
                if len(got) < GREET_FLOOR: fails.append(f"greet/sprite/{gk}={len(got)}")
                print(f"greet sprite/{gk}: {len(got)}")
            else:
                greets["greet"]["sprite"][gk] = got[:GREET_TARGET]
                print(f"greet sprite/{gk}: {len(got)} (at target)")
    if not stopped:
        for fam, adesc in list(AXES.items()) + [("sprite", None)]:
            if deadline and time.time() > deadline:
                stopped = True; break
            bucket = greets["faq"].setdefault(fam, [])
            got = [p for p in bucket if isinstance(p, dict) and "q" in p and "a" in p]
            if len(got) < FAQ_TARGET:
                for _ in range(3):
                    for p in gen_faq_bucket(adesc, sprite=(fam == "sprite")):
                        if p["q"] in all_lines or p["a"] in all_lines: continue
                        got.append(p); all_lines.update((p["q"], p["a"]))
                    if len(got) >= FAQ_TARGET: break
                got = got[:FAQ_TARGET]
                greets["faq"][fam] = got
                save_greetings(greets)
                if len(got) < FAQ_FLOOR: fails.append(f"faq/{fam}={len(got)}")
                print(f"faq {fam}: {len(got)}")
            else:
                greets["faq"][fam] = got[:FAQ_TARGET]
                print(f"faq {fam}: {len(got)} (at target)")
    if stopped:
        save_greetings(greets)
    return greets, fails, stopped

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--target", type=int, default=15, help="lines per axes bucket (floor 4, cap 15)")
    ap.add_argument("--sprite-target", dest="sprite_target", type=int, default=10,
                    help="lines per sprite bucket (floor 3, cap 10)")
    ap.add_argument("--greetings", action="store_true",
                    help="generate the greetings face (greet+faq; GREETINGS.md contract v1.0)")
    ap.add_argument("--budget", type=int, default=0,
                    help="soft seconds budget; stop cleanly between buckets (0=off)")
    args = ap.parse_args()
    args.target = max(4, min(15, args.target))
    args.sprite_target = max(3, min(10, args.sprite_target))
    if args.append and not acquire_lock():
        print("pool round already running (lock held); skip")
        sys.exit(0)
    if args.greetings:
        all_lines = set()
        if os.path.isfile(POOL):
            with open(POOL, encoding="utf-8") as f:
                pools = json.load(f)
            for v in pools.values():
                for ax in v.values():
                    if isinstance(ax, list): all_lines.update(ax)
                    else:
                        for ctx in ax.values(): all_lines.update(ctx)
        deadline = time.time() + args.budget if args.budget > 0 else None
        greets, fails, stopped = gen_greetings(all_lines, deadline, resume=args.append)
        total = (sum(len(b) for ax in greets["greet"]["axes"].values() for b in ax.values())
                 + sum(len(b) for b in greets["greet"]["sprite"].values())
                 + sum(2 * len(b) for b in greets["faq"].values()))
        try:
            if os.path.isfile(LOCK): os.remove(LOCK)
        except Exception:
            pass
        print(f"GREETINGS_TOTAL={total} FAIL_BUCKETS={fails if fails else 'NONE'}"
              + (" BUDGET_STOP=resume-next-greetings-round" if stopped else ""))
        sys.exit(1 if fails else 0)
    pools = {"axes": {}, "sprite": {}}
    if args.append and os.path.isfile(POOL):
        with open(POOL, encoding="utf-8") as f:
            pools = json.load(f)
    all_lines = set()
    for v in pools.values():
        for ax in v.values():
            if isinstance(ax, list):  # sprite buckets are ctx->list, axes are ctx->dict
                all_lines.update(ax)
            else:
                for ctx in ax.values():
                    all_lines.update(ctx)
    fails = []
    for axis, adesc in AXES.items():
        pools["axes"].setdefault(axis, {})
        for ctx, cdesc in CONTEXTS.items():
            pools["axes"][axis].setdefault(ctx, [])
            got = [l for l in pools["axes"][axis][ctx] if valid(l)]
            if len(got) >= args.target:
                pools["axes"][axis][ctx] = got[:args.target]
                print(f"bucket {axis}/{ctx}: {len(got)} (at target)")
                continue
            for attempt in range(3):
                fresh = [l for l in gen_bucket(adesc, cdesc) if l not in all_lines]
                got = got + fresh
                all_lines.update(fresh)
                if len(got) >= args.target: break
            got = got[:args.target]
            pools["axes"][axis][ctx] = got
            save_pools(pools)
            if len(got) < 4:
                fails.append(f"{axis}/{ctx}={len(got)}")
            print(f"bucket {axis}/{ctx}: {len(got)}")
    for ctx, cdesc in SPRITE_CONTEXTS.items():
        pools["sprite"].setdefault(ctx, [])
        got = [l for l in pools["sprite"].get(ctx, []) if 4 <= len(l) <= 24]
        if len(got) >= args.sprite_target:
            pools["sprite"][ctx] = got[:args.sprite_target]
            print(f"bucket sprite/{ctx}: {len(got)} (at target)")
            continue
        for attempt in range(2):
            fresh = [l for l in gen_sprite_bucket(cdesc) if l not in all_lines]
            got = got + fresh
            all_lines.update(fresh)
            if len(got) >= args.sprite_target: break
        got = got[:args.sprite_target]
        pools["sprite"][ctx] = got
        save_pools(pools)
        if len(got) < 3:
            fails.append(f"sprite/{ctx}={len(got)}")
        print(f"bucket sprite/{ctx}: {len(got)}")
    save_pools(pools)
    try:
        if os.path.isfile(LOCK):
            os.remove(LOCK)
    except Exception:
        pass
    # QC summary
    total = sum(len(c) for ax in pools["axes"].values() for c in ax.values()) + sum(len(c) for c in pools["sprite"].values())
    print(f"TOTAL={total} FAIL_BUCKETS={fails if fails else 'NONE'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
