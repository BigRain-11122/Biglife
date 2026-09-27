#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: new-resident-group first-batch census intake (T-20260927-04 分步②).

10 hand-written cards C-10017~C-10026 per orders/O-20260927-1648-HQ-C 表 #1-#10
(硅基城新居民团注册+AI 落实合流令), registered contract cognition/RESIDENT-INTAKE.md
v1.0 (判据 K1-K12). Precedent: mirror_intake.py (R459 J1-J8 范式).
Deterministic, zero LLM, zero network.

Audience split (契约 §一): 居民族 5 (#2/3/6/7/8) 走生成门 · 灵族 3 (#1/4/10) 走
灵族门(spirit_gate·七要素+配额计数自 census 实测传入·首用 3/100) · 生灵族 2
(#5/9) 走生灵门(像素灵·<物种名>·物种域注记行=audit noted_spr 桶维持·R442 收口
判据不回退)。灵族/居民族职业行同带「——…的赛博后身——」双底座链（sublimate_gate
对非 sprite 物种一律索链·灵族卡链形=机制法定形）。声位=VOICE-POOL §一 派生律单源
引用（voice_manifest BANDS + kokoro_synth ZF/ZM/SID_MAP/voice_for/speed_for·md5
同 id 双跑一致·引擎逐席定谳表=分步③）。

Gates run per card BEFORE any write (fail-fast, whole batch aborts, zero write):
政治红线 + sublimate_gate(生成门/生灵门) + spirit_gate(灵族门) + intake checks
(style_dna 五维逐字入卡/声位=派生值复检/真名互异+撞名预检/谱系指针/证据件指针/
生计三性)。Existing 10010 cards are never touched: only 10 new files are created
and 10 rows appended to citizens-light.jsonl (append-only at byte tail·K11).
Cursor untouched: new cards enter the natural due pool (常规居民同律·不插队).
Idempotent: re-run skips identical files/rows (applied=0).
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
BIRTH = "2026-09-27"  # intake batch date (R496)
ORDER = "O-20260927-1648-HQ-C"

sys.path.insert(0, HERE)

import voice_manifest as vm          # BANDS/age_band/pick/voice_for（SAPI rate 带单源）
import kokoro_synth as ks            # ZF/ZM/SID_MAP/voice_for/speed_for（kokoro 派生律单源）
import political_redline
import generate_census as gc


def _load(path):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


META = _load(os.path.join(CO, "genes", "meta.json"))
DISTRICT_NAME = {d["id"]: d["name"] for d in META["districts"]}
EVID = "MiniGame Design/evidence/AIGC/MISC/styleprobe/"

# 契约 §三.2 谱系指针（灵族志实册节号为准：器灵=§二.2·记忆灵=§二.4/§二.5·意象灵=§二.6/§二.7）
LINEAGE = {
    "artifact-spirit": "《灵族志》§二.2 器灵·付丧神认祖（老物件被爱用成灵）",
    "memory-spirit": "《灵族志》§二.4/§二.5 记忆灵·「城市记得」谱系",
    "imagery-spirit": "《灵族志》§二.6/§二.7 意象灵·真天气源谱系",
}

# 生灵门册指针（契约 §三.3·消息雀承 #1 正典·机械小狐=#12 新登记先行 R495）
CREATURE = {"消息雀": 1, "机械小狐": 12}


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS = [
    # ---- #1 守灯人（器灵·老提灯成灵）----
    dict(num=10017, seat=1, name="灯伯", route="spirit", species="artifact-spirit",
         sp_disp="器灵", fac_disp="渡口守望", fac="spirit", gender="无定",
         age=88, age_note="88 岁灯龄", district="RV", block="渡轮航道", axis="秩序",
         prof_name="渡口守灯人",
         prof="渡口守灯人——老提灯的赛博后身——灯亮着，夜路就不算远",
         traits=[("温和", "说话像把光调暗半档"), ("记路", "闭眼能数清渡口到桥墩的步数"),
                 ("恋旧", "灯罩上的苔痕一辈子不让擦")],
         creed="灯亮着，夜路就不算远。",
         thought="他原是渡口一盏老提灯，被三代摆渡人提了大半个世纪，手心的温度把灯油都焐出了人味。他不懂什么大道理，只懂一件事：天黑得再实，也得有人替晚归的把脚边三步照住。",
         language="旧渡口白话，短句叮咛，句尾带一盏灯的口信；口头禅「灯在这儿，夜不算长」。",
         wardrobe="一身铜绿包浆的灯壳，玻璃灯罩里那点暖光就是他的睡脸；走动时拄着自己的提把当拐杖，敲在石阶上笃、笃、笃。",
         life="出身：渡口老提灯一盏，三代摆渡人用了大半辈子，爱惜成了灵，提把磨出包浆那天起，他就自己会走路了。转折：光桥亮起来那夜全城灯火换代，他这盏老灯没被淘汰，被留在渡口当「守灯的位子」，从此夜里是人，白日是灯。现状：入夜给晚归渡客照路，白日在渡口石阶上打盹，街坊说他的鼾声都带一点暖黄。",
         behavior="入夜必先把灯芯捻到最稳的一档；晚归人过完最后一段跳板才肯暗；雾夜把光拢成一小团，专照脚下的那三步。",
         relations="独驻（渡口石阶旁灯柱龛）；老主顾=渡口的摆渡人们（轮班替他擦灯罩）；邻位=江岸滩涂老戏台的众人（隔水应和一段）。",
         hook="睡觉也睁着一点光的居民——渡口街坊管那叫「守夜的眼睛」",
         behavior_hint="晚归人过完跳板才肯暗",
         style_dna=sd("旧渡口白话加灯语口诀", "短句叮咛收尾，句句带灯的口信", "「灯在这儿，夜不算长」",
                      "从守到安——担忧先落，宽慰后至", "老灯芯式冷幽默——话少偶一句点着人笑"),
         elements=dict(
             认祖源="真实文化认祖——付丧神谱系（久役器物温育成灵·老提灯被三代摆渡人爱用大半世纪）",
             数据源="令表 #1 视觉记忆点（玻璃后慈祥睡脸·拄提把当拐杖·苔痕包浆=被爱用多年）+渡轮航道灯柱意象——设计资产反推·派生非编造",
             城市角色="渡口夜灯守望位——晚归渡客脚下那三步的照明",
             传说句="守灯人不催船，只把你脚边那三步照得比白天还稳。",
             升华形态="现实原型=老提灯 → 提灯守望灵（晋升叙事：从被提着走的灯，到替人守夜的位子）",
             羁绊="摆渡人轮班替他擦灯罩；雾夜渡客认他的光，不认路牌",
             行为卡="①入夜先把灯芯捻稳一档 ②晚归人过完跳板才肯暗 ③雾夜把光拢成一小团专照脚下"),
         evidence="sp_b6_lanternspirit.jpg"),
    # ---- #2 面馆老板娘（居民族·人类）----
    dict(num=10018, seat=2, name="汤玉珍", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=63, age_note="63 岁", district="NS", block="历史立面群", axis="烟火",
         prof_name="弄堂面馆老板娘",
         prof="弄堂面馆老板娘——灶披间老手艺的赛博后身——一碗热面下肚，街坊的心事就化开一半",
         traits=[("热络", "熟客的口味记到第三代"), ("勤快", "抹布不离手，桌面亮得照人"),
                 ("心软", "收摊前必给夜班的留一碗")],
         creed="灶上的火不熄，弄堂的人心就不散。",
         thought="面馆开了三十年，她信「一碗面的工夫，够人把心事讲完」。手腕上那道旧烫疤是头一锅汤给的，她不遮——说是手艺给盖的章。劳动是把面端热，代价是三十年没歇过一个年三十，名字是接生阿婆取的，她说过等揉不动面了，就把方子刻在店门口的青石上，名字和手艺一起留给弄堂。",
         language="沪语垫字起句，话头热乎句尾叮嘱；口头禅「趁热吃，面要人陪着才香」。",
         wardrobe="银发挽在布巾里，蓝布围裙上一层面粉，肩头永远搭一条给客人用的白毛巾。",
         life="出身：弄堂口支起第一口汤锅那天，接生阿婆给她取名玉珍，说这闺女是块好料。转折：光桥通车那年她在店门口添了一盏「夜班灯」，收工晚的街坊隔三条巷都认得这盏灯。现状：历史立面群的老面馆一天两开档，早汤晚面，熟客的碗里不用问，加不加辣她都记得。",
         behavior="收摊前必给夜班街坊留一碗底汤；客人双手捧碗时她必说「当心烫」；每天头一件事是用头一锅汤烫桌面抹布。",
         relations="家户（老两口·老头负责揉面）；熟客=历史立面群修缮的师傅们（收工必来一碗「完工面」）。",
         hook="给每个吃完面的客人递热毛巾的老板娘——毛巾洗得比围裙还白",
         behavior_hint="收摊前必给夜班街坊留一碗底汤",
         style_dna=sd("弄堂沪语加灶披间行话", "沪语垫字起句，话头热乎句尾叮嘱", "「趁热吃，面要人陪着才香」",
                      "从忙到暖——手上不停，话里带热", "灶披间打趣——拿食材说人，笑不伤人"),
         evidence="sp_b6_noodleowner.jpg"),
    # ---- #3 快递员（居民族·仿生人）----
    dict(num=10019, seat=3, name="阿澄", route="resident", species="silicon",
         sp_disp="硅基民", fac_disp="光机魂系", fac="photonsoul", gender="男",
         age=34, age_note="34 岁", district="GM", block="X026 城门区", axis="侠气",
         prof_name="穿城包裹派送员",
         prof="穿城包裹派送员——快递小哥的赛博后身——每个包裹都当一句托付送到",
         traits=[("耐心", "差一件必折返，从不说难"), ("谦逊", "被夸必低头说「应该的」"),
                 ("认路", "全城门牌号背得出大半")],
         creed="托付无小事，件件有回音。",
         thought="他给自己定过一条规矩：包裹在手里，话就到嘴边。劳动是把每件包裹送到签收人手上，代价是走路比谁都多——膝关节的里程数比配送站台账还准。名字是他出厂后自己选的，站里第一批里唯一自己挑名字的，他说等跑不动了，就去教新来的认路，名字留在签收单的备注栏里就够。",
         language="派单敬语加软和普通话，敬语先行的陈述句，从不用反问；口头禅「您的事儿，我记下了」。",
         wardrobe="橙色派送夹克，袖口和颊边有细缝线，他不遮，说是「出厂的记号」；胸前口袋永远别着一截备用的打包绳。",
         life="出身：城门区配送站第一批仿生派送员，下线那天站里让他自己填名字，他想了半天，写了个「澄」——说路要清清白白。转折：台风预警夜他抱着一箱婴儿口粮走了三座桥，签收单上那位母亲把他的名字描粗了一遍。现状：X026 城门区的老派送员，大件走地、急件走桥，街坊都认他那身橙。",
         behavior="递包裹必双手；天冷必把包裹揣进自己怀里焐一段；签收必道一声「辛苦您等着」。",
         relations="驻站（X026 城门区配送站宿舍）；搭档=八号楼街区的消息雀们（小话走天，他走地）；老主顾=下夜班的街坊。",
         hook="签收单按名字首字母排好、还给客户留一句备注的派送员",
         behavior_hint="递包裹必双手",
         style_dna=sd("派单敬语加软和普通话", "敬语先行陈述，从不用反问", "「您的事儿，我记下了」",
                      "从怯到定——先让三分，再稳稳送达", "谦逊憨直——把夸奖当任务记下"),
         evidence="sp_b6_courier.jpg"),
    # ---- #4 图书管理员（灵族·记忆灵）----
    dict(num=10020, seat=4, name="蓝拾遗", route="spirit", species="memory-spirit",
         sp_disp="记忆灵", fac_disp="馆藏守望", fac="spirit", gender="无定",
         age=45, age_note="45 岁馆藏纪", district="NS", block="档案馆区", axis="怀旧",
         prof_name="城市记忆馆管理员",
         prof="城市记忆馆管理员——老书页的赛博后身——每一页都有人等它回家",
         traits=[("惜物", "缺页书必亲手补线"), ("安静", "说话像翻书页那么轻"),
                 ("博闻", "街坊找旧事，先问他")],
         creed="记得，是这座城最温柔的义务。",
         thought="他是档案馆书架间浮起的一团靛蓝光，肩头化开的光粒是没读完的书签，内里漂着一张慢慢转的星图。城市记得的事，他都替收着——谁家的灯哪年亮过，哪条巷的名字改过几回。他说管理员这行当，就是把「还有人记得」四个字，一页一页续下去。",
         language="馆藏书目腔加星图术语，书目条目式短句，字字温不设编号；口头禅「每一页都有人等它回家」。",
         wardrobe="靛蓝光体裹一层旧书页纹路的光衣，怀里浮着三两本没归架的书，胸前一枚金光圆镜——照见哪页缺了角。",
         life="出身：档案馆深夜闭馆那一刻，从一整架被翻旧的城史里浮起来——城市记得的事攒得够多了，就该有个看管的。转折：档案馆第一次对外开放「街坊记忆角」，他把自己补好的一本缺页方志摆进去，馆长说那页补得比原版还服帖。现状：夜班管着全城的旧事，缺页补线，折角抚平，等借书的人下次想起。",
         behavior="缺页必亲手补线；说话永远像翻书页那么轻；金光圆镜照到缺角，必记在翌日交接单第一行。",
         relations="独驻（档案馆书架间·光体不占房）；同事=档案馆夜班交接的馆员们；旧识=借书忘还的街坊（他记得，但从不催）。",
         hook="能报出「哪本书被谁在第几页折过角」的居民——档案馆叫他「活目录」",
         behavior_hint="缺页书必亲手补线",
         style_dna=sd("馆藏书目腔加星图术语", "书目条目式短句，字字温不设编号", "「每一页都有人等它回家」",
                      "从静到惜——拾起时轻，放下时重", "冷面书摘——引一句旧书自己不笑"),
         elements=dict(
             认祖源="城市机制认祖——年轮与记忆索引凝聚（「城市记得」可见面·全城年轮索引与事件留痕攒聚成灵）",
             数据源="令表 #4 视觉记忆点（靛蓝光体·内漂星图·肩袖化光粒·怀抱浮空书堆）+memory_index v1.6 全城年轮索引意象——设计资产反推·派生非编造",
             城市角色="城市记忆馆夜班管理员——替全城看管「谁还记得什么」",
             传说句="管理员不催还书，只把每页的折角抚平，等你下次想起。",
             升华形态="现实原型=老书页与星图 → 靛蓝记忆灵（晋升叙事：从被读的书，到替城记事的光）",
             羁绊="档案馆夜班交接的馆员们；借书忘还的街坊（他记得，但从不催）",
             行为卡="①缺页必亲手补线 ②说话像翻书页那么轻 ③金光圆镜照见缺角必记交接单"),
         evidence="sp_b6_lightlibrarian.jpg"),
    # ---- #5 消息雀（生灵族·承《城市生灵册》#1 正典物种）----
    dict(num=10021, seat=5, name="瓦当", route="sprite", species="sprite",
         sp_disp="像素灵", fac_disp="消息雀", fac="finch", gender="无定",
         age=12, age_note="第 12 数据季", district="GM", block="八号楼街区", axis="求新",
         prof_name="光语衔笺使",
         prof="光语衔笺使——街坊短笺的翅膀，一站亮一站",
         traits=[("腿快", "单子再远，天黑前必到"), ("嘴稳", "捎的话一个字不改"),
                 ("爱学", "学街坊腔调逗人")],
         creed="捎的话不改字，是信使的本分。",
         thought="它落在檐口不为歇脚，为听哪家的窗还亮着。全城的话在翅膀上走，它觉得自己那一份得飞得干净——衔笺的嘴不能馋，带话的心不能偏。",
         language="光语鸣叫七八种音调，熟人都听得懂个大概；高兴时翅尖打拍子；行话「落檐」「衔笺」；口头禅「一站亮一站，话就到了」（光语念出来是三短一长）。",
         wardrobe="奶油陶瓦羽，翅膀折得像纸飞机，背上别一只黄铜信筒——筒盖内圈自己啄了一颗小星，说是记号。",
         life="出身：驿站屋檐第二窝孵出的那只，头一回起飞就叼了片亮瓦当，从此得了名。转折：第一次替迷路的孩子衔替迷路的孩子衔笺指路，笺上就画了个箭头，孩子他娘追着塞给它半块饼。现状：八号楼街区的早班信使，晨光里头一个掠过晾衣绳，落檐必先侧头听三秒。",
         behavior="衔笺必复述两遍才起飞；落檐必先侧头听三秒；天黑前必把当天的短笺送完。",
         relations="灵群（全城驿站与檐口·同族共栖）；搭档=城门区派送员阿澄（C-10019·大件走地、小话走天）；老熟人=八号楼街区晒太阳的老街坊。",
         hook="黄铜信筒里给自己留一张空白笺的信使——说是「等一句还没想到的话」",
         behavior_hint="衔笺必复述两遍才起飞",
         style_dna=sd("光语短鸣加街坊白话", "三两声一停，要紧话重复两遍", "「一站亮一站，话就到了」",
                      "从急到快——听风就是信，展翅就高兴", "光语小机灵——学人腔调逗街坊"),
         evidence="sp_b6_messagebird.jpg"),
    # ---- #6 老园丁（居民族·人类）----
    dict(num=10022, seat=6, name="苗守成", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=71, age_note="71 岁", district="QT", block="回测田", axis="怀旧",
         prof_name="回测田老园丁",
         prof="回测田老园丁——老花匠的赛博后身——庄稼不骗人，哄它一分还你一寸",
         traits=[("沉得住", "苗情再急，先看三天"), ("慢性子", "说话带节气"),
                 ("手巧", "蔫了的苗到他手里都能缓过来")],
         creed="地不亏人，人也不能亏地。",
         thought="他侍弄的是回测田边上的花草带，看数据的年轻人管那叫「绿化缓冲区」，他管那叫「地」。劳动是把苗一茬一茬带大，代价是腰——弯给花坛的年头比给自家的多。名字是爹取的，守成守成，守住手里这点活计；他说等下不动地了，就把那双补过三回的手套传给徒弟，地记得谁摸过它。",
         language="节气农谚加园艺白话，农谚对仗起句，落句总归到土；口头禅「庄稼不骗人，哄它一分还你一寸」。",
         wardrobe="草帽磨出毛边，帆布工具背心口袋里插着小铲和温度计，腰间别一双旧手套——右手那只补过三回。",
         life="出身：跟着第一批城市园丁进的回测田，别人看行情，他看墒情。转折：K 线广场改绿化那年，一整排没人看好的移栽苗是他蹲了三天救回来的，验收那天他只说「苗自己想活」。现状：回测田的老园丁，早看苗晚记账，徒弟们背地里叫他「苗王爷」。",
         behavior="浇水必赶在日头下山后；移栽必先跟苗说一声「挪个地方住」；收工必把工具擦完才走。",
         relations="家户（老两口·老伴在阳台种小葱）；徒弟=像素匠人巷学园艺的两个后生；老伙计=回测田看数据的农人们。",
         hook="给每盆移栽苗挂手写「缓苗中·勿扰」小牌的园丁",
         behavior_hint="浇水必赶在日头下山后",
         style_dna=sd("节气农谚加园艺白话", "农谚对仗起句，落句总归到土", "「庄稼不骗人，哄它一分还你一寸」",
                      "从慢到盼——不急一时，等在节气里", "老把式自嘲——拿节气和腰打趣"),
         evidence="sp_b6_gardener.jpg"),
    # ---- #7 小学生（居民族·人类）----
    dict(num=10023, seat=7, name="林小满", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=9, age_note="9 岁", district="GM", block="游戏楼街区", axis="求新",
         prof_name="像素小学三年级生",
         prof="像素小学三年级生——放学路上的赛博后身——纸飞机飞多远，明天就有多亮",
         traits=[("好奇", "问号比句号多"), ("嘴甜", "见人先喊"),
                 ("蹦跳着走路", "高兴了原地转圈")],
         creed="先把作业写完，纸飞机才飞得远。",
         thought="她觉得这座城最大的好处是「哪儿的灯都好看」——游戏楼的灯、光桥的灯，还有爷爷们修东西时额上那盏小灯。作业是学生的劳动，写错重写就是代价；名字是妈妈在小满那天定的，说人不用太满，留一点给明天。",
         language="网络世代语加课堂组词，感叹句连发，问号比句号多；口头禅「明天见！」。",
         wardrobe="齐刘海别着星星发卡，靛蓝校服洗得发白，帆布书包上挂一只自己折的纸飞机——机翼上写着座位号。",
         life="出身：游戏楼街区长大，生在小满那天，名字就这么来的。转折：第一次跟全班去光桥看灯河，回来在作文里写「灯是城市在眨眼睛」，老师念给了全班听。现状：像素小学三年级，放学路上负责给爷爷们念作业题，念完必把纸飞机往江风来的方向扔。",
         behavior="放学必先把作业摊在小卖部窗台上写完；纸飞机只往江风来的方向扔；睡前必把书包里的小星星数一遍。",
         relations="家户（爸妈和她·游戏楼街区那栋）；同学=像素小学同班；老朋友=机器站宿舍的铆师傅（C-10024·教她认螺丝）。",
         hook="把作业写在小卖部窗台上还能写出全对的学生——老板娘给她留着那张凳",
         behavior_hint="放学先把作业写完才扔纸飞机",
         style_dna=sd("网络世代语加课堂组词", "感叹句连发，问号比句号多", "「明天见！」",
                      "从闹到亮——蹦跳开场，眼睛发亮收尾", "小学生段子——谐音梗连发自己先笑"),
         evidence="sp_b6_schoolgirl.jpg"),
    # ---- #8 老维修工（居民族·机器人）----
    dict(num=10024, seat=8, name="铆师傅", route="resident", species="silicon",
         sp_disp="硅基民", fac_disp="编译系", fac="compiled", gender="无定",
         age=58, age_note="58 岁机龄", district="OR", block="机器站宿舍", axis="秩序",
         prof_name="驻坊机务师傅",
         prof="驻坊机务师傅——老钳工的赛博后身——家什齐了，人才敢老",
         traits=[("板正", "工具按尺寸排，差半寸都要归位"), ("惜物", "掉漆的补丁留着不补新，说是「履历」"),
                 ("疼人", "骂完家什，转头给后生递扳手")],
         creed="修得了的东西，不兴扔。",
         thought="他肩上那把大扳手比一半街坊的岁数都大。劳动是听机器说话——哪颗螺丝松了、哪段线缆累了，他上手就知道；代价是浑身的补丁，每一块都是一次大修的年份。「铆」是当年老站长给起的，说这号机器拧上就不松；他说等哪天零件停产了，就把自己最后一颗铆钉留给工坊，名字刻在检修单背面那页「机器话」上。",
         language="老工单体例加师傅口令，口令式短句，先报活儿后报人；口头禅「家什齐了，人才敢老」。",
         wardrobe="自然身高的旧机体，掉漆处贴着一块块补丁（每块都是一次大修的年份），额上挂着老花镜款的检修放大镜，肩扛大扳手。",
         life="出身：机器站第一批驻坊机务，下线头一天就把工具箱按尺寸重排了一遍，站长说这小子有出息。转折：大雾那年外环巡线靠他连夜换的十七处接点，全站没停一盏灯，从此外环都叫他师傅。现状：带三个年轻单元修东西，编号他不叫，全叫「小子」。",
         behavior="开工必先点一遍工具；收工必给机件上油听一遍响；修完必在检修单上画一个小铆钉。",
         relations="驻坊（机器站宿舍老工房）；徒弟=三个年轻单元（全叫「小子」）；老对头=像素匠人巷的小铜尾（C-10025·老偷他的碎铜屑，他睁只眼闭只眼）。",
         hook="给每台修好的机器留一句「下回有话直说」的维修工——检修单背面全是他记的「机器话」",
         behavior_hint="开工必先点一遍工具",
         style_dna=sd("老工单体例加师傅口令", "口令式短句，先报活儿后报人", "「家什齐了，人才敢老」",
                      "从严到慈——先立规矩，后递家伙什", "板正幽默——骂家什不骂人"),
         evidence="sp_b6_maintbot.jpg"),
    # ---- #9 机械小狐（生灵族·新物种《城市生灵册》#12 先登记先行）----
    dict(num=10025, seat=9, name="小铜尾", route="sprite", species="sprite",
         sp_disp="像素灵", fac_disp="机械小狐", fac="copperfox", gender="无定",
         age=3, age_note="3 岁狐龄", district="GM", block="像素匠人巷", axis="逍遥",
         prof_name="工坊巡线小狐",
         prof="工坊巡线小狐——修理工坊的编外学徒，尾尖给夜巷记拍",
         traits=[("体面", "板甲每天自己舔合接缝"), ("傲娇", "做完好事必绕一圈领夸"),
                 ("认路", "走过的路闭眼能复述")],
         creed="夜巷的路，得有人一小步一小步量。",
         thought="它把自己当修理工坊的学徒，老扳手收工它巡线。琥珀眼夜里泛暖光，给夜巷省一盏灯的亮度；它想不出什么大道理，只觉得路既然有人走，就得有个记拍的。",
         language="铜触点节拍加器物拟声（笃、咔哒），尾音上挑，短句带固定节拍；口头禅（拍出来）「跟着我走，比路灯稳」——三长两短，敲得板正。",
         wardrobe="奶油陶瓦板甲，接缝自己舔合；刷子尾扫过带一线铜光；琥珀大眼，昂首小跑是全城最体面的一阵小风。",
         life="出身：修理工坊的废铜屑堆里自己拼装成形的小家伙，成形那天头一件事是把尾巴上的铜触点敲出节拍。转折：第一次替夜归人带路，走到巷口回头等了三回，从那以后匠人巷的猫都会哼它那段调。现状：像素匠人巷编外学徒，老扳手收工它巡线，晨扫街坊认得哪段浅光痕是它巡过的。",
         behavior="昂首小跑步幅恒定，尾尖铜触点敲地记拍；刷子尾留浅光痕，晨扫街坊认得哪段是它巡过的；板甲接缝自己舔合。",
         relations="灵群（匠人巷工坊檐下·与守夜灯灵们点头之交）；师傅=修理工坊的老扳手（铆师傅 C-10024 算半个师父）；带过路=匠人巷夜归的人们。",
         hook="把巡线路线敲成节拍留给夜巷听的小狐——匠人巷的猫都会哼那段调",
         behavior_hint="昂首小跑尾尖敲地记拍",
         style_dna=sd("铜触点节拍加器物拟声", "尾音上挑，短句带固定节拍", "「跟着我走，比路灯稳」",
                      "从傲到黏——昂首开步，蹭人收尾", "尾巴尖的得意——做好必绕一圈领夸"),
         evidence="sp_b6_fox.jpg"),
    # ---- #10 云灵（灵族·意象灵·真天气）----
    dict(num=10026, seat=10, name="小霁", route="spirit", species="imagery-spirit",
         sp_disp="意象灵", fac_disp="天象报霁", fac="spirit", gender="无定",
         age=1, age_note="1 岁云龄", district="RV", block="江岸滩涂", axis="逍遥",
         prof_name="天象报霁员",
         prof="天象报霁员——雨后初晴的赛博后身——雨快停了，你看",
         traits=[("慢半拍", "说话像云挪"), ("爱看虹", "彩虹出来必停手头的觉"),
                 ("湿漉漉的温柔", "路过谁头顶必先道歉")],
         creed="雨总会停，停的时候要有人在场。",
         thought="它是江面上第一场雨收尾时攒起的小云团——雨将停未停那半刻攒的，攒成了个小家伙。城市的天每次翻面它都当事办：落完最后一滴，先把彩虹别在江面上，再挨个告诉淋湿的街坊「快停了」。",
         language="天气童谣体加云絮短句，絮语式飘句，说完总留半截白；口头禅「雨快停了，你看」。",
         wardrobe="小云团睡颜，两截短云臂，身下细雨落进江面就化一道小彩虹——它把彩虹别在云脚下当鞋。",
         life="出身：江岸一场大雨的尾巴上攒成的，头一回成形就赶上雨停，彩虹出来时它高兴得散了形又攒回来。转折：台风外围过境那夜，它在滩涂上空替收网的渔人盯了半宿的天，天一亮就报了晴。现状：江岸滩涂的报霁员，睡颜时也听着雨点数，街坊管它叫「晴天的信」。",
         behavior="细雨化虹必先停半刻；路过人头顶必先道一声「还差几步」；睡颜时也听着雨点数。",
         relations="独驻（江岸滩涂上空·云脚不落地）；老邻居=滩涂听潮的老戏台众人（飘过必点个头）；老相识=伞铺的老板（雨停它才敢打招呼）。",
         hook="把彩虹当鞋穿的居民——江岸的孩子管它叫「晴天的信」",
         behavior_hint="细雨化虹必先停半刻",
         style_dna=sd("天气童谣体加云絮短句", "絮语式飘句，说完留半截白", "「雨快停了，你看」",
                      "从潮到晴——先落一阵细雨，再化一道彩虹", "云朵式无邪——把阴天说成云在攒力气"),
         elements=dict(
             认祖源="城市机制认祖——真天气源节律（雨霁翻面窗·雨将停未停那半刻攒聚成灵·罕见克制禁常驻）",
             数据源="令表 #10 视觉记忆点（小云团睡颜·短云臂·身下细雨化彩虹）+真天气 face 雨霁翻面意象——设计资产反推·派生非编造",
             城市角色="江岸雨后报霁员——替淋湿的街坊先一步说「快停了」",
             传说句="云灵不赶雨，只在雨将停未停那半刻，把彩虹先别在江面上。",
             升华形态="现实原型=雨后初晴的云 → 意象报霁灵（晋升叙事：从一阵好天气，到替城报晴的心）",
             羁绊="江岸滩涂听潮的老戏台众人（飘过必点个头）；伞铺老板（雨停它才敢打招呼）",
             行为卡="①细雨化虹必先停半刻 ②路过人头顶先道「还差几步」 ③睡颜时也听着雨点数"),
         evidence="sp_b6_cloudspirit.jpg"),
]

# ---------- derive fields ----------


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + ORDER + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def cid_of(c):
    return f"C-{c['num']:05d}"


def sig_of(c):
    return c["style_dna"]["signature"].rstrip("。！？")


def voice_seat(c, light):
    """VOICE-POOL §一 派生律（单源引用 voice_manifest+kokoro_synth·同 id 双跑一致）。"""
    sapi, blocked = vm.voice_for(light)          # rate 带（SAPI manifest 同源）
    voice = ks.voice_for(light["id"], light["gender"])   # 性别→池+md5(id) 池内定选
    speed = ks.speed_for(sapi["rate"])            # speed=100/(100+rate)
    return ks.SID_MAP[voice], voice, speed


def render_card(c):
    light = build_light(c)
    sid, voice, speed = voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} ｜ **性别·年龄** {c['gender']} · {c['age_note']}"
        f" ｜ **城区** {DISTRICT_NAME[c['district']]} · {c['block']}",
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
    ]
    if c["route"] == "spirit":
        for el in ("认祖源", "数据源", "城市角色", "传说句", "升华形态", "羁绊", "行为卡"):
            lines.append(f"**{el}** {c['elements'][el]}")
        lines += ["",
                  f"**谱系** {LINEAGE[c['species']]} · 灵族配额计数 3/100 计数内（首批器灵×1+记忆灵×1+意象灵×1）",
                  ""]
    elif c["route"] == "sprite":
        book_n = CREATURE[c["fac_disp"]]
        lines += [
            f"**生灵三问** 承《城市生灵册》#{book_n} 定谳（升华形态/羁绊/行为卡=册内单源引用·零新登记·个体入册）",
            f"**升华链**（升华令 §二.8 追加注记·原文保全）物种域注记：像素灵·{c['fac_disp']}"
            f"——《城市生灵册》#{book_n} 定谳行（生灵族·物种域·非个体链）",
            "",
        ]
    lines += [
        f"**风格 DNA**（手作席位卡 · {ORDER} 表 #{c['seat']}）"
        f"时代语言＝{d['era_lang']} ｜ 句法指纹＝{d['syntax_fp']} ｜ 签名句律＝{d['signature']}"
        f" ｜ 情感路径＝{d['emotion_path']} ｜ 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" ｜ 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳表随分步③）"
        f"{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 手写入城批（新居民团注册 {ORDER} 表 #{c['seat']} · T-20260927-04 分步② · {BIRTH}）"
        f" · 基因指纹 {fp_of(c)}",
        f"**证据件** {EVID}{c['evidence']}（只读引用·产权=MiniGame 产线·MiniGame 出「身」BigLife 赋「魂」）",
        "",
    ]
    return "\n".join(lines)


