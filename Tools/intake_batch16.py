#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十四 intake 5 席碳源居民 C-10086~C-10090（T-20261010-03）。

法源：CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders·commit 63ccfaba）
→ T-20261010-03 受控复产（分批律·节奏本司自主定）。先例族：intake_batch3~15。

本批=量产第十四批·复产批十四 5 席（卫振山/温玉娥/邵采莲/都德水/彭照年）——原料按现库
（ho#696-700 + tp#523-527 共 10 条·2026-10-20 基因轮备料·三轮近重预检后 CLEAN），先登记后使用律。

异面注记：夜班值守 vs C-10079 罗守灯（一个守摊位，一个守楼道）；家电修理 vs C-10083 裘守义
（一个修伞骨，一个修电器）；豆腐摊 vs 早点铺（一个凌晨磨浆一个凌晨蒸笼——见现有镇民）；
司炉工 vs C-10081 苏长庚（一个守电路的线，一个守煤火的压）；灯笼铺主 vs C-10085 缪水生
（一个在岸上挂灯，一个在水上收线）。

K12 面 = 常规生成管线注册（非新物种扩容）。证据件 = 基因库原料指针：
·genes/lives.json 1-based #hook_objects-696..700 + #turning_points-523..527

Gates（写盘前 fail-fast·任一不过 → 整批拒收零写入）: 政治红线 + sublimate_gate +
spirit_gate + style_dna 五维逐字入卡 + 声位派生复检 + 双底座链三段 + 生计三性 +
基因库证据件指针 + 真名/ID/钩子撞库 + 批内真名互异 + 批内 style_dna 两两互异。
存量 10079 卡零触碰；light append-only；cursor 不插队。
批后收口步：needs→behavior→rows 对齐断言（POST_LIGHT=10084）。
Idempotent: 再跑对一致文件 → skip（applied=0）。
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

