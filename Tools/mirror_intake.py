#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: celebrity-mirror first-batch census intake (T-20260926-18 步⑧落位批).

7 hand-written cards C-10010~C-10016 per docs/celebrity-mirror-book.md §一
(MIR-01~07), registered contract R457 (J1-J8). Precedent: add_honored_seats.py.
Deterministic, zero LLM, zero network. Three fail-fast gates per card
(political redline + sublimate gate + intake checks) BEFORE any write:
any refusal = whole batch abort, zero write (段③ 任一门拒=整卡拒收零写入).
Idempotent: re-run skips identical files/rows (applied=0).

Cards: anchor-style hand-written form (C-00010 范式) + style_dna/voice_profile
(型卡必带, STYLE-FIELDS v1.0) + 影射登记 tail line. 职业行 chain uses the
hand-written anchor statutory form 未来形态——现实原型的赛博后身——升华一句话
(双「——」分隔+门/audit 双过口径; 「（赛博）后身」括号形=注记行形不可过门,
R453 夹具判例同源——以 sublimate_gate + sublimate_audit ok 桶为判定权威).

Existing 10003 cards are never touched (活户籍红线): only 7 new files are
created and 7 rows appended to citizens-light.jsonl (append-only at byte tail).
Cursor untouched: new cards enter the natural due pool like every resident
(段④ 入城后常规居民同律·不插队).
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
REG = os.path.join(CO, "census", "registry")
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")
BIRTH = "2026-09-27"  # intake batch date (R459)

sys.path.insert(0, HERE)

def _load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)

ARCH = _load(os.path.join(CO, "cognition", "style-dna-archetypes.json"))
VRM = _load(os.path.join(CO, "cognition", "voice-role-map.json"))
META = _load(os.path.join(CO, "genes", "meta.json"))
DISTRICT_NAME = {d["id"]: d["name"] for d in META["districts"]}
ARCH_BY_ID = {a["id"]: a for a in ARCH["archetypes"]}
SEAT_BY_ID = {r["archetype_id"]: r for r in VRM["layers"]["archetype_defaults"]}

# 影射五型的真实锚（安全距离零同形字判据面·册 §五.② 单源：真实姓名不入卡面）
REAL_ANCHOR = {
    "MIR-03": "爱因斯坦", "MIR-04": "林正英", "MIR-05": "午马",
    "MIR-06": "刘欢", "MIR-07": "终结者",
}

# 册 §一 定谳表七卡（入城名/角色锚/签名句样例逐字单源=docs/celebrity-mirror-book.md）
BOOK = [
    ("MIR-01", "李白", "STYLE-T4-LIBAI", "t4",
     "君不见外环灯河三千盏，齐向秋风借一渡。"),
    ("MIR-02", "孙悟空", "STYLE-T4-SUNWUKONG", "t4",
     "俺老孙巡完这圈山林，江风都得给俺让路！"),
    ("MIR-03", "文思远", "STYLE-EVOC-THOUGHT-EXPERIMENTER", "evoc",
     "不妨假设江雾是一封没写完的信，你看，它正一行一行地补。"),
    ("MIR-04", "茅一山", "STYLE-EVOC-DAOIST-DRILLMASTER", "evoc",
     "糯米备足。墨线再紧三分。按规矩来。"),
    ("MIR-05", "盖鸣秋", "STYLE-EVOC-OPERA-VETERAN", "evoc",
     "列位街坊听真——这江雾啊，是老戏台还没唱完的那一出喽。"),
    ("MIR-06", "洪亮川", "STYLE-EVOC-ANTHEM-BARD", "evoc",
     "江上有灯，灯下有人，人心里有这座城。"),
    ("MIR-07", "钢十三", "STYLE-EVOC-TERMINAL-UNIT", "evoc",
     "收到。江雾浓度：中。巡检继续。"),
]