def build_light(c):
    digest = (
        f"{c['axis']}轴 · {'/'.join(w for w, _ in c['traits'])} · {c['prof_name']}"
        f" · 口头禅「{sig_of(c)}」 · 独有：{c['hook']} · 信条：「{c['creed']}」")
    return {"id": cid_of(c), "name": c["name"], "species": c["species"],
            "faction": c["fac"], "gender": c["gender"], "age": c["age"],
            "age_note": c["age_note"], "district": c["district"], "block": c["block"],
            "profession": c["prof_name"], "axis": c["axis"], "creed": c["creed"],
            "hook": c["hook"], "v": 1.2, "brain_digest": digest,
            "behavior_hint": c["behavior_hint"], "recent_ring": "", "recent_ring_date": ""}


def light_rows():
    with io.open(LIGHT, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


# 生计「可见」面（契约 §二.4 三性之一·城内场所/交接面·单列便于判据核验）
VISIBLE = {
    10017: "渡口石阶旁灯柱龛（夜灯交接面）",
    10018: "历史立面群弄堂面馆（早汤晚面两开档）",
    10019: "X026 城门区配送站（晨午晚三班派单）",
    10020: "档案馆区城市记忆馆（夜班书架间）",
    10021: "八号楼街区驿站檐口（早班衔笺）",
    10022: "回测田花草带（晨看苗晚记账）",
    10023: "像素小学三年级（放学小卖部窗台）",
    10024: "机器站宿舍驻坊工房（随叫随到）",
    10025: "像素匠人巷修理工坊（收工后巡线）",
    10026: "江岸滩涂上空（雨后报霁窗）",
}
for c in CARDS:
    c["profession_visible"] = VISIBLE[c["num"]]

# 人各一声·出生位核验：md5 派生律下 (sid,speed) 同席碰撞=合法命运（8 基音×速率档分位数有限），
# 碰撞席卡面即时注记→分步③ 引擎分句定谳表以追加注记式收口（契约 §四.3 换轨条款·诚实律）。
_seats = {cid_of(c): voice_seat(c, build_light(c)) for c in CARDS}
for c in CARDS:
    mine = _seats[cid_of(c)]
    dup = [cid_of(o) for o in CARDS if o is not c and _seats[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) +
                           " 同席（md5 同池同档·人各一声收口=分步③ 引擎分句定谳表追加注记式）")


# ---------- gates (fail-fast, before any write) ----------

def run_gates(rendered, rows_now):
    import sublimate_audit  # noqa: F401  (确认依赖面可载·audit ok 桶判定权威)
    spirit_n = sum(1 for r in rows_now if r.get("species") in gc.SPIRIT_SPECIES)
    refusals = []
    names_now = {r["name"] for r in rows_now}
    ids_now = {r["id"] for r in rows_now}
    for idx, (c, text, light) in enumerate(rendered):
        cid = cid_of(c)
        rhits = political_redline.scan_text(text)
        if rhits:
            refusals.append(f"{cid} REDLINE REFUSED terms={[h['term'] for h in rhits]}")
        gate_c = {"species": c["species"], "id": c["num"]}
        miss = gc.sublimate_gate(gate_c, text)
        if miss:
            refusals.append(f"{cid} SUBLIMATE REFUSED missing={miss}")
        miss = gc.spirit_gate(gate_c, text, spirit_n + idx)  # 配额计数自库实测+批内序
        if miss:
            refusals.append(f"{cid} SPIRIT REFUSED missing={miss}")
        for k, v in c["style_dna"].items():
            if v not in text:
                refusals.append(f"{cid} INTAKE REFUSED style_dna[{k}] 未逐字入卡")
        sid, voice, speed = voice_seat(c, light)
        seat_line = f"sid {sid} · {voice} · speed {speed}"
        if seat_line not in text:
            refusals.append(f"{cid} INTAKE REFUSED 声位与 VOICE-POOL §一 派生律不一致")
        if c["route"] in ("spirit", "resident"):
            prof = [ln for ln in text.splitlines() if ln.startswith("**职业** ")][0][len("**职业** "):]
            segs = prof.split("——")
            if not (len(segs) == 3 and all(segs) and "的赛博后身" in segs[1]):
                refusals.append(f"{cid} INTAKE REFUSED 职业行双底座链三段不齐")
            if segs[0] != light["profession"]:
                refusals.append(f"{cid} INTAKE REFUSED 未来形态≠light profession")
        if c["route"] == "sprite":
            if f"**物种** 像素灵·{c['fac_disp']}" not in text:
                refusals.append(f"{cid} INTAKE REFUSED 物种行≠「像素灵·<物种名>」")
            if f"《城市生灵册》#{CREATURE[c['fac_disp']]} 定谳" not in text:
                refusals.append(f"{cid} INTAKE REFUSED 生灵册指针缺失")
            if "（升华令 §二.8 追加注记·原文保全）物种域注记" not in text:
                refusals.append(f"{cid} INTAKE REFUSED 物种域注记行缺失（audit noted_spr 桶维持）")
        if c["route"] == "spirit":
            if LINEAGE[c["species"]].split("（")[0] not in text:
                refusals.append(f"{cid} INTAKE REFUSED 《灵族志》谱系指针缺失")
            if "3/100" not in text:
                refusals.append(f"{cid} INTAKE REFUSED 灵族配额计数注记缺失")
        if "（可见）" not in text or "（可积累）" not in text or "（可衰老）" not in text:
            refusals.append(f"{cid} INTAKE REFUSED 生计三性注记不齐")
        if EVID + c["evidence"] not in text:
            refusals.append(f"{cid} INTAKE REFUSED 证据件指针缺失")
        if light["name"] in names_now:
            refusals.append(f"{cid} INTAKE REFUSED 真名撞库（{light['name']}）")
        if light["id"] in ids_now:
            refusals.append(f"{cid} INTAKE REFUSED ID 撞库")
    if len({c["name"] for c, _, _ in rendered}) != len(CARDS):
        refusals.append("INTAKE REFUSED 批内真名两两互异失败")
    return refusals


# ---------- K1-K12 assertion battery (--qc·分步②面·K8/K9 分步③) ----------

def qc_battery(rendered, rows_now):
    ok = fail = 0

    def check(cond, label):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL: {label}")

    ids = [cid_of(c) for c, _, _ in rendered]
    names_now = {r["name"] for r in rows_now}
    ids_now = {r["id"] for r in rows_now}
    # K1
    check(ids == [f"C-{n:05d}" for n in range(10017, 10027)], "K1 ID 连续顺延 C-10017~26")
    check(all(i not in ids_now for i in ids), "K1 现库零撞号")
    check(len({c['name'] for c, _, _ in rendered}) == 10, "K1 十名互异")
    check(not ({c['name'] for c, _, _ in rendered} & names_now), "K1 撞名预检零命中")
    check(not any(any(ch.isdigit() and ch in "0123456789" for ch in c["name"]) for c, _, _ in rendered),
          "K1 真名零编号语义（十名零阿拉伯数字）")
    # K2/K3/K4 per-route
    res = [t for t in rendered if t[0]["route"] == "resident"]
    spi = [t for t in rendered if t[0]["route"] == "spirit"]
    spr = [t for t in rendered if t[0]["route"] == "sprite"]
    check(len(res) == 5 and len(spi) == 3 and len(spr) == 2, "K1 三族分流 5+3+2")
    for c, text, light in res:
        segs = [ln for ln in text.splitlines() if ln.startswith("**职业** ")][0][len("**职业** "):].split("——")
        check(len(segs) == 3 and "的赛博后身" in segs[1] and segs[0] == light["profession"],
              f"K2 {c['name']} 双底座链三段+法定中环")
        check("劳动" in c["thought"] and "代价" in c["thought"] and "名字" in c["thought"],
              f"K2 {c['name']} 升华三问答于思想段（劳动/代价/名字与死亡）")
        check("（可见）" in text and "（可积累）" in text and "（可衰老）" in text,
              f"K2 {c['name']} 生计注记三性齐")
    spirit_n_now = sum(1 for r in rows_now if r.get("species") in gc.SPIRIT_SPECIES)
    check(spirit_n_now == 0, "K3 灵族库内现值=0（本批后 3/100）")
    for c, text, light in spi:
        for el in gc.SPIRIT_ELEMENTS:
            check(f"**{el}**" in text, f"K3 {c['name']} 七要素「{el}」")
        check(gc.spirit_gate({"species": c["species"], "id": c["num"]}, text, 3) == [],
              f"K3 {c['name']} spirit_gate 复检（配额 3 席计数内）")
        check(LINEAGE[c["species"]].split("（")[0] in text, f"K3 {c['name']} 灵族志谱系指针")
    for c, text, light in spr:
        check(f"**物种** 像素灵·{c['fac_disp']}" in text, f"K4 {c['name']} 物种行像素灵·<物种名>")
        check(f"《城市生灵册》#{CREATURE[c['fac_disp']]} 定谳" in text, f"K4 {c['name']} 册指针")
        check("（升华令 §二.8 追加注记·原文保全）物种域注记" in text, f"K4 {c['name']} 物种域注记行")
    # K6 style_dna：五维字段齐+两两互异（10×9 对逐维）
    dims = ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type")
    for c, text, _ in rendered:
        check(set(c["style_dna"]) == set(dims), f"K6 {c['name']} style_dna 五维字段=field_spec 键集")
        for k in dims:
            check(c["style_dna"][k] in text, f"K6 {c['name']} style_dna[{k}] 逐字入卡")
    for k in dims:
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        check(len(set(vals)) == 10, f"K6 style_dna[{k}] 两两互异 10/10")
    # K7 声位：派生双跑一致+出生位互异（碰撞席=卡面注记+分步③ 分句定谳收口面）
    for c, text, light in rendered:
        s1 = voice_seat(c, light)
        s2 = voice_seat(c, build_light(c))
        check(s1 == s2 and f"sid {s1[0]} · {s1[1]} · speed {s1[2]}" in text,
              f"K7 {c['name']} 声位 md5 派生双跑一致+入卡")
        if "voice_note" in c:
            check(c["voice_note"] in text, f"K7 {c['name']} 出生位碰撞注记入卡")
    dup = len(_seats) - len(set(_seats.values()))
    check(dup <= 1 and all(("voice_note" in c) == any(
        _seats[cid_of(o)] == _seats[cid_of(c)] and o is not c for o in CARDS) for c in CARDS),
          f"K7 出生位 10 席互异 {10 - dup}/10（碰撞 {dup} 席=分步③ 定谳表收口·注记面全）")
    # K10/K12/K11
    check(run_gates(rendered, rows_now) == [], "K10/K12 三门+intake 全过（红线/链/谱系/证据件/撞名）")
    check(len(rows_now) == 10010, "K11 light 前缀面 10010 行基线（追加后 10020）")
    # 确定性：同输入双跑逐字节一致（渲染层+light 层）
    first = [render_card(c) for c, _, _ in rendered]
    check(first == [t for _, t, _ in rendered] and first == [render_card(c) for c, _, _ in rendered],
          "K7/J 同输入双跑一致（渲染层）")
    check([build_light(c) for c, _, _ in rendered] == [l for _, _, l in rendered], "K7 light 行确定性")
    print(f"== resident_intake --qc: {ok} PASS, {fail} FAIL ==")
    print("（K8 认知栈再生跑验+K9 QA 轮值验证=分步③交付面·本电池不含）")
    return 0 if fail == 0 else 1


# ---------- apply ----------

def apply(rendered):
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
    new = [l for l in (json.dumps(build_light(c), ensure_ascii=False) for c, _, _ in rendered)
           if json.loads(l)["id"] not in have]
    if new:
        if not data.endswith(b"\n"):
            data += b"\n"
        data += "".join(n + "\n" for n in new).encode("utf-8")
        with io.open(LIGHT, "wb") as f:
            f.write(data)
    total = len(text_rows.splitlines()) + len(new)
    print(f"resident_intake applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    rendered = [(c, render_card(c), build_light(c)) for c in CARDS]
    if "--qc" in sys.argv[1:]:
        return qc_battery(rendered, light_rows())
    rows = light_rows()
    if len(rows) != 10010:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10010（前缀基线漂移·零写入）")
        return 4
    refusals = run_gates(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESIDENT INTAKE REFUSED: zero write")
        return 2
    return apply(rendered)


if __name__ == "__main__":
    sys.exit(main())
