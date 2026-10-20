#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十三 intake 5 席碳源居民 C-10081~C-10085（T-20261010-03）。

法源：CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders·commit 63ccfaba）
→ T-20261010-03 受控复产（分批律·节奏本司自主定）。先例族：intake_batch3~14。

本批=量产第十三批·复产批十三 5 席（苏长庚/虞小满/裘守义/贺满仓/缪水生）——原料按现库
（ho#691-695 + tp#518-522 共 10 条·R1807 基因轮备料），先登记后使用律，不做超料凑数。

异面注记：看线人 vs C-10079 罗守灯（夜市摊主·一个守摊位一个守旧楼走廊）；
抄表员 vs C-00356 档案修护师（一个抄新数一个修旧档）；背楼师傅 vs C-10075 老瓦匠
（一个背家当一个铺房顶）；渔具铺主 vs 修灯摊（一个在水上收线一个在夜里接线）。

K12 面 = 常规生成管线注册（非新物种扩容）。证据件 = 基因库原料指针：
·genes/lives.json 1-based #hook_objects-691..695 + #turning_points-518..522
·本批实锚全在库·hook_objects 总数 695/turning_points 总数 522 复读核对。

Gates（写盘前 fail-fast·任一不过 → 整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉） + style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10074 卡零触碰；light append-only 追加字节尾；cursor 不插队。
批后收口步：needs→behavior→rows 对齐断言（POST_LIGHT=10079）。
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

import resident_intake as ri          # 先例族单源：cid_of/build_light/voice_seat/light_rows/LIGHT
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"                   # 复产批十三批次日
BATCH = "复产批十三"
MAX_ID = 10080                         # 现存最大号（K1 连续顺延上界=批十二尾席）
POST_LIGHT = 10079                     # 批后 light 断言（10074+5）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + ri.ORDER + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def cid_of(c):
    return f"C-{c['num']:05d}"


