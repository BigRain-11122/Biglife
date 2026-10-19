#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批八 intake —— 4 席碳源居民 C-10063~C-10066（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~9
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4+R1756 批六 4/4
+R1758 批七 4/4 全门闸走满实证）。
本批=量产第六批·批八 4 席（晏知秋/平松年/练铁生/曾稳山·R1759 席位方案定谳+原料 8/8 落库就绪
·qa/gene-round-R1759.log·换域面书报亭/裱画案头/白铁摊/剃头担子四域）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-673/674/675/676+#turning_points-500/501/502/503
·本批实锚全在库·hook_objects 总数 676/turning_points 总数 503 复读核对·tp 原文代词=他
·R1754 判例=四席男席）。
批后收口步（R1759 候选单兑现·生产环 72h 自续验收面）: apply 后内嵌「needs face 刷新→
behavior 强制再生→rows 对齐断言」三步——R1758/R1759 behavior 批后滞后缺陷（unchanged-skip
判据不含 light 行数变化）结构性根治，落后=批内零容忍。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10056 卡零触碰；light append-only 追加字节尾；cursor 不插队。
Idempotent: 再跑对一致文件/行 skip（applied=0）。
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

import resident_intake as ri          # 先例族单源：cid_of/build_light/voice_seat/sd/light_rows/LIGHT
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-19"                   # 复产批八批日（CEO 解禁令当日滚动批）
BATCH = "复产批八"
MAX_ID = 10062                         # 现存最大号（K1 连续顺延上界=批七尾席）
POST_LIGHT = 10060                     # 批后 light 行数（批八收口断言基线）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS10 = [
    # ---- 席 #1 老书报亭主（碳基·通勤族·GM·好奇轴）----
    dict(num=10063, seat=1, name="晏知秋", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="男",
         age=52, age_note="52 岁", district="GM", block="八号楼街区", axis="好奇",
         prof_name="八号楼街区老书报亭主",
         prof="八号楼街区老书报亭主——书报亭主的赛博后身——一盏绿罩台灯守着一亭子纸页，城里明天的事今晚就到了他柜上",
         traits=[("好奇", "新到的刊他总要先翻一遍目录"),
                 ("博闻", "哪条街出了新鲜事他都能接上茬"),
                 ("手勤", "过期旧报从不乱扔，整摞装订留底")],
         creed="灯不灭，事就先知道。",
         thought="劳动是替八号楼街区守一亭子先知道的事——手机把新闻递到每个人指尖以后，纸页的口气、油墨的分寸、翻页的响动仍是他柜上一座活的城，他把新到的刊一摞摞码上灯下，街坊明天聊的天今晚就齐了；代价是起早贪黑守着亭子，家里饭桌上他总忍不住把明天的新闻先讲一半，家里人笑他卖报的命操着全城的心；名字是街口老教书先生给起的，说晏家小子眼里有秋色，天下事跟节气一样都能先知一步，这名字压得住一亭子纸页；他说等看不动了，就把亭子里那盏绿罩台灯擦亮了交给接摊的人，让晏知秋这三个字跟着灯下那摞留底的旧报，在八号楼街区再亮几十年。",
         language="书报亭柜台吆喝带刊头腔，报事先报明儿的事，句尾爱带一句灯下见；口头禅「灯不灭，事就先知道」。",
         wardrobe="洗得发白的帆布围裙口袋里插着裁报刀，老花镜的挂绳换了三回，亭子角上码着装订成册的留底旧报。",
         life="出身：八号楼街区通公交那年接的亭子，摊子是他叔传的，教的第一课是过期报纸也是城的家底。转折：报亭挂上玻璃灯箱以后，过期旧报整摞装订成册留了底，他说一城的口气都在纸页里。现状：书报亭里那盏绿玻璃罩子的旧台灯——叔传的，夜里理刊全凭这盏灯照；同城游戏楼街区的老影像厅放映员楚映阶下片路过亭子，一个收旧海报一个留旧报，是 GM 城里的一对纸页守夜人。",
         behavior="开亭必先擦一遍绿罩台灯；新刊到柜必先翻一遍目录；收亭必把当日卖剩的报码回留底摞。",
         relations="住八号楼街区亭子后的小隔间（绿罩台灯就挂在床头）；同城老友=游戏楼街区老影像厅放映员楚映阶（C-10056·一个收旧海报一个留旧报，GM 城里的一对纸页守夜人）；老主顾=靠他先知道城里新鲜事的街坊们。",
         hook="书报亭里那盏绿玻璃罩子的旧台灯——八号楼街区的叔传台灯，一城留底旧报的口气全在这盏灯下理齐",
         behavior_hint="开亭必先擦一遍绿罩台灯",
         style_dna=sd("书报亭柜台吆喝带刊头腔", "报事先报明儿的事，短句像裁报刀", "灯不灭，事就先知道",
                      "从新到熟——先翻目录，后开口", "亭主式打探幽默——拿手机推送打趣纸页"),
         gene_evidence="genes/lives.json#hook_objects-673（书报亭里那盏绿玻璃罩子的旧台灯。）"
                       "+ #turning_points-500（报亭挂上玻璃灯箱以后，过期旧报整摞装订成册留了底，他说一城的口气都在纸页里。）"),
    # ---- 席 #2 老裱画师（碳基·弄堂派·NS·怀旧轴）----
    dict(num=10064, seat=2, name="平松年", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=63, age_note="63 岁", district="NS", block="档案馆区", axis="怀旧",
         prof_name="档案馆区老裱画师",
         prof="档案馆区老裱画师——裱画师傅的赛博后身——一双手把旧字画在案头抚平了再上墙，城里的纸寿就多过人",
         traits=[("手轻", "画心过手比端汤还稳"),
                 ("念旧", "残了的旧画他总劝人莫急着重装"),
                 ("耐心", "好纸上的活他肯等足工期")],
         creed="好纸经得起等。",
         thought="劳动是替档案馆区守一层一层的纸寿——复印机把拓碑的活计接走以后，旧字画修复这门口里手艺反倒金贵起来，他把残画一寸一寸在案头揭平，城里的记性就裱得住；代价是常年低头弯腰，指腹的茧比排刷毛还硬，一幅画等上三个月家里人跟着等三个月，饭桌上的话他常常让画先说；名字是裱画铺老师傅给起的，说平家的手松得开也收得住，年岁再紧的画到他手里都能松一松，这名字是案头修出来的；他说等揭不动了，就把案头那把鬃毛磨秃的老排刷传给跟他学托纸的徒弟，让平松年这三个字跟着一层一层的命纸，在档案馆区再裱几十年。",
         language="裱画铺案头慢语带行话，说画先说纸性，句尾爱带一句等得住；口头禅「好纸经得起等」。",
         wardrobe="靛青围裙浆洗得挺括，案头绒布掸得无尘，那把鬃毛磨秃的老排刷别在围裙带里。",
         life="出身：档案馆区裱画铺里学徒出身，师父教的第一课是托纸上墙先看天。转折：复印机把拓碑的活计接走以后，铺里专做旧字画修复，他说好纸经得起等。现状：裱画案头那把鬃毛磨秃的老排刷——师父传的，排笔走的分寸全在这把秃了毛的老刷上；同城历史立面群的老照相馆暗房师傅谢韵秋收工路过铺门口，一个存旧相一个裱旧画，是 NS 城里的一对旧物守相人。",
         behavior="开案必先扫一遍绒布台；托纸必先看一遍天色；收工必把排刷涮净了挂回案头。",
         relations="住档案馆区铺子后间的阁楼（天窗正对着案头）；同城老友=历史立面群老照相馆暗房师傅谢韵秋（C-10047·一个存旧相一个裱旧画，NS 城里的一对旧物守相人）；徒弟=跟他学托纸上墙的小徒弟。",
         hook="裱画案头那把鬃毛磨秃的老排刷——档案馆区的师传排刷，几层命纸的分寸全在这把秃刷的腕上",
         behavior_hint="托纸必先看一遍天色",
         style_dna=sd("裱画铺案头慢语带行话", "说画先说纸性，一句是一层", "好纸经得起等",
                      "从残到全——先揭后托，后上墙", "案头式念旧幽默——拿复印机打趣老手艺"),
         gene_evidence="genes/lives.json#hook_objects-674（裱画案头那把鬃毛磨秃的老排刷。）"
                       "+ #turning_points-501（复印机把拓碑的活计接走以后，铺里专做旧字画修复，他说好纸经得起等。）"),
    # ---- 席 #3 老白铁匠（碳基·原生代·RV·烟火轴）----
    dict(num=10065, seat=3, name="练铁生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=49, age_note="49 岁", district="RV", block="光桥市集", axis="烟火",
         prof_name="光桥市集老白铁匠",
         prof="光桥市集老白铁匠——白铁匠的赛博后身——一座老铁砧敲敲打打几十年，市集上人家的壶底桶箍都认他的手",
         traits=[("爽利", "活计当面敲定价"),
                 ("手艺硬", "壶底桶箍敲出来滴水不漏"),
                 ("仗义", "街坊的旧桶修不好不收钱")],
         creed="桶有价，手艺无价。",
         thought="劳动是替光桥市集守一摊敲得响的手艺——塑料桶把铁皮桶的行情挤对没了以后，他干脆把摊子改成修补铺，人家桶坏了舍不得扔的还寻得回他这双手，市集的烟火里敲打声就断不了；代价是常年守着炉子砧子，虎口的茧一层压一层，夏天摊前热得像蒸笼，家里人熬的绿豆汤总等他收了锤才喝上凉的那口；名字是市集老铁匠给起的，说练家的手是铁里生的，砧上滚过的活到他手里都能活，这名字是敲出来的；他说等敲不动了，就把铺子角落里那座磨出光面的老铁砧留在市集，让练铁生这三个字跟着一声一声敲打，在光桥市集再响几十年。",
         language="白铁摊前吆喝带敲打口风，说活先说料，句尾爱带一句当面敲定；口头禅「桶有价，手艺无价」。",
         wardrobe="帆布工装袖口烫着细小的锡点，围裙上锤痕叠着锤痕，那副包了浆的木柄小锤不离手。",
         life="出身：光桥市集开市那年跟着师父支的摊，学的是敲壶底收口不伤料。转折：铁皮桶被塑料桶挤对得没了行情，他干脆把摊子改成修补铺，说桶有价手艺无价。现状：白铁铺角落里那座磨出光面的老铁砧——师父传的，几十年敲出来的光面就是活计的账本；同城江岸滩涂的苇编匠人麦冬生赶集路过摊前，一个编苇一个敲铁，是 RV 市集上的一对老手作。",
         behavior="开摊必先净一遍砧面；接活必先当面试水；收摊必把锤子砧子擦干收好。",
         relations="住光桥市集铺子后的板间（铁砧就守在窗边）；同城老友=江岸滩涂苇编匠人麦冬生（C-10049·一个编苇一个敲铁，RV 市集上的一对老手作）；老主顾=桶底壶嘴坏了都寻他的市集街坊们。",
         hook="白铁铺角落里那座磨出光面的老铁砧——光桥市集的师传铁砧，几十年壶底桶箍的敲打声全落在这方砧面上",
         behavior_hint="接活必先当面试水",
         style_dna=sd("白铁摊前吆喝带敲打口风", "说活先说料，短句当当响", "桶有价，手艺无价",
                      "从坏到好——先看伤，后开锤", "摊前式热幽默——拿塑料桶打趣老手艺"),
         gene_evidence="genes/lives.json#hook_objects-675（白铁铺角落里那座磨出光面的老铁砧。）"
                       "+ #turning_points-502（铁皮桶被塑料桶挤对得没了行情，他干脆把摊子改成修补铺，说桶有价手艺无价。）"),
    # ---- 席 #4 老剃头挑子师傅（碳基·新市民派·MD·逍遥轴）----
    dict(num=10066, seat=4, name="曾稳山", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=61, age_note="61 岁", district="MD", block="医馆巷", axis="逍遥",
         prof_name="医馆巷老剃头挑子师傅",
         prof="医馆巷老剃头挑子师傅——剃头匠的赛博后身——一副挑子走街串巷几十年，巷子里的后脑勺都认他这双手",
         traits=[("随和", "熟客坐门槛上他也照样下手"),
                 ("手稳", "刀口贴着后脑勺走从不慌"),
                 ("逍遥", "剃完一头爱多聊半支烟的工夫")],
         creed="熟客的后脑勺，认我这双手。",
         thought="劳动是替医馆巷守一副走得动的挑子——理发店开进巷子以后，挑子照旧走街，老主顾剃头不为赶时髦，图的是他这双手认得每一颗后脑勺，巷口的逍遥就剃得出来；代价是肩上一头热一头凉挑了几十年，脚底板的老茧比巷口石阶还厚，家里人常劝他歇，他说只要还有人坐上凳子就不算歇；名字是巷口老中医给起的，说曾家的手稳得住，刀在头上走像山一样定，这名字是挑子走出来的；他说等挑不动了，就把担子上那副报街用的旧唤头交给接挑子的后生，让曾稳山这三个字跟着巷口一声长鸣，在医馆巷再走几十年。",
         language="剃头挑子走街吆喝带巷语，开刀先问一声稳当，句尾爱带一句坐好莫动；口头禅「熟客的后脑勺，认我这双手」。",
         wardrobe="洗旧的靛蓝布衫袖口利落，围布叠得方方正正，挑子一头挂着荡刀布一头挂着铜盆。",
         life="出身：挑子是他爹传的，走的第一条巷就是医馆巷，学的是刀贴头皮走不伤一寸。转折：理发店开进巷子以后，挑子照旧走街，他说熟客的后脑勺认他这双手。现状：剃头担子上那副报街用的旧唤头——爹传的，巷口一响老主顾就知道他到了；同城医馆巷的老药师桂存仁抓完药出门晒太阳，总要他顺手修一修鬓角，是医馆巷里的一对老闲人。",
         behavior="开工必先荡三下刀布；落刀必先问一声稳当；收挑必把唤头擦亮了挂回担头。",
         relations="住医馆巷巷尾的赁屋（挑子就立在门边）；同城老友=医馆巷老药师桂存仁（C-10045·一个抓药一个剃头，医馆巷里的一对老闲人）；老主顾=巷子里几代人都坐过他凳子的老街坊们。",
         hook="剃头担子上那副报街用的旧唤头——医馆巷的家传唤头，巷口一声长鸣就是挑子到了的信号",
         behavior_hint="落刀必先问一声稳当",
         style_dna=sd("剃头挑子走街吆喝带巷语", "开刀先问一声稳当，短句贴着刀走", "熟客的后脑勺，认我这双手",
                      "从生到熟——先看头型，后落刀", "挑子式闲幽默——拿理发店打趣老挑子"),
         gene_evidence="genes/lives.json#hook_objects-676（剃头担子上那副报街用的旧唤头。）"
                       "+ #turning_points-503（理发店开进巷子以后，挑子照旧走街，他说熟客的后脑勺认他这双手。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card10(c):
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
VISIBLE10 = {
    10063: "八号楼街区书报亭（开亭最早·灯下理刊·收亭最晚）",
    10064: "档案馆区裱画铺案头（工期一坐一整天·托纸看天·收工涮刷）",
    10065: "光桥市集白铁摊（开摊即开敲·当面试水·收摊擦砧）",
    10066: "医馆巷走街挑子（巷口唤头一响·落刀问稳当·收工擦唤头）",
}
for c in CARDS10:
    c["profession_visible"] = VISIBLE10[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats10 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS10}
for c in CARDS10:
    mine = _seats10[cid_of(c)]
    dup = [cid_of(o) for o in CARDS10 if o is not c and _seats10[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates10(rendered, rows_now):
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
def apply10(rendered):
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
    print(f"resume-intake b8 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


# ---------- 批后收口步（R1759 候选单兑现：needs face 刷新→behavior 强制再生→rows 对齐断言）----------
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
    rendered = [(c, render_card10(c), ri.build_light(c)) for c in CARDS10]
    rows = ri.light_rows()
    # K1 基线：light=10056（批七后）·现 max=C-10062·新号 C-10063~C-10066 连续顺延
    if len(rows) != 10056:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10056（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 676 and tp_n == 503):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 676/503（批八原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("书报亭里那盏绿玻璃罩子的旧台灯。",
                 "裱画案头那把鬃毛磨秃的老排刷。",
                 "白铁铺角落里那座磨出光面的老铁砧。",
                 "剃头担子上那副报街用的旧唤头。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("报亭挂上玻璃灯箱以后，过期旧报整摞装订成册留了底，他说一城的口气都在纸页里。",
                 "复印机把拓碑的活计接走以后，铺里专做旧字画修复，他说好纸经得起等。",
                 "铁皮桶被塑料桶挤对得没了行情，他干脆把摊子改成修补铺，说桶有价手艺无价。",
                 "理发店开进巷子以后，挑子照旧走街，他说熟客的后脑勺认他这双手。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates10(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply10(rendered)
    if rc == 0:
        rc = post_closeout()
        # 落库后自证：light=10060·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == POST_LIGHT, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light={POST_LIGHT} cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
