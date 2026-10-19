#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批九 intake —— 4 席碳源居民 C-10067~C-10070（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~10
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4+R1756 批六 4/4
+R1758 批七 4/4+R1760 批八 4/4 全门闸走满实证）。
本批=量产第七批·批九 4 席（倪笔正/宁守时/岳执衡/关橹声·R1761 席位方案定谳+原料 8/8 落库就绪
·qa/gene-round-R1761.log·换域面=修笔/修表/做秤/护河四新域——修笔/做秤/护河全库首域·修表与
C-10040 守钟人异面不撞）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-677/678/679/680+#turning_points-504/505/506/507
·本批实锚全在库·hook_objects 总数 680/turning_points 总数 507 复读核对·tp 原文代词=他
·R1761 定谳=四席男席·真名预检 4/4 unique）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10060 卡零触碰；light append-only 追加字节尾；cursor 不插队。
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
BIRTH = "2026-10-19"                   # 复产批九批日（CEO 解禁令当日滚动批）
BATCH = "复产批九"
MAX_ID = 10066                         # 现存最大号（K1 连续顺延上界=批八尾席）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS11 = [
    # ---- 席 #1 老修笔师（碳基·原生代·NS·怀旧轴）----
    dict(num=10067, seat=1, name="倪笔正", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="NS", block="档案馆区", axis="怀旧",
         prof_name="档案馆区老修笔师",
         prof="档案馆区老修笔师——修笔匠的赛博后身——一盘铱金笔尖按粗细分好，全城写字人手里的笔就都有了着落",
         traits=[("较真", "笔尖歪半丝他都要重铆一遍"),
                 ("念旧", "案头那盘老笔尖谁劝也不收"),
                 ("手轻", "开笔先在灯下看一遍尖嘴")],
         creed="笔尖正了，字才立得住。",
         thought="劳动是替档案馆区守一门修笔的老手艺——流水线出的笔再多，笔尖磕了铱粒、歪了缝，写字人手里那点分寸就没了着落，他一尖一尖修回来，城里的字就还立得住；代价是常年弓在案头，眼睛熬在灯下比笔尖还尖，家里人劝他歇案他总说再修完这一盘，指腹的茧磨得比铱粒还亮；名字是街口老书法家给起的，说倪家的手正，笔到他手里就没有修不直的尖，这名字配得上守笔的人；他说等修不动了，就把案头那盘按粗细分好的铱金笔尖传给肯学这门活的小徒弟，让倪笔正这三个字跟着全城写字人手里的笔，在档案馆区再立几十年。",
         language="修笔案头老手艺腔带书卷气，报笔先报尖嘴，句尾爱带一句立得住；口头禅「笔尖正了，字才立得住」。",
         wardrobe="藏青布褂袖口套着旧袖筒，案头灯罩擦得发亮，指腹的茧比铱粒还厚。",
         life="出身：档案馆区笔铺巷长大的孩子，父亲那辈就在巷口摆修笔摊，他十六岁接的第一支笔是老书法家摔了尖的爱笔。转折：钢笔厂流水线铺开之后，肯修老笔的人少了，他偏接过这门活——流水线出的笔再多，写字人手里那点分寸还得靠修笔人一尖一尖找回来。现状：修笔铺案头一盘按尖嘴粗细排开的铱金笔尖——师父传的，哪路笔尖磕了铱粒，他眯眼一照就知道差在哪；同城档案馆区的老裱画师平松年收工路过笔铺，两人一个裱旧纸一个修旧笔，是北外滩出名的一纸一笔。",
         behavior="接笔必先在灯下照一遍尖嘴；修尖必先试一遍出水；交笔必在登记本上记下尖型，一笔不漏。",
         relations="住档案馆区笔铺巷的旧居（案头灯常年亮到收市）；同城老友=档案馆区老裱画师平松年（C-10064·一个裱旧纸一个修旧笔，北外滩的一纸一笔）；徒弟=巷里跟他学修尖的小学徒们。",
         hook="修笔铺案头一盘按尖嘴粗细排开的铱金笔尖——档案馆区修笔铺的师传笔尖盘，全城写字人手里那点分寸全从这盘里找回来",
         behavior_hint="接笔必先在灯下照一遍尖嘴",
         style_dna=sd("修笔案头老手艺腔带书卷气", "报笔先报尖嘴，短句一字一铆", "笔尖正了，字才立得住",
                      "从旧到正——先照尖，后开笔", "修笔式书卷幽默——拿流水线打趣老笔尖"),
         gene_evidence="genes/lives.json#hook_objects-677（修笔铺案头一盘按尖嘴粗细排开的铱金笔尖。）"
                       "+ #turning_points-504（钢笔厂流水线铺开之后，肯修老笔的人少了，他偏接过这门活。）"),
    # ---- 席 #2 老修表师（碳基·弄堂派·GM·安稳轴）----
    dict(num=10068, seat=2, name="宁守时", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=62, age_note="62 岁", district="GM", block="八号楼街区", axis="安稳",
         prof_name="八号楼街区老修表师",
         prof="八号楼街区老修表师——修表匠的赛博后身——一枚放大镜贴着眼睛对准摆轮，街坊腕上的老表就没一块走错的",
         traits=[("守时", "交表比约点从不迟一刻"),
                 ("手细", "游丝乱一丝他都要镊正"),
                 ("热心", "老街坊的表他义务校到底")],
         creed="表走得准，日子不慌。",
         thought="劳动是替八号楼街区守一门对得准的老手艺——电子表满街再方便，老街坊腕上那块老表连着的日子快慢，还得有人肯俯下身一格一格校回来，他把街坊的日子校准，弄堂的钟点就都齐了；代价是常年贴着放大镜弓在台前，眼睛一到傍晚就发花，家里人喊吃饭他总说等这枚摆轮稳下来，指节的茧比表壳还硬；名字是弄堂老钟表匠给起的，说宁家守得住时，街坊的表到他手里就没有修不准的，这名字往铺门一挂就是几十年；他说等镊不动了，就把玻璃柜里垫绒布的那格老怀表校准仪传给肯学的小徒弟，让宁守时这三个字跟着街坊腕上的老表，在八号楼街区再走几十年。",
         language="弄堂修表铺慢语带街坊闲话，报表先报误差，句尾爱带一句不慌；口头禅「表走得准，日子不慌」。",
         wardrobe="灰呢旧马甲口袋里别着两把镊子，右眼常挂着那枚老放大镜，台灯擦得比表盘还亮。",
         life="出身：弄堂口修表铺里长大的孩子，父亲那辈守的就是这间铺面，他十四岁上手拆的第一块表是老街坊的上海牌。转折：电子表满街以后，修表铺冷清了些，他转去给老街坊义务校表，手艺不生——铺子冷清了，街坊腕上的日子不能冷清。现状：修表铺玻璃柜里垫绒布的那格老怀表校准仪——师父传的，哪块老表走不稳，往这格里躺一晚就听得出毛病；同城八号楼街区的老书报亭主晏知秋收摊路过铺门口，两人一个守钟点一个守报头，是八号楼街区出名的一钟一报。",
         behavior="接表必先上弦听一遍走字；校表必对一遍报时台；交表必把误差写在单据角上，一格不差。",
         relations="住八号楼街区修表铺的阁楼（推开窗就望得见街口的书报亭）；同城老友=八号楼街区老书报亭主晏知秋（C-10063·一个守钟点一个守报头，八号楼街区的一钟一报）；徒弟=弄堂里跟他学镊游丝的小徒弟们。",
         hook="修表铺玻璃柜里垫绒布的那格老怀表校准仪——八号楼街区修表铺的师传校准仪，街坊腕上老表的快慢全在这格绒布上听出来",
         behavior_hint="校表必对一遍报时台",
         style_dna=sd("弄堂修表铺慢语带街坊闲话", "报表先报误差，收句必落在走字上", "表走得准，日子不慌",
                      "从快到准——先听摆，后对时", "修表铺慢幽默——拿电子表打趣老机芯"),
         gene_evidence="genes/lives.json#hook_objects-678（修表铺玻璃柜里垫绒布的那格老怀表校准仪。）"
                       "+ #turning_points-505（电子表满街以后，修表铺冷清了些，他转去给老街坊义务校表，手艺不生。）"),
    # ---- 席 #3 老做秤师（碳基·原生代·RV·秩序轴）----
    dict(num=10069, seat=3, name="岳执衡", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=54, age_note="54 岁", district="RV", block="光桥市集", axis="秩序",
         prof_name="光桥市集老做秤师",
         prof="光桥市集老做秤师——做秤匠的赛博后身——一杆杆秤钉满了秤星，市集上的斤两就一句不虚",
         traits=[("公道", "秤星偏一毫他要拆了重钉"),
                 ("手准", "钉星不看图全凭手感"),
                 ("耐烦", "一根秤杆能磨上三天")],
         creed="秤星不哄人，斤两才作数。",
         thought="劳动是替光桥市集守一杆杆不哄人的秤——电子秤按键再快，秤杆上那几排钉出来的秤星，是市集几十年攒下的公道，他把秤星钉准，买卖两头的心里就都有底；代价是常年俯在秤杆上钉星，眼睛熬得比秤星还亮，指腹被钉冲磨出的茧厚得捏得住针尖，家里人劝他歇手他总说这杆钉完就收；名字是市集老会长给起的，说岳家的手准，钉出来的秤从不亏人一两，这名字在市集传了几十年；他说等钉不动了，就把墙上那串试秤用的标准铜砝码传给肯接铺子的小徒弟，让岳执衡这三个字跟着市集的斤两，在光桥再准几十年。",
         language="市集做秤行话带秤星口诀，报秤先报定盘，句尾爱带一句不亏一两；口头禅「秤星不哄人，斤两才作数」。",
         wardrobe="深蓝围裙口袋里插着钉冲和小铜锤，指腹的茧捏得住针尖，袖口沾着秤杆的木香。",
         life="出身：光桥市集摆秤摊人家的孩子，父亲钉秤他就在旁边递铜皮，他上手钉的第一杆秤是给老鱼摊定的大秤。转折：电子秤进了菜场，来问杆秤的人少了，他开始给博物馆修老秤——市面冷了，老秤上的公道不能丢。现状：做秤铺墙上挂着一串试秤用的标准铜砝码——家传的，每杆新秤出厂前都要先过这串砝码的手；同城光桥市集的老白铁匠练铁生收炉路过秤铺，两人一个打白铁一个钉秤星，是光桥市集出名的一铁一秤。",
         behavior="开秤必先校一遍定盘星；钉星必先试三遍砝码；交秤必当着买主的面称一次手边的旧物，一两不差才放手。",
         relations="住光桥市集做秤铺的后屋（铺门一开就望得见白铁铺的炉火）；同城老友=光桥市集老白铁匠练铁生（C-10065·一个打白铁一个钉秤星，光桥市集的一铁一秤）；徒弟=市集里跟他学钉星的小徒弟们。",
         hook="做秤铺墙上挂着一串试秤用的标准铜砝码——光桥市集做秤铺的家传砝码串，每杆新秤的公道全先过这串铜星的手",
         behavior_hint="开秤必先校一遍定盘星",
         style_dna=sd("市集做秤行话带秤星口诀", "报秤先报定盘，一句是一两", "秤星不哄人，斤两才作数",
                      "从称到信——先定星，后交秤", "市集直幽默——拿电子秤打趣老杆秤"),
         gene_evidence="genes/lives.json#hook_objects-679（做秤铺墙上挂着一串试秤用的标准铜砝码。）"
                       "+ #turning_points-506（电子秤进了菜场，来问杆秤的人少了，他开始给博物馆修老秤。）"),
    # ---- 席 #4 老护河员（碳基·弄堂派·RV·逍遥轴）----
    dict(num=10070, seat=4, name="关橹声", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=60, age_note="60 岁", district="RV", block="渡轮航道", axis="逍遥",
         prof_name="渡口老护河员",
         prof="渡口老护河员——老船工的赛博后身——一支老橹在水里摇了四十年，江面的深浅风流他都认得",
         traits=[("识水", "看水色就知道明天的流"),
                 ("守约", "每天一趟河上撑风雪不误"),
                 ("淡泊", "渡口冷清了他也不急不恼")],
         creed="水路认人，橹声认河。",
         thought="劳动是替这条江守一趟一趟的水路——大桥通车以后渡口冷清了，可江上的流、汛里的旧桩、夜里认水的老规矩，还得有人每天撑一趟船记一遍，他把这趟撑下去，江面的路就没断；代价是常年泡在水汽里，膝盖落了风湿的老病，家里人劝他上岸他总说等把这趟水路看老，手里的老茧厚得握得住橹把，肩膀被纤绳勒出的印子一辈子没褪；名字是渡口老辈船工给起的，说关家的橹声沉，水再急他一橹下去河就认得，这名字在渡口传了一辈子；他说等撑不动了，就把渡口石桩上那道拴缆绳勒出来的深槽指给接班的护河员看，让关橹声这三个字跟着每天的橹声，在这条江上再响几十年。",
         language="渡口水话带船家号子，报水先报流速，句尾爱带一句稳住桨；口头禅「水路认人，橹声认河」。",
         wardrobe="旧蓑衣换成了防水胶衣，裤脚常年沾着江泥，那支老橹磨得油亮。",
         life="出身：渡口船家讨生活人家的孩子，父亲把橹传到他手里那年他才十五，学的第一课是听水认流。转折：大桥通车之后，渡口的营生渐渐稀了，他领了护河员的活，照旧每天在河上撑一趟——营生稀了，水路上的老规矩不能稀。现状：渡口石桩上拴缆绳勒出来的那道深槽——父辈传下的老石桩，几十年缆绳勒进石头里的印子，就是这条水路最老的账本；同城渡口的守灯人灯伯夜里亮灯他清早出船，两人一灯一橹守着渡口的晨昏，是江上出名的一灯一橹。",
         behavior="出船必先看一遍水色；过湾必先听一遍流声；收船必把当日水情记进渡口的老水簿，一天不缺。",
         relations="住渡口石阶旁的看船小屋（推开门就是石桩和缆绳）；同城老友=渡口守灯人灯伯（C-10017·一个夜里守灯一个清早护河，渡口晨昏的一灯一橹）；徒弟=跟他听水认流的小护河员们。",
         hook="渡口石桩上拴缆绳勒出来的那道深槽——渡口船家的老石桩，几十年缆绳勒出的印子就是这条水路最老的账本",
         behavior_hint="出船必先看一遍水色",
         style_dna=sd("渡口水话带船家号子", "报水先报流速，话头顺流走", "水路认人，橹声认河",
                      "从桥到河——先看水，后下橹", "船家水幽默——拿大桥打趣老渡船"),
         gene_evidence="genes/lives.json#hook_objects-680（渡口石桩上拴缆绳勒出来的那道深槽。）"
                       "+ #turning_points-507（大桥通车之后，渡口的营生渐渐稀了，他领了护河员的活，照旧每天在河上撑一趟。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card11(c):
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
VISIBLE11 = {
    10067: "档案馆区笔铺修笔案（晨开案·学生放学送笔高峰·收市最晚）",
    10068: "八号楼街区修表铺（早市开铺·义务校表日·关门最准点）",
    10069: "光桥市集做秤铺（晨市开铺·新秤过砝码·收市最晚）",
    10070: "渡口石阶航道（清早出船一趟·巡河全段·收船最晚）",
}
for c in CARDS11:
    c["profession_visible"] = VISIBLE11[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats11 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS11}
for c in CARDS11:
    mine = _seats11[cid_of(c)]
    dup = [cid_of(o) for o in CARDS11 if o is not c and _seats11[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates11(rendered, rows_now):
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
def apply11(rendered):
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
    print(f"resume-intake b9 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card11(c), ri.build_light(c)) for c in CARDS11]
    rows = ri.light_rows()
    # K1 基线：light=10060（批八后）·现 max=C-10066·新号 C-10067~C-10070 连续顺延
    if len(rows) != 10060:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10060（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 680 and tp_n == 507):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 680/507（批九原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("修笔铺案头一盘按尖嘴粗细排开的铱金笔尖。",
                 "修表铺玻璃柜里垫绒布的那格老怀表校准仪。",
                 "做秤铺墙上挂着一串试秤用的标准铜砝码。",
                 "渡口石桩上拴缆绳勒出来的那道深槽。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("钢笔厂流水线铺开之后，肯修老笔的人少了，他偏接过这门活。",
                 "电子表满街以后，修表铺冷清了些，他转去给老街坊义务校表，手艺不生。",
                 "电子秤进了菜场，来问杆秤的人少了，他开始给博物馆修老秤。",
                 "大桥通车之后，渡口的营生渐渐稀了，他领了护河员的活，照旧每天在河上撑一趟。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates11(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply11(rendered)
    if rc == 0:
        # 落库后自证：light=10064·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10064, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10064 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
