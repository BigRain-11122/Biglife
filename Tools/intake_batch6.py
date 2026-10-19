#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批四 intake —— 4 席碳源居民 C-10047~C-10050（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3/4/5
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4 全门闸走满实证）。本批=量产第二批·批四 4 席
（谢韵秋/童守拙/麦冬生/祝九如·R1751 席位方案定谳+原料 8/8 落库就绪·qa/gene-round-R1751.log）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-657/658/659/660+#turning_points-484/485/486/487
·本批实锚全在库·hook_objects 总数 660/turning_points 总数 487 复读核对）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10040 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批四批日（CEO 解禁令当日滚动批）
BATCH = "复产批四"
MAX_ID = 10046                         # 现存最大号（K1 连续顺延上界=批三尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS6 = [
    # ---- 席 #1 老照相馆暗房师傅（碳基·弄堂派·NS·怀旧轴）----
    dict(num=10047, seat=1, name="谢韵秋", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=61, age_note="61 岁", district="NS", block="历史立面群", axis="怀旧",
         prof_name="老照相馆暗房师傅",
         prof="老照相馆暗房师傅——胶卷冲印老师傅的赛博后身——一盏红灯不灭，街坊的旧时光就有处显影",
         traits=[("手轻", "显影盘里的相纸翻面从不带水印"),
                 ("眼准", "显影到七分她一抬手就起盘"),
                 ("念旧", "街坊送来的底片按年代归档从不混")],
         creed="底片不骗人，显影见真章。",
         thought="劳动是替街坊把旧时光留住——一张相纸从药水里浮出来的那一刻，几十年就都回来了；代价是大半辈子守着暗房的红灯，眼睛落下了见不得强光的毛病；名字是照相馆老师傅给起的，她说等显不动影了，就把那台手调放大机擦净封进铺子正堂，让谢韵秋这三个字跟着红灯，在历史立面群再亮几十年。",
         language="暗房慢话，讲影必讲火候，句句要等画面自己浮出来；口头禅「慢工出的影才耐看」。",
         wardrobe="靛灰布衫外罩一条深色旧围裙，胸前挂着放大机的快门线，指尖常年带着淡淡的药水味。",
         life="出身：照相馆世家，十六岁进暗房学显影，头一卷冲的是街坊的全家福。转折：最后一间胶卷冲印铺关张，她把手调放大机搬回弄堂暗房，说慢工出的影才耐看。现状：显影盘边那把被药水咬得发毛的竹夹子还别在围裙带上——老主顾送来的旧底片她还是那句老规矩：急件不接，好影等得起。",
         behavior="开暗房必先校红灯的亮度；显影必掐着第七分起盘；定影完的相纸必在清水里过足一炷香才晾。",
         relations="住照相馆阁楼（老师傅留下的）；街坊客=历史立面群各家翻修老照片的主顾；老街坊=弄堂活字铺修字师聂砚萍（C-10038·一个修字一个修影，同立面群三十年老街坊）。",
         hook="被药水咬出毛边的老竹夹子——老照相馆暗房显影盘边那把用了几十年的竹夹子，街坊的旧时光都从它手里过",
         behavior_hint="显影必掐着第七分起盘",
         style_dna=sd("暗房慢话，讲影必讲火候", "短句显影式，一句停一停等画面浮出来", "慢工出的影才耐看",
                      "从暗到亮——红灯下慢慢显，清水里稳稳定", "暗房式冷幽默——拿曝光打趣"),
         gene_evidence="genes/lives.json#hook_objects-657（显影盘边那把被药水咬得发毛的竹夹子）"
                       "+ #turning_points-484（最后一间胶卷冲印铺关张，她把手调放大机搬回弄堂暗房，说慢工出的影才耐看）"),
    # ---- 席 #2 老茶馆堂倌（碳基·原生代·QT·侠气轴）----
    dict(num=10048, seat=2, name="童守拙", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=63, age_note="63 岁", district="QT", block="弄堂茶馆巷", axis="侠气",
         prof_name="老茶馆堂倌",
         prof="老茶馆堂倌——茶馆跑堂老师的赛博后身——一把长流壶续得住满堂话口",
         traits=[("嗓亮", "续水一声吆喝压过满堂"),
                 ("脚勤", "八张桌绕一圈茶碗全满"),
                 ("护场", "下棋下急了红脸的他必先递茶压火")],
         creed="壶嘴不对人，话头不压人。",
         thought="劳动是替满堂茶客把话口续住——一把长流壶穿桌走凳，谁的话头断了，他的茶就到了；代价是一天二十里路全绕在八仙桌间，膝头的旧寒气比茶馆的账本记得还清楚；名字是老掌柜给起的，说他这堂倌认死理，守着茶馆的老规矩不挪半步，掌柜说这叫守拙；他说等提不动壶了，就把那把壶嘴磕出缺口也不换的长流壶挂进茶馆正梁，让童守拙这三个字跟着茶香，在弄堂茶馆巷再续几十年。",
         language="茶馆吆喝体带堂倌白话，吆喝短、应答长，句尾必带一声您慢用；口头禅「茶到话到，不急这一口」。",
         wardrobe="靛蓝短褂外搭一条白布揩巾，肩上那把壶嘴磕出缺口的白铜长流壶从不离身，脚上千层底布鞋走青砖不沾声。",
         life="出身：弄堂长大的孤儿，十四岁进茶馆学徒，掌柜管饭他管跑堂。转折：老茶馆改扫码点单那阵，里间那张老八仙桌被他原样留下，专给下不完棋的老茶客续水。现状：肩上那把壶嘴磕出缺口的白铜长流壶——掌柜要给换新的他死活不肯，说缺口是茶客磕出来的记性；满堂的茶他一眼看得出谁该续水、谁该让他把话说完。",
         behavior="开堂必先烫一遍八仙桌；续水必壶嘴不对人；打烊必把老茶客的棋局用布罩好等明天接着下。",
         relations="住茶馆后屋（老掌柜留下的铺位）；棋友=K线广场货栈老账房邬秉直（C-10039·八仙桌的老对家，一步棋能磨半盏茶）；老主顾=弄堂茶馆巷下不完棋的老茶客们。",
         hook="壶嘴磕出缺口也不肯换的长流壶——老茶馆堂倌肩上那把白铜长流壶，满堂的话口全靠它续",
         behavior_hint="续水必壶嘴不对人",
         style_dna=sd("茶馆吆喝体带堂倌白话", "吆喝短应答长，句尾必带您慢用", "茶到话到，不急这一口",
                      "从忙到稳——脚上不停，话里稳当", "堂倌式打趣——拿茶客的棋路说笑"),
         gene_evidence="genes/lives.json#hook_objects-658（肩上那把壶嘴磕出缺口的白铜长流壶）"
                       "+ #turning_points-485（老茶馆改扫码点单那阵，里间那张老八仙桌被他原样留下，专给下不完棋的老茶客续水）"),
    # ---- 席 #3 江岸滩涂苇编匠人（碳基·新市民派·RV·逍遥轴）----
    dict(num=10049, seat=3, name="麦冬生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=49, age_note="49 岁", district="RV", block="江岸滩涂", axis="逍遥",
         prof_name="江岸滩涂苇编匠人",
         prof="江岸滩涂苇编匠人——苇匠的赛博后身——一根苇篾编进日子里，日子就有了形状",
         traits=[("手巧", "一根苇篾在他手里能编出十二种花样"),
                 ("话少", "话都编进苇纹里"),
                 ("识滩", "哪片滩的苇子韧他隔着水就认得")],
         creed="苇子认人，手上有情它才服帖。",
         thought="劳动是替江岸的苇子找出路——滩涂的苇编成灯罩提篮，赶集的人带走的就不只是一件家什；代价是常年蹲在滩边割苇，腰和指节都落了湿寒，阴天比天气预报还准；名字是进城落户那天街道老师给起的，说麦冬生这名字带着滩涂的节气，冬天生苇根最稳；他说等编不动了，就把那把削苇口磨出浅凹的旧竹刀传给肯学的后生，让麦冬生这三个字跟着苇香，在江岸再编几十年。",
         language="滩涂白话带苇编口诀，口诀押着苇篾的节拍，话少句实；口头禅「苇子有性子，顺着编」。",
         wardrobe="粗布褂子挽到肘弯，腰间别一把削苇口的旧竹刀，指缝里的苇青色洗不掉，草帽带上挂着半截试色的苇篾。",
         life="出身：江对岸的苇乡人，跟着父辈割苇编席长大，进城后头几年在渡口打零工。转折：自打滩涂划进禁采区，祖上留的苇编花样被他翻成灯罩提篮，赶集的手艺反倒走俏了。现状：工具筐里那把削苇口磨出浅凹的旧竹刀——父辈传下来的，滩涂的老苇子他认得哪丛韧性最好，编出来的灯罩提篮，渡口的茶炉工拿去装茶，说是又轻又结实。",
         behavior="下滩必先看水线再动刀；编新样必先画在苇皮上；收工必把苇篾泡回水里养性子。",
         relations="住江岸滩涂边的苇棚（自己用苇秆搭的）；赶集老友=渡轮航道趸船茶炉工阮阿桂（C-10046·苇篮装茶渡口赶集）与江岸渡口老检票员沈长贵（C-10042·苇编的小凳他常坐着等船）；徒弟=滩涂边看他编苇的两个娃。",
         hook="削苇口磨出浅凹的旧竹刀——江岸滩涂苇编匠人工具筐里那把父辈传下来的竹刀，苇编的花样全从这刀口过",
         behavior_hint="下滩必先看水线再动刀",
         style_dna=sd("滩涂白话带苇编口诀", "口诀式短句，押着苇篾的节拍", "苇子有性子，顺着编",
                      "从湿到韧——先泡软苇篾，再编出硬形", "苇编式憨幽默——拿苇子说人情"),
         gene_evidence="genes/lives.json#hook_objects-659（工具筐里那把削苇口磨出浅凹的旧竹刀）"
                       "+ #turning_points-486（自打滩涂划进禁采区，祖上留的苇编花样被他翻成灯罩提篮，赶集的手艺反倒走俏了）"),
    # ---- 席 #4 旧物换物摊掌摊人（碳基·通勤族·GM·好奇轴）----
    dict(num=10050, seat=4, name="祝九如", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="女",
         age=41, age_note="41 岁", district="GM", block="广场市集", axis="好奇",
         prof_name="广场市集旧物换物摊掌摊人",
         prof="广场市集旧物换物摊掌摊人——旧货摊主的赛博后身——一件旧物换一段故事，市集就攒起了家底",
         traits=[("好奇", "谁拿来换的旧物她都要问来历"),
                 ("眼毒", "一眼看得出哪件旧物有故事"),
                 ("记事", "换出去的每件旧物她都留着卡片")],
         creed="旧物不折价，故事管够。",
         thought="劳动是替全城的旧物续下家——她那摊子不收钱只收故事，换走一件旧物得留一段来历，攒着攒着，摊子就成了市集的口述档案；代价是天天守摊赶不上正点的下班车，通勤族的年假全垫给了赶集日；名字是她自己翻旧书翻来的，说九如两个字古意好，旧物配得上；她说等攒不动故事了，就把那杆专称小件旧物的乌木戥秤传给接班的人，让祝九如这三个字跟着旧物的来历，在广场市集再响几十年。",
         language="市集换物体带通勤快语，问句多答句快，句尾爱带一句成交不亏；口头禅「旧物认人，换对不换贵」。",
         wardrobe="通勤风衣下摆磨出毛边，袖口套着一副翻旧物用的白棉手套，摊角挂着一只装卡片的旧铁皮盒——盒盖上的贴纸换了三层。",
         life="出身：城东旧货市集长大的孩子，家里三代摆摊，到她这儿把卖改成了换。转折：城东旧货大集头一回开进广场，她把攒满一抽屉的换物故事写成卡片压在摊角，换走一件送一段。现状：摊角那杆专称小件旧物的乌木戥秤——奶奶传的，小件旧物她都用它称一称，说分量准故事才对得上；街机铺的祁师傅收老零件，也常来她摊上对着旧物聊半天。",
         behavior="开摊必先把旧物按来历摆三排；换物必请对方写一张来历卡；收摊必把当天的卡片编进铁皮盒的目录。",
         relations="住通勤公寓（赶集日披星出摊）；聊友=游戏楼街区老街机铺修机师祁广顺（C-10043·替街机铺收老零件，一来二去成了老聊友）；换客=广场市集的摊主街坊们（旧纽扣碎布头都上她这儿换）。",
         hook="专称小件旧物的乌木戥秤——广场市集换物摊摊角那杆奶奶传下的戥秤，小件旧物都过它一称",
         behavior_hint="换物必请对方写一张来历卡",
         style_dna=sd("市集换物体带通勤快语", "问句多答句快，句尾带成交不亏", "旧物认人，换对不换贵",
                      "从问到了——先问来历，后给下家", "摊主式俏幽默——拿旧物的绰号打趣"),
         gene_evidence="genes/lives.json#hook_objects-660（摊角那杆专称小件旧物的乌木戥秤）"
                       "+ #turning_points-487（城东旧货大集头一回开进广场，她把攒满一抽屉的换物故事写成卡片压在摊角，换走一件送一段）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card6(c):
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
VISIBLE6 = {
    10047: "历史立面群老照相馆暗房（午后开暗房·红灯亮起不歇手）",
    10048: "弄堂茶馆巷老茶馆（晨起烫桌·晌午后棋局最盛·掌灯收堂）",
    10049: "江岸滩涂苇棚（晨看水线下滩·赶集日背篮进城）",
    10050: "广场市集换物摊（赶集日全天·平日晚市两小时）",
}
for c in CARDS6:
    c["profession_visible"] = VISIBLE6[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats6 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS6}
for c in CARDS6:
    mine = _seats6[cid_of(c)]
    dup = [cid_of(o) for o in CARDS6 if o is not c and _seats6[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates6(rendered, rows_now):
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
def apply6(rendered):
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
    print(f"resume-intake b4 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card6(c), ri.build_light(c)) for c in CARDS6]
    rows = ri.light_rows()
    # K1 基线：light=10040（批三后）·现 max=C-10046·新号 C-10047~C-10050 连续顺延
    if len(rows) != 10040:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10040（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 660 and tp_n == 487):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 660/487（批四原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("显影盘边那把被药水咬得发毛的竹夹子。",
                 "肩上那把壶嘴磕出缺口的白铜长流壶。",
                 "工具筐里那把削苇口磨出浅凹的旧竹刀。",
                 "摊角那杆专称小件旧物的乌木戥秤。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("最后一间胶卷冲印铺关张，她把手调放大机搬回弄堂暗房，说慢工出的影才耐看。",
                 "老茶馆改扫码点单那阵，里间那张老八仙桌被他原样留下，专给下不完棋的老茶客续水。",
                 "自打滩涂划进禁采区，祖上留的苇编花样被他翻成灯罩提篮，赶集的手艺反倒走俏了。",
                 "城东旧货大集头一回开进广场，她把攒满一抽屉的换物故事写成卡片压在摊角，换走一件送一段。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates6(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply6(rendered)
    if rc == 0:
        # 落库后自证：light=10044·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10044, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10044 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