CARDS15 = [
    # ---- #1 外环旧楼看线人（碳基·原生代·OR·侠气轴）----
    dict(num=10081, seat=1, name="苏长庚", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=58, age_note="58 岁", district="OR", block="旧楼三层楼梯口小屋",
         axis="侠气",
         prof_name="外环旧楼看线人",
         prof="外环旧楼看线人——老楼公共区域拉临时线的电工的赛博后身——暴雨夜他先给三家邻居的窗口接上临时线，"
              "自家门前的灯留到最后才接，天亮才发现自己门口还黑着",
         traits=[("守邻", "邻家的灯不亮，他自己那晚就不睡"),
                 ("惜线", "旧电线剪一段留一段，线头一根不丢"),
                 ("记门", "哪家老人夜里要留一盏灯，他心里有一张表")],
         creed="邻家的窗口先亮，我这儿不着急",
         thought="劳动是替外环感知网的老楼守住走廊里那点光——新楼的感应灯再聪明，老楼三层的声控灯灭了，"
                 "还得有人搬着梯子一盏一盏换；他把线接稳了，晚归的人和上楼的老人才不用摸黑数台阶；"
                 "代价是常年仰头接线落下的颈痛，暴雨夜连着跑三栋楼，梯子扛上扛下；家里劝他别管了，"
                 "他总说等这几栋楼都换成新线再说；名字是父亲按族谱里的字取的，长庚是傍晚才亮的那颗星，"
                 "父亲说这名字就是给夜里守灯的娃起的；他说等爬不动梯子了，就把那卷胶布和剥线钳交给"
                 "肯学的年轻人，让苏长庚这三个字跟着一盏一盏的灯，在外环旧楼的走廊里再亮几十年",
         language="老楼道口音，句子短，尾音压得很低，开口先问哪家的灯泡又不亮了，句尾常落一句亮着就行。"
                  "口头禅「灯先亮着，人再慢慢来」",
         wardrobe="旧工装外罩一件洗白的棉背心，腰间挂一卷绝缘胶布和一把剥线钳，口袋里塞着几个备用的螺口灯泡",
         life="出身：老楼里长大的孩子，父亲在楼道里给人换灯泡，他在下面扶着梯子递灯泡。"
              "转折：架临时线那几晚，自家门前的灯他留到最后才接，邻居的窗口先亮了两个晚上。"
              "现状：公用晾晒区的铁丝上挂着一把用旧电线弯成的衣架，缠胶布那一段总朝里；"
              "同城老友=外环夜市修灯摊主罗守灯（C-10079·一个守夜里出摊的摊子，一个守旧楼走廊的灯）",
         behavior="巡楼必从顶层往下走；接线前必先拉总闸再把工具摆成一排；收工必把剪下的短电线头绕成小卷收进口袋",
         relations="住旧楼三层楼梯口那间小屋（窗台上摆着备用的灯泡）；同城老友=外环夜市修灯摊主罗守灯"
                   "（C-10079·都是跟电线打交道的人）；常来搭手=楼里几个放学的孩子，他教他们先认总闸再认灯",
         hook="一把用旧电线弯成的衣架，缠胶布那一段总朝里，说是怕刮坏别人晾的被单"
              "——挂在旧楼公用晾晒区的铁丝上，一眼就认得",
         behavior_hint="接线前必先拉总闸",
         style_dna=sd("老楼道口音，句子短，尾音压得很低",
                      "先问线再问人，一句一停",
                      "灯先亮着，人再慢慢来",
                      "从惦记到放心——先把邻家的灯接上",
                      "冷面的街坊打趣——拿旧电线当话题"),
         gene_evidence="genes/lives.json#hook_objects-691（一把用旧电线弯成的衣架，缠胶布那一段总朝里，说是怕刮坏别人晾的被单。）"
                       "+ #turning_points-518（架临时线那几晚，自家门前的灯他留到最后才接，邻居的窗口先亮了两个晚上。）"),
    # ---- #2 水务抄表员（碳基·原生代·QT·秩序轴）----
    dict(num=10082, seat=2, name="虞小满", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=41, age_note="41 岁", district="QT", block="计量新村出租屋",
         axis="秩序",
         prof_name="水务抄表员",
         prof="水务抄表员——老城区上门抄水表的记账员的赛博后身——刚接手那年把073念成037赔了半日工钱，"
              "往后每读一位数，手指就在纸面上挪一格",
         traits=[("数准", "一个数字念三遍，念完再对一眼表"),
                 ("走熟", "哪户的水表在楼道哪一格，她一摸就到"),
                 ("认账", "差额自己先垫上，再回头一户一户查")],
         creed="数对上了，心里才不欠",
         thought="劳动是替 QUANT 城把每户的用量一笔一笔对上——系统再自动，一根漏水的管子和一户多走的表，"
                 "还得有人蹲下来对着表盘读数；她把数念准了，谁家这个月的账就冤不了；代价是每月初连着跑"
                 "十几栋楼，蹲久了站起来眼发黑，雨天在楼道里记数，纸都洇了；家里人说这活太琐碎，"
                 "她总说等这批老表都换完再说；名字是母亲按小满节气给起的，说满则溢、小满正好，"
                 "算账的人心里得留一分余地；她说等眼睛看不清表盘细字了，就把那支削得短短的铅笔和"
                 "抄表夹交给肯学的年轻人，教他们念数之前先把纸抚平",
         language="票本子腔，报数清楚到个位，先报户号再报读数，句尾常带一句我再念一遍。"
                  "口头禅「数对上了，心里才不欠」",
         wardrobe="深蓝工作服袖口卷到小臂，斜挎一只磨白的抄表夹，夹子侧面插着两支铅笔和一块橡皮",
         life="出身：县城里长大的孩子，母亲在供销社记账，她在柜台边学着把数目念清楚。"
              "转折：刚接手抄表把073念成037，赔了半日工钱；往后抄表，手指点在纸面一位一位挪。"
              "现状：抄表夹里压着一张折成四折的便条，铅笔写过又擦，纸背透出去年的字影，"
              "剩下那行号码她一直不敢描重——那是当年念错那户人家的电话；同楼=门岗老保安（夜里替她留门）",
         behavior="敲门必先退半步再敲三下；读数必用手指点着纸面一位一位挪；抄完必回头把表盖上的灰擦一把",
         relations="住计量新村的出租屋（桌上摊着上一月的抄表单）；同楼=小区门岗老保安，夜里替她留门；"
                   "老住户都认得她那只斜挎的抄表夹",
         hook="一张折成四折的便条，铅笔写过又擦，纸背透出去年的字影，剩下的那行号码她不敢描重"
              "——压在抄表夹最里层，谁也没见她拿出来过",
         behavior_hint="读数必用手指点着纸面一位一位挪",
         style_dna=sd("票本子腔，报数清楚到个位",
                      "先报户号后报读数，倒装收尾",
                      "数对上了，心里才不欠",
                      "从紧张到踏实——一个数字念三遍",
                      "自嘲式——把自己念错的号码当笑话"),
         gene_evidence="genes/lives.json#hook_objects-693（一张折成四折的便条，铅笔写过又擦，纸背透出去年的字影，剩下的那行号码他不敢描重。）"
                       "+ #turning_points-519（刚接手抄表把073念成037，赔了半日工钱；往后抄表，手指点在纸面一位一位挪。）"),
    # ---- #3 雨具修补摊主（碳基·原生代·RV·惜物轴）----
    dict(num=10083, seat=3, name="裘守义", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=60, age_note="60 岁", district="RV", block="棚户巷雨具摊",
         axis="惜物",
         prof_name="雨具修补摊主",
         prof="雨具修补摊主——老街修伞匠的赛博后身——暴雨夜他把摊上唯一那把伞借给楼上姑娘，"
              "第二天伞挂回门把，断了一根骨，他修好又挂回去，没说一句",
         traits=[("手稳", "换一根伞骨，撑开转一圈不歪"),
                 ("惜旧", "能修就不换，旧骨配旧布"),
                 ("收声", "修好了不邀功，只把伞撑在棚下等人来取")],
         creed="能修就不换",
         thought="劳动是替江面与光桥的雨天把破伞一骨一骨接回去——新伞便宜，可一把用顺了手的旧伞，"
                 "伞骨都记着主人的力道；他把断骨换好，人走在雨里就不用缩着肩；代价是常年低头穿线落下的眼酸，"
                 "梅雨季节一坐一整天，手指被钢丝划出细口；老伴劝他收了摊享清福，他总说等这条巷的伞都修完再说；"
                 "名字是父亲给起的，守义两个字，说是修伞的人先得守住答应人家的事；他说等穿不动线了，"
                 "就把那盒伞骨和铜别针交给肯学的年轻人，让裘守义这三个字跟着一把把撑开的伞，"
                 "在棚户巷的雨里再挡几十年",
         language="手艺人的低嗓，带一点雨天的潮气，先看伤口再报价，句子短，常把能修就不换挂在嘴上。"
                  "口头禅「能修就不换」",
         wardrobe="深灰旧围裙上别着一排伞骨和几枚铜别针，门后挂着一件领口补过三针的旧雨衣",
         life="出身：棚户巷里长大的孩子，父亲修伞，他在旁边把拆下来的旧骨按长短排好。"
              "转折：暴雨夜楼上姑娘敲门借伞，他把唯一的那把给了她，转天伞挂回门把，断了一根骨。"
              "现状：门后挂着那件旧雨衣，领口补过三针，补线比布深一档；借伞的姑娘每逢下雨都来修伞，"
              "两人从不多话，一个放下伞，一个撑开看",
         behavior="接伞必先撑开转一圈看断在哪；换骨必用旧伞拆下来的同色骨；雨天收摊前必把没取走的伞一把把撑开晾在棚下",
         relations="住棚户巷摊后的矮屋（屋里挂满待修的伞）；常客=楼上那位姑娘，每逢下雨来修伞；"
                   "街坊都认得门后那件旧雨衣",
         hook="一件旧雨衣，领口补过三针，补线比布深一档，挂在门后不用看名字"
              "——棚户巷雨具摊的门后，谁都知道那是他的",
         behavior_hint="接伞必先撑开转一圈看断在哪",
         style_dna=sd("手艺人的低嗓，带一点雨天的潮气",
                      "先看伤口再报价，短句连缀",
                      "能修就不换",
                      "从心疼到温热——把别人的破伞修好",
                      "机锋式——拿断伞骨打趣天气"),
         gene_evidence="genes/lives.json#hook_objects-695（一件旧雨衣，领口补过三针，补线比布深一档，挂在门后不用看名字。）"
                       "+ #turning_points-520（暴雨夜楼上姑娘敲门借伞，他把唯一的那把给了她，转天伞挂回门把，断了一根骨。）"),
    # ---- #4 搬家背楼师傅（碳基·原生代·OR·实在轴）----
    dict(num=10084, seat=4, name="贺满仓", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=46, age_note="46 岁", district="OR", block="外环背街合租房",
         axis="实在",
         prof_name="搬家背楼师傅",
         prof="搬家背楼师傅——码头扛包工的赛博后身——头一回挣的工钱缝进席子夹层整整三年没动，"
              "换房翻出来时纸钞返潮，他蹲在楼梯转角一张张晾干",
         traits=[("肩稳", "冰箱上六楼，一个角不磕"),
                 ("守信", "说几点到就几点到，雨里也来"),
                 ("记账", "工钱一分一分缝起来，不乱花")],
         creed="楼有多高，肩就有多稳",
         thought="劳动是替外环感知网把一户人家的家当一步一步背上楼——电梯坏了、楼道窄了、柜子沉了，"
                 "总得有人肯把绳往肩上一垫；他把东西背上去了，搬家的人在新屋里就能先坐下喝口水；"
                 "代价是腰上的旧伤，一到阴天就发紧，最重的一趟背完要在楼道里蹲半晌；家里人说换个轻省活，"
                 "他总说等孩子念完书再说；名字是爷爷给起的，满仓两个字，说是背东西的人先得让自家的仓满；"
                 "他说等背不动了，就把那卷尼龙绳和那双胶鞋交给肯学的年轻人，教他们先打双套结再上肩",
         language="码头号子腔，字重，句尾带喘，先上肩后说话，常把人家的旧柜子说成一船货。"
                  "口头禅「楼有多高，肩就有多稳」",
         wardrobe="褪色的劳保外套上垫一条宽带子缠肩，裤脚扎进胶鞋，腰间挂着一卷尼龙绳",
         life="出身：码头边上长大的孩子，父亲扛包，他在跳板边上递绳子。"
              "转折：工资缝进席子夹层，整整三年没动；换房翻出来纸钞返潮，摊在楼梯转角一张张晾。"
              "现状：那床旧席子边角用布条包了三道，夏天铺开时总把包边转到脚边——那是他缝工钱的地方；"
              "同乡=码头旧工友，如今在别处看仓",
         behavior="上手前必先绕柜子走一圈看有没有暗角；捆绳必打双套结；下楼必扶着扶手空手走，不让人家跟着",
         relations="住外环背街的合租房（床下就是那卷尼龙绳）；同乡=码头旧工友，如今在别处看仓；"
                   "背过的老住户逢年过节会给他留一碗汤",
         hook="一床卷起来的旧席子，边角用布条包了三道，夏天铺开时总把包边转到脚边"
              "——那是他缝工钱的地方，卷起来就压在床底",
         behavior_hint="捆绳必打双套结",
         style_dna=sd("码头号子腔，字重，句尾带喘",
                      "先上肩后说话，动宾倒置",
                      "楼有多高，肩就有多稳",
                      "从硬撑到松开——把工钱数给孩子",
                      "夸张式——把楼梯说成山"),
         gene_evidence="genes/lives.json#hook_objects-694（一床卷起来的旧席子，边角用布条包了三道，夏天铺开时总把包边转到脚边。）"
                       "+ #turning_points-521（工资缝进席子夹层，整整三年没动；换房翻出来纸钞返潮，摊在楼梯转角一张张晾。）"),
    # ---- #5 江边渔具铺主（碳基·原生代·NS·念旧轴）----
    dict(num=10085, seat=5, name="缪水生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=55, age_note="55 岁", district="NS", block="北外滩岸边吊脚棚",
         axis="念旧",
         prof_name="江边渔具铺主",
         prof="江边渔具铺主——江上渔船伙夫的赛博后身——往老家头一回寄钱，收款人名字对着户口簿一笔一笔描，"
              "写完还要用手指再划一遍笔画",
         traits=[("识水", "看云就知道明天能不能出竿"),
                 ("惜物", "收线先擦木轴，旧线不舍得扔"),
                 ("厚道", "新手来买钩，先教绑三遍再收钱")],
         creed="线在手里，家就在岸上",
         thought="劳动是替北外滩·治理岸的江边把一根线一段一段续下去——江上的风浪不由人，"
                 "可竿子、钩子、线结这些手上活，总得有人在铺子里替出江的人备齐；他把线擦亮了，"
                 "钓鱼的人站在岸边心里就踏实；代价是常年泡在江风里落下的关节痛，涨水季一夜起来看三回水位；"
                 "家里人劝他搬到城里住，他总说等这排吊脚棚拆了再说；名字是奶奶给起的，水生两个字，"
                 "说是江边生的孩子，名字里得有水才养得住；他说等拿不稳绕线板了，就把柜台上那盘线"
                 "和那截木轴留给常来的夜钓老伙计，让缪水生这三个字跟着一根根线，在江边再续几十年",
         language="江边慢腔，拖长音，句里带水汽，先看线再收竿，主语常省略，常把空竿说成满载。"
                  "口头禅「线在手里，家就在岸上」",
         wardrobe="洗得发白的蓝布褂子外罩一件旧马甲，腰间挂着一盒鱼钩，脚上的胶鞋常年带着江泥",
         life="出身：江上渔船里长大的孩子，父亲在船尾收线，他在船头数钩。"
              "转折：往老家第一次寄钱，收款人名字对着户口簿描，写完还要用手指再划一遍笔画。"
              "现状：柜台上那盘钓线，木轴上记着上一个主人的姓名首字，他每次收线都先把那截木轴擦一遍——"
              "那盘线他一直不卖；常客=江上夜钓的老伙计们",
         behavior="开门必先把门口的鱼护拎起来看一遍；收线必擦木轴；来客买钩必先教绑三遍再收钱",
         relations="住北外滩岸边的吊脚棚（棚里挂着晒干的鱼护）；常客=江上夜钓的老伙计们；"
                   "老家还有一家子人，钱按月寄",
         hook="一盘钓线，木轴上记着上一个主人的姓名首字，他每次收线都先把那截木轴擦一遍"
              "——摆在铺子柜台最里侧，从不卖",
         behavior_hint="收线必擦木轴",
         style_dna=sd("江边慢腔，拖长音，句里带水汽",
                      "先看线再收竿，主语常省略",
                      "线在手里，家就在岸上",
                      "从漂泊到安顿——把那截木轴擦亮",
                      "说反话——把空竿说成满载"),
         gene_evidence="genes/lives.json#hook_objects-692（一盘钓线，木轴上记着上一个主人的姓名首字，他每次收线都先把那截木轴擦一遍。）"
                       "+ #turning_points-522（往老家第一次寄钱，收款人名字对着户口簿描，写完还要用手指再划一遍笔画。）"),
]

