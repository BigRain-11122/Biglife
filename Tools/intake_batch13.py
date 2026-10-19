#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十一 intake —— 4 席碳源居民 C-10075~C-10078（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders L1274
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~12
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4+R1756 批六 4/4
+R1758 批七 4/4+R1760 批八 4/4+R1763 批九 4/4+R1766 批十 4/4 全门闸走满实证）。
本批=量产第九批·复产批十一 4 席（匡稳脊/柳千结/糜花信/唐串红·R1767 原料 8/8 落库就绪
·ho685-688+tp512-515·四新域=瓦匠/补网/养蜂/糖墩子——R1767 选域实测 0 覆盖定谳——异面注记：
瓦匠 vs C-00356 档案修护师=修护行当异面〔一个守屋瓦一个守旧档〕·补网 vs C-10028 渔匠=江上渔
行当异面〔一个长凳补网一个码头打渔〕·养蜂 vs C-10035 插花师=花事行当异面〔一个酿蜜一个插花〕
·糖墩子 vs C-10027 司茶师=巷口吃食行当异面〔一个串糖一个司茶〕）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-685/686/687/688+#turning_points-512/513/514/515
·本批实锚全在库·hook_objects 总数 688/turning_points 总数 515 复读核对·tp 原文代词=TP514 他
·R1769 定谳=两男席〔瓦匠/养蜂〕两女席〔补网/糖墩子·真名预检 4/4 unique〕）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10068 卡零触碰；light append-only 追加字节尾；cursor 不插队。
批后收口步（R1759 候选单·intake_batch10 先例）: needs face 刷新→behavior 强制再生→
rows 对齐 light 断言（POST_LIGHT=10072）。
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
BIRTH = "2026-10-20"                   # 复产批十一批日（解禁令次日夜班滚动批）
BATCH = "复产批十一"
MAX_ID = 10074                         # 现存最大号（K1 连续顺延上界=批十尾席）
POST_LIGHT = 10072                     # 批后收口步 light 断言


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS13 = [
    # ---- 席 #1 老瓦匠（碳基·原生代·NS·秩序轴）----
    dict(num=10075, seat=1, name="匡稳脊", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=62, age_note="62 岁", district="NS", block="历史立面群", axis="秩序",
         prof_name="历史立面群老瓦匠",
         prof="历史立面群老瓦匠——老屋面工的赛博后身——机制琉璃瓦进了建材铺，他照样替街坊捡瓦补漏，瓦一垄一垄铺得匀，屋子住着才安稳",
         traits=[("守拙", "新瓦片再亮他也先拿旧瓦补边"),
                 ("稳当", "上房必先试一遍脚下的椽"),
                 ("实诚", "工钱按垄算多一垄是一垄")],
         creed="瓦要一垄一垄铺，屋子才住得安稳。",
         thought="劳动是替历史立面群守一坡经得起雨的老瓦——机制琉璃瓦再整齐，老屋檐口的漏，还得有人肯一垄一垄爬上去补匀，他把瓦补下去，街坊屋里睡觉就踏实；代价是常年弓腰跪在坡瓦上，膝头磨出两块老茧，落雨天也不肯歇活，家里人劝他下房他总说补完这一坡再说；名字是瓦棚老师傅给起的，说匡家的瓦刀稳，垄垄铺得匀，经他手补的屋顶就没有再漏过的，这名字在历史立面群的屋脊上传了几十年；他说等爬不动房了，就把那把木柄发黑的半圆瓦刀传给肯学补瓦的娃，让匡稳脊这三个字跟着一坡一坡的老瓦，在历史立面群再稳几十年。",
         language="瓦匠棚慢手艺人腔带白灰味，开口先问屋漏了几场雨，句尾爱带一句铺得匀；口头禅「瓦要一垄一垄铺，屋子才住得安稳」。",
         wardrobe="粗帆布工装裤膝头打着皮补丁，腰后布带里别着那把半圆瓦刀，指缝里嵌着洗不净的白灰。",
         life="出身：历史立面群瓦棚后院长大的孩子，父亲踩在坡瓦上补漏，他在下面递瓦刀和白灰。转折：机制琉璃瓦进了建材铺，老瓦匠还是替街坊们捡瓦补漏，瓦要一垄一垄铺得匀，屋子住着才安稳——机器瓦再齐整，老屋的檐口还得一把老瓦刀伺候。现状：瓦棚里那把半圆形瓦刀，木柄让手汗浸得发黑，刃口还沾着未干的白灰——老师傅传的，补瓦前他都要先在灰里蘸一遍刃；同城老友=同街区档案修护师崔阿凤（C-00356·一个守屋瓦一个守旧档，历史立面群修护行当的一瓦一档）。",
         behavior="开垄必先洒一遍水压实底瓦；上房必先试一遍脚下的椽；收活必把碎瓦扫进筐，檐口一片不留。",
         relations="住历史立面群瓦棚后的旧屋（推开棚门就是当年瓦场）；同城老友=历史立面群档案修护师崔阿凤（C-00356·一个守屋瓦一个守旧档，历史立面群修护行当的一瓦一档）；徒弟=街区里跟他学拣瓦上垄的小辈们。",
         hook="瓦匠的那把半圆形瓦刀，木柄让手汗浸得发黑，刃口还沾着未干的白灰——历史立面群瓦棚的师传瓦刀，街坊屋顶的安稳全从这刃口上一垄一垄匀出来",
         behavior_hint="上房必先试一遍脚下的椽",
         style_dna=sd("瓦匠棚慢手艺人腔带白灰味", "一句压一句，慢话里带工序", "瓦要一垄一垄铺，屋子才住得安稳",
                      "从漏到安——先拣瓦，后上垄", "瓦匠灰幽默——拿机制琉璃瓦打趣老瓦刀"),
         gene_evidence="genes/lives.json#hook_objects-685（瓦匠的那把半圆形瓦刀，木柄让手汗浸得发黑，刃口还沾着未干的白灰。）"
                       "+ #turning_points-512（机制琉璃瓦进了建材铺，老瓦匠还是替街坊们捡瓦补漏，瓦要一垄一垄铺得匀，屋子住着才安稳。）"),
    # ---- 席 #2 老补网匠（碳基·弄堂派·RV·安稳轴）----
    dict(num=10076, seat=2, name="柳千结", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=54, age_note="54 岁", district="RV", block="渔匠码头巷", axis="安稳",
         prof_name="渔匠码头巷老补网匠",
         prof="渔匠码头巷老补网匠——渔家补网人的赛博后身——探鱼器再灵，江上的破网还得她坐长凳一梭一梭补匀，网眼匀了收成才有数",
         traits=[("指快", "一梭过去三个眼不带回头的"),
                 ("耐烦", "教孩子打结能陪一整晌"),
                 ("知数", "谁家几张网她心里有本账")],
         creed="网眼要匀，收成才有数。",
         thought="劳动是替渔匠码头巷守一张经得起江风的网——探鱼器再灵，网眼的匀与破，还得有人肯坐长凳一梭一梭补回来，她把网补下去，江上收成才有数；代价是常年捏梭勒得指肚起沟，麻线把掌心磨出老皮，冬天江风灌棚她也不歇凳，家里人劝她收凳她总说补完这批网再说；名字是渔家长辈给起的，说柳家的手细，千个结打得一个样，经她手补的网就没有跑过鱼的，这名字在码头巷的网架上挂了几十年；她说等捏不动梭了，就把那把磨得溜滑的青竹梭传给肯学补网的娃，让柳千结这三个字跟着一网一网的匀眼，在渔匠码头巷再收几十年的成。",
         language="补网场长凳慢语带江风咸味，开口先数今天补几张，句尾爱带一句有数；口头禅「网眼要匀，收成才有数」。",
         wardrobe="靛蓝布衫袖口卷到肘，腰后布带里插着青竹梭，指间常绕着一圈备用的麻线。",
         life="出身：渔匠码头巷补网棚里长大的孩子，母亲坐长凳补网，她在旁边绕线团。转折：渔船装上了探鱼器，补网场的老把式还守着长凳，教半大孩子们打结起头，网眼匀了，收成才有数——机器探得见鱼群，探不见网眼里的手上功夫。现状：补网棚的青竹梭插在腰后的布带里，磨得溜滑，网脚堆着几团备用的旧麻线——家传的补网梭，巷里渔家几张网的破眼全从这一梭一结里匀回来；同城老友=码头手作渔匠岑刻舟（C-10028·一个补网一个打渔，渔匠码头的一梭一桨）。",
         behavior="落座必先理顺一束麻线；补网必先数一遍破眼；收凳必把梭子别回腰后布带，线头一根不落。",
         relations="住渔匠码头巷补网棚的长凳后屋（棚尾挂着几卷备用的旧网脚）；同城老友=码头手作渔匠岑刻舟（C-10028·一个补网一个打渔，渔匠码头的一梭一桨）；徒弟=巷里跟她学打结起头的半大孩子们。",
         hook="补网用的梭子插在腰后的布带里，青竹磨得溜滑，网脚堆着几团备用的旧麻线——渔匠码头补网棚的家传竹梭，江上收成的数全从这一梭一结里匀回来",
         behavior_hint="补网必先数一遍破眼",
         style_dna=sd("补网场长凳慢语带江风咸味", "短句连打结，一句一扣", "网眼要匀，收成才有数",
                      "从破到补——先理线，后打结", "补网慢幽默——拿探鱼器打趣老梭子"),
         gene_evidence="genes/lives.json#hook_objects-686（补网用的梭子插在腰后的布带里，青竹磨得溜滑，网脚堆着几团备用的旧麻线。）"
                       "+ #turning_points-513（渔船装上了探鱼器，补网场的老把式还守着长凳，教半大孩子们打结起头，网眼匀了，收成才有数。）"),
    # ---- 席 #3 老养蜂人（碳基·原生代·NS·逍遥轴）----
    dict(num=10077, seat=3, name="糜花信", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="NS", block="花道小院巷", axis="逍遥",
         prof_name="花道小院巷老养蜂人",
         prof="花道小院巷老养蜂人——追花期老蜂倌的赛博后身——蜂场跟花期挪去了远郊果园，院里两只老箱他守着，好蜜急不得，等花一茬一茬开过去",
         traits=[("慢性子", "摇蜜从不多摇一滴"),
                 ("识花", "街坊问花期他一口报得准"),
                 ("手轻", "掀箱盖不带响，蜂群不炸窝")],
         creed="好蜜急不得，等花一茬一茬开过去。",
         thought="劳动是替花道小院巷守一箱等得起花期的蜜——超市蜂蜜再便当，院里那两口老箱的甜，还得有人肯跟着花期慢慢等，他把蜂守下去，巷里的春天就有蜜味；代价是常年被蜂蜇出手背上的旧包，摇蜜季熬到眼花，家里人劝他装箱退休他总说等这一茬花过去再说；名字是蜂场老把式给起的，说糜家的性子稳，花开到几成他一口报得准，这名字跟着蜂箱在花道上走了几十年；他说等掀不动箱盖了，就把那两只老蜂箱连同杉木盖一起交给肯学养蜂的娃，让糜花信这三个字跟着一茬一茬的花期，在花道小院巷再甜几十年。",
         language="蜂场小院慢语带花蜜甜味，开口先报哪种花开到第几茬，句尾爱带一句急不得；口头禅「好蜜急不得，等花一茬一茬开过去」。",
         wardrobe="米白粗布褂换了旧草帽，手里常提着杉木蜂箱盖，指缝里粘着几点金色蜡屑。",
         life="出身：花道小院巷蜂房小院长大的孩子，父亲跟花期走，他在院里守着两只老箱。转折：蜂场跟着花期挪去了远郊果园，院里留两只老箱，开春他领着娃娃们认蜂王，好蜜急不得，得等花一茬一茬开过去——蜂场挪得再远，院里老箱的蜂王认得回家的路。现状：院角那两只老蜂箱，杉木盖晒出了白边，箱口那块起落板上总粘着几点金色的蜡屑——师父传的老箱，开春认蜂王的老课全在这块起落板前上；同城老友=花道小院插花师叶知秋（C-10035·一个酿蜜一个插花，花道小院的一蜂一花）。",
         behavior="开箱必先站到下风口；摇蜜必先看一遍天色；收工必把起落板擦净，蜡屑一点不留箱口。",
         relations="住花道小院巷蜂房小院（院角就是那两只老蜂箱）；同城老友=花道小院插花师叶知秋（C-10035·一个酿蜜一个插花，花道小院的一蜂一花）；徒弟=巷里跟他认蜂王的娃娃们。",
         hook="老蜂箱的杉木盖晒出了白边，箱口那块起落板上总粘着几点金色的蜡屑——花道小院蜂房小院的师传老箱，巷里那点甜全从这块起落板上进出",
         behavior_hint="开箱必先站到下风口",
         style_dna=sd("蜂场小院慢语带花蜜甜味", "慢句带甜尾，一句一茬花", "好蜜急不得，等花一茬一茬开过去",
                      "从急到甜——先看花，后开箱", "蜂箱甜幽默——拿超市蜂蜜打趣老蜂箱"),
         gene_evidence="genes/lives.json#hook_objects-687（老蜂箱的杉木盖晒出了白边，箱口那块起落板上总粘着几点金色的蜡屑。）"
                       "+ #turning_points-514（蜂场跟着花期挪去了远郊果园，院里留两只老箱，开春他领着娃娃们认蜂王，好蜜急不得，得等花一茬一茬开过去。）"),
    # ---- 席 #4 老糖墩子匠（碳基·弄堂派·QT·烟火轴）----
    dict(num=10078, seat=4, name="唐串红", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=49, age_note="49 岁", district="QT", block="弄堂茶馆巷", axis="烟火",
         prof_name="弄堂茶馆巷老糖墩子匠",
         prof="弄堂茶馆巷老糖墩子匠——老糖摊师傅的赛博后身——真空包装进了超市货架，她的挑子照旧歇在校门口，玻璃罩一掀，糖壳咬得咔咔响",
         traits=[("手准", "一勺糖稀挂一串不多不少"),
                 ("爽利", "找零嘴皮子比秤还快"),
                 ("热心", "巷口谁家娃考了好试她多送半串")],
         creed="糖壳咬得咔咔响，日子才过得脆。",
         thought="劳动是替弄堂茶馆巷守一口挂得住脆响的糖锅——真空包装再方便，糖壳现挂的那声咔咔，还得有人肯守着铜锅一串一串熬出来，她把糖挂下去，巷里娃放学就有盼头；代价是常年站在灶边熬糖，手腕让铜勺压出酸，夏天灶火烤得满头汗，家里人劝她收摊她总说熬完这一锅再说；名字是糖摊祖师给起的，说唐家的糖稀挂得住串，糖壳咬得响不粘牙，这名字在巷口吆喝了几十年；她说等抡不动糖勺了，就把那口咕嘟泡的铜锅传给肯学挂糖的姑娘，让唐串红这三个字跟着一串一串的红果，在弄堂茶馆巷再脆几十年。",
         language="糖摊吆喝腔带糖稀甜香，开口先问今天要几串，句尾爱带一句咬得响；口头禅「糖壳咬得咔咔响，日子才过得脆」。",
         wardrobe="枣红布围裙口袋里揣着竹签和零钱盒，手腕上搭着擦糖勺的粗布，鬓边别着一小截红果色的头绳。",
         life="出身：弄堂茶馆巷糖坊小屋长大的孩子，母亲守铜锅挂糖，她在旁边串红果。转折：超市货架添了真空包装的糖串，糖墩子挑子仍歇在校门口，玻璃罩一掀，糖壳咬得咔咔响——真空袋装得下糖串，装不进那一声现挂的脆响。现状：糖坊那口铜锅，糖稀在灶上咕嘟出细密的泡，红果先拿竹签串好码在木托盘上——祖师传的糖锅，巷里娃放学铃一响的那口脆全从这锅里挂出来；同城老友=弄堂茶馆司茶师乔雨前（C-10027·一个串糖一个司茶，弄堂茶馆巷的一茶一糖）。",
         behavior="出摊必先擦一遍玻璃罩；挂糖必先试一遍糖稀的稠；收摊必把铜锅刷净擦干，糖渣一点不糊锅。",
         relations="住弄堂茶馆巷尾的糖坊小屋（屋后灶台就是那口铜锅）；同城老友=弄堂茶馆司茶师乔雨前（C-10027·一个串糖一个司茶，弄堂茶馆巷的一茶一糖）；徒弟=巷里跟她学串果挂糖的姑娘小辈们。",
         hook="糖墩子的红果先拿竹签串好，码在木托盘上，糖稀在铜锅里咕嘟出细密的泡——弄堂茶馆巷糖坊的祖传铜锅，巷里娃那声咔咔响全从这锅里挂出来",
         behavior_hint="挂糖必先试一遍糖稀的稠",
         style_dna=sd("糖摊吆喝腔带糖稀甜香", "脆句短促，一句一串", "糖壳咬得咔咔响，日子才过得脆",
                      "从酸到甜——先串果，后挂糖", "糖摊甜幽默——拿真空包装打趣现挂的糖壳"),
         gene_evidence="genes/lives.json#hook_objects-688（糖墩子的红果先拿竹签串好，码在木托盘上，糖稀在铜锅里咕嘟出细密的泡。）"
                       "+ #turning_points-515（超市货架添了真空包装的糖串，糖墩子挑子仍歇在校门口，玻璃罩一掀，糖壳咬得咔咔响。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card13(c):
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
VISIBLE13 = {
    10075: "历史立面群瓦棚（雨天接漏最忙·补瓦按垄点工·收工最晚）",
    10076: "渔匠码头巷补网棚（晨间理线·渔汛前补网最忙·长凳常年不空）",
    10077: "花道小院巷蜂房小院（开春认蜂王课·摇蜜季开箱·花期追花最勤）",
    10078: "弄堂茶馆巷口糖摊（放学铃后最忙·现挂糖壳·收摊擦锅最净）",
}
for c in CARDS13:
    c["profession_visible"] = VISIBLE13[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats13 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS13}
for c in CARDS13:
    mine = _seats13[cid_of(c)]
    dup = [cid_of(o) for o in CARDS13 if o is not c and _seats13[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates13(rendered, rows_now):
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
def apply13(rendered):
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
    print(f"resume-intake b11 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


# ---------- 批后收口步（R1759 候选单·intake_batch10 先例：needs→behavior→rows 对齐断言）----------
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
    rendered = [(c, render_card13(c), ri.build_light(c)) for c in CARDS13]
    rows = ri.light_rows()
    # K1 基线：light=10068（批十后）·现 max=C-10074·新号 C-10075~C-10078 连续顺延
    if len(rows) != 10068:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10068（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·R1767 落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 688 and tp_n == 515):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 688/515（批十一原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("瓦匠的那把半圆形瓦刀，木柄让手汗浸得发黑，刃口还沾着未干的白灰。",
                 "补网用的梭子插在腰后的布带里，青竹磨得溜滑，网脚堆着几团备用的旧麻线。",
                 "老蜂箱的杉木盖晒出了白边，箱口那块起落板上总粘着几点金色的蜡屑。",
                 "糖墩子的红果先拿竹签串好，码在木托盘上，糖稀在铜锅里咕嘟出细密的泡。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("机制琉璃瓦进了建材铺，老瓦匠还是替街坊们捡瓦补漏，瓦要一垄一垄铺得匀，屋子住着才安稳。",
                 "渔船装上了探鱼器，补网场的老把式还守着长凳，教半大孩子们打结起头，网眼匀了，收成才有数。",
                 "蜂场跟着花期挪去了远郊果园，院里留两只老箱，开春他领着娃娃们认蜂王，好蜜急不得，得等花一茬一茬开过去。",
                 "超市货架添了真空包装的糖串，糖墩子挑子仍歇在校门口，玻璃罩一掀，糖壳咬得咔咔响。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates13(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply13(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        # 落库后自证：light=10072·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10072, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10072 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
