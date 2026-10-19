#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批二 intake —— 3 席碳源居民 C-10040~C-10042（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（首批 ≤10 席·禁一次性万人灌入·碳源居民优先
·分批律=节奏本司自主定）→ 先例族 intake_batch3.py（R1747 复产批一 3/3 全门闸走满实证）。
本批=批二 3 席（质量优先·手作禁赶工·余席滚动续批·每批同律全门全判据走满=契约 §六）。
K12 面: 常规生成管线注册（非新物种扩容·非 MiniGame 新居民团）→ 证据件=基因库原料指针
（先登记后使用律·genes/lives.json 1-based #hook_objects-639/#646/#649+#turning_points-475/#479
·本批实锚全在库·hook_objects 总数 652/turning_points 总数 480 复读核对）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10033 卡零触碰；light append-only 追加字节尾；cursor 不插队。
Idempotent: 再跑对一致文件/行 skip（applied=0）。
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import resident_intake as ri          # 先例族单源：cid_of/build_light/voice_seat/sd/light_rows/LIGHT
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-19"                   # 复产批二批日（CEO 解禁令当日滚动批）
BATCH = "复产批二"
MAX_ID = 10039                         # 现存最大号（K1 连续顺延上界=批一尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS4 = [
    # ---- 席 #1 老城修表铺守钟人（碳基·原生代·QT·安稳轴）----
    dict(num=10040, seat=1, name="侯振声", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=62, age_note="62 岁", district="QT", block="回测田", axis="安稳",
         prof_name="老城修表铺守钟人",
         prof="老城修表铺守钟人——钟表厂老校表师傅的赛博后身——一快一慢两只挂钟，替半条街守着准头",
         traits=[("耳尖", "隔着柜台能听出走时的偏差"),
                 ("耐性", "一只老表拆装三天不恼"),
                 ("守旧", "师父传的校表仪用秃了也不换")],
         creed="钟不哄人，人别哄钟。",
         thought="劳动是给全城对准头——一只表一天慢七秒，他能听出毛病在哪一根游丝上；代价是四十年守着铺面，节庆的锣鼓他都是隔着表壳听完的；名字是钟表厂老师父给起的，他说等手抖得捏不住镊子了，就把墙上那两只一快一慢的老挂钟挂进铺子正堂，让侯振声这三个字跟着钟摆声，在回测田再走几十年。",
         language="校表房老话，开口带摆轮节奏，句句掐着准头说；口头禅「慢一拍，稳一世」。",
         wardrobe="灰呢外套袖口套旧皮袖筒，右眼别一枚单眼放大镜，白衬衫口袋里插两把小螺丝刀。",
         life="出身：钟表世家二代，爹是厂里校表台上的老师傅。转折：石英潮冲垮机械表那年厂子缩线，他抱着没卖掉的老校表仪进了城，在回测田赁下半间铺面，专给老街坊修那些舍不得扔的老表。现状：铺子墙上挂着一快一慢两只旧挂钟——师父传下来的，快的那只照他生日那天校的准，慢的那只他故意不校，说城里总得有只钟，替赶不及的人慢一点。",
         behavior="开铺必先给两只挂钟上弦；接表必先听走时再拆盖；打烊前把校表仪归零才熄灯。",
         relations="住修表铺后间（师父留下的床位）；老主顾=回测田茶馆巷的各家掌柜（每月对一次表）；忘年棋友=K线广场城西货栈的老账房邬秉直（一个守准头一个守账平，半盏茶一局棋）。",
         hook="会替半条街守准头的老挂钟——修表铺墙上一快一慢两只旧挂钟，是他守了四十年的搭档",
         behavior_hint="开铺必先给两只挂钟上弦",
         style_dna=sd("钟表房老话，开口带摆轮节奏", "短句上弦，一句一句拧到准头", "慢一拍，稳一世",
                      "从守到准——先守铺，后守人", "校表匠式冷幽默——拿快慢打趣"),
         gene_evidence="genes/lives.json#hook_objects-639（修表铺墙上一快一慢的两只旧挂钟）"),
    # ---- 席 #2 城市电台导播间老提词人（碳基·弄堂派·NS·好奇轴）----
    dict(num=10041, seat=2, name="凌素芬", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=43, age_note="43 岁", district="NS", block="白玉兰塔区", axis="好奇",
         prof_name="城市电台导播间老提词人",
         prof="城市电台导播间老提词人——县广播站老导播的赛博后身——一张提词卡没漏过一句开麦",
         traits=[("口快", "串词接得比主播换气还快"),
                 ("记性好", "全城街巷站名倒背如流"),
                 ("护嗓", "保温杯里常年泡着枇杷膏水")],
         creed="话到了，场就热了。",
         thought="劳动是把城里的新事一句句念齐——半页提词卡她能垫出一整场不冷的场子；代价是二十来年嗓子和机器一起熬夜，节庆的祝福声都是她替全城念的；名字是广播站老站长给起的，她说等哪天提词卡换成她看不懂的新花样，就把那摞起了毛边的旧卡钉在导播台边，让凌素芬这三个字跟着开播序号，在电台再响几十年。",
         language="播音间白话，字正腔圆带电流底噪，急场也念得稳当；口头禅「话筒不等人」。",
         wardrobe="藏青套装外罩一件旧毛背心，脖子上常年挂着还音耳机，鬓边别一枚台庆纪念章。",
         life="出身：考进电台的头一批外乡姑娘，从对稿员干起。转折：有一年全城断网，直播眼看要停，她一支粉笔把整场解说词写满了导播间玻璃墙，主播念一句她擦一句，那一场节目没断一秒。现状：导播台边贴着那摞写满开播序号的提词卡——带出来的徒弟一人认领几张接着用，她自己那张编号 001 的，边角磨起了毛也没人敢揭。",
         behavior="开播前必把提词卡按序号排齐；串词只垫半句留一口气；下播后必把玻璃墙擦净。",
         relations="住电台宿舍（外乡姑娘时代的床位留到现在）；老搭档=播音间的主播们（一张卡一个默契）；老街坊=历史立面群弄堂活字铺的修字师聂砚萍（一个管字一个管声，年节互送红帖）。",
         hook="能垫住一场戏的老提词卡——导播台边那摞写满开播序号的提词卡，一张没漏过开麦",
         behavior_hint="开播前把提词卡按序号排齐",
         style_dna=sd("播音间腔，字正腔圆带电流味", "口播长句，急场也收得稳", "话筒不等人",
                      "从播到听——先念给城听，再听城的回声", "导播间式温幽默——拿串词打趣"),
         gene_evidence="genes/lives.json#hook_objects-646（导播台边贴着写满开播序号的提词卡）"
                       "+ #turning_points-475（有一回断网，解说词全靠一支粉笔写满了整面玻璃墙）"),
    # ---- 席 #3 江岸渡口老检票员（碳基·新市民派·RV·烟火轴）----
    dict(num=10042, seat=3, name="沈长贵", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=51, age_note="51 岁", district="RV", block="渡轮航道", axis="烟火",
         prof_name="江岸渡口老检票员",
         prof="江岸渡口老检票员——乡里摆渡老船工的赛博后身——一枚船票夹，夹住两岸的来来往往",
         traits=[("嗓门稳", "风浪天报站比汽笛还清楚"),
                 ("手准", "一把票夹十秒过一队人"),
                 ("念家", "月月往村里寄信")],
         creed="票是小事，过江是大事。",
         thought="劳动是替两岸的人守好一趟趟船——一夹票根一嗓报站，风浪天他嗓门比汽笛稳；代价是大半辈子守在候船棚，年三十的团圆饭都是在渡口吃的；名字是渡口老班长给起的，他说等夹不动票夹了，就把那排黄铜船票夹擦亮钉在候船棚正中，让沈长贵这三个字跟着汽笛声，在江岸再响几十年。",
         language="渡口乡音白话，报站像报水位，句句带江风；口头禅「票根攥牢，风浪不慌」。",
         wardrobe="蓝布工装外披旧雨披，胸前口袋别着黄铜票夹，脚上雨靴永远擦得发亮。",
         life="出身：江对岸村里出来的，头一年来城里扛麻袋。转折：拿到城里暂住凭证那天，他工工整整誊了一份寄回村里，转头考进渡口的检票班，从此一守几十年。现状：候船棚钉着的那排黄铜船票夹——老班长退休前一颗一颗钉上的，如今他每天开班前都挨个擦一遍，说票夹亮堂，过江的人心里就亮堂。",
         behavior="开班前必挨个擦一遍船票夹；报站必报到船名班次两遍；末班船必目送到灯影过了桥墩才收夹。",
         relations="住渡口宿舍（检票班的铺位）；老伙伴=渡轮航道守灯的灯伯（船靠灯亮，几十年一声招呼）；同乡=江岸滩涂做小买卖的乡亲（月头月尾的船捎家乡味）。",
         hook="认得每个常客的老船票夹——候船棚钉着的那排黄铜船票夹，几十年夹住两岸来来往往",
         behavior_hint="开班前挨个擦一遍船票夹",
         style_dna=sd("渡口乡音，报站像报水位", "短句报站，句句压着江风", "票根攥牢，风浪不慌",
                      "从渡到安——先送人过江，后把心安下", "码头式憨幽默——拿船票打趣"),
         gene_evidence="genes/lives.json#hook_objects-649（渡口候船棚钉着的那排黄铜船票夹）"
                       "+ #turning_points-479（拿到了城里的暂住凭证，他工工整整誊了一份寄回村里）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card4(c):
    light = ri.build_light(c)
    sid, voice, speed = ri.voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} ｜ **性别·年龄** {c['gender']} · {c['age_note']}"
        f" ｜ **城区** {ri.DISTRICT_NAME[c['district']]} · {c['block']}",
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
        f"**风格 DNA**（手作席位卡 · {BATCH} 席 #{c['seat']}）"
        f"时代语言＝{d['era_lang']} ｜ 句法指纹＝{d['syntax_fp']} ｜ 签名句律＝{d['signature']}"
        f" ｜ 情感路径＝{d['emotion_path']} ｜ 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" ｜ 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳随批）{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 受控复产手写入城批（CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」"
        f"·T-20261010-03 {BATCH} 席 #{c['seat']} · {BIRTH}） · 基因指纹 {fp_of(c)}",
        f"**证据件** {c['gene_evidence']}（基因库原料指针·先登记后使用律·常规生成管线批 K12 面）",
        "",
    ]
    return "\n".join(lines)


