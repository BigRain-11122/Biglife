#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批五 intake —— 4 席碳源居民 C-10051~C-10054（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~6
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4 全门闸走满实证）。本批=量产第三批·
批五 4 席（邝铁砧/桑银针/温开阳/蒲苇航·R1753 席位方案定谳+原料 8/8 落库就绪·qa/gene-round-R1753.log）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-661/662/663/664+#turning_points-488/489/490/491
·本批实锚全在库·hook_objects 总数 664/turning_points 总数 491 复读核对）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10044 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批五批日（CEO 解禁令当日滚动批）
BATCH = "复产批五"
MAX_ID = 10050                         # 现存最大号（K1 连续顺延上界=批四尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS7 = [
    # ---- 席 #1 老单车铺修车匠（碳基·原生代·OR·侠气轴）----
    dict(num=10051, seat=1, name="邝铁砧", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="OR", block="机器站巷口", axis="侠气",
         prof_name="老单车铺修车匠",
         prof="老单车铺修车匠——补胎匠的赛博后身——一把小锤敲正车圈，满街的旧车就有路走",
         traits=[("手稳", "车圈在他手里敲一圈不差半分音"),
                 ("义气", "半路抛锚的活儿他随叫随到"),
                 ("惜物", "报废的旧零件也要擦净归置")],
         creed="车正不怕路斜。",
         thought="劳动是替满街的旧单车守一条正路——补胎换条敲车圈，谁的车在半路歪了轮，推到他摊上就能重新上路；代价是指节被车条敲得变了形，阴雨天比街口的信号灯还先报信；名字是老车铺师傅给起的，说铁砧压得住车圈，他这辈子也压得住这摊手艺；他说等敲不动了，就把那把敲惯车圈的鸭嘴小锤挂进车铺门楣，让邝铁砧这三个字跟着车铃声，在机器站巷口再响几十年。",
         language="巷口快话带修车行话，句短声亮，答话不绕弯，句尾爱带一句推来我瞧；口头禅「车正不怕路斜」。",
         wardrobe="洗得发白的工装外罩皮围裙，围裙口袋里插着撬胎棒，指节上的旧茧一层压一层。",
         life="出身：机器站边长大的孩子，十六岁进老单车铺学徒，师傅教的第一课是敲车圈听音。转折：满街换上新式电车以后，补胎换条这桩笨功夫在他手里反倒成了稀罕活，老街坊的旧车宁可推三条街也要来找他。现状：修车摊里那把敲惯车圈的鸭嘴小锤——师傅传的，车圈正不正他闭眼都听得出；电车公司的检修工下班路过，也爱把自家那台旧车推来让他掌掌眼。",
         behavior="开摊必先把车圈校具摆上台；补胎必先过水盆找眼；收摊必把当天的旧内胎补好挂墙，一条不糟蹋。",
         relations="住机器站宿舍边的老车铺阁楼（师傅留下的）；同区老友=机器站宿舍的铆师傅（C-10022·一个铆钢梁一个敲车圈，机器站巷口的老搭档）；老主顾=满街舍不得换新车的老街坊们。",
         hook="修车摊里那把敲惯车圈的鸭嘴小锤——老单车铺修车匠的师传小锤，满街旧车的正轮全从它底下过",
         behavior_hint="补胎必先过水盆找眼",
         style_dna=sd("巷口快话带修车行话", "句短声亮，答话不绕弯", "车正不怕路斜",
                      "从响到稳——锤声先响，话头后稳", "老师傅式憨幽默——拿电车打趣旧车"),
         gene_evidence="genes/lives.json#hook_objects-661（修车摊里那把敲惯车圈的鸭嘴小锤。）"
                       "+ #turning_points-488（满街换上新式电车以后，补胎换条这桩笨功夫在他手里反倒成了稀罕活。）"),
    # ---- 席 #2 银针铺老打磨师（碳基·弄堂派·MD·安稳轴）----
    dict(num=10052, seat=2, name="桑银针", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=54, age_note="54 岁", district="MD", block="医馆巷", axis="安稳",
         prof_name="医馆巷银针铺老打磨师",
         prof="医馆巷银针铺老打磨师——磨针匠的赛博后身——一枚探针守全套银针的锋，巷子里的病家就睡得稳",
         traits=[("手细", "一枚探针在她指间能磨出镜面"),
                 ("心静", "磨针的活一坐就是半天不挪"),
                 ("守旧", "祖辈的针谱她一件不缺盘清")],
         creed="针稳病家稳。",
         thought="劳动是替老医馆的银针守住锋——针磨得亮，大夫下针才有底气，巷子里的病家才敢把身子托过来；代价是常年伏在磨针石前，肩颈僵得比针匣的老银还硬，眼里的红血丝比银丝先上来；名字是祖父给起的，说桑家的针要又稳又韧，银里得掺着忍劲；她说等磨不动了，就把针匣里那枚缠着细银丝柄的老探针传给小徒弟，让桑银针这三个字跟着医馆巷的药香，再稳几十年。",
         language="医馆巷软语带磨针口诀，口诀轻、语速慢，句句像掸灰那样轻；口头禅「针稳病家稳」。",
         wardrobe="素青布褂袖口束得整齐，指间常年一枚细银丝柄的探针，围裙上沾着磨针石的细灰。",
         life="出身：医馆巷银针世家，祖父那辈起就给老医馆供针，她十岁起坐在磨针石边学手。转折：老医馆并进联合诊室那年，她把祖辈留下的整套银针一件件盘清，照旧天天磨一轮，巷里的大夫认她这一手。现状：针匣里那枚缠着细银丝柄的老探针——祖母传的，银针有没有失锋，它一探就知道；同巷的老药师桂存仁隔着巷口打招呼，说有她在，这巷子的针就乱不了。",
         behavior="开铺必先净手再开针匣；磨针必先看天光定角度；收针必按针谱归位，一件对一格。",
         relations="住医馆巷银针铺后屋（祖上传的铺面）；同巷老友=医馆巷老药师桂存仁（C-10045·一个供药一个供针，医馆巷的两味老底子）；主顾=联合诊室里认她银针的大夫们。",
         hook="针匣里那枚缠着细银丝柄的老探针——医馆巷银针铺的祖传探针，全套银针的锋钝全凭它一探",
         behavior_hint="磨针必先看天光定角度",
         style_dna=sd("医馆巷软语带磨针口诀", "口诀轻轻答，语速慢慢收", "针稳病家稳",
                      "从细到净——先掸灰，后见亮", "磨针式静幽默——拿针尖的脾气说笑"),
         gene_evidence="genes/lives.json#hook_objects-662（针匣里那枚缠着细银丝柄的老探针。）"
                       "+ #turning_points-489（老医馆并进联合诊室那年，她把祖辈留下的整套银针一件件盘清，照旧天天磨一轮。）"),
    # ---- 席 #3 老霓虹灯匠（碳基·通勤族·NS·求新轴）----
    dict(num=10053, seat=3, name="温开阳", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="男",
         age=46, age_note="46 岁", district="NS", block="白玉兰塔区", axis="求新",
         prof_name="白玉兰塔区老霓虹灯匠",
         prof="白玉兰塔区老霓虹灯匠——弯管灯匠的赛博后身——一根玻璃管弯出手写的光，半条街的招牌就认这口气",
         traits=[("手巧", "玻璃管在他手里弯出整条街的字"),
                 ("眼毒", "灭掉的灯管他一眼看出病在哪头"),
                 ("胆新", "新灯样他敢头一个试")],
         creed="灯亮着，街就没睡。",
         thought="劳动是替塔区的夜留住手写的光——电子屏再快，弯管吹出来的字带着手的温度，半条街的招牌认的就是这口气；代价是常年在灯架和工坊两头跑，通勤族的月票磨成了毛边，指腹被火头燎出的茧一层叠一层；名字是灯匠行的老师傅给起的，说温家的火头不烈却透，开阳照着夜行的人；他说等弯不动玻璃了，就把工具袋里那支试霓虹的老氖泡电笔送进塔区的陈列窗，让温开阳这三个字跟着霓虹，在白玉兰塔区再亮几十年。",
         language="灯匠行话带通勤快语，报活先报火候，句尾爱带一句今晚准亮；口头禅「灯亮着，街就没睡」。",
         wardrobe="工装马甲口袋里插着氖泡电笔，帆布工具袋磨白了边，袖口有火头燎出的小焦痕。",
         life="出身：塔区灯匠世家的独苗，十八岁随父上灯架，学的第一课是对火头。转折：塔区整面换上电子屏的那场翻新里，弯管吹玻璃的功夫他偏留了一手，夜里照样点亮半条街——老字号的招牌还是认他这口气手弯的光。现状：工具袋里那支试霓虹的老氖泡电笔——父亲传的，灯管灭了他往支架上一搭就知道病在哪头；电台导播间退下来的凌素芬夜里散步路过，说塔区的天际线还是得有他这几笔手写的光。",
         behavior="上架必先三查火头；弯管必先在图上走一遍气路；交工必守到掌灯头一刻看亮。",
         relations="住通勤公寓（工坊与灯架两头跑）；同塔区老友=白玉兰塔区老提词人凌素芬（C-10041·一个管字上屏一个管字亮起，塔区夜色的两位守字人）；主顾=塔区认手弯霓虹的老字号们。",
         hook="工具袋里那支试霓虹的老氖泡电笔——老霓虹灯匠袋里的师传电笔，半条街的病灯全凭它一搭断症",
         behavior_hint="交工必守到掌灯头一刻看亮",
         style_dna=sd("灯匠行话带通勤快语", "报活先报火候，句尾必兑现", "灯亮着，街就没睡",
                      "从暗到亮——先找病头，后交亮字", "灯匠式暖幽默——拿电子屏打趣手艺"),
         gene_evidence="genes/lives.json#hook_objects-663（工具袋里那支试霓虹的老氖泡电笔。）"
                       "+ #turning_points-490（塔区整面换上电子屏的那场翻新里，弯管吹玻璃的功夫他偏留了一手，夜里照样点亮半条街。）"),
    # ---- 席 #4 糖画老手艺人（碳基·新市民派·QT·烟火轴）----
    dict(num=10054, seat=4, name="蒲苇航", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=39, age_note="39 岁", district="QT", block="K线广场", axis="烟火",
         prof_name="K线广场糖画老手艺人",
         prof="K线广场糖画老手艺人——糖画艺人的赛博后身——一勺糖稀转出十二生肖，广场的日子就有口甜",
         traits=[("手快", "一勺糖稀三笔出一只虎头"),
                 ("会看", "广场的行情口他听两句就懂三分"),
                 ("热场", "摊子前围的人他总能逗住")],
         creed="糖要趁热，日子要趁甜。",
         thought="劳动是替广场攒一口甜——行情屏上的数字起起落落，他把十二生肖照着盘口重排，转出一勺勺看得见的盼头，排队的孩子和大人都当讨个彩；代价是常年守着糖锅，手腕被糖稀燎出串小泡，赶集日一站就是一整天；名字是进城落户时自己留的，说蒲苇看着轻，风里偏偏最韧，航是盼着日子有去处；他说等转不动糖了，就把那口熬糖稀的小紫铜吊锅传给肯学的娃，让蒲苇航这三个字跟着糖香，在K线广场再转几十年。",
         language="广场吆喝带糖画口诀，口诀顺着转勺的圈，句尾爱带一句转个好彩头；口头禅「糖要趁热，日子要趁甜」。",
         wardrobe="碎花罩衫外系一条厚布围裙，手腕缠着防烫的旧布条，摊角木匣里码着备用的竹签。",
         life="出身：南边糖画世家的后生，跟着舅舅走街串巷学的手艺，进城头两年在夜市摆摊。转折：行情屏搬进广场以后，糖画的十二生肖被他照着盘口重新排过一轮，转糖的手一天没歇——涨的生肖排在头位，广场的看盘人转糖当讨彩。现状：糖画摊边那口熬糖稀的小紫铜吊锅——舅舅给的，糖稀老嫩他看一眼锅边的挂霜就知道；K线广场的老账房邬秉直收摊路过，总爱买一支慢转的龙，说买的不只是甜，是转糖那一会儿的定心。",
         behavior="开摊必先熬一锅试稀定火候；转糖必先报一句生肖彩头；收摊必把铜锅擦净上油，锅底不许留糖疤。",
         relations="住广场边的新市民公寓（赶集日披星出摊）；同广场老友=K线广场货栈老账房邬秉直（C-10039·收摊必来转一支慢龙的老主顾）；熟客=广场上看盘口顺便讨彩头的街坊们。",
         hook="糖画摊边那口熬糖稀的小紫铜吊锅——K线广场糖画摊的舅舅传家吊锅，一锅糖稀的火候全在锅边挂霜里",
         behavior_hint="转糖必先报一句生肖彩头",
         style_dna=sd("广场吆喝带糖画口诀", "口诀顺着转勺的圈走", "糖要趁热，日子要趁甜",
                      "从热到甜——先定火候，后转彩头", "糖画式甜幽默——拿行情打趣生肖"),
         gene_evidence="genes/lives.json#hook_objects-664（糖画摊边那口熬糖稀的小紫铜吊锅。）"
                       "+ #turning_points-491（行情屏搬进广场以后，糖画的十二生肖被他照着盘口重新排过一轮，转糖的手一天没歇。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card7(c):
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
VISIBLE7 = {
    10051: "机器站巷口修车摊（清晨出摊·晌午补胎最忙·掌灯收摊）",
    10052: "医馆巷银针铺（晨起磨针·午后随堂坐诊·掌灯盘针）",
    10053: "白玉兰塔区霓虹工坊（通勤日晚上工·翻新季整月驻场）",
    10054: "K线广场糖画摊（赶集日全天·平日晚市两小时）",
}
for c in CARDS7:
    c["profession_visible"] = VISIBLE7[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats7 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS7}
for c in CARDS7:
    mine = _seats7[cid_of(c)]
    dup = [cid_of(o) for o in CARDS7 if o is not c and _seats7[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates7(rendered, rows_now):
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
def apply7(rendered):
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
    print(f"resume-intake b5 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card7(c), ri.build_light(c)) for c in CARDS7]
    rows = ri.light_rows()
    # K1 基线：light=10044（批四后）·现 max=C-10050·新号 C-10051~C-10054 连续顺延
    if len(rows) != 10044:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10044（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 664 and tp_n == 491):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 664/491（批五原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("修车摊里那把敲惯车圈的鸭嘴小锤。",
                 "针匣里那枚缠着细银丝柄的老探针。",
                 "工具袋里那支试霓虹的老氖泡电笔。",
                 "糖画摊边那口熬糖稀的小紫铜吊锅。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("满街换上新式电车以后，补胎换条这桩笨功夫在他手里反倒成了稀罕活。",
                 "老医馆并进联合诊室那年，她把祖辈留下的整套银针一件件盘清，照旧天天磨一轮。",
                 "塔区整面换上电子屏的那场翻新里，弯管吹玻璃的功夫他偏留了一手，夜里照样点亮半条街。",
                 "行情屏搬进广场以后，糖画的十二生肖被他照着盘口重新排过一轮，转糖的手一天没歇。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates7(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply7(rendered)
    if rc == 0:
        # 落库后自证：light=10048·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10048, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10048 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
