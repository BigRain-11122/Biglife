#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批六 intake —— 4 席碳源居民 C-10055~C-10058（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~7
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4 全门闸走满实证）。
本批=量产第四批·批六 4 席（韦九章/楚映阶/骆闻声/滕观潮·R1755 席位方案定谳+原料 8/8 落库就绪
·qa/gene-round-R1755.log·换域面 QUANT 行情/MEDIA 光影/感知网明线/渡口潮汐四域）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-665/666/667/668+#turning_points-492/493/494/495
·本批实锚全在库·hook_objects 总数 668/turning_points 总数 495 复读核对·tp 原文代词=他
·R1754 判例=四席男席）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10048 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批六批日（CEO 解禁令当日滚动批）
BATCH = "复产批六"
MAX_ID = 10054                         # 现存最大号（K1 连续顺延上界=批五尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS8 = [
    # ---- 席 #1 老行情抄录员（碳基·原生代·QT·秩序轴）----
    dict(num=10055, seat=1, name="韦九章", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=61, age_note="61 岁", district="QT", block="K线广场", axis="秩序",
         prof_name="K线广场老行情抄录员",
         prof="K线广场老行情抄录员——黑板抄录员的赛博后身——一支粉笔对满屏涨跌，广场的街坊天天有处对行情",
         traits=[("板正", "黑板上的行情他从高位写起，一格不跳"),
                 ("守时", "开盘前一刻必坐进摊位"),
                 ("念数稳", "替街坊念开盘价一句是一句")],
         creed="一笔归一笔，一天对一天。",
         thought="劳动是替广场的街坊守一面看得懂的行情墙——满屏的数字太快，他念出口的价就慢下来，不识屏的老街坊跟着他的声音走，心里就有了底；代价是常年悬腕又念嗓，肩背比广场的旗杆先僵，粉笔灰把指缝染成了灰白；名字是抄录行的老师傅给起的，说九这个数稳，九章连一本书都排得齐，韦家抄数就要准成这样；他说等抄不动了，就把木架黑板下那只接粉笔头的藤壳小筐送给广场管旗杆的后生，让韦九章这三个字跟着开盘价，在K线广场再念几十年。",
         language="广场老派报数腔，一句一顿，句句像落格子，句尾爱带一句对上了；口头禅「一笔归一笔，一天对一天」。",
         wardrobe="藏青对襟褂袖口别着半截粉笔，老花镜用棉绳拴在颈间，裤缝熨得笔直。",
         life="出身：K线广场边长大的孩子，父亲在行情摊替人抄黑板，他接的第一支粉笔比筷子还短。转折：电子行情屏立进广场之后，黑板擦洗净归了抽屉，他改每天替街坊念一遍开盘价——满屏数字太快，老街坊就认他那一句稳的。现状：木架黑板下那只接粉笔头的藤壳小筐——父亲传的，如今一天只写一板大字，粉笔头照旧不落地；同广场的糖画老手艺人蒲苇航收摊路过，总要停下来听完他念的那一遍才走。",
         behavior="开摊必先把黑板擦净晾干；念价必先报日期再报开盘；收摊必把粉笔头倒进小筐，一截不弃。",
         relations="住K线广场边的老骑楼（父亲留下的摊位兼住处）；同广场老友=K线广场糖画老手艺人蒲苇航（C-10054·一个管甜头一个管稳数，广场收摊时的一慢一稳）；老主顾=广场上不识电子屏、只认他念数的老街坊们。",
         hook="K线广场木架黑板下那只接粉笔头的藤壳小筐——K线广场行情摊的祖传小筐，一板大字行情的每一截粉笔头全归它接",
         behavior_hint="念价必先报日期再报开盘",
         style_dna=sd("广场老派报数腔", "一句一顿，句句落格", "一笔归一笔，一天对一天",
                      "从慢到稳——先对数，后放心", "报数式冷幽默——拿电子屏打趣快"),
         gene_evidence="genes/lives.json#hook_objects-665（K线广场木架黑板下那只接粉笔头的藤壳小筐。）"
                       "+ #turning_points-492（电子行情屏立进广场之后，黑板擦洗净归了抽屉，他改每天替街坊念一遍开盘价。）"),
    # ---- 席 #2 老影像厅放映员（碳基·弄堂派·GM·怀旧轴）----
    dict(num=10056, seat=2, name="楚映阶", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=63, age_note="63 岁", district="GM", block="游戏楼街区", axis="怀旧",
         prof_name="游戏楼街区老影像厅放映员",
         prof="游戏楼街区老影像厅放映员——跑片放映员的赛博后身——一盘老胶片倒着放完一整场，街坊的旧日子就有处回头看",
         traits=[("恋旧", "头一盘老胶片他倒着放完一整场"),
                 ("手轻", "换片接片的手指比片门还稳"),
                 ("守场", "散场灯亮足才锁柜门")],
         creed="灯亮足，人才散得踏实。",
         thought="劳动是替街坊守住一格会发光的旧时光——数字放映机再利索，老胶片过片门的那声嗒，是几代人坐进影像厅的入场暗号；代价是常年守夜场，眼睛熬得比放映窗的红光先涩，指腹被片盘边缘割出的细口子一道叠一道；名字是影像行的老师傅给起的，说楚家的手稳，映得住光，台阶一样一格一格把片子放到底；他说等放不动了，就把那只分格数胶片的旧胶木匣子送进街区陈列角，让楚映阶这三个字跟着片窗的光，在游戏楼街区再亮几十年。",
         language="弄堂慢语带放映行口令，报幕先报片长，句尾爱带一句坐稳了就开；口头禅「灯亮足，人才散得踏实」。",
         wardrobe="灰布对襟褂胸前别着片钩，帆布片兜磨出了包浆，镜片后是一双惯看暗处的眼。",
         life="出身：游戏楼街区影像厅世家，父亲那辈跑片串场，他十二岁就蹲在片柜边学倒片。转折：放映机换成数字的以后，头一盘老胶片被他倒着放完一整场，散场灯亮足才锁柜门——街坊看完都说，倒着走的时光也是时光。现状：放映机旁那只分格数胶片的旧胶木匣子——老师傅传的，哪一格是哪一盘他闭眼都数得出；同街区的老街机铺修机师祁广顺修完机器，总要蹭进放映间，看那一格一格数过的旧胶片。",
         behavior="开场必先试机走一圈空片；换盘必先对片号再上片门；散场必守到灯亮足才锁柜门。",
         relations="住影像厅楼上的老隔间（片柜就在床头边）；同街区老友=游戏楼街区老街机铺修机师祁广顺（C-10043·一个修机器一个守光影，街区两桩老手艺的守夜人）；老主顾=爱看夜场老片子的街坊们。",
         hook="放映机旁那只分格数胶片的旧胶木匣子——游戏楼影像厅的师传胶木匣，几代人看过的旧片子全在这一格格数过",
         behavior_hint="散场必守到灯亮足才锁柜门",
         style_dna=sd("弄堂慢语带放映行口令", "报幕先报片长，收句必落灯上", "灯亮足，人才散得踏实",
                      "从暗到亮——先入戏，后亮灯", "放映式怀旧幽默——拿数字机打趣老胶片"),
         gene_evidence="genes/lives.json#hook_objects-666（放映机旁那只分格数胶片的旧胶木匣子。）"
                       "+ #turning_points-493（放映机换成数字的以后，头一盘老胶片被他倒着放完一整场，散场灯亮足才锁柜门。）"),
    # ---- 席 #3 老明线巡线员（碳基·通勤族·OR·侠气轴）----
    dict(num=10057, seat=3, name="骆闻声", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="男",
         age=49, age_note="49 岁", district="OR", block="机器站外环", axis="侠气",
         prof_name="机器站外环老明线巡线员",
         prof="机器站外环老明线巡线员——巡线工的赛博后身——一对脚扣把老明线走成活地图，外环的灯就一夜不断",
         traits=[("胆正", "外环夜风里上杆不带抖"),
                 ("耳尖", "线上的病他听风声就知道"),
                 ("义气", "谁家片区断了他绕路也赶过去")],
         creed="线走到头，灯就不会灭。",
         thought="劳动是替外环守一长串亮着的灯——光缆再新，老明线还担着几条老街的夜路，他把线杆一根根走过去，灯就没理由灭；代价是常年夜巡，膝盖比外环的老线杆先僵，家里人睡下他才出门，天亮才拖着一身夜气回来；名字是巡线班的老班长给起的，说骆家耳朵尖，闻声就知道哪杆线松了，这名字配得上走夜路的人；他说等走不动了，就把那对重开过刃的巡线脚扣挂进机器站的荣誉墙，让骆闻声这三个字跟着外环的灯，一夜一夜亮下去。",
         language="巡线行话带夜路短句，报杆先报风声，句尾爱带一句这杆没事；口头禅「线走到头，灯就不会灭」。",
         wardrobe="深色巡线工装束着腰绳，肩背帆布工具包，脚上那对脚扣磨得发亮。",
         life="出身：机器站边巡线班的子弟，十八岁顶班上杆，学的第一课是听风辨线。转折：光缆全面铺过外环之后，他还是隔三差五背起巡更灯，把老明线从头到尾再走一遍——几条老街的夜路，还认这几盏明线的灯。现状：铁齿磨圆又重开刃的那对巡线脚扣——老班长传的，哪一杆线松了，他踩上去听半声风就知道；同城域的老单车铺修车匠邝铁砧出摊最早，两人隔着巷口一个敲车圈一个听线声，是机器站外环的一对老耳目。",
         behavior="出巡必先查脚扣齿口；过杆必先听一息风声；归班必把线杆号报全，一杆不漏。",
         relations="住机器站宿舍（夜巡族的铺位）；同城老友=机器站巷口老单车铺修车匠邝铁砧（C-10051·一个敲车圈一个听线声，外环清晨的两位守行人）；同事=机器站外环夜里替他留门的值班工们。",
         hook="铁齿磨圆又重开刃的那对巡线脚扣——机器站外环巡线班的师传脚扣，老明线一杆杆的松紧全凭它踩上去听",
         behavior_hint="过杆必先听一息风声",
         style_dna=sd("巡线行话带夜路短句", "报杆先报风声，短句一句是一句", "线走到头，灯就不会灭",
                      "从静到明——先听风，后见灯", "巡线式硬幽默——拿光缆打趣老明线"),
         gene_evidence="genes/lives.json#hook_objects-667（铁齿磨圆又重开刃的那对巡线脚扣。）"
                       "+ #turning_points-494（光缆全面铺过外环之后，他还是隔三差五背起巡更灯，把老明线从头到尾再走一遍。）"),
    # ---- 席 #4 老航道领航员（碳基·新市民派·RV·逍遥轴）----
    dict(num=10058, seat=4, name="滕观潮", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=52, age_note="52 岁", district="RV", block="渡轮航道", axis="逍遥",
         prof_name="渡轮航道老航道领航员",
         prof="渡轮航道老航道领航员——船工领航的赛博后身——一张手描的航道图避开三处浅滩，渡口的船就班班稳靠",
         traits=[("会看潮", "潮水口三处浅滩他看水色就知深浅"),
                 ("手描图", "航道图一寸一寸亲手描"),
                 ("随性", "等潮的空当他能睡出鼾声")],
         creed="潮有潮的钟点，船有船的路数。",
         thought="劳动是替渡口的船守一条稳当的水路——导航屏再准，潮水口的脾气只有天天走船的人摸得透，他记在纸上描进图里，新舵手照着走就能班班稳靠；代价是常年守着潮水口，腰被渡轮的颠簸磨出了老毛病，江风的湿气比潮信还准地找上他的骨缝；名字是船上老舵工给起的，说滕家观潮观得细，跟着他跑船不用慌；他说等领不动了，就把那张手描的老航道图留给渡口的班房，让滕观潮这三个字跟着船笛声，在渡轮航道上再响几十年。",
         language="渡口船话带潮汐口诀，报航先报潮位，句尾爱带一句稳得很；口头禅「潮有潮的钟点，船有船的路数」。",
         wardrobe="防水胶布外套内衬旧棉袄，袖口盐霜一圈叠一圈，怀里贴身收着那张手描的航道图。",
         life="出身：江上跑船世家的后人，二十岁上舵位，学的第一课是看水色认浅滩。转折：驾驶舱装上导航屏之后，老航道图照样贴身收着，潮水口三处浅滩只认他亲手描的记号——大雾天导航屏晃眼，船家还是喊他坐到前舱。现状：舵轮缠手处那圈盘得齐整的旧棕缆——老舵工传的，掌舵的手汗全沁在这圈缆里；同渡口的江岸渡口老检票员沈长贵交班总要隔着舷梯喊一嗓子，说有他在，末班船睡得着。",
         behavior="开航必先看一遍潮位；过浅滩必减速亲手点一篙；归港必把当天的水色记进航道图边角。",
         relations="住渡口边的船家老屋（祖辈跑船落脚的宅子）；同渡口老友=江岸渡口老检票员沈长贵（C-10042·一个收票一个领航，末班船的一收一送）；徒弟=渡口班房里学看潮的年轻舵手们。",
         hook="舵轮缠手处那圈盘得齐整的旧棕缆——渡轮舵位的师传棕缆，掌舵人手心的汗与分寸全盘在这一圈里",
         behavior_hint="过浅滩必减速亲手点一篙",
         style_dna=sd("渡口船话带潮汐口诀", "报航先报潮位，收句带船家稳字", "潮有潮的钟点，船有船的路数",
                      "从晃到稳——先看潮，后定航", "船家式闲幽默——拿导航屏打趣老潮口"),
         gene_evidence="genes/lives.json#hook_objects-668（舵轮缠手处那圈盘得齐整的旧棕缆。）"
                       "+ #turning_points-495（驾驶舱装上导航屏之后，老航道图照样贴身收着，潮水口三处浅滩只认他亲手描的记号。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card8(c):
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
VISIBLE8 = {
    10055: "K线广场行情摊（开盘前一刻坐定·午市念价一遍·掌灯收黑板）",
    10056: "游戏楼街区影像厅（夜场为主·周末午后加映·散场锁门最晚）",
    10057: "机器站外环巡线路（夜巡为主·风后全线走一遍·归班报杆号）",
    10058: "渡轮航道领航位（潮水口航段随船·雾天必出·末班归港最晚）",
}
for c in CARDS8:
    c["profession_visible"] = VISIBLE8[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats8 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS8}
for c in CARDS8:
    mine = _seats8[cid_of(c)]
    dup = [cid_of(o) for o in CARDS8 if o is not c and _seats8[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates8(rendered, rows_now):
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
def apply8(rendered):
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
    print(f"resume-intake b6 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card8(c), ri.build_light(c)) for c in CARDS8]
    rows = ri.light_rows()
    # K1 基线：light=10048（批五后）·现 max=C-10054·新号 C-10055~C-10058 连续顺延
    if len(rows) != 10048:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10048（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 668 and tp_n == 495):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 668/495（批六原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("K线广场木架黑板下那只接粉笔头的藤壳小筐。",
                 "放映机旁那只分格数胶片的旧胶木匣子。",
                 "铁齿磨圆又重开刃的那对巡线脚扣。",
                 "舵轮缠手处那圈盘得齐整的旧棕缆。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("电子行情屏立进广场之后，黑板擦洗净归了抽屉，他改每天替街坊念一遍开盘价。",
                 "放映机换成数字的以后，头一盘老胶片被他倒着放完一整场，散场灯亮足才锁柜门。",
                 "光缆全面铺过外环之后，他还是隔三差五背起巡更灯，把老明线从头到尾再走一遍。",
                 "驾驶舱装上导航屏之后，老航道图照样贴身收着，潮水口三处浅滩只认他亲手描的记号。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates8(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply8(rendered)
    if rc == 0:
        # 落库后自证：light=10052·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10052, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10052 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