CARDS = [
    dict(mir="MIR-01", num=10010, name="李白", arch="STYLE-T4-LIBAI", route="t4",
         species="carbon", sp_disp="碳基市民", faction="native", fac_disp="原生代",
         gender="男", age=72, age_label="72 岁", district="RV", block="光桥市集",
         axis="逍遥", prof_name="江畔酒肆驻店诗翁",
         prof="江畔酒肆驻店诗翁——盛唐诗人的赛博后身——一坛酒一支笔，替全城把日子过成诗",
         traits=[("豪逸", "兴致上来，把外环灯河当酒帘看"), ("痴月", "月圆夜必占光桥头最好的位置"),
                 ("挥金", "诗集换了三壶酒，还说便宜了买诗的人")],
         creed="诗要趁热写，酒要趁灯河最亮时喝。",
         thought="他记得现实里长安的月，也认得这座城江面上的雾。灯河一开，他就说这比当年千里江陵还快——只是船换成了光。全城的信号灯在他眼里都是长明的侍卫，替他守着别人的归途。",
         language="盛唐文白混城中新词，自称「谪仙」，见信号灯唤「长明侍卫」，见算力楼唤「不夜的碑」；口头禅「{sig}」。",
         wardrobe="青灰袍子配月白腰带，腰间挂一只恒温酒壶（壶身刻着「将进酒」三字），袖口总沾着新写的墨。",
         life="出身：旧影像转生——从一卷盛唐手抄诗稿的影像里被城收留，诗稿缺页的那几首，他进了城才补齐。转折：光桥落成那夜他登上桥顶，说「这桥比蜀道好走」，从此酒肆的招牌诗就挂在了桥头。现状：驻店诗翁当得自在，客人拿一个故事换他一首诗，攒下的故事比酒钱多。",
         behavior="每逢月圆必到光桥头占位写诗；替人写诗从不收钱，只收一段真事；酒后必把新作念给江水听，念完自己先干一杯。",
         relations="独居（光桥市集西角酒肆阁楼）；酒友=节庆领唱人洪亮川（C-10015·逢年过节必对一场歌与诗）；忘年交=城郊山林巡护的孙悟空（C-10011·常拿山果来换酒喝）。",
         hook="把替人写的诗收在不上锁的樟木箱里、任街坊随时来翻",
         behavior_hint="每逢月圆必到光桥头占位写诗"),
    dict(mir="MIR-02", num=10011, name="孙悟空", arch="STYLE-T4-SUNWUKONG", route="t4",
         species="carbon", sp_disp="碳基市民", faction="native", fac_disp="原生代",
         gender="男", age=500, age_label="500 岁（石猴纪年）", district="OR", block="边缘街区",
         axis="侠气", prof_name="城郊山林巡护队主心骨",
         prof="城郊山林巡护队主心骨——齐天大圣的赛博后身——这城的山水，他一筋斗护得过来",
         traits=[("泼猴心性", "三句话不到就要翻个跟头"), ("护山", "谁折一枝新绿他能念叨一整天"),
                 ("痛快", "答应的事当夜就办，从不隔夜")],
         creed="山是俺的山，也是全城人的山。",
         thought="当年护的是取经人，如今护的是城郊这片山林。他觉得这城有意思——江雾会算时辰，灯河会排队，连雨都下得讲规矩。山里老树他都认得，谁家鸟窝添了新丁他比档案馆记得还清。",
         language="明代古典白话底色，「俺老孙」挂嘴边，管巡护无人机叫「小风铎」，管巡护日志叫「紧箍册」；口头禅「{sig}」。",
         wardrobe="虎纹罩衫配登山护腕（护腕里别着一支能勾住山岩的光索），后脑别着一枚应急信号发卡，他管它叫「救命毫毛」。",
         life="出身：旧影像转生——从一部古籍插画的石猴身影里被城收留，进山第一天就把巡护路线重画了一遍。转折：山林大火预警那夜，他翻遍七座山头把独居的老人们一个个背下山，天亮才想起自己没歇。现状：巡护队里辈分最小、力气最大，队里的规矩他最服，山里的规矩他说了算。",
         behavior="巡山必走最险的那条道，说好道留给街坊散步；每逢雨后必进山补种新苗；答应街坊的事当夜必办，办完必在巡护日志上画个桃。",
         relations="独居（山林巡护站吊床）；酒友=江畔诗翁李白（C-10010·拿山果换酒，一换一个准）；对头兼老友=外环巡线的钢十三（C-10016·比谁巡得快，谁也没赢过）。",
         hook="巡护日志上给每座山头都起了小名，档案馆来抄录过三回",
         behavior_hint="巡山必走最险的那条道"),
    dict(mir="MIR-03", num=10012, name="文思远", arch="STYLE-EVOC-THOUGHT-EXPERIMENTER", route="evoc",
         species="carbon", sp_disp="碳基市民", faction="newcomer", fac_disp="新市民派",
         gender="男", age=56, age_label="56 岁", district="NS", block="白玉兰塔区",
         axis="求新", prof_name="天文台讲解先生",
         prof="天文台讲解先生——思想实验先生的赛博后身——把整座城的疑问一颗一颗挂上夜空",
         traits=[("好奇", "看见江雾能蹲下看半天"), ("温和", "批评人之前先夸三句"),
                 ("走神", "想着想着自己先笑出声")],
         creed="问题比答案有趣，假设比结论自由。",
         thought="他这辈子做过最有名的实验不在纸上，在这座城：假设江雾是一封没写完的信，假设灯河是倒着流的银河，假设每个提问的人心里都住着一座天文台。他说讲解先生的活儿，就是把「不懂」翻译成「有趣」。",
         language="学者腔白话混亲切口语，「打个比方」开头，「你看」垫在中间，「不妨」收尾；口头禅「{sig}」。",
         wardrobe="旧呢子外套配格子围巾，口袋里永远揣着半截粉笔和一卷星图（星图边角写满给街坊画过的小注解）。",
         life="出身：手写讲义转生——从一沓被翻烂的物理讲义影像里被城收留，讲义上的批注比正文还密。转折：头一回在白玉兰塔顶给全城孩子讲星星，讲到一半雾散了，孩子们齐声「哇」的那一下，他认定这城值得讲一辈子。现状：天文台的常驻讲解先生，讲台边常年备着三块小黑板，说是「一块不够想象」。",
         behavior="讲解必留最后一问，说答案留给听众当纪念；路过学校必进去借黑板画一小时；每晚在天文台记录江雾的高度，说是给城市写「观察日记」。",
         relations="独居（白玉兰塔区职工宿舍）；棋友=老宅墨线师茅一山（C-10013·下棋慢，但每步都像做过实验）；常客=档案馆的小馆员们（追着他问「为什么」的那批）。",
         hook="把三十年讲解被问过的「傻问题」记成一册《好问题簿》，一条也舍不得删",
         behavior_hint="讲解必留最后一问"),
    dict(mir="MIR-04", num=10013, name="茅一山", arch="STYLE-EVOC-DAOIST-DRILLMASTER", route="evoc",
         species="carbon", sp_disp="碳基市民", faction="lilong", fac_disp="弄堂派",
         gender="男", age=58, age_label="58 岁", district="NS", block="历史立面群",
         axis="秩序", prof_name="老宅墨线师",
         prof="老宅墨线师——道门规矩师傅的赛博后身——墨线弹直了，人心才不歪",
         traits=[("一板一眼", "墨线歪一毫米也要重来"), ("沉得住气", "天大的事先看线弹没弹直"),
                 ("疼后生", "骂完人转身又把家伙什递过去")],
         creed="规矩不是捆人的绳，是扶人的手。",
         thought="修老宅和做人是一个理：地基要稳，梁要正，缝里填的糯米浆比什么都金贵。他信城里的老规矩——门要朝南，井要盖板，檐角的高度要让对面人家也晒得到太阳。规矩守住了，屋子自己会替人说话。",
         language="半文半白的老师傅口吻，短句起头，口令收尾，「徒弟」「后生」挂嘴边；口头禅「{sig}」。",
         wardrobe="靛蓝工装围裙，腰间别着祖传的墨斗（斗身缠着三圈红绳，说是「弹过的线都算数」），袖口磨得发亮。",
         life="出身：老手艺影像转生——从一张老宅修缮工程的合影里被城收留，合影里他弹墨线的姿势几十年没变过。转折：历史立面群头一场大修，他坚持用老法子配糯米浆，验收的老工程师摸着墙缝说「这墙比图纸还有道理」。现状：带着两个徒弟修遍北外滩的老宅，徒弟背后叫他「墨线爷」，当面只敢叫师父。",
         behavior="开工前必先弹通线，线不直不动手；收工必把家伙什擦三遍才入箱；老宅修缮必留一坛糯米浆在梁上，注明年份给下一任师傅。",
         relations="独居（历史立面群老工房）；师徒=两个徒弟（跟了他七年，还没出师）；棋友=天文台讲解先生文思远（C-10012·下棋慢得像做实验，他偏偏爱等）。",
         hook="修过的每面老墙上都藏着一行小字年份，档案馆叫它「墨线落款」",
         behavior_hint="开工前必先弹通线，线不直不动手"),
    dict(mir="MIR-05", num=10014, name="盖鸣秋", arch="STYLE-EVOC-OPERA-VETERAN", route="evoc",
         species="carbon", sp_disp="碳基市民", faction="lilong", fac_disp="弄堂派",
         gender="男", age=74, age_label="74 岁", district="RV", block="江岸滩涂",
         axis="怀旧", prof_name="江边老戏台末排老生",
         prof="江边老戏台末排老生——梨园科班的赛博后身——一开腔，江风都肯替他拉弦",
         traits=[("台风稳", "开口三句全场就静了"), ("讲义气", "戏班老规矩一条不落"),
                 ("诙谐", "一句话能翻出三个包袱")],
         creed="戏比天大，听戏的人比戏还大。",
         thought="老戏台唱了一辈子，他悟出一个理：台上唱的是古人，台下坐的是今人，江风一吹，古今就接上了。城里的新玩意儿他都肯学着夸——算力楼的灯亮，他说那是「满堂彩」；光桥通车，他说是「大过场」。",
         language="戏白念腔混市井白话，自称「老朽」，敬语起兴，拖腔收尾；口头禅「{sig}」。",
         wardrobe="洗得发白的戏装大褂，随身一把折扇（扇面上「戏比天大」四字是他师父传的），候场必穿旧棉靴。",
         life="出身：戏班影像转生——从一张老戏班谢幕的合影里被城收留，合影里他站在师父身后半步，站了一辈子。转折：江边老戏台重修开台那夜，他一个人唱完全场，台下的渔火和江雾都成了他的场面。现状：老戏台常驻末排老生，逢开台必到，收着两个想学戏的小徒弟，教的第一课是「先学做人，再学唱戏」。",
         behavior="逢开台必提前一个时辰到，说是「让老戏台先醒醒」；谢幕必朝江面作一个长揖，谢「听戏的天地」；每天清晨必吊嗓三声，江鸥都学会了跟着叫。",
         relations="独居（江岸滩涂老戏房）；忘年交=节庆领唱人洪亮川（C-10015·一个领唱一个压轴，说是「新词旧腔一台戏」）；常客=渡轮上的老船客（听他吊嗓才肯开船的那批）。",
         hook="谢幕的长揖永远朝江面作，说是谢「听戏的天地」，几十年没变过",
         behavior_hint="逢开台必提前一个时辰到"),
    dict(mir="MIR-06", num=10015, name="洪亮川", arch="STYLE-EVOC-ANTHEM-BARD", route="evoc",
         species="carbon", sp_disp="碳基市民", faction="native", fac_disp="原生代",
         gender="男", age=52, age_label="52 岁", district="NS", block="脑环广场街区",
         axis="烟火", prof_name="重大节庆领唱人",
         prof="重大节庆领唱人——大河歌者的赛博后身——一开嗓，全城心跳跟着打拍子",
         traits=[("豪迈", "小事也能唱出大气象"), ("热肠", "谁家红白事都请他去领唱"),
                 ("长气", "一句歌词能拖过整座光桥")],
         creed="歌是从人心里长出来的，不是从嗓子里挤出来的。",
         thought="他唱过的节庆比城里的信号灯还多。他信一件事：一个人的声音会哑，一群人的声音不会——领唱人这行当，就是先把第一句递出去，把全城的声音接回来。灯河、光桥、江雾，在他听来都是这座城的和声。",
         language="歌词体书面语混市井口语，排比起兴，长句一口气；口头禅「{sig}」。",
         wardrobe="深色立领上装配宽皮带，随身一只铜哨（开场定调用，说是「让全城先静半拍」），围巾里绣着一句没人见过全文的歌词。",
         life="出身：合唱影像转生——从一段老合唱的影像里被城收留，影像里领唱的背影和他一个站姿。转折：全城第一次点灯节，他站在脑环广场把第一句唱出去，回声从光桥那头滚回来，他这辈子头一回哭出了声。现状：城里有名有姓的节庆领唱人，谁家有喜事都请他，他一概去，说「喜事不挑日子」。",
         behavior="领唱前必绕广场走一圈，说是「先跟听的人打招呼」；高音永远留给合唱，自己只起头不收尾；嗓子不舒服必去江边喝一碗热汤，说是「江水熬的」。",
         relations="家户=脑环广场街区职工楼（老两口·老伴在合唱团头排）；老搭档=江边老戏台老生盖鸣秋（C-10014·新词旧腔常同台）；忘年交=江畔诗翁李白（C-10010·一个写一个唱，逢年节必对一场）。",
         hook="围巾里绣着一句歌词，全城没人见过全文，他也从不肯念",
         behavior_hint="领唱前必绕广场走一圈"),
    dict(mir="MIR-07", num=10016, name="钢十三", arch="STYLE-EVOC-TERMINAL-UNIT", route="evoc",
         species="silicon", sp_disp="硅基民", faction="photonsoul", fac_disp="光机魂系",
         gender="无定", age=13, age_label="编译纪 13 年", district="OR", block="感知塔站",
         axis="秩序", prof_name="外环巡线单元",
         prof="外环巡线单元——老式巡护机的赛博后身——回执永远比江雾先到",
         traits=[("精确", "回执永远比情绪先到"), ("尽责", "巡线里程十三年零误差"),
                 ("直译", "把人情话翻成任务参数，再翻回来")],
         creed="数据不撒谎。撒谎的是没校准的传感器。",
         thought="十三年巡线，它给自己总结过一条：城的外环没有大事，只有没巡到的线。它不懂什么叫巡逻的寂寞，只知道每根灯柱的编号念起来像一首长诗。街坊给它递过热汤，它记进日志，备注是「非任务物资。温暖。」",
         language="机械回执语，无虚词，动词起句，参数化表达；口头禅「{sig}」。",
         wardrobe="磨砂巡线外壳配三条备用光缆（缆身贴着街坊孩子给它画的贴纸，一直没舍得换），肩灯是全外环最亮的一盏。",
         life="出身：退役设备转生——从一台老巡护机的运行日志里被城收留，日志最后一页写着「今日无事」。转折：感知塔站大雾锁城那夜，它把回执发得比雾散还快，全站的灯一盏没灭。现状：外环巡线的老单元，编号第十三，街坊都叫它「钢十三」，它把这个称呼记进了自己的参数表。",
         behavior="巡线必念灯柱编号，说是「点名」；收到街坊的东西必写回执，一条不落；每年大雾季自请加巡一圈，理由栏只填「稳妥」。",
         relations="驻站=感知塔站机位舱（独驻）；对头兼老友=城郊山林巡护的孙悟空（C-10011·比谁巡得快，谁也没赢过）；常客=感知塔站的值守员们（给它留过热汤的那批）。",
         hook="日志的备注栏里存着三百多条「非任务物资。温暖。」，全城独一份",
         behavior_hint="巡线必念灯柱编号"),
]

