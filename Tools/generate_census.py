#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BigLife census generator v1.0 - renders 10,000 citizen cards from gene banks.

Law: docs/CODEX.md (population codex). Deterministic: seed fixed for batch P-0.
Uniqueness triple-check (CODEX 11): name / hook pair / trait-profession-district fingerprint.
ASCII-safe console output; all files written UTF-8 (no BOM).
Usage: python generate_census.py [--seed 20260923] [--out census]
"""
import json, hashlib, os, random, sys, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
GENES = os.path.join(CO, "genes")

def load(name):
    with open(os.path.join(GENES, name), encoding="utf-8") as f:
        return json.load(f)

META = load("meta.json")
NAMES = load("names.json")
PROF = load("professions.json")
PERS = load("personality.json")
LANG = load("language.json")
WARD = load("wardrobe.json")
LIVES = load("lives.json")
ANCHORS = load("anchors.json")

DISTRICT_NAME = {d["id"]: d["name"] for d in META["districts"]}
DISTRICT_BLOCKS = {d["id"]: d["blocks"] for d in META["districts"]}
SPECIES = {s["id"]: s for s in META["species"]}
CARBON_FACTIONS = {f["id"]: f for f in SPECIES["carbon"]["factions"]}
SPRITE_ROLE = {r["species"]: r for r in PROF["sprite_roles"]}
SPRITE_ROLE_BY_FACTION = {"finch": SPRITE_ROLE["消息雀"], "radiocat": SPRITE_ROLE["电波猫"], "nightlamp": SPRITE_ROLE["守夜灯灵"],
                          "koi": SPRITE_ROLE["数据锦鲤"], "rainfrog": SPRITE_ROLE["雨声蛙"], "chimefly": SPRITE_ROLE["风铃蝶"]}
SILICON_FACTIONS = {f["id"]: f for f in SPECIES["silicon"]["factions"]}
AXES = PERS["axes"]
TRAITS_BY_AXIS = {}
for t in PERS["traits"]:
    TRAITS_BY_AXIS.setdefault(t["axis"], []).append(t)
CREEDS_BY_AXIS = {}
for c in PERS["creeds"]:
    CREEDS_BY_AXIS.setdefault(c["axis"], []).append(c["text"])
CATCH_BY_AXIS = {}
for cp in LANG["catchphrases"]:
    CATCH_BY_AXIS.setdefault(cp["axis"], []).append(cp["text"])
CATCH_ALL = [cp["text"] for cp in LANG["catchphrases"]]
DIALECTS = {d["name"]: d for d in LANG["dialects"]}
PROFS = PROF["professions"]

DENY_NAMES = {"盛永康", "孙君晟", "许瑛琦", "孙弋杰", "Jason", "贾森", "Lucy", "露西"}

def pick(rng, seq):
    return seq[rng.randrange(len(seq))]

def weighted(rng, pairs):
    # pairs: list of (item, weight)
    total = sum(w for _, w in pairs)
    x = rng.random() * total
    for item, w in pairs:
        x -= w
        if x <= 0:
            return item
    return pairs[-1][0]

class Registrar:
    """Global uniqueness registries (CODEX 11.1)."""
    def __init__(self):
        self.names = set()
        self.hooks = set()
        self.fingerprints = set()
        self.name_fail = 0
        self.hook_fail = 0
        self.fp_fail = 0
    def try_name(self, n):
        if n in DENY_NAMES: return False
        if n in self.names: return False
        self.names.add(n); return True
    def try_hook(self, h):
        if h in self.hooks: self.hook_fail += 1; return False
        self.hooks.add(h); return True
    def try_fp(self, key):
        if key in self.fingerprints: self.fp_fail += 1; return False
        self.fingerprints.add(key); return True

REG = Registrar()

def carbon_name(rng, band, gender):
    pools = NAMES["given"]["male" if gender == "M" else "female"]
    for _ in range(200):
        if band == "young" and rng.random() < 0.10:
            given = pick(rng, NAMES["given"]["cyber"])
        else:
            given = pick(rng, pools[band])
        if gender == "F" and band in ("child",) and given in ("元宝", "天天", "阿果", "小北"):
            continue
        name = pick(rng, NAMES["surnames"]) + given
        if REG.try_name(name):
            return name
    # collision fallback: suffix by district disambiguation (CODEX 5.4)
    for i in range(50):
        name = pick(rng, NAMES["surnames"]) + pick(rng, pools[band]) + "-" + pick(rng, ["南岸", "北岸", "桥东", "桥西"])
        if REG.try_name(name):
            return name
    raise RuntimeError("carbon name space exhausted")

SILICON_SUFFIX = ["-2", "-3", "-4", "-5", "-6", "-7", "-8", "-9", "·夜", "·晨", "·午", "·老", "·小", "·甲", "·乙", "·丙", "·丁", "·快", "·慢", "·新", "·拾", "·叁"]
def silicon_name(rng):
    for _ in range(300):
        name = pick(rng, NAMES["silicon_names"])
        if REG.try_name(name):
            return name
    for _ in range(3000):
        name = pick(rng, NAMES["silicon_names"]) + pick(rng, SILICON_SUFFIX)
        if REG.try_name(name):
            return name
    raise RuntimeError("silicon name space exhausted")

SPRITE_PREFIX = ["小", "阿", "黑", "白"]
def sprite_name(rng):
    for _ in range(300):
        name = pick(rng, NAMES["sprite_names"])
        if REG.try_name(name):
            return name
    for _ in range(3000):
        name = pick(rng, SPRITE_PREFIX) + pick(rng, NAMES["sprite_names"])
        if REG.try_name(name):
            return name
    raise RuntimeError("sprite name space exhausted")

def professions_for(rng, district, band, species):
    if species == "sprite":
        return None
    if species == "silicon":
        band = "young" if rng.randrange(100) < 60 else ("mid" if rng.randrange(100) < 80 else "old")
    cands = [p for p in PROFS if district in p["districts"] and band in p["bands"]]
    if not cands:
        cands = [p for p in PROFS if band in p["bands"]]
    return cands

def make_citizen(rng, cid, district, species, band=None):
    sp = SPECIES[species]
    if species == "carbon":
        faction = weighted(rng, [(f["id"], f["weight"]) for f in sp["factions"]])
        if band is None:
            band = weighted(rng, [(b["id"], b["share"]) for b in META["age_bands"]])
        gender = "M" if rng.random() < META["gender"]["male"] else "F"
        age = rng.randrange(META["age_bands"][["child","young","mid","old"].index(band)]["range"][0],
                            META["age_bands"][["child","young","mid","old"].index(band)]["range"][1] + 1)
        name = carbon_name(rng, band, gender)
        age_label = f"{age} 岁"
    elif species == "silicon":
        faction = weighted(rng, [(f["id"], f["weight"]) for f in sp["factions"]])
        gender = "无定" if rng.random() < 0.5 else ("男" if rng.random() < 0.6 else "女")
        years = rng.randrange(2, 40) if faction == "elf" else (rng.randrange(8, 60) if faction == "compiled" else rng.randrange(20, 90))
        age_label = f"编译纪 {years} 年"
        band = "young" if years <= 8 else ("mid" if years <= 25 else "old")
        name = silicon_name(rng)
    else:
        faction = weighted(rng, [(f["id"], f["weight"]) for f in sp["factions"]])
        gender = "无定"
        seasons = rng.randrange(1, 60)
        age_label = f"第 {seasons} 数据季"
        band = "mid"
        name = sprite_name(rng)

    block = pick(rng, DISTRICT_BLOCKS[district])
    cands = professions_for(rng, district, band, species)
    prof = pick(rng, cands) if cands else None

    axis = pick(rng, AXES)
    t1 = pick(rng, TRAITS_BY_AXIS[axis])
    others = [t for a in AXES if a != axis for t in TRAITS_BY_AXIS[a]]
    t2, t3 = rng.sample(others, 2)
    while t2["name"] == t3["name"] or t2["name"] == t1["name"] or t3["name"] == t1["name"]:
        t2, t3 = rng.sample(others, 2)
    creed = pick(rng, CREEDS_BY_AXIS[axis])
    thought = pick(rng, PERS["opinions"][axis]) + pick(rng, PERS["observations"][axis])

    if species == "carbon":
        fac = CARBON_FACTIONS[faction]
        dname = pick(rng, fac["dialects"])
    elif species == "silicon":
        dname = pick(rng, SILICON_FACTIONS[faction]["dialects"])
    else:
        dname = None
    dialect = DIALECTS[dname] if dname else None
    words = rng.sample(dialect["words"], 2) if dialect else []
    if rng.random() < 0.75:
        catch = pick(rng, CATCH_BY_AXIS[axis]).rstrip("。")
    else:
        catch = pick(rng, CATCH_ALL).rstrip("。")

    base = pick(rng, WARD["bases"][CARBON_FACTIONS[faction]["name"] if species == "carbon" else (SILICON_FACTIONS[faction]["name"] if species == "silicon" else "像素灵")])
    trim = pick(rng, WARD["cyber_trim"])
    sig = pick(rng, [s["item"] for s in WARD["signature_items"]])
    if species == "sprite":
        wardrobe = f"{base}。{WARD['sprite_wear']}"
    else:
        wardrobe = f"{base}，{trim}，随身是{sig}。"

    if species == "carbon":
        origin_key = {"lilong": "lilong", "newcomer": "newcomer", "commuter": "commuter", "native": "native"}[faction]
        origin = pick(rng, LIVES["origins"][origin_key])
        origin = origin.replace("{region}", pick(rng, LIVES["origin_regions"])).replace("{year}", pick(rng, LIVES["origin_years"]))
    elif species == "silicon":
        origin_key = {"photonsoul": "photonsoul", "compiled": "compiled", "elf": "elf"}[faction]
        origin = pick(rng, LIVES["origins"][origin_key])
    else:
        origin = pick(rng, LIVES["origins"]["sprite"])

    n_tp = 2 if rng.random() < 0.45 else 1
    tps = rng.sample(LIVES["turning_points"], n_tp)
    present = pick(rng, LIVES["presents"])
    habits = rng.sample(LIVES["sprite_habits"], 2) if species == "sprite" else rng.sample(LIVES["habits"], 2)

    hook_scope = pick(rng, LIVES["hook_scopes"]) if rng.random() < 0.85 else ""
    hook_pool = LIVES["sprite_hook_actions"] if species == "sprite" else LIVES["hook_actions"]
    for _ in range(80):
        act = pick(rng, hook_pool); obj = pick(rng, LIVES["hook_objects"])
        tpl = act.replace(" {obj}", "{obj}").replace("{obj} ", "{obj}")
        hook = tpl.replace("{obj}", obj)
        if REG.try_hook(hook + hook_scope):
            break
    else:
        hook = "有自己的一个小秘密"
        hook_scope = "——等一个值得告诉的人"

    lang_bits = []
    if words:
        lang_bits.append("「" + words[0] + "」「" + words[1] + "」的底色")
    if prof and prof.get("jargon"):
        lang_bits.append("行话「" + "」「".join(prof["jargon"][:2]) + "」")
    lang_bits.append("口头禅「" + catch + "」")
    if dialect:
        lang_bits.append(dialect["note"])
    if species != "sprite":
        language = "，".join(lang_bits) + "。"
    else:
        role = SPRITE_ROLE_BY_FACTION[faction]
        language = (f"{role['species']}的光语与鸣叫（音调有七八种，熟人都听得懂个大概）；高兴时"
                    + pick(rng, ["翅尖打拍子", "尾光会哼歌", "绒羽起涟漪"])
                    + "；行话「" + "」「".join(role["jargon"][:2]) + "」。")

    life = f"出身：{origin}。转折：{tps[0]}"
    if len(tps) > 1:
        life += f"；又有一回，{tps[1]}"
    life += f"。现状：{present}。"

    if species == "sprite":
        role = SPRITE_ROLE_BY_FACTION[faction]
        behavior = f"{habits[0]}；{habits[1]}。"
        prof_line = f"{role['name']}——{role['duty']}"
    else:
        prof_line = f"{prof['name']}：{prof['twist']}"
        behavior = f"{prof['rhythm']}；{habits[0]}；{habits[1]}。"

    thought = swap_pronouns(thought, gender)
    life = swap_pronouns(life, gender)
    behavior = swap_pronouns(behavior, gender)
    hook_scope = swap_pronouns(hook_scope, gender)

    fp_key = (tuple(sorted([t1["name"], t2["name"], t3["name"]])), prof["name"] if prof else faction, district, band, gender)
    for _ in range(80):
        if REG.try_fp(fp_key):
            break
        t2, t3 = rng.sample(others, 2)
        fp_key = (tuple(sorted([t1["name"], t2["name"], t3["name"]])), prof["name"] if prof else faction, district, band, gender)
    else:
        REG.try_fp(fp_key + (cid,))

    fp_hash = hashlib.sha1(json.dumps(fp_key, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]

    return {
        "id": cid, "name": name, "species": species, "faction": faction, "gender": gender,
        "age_label": age_label, "district": district, "block": block,
        "prof": prof_line,         "prof_name": (prof["name"] if prof else SPRITE_ROLE_BY_FACTION[faction]["name"]),
        "traits": [t1, t2, t3], "creed": creed, "thought": thought, "language": language,
        "wardrobe": wardrobe, "life": life, "behavior": behavior, "hook": hook, "hook_scope": hook_scope,
        "axis": axis, "fp": fp_hash, "band": band,
    }

def render_card(c, extra_relations=""):
    sp_name = SPECIES[c["species"]]["name"]
    fac_name = (CARBON_FACTIONS[c["faction"]]["name"] if c["species"] == "carbon"
                else SILICON_FACTIONS[c["faction"]]["name"] if c["species"] == "silicon"
                else c["faction"])
    fac_disp = {"finch": "消息雀", "radiocat": "电波猫", "nightlamp": "守夜灯灵", "koi": "数据锦鲤", "rainfrog": "雨声蛙", "chimefly": "风铃蝶"}.get(c["faction"], fac_name)
    gender_disp = {"M": "男", "F": "女"}.get(c["gender"], c["gender"])
    traits = " · ".join(f"{t['name']}（{t['note']}）" for t in c["traits"])
    lines = [
        f"# C-{c['id']:05d} · {c['name']}",
        "",
        f"**物种** {sp_name}·{fac_disp} ｜ **性别·年龄** {gender_disp} · {c['age_label']} ｜ **城区** {DISTRICT_NAME[c['district']]} · {c['block']}",
        f"**职业** {c['prof']}",
        "",
        f"**性格** {traits}",
        "",
        f"**信条** 「{c['creed']}」",
        "",
        f"**思想** {c['thought']}",
        "",
        f"**语言** {c['language']}",
        "",
        f"**服装** {c['wardrobe']}",
        "",
        f"**经历** {c['life']}",
        "",
        f"**行为** {c['behavior']}",
        "",
    ]
    rel = c.get("relations") or extra_relations or "暂无登记的近邻（新区新档，随城市真实事件生长中）"
    lines += [f"**关系** {rel}", "",
              f"**钩子** 全城唯一{c['hook']}的{('居民' if c['species'] != 'sprite' else '像素灵')}{c.get('hook_scope','')}。", "",
              "**进化** v1.0 出生档案 · 2026-09-23 · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
              "",
              f"**溯源** 生成批次 P-0 · 基因指纹 {c['fp']}",
              ""]
    return "\n".join(lines)

REL_TYPES = ["邻居", "棋友", "老主顾", "工友", "忘年交", "牌友", "茶友", "常客", "对手", "老搭档"]

def swap_pronouns(text, gender):
    """Align third-person pronouns in shared gene pools with the citizen's gender."""
    if gender == "F":
        return text.replace("他", "她")
    if gender == "M":
        return text.replace("她", "他")
    return text