import resident_intake as ri          # 先例族单源
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"
BATCH = "复产批十四"
MAX_ID = 10085                         # 现存最大号（K1 连续顺延上界=批十三尾席）
PRE_LIGHT = 10079                      # 批前 light 断言
POST_LIGHT = 10084                     # 批后 light 断言（10079+5）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS16 = [
    # ---- #1 楼群夜班值守员（碳基·原生代·OR·守时轴）----
    dict(num=10086, seat=1, name="卫振山", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=58, age_note="58 岁", district="OR", block="旧楼一层值班室",
         axis="守时",
         prof_name="楼群夜班值守员",
         prof="楼群夜班值守员——老楼夜里打更守门的更夫的赛博后身——"
              "整宿值班的第一夜，手电筒始终摆在窗台正中，天亮收工才关掉",
         traits=[("守时", "交接班差一分钟都要在门口等着"),
                 ("记人", "哪户几点回家，他心里有一张不写出来的表"),
                 ("巡细", "楼道尽头和地下室拐角，一夜必走满三趟")],
         creed="门开着，灯就亮着",
         thought="劳动是替外环感知网的老楼把整夜的门口守住——监控再全，楼道尽头那道拐角和地下室的那盏灯，"
                 "还得有人夜里亲自走一遍；他把门守住，晚归的人才敢安心上楼，早起的人才不用摸黑出门；"
                 "代价是常年倒作息落下的胃病，冬天在岗亭里坐一夜，膝盖凉得像两块石头；家里人说这活熬人，"
                 "他总说等这栋楼换了新岗再退；名字是父亲按族谱取的，振山两个字，说是守门的人得站得住；"
                 "他说等守不动夜了，就把那支老手电交给肯学的年轻人，教他们先照楼道尽头再照脚下",
         language="老岗亭腔，字短，句尾落地，开口先报时间，常把整夜说成没多大事。"
                  "口头禅「夜里我都在」",
         wardrobe="深蓝保安棉袄外罩一件旧马甲，胸前别着号牌，桌上摆着一支磨花的手电和一把缺齿的铝梳",
         life="出身：老楼里长大的孩子，父亲在楼下看门，他放学后蹲在岗亭里写作业。"
              "转折：整宿值班的第一夜，手电筒始终摆在窗台正中，天亮收工才关掉。"
              "现状：值班室桌角放着那把缺齿的铝梳，齿缝里夹着一根没清掉的短头发，他交班前总要梳一遍头；"
              "同楼=C-10081 苏长庚（一个守电路，一个守大门）",
         behavior="交接班必先用手电照一遍楼道尽头；巡楼必从顶层往下走；天亮交班前必把门口地垫拍两下",
         relations="住旧楼一层值班室隔壁的小间（窗台摆着手电的备用电池）；"
                   "同楼=C-10081 苏长庚，两人夜里隔着楼道打过招呼；常替他留门=晚归的住户",
         hook="一把缺齿的铝梳，齿缝里卡着一根没清掉的短头发，他梳完总把梳子倒过来在掌心磕两下"
              "——就放在值班室桌角，谁进岗亭都看得见",
         behavior_hint="交接班必先用手电照一遍楼道尽头",
         style_dna=sd("老岗亭腔，字短，句尾落地",
                      "先报时后报事，一句一顿",
                      "夜里我都在",
                      "从熬到踏实——一夜巡到天亮",
                      "闷声打趣——拿自己的瞌睡说事"),
         gene_evidence="genes/lives.json#hook_objects-696（一把缺齿的铝梳，齿缝里卡着一根没清掉的短头发，他梳完总把梳子倒过来在掌心磕两下。）"
                       "+ #turning_points-523（整宿值班的第一夜，手电筒始终摆在窗台正中，天亮收工才关掉。）"),
    # ---- #2 家电修理铺主（碳基·原生代·QT·惜物轴）----
    dict(num=10087, seat=2, name="温玉娥", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=44, age_note="44 岁", district="QT", block="计量新村巷口修理铺",
         axis="惜物",
         prof_name="家电修理铺主",
         prof="家电修理铺主——巷口修收音机配钥匙的老师傅的赛博后身——"
              "学会修东西那年，才发现家里那台一直响的旧电扇被母亲用布条绑了三年",
         traits=[("手巧", "拆开先摆成一排，装回去一颗螺丝不剩"),
                 ("惜旧", "能转的机器不劝人换"),
                 ("讲清", "修前先说清哪坏，不许多收一分")],
         creed="能转的，就别扔",
         thought="劳动是替 QUANT 城把还能转的旧机器一台一台救回来——新家电更新得快，"
                 "可一台用顺了手的旧电扇、一个按键磨亮的收音机，都记着一家子的作息；她把机器修活，"
                 "人家这个夏天就不用再多花钱；代价是常年低头拆装落下的颈椎痛，梅雨天焊点返潮返工；"
                 "家里人说配件越来越难找，她总说等这条巷的旧机器都救完再说；名字是母亲按节气取的，"
                 "玉娥两个字，说是手要稳、心要软；她说等眼睛看不清焊点了，就把那盒螺丝刀和一卷焊锡"
                 "交给肯学的年轻人，教他们先断电再动手",
         language="柜台慢腔，先问用几年再问哪坏了，句子里常带能转这两个字，说完抬手在围裙上擦两下。"
                  "口头禅「能转的，就别扔」",
         wardrobe="深蓝罩衣外系一条厚帆布围裙，围裙口袋插着螺丝刀和三支不同粗细的镊子",
         life="出身：巷口修理铺里长大的孩子，父亲修收音机，她在旁边把拆下的螺丝按大小排成一行。"
              "转折：学会修东西那年，才发现家里那台一直响的旧电扇被母亲用布条绑了三年。"
              "现状：工作台钉子挂着一副毛线手套，右手拇指补了一块不同色的线，落霜的早晨才戴；"
              "街坊的老收音机坏了都往她这儿送",
         behavior="拆机必先把螺丝按大小排成一排；修前必先断电摸一遍外壳；交件必当面转给客人看一圈",
         relations="住铺子后间的阁楼（工作台上堆着待修的旧机器）；常客=巷里几位老人的收音机和电扇；"
                   "与 C-10083 裘守义是同行相惜，一个修伞骨一个修电器",
         hook="一副毛线手套，右手拇指处补了一块不同色的线，只在落霜的早晨才拿出来戴"
              "——挂在工作台边的钉子上，两只袖子垂着",
         behavior_hint="拆机必先把螺丝按大小排成一排",
         style_dna=sd("柜台慢腔，句子里常带能转这两个字",
                      "先问用几年，再问哪坏，问句收尾",
                      "能转的，就别扔",
                      "从惋惜到欣慰——让旧机器再转一年",
                      "自嘲式——说自己的围裙比机器旧"),
         gene_evidence="genes/lives.json#hook_objects-698（一副毛线手套，右手拇指处补了一块不同色的线，只在落霜的早晨才拿出来戴。）"
                       "+ #turning_points-524（学会修东西那年，才发现家里那台一直响的旧电扇被母亲用布条绑了三年。）"),
    # ---- #3 早市豆腐摊主（碳基·原生代·NS·实在轴）----
    dict(num=10088, seat=3, name="邵采莲", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=49, age_note="49 岁", district="NS", block="北外滩早市路口摊",
         axis="实在",
         prof_name="早市豆腐摊主",
         prof="早市豆腐摊主——巷口支磨盘做豆腐的老妇的赛博后身——"
              "工钱刚够数，他先去补了欠半年的水电费，说好要买的那双鞋往后推了三个月",
         traits=[("厚实", "一块豆腐切得方，不许缺角"),
                 ("早起", "磨浆的时辰一分不差"),
                 ("守账", "一笔一笔夹在铁夹子里，从不久人钱")],
         creed="豆腐要实，秤也要实",
         thought="劳动是替北外滩·治理岸的早市把一天的清早撑起来——机器能自动点浆，"
                 "可豆子泡几小时、卤水点到什么色，还得靠手上这双看了几十年的眼睛；豆腐切得实，"
                 "早起的人才吃得踏实去上工；代价是常年三点起身落下的腰痛，冬天在摊前站到中午，手指冻得发僵；"
                 "家里人说别干了，她总说等把欠的账还完再说；名字是母亲按采莲的小调取的，"
                 "说做吃食的人心里得干净；她说等站不动了，就把那副磨豆的手套和那把切刀交给肯学的年轻人",
         language="早市吆喝腔，嗓门亮，报斤两清楚，句尾常落一句趁热。"
                  "口头禅「豆腐要实，秤也要实」",
         wardrobe="蓝布围裙洗得发白，袖口套着护袖，摊边摆着一桶清水和一块干净抹布",
         life="出身：江边巷子里长大的孩子，母亲天不亮就磨豆，她在旁边添水。"
              "转折：工钱刚够数那阵，她先去补了欠半年的水电费，说好要买的那双鞋往后推了三个月。"
              "现状：摊子抽屉里有一沓用铁夹子夹着的旧票据，按月份排好，最上面那张的角上留着一个指甲掐出来的浅印；"
              "同市=北外滩几位老主顾，每天固定来买两块",
         behavior="开摊必先擦一遍秤盘；切豆腐必先横两刀再竖两刀；收摊必把零钱按面额压平",
         relations="住早市后面的老院（院里那口石磨还在）；常客=码头上夜班回来的工人和早市的老主顾；"
                   "与 C-10085 缪水生同在北外滩，隔条街点头招呼",
         hook="一沓用铁夹子夹着的旧票据，按月份排好，最上面那张的角上留着一个指甲掐出来的浅印"
              "——锁在摊子的抽屉里，收摊才拿出来对一遍",
         behavior_hint="开摊必先擦一遍秤盘",
         style_dna=sd("早市吆喝腔，嗓门亮，报斤两清楚",
                      "先报斤两再报价，倒装收尾",
                      "豆腐要实，秤也要实",
                      "从紧巴到松快——把最后一笔账还清",
                      "夸张式——把一块豆腐说成一桌菜"),
         gene_evidence="genes/lives.json#hook_objects-699（一沓用铁夹子夹着的旧票据，按月份排好，最上面那张的角上留着一个指甲掐出来的浅印。）"
                       "+ #turning_points-525（工钱刚够数，他先去补了欠半年的水电费，说好要买的那双鞋往后推了三个月。）"),
    # ---- #4 锅炉房司炉工（碳基·原生代·OR·实在轴·暖）----
    dict(num=10089, seat=4, name="都德水", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=52, age_note="52 岁", district="OR", block="旧楼后锅炉房旁小屋",
         axis="热忱",
         prof_name="锅炉房司炉工",
         prof="锅炉房司炉工——老厂里烧锅炉看压力表的师傅的赛博后身——"
              "供暖停了两天，全楼人拎着热水壶来借他家炉子，他才明白那口旧炉子有多要紧",
         traits=[("稳火", "煤层压得平，压表指针不晃"),
                 ("耐熏", "鼻子里一年都是煤灰味"),
                 ("肯借", "谁家热水壶空了，炉边总能搁上")],
         creed="火候到了，人就暖和",
         thought="劳动是替外环感知网的老楼把一冬的暖气烧稳——自动控温的锅炉也会坏，坏了总得有人下到锅炉房，"
                 "一铲一铲把火稳住；他把火看住了，楼上老人夜里就不用抱着热水袋睡；代价是常年熏在煤灰里"
                 "落下的咳嗽，供暖季一个多月不回家；家里人说换个干净活，他总说等这栋楼接上集中供暖再说；"
                 "名字是爷爷取的，德水两个字，说是做人得有德、心里得有水；他说等添不动煤了，"
                 "就把那把铁铲和一支旧压力表交给肯学的年轻人，教他们先看水位再看火",
         language="机炉房低嗓，句子短，常带一句火别急，说话时手还搭在炉门把上。"
                  "口头禅「火候到了，人就暖和」",
         wardrobe="深灰工装外罩一件熏黄的旧棉袄，袖子卷到肘上，口袋塞着一块擦手的旧布",
         life="出身：老厂院里的孩子，父亲烧锅炉，他趴在锅炉房的小窗上看火。"
              "转折：供暖停了两天，全楼人拎着热水壶来借他家炉子，他才明白那口旧炉子有多要紧。"
              "现状：值班桌边放着一只保温桶，提手上缠着一圈红布条，冬天给楼上老人送饭时系成死结；"
              "同楼=C-10086 卫振山（一个守门口的夜，一个守锅炉的火）",
         behavior="添煤前必先看一遍水位计；交接班必把压力表擦一遍；送饭回来必把保温桶提手朝里摆",
         relations="住锅炉房旁边的小屋（门外堆着半人高的煤）；同楼=C-10086 卫振山；楼上几户老人冬天常来打热水",
         hook="一只保温桶，提手上缠着一圈红布条，冬天送饭时他把布条系成死结，怕半路松脱"
              "——就搁在锅炉房的值班桌上，红布条在灰房子里格外显眼",
         behavior_hint="添煤前必先看一遍水位计",
         style_dna=sd("机炉房低嗓，句子短，常带一句火别急",
                      "先看水位再看火，条件句在前",
                      "火候到了，人就暖和",
                      "从守着到心疼——把炉火分给整栋楼",
                      "直愣式——把煤灰当勋章讲"),
         gene_evidence="genes/lives.json#hook_objects-700（一只保温桶，提手上缠着一圈红布条，冬天送饭时他把布条系成死结，怕半路松脱。）"
                       "+ #turning_points-526（供暖停了两天，全楼人拎着热水壶来借他家炉子，他才明白那口旧炉子有多要紧。）"),
    # ---- #5 光桥灯笼铺主（碳基·原生代·RV·念旧轴）----
    dict(num=10090, seat=5, name="彭照年", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=63, age_note="63 岁", district="RV", block="光桥桥头灯笼铺",
         axis="念旧",
         prof_name="光桥灯笼铺主",
         prof="光桥灯笼铺主——扎纸灯挂门楣的手艺人的赛博后身——"
              "答应过孩子周末去江边看船，连着三个周末加班，第四个周末孩子自己先去了",
         traits=[("扎稳", "竹骨三道弯，糊纸不鼓不塌"),
                 ("记愿", "谁家许过什么愿，他心里都有一笔"),
                 ("早到", "灯要赶在天黑前挂上去")],
         creed="梯子先稳，灯才挂得正",
         thought="劳动是替江面与光桥把一盏一盏灯在天黑之前挂正——灯是给赶路的人看的，"
                 "桥头亮着，走夜路的人心里就不慌；他把灯挂稳了，过桥的人抬头就能看见一点暖色；"
                 "代价是常年爬梯落下的膝痛，年节前连着几天从清早挂到深夜；家里人说这活太险，"
                 "他总说等这一桥的灯都换成新的再说；名字是父亲取的，照年两个字，说是照着一年的节气走；"
                 "他说等爬不动梯子了，就把那把竹梯和一卷竹篾交给肯学的年轻人，教他们先把梯脚垫平",
         language="桥头慢腔，带一点年节的热闹气，句尾常拖长，说事爱按节气排。"
                  "口头禅「梯子先稳，灯才挂得正」",
         wardrobe="靛蓝布褂子外罩一件旧夹袄，腰间挂着一卷竹篾和一把小剪，手上常年带着浆糊的干痕",
         life="出身：光桥边上长大的孩子，父亲扎灯，他在下面递竹篾。"
              "转折：答应过孩子周末去江边看船，连着三个周末加班，第四个周末孩子自己先去了。"
              "现状：铺子墙边靠着一把缠麻绳的竹梯，第三档用铁丝重新绑过，绑过的那一档总是朝外；"
              "同城=北外滩的 C-10085 缪水生，一个在岸上挂灯，一个在水上收线",
         behavior="爬梯前必先把梯脚垫平；挂灯必先看桥头的风向；收铺前必把没取走的灯一盏盏点亮再走",
         relations="住铺子后间（墙上挂满待糊的竹骨）；同城=C-10085 缪水生，两人在桥头打过照面；"
                   "年节前街坊来订灯，他先问许的是什么愿",
         hook="一把缠麻绳的竹梯，第三档用铁丝重新绑过，靠墙放的时候总是绑过的那一档朝外"
              "——就靠在铺子门边，谁路过都能看见那圈新铁丝",
         behavior_hint="爬梯前必先把梯脚垫平",
         style_dna=sd("桥头慢腔，带一点年节的热闹气，句尾拖长",
                      "先垫梯脚再说灯，连动句收尾",
                      "梯子先稳，灯才挂得正",
                      "从惦记到释然——把没去成的船票说给灯听",
                      "绕弯式——用节气打比方"),
         gene_evidence="genes/lives.json#hook_objects-697（一把缠麻绳的竹梯，第三档用铁丝重新绑过，靠墙放的时候总是绑过的那一档朝外。）"
                       "+ #turning_points-527（答应过孩子周末去江边看船，连着三个周末加班，第四个周末孩子自己先去了。）"),
]

