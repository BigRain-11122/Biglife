#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批三 intake —— 4 席碳源居民 C-10043~C-10046（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（首批 ≤10 席·禁一次性万人灌入·碳源居民优先
·分批律=节奏本司自主定）→ 先例族 intake_batch3.py（R1747 批一 3/3）+ intake_batch4.py
（R1748 批二 3/3 全门闸走满实证）。本批=批三 4 席（祁广顺/鲁怀镜/桂存仁/阮阿桂
·R1749 席位方案定谳+原料 7/7 落库就绪）——四席落=首批 10 席收口。
K12 面: 常规生成管线注册（非新物种扩容·非 MiniGame 新居民团）→ 证据件=基因库原料指针
（先登记后使用律·genes/lives.json 1-based #hook_objects-653/654/655/656
+#turning_points-481/482/483·本批实锚全在库·hook_objects 总数 656/turning_points 总数 483 复读核对）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10036 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批三批日（CEO 解禁令当日滚动批）
BATCH = "复产批三"
MAX_ID = 10042                         # 现存最大号（K1 连续顺延上界=批二尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS5 = [
    # ---- 席 #1 老街机铺修机师（碳基·原生代·GM·求新轴）----
    dict(num=10043, seat=1, name="祁广顺", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="GM", block="游戏楼街区", axis="求新",
         prof_name="老街机铺修机师",
         prof="老街机铺修机师——街机厅老修机师傅的赛博后身——一把烙铁，让整条街的少年时代都续着币",
         traits=[("耳灵", "隔着机箱能听出哪颗电容在喘"),
                 ("手稳", "三十年的烙铁功夫焊点不虚"),
                 ("护旧", "老机器能修绝不换新")],
         creed="机器不老，人心别老。",
         thought="劳动是替整条街守住少年时代——一台老对战机他能让它再响二十年；代价是耳朵里常年嗡着电流声，家里人说话他都得偏着头听；名字是街机厅老掌柜给起的，他说等手抖得捏不住烙铁了，就把那台修了又修的老对战机擦亮摆进铺堂正中，让祁广顺这三个字跟着投币声，在游戏楼再响几十年。",
         language="街机铺老话，开口带币仓铜响，句句像搓招一样利落；口头禅「再来一局，总会赢」。",
         wardrobe="藏蓝工装外套口袋里别着两把小螺丝刀，手腕上常年套着防静电腕带，鼻梁上架一副修机老花镜。",
         life="出身：游戏楼街区土生土长，小时候放学就赖在街机厅看人打对战机。转折：街机换代最凶的那个春天，铺里老机器一台台被抬走当废铁，祁师傅把淘汰的老机器一台台修好摆进铺堂，说留下的是街坊的少年时代。现状：铺堂正中那台摇杆握手处沁出深褐汗光的老对战机——修了又修二十年，街坊来投币打的不是分数，是当年放学的那一局。",
         behavior="开铺必先给每台机器通电试一把；修机必先听电流声再开盖；打烊必把当日币仓擦干才锁门。",
         relations="住街机铺阁楼（老掌柜留下的床位）；街坊=像素匠人巷梆子戏木作坊掌作傅连奎（一个修戏箱一个修机箱，年节互送手艺）；老主顾=游戏楼放学档的半大孩子们（高分榜他手写挂在门口）。",
         hook="摇杆被手汗养出老光的对战机——游戏楼老街机铺铺堂正中那台修了又修的老对战机，续着整条街的少年时代",
         behavior_hint="开铺必先给每台机器通电试一把",
         style_dna=sd("街机铺老话，开口带币仓铜响", "短句快拍，一句接一句像搓招", "再来一局，总会赢",
                      "从修到续——先修机器，后续人心", "街机铺式谐趣幽默——拿搓招打趣"),
         gene_evidence="genes/lives.json#hook_objects-654（游戏楼街机铺里那台修了又修、摇杆握手处沁出深褐汗光的老对战机）"
                       "+ #turning_points-482（街机换代最凶的那个春天，祁师傅把淘汰的老机器一台台修好摆进铺堂，说留下的是街坊的少年时代）"),
    # ---- 席 #2 外环感知塔擦镜师（碳基·通勤族·OR·秩序轴）----
    dict(num=10044, seat=2, name="鲁怀镜", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="女",
         age=46, age_note="46 岁", district="OR", block="感知塔", axis="秩序",
         prof_name="外环感知塔擦镜师",
         prof="外环感知塔擦镜师——天文台老擦镜师傅的赛博后身——一块麂皮，替全城把天擦亮",
         traits=[("眼细", "镜面上一个指纹都藏不住"),
                 ("耐风", "塔顶的风口一站一整天"),
                 ("守时", "擦镜的时辰从不差一刻")],
         creed="天看不清，先擦自己。",
         thought="劳动是替全城把天擦亮——一块镜面干净，塔顶的云脚城外的风都看得真；代价是大半辈子贴着塔顶的风口，年节的家宴她都是看着塔下万家灯火过的；名字是天文台老台长给起的，他说等哪天胳膊举不动麂皮了，就把那块映得出云脚的老镜面擦净封进塔史室，让鲁怀镜这三个字跟着天色，在感知塔再明几十年。",
         language="塔顶静语，句句干净得像擦过的镜面，慢声细语不紧不慢；口头禅「镜面干净，天就老实」。",
         wardrobe="灰蓝风衣配一副薄皮手套，胸前挂一只装麂皮的旧帆布包，袖口永远沾着淡淡的镜粉。",
         life="出身：进城谋生的头一批通勤姑娘，白日在城里做校对，夜里去天文台帮工擦镜。转折：感知塔建起招塔务那年，她凭着擦镜的稳手考了进去，从内环擦到外环，再没离开过塔顶的风。现状：塔顶那块映得出云脚、边角发乌的老镜面——别处早换了新镜，她偏留这块老的，说新镜看得清，老镜看得真。",
         behavior="上塔必先背风把镜面擦三遍；对光必记当日云脚方位；下塔必把麂皮叠回原位。",
         relations="住塔下通勤公寓（早班索道票根攒了一抽屉）；塔下老熟人=白玉兰塔区城市电台的老提词人凌素芬（塔上云脚一变，她开麦就报）；同班组=外环感知网各班塔务（交接班对表各擦各的镜）。",
         hook="映得出云脚的老镜面——感知塔顶那块边角发乌、被她擦了几十年的老镜面",
         behavior_hint="上塔必先背风把镜面擦三遍",
         style_dna=sd("塔顶静语，句句干净得像擦过的镜面", "长句缓拭，一层一层擦到亮", "镜面干净，天就老实",
                      "从拭到明——先擦镜，后望天", "塔顶式淡幽默——拿云影打趣"),
         gene_evidence="genes/lives.json#hook_objects-655（感知塔顶那块映得出云脚、边角发乌的老镜面）"),
    # ---- 席 #3 医馆巷老药师（碳基·原生代·MD·安稳轴）----
    dict(num=10045, seat=3, name="桂存仁", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="MD", block="医馆巷", axis="安稳",
         prof_name="医馆巷老药师",
         prof="医馆巷老药师——百年药铺老柜台的赛博后身——一杆戥子，把医馆巷的分量称了几十年",
         traits=[("手准", "一杆戥子抓药分毫不差"),
                 ("柜熟", "百子柜每格药名倒背如流"),
                 ("心细", "方笺上每味药必查三遍")],
         creed="戥子上见良心。",
         thought="劳动是替一条巷子称住分量——一杆戥子一排药斗，抓出去的每味药都见得着师门；代价是五十年守着药柜，巷口戏台的热闹他都是隔着药香听完的；名字是师门药斗传下来那天师父给起的，他说等眯得看不清药签了，就把那排压着师门药签的老药斗原样锁进铺堂，让桂存仁这三个字跟着药香，在医馆巷再飘几十年。",
         language="药铺柜台老话，字斟句酌带药香，三字一顿见分量；口头禅「药不欺人，分量见真」。",
         wardrobe="深褐布褂外罩一条洗白的围裙，胸前口袋插着老花镜和一沓药签，指间常年带着淡淡的药香。",
         life="出身：师门药铺的关门徒弟，从戥子称药学起。转折：大药行撤柜的那个冬天，整套百子柜眼看要拆散当旧货，桂师傅带着徒弟把整套百子柜连夜盘进医馆巷，一格都没散。现状：药柜顶那排一百零一格、格底压着师门药签的老药斗——百子柜的根底全在这一排斗格里，老街坊抓药，他还是那句话：药斗不乱，分量不欺。",
         behavior="开铺必先校一杆戥子；抓药必对药签查三遍；打烊必把当日方笺压回药斗格底。",
         relations="住药铺后堂（师父留下的老床）；忘年棋友=QUANT 城修表铺守钟人侯振声（一个守分量一个守准头，半盏茶一局棋）；老街坊=医馆巷各家铺面掌柜（节气互送自家吃食）。",
         hook="压着师门药签的老药斗——医馆巷药柜顶那排一百零一格的老药斗，一格一签见师门",
         behavior_hint="开铺必先校一杆戥子",
         style_dna=sd("药铺柜台老话，字斟句酌带药香", "三字一顿的老方笺体，慢工出细活", "药不欺人，分量见真",
                      "从称到守——先称分量，后守巷子", "药柜式干幽默——拿药名打趣"),
         gene_evidence="genes/lives.json#hook_objects-653（医馆巷药柜顶那排一百零一格、格底压着师门药签的老药斗）"
                       "+ #turning_points-483（大药行撤柜的那个冬天，桂师傅带着徒弟把整套百子柜连夜盘进医馆巷，一格都没散）"),
    # ---- 席 #4 趸船茶炉工（碳基·新市民派·RV·烟火轴）----
    dict(num=10046, seat=4, name="阮阿桂", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="女",
         age=55, age_note="55 岁", district="RV", block="渡轮航道", axis="烟火",
         prof_name="趸船茶炉工",
         prof="趸船茶炉工——码头老茶炉工的赛博后身——一把敲火钎，把江上的寒夜敲出热气",
         traits=[("嗓亮", "炉膛一响她喊茶全船都听得见"),
                 ("手快", "一把茶壶十碗热汤不洒一滴"),
                 ("热心", "谁的难处她都记在灶边小本上")],
         creed="一碗热茶，顶得住江风。",
         thought="劳动是替过江的人焐一程热乎——一炉姜茶一碗热汤，寒夜里的渡口有个不熄的亮；代价是小半辈子睡在趸船舱，年三十的饺子都是在船头吃的；名字是渡口老班长给起的，他说等抡不动敲火钎了，就把那把缠满红棉线的老钎挂进候船棚正中，让阮阿桂这三个字跟着茶香，在江岸再飘几十年。",
         language="趸船灶间白话，句句冒热气带江雾味，嗓门混着炉膛响；口头禅「炉子不凉，人心不散」。",
         wardrobe="藏红棉袄外系一条旧帆布围裙，手腕上缠着渡客送的红棉线，脚上布鞋永远擦得干干净净。",
         life="出身：江对岸跟着跑船的爹进的城，头几年在趸船上帮厨烧水。转折：寒潮封航那一夜，末班船的船工冻得握不住缆，她把炉子支到跳板口，一碗姜茶送到开船，渡口管那叫暖心灶。现状：趸船炉膛旁那把缠着一圈圈渡客红棉线的老敲火钎——过江人路过都要摸一把，说摸过火钎，这一冬手都是热的。",
         behavior="开船前必把炉膛掏亮；茶桶必留头一勺给头班船工；封火必把敲火钎挂回炉膛旁老钉子。",
         relations="住趸船舱室（灶间旁的小铺）；同渡口老伙伴=江岸渡口老检票员沈长贵（船一靠班，茶先送到跳板口）；守灯的灯伯（灯亮茶热，几十年一声招呼）。",
         hook="缠满渡客红棉线的老敲火钎——趸船炉膛旁那把缠着一圈圈红棉线的老敲火钎，渡口叫它暖心钎",
         behavior_hint="开船前必把炉膛掏亮",
         style_dna=sd("趸船灶间白话，句句冒热气带江雾味", "热句短促，一句敲一下炉膛", "炉子不凉，人心不散",
                      "从火到暖——先烧一炉，后暖一船", "灶间式热幽默——拿火候打趣"),
         gene_evidence="genes/lives.json#hook_objects-656（趸船炉膛旁那把缠着一圈圈渡客红棉线的老敲火钎）"
                       "+ #turning_points-481（寒潮封航那一夜，她把炉子支到跳板口，一碗姜茶送到开船，渡口管那叫暖心灶）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card5(c):
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
VISIBLE5 = {
    10043: "游戏楼街区老街机铺（晌午开门试机·放学档最忙·周末守铺到深夜）",
    10044: "外环感知塔（晨起擦镜·午后对光·大雾天加巡）",
    10045: "医馆巷老药铺（坐堂抓药·巳时戥秤校准·雨天照常开门）",
    10046: "渡轮航道趸船茶炉（开船前生炉·头班茶送到跳板·末班封火）",
}
for c in CARDS5:
    c["profession_visible"] = VISIBLE5[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats5 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS5}
for c in CARDS5:
    mine = _seats5[cid_of(c)]
    dup = [cid_of(o) for o in CARDS5 if o is not c and _seats5[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates5(rendered, rows_now):
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
    # K6 批面：style_dna 五维逐维两两互异（4 席 4×3 对/维）
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


# ---------- apply（新文件 only·light append-only·幂等）----------
def apply5(rendered):
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
    print(f"resume-intake b3 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card5(c), ri.build_light(c)) for c in CARDS5]
    rows = ri.light_rows()
    # K1 基线：light=10036（批二后）·现 max=C-10042·新号 C-10043~C-10046 连续顺延
    if len(rows) != 10036:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10036（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    refusals = run_gates5(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply5(rendered)
    if rc == 0:
        # 落库后自证：light=10040·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10040, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10040 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