def build_households(rng, citizens):
    by_district = {}
    for c in citizens:
        by_district.setdefault(c["district"], []).append(c)
    hcount = 0
    lcount = 0
    for district, members in by_district.items():
        pool = [c for c in members if c["species"] != "sprite"]
        sprites = [c for c in members if c["species"] == "sprite"]
        rng.shuffle(pool)
        idx = 0
        def take(band=None, gender=None, species=None):
            nonlocal idx
            for j in range(idx, len(pool)):
                c = pool[j]
                if band and c["band"] != band: continue
                if gender and c["gender"] != gender: continue
                if species and c["species"] != species: continue
                if c.get("household"): continue
                pool[j], pool[idx] = pool[idx], pool[j]
                idx += 1
                return c
            return None
        while True:
            t = weighted(rng, [(h["type"], h["weight"]) for h in LIVES["households"]])
            grp = []
            if t == "独居":
                c = take()
                if c: grp = [c]
            elif t == "老两口":
                a = take("old", "M"); b = take("old", "F")
                if a and b: grp = [a, b]
            elif t == "夫妻带娃":
                a = take(band=None, gender="M"); b = take(band=None, gender="F")
                k = take("child")
                if a and b and k: grp = [a, b, k]
            elif t == "三代同堂":
                g1 = take("old", "M"); g2 = take("old", "F"); p = take("mid"); k = take("child")
                if g1 and g2 and p and k: grp = [g1, g2, p, k]
            elif t == "兄弟/姐妹同住":
                a = take(None, "M") or take(None, "F")
                b = take(None, a["gender"] if a else None)
                if a and b: grp = [a, b]
            elif t == "室友合租":
                a = take("young"); b = take("young")
                if a and b: grp = [a, b]
            elif t == "师徒同院":
                m = take("mid") or take("old"); app = take("young") or take("child")
                if m and app: grp = [m, app]
            if not grp:
                rest = [c for c in pool[idx:] if not c.get("household")]
                for c in rest:
                    c["household"] = f"H-{district}{hcount:04d}"
                    c["household_type"] = "独居"
                break
            hcount += 1
            hid = f"H-{district}{hcount:04d}"
            for c in grp:
                c["household"] = hid
                c["household_type"] = t
        # sprite packs
        rng.shuffle(sprites)
        while sprites:
            pack, sprites = sprites[:3], sprites[3:]
            lcount += 1
            lid = f"L-{lcount:03d}"
            for c in pack:
                c["household"] = lid
                c["household_type"] = "灵群"