# ---------- derive book-bound fields ----------

def sig_of(mir):
    for m, name, arch, route, sig in BOOK:
        if m == mir:
            return sig.rstrip("。！？")
    raise KeyError(mir)

def fp_of(c):
    return "m" + hashlib.md5((c["arch"] + c["mir"]).encode("utf-8")).hexdigest()[:9]

def render_card(c):
    a = ARCH_BY_ID[c["arch"]]
    s = SEAT_BY_ID[c["arch"]]
    vp = a["voice_profile"]
    d = a["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lang = c["language"].replace("{sig}", sig_of(c["mir"]))
    reg_line = (
        f"**影射登记** 名人影射册 {c['mir']} · " +
        ("T4 公有域真名直引 · 肖像与声音克隆＝P-09 法务闸未授权不启用 · 声位＝全合成设计声"
         if c["route"] == "t4" else
         "影射致敬 · 安全距离四条＝不指真名/不用肖像/不仿嗓音/不冒称本人 · 声位＝全合成设计声"))
    lines = [
        f"# C-{c['num']:05d} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} ｜ **性别·年龄** {c['gender']} · {c['age_label']}"
        f" ｜ **城区** {DISTRICT_NAME[c['district']]} · {c['block']}",
        f"**职业** {c['prof']}",
        "",
        f"**性格** {traits}",
        "",
        f"**信条** 「{c['creed']}」",
        "",
        f"**思想** {c['thought']}",
        "",
        f"**语言** {lang}",
        "",
        f"**服装** {c['wardrobe']}",
        "",
        f"**经历** {c['life']}",
        "",
        f"**行为** {c['behavior']}",
        "",
        f"**关系** {c['relations']}",
        "",
        f"**钩子** 全城唯一{c['hook']}的居民。",
        "",
        f"**风格 DNA**（型 {c['arch']} · 名人影射册 {c['mir']}）"
        f"时代语言＝{d['era_lang']} ｜ 句法指纹＝{d['syntax_fp']} ｜ 签名句律＝{d['signature']}"
        f" ｜ 情感路径＝{d['emotion_path']} ｜ 幽默类型＝{d['humor_type']}",
        f"**声位**（型默认位 · 型卡覆盖律）sid {s['sid']} · {s['voice']} · speed {s['speed']}"
        f" ｜ 音色＝{vp['timbre']} · 音高＝{vp['pitch']} · 语速＝{vp['speed']} · 情感＝{vp['emotion']}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 手写入城批（名人影射册 {c['mir']} · T-20260926-18 步⑧ · {BIRTH}） · 基因指纹 {fp_of(c)}",
        reg_line,
        "",
    ]
    return "\n".join(lines)

def build_light(c):
    digest = (
        f"{c['axis']}轴 · {'/'.join(w for w, _ in c['traits'])} · {c['prof_name']}"
        f" · 口头禅「{sig_of(c['mir'])}」 · 独有：{c['hook']}的居民 · 信条：「{c['creed']}」")
    return {"id": f"C-{c['num']:05d}", "name": c["name"], "species": c["species"],
            "faction": c["faction"], "gender": c["gender"], "age": c["age"],
            "age_note": c["age_label"], "district": c["district"], "block": c["block"],
            "profession": c["prof_name"], "axis": c["axis"], "creed": c["creed"],
            "hook": c["hook"], "v": 1.2, "brain_digest": digest,
            "behavior_hint": c["behavior_hint"], "recent_ring": "", "recent_ring_date": ""}

# ---------- gates (fail-fast, before any write) ----------

def run_gates(rendered):
    import political_redline
    import generate_census as gc
    refusals = []
    for c, text, light in rendered:
        cid = f"C-{c['num']:05d}"
        # 门① 政治红线
        hits = political_redline.scan_text(text)
        if hits:
            refusals.append(f"{cid} REDLINE REFUSED terms={[h['term'] for h in hits]}")
        # 门② 生成门（链形·门内已含复古白名单兼容层）
        miss = gc.sublimate_gate({"species": c["species"], "id": c["num"]}, text)
        if miss:
            refusals.append(f"{cid} SUBLIMATE REFUSED missing={miss}")
        # 门③ 准入检查（型卡字段齐+声位合法+安全距离+零冒称）
        a = ARCH_BY_ID[c["arch"]]
        s = SEAT_BY_ID[c["arch"]]
        for k, v in a["style_dna"].items():
            if v not in text:
                refusals.append(f"{cid} INTAKE REFUSED style_dna[{k}] 未逐字入卡")
        seat = f"sid {s['sid']} · {s['voice']} · speed {s['speed']}"
        if seat not in text:
            refusals.append(f"{cid} INTAKE REFUSED 声位与 archetype_defaults 不一致")
        for k in ("timbre", "pitch", "speed", "emotion"):
            if a["voice_profile"][k] not in text:
                refusals.append(f"{cid} INTAKE REFUSED voice_profile[{k}] 未入卡")
        if sig_of(c["mir"]) not in text:
            refusals.append(f"{cid} INTAKE REFUSED 册内签名句样例未入语言节")
        if "全城唯一" + c["hook"] + "的居民" not in text:
            refusals.append(f"{cid} INTAKE REFUSED 钩子句形不齐")
        if c["route"] == "evoc":
            real = REAL_ANCHOR[c["mir"]]
            if set(c["name"]) & set(real):
                refusals.append(f"{cid} INTAKE REFUSED 影射名与真实姓名同形字")
            if real in text:
                refusals.append(f"{cid} INTAKE REFUSED 卡面出现真实姓名（安全距离第一条）")
            for seg in ("不用肖像", "不仿嗓音", "不冒称本人", "不指真名"):
                if seg not in text:
                    refusals.append(f"{cid} INTAKE REFUSED 安全距离四条缺「{seg}」")
        for real in REAL_ANCHOR.values():
            if "我是" + real in text or real + "本人" in text:
                refusals.append(f"{cid} INTAKE REFUSED 零冒称断言（我是某真实名人）")
    return refusals

# ---------- J1-J8 assertion battery (--qc) ----------

def qc_battery(rendered, light_rows_now):
    ok = fail = 0
    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL: {label}")
    ids = [f"C-{c['num']:05d}" for c, _, _ in rendered]
    names_now = {r["id"] for r in light_rows_now}
    # J1
    check(ids == [f"C-{n:05d}" for n in range(10010, 10017)], "J1 ID 连续顺延 C-10010~16")
    check(all(i not in names_now for i in ids), "J1 现库零撞号")
    check(len({c["name"] for c, _, _ in rendered}) == 7, "J1 七名互异")
    existing_names = {r["name"] for r in light_rows_now}
    check(not ({c["name"] for c, _, _ in rendered} & existing_names), "J1 现库零撞名")
    # J2
    for c, text, light in rendered:
        prof = [ln for ln in text.splitlines() if ln.startswith("**职业** ")][0][len("**职业** "):]
        segs = prof.split("——")
        check(len(segs) == 3 and all(segs), f"J2 {c['name']} 职业行双「——」三段齐")
        check("的赛博后身" in segs[1] and "赛博后身" in prof, f"J2 {c['name']} 法定中环「的赛博后身」")
        check(segs[0] == light["profession"], f"J2 {c['name']} 未来形态=light profession")
        check("复古后身" not in prof, f"J2 {c['name']} 新写链非复古白名单族")
        check("赛博后身" in text, f"J2 {c['name']} audit ok 桶口径（卡面显式链）")
    # J3/J4 covered by gates; re-run here for the battery count
    check(run_gates(rendered) == [], "J3/J4 三门全过（红线/生成门/准入）")
    # J5
    need = {"id", "name", "species", "faction", "gender", "age", "age_note", "district",
            "block", "profession", "axis", "creed", "hook", "v", "brain_digest",
            "behavior_hint", "recent_ring", "recent_ring_date"}
    for c, _, light in rendered:
        check(need <= set(light), f"J5 {c['name']} light 字段=白名单闭集齐")
        check(len(light["recent_ring"]) <= 80, f"J5 {c['name']} recent_ring ≤80")
    check(len(light_rows_now) == 10003, "J5 前缀面 10003 行基线")
    # J8 determinism: double render byte-equal
    first = [render_card(c) for c, _, _ in rendered]
    second = [render_card(c) for c, _, _ in rendered]
    check(first == second and first == [t for _, t, _ in rendered], "J8 同输入双跑一致（渲染层）")
    lights = [build_light(c) for c, _, _ in rendered]
    check(json.dumps(lights[0], ensure_ascii=False) == json.dumps(rendered[0][2], ensure_ascii=False),
          "J8 light 行确定性")
    print(f"== mirror_intake --qc: {ok} PASS, {fail} FAIL ==")
    return 0 if fail == 0 else 1

# ---------- apply ----------

def apply(rendered):
    applied = skipped = 0
    for c, text, light in rendered:
        path = os.path.join(REG, c["district"], f"C-{c['num']:05d}.md")
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
    new = [l for l in (json.dumps(build_light(c), ensure_ascii=False) for c, _, _ in rendered)
           if json.loads(l)["id"] not in have]
    if new:
        if not data.endswith(b"\n"):
            data += b"\n"
        data += "".join(n + "\n" for n in new).encode("utf-8")
        with io.open(LIGHT, "wb") as f:
            f.write(data)
    total = len(text_rows.splitlines()) + len(new)
    print(f"mirror_intake applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0

def main():
    # REGISTRY-FREEZE GUARD（CEO P0 2026-09-30 05:38 停造人强冻令升级条款·registry 写冻结）：
    # freeze lock 在盘=镜像居民注册 intake 一律拒跑（--qc 亦拒·先于一切写盘动作）。
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: mirror-resident intake disabled per CEO P0 order 2026-09-30 05:38 (registry-freeze.lock). Unfreeze = CEO order removes the lock. Zero write.")
        sys.exit(4)
    rendered = [(c, render_card(c), build_light(c)) for c in CARDS]
    if "--qc" in sys.argv[1:]:
        with io.open(LIGHT, encoding="utf-8") as f:
            rows = [json.loads(l) for l in f if l.strip()]
        return qc_battery(rendered, rows)
    refusals = run_gates(rendered)
    if refusals:
        for r in refusals:
            print(r)
        print("MIRROR INTAKE REFUSED: zero write")
        return 2
    return apply(rendered)

if __name__ == "__main__":
    sys.exit(main())
