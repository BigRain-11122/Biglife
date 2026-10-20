#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十二 intake — 2 席碳源居民 C-10079~C-10080（T-20261010-03）。

法源：CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders ·commit 63ccfaba）
→ T-20261010-03 受控复产（分批律·节奏本司自主定）。先例族：intake_batch3~13
（R1747 批一 3/3 … R1787 批十一 4/4 全门闸走满实证）。

本批=量产第十批·复产批十二 2 席（罗守灯·岑记春）——原料按现库可用量定席位
（ho#689-690 + tp#516-517 共 4 条·先登记后使用律），不做超料凑数。

异面注记：临电电工 vs C-10075 老瓦匠（一个屋顶铺瓦一个工地拉线·两手活异面）；
编年史馆户籍誊抄员 vs C-00356 档案修护师（一个抄新录一个修旧档·档事异面）。

K12 面 = 常规生成管线注册（非新物种扩容）。证据件 = 基因库原料指针：
·genes/lives.json 1-based #hook_objects-689/690 + #turning_points-516/517
·本批实锚全在库·hook_objects 总数 690/turning_points 总数 517 复读核对。

Gates（写盘前 fail-fast·任一不 → 整批拒收零写入）: 政治红线 + sublimate_gate 生成面 +
spirit_gate（配额面·碳基零涉） + style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 + 钩子全库唯一。
存量 10072 卡零触碰；light append-only 追加字节尾；cursor 不插队。
批后收口步：needs→behavior→rows 对齐断言（POST_LIGHT=10074）。
Idempotent: 再跑对一致文本 → skip（applied=0）。
"""
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import resident_intake as ri          # 先例族单源：cid_of/build_light/voice_seat/light_rows/LIGHT
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"                   # 复产批十二批日
BATCH = "复产批十二"
MAX_ID = 10078                         # 现存最大号（K1 连续顺延上界=批十一尾席）
POST_LIGHT = 10074                     # 批后 light 断言（10072+2）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS14 = [
    # ---- 席#1 外环夜市修灯摊主（碳基·原生代·OR·侠气轴）----
    dict(num=10079, seat=1, name="罗守灯", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=52, age_note="52 岁", district="OR", block="工地宿舍巷", axis="侠气",
         prof_name="外环夜市修灯摊主",
         prof="外环夜市修灯摊主——工地临电电工的赛博后身——台风过境后的清晨，"
              "他把自己摊上的灯全摘下来挂到断电路口，天亮才发现自己那晚没合眼",
         traits=[("守约", "应下几点来修就几点到，风大也不改口"),
                 ("稳手", "带电的活必先断总闸，再上手"),
                 ("惜物", "灯芯还能救的绝不换新的")],
         creed="灯亮着，路就有人走。",
         thought="劳动是替外环感知区守一盏夜里不灭的灯——新灯再亮，工地和巷口的旧线还得有人肯蹲下来一根一根捋顺，"
                 "他把灯点亮，夜班的人回家的路就有个准头；代价是常年仰头接线落下的颈痛，台风夜连着守两个通宵，"
                 "家里人劝他把摊收了享清福，他总说等这条巷的路灯都稳了再说；名字是老家父亲给起的，说罗家的孩子在工地上守得住灯，"
                 "灯亮了人心就不慌，这名字跟着他从城郊的塔吊下一直守到外环的巷口；他说等拿不稳钳子了，"
                 "就把那只刻着工号的铝饭盒和整袋工具交给肯学接线的年轻人，让罗守灯这三个字跟着一盏一盏的亮，"
                 "在外环感知区的夜里再守几十年",
         language="工地口音的直腔带一点灯油的焦味，开口先问哪条线的灯又不亮了，句尾爱带一句亮着就行；"
                  "口头禅「灯亮着，路就有人走」",
         wardrobe="旧反光背心套在蓝工装上，腰后工具袋里塞着一只掉漆的铝饭盒和几卷绝缘胶布，指尖总沾着细碎的铜屑",
         life="出身：城郊工地棚里长大的孩子，父亲在塔吊下接线，他在旁边递钳子和胶布。"
              "转折：台风过境后的清晨，他把自己摊上的灯全摘下来挂到断电路口，天亮才发现自己那晚没合眼——"
              "摊子少摆一夜不要紧，断电的路口不能黑。"
              "现状：摊上那只掉漆的铝饭盒，底部刻着三横一竖，是他刚进城时刻下的工号——徒弟们笑他留着旧饭盒，"
              "他说那时候一顿饭就是一天的工；同城老友=历史立面群老瓦匠匡稳脊（C-10075·一个铺房顶一个拉线路，外环的两手活）",
         behavior="出摊必先把摊灯一盏盏试亮；接活必先断总闸再上手；收摊必把电线盘成同向的圈，线头一根不落地扎紧",
         relations="住工地宿舍巷的活动板房里（床下就是那袋工具）；同城老友=历史立面群老瓦匠匡稳脊（C-10075·一个铺房顶一个拉线路，外环的两手活）；"
                   "徒弟=巷里跟他学接线的年轻工友",
         hook="一只掉漆的铝饭盒，底部刻着三横一竖，是他刚进城时刻下的工号——外环工地宿舍巷摊上的旧饭盒，"
              "进城那年的一天一顿全刻在这三横一竖里",
         behavior_hint="接活必先断总闸再上手",
         style_dna=sd("工地直腔带灯油焦味", "一句一断，先报险再报修", "灯亮着，路就有人走",
                      "从黑到亮——先断闸，后接线", "电工冷幽默——拿新路灯打趣老胶布"),
         gene_evidence="genes/lives.json#hook_objects-689（一只掉漆的铝饭盒，底部刻着三横一竖，是他刚进城时刻下的工号。）"
                       "+ #turning_points-516（台风过境后的清晨，他把自己摊上的灯全摘下来挂到断电路口，天亮才发现自己那晚没合眼。）"),
    # ---- 席#2 编年史馆户籍誊抄员（碳基·原生代·NS·秩序轴）----
    dict(num=10080, seat=2, name="岑记春", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=49, age_note="49 岁", district="NS", block="编年史馆档案巷", axis="秩序",
         prof_name="编年史馆户籍誊抄员",
         prof="编年史馆户籍誊抄员——老抄录员的赛博后身——编年史馆开放查询那天，"
              "她翻到一条陌生的批注，回头找了半年没找到人，从此每条记录都写得格外仔细",
         traits=[("笔稳", "一页誊完不涂一个墨点"),
                 ("记性", "谁家哪年迁进迁出，她心里有一本"),
                 ("耐烦", "查一条旧记录能翻一下午不催人")],
         creed="写下的每一个字，将来都有人回头找。",
         thought="劳动是替北外滩·治理岸把人的来处一笔一笔誊清楚——系统再快，一条记录写得对不对，"
                 "还得有人肯对着原件逐字核一遍，她把字写准了，往后谁来找自己，就找得到；代价是常年伏案的肩背酸痛，"
                 "眼力一年不如一年，家里人说这活熬人，她总说等这一批旧档誊完再说；名字是母亲给起的，"
                 "说岑家的女儿记事清，一笔一划都是春天里的事，这名字跟着她在档案巷的桌前一坐几十年；"
                 "她说等捏不稳笔了，就把那摞誊完的册子和那只缠了胶带的搪瓷缸交给肯坐得住的年轻人，"
                 "让岑记春这三个字跟着一行一行的册页，在编年史馆里再清楚几十年",
         language="档案室轻软腔带纸墨味，开口先核年份月份，句尾爱带一句写准了；口头禅「写下的每一个字，将来都有人回头找」",
         wardrobe="洗旧的开衫搭在椅背上，袖口用小夹子别住防止蹭墨，桌角搁着一只缠了两圈透明胶带的搪瓷缸",
         life="出身：档案巷誊写室里长大的孩子，母亲抄户籍册，她在旁边裁纸、晾墨。"
              "转折：编年史馆开放查询那天，她在自己的条目里看到一行陌生人的批注，回头找了半年没找到人，"
              "从此每条记录都写得格外仔细——一个不相干的人都会回头看她写的字。"
              "现状：桌角那只搪瓷缸，缸沿磕掉一小块瓷，她用透明胶带细细缠过两圈，说这么握着不硌手——"
              "母亲留下的缸，一缸热水陪她誊过一册又一册；同城老友=历史立面群档案修护师崔阿凤（C-00356·一个抄新录一个修旧档，治理岸的档事两双手）",
         behavior="落笔必先核一遍原件编号；誊完一页必对读一遍不轻过；下班必把缸洗净倒扣，纸面一张不压",
         relations="住编年史馆档案巷后院的旧屋（窗下就是她誊册的长桌）；同城老友=历史立面群档案修护师崔阿凤（C-00356·一个抄新录一个修旧档，治理岸的档事两双手）；"
                   "徒弟=档案巷里跟她核原件的小辈们",
         hook="一只搪瓷缸，缸沿磕掉一小块瓷，她用透明胶带细细缠过两圈，说这么握着不硌手——编年史馆档案巷长桌上的旧缸，"
              "一缸热水陪她誊过一册又一册",
         behavior_hint="誊完一页必对读一遍",
         style_dna=sd("档案室轻软腔带纸墨味", "短句稳落，先核后记", "写下的每一个字，将来都有人回头找",
                      "从陌生到责任——先被看见，后写仔细", "档案室淡幽默——拿新系统打趣旧墨线"),
         gene_evidence="genes/lives.json#hook_objects-690（一只搪瓷缸，缸沿磕掉一小块瓷，他用透明胶带细细缠过两圈，说这么握着不硌手。）"
                       "+ #turning_points-517（编年史馆开放查询那天，他在自己的条目里看到一行陌生人的批注，回头找了半年没找到人，从此每条记录都写得格外仔细。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card14(c):
    light = ri.build_light(c)
    sid, voice, speed = ri.voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} | **性别·年龄** {c['gender']} · {c['age_note']}"
        f" | **城区** {ri.DISTRICT_NAME[c['district']]} · {c['block']}",
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
        f"**关系** {c['relations']}",
        "",
        f"**钩子** 全城唯一{c['hook']}。",
        "",
        f"**生计**（可见）{c['profession_visible']} ·（可积累）年轮履历随城市真实事件写入"
        f" ·（可衰老）{c['age_note']}=资历徽章",
        "",
        f"**风格 DNA**（手作席位卡 · {BATCH} · #{c['seat']}）",
        f"时代语言＝{d['era_lang']} | 句法指纹＝{d['syntax_fp']} | 签名句律＝{d['signature']}"
        f" | 情感路径＝{d['emotion_path']} | 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" | 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳随批）{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历轴 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 受控复产手写入城批（CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」"
        f"·T-20261010-03 {BATCH} · #{c['seat']} · {BIRTH}）· 基因指纹 {fp_of(c)}",
        f"**证据件** {c['gene_evidence']}（基因库原料指针·先登记后使用律·常规生成管线批 K12 面）",
        "",
    ]
    return "\n".join(lines)


# 生计「可见」面（契约 §一.4 三性之一·城内场所/交接面）
VISIBLE14 = {
    10079: "外环工地宿舍巷夜灯修理摊（入夜开摊·台风夜最忙·随叫随到）",
    10080: "编年史馆档案巷誊抄长桌（白日誊册·开馆查询日最忙·桌角一缸常满）",
}
for c in CARDS14:
    c["profession_visible"] = VISIBLE14[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats14 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS14}
for c in CARDS14:
    mine = _seats14[cid_of(c)]
    dup = [cid_of(o) for o in CARDS14 if o is not c and _seats14[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) +
                           " 同席（md5 同池同档·人各一声收口·引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一不 → 整批拒收零写入）----------
def run_gates14(rendered, rows_now):
    spirit_n = sum(1 for r in rows_now if r.get("species") in gc.SPIRIT_SPECIES)
    refusals = []
    names_now = {r["name"] for r in rows_now}
    ids_now = {r["id"] for r in rows_now}
    hooks_now = {r.get("hook", "") for r in rows_now}
    for idx, (c, text, light) in enumerate(rendered):
        cid = cid_of(c)
        rhits = political_redline.scan_text(text)
        if rhits:
            refusals.append(f"{cid} REDLINE REFUSED terms={[h['term'] for h in rhits]}")
        gate_c = {"species": c["species"], "id": c["num"]}
        miss = gc.sublimate_gate(gate_c, text)
        if miss:
            refusals.append(f"{cid} SUBLIMATE REFUSED missing={miss}")
        miss = gc.spirit_gate(gate_c, text, spirit_n + idx)
        if miss:
            refusals.append(f"{cid} SPIRIT REFUSED missing={miss}")
        for k, v in c["style_dna"].items():
            if v not in text:
                refusals.append(f"{cid} INTAKE REFUSED style_dna[{k}] 未逐字入卡")
        sid, voice, speed = ri.voice_seat(c, light)
        seat_line = f"sid {sid} · {voice} · speed {speed}"
        if seat_line not in text:
            refusals.append(f"{cid} INTAKE REFUSED 声位与 VOICE-POOL §一 派生律不一致")
        prof = [ln for ln in text.splitlines() if ln.startswith("**职业** ")][0][len("**职业** "):]
        segs = prof.split("——")
        if not (len(segs) == 3 and all(segs) and "的赛博后身" in segs[1]):
            refusals.append(f"{cid} INTAKE REFUSED 职业行双底座链三段不齐")
        elif segs[0] != light["profession"]:
            refusals.append(f"{cid} INTAKE REFUSED 未来形态≠light profession")
        if "（可见）" not in text or "（可积累）" not in text or "（可衰老）" not in text:
            refusals.append(f"{cid} INTAKE REFUSED 生计三性注记不齐")
        if c["gene_evidence"] not in text:
            refusals.append(f"{cid} INTAKE REFUSED 基因库证据件指针缺失（K12 常规管线面）")
        if light["name"] in names_now:
            refusals.append(f"{cid} INTAKE REFUSED 真名撞库（{light['name']}）")
        if light["id"] in ids_now:
            refusals.append(f"{cid} INTAKE REFUSED ID 撞库")
        if light["hook"] in hooks_now:
            refusals.append(f"{cid} INTAKE REFUSED 钩子撞库（全城唯一律）")
    if len({c["name"] for c, _, _ in rendered}) != len(rendered):
        refusals.append("INTAKE REFUSED 批内真名两两互异失败")
    # K6 批面：style_dna 五维逐维两两互异
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


# ---------- apply（新文件 only·light append-only·幂等）----------
def apply14(rendered):
    applied = skipped = 0
    for c, text, light in rendered:
        path = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            with io.open(path, encoding="utf-8") as f:
                if f.read() == text:
                    skipped += 1
                    continue
                print(f"INTAKE REFUSED: {path} 已存在且内容不一致（活户籍红线·零改写）")
                return 3
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        applied += 1
    with io.open(LIGHT, "rb") as f:
        data = f.read()
    text_rows = data.decode("utf-8")
    have = {json.loads(l)["id"] for l in text_rows.splitlines() if l.strip()}
    new = [l for l in (json.dumps(ri.build_light(c), ensure_ascii=False) for c, _, _ in rendered)
           if json.loads(l)["id"] not in have]
    if new:
        if not data.endswith(b"\n"):
            data += b"\n"
        data += "".join(n + "\n" for n in new).encode("utf-8")
        with io.open(LIGHT, "wb") as f:
            f.write(data)
    total = len(text_rows.splitlines()) + len(new)
    print(f"resume-intake b12 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


# ---------- 批后收口步（intake_batch10 先例：needs→behavior→rows 对齐断言）----------
def post_closeout():
    r1 = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "needs.py")],
                        cwd=HERE, timeout=300, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    r2 = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "behavior.py")],
                        cwd=HERE, timeout=300, capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    beh = os.path.join(CO, "census", "export", "citizen-behavior.jsonl")
    with io.open(beh, encoding="utf-8") as f:
        n = sum(1 for l in f if l.strip())
    tail = [l for l in (r2.stdout or "").splitlines() if l.strip()][-2:]
    print("POST-CLOSEOUT: needs rc=%d behavior rc=%d rows=%d | %s"
          % (r1.returncode, r2.returncode, n, " / ".join(tail)))
    if r2.returncode != 0 or n != POST_LIGHT:
        print("POST-CLOSEOUT FAIL: behavior rc=%d rows=%d != %d" % (r2.returncode, n, POST_LIGHT))
        return 5
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card14(c), ri.build_light(c)) for c in CARDS14]
    rows = ri.light_rows()
    # K1 基线：light=10072（批十一后）·现 max=C-10078·新号 C-10079~C-10080 连续顺延
    if len(rows) != 10072:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10072（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 690 and tp_n == 517):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 690/517（批十二原料基线漂移·零写入）")
        return 4
    ho_texts = {h.rstrip("。") for h in genes["hook_objects"]}
    tp_texts = {t.rstrip("。") for t in genes["turning_points"]}
    for need in ("一只掉漆的铝饭盒，底部刻着三横一竖，是他刚进城时刻下的工号",
                 "一只搪瓷缸，缸沿磕掉一小块瓷，他用透明胶带细细缠过两圈，说这么握着不硌手"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("台风过境后的清晨，他把自己摊上的灯全摘下来挂到断电路口，天亮才发现自己那晚没合眼",
                 "编年史馆开放查询那天，他在自己的条目里看到一行陌生人的批注，回头找了半年没找到人，从此每条记录都写得格外仔细"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates14(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply14(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        # 落库后自证：light=10074·两卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == POST_LIGHT, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light={POST_LIGHT} cards=2/2 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())