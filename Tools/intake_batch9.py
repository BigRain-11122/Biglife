#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批七 intake —— 4 席碳源居民 C-10059~C-10062（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~8
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4+R1756 批六 4/4
全门闸走满实证）。
本批=量产第五批·批七 4 席（雷守闸/岑守频/席静波/黎望畴·R1757 席位方案定谳+原料 8/8 落库就绪
·qa/gene-round-R1757.log·换域面 QUANT 算力塔配电/MEDIA 导播台/感知网监听哨/QUANT 回测田垄头四域）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-669/670/671/672+#turning_points-496/497/498/499
·本批实锚全在库·hook_objects 总数 672/turning_points 总数 499 复读核对·tp 原文代词=他
·R1754 判例=四席男席）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10052 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批七批日（CEO 解禁令当日滚动批）
BATCH = "复产批七"
MAX_ID = 10058                         # 现存最大号（K1 连续顺延上界=批六尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS9 = [
    # ---- 席 #1 老配电检修工（碳基·原生代·QT·秩序轴）----
    dict(num=10059, seat=1, name="雷守闸", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=55, age_note="55 岁", district="QT", block="算力塔机房", axis="秩序",
         prof_name="算力塔机房老配电检修工",
         prof="算力塔机房老配电检修工——配电检修工的赛博后身——一双手套摸过全塔的老闸刀，配电间的灯就没黑过一夜",
         traits=[("较真", "闸刀合闸的响声不对他当场重合一遍"),
                 ("守序", "配电间的操作票一张按一张钉齐"),
                 ("手稳", "带电的活他手套不离手")],
         creed="闸响对了，灯才亮得踏实。",
         thought="劳动是替算力塔守一间不出错的配电间——自动巡检报表再全，那声闸刀合上的脆响才是机器没说谎的凭据，他一句句听过去，塔里的灯就稳得住；代价是常年与电为邻，耳朵被闸响磨得比老闸刀还灵，家里人睡觉他听响，天亮才带着一身机油味回来；名字是配电班老师傅给起的，说雷家守闸守得正，电走雷行他都敢拦，这名字配得住看闸的人；他说等退休了，就把配电间里那副磨白了指节的旧绝缘手套交进塔里的老物件柜，让雷守闸这三个字跟着每旬那声闸响，在算力塔再响几十年。",
         language="机房老电工腔带操作票用语，报闸先报回路，句尾爱带一句响对了；口头禅「闸响对了，灯才亮得踏实」。",
         wardrobe="藏蓝电工工装袖口磨得发白，帆布工具包里操作票叠得方正，那副旧绝缘手套常年别在腰后。",
         life="出身：算力塔基建那年进的配电班，师父领着认的第一条回路是塔底的老配电间。转折：机房上了自动巡检以后，配电老闸刀他照样每旬亲手合一遍听响——报表再全，那声脆响才是他心里的底。现状：配电间里那副磨白了指节的旧绝缘手套——师父传的，哪一路闸刀松了，他戴上手套一摸就知道；同城K线广场的老行情抄录员韦九章收摊路过塔下，两人一个念开盘价一个听闸响，是 QT 城里出名的一慢一响。",
         behavior="合闸必先核一遍操作票；巡检必先摸一遍闸壳温度；收工必把当旬的闸响记进值班本，一响不漏。",
         relations="住算力塔塔底配电班宿舍（师父那辈传下的铺位）；同城老友=K线广场老行情抄录员韦九章（C-10055·一个念开盘价一个听闸响，QT 城里的一慢一响）；徒弟=配电班里跟他学合闸听响的年轻检修工们。",
         hook="算力塔配电间里那副磨白了指节的旧绝缘手套——算力塔配电间的师传手套，老闸刀每一回合闸的分寸全在这副掌心里",
         behavior_hint="合闸必先核一遍操作票",
         style_dna=sd("机房老电工腔带操作票用语", "报闸先报回路，短句一字是一钉", "闸响对了，灯才亮得踏实",
                      "从响到明——先听闸，后安心", "检修式冷幽默——拿自动巡检打趣老闸刀"),
         gene_evidence="genes/lives.json#hook_objects-669（算力塔配电间里那副磨白了指节的旧绝缘手套。）"
                       "+ #turning_points-496（机房上了自动巡检以后，配电老闸刀他照样每旬亲手合一遍听响。）"),
    # ---- 席 #2 老切换师（碳基·弄堂派·MD·怀旧轴）----
    dict(num=10060, seat=2, name="岑守频", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=60, age_note="60 岁", district="MD", block="导播台", axis="怀旧",
         prof_name="导播台老切换师",
         prof="导播台老切换师——导播切换员的赛博后身——一路老推子推得比触屏还稳，城市的广播声就不断档",
         traits=[("念旧", "那一路老推子谁劝也不换"),
                 ("手稳", "推子走位差一丝他就重来"),
                 ("带新人", "新来的都得先跟他学三秒静场")],
         creed="推子在手，声音不慌。",
         thought="劳动是替导播台守一路不断的声音——触屏再利索，声音从指腹过推子的那点分量，是新耳朵学不会的分寸，他把这一路守住，城市的早班广播就不迟到；代价是常年在监听位上坐成了一块老钟表，耳朵比闹铃还准，家里饭桌上的热菜总等他把那三秒静场听完才动筷；名字是台里老台长给起的，说岑家的手稳，守得住频率，这名字往台牌一挂就是几十年；他说等推不动了，就把台面下那杆拧惯了旋钮的乌木柄小改锥传给学手稳的新切换师，让岑守频这三个字跟着那一路老推子，在导播台再推几十年。",
         language="导播间调度口令带弄堂慢语，报信号先报一路，句尾爱带一句稳住再走；口头禅「推子在手，声音不慌」。",
         wardrobe="深灰夹克胸前口袋插着记号笔，台前坐得端正，指节上是常年推推子磨出的薄茧。",
         life="出身：导播台边上长大的孩子，父亲那辈就在台里守推子，他十六岁进台学的第一课是不带响推推子。转折：切换台全换成触屏以后，有一路老推子他始终没换，专门教新来的什么叫手稳。现状：导播台台面下那杆拧惯了旋钮的乌木柄小改锥——老师傅传的，哪一路旋钮松了丝，他一杆就拧得回来；同城医馆巷的银针铺老打磨师桑银针关铺路过台门口，总要把他那路没换的老推子看一眼才走。",
         behavior="开播前必先走一遍信号；换路必先听三秒静场；收播必把推子归零再离台。",
         relations="住导播台后巷的老公房（推开窗就望得见台里的信号灯）；同城老友=医馆巷银针铺老打磨师桑银针（C-10052·一个磨针一个稳推子，MD 城里的一细一稳）；徒弟=台里跟他学三秒静场的新切换师们。",
         hook="导播台台面下那杆拧惯了旋钮的乌木柄小改锥——导播台的师传改锥，几代切换师拧过的旋钮全认这杆乌木柄",
         behavior_hint="换路必先听三秒静场",
         style_dna=sd("导播间调度口令带弄堂慢语", "报信号先报一路，收句必落推子上", "推子在手，声音不慌",
                      "从杂到清——先压推子，后出声", "导播式旧忆幽默——拿触屏打趣老推子"),
         gene_evidence="genes/lives.json#hook_objects-670（导播台台面下那杆拧惯了旋钮的乌木柄小改锥。）"
                       "+ #turning_points-497（切换台全换成触屏以后，有一路老推子他始终没换，专门教新来的什么叫手稳。）"),
    # ---- 席 #3 老值机员（碳基·通勤族·OR·安稳轴）----
    dict(num=10061, seat=3, name="席静波", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="男",
         age=47, age_note="47 岁", district="OR", block="监听哨", axis="安稳",
         prof_name="监听哨老值机员",
         prof="监听哨老值机员——值机监听员的赛博后身——一只老动圈耳机贴着耳朵守夜，外环的风吹草动就逃不过那双手",
         traits=[("耐静", "一夜只听底噪也不觉长"),
                 ("心细", "毛边差半格他都要记档"),
                 ("守点", "交班的表针没到人先到")],
         creed="耳朵值机，心里有数。",
         thought="劳动是替外环守一夜一夜的静——数字监听表再密，电流里那一点毛边只有贴过耳朵的耳朵认得出，他把毛边一只只记进档，哨里的夜就睡得安稳；代价是常年与夜班为伴，天亮下班的人流里他永远逆着走，耳机摘下来耳边还嗡着底噪，家里人说话他总让人重复第二遍；名字是哨上老值机长给起的，说席家的耳朵静得住，波里再乱的动静他都听得平，这名字配得上守夜的人；他说等值不动了，就把岗亭里那轴缠剩的旧漆包铜线和那只老动圈耳机一起留给哨上的接班人，让席静波这三个字跟着夜里的底噪，在监听哨再守几十年。",
         language="监听哨夜班行话，报频先报底噪，句尾爱带一句记下了；口头禅「耳朵值机，心里有数」。",
         wardrobe="靛蓝值机服肩头搭着旧毛巾，那只老动圈耳机挂在颈间，夜班表走得分秒不差。",
         life="出身：监听哨建成那年顶的班，师父教的头一课是先听十分钟底噪再上表。转折：监听系统全数字化以后，岗亭里留了只老动圈耳机，他说电流的毛边瞒不过内行。现状：监听哨岗亭里那轴缠剩的旧漆包铜线——师父传的，接线收头的老手艺全在这轴线上；同城机器站外环的老明线巡线员骆闻声夜里过岗亭，隔着窗一个听线声一个听毛边，是外环的一对夜耳目。",
         behavior="接班必先抄一遍频点表；报数必先报底噪再报信号；交班必把毛边记录钉进值机簿。",
         relations="住监听哨值班岗亭后的小隔间（耳机就挂在床头）；同城老友=机器站外环老明线巡线员骆闻声（C-10057·一个听线声一个听毛边，外环夜路上的一对老耳目）；同事=哨上夜里换班的值机员们。",
         hook="监听哨岗亭里那轴缠剩的旧漆包铜线——监听哨的师传铜线，老值机员接过的每一处断头全在这轴上收口",
         behavior_hint="报数必先报底噪再报信号",
         style_dna=sd("监听哨夜班行话", "报频先报底噪，句句贴着表针走", "耳朵值机，心里有数",
                      "从静到稳——先听毛边，后落笔", "值机式干幽默——拿数字监听打趣老耳机"),
         gene_evidence="genes/lives.json#hook_objects-671（监听哨岗亭里那轴缠剩的旧漆包铜线。）"
                       "+ #turning_points-498（监听系统全数字化以后，岗亭里留了只老动圈耳机，他说电流的毛边瞒不过内行。）"),
    # ---- 席 #4 老巡田人（碳基·新市民派·QT·烟火轴）----
    dict(num=10062, seat=4, name="黎望畴", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=58, age_note="58 岁", district="QT", block="回测田", axis="烟火",
         prof_name="回测田老巡田人",
         prof="回测田老巡田人——巡田员的赛博后身——一双脚板把田埂走成活账本，垄里的实情就一句不虚",
         traits=[("勤脚", "田埂一天两遍风雨不缺"),
                 ("眼毒", "苗色差半分他一眼就断"),
                 ("实诚", "报垄情从不掺半句虚")],
         creed="田埂上的事，脚底板说了算。",
         thought="劳动是替回测田守一垄一垄的真收成——无人机拍得再细，土的松紧、苗的火色、垄沟的深浅，全要脚底板踩过去才算数，他走一遍记一遍，田里的账就一句不虚；代价是常年风里来雨里去，裤脚的泥洗了又沾，脚底板的老茧比田埂还厚，家里人一年到头难得同他吃上几顿整饭；名字是田头老把式给起的，说黎家的眼毒，望一眼田畴就知道长势，这名字是田埂上走出来的；他说等走不动了，就把垄头那根量行距的自制老木卡尺挂进田头的守望棚，让黎望畴这三个字跟着一垄一垄的实情，在回测田再走几十年。",
         language="回测田垄头土话带农谚，报垄先报长势，句尾爱带一句看天吃饭不糊弄；口头禅「田埂上的事，脚底板说了算」。",
         wardrobe="洗旧的帆布褂子裤脚沾着垄土，草帽带子换了三回，田头本用塑料布包得严实。",
         life="出身：回测田开垄那年就在田里跑，父辈守的是这片田的第一茬收成。转折：无人机接手巡田以后，旧田埂照旧由他来回走，说地里的实情脚底板最先清楚。现状：回测田垄头那根量行距的自制老木卡尺——家传的，一垄一垄的行距实数全凭它量；同田的回测田老修表铺守钟人侯振声收铺路过垄头，两人一个守钟点一个守节气，是回测田的一双老守时人。",
         behavior="下田必先看一遍天色；巡垄必亲手拔两株草验土；收工必把垄情记进田头本，一垄不落。",
         relations="住回测田田头的守望棚（田在哪家就在哪）；同田老友=回测田老修表铺守钟人侯振声（C-10040·一个守钟点一个守节气，回测田的一双老守时人）；老主顾=靠他报垄情下种的老种植户们。",
         hook="回测田垄头那根量行距的自制老木卡尺——回测田的家传卡尺，每一垄行距的实数全凭这根木尺量出来",
         behavior_hint="巡垄必亲手拔两株草验土",
         style_dna=sd("回测田垄头土话带农谚", "报垄先报长势，一句是一垄", "田埂上的事，脚底板说了算",
                      "从走到知——先下田，后开口", "巡田式土幽默——拿无人机打趣老田埂"),
         gene_evidence="genes/lives.json#hook_objects-672（回测田垄头那根量行距的自制老木卡尺。）"
                       "+ #turning_points-499（无人机接手巡田以后，旧田埂照旧由他来回走，说地里的实情脚底板最先清楚。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card9(c):
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
VISIBLE9 = {
    10059: "算力塔配电间（每旬合闸日必到·夜巡走全回路·收工最晚）",
    10060: "导播台切换位（早晚班连着坐·开播前试信号·收播归零最晚）",
    10061: "监听哨值机岗（夜班为主·底噪十分钟起步·交班表最准）",
    10062: "回测田田埂（清晨巡头遍·傍晚巡二遍·雨天也走垄）",
}
for c in CARDS9:
    c["profession_visible"] = VISIBLE9[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats9 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS9}
for c in CARDS9:
    mine = _seats9[cid_of(c)]
    dup = [cid_of(o) for o in CARDS9 if o is not c and _seats9[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates9(rendered, rows_now):
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
def apply9(rendered):
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
    print(f"resume-intake b7 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card9(c), ri.build_light(c)) for c in CARDS9]
    rows = ri.light_rows()
    # K1 基线：light=10052（批六后）·现 max=C-10058·新号 C-10059~C-10062 连续顺延
    if len(rows) != 10052:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10052（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 672 and tp_n == 499):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 672/499（批七原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("算力塔配电间里那副磨白了指节的旧绝缘手套。",
                 "导播台台面下那杆拧惯了旋钮的乌木柄小改锥。",
                 "监听哨岗亭里那轴缠剩的旧漆包铜线。",
                 "回测田垄头那根量行距的自制老木卡尺。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("机房上了自动巡检以后，配电老闸刀他照样每旬亲手合一遍听响。",
                 "切换台全换成触屏以后，有一路老推子他始终没换，专门教新来的什么叫手稳。",
                 "监听系统全数字化以后，岗亭里留了只老动圈耳机，他说电流的毛边瞒不过内行。",
                 "无人机接手巡田以后，旧田埂照旧由他来回走，说地里的实情脚底板最先清楚。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates9(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply9(rendered)
    if rc == 0:
        # 落库后自证：light=10056·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10056, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10056 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