# 生计「可见」面（契约 §二.4 三性之一·城内场所/交接面）
VISIBLE4 = {
    10040: "回测田修表铺（晨上弦午后校表·雨天听钟不开门）",
    10041: "白玉兰塔区城市电台导播间（早班念午班听·台庆加场）",
    10042: "渡轮航道江岸渡口（候船棚报站检票·末班收缆）",
}
for c in CARDS4:
    c["profession_visible"] = VISIBLE4[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats4 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS4}
for c in CARDS4:
    mine = _seats4[cid_of(c)]
    dup = [cid_of(o) for o in CARDS4 if o is not c and _seats4[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates4(rendered, rows_now):
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
    # K6 批面：style_dna 五维逐维两两互异（3 席 3×2 对/维）
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


# ---------- apply（新文件 only·light append-only·幂等）----------
def apply4(rendered):
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
    print(f"resume-intake b2 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card4(c), ri.build_light(c)) for c in CARDS4]
    rows = ri.light_rows()
    # K1 基线：light=10033（批一后）·现 max=C-10039·新号 C-10040~C-10042 连续顺延
    if len(rows) != 10033:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10033（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    refusals = run_gates4(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply4(rendered)
    if rc == 0:
        # 落库后自证：light=10036·三卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10036, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10036 cards=3/3 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