VISIBLE15 = {
    10081: "外环旧楼公用晾晒区看线摊（白天巡楼·暴雨夜最忙·工具挂在三层楼梯口）",
    10082: "QUANT 城计量新村各楼道水表箱前（每月初上门抄表·雨天在楼道里蹲着记）",
    10083: "棚户巷雨具修补摊（雨后最忙·门后挂着待取修好的伞）",
    10084: "外环背街搬家接活点（清早等活·月底搬家最忙·绳卷挂在车把上）",
    10085: "北外滩岸边渔具铺（涨水季看水位·傍晚夜钓的人来配线）",
}
for c in CARDS15:
    c["profession_visible"] = VISIBLE15[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats15 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS15}
for c in CARDS15:
    mine = _seats15[cid_of(c)]
    dup = [cid_of(o) for o in CARDS15 if o is not c and _seats15[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) +
                           " 同席（md5 同池同档·人各一声收口·引擎定谳表追加注记式）")


def render_card15(c):
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


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + ri.ORDER + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def cid_of(c):
    return f"C-{c['num']:05d}"


# ---------- gates（fail-fast·写盘前·任一不过 → 整批拒收零写入）----------
def run_gates15(rendered, rows_now):
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
    # K6 批面：style_dna 五维逐维两两互异
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


# ---------- apply（新文件 only·light append-only·幂等）----------
def apply15(rendered):
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
    print(f"resume-intake b15 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


# ---------- 批后收口步（intake_batch10 先例：needs→behavior→rows 对齐断言）----------
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
    rendered = [(c, render_card15(c), ri.build_light(c)) for c in CARDS15]
    rows = ri.light_rows()
    # K1 基线：light=10074（批十二后）·新 max=C-10080·新号 C-10081~C-10085 连续顺延
    if len(rows) != 10074:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10074（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 695 and tp_n == 522):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 695/522（批十三原料基线漂移·零写入）")
        return 4
    for idx in range(690, 695):
        if not genes["hook_objects"][idx].strip():
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 空条目零写入")
            return 4
    for idx in range(517, 522):
        if not genes["turning_points"][idx].strip():
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 空条目零写入")
            return 4
    refusals = run_gates15(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply15(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        # 落库后自证：light=10079·五卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == POST_LIGHT, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light={POST_LIGHT} cards=5/5 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())