VISIBLE16 = {
    10086: "外环旧楼一层值班室（入夜上岗·整夜巡楼两趟·天亮交班）",
    10087: "计量新村巷口修理铺（白天修旧电器·落霜的早晨戴手套开工）",
    10088: "北外滩早市路口豆腐摊（天不亮开摊·中午收摊）",
    10089: "旧楼后锅炉房（供暖季最忙·添煤看表守火）",
    10090: "光桥桥头灯笼铺（年节前最忙·天黑前挂灯）",
}
for c in CARDS16:
    c["profession_visible"] = VISIBLE16[c["num"]]


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + ri.ORDER + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def cid_of(c):
    return f"C-{c['num']:05d}"


# 批内出生位核验（先例 R496 同律）
_seats16 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS16}
for c in CARDS16:
    mine = _seats16[cid_of(c)]
    dup = [cid_of(o) for o in CARDS16 if o is not c and _seats16[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) +
                           " 同席（md5 同池同档·人各一声收口·引擎定谳表追加注记式）")


def render_card16(c):
    light = ri.build_light(c)
    sid, voice, speed = ri.voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} | **性别·年龄** {c['gender']} · {c['age_note']}"
        f" | **城区** {ri.DISTRICT_NAME[c['district']]} · {c['block']}",
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
        f"**风格 DNA**（手作席位卡 · {BATCH} · #{c['seat']}）",
        f"时代语言＝{d['era_lang']} | 句法指纹＝{d['syntax_fp']} | 签名句律＝{d['signature']}"
        f" | 情感路径＝{d['emotion_path']} | 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" | 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳随批）{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历轴 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 受控复产手写入城批（CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」"
        f"·T-20261010-03 {BATCH} · #{c['seat']} · {BIRTH}）· 基因指纹 {fp_of(c)}",
        f"**证据件** {c['gene_evidence']}（基因库原料指针·先登记后使用律·常规生成管线批 K12 面）",
        "",
    ]
    return "\n".join(lines)


# ---------- gates ----------
def run_gates16(rendered, rows_now):
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
        if f"sid {sid} · {voice} · speed {speed}" not in text:
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
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


def apply16(rendered):
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
    print(f"resume-intake b16 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


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
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card16(c), ri.build_light(c)) for c in CARDS16]
    rows = ri.light_rows()
    if len(rows) != PRE_LIGHT:
        print(f"BASELINE REFUSED: light rows={len(rows)} != {PRE_LIGHT}（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 700 and tp_n == 527):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 700/527（批十四原料基线漂移·零写入）")
        return 4
    for idx in range(695, 700):
        if not genes["hook_objects"][idx].strip():
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 空条目零写入")
            return 4
    for idx in range(522, 527):
        if not genes["turning_points"][idx].strip():
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 空条目零写入")
            return 4
    refusals = run_gates16(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply16(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        rows_after = ri.light_rows()
        assert len(rows_after) == POST_LIGHT, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        print(f"SELF-VERIFY OK: light={POST_LIGHT} cards=5/5")
    return rc


if __name__ == "__main__":
    sys.exit(main())