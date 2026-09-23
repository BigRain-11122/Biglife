#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pool_gen.py - city speech pool generator (cognition layer 2).

Pre-generates bark lines for ALL citizens to share: 6 thought-axes x 12 real
contexts (+ sprite pool). Paid once, consumed forever at zero cost.
Honesty law (cognition/README): pool = context-flavored tone, zero concrete
facts - no digits, no names, no dates; facts enter only via spotlight/ring,
and pool contexts are only ACTIVATED by real data (the fact gate).
Local Ollama only (qwen2.5:7b-instruct, zero token).
Usage: python -X utf8 pool_gen.py [--append]
"""
import argparse, json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
POOL = os.path.join(CO, "cognition", "pools.json")
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
    lines = [l for l in clean_lines(raw) if 4 <= len(l) <= 24 and not re.search(r"[0-9]", l)]
    return lines

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--append", action="store_true")
    args = ap.parse_args()
    pools = {"axes": {}, "sprite": {}}
    if args.append and os.path.isfile(POOL):
        with open(POOL, encoding="utf-8") as f:
            pools = json.load(f)
    all_lines = set()
    for v in pools.values():
        for ax in v.values():
            for ctx in ax.values():
                all_lines.update(ctx)
    fails = []
    for axis, adesc in AXES.items():
        pools["axes"].setdefault(axis, {})
        for ctx, cdesc in CONTEXTS.items():
            need = 4
            got = [l for l in pools["axes"][axis].get(ctx, []) if valid(l)]
            if len(got) >= 6 and not args.append:
                pools["axes"][axis][ctx] = got[:6]; continue
            for attempt in range(3):
                fresh = [l for l in gen_bucket(adesc, cdesc) if l not in all_lines]
                got = got + fresh
                all_lines.update(fresh)
                if len(got) >= 6: break
            got = got[:6]
            pools["axes"][axis][ctx] = got
            if len(got) < need:
                fails.append(f"{axis}/{ctx}={len(got)}")
            print(f"bucket {axis}/{ctx}: {len(got)}")
    for ctx, cdesc in SPRITE_CONTEXTS.items():
        pools["sprite"].setdefault(ctx, [])
        got = [l for l in pools["sprite"].get(ctx, []) if 4 <= len(l) <= 24]
        if len(got) >= 3 and not args.append:
            pools["sprite"][ctx] = got[:5]; continue
        for attempt in range(2):
            fresh = [l for l in gen_sprite_bucket(cdesc) if l not in all_lines]
            got = got + fresh
            all_lines.update(fresh)
            if len(got) >= 3: break
        got = got[:5]
        pools["sprite"][ctx] = got
        if len(got) < 3:
            fails.append(f"sprite/{ctx}={len(got)}")
        print(f"bucket sprite/{ctx}: {len(got)}")
    with open(POOL, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pools, f, ensure_ascii=False, indent=1)
    # QC summary
    total = sum(len(c) for ax in pools["axes"].values() for c in ax.values()) + sum(len(c) for c in pools["sprite"].values())
    print(f"TOTAL={total} FAIL_BUCKETS={fails if fails else 'NONE'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