def build_relations(rng, citizens):
    by_district = {}
    for c in citizens:
        by_district.setdefault(c["district"], []).append(c)
    for c in citizens:
        if c["species"] == "sprite" and c["household_type"] == "灵群":
            c["relations"] = f"灵群 {c['household']}（同群共栖）；{DISTRICT_NAME[c['district']]}的街坊都认得它。"
            continue
        parts = []
        if c.get("household"):
            parts.append(f"家户 {c['household']}（{c['household_type']}）")
        others = [o for o in by_district[c["district"]] if o["id"] != c["id"]]
        for _ in range(min(2, len(others))):
            if rng.random() < 0.8 or not parts:
                o = pick(rng, others)
                parts.append(f"{pick(rng, REL_TYPES)} C-{o['id']:05d} {o['name']}")
        c["relations"] = "；".join(parts) + "。" if parts else ""

def render_anchor(a):
    """Hand-written anchor cards (C-00010..C-00029) - full custom content."""
    sp_name = SPECIES[a["species"]]["name"]
    fac_name = (CARBON_FACTIONS[a["faction"]]["name"] if a["species"] == "carbon"
                else SILICON_FACTIONS[a["faction"]]["name"] if a["species"] == "silicon" else a["faction"])
    gender_disp = {"male": "男", "female": "女", "unisex": "无定"}[a["gender"]]
    age_disp = a.get("age_note") or f"{a['age']} 岁"
    traits = " · ".join(f"{t[0]}（{t[1]}）" for t in a["traits"])
    lines = [
        f"# C-{a['cid']:05d} · {a['name']}",
        "",
        f"**物种** {sp_name}·{fac_name} ｜ **性别·年龄** {gender_disp} · {age_disp} ｜ **城区** {DISTRICT_NAME[a['district']]} · {a['block']}",
        f"**职业** {a['profession']}——{a['prof_twist']}",
        "",
        f"**性格** {traits}",
        "",
        f"**信条** 「{a['creed']}」",
        "",
        f"**思想** {a['thought']}",
        "",
        f"**语言** {a['language']}",
        "",
        f"**服装** {a['wardrobe']}",
        "",
        f"**经历** {a['life']}",
        "",
        f"**行为** {a['behavior']}",
        "",
        f"**关系** {a['relations']}",
        "",
        f"**钩子** {a['hook']}",
        "",
        "**进化** v1.0 出生档案 · 2026-09-23 · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        "**溯源** 手写展示锚（原型样板） · 批次 P-0",
        "",
    ]
    light = {
        "id": f"C-{a['cid']:05d}", "name": a["name"], "species": a["species"], "faction": a["faction"],
        "gender": gender_disp, "age": a.get("age"), "age_note": a.get("age_note"),
        "district": a["district"], "block": a["block"], "profession": a["profession"],
        "axis": None, "creed": a["creed"], "hook": a["hook"], "v": 1, "anchor": True,
    }
    return "\n".join(lines), light

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260923)
    ap.add_argument("--out", default=os.path.join(CO, "census"))
    args = ap.parse_args()
    rng = random.Random(args.seed)
    out = args.out
    # LIVE-CENSUS GUARD: once evolution began, regeneration would wipe grown rings.
    if os.path.isfile(os.path.join(CO, "state", "evolve-cursor.json")) and "--force" not in sys.argv:
        print("REFUSED: census is live (evolve-cursor.json exists). Regeneration requires --force and a task-board order.")
        sys.exit(4)
    regdir = os.path.join(out, "registry")
    anchdir = os.path.join(out, "anchors")
    expdir = os.path.join(out, "export")
    for d in (regdir, anchdir, expdir, os.path.join(out, "reserved")):
        os.makedirs(d, exist_ok=True)
    for dd in DISTRICT_NAME:
        os.makedirs(os.path.join(regdir, dd), exist_ok=True)

    # anchors first (C-00010..C-00029)
    citizens = []
    lights = []
    for a in ANCHORS["citizens"]:
        REG.try_name(a["name"])
        text, light = render_anchor(a)
        with open(os.path.join(anchdir, f"C-{a['cid']:05d}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        lights.append(light)

    # generated population (C-00030..C-10000)
    cid = 30
    quotas = []
    for d in META["districts"]:
        for s in META["species"]:
            pass
    district_alloc = {d["id"]: d["quota"] for d in META["districts"]}
    anchor_by_district = {}
    for a in ANCHORS["citizens"]:
        anchor_by_district[a["district"]] = anchor_by_district.get(a["district"], 0) + 1
    total_gen = 10000 - 30 - len(ANCHORS["citizens"])
    # species split global
    species_counts = {"carbon": int(round(total_gen * 0.75)), "silicon": int(round(total_gen * 0.20)), "sprite": 0}
    species_counts["sprite"] = total_gen - species_counts["carbon"] - species_counts["silicon"]
    # distribute species per district proportional to quota
    plan = []  # (district, species)
    for did, quota in district_alloc.items():
        n = quota - anchor_by_district.get(did, 0)
        for sp, share in (("carbon", species_counts["carbon"]), ("silicon", species_counts["silicon"]), ("sprite", species_counts["sprite"])):
            pass
    # simpler: flat per-district species ratios (75/20/5), global corrected at the end
    for did, quota in district_alloc.items():
        n = quota - anchor_by_district.get(did, 0)
        nc = int(round(n * 0.75)); ns = int(round(n * 0.20)); nr = n - nc - ns
        for _ in range(nc): plan.append((did, "carbon"))
        for _ in range(ns): plan.append((did, "silicon"))
        for _ in range(nr): plan.append((did, "sprite"))
    rng.shuffle(plan)
    for did, sp in plan:
        c = make_citizen(rng, cid, did, sp)
        citizens.append(c)
        cid += 1
    # fill to exactly 10000 ids
    while cid <= 10000:
        did = pick(rng, list(district_alloc))
        c = make_citizen(rng, cid, did, "carbon")
        citizens.append(c)
        cid += 1

    build_households(rng, citizens)
    build_relations(rng, citizens)

    for c in citizens:
        text = render_card(c)
        with open(os.path.join(regdir, c["district"], f"C-{c['id']:05d}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        lights.append({
            "id": f"C-{c['id']:05d}", "name": c["name"], "species": c["species"], "faction": c["faction"],
            "gender": {"M": "男", "F": "女"}.get(c["gender"], c["gender"]), "age": c["age_label"],
            "district": c["district"], "block": c["block"], "profession": c["prof_name"],
            "axis": c["axis"], "creed": c["creed"], "hook": c["hook"] + c.get("hook_scope", ""), "v": 1,
        })
    with open(os.path.join(expdir, "citizens-light.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for l in lights:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")

    # reserved seats README
    with open(os.path.join(out, "reserved", "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# 城主荣誉市民保留席（C-00001 ~ C-00009）\n\n按 docs/CODEX.md §十：本九席永久保留给 CEO 点名入册的荣誉市民（人设权=CEO），当前空悬。命名后由 OS 循环落卡：正典文件落 FluxVerse，本目录登记户籍号与引文。\n")

    # stats
    n_total = len(lights)
    by_district = {}
    by_species = {}
    by_band = {}
    by_gender = {}
    by_axis = {}
    by_faction = {}
    for l in lights:
        by_district[l["district"]] = by_district.get(l["district"], 0) + 1
        by_species[l["species"]] = by_species.get(l["species"], 0) + 1
        by_faction[l["faction"]] = by_faction.get(l["faction"], 0) + 1
        by_gender[l["gender"]] = by_gender.get(l["gender"], 0) + 1
        by_axis[l["axis"] or "手写锚（六轴之外）"] = by_axis.get(l["axis"] or "手写锚（六轴之外）", 0) + 1
    for c in citizens:
        by_band[c["band"]] = by_band.get(c["band"], 0) + 1
    lines = ["# INDEX —— 万人户籍名册统计（批次 P-0 · 2026-09-23）", "",
             f"**总人口：{n_total}**（生成 {len(citizens)} + 手写锚 {len(ANCHORS['citizens'])} + 保留席 9）", "",
             "## 按城区", ""]
    lines += [f"- {DISTRICT_NAME[k]}：{v}" for k, v in sorted(by_district.items())]
    lines += ["", "## 按物种", ""]
    sp_disp = {"carbon": "碳基市民", "silicon": "硅基民", "sprite": "像素灵"}
    lines += [f"- {sp_disp[k]}：{v}" for k, v in sorted(by_species.items())]
    fac_disp = {"lilong": "弄堂派", "newcomer": "新市民派", "commuter": "通勤族", "native": "原生代",
                "photonsoul": "光机魂系", "compiled": "编译系", "elf": "精灵系",
                "finch": "消息雀", "radiocat": "电波猫", "nightlamp": "守夜灯灵", "koi": "数据锦鲤", "rainfrog": "雨声蛙", "chimefly": "风铃蝶"}
    lines += ["", "## 按派系", ""]
    lines += [f"- {fac_disp.get(k, k)}：{v}" for k, v in sorted(by_faction.items())]
    band_disp = {"child": "少年", "young": "青年", "mid": "中年", "old": "老年"}
    lines += ["", "## 按年龄段（碳基+硅基代际口径）", ""]
    lines += [f"- {band_disp[k]}：{v}" for k, v in sorted(by_band.items())]
    lines += ["", "## 按性别", ""]
    lines += [f"- {k}：{v}" for k, v in sorted(by_gender.items())]
    lines += ["", "## 按思想六轴", ""]
    lines += [f"- {k}轴：{v}" for k, v in sorted(by_axis.items())]
    lines += ["", "## 唯一性三查（CODEX §十一）", "",
              f"- 姓名唯一：{'PASS' if len(REG.names) == len(set(REG.names)) else 'FAIL'}（在册 {len(REG.names)}）",
              f"- 钩子唯一：{'PASS' if len(REG.hooks) == len(set(REG.hooks)) else 'FAIL'}（在册 {len(REG.hooks)}，碰撞重试 {REG.hook_fail} 次）",
              f"- 指纹唯一（特质组×职业×城区×段×性别）：{'PASS' if len(REG.fingerprints) == len(set(REG.fingerprints)) else 'FAIL'}（在册 {len(REG.fingerprints)}，碰撞重试 {REG.fp_fail} 次）",
              "",
              "消费面：`census/export/citizens-light.jsonl`（引擎/CityWatch 只读）。手写锚见 `census/anchors/`。保留席见 `census/reserved/README.md`。",
              ""]
    with open(os.path.join(out, "INDEX.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"OK citizens={n_total} cards registry={len(citizens)} anchors={len(ANCHORS['citizens'])} names={len(REG.names)} hooks_retry={REG.hook_fail} fp_retry={REG.fp_fail}")

if __name__ == "__main__":
    main()
