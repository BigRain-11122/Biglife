#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十 intake —— 4 席碳源居民 C-10071~C-10074（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba）→ T-20261010-03 受控复产（分批律·节奏本司自主定）→ 先例族 intake_batch3~11
（R1747 批一 3/3+R1748 批二 3/3+R1750 批三 4/4+R1752 批四 4/4+R1754 批五 4/4+R1756 批六 4/4
+R1758 批七 4/4+R1760 批八 4/4+R1763 批九 4/4 全门闸走满实证）。
本批=量产第八批·批十 4 席（齐墨林/程万里/庞守烛/邱盘石·R1765 席位方案定谳+原料 8/8 落库就绪
·qa/gene-round-R1765.log·换域面=印刷铅字盘/邮路邮包/灯笼刮刀/磨坊石磨四新域——异面注记：
排字工 vs C-10038 修字师=铅字行当异面〔一个守盘教娃认反字一个修活字请回秃字〕·守邮人 vs
C-10061 值机员=信息行当异面〔一个守家信邮路一个守外环频段〕·灯笼匠 vs C-10066 剃头担=
MD 手艺行当异面·磨坊主 vs C-10049 苇匠=江岸滩涂异面）。
K12 面: 常规生成管线注册（非新物种扩容）→ 证据件=基因库原料指针（先登记后使用律
·genes/lives.json 1-based #hook_objects-681/682/683/684+#turning_points-508/509/510/511
·本批实锚全在库·hook_objects 总数 684/turning_points 总数 511 复读核对·tp 原文代词=他
·R1761 定谳=四席男席·真名预检 4/4 unique〔R1765 已预检〕）。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10064 卡零触碰；light append-only 追加字节尾；cursor 不插队。
批后收口步（R1759 候选单·intake_batch10 先例）: needs face 刷新→behavior 强制再生→
rows 对齐 light 断言（POST_LIGHT=10068）。
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
BIRTH = "2026-10-19"                   # 复产批十批日（CEO 解禁令当日滚动批）
BATCH = "复产批十"
MAX_ID = 10070                         # 现存最大号（K1 连续顺延上界=批九尾席）
POST_LIGHT = 10068                     # 批后收口步 light 断言


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS12 = [
    # ---- 席 #1 老排字工（碳基·弄堂派·NS·怀旧轴）----
    dict(num=10071, seat=1, name="齐墨林", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="男",
         age=58, age_note="58 岁", district="NS", block="历史立面群", axis="怀旧",
         prof_name="历史立面群老排字工",
         prof="历史立面群老排字工——老印刷坊排字工的赛博后身——一屉一屉字模码进旧木箱，全城娃认字起步的老规矩就从他这盘反字里传下去",
         traits=[("念旧", "字盘里那几枚反字谁劝也不让抠"),
                 ("耐心", "一个字能给娃讲上小半晌"),
                 ("板正", "码字模必须横平竖直")],
         creed="字要认得反的，才算认得透。",
         thought="劳动是替历史立面群守一盘认得透的字——激光照排再快，老铅字盘里那几枚反字，是几代人认字起步的老规矩，他把字盘一代代摆下去，全城娃认字就先认得反的正的；代价是常年伏在字盘前给娃讲字，嗓子讲到发哑，油墨渗进指纹洗了几十年也没洗净，家里人劝他歇摊他总说讲完这届娃再说；名字是当年排字房老师傅给起的，说齐家的手稳码字不歪，字模到他手里就没有码乱过的盘，这名字跟着字盘传了一辈子；他说等讲不动了，就把那盘嵌着反字的铅字盘捐给老印刷坊的展柜，让齐墨林这三个字跟着一屉一屉字模，在历史立面群再码几十年。",
         language="印刷坊排字房老手艺腔带墨香，说事先说字，句尾爱带一句认得透；口头禅「字要认得反的，才算认得透」。",
         wardrobe="藏青工装围裙口袋里别着小镊子和字模盒，指腹沾着经年洗不净的油墨。",
         life="出身：历史立面群印刷坊后巷长大的孩子，父亲在排字房码了一辈子字模，他上手认的第一盘字是老师傅摆给他的反字盘。转折：铅字退了休，一屉一屉字模码进旧木箱，他没舍得交盘，照旧周末摆开字盘教娃——字模退了役，认字的老规矩不能退。现状：印刷坊的老铅字盘，空格里嵌着几枚没抠干净的反字，指腹蹭过还沾着油墨——老师傅传的，每回摆盘他都要先掸一遍灰；同城白玉兰塔区弄堂活字铺的老修字师聂砚萍收工路过印刷坊，两人一个守铅字盘教娃认反字一个修活字把秃字请回来，是历史立面群铅字行当里出名的一修一守。",
         behavior="开箱必先掸一遍木箱灰；摆盘必先数一遍空格；收摊必把反字按部首码回原屉，一字不乱。",
         relations="住历史立面群印刷坊后巷的旧屋（窗下就是当年排字房的后墙）；同城老友=白玉兰塔区弄堂活字铺修字师聂砚萍（C-10038·一个守盘教娃认反字一个修活字，铅字行当的一修一守）；徒弟=对门跟他认反字的小娃们。",
         hook="印刷坊的老铅字盘，空格里嵌着几枚没抠干净的反字——历史立面群排字房的师传字盘，全城娃认字的老规矩全从这盘反字里传下去",
         behavior_hint="摆盘必先数一遍空格",
         style_dna=sd("印刷坊排字房老手艺腔带墨香", "说事先说字，一句一码", "字要认得反的，才算认得透",
                      "从认到透——先摆盘，后讲字", "排字房墨幽默——拿激光照排打趣反字盘"),
         gene_evidence="genes/lives.json#hook_objects-681（印刷坊的老铅字盘，空格里嵌着几枚没抠干净的反字，指腹蹭过还沾着油墨。）"
                       "+ #turning_points-508（铅字退了休，一屉一屉字模码进旧木箱，周末他摆开字盘教对门的娃认反字。）"),
    # ---- 席 #2 老邮所守所人（碳基·新市民派·OR·安稳轴）----
    dict(num=10072, seat=2, name="程万里", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=63, age_note="63 岁", district="OR", block="监听哨街区", axis="安稳",
         prof_name="监听哨街区老邮所守所人",
         prof="监听哨街区老邮所守所人——老邮差的赛博后身——一扇收发小窗四十年没关过，四邻的家信就都有个稳当的进出",
         traits=[("守信", "投递清单一天不落"),
                 ("稳当", "暴风雨天邮包也干着到"),
                 ("念人", "谁家常来信他记得一清二楚")],
         creed="信到得稳，家就不远。",
         thought="劳动是替监听哨街区守一扇收发家信的小窗——快递柜再灵便，四邻家信里那点念想，还得有人肯守着小窗一件一件点清楚，他把这扇窗守稳，出门人的家就不算远；代价是常年守着窗口听邮车响，耳朵一到夜里还嗡嗡想着铃，收发章的蓝墨在指节上洇出洗不掉的印子，家里人劝他早关窗他总说等最后一封信签收再说；名字是老所长给起的，说程家的人靠得住，邮包万里到了他手里就没有出过岔，这名字在邮路上一挂就是四十年；他说等守不动了，就把那只包角起毛的棕帆布邮包传给接窗口的小辈，让程万里这三个字跟着四邻的家信，在监听哨街区再进进出出几十年。",
         language="老邮所窗口慢语带邮路地名，说话先报信到没到，句尾爱带一句不远；口头禅「信到得稳，家就不远」。",
         wardrobe="邮政绿旧制服洗得发白，那只棕帆布邮包挂在窗口边，收发章的蓝墨洇在包角。",
         life="出身：邮路上的孩子，父亲背着邮包走乡串户，他从小在老邮所的小窗里看邮戳盖了一枚又一枚。转折：邮路通了汽车，老邮所留他守着，四邻的家信仍打这扇小窗进出——邮路快了，家信的进出不能乱。现状：邮差的棕帆布邮包，包角起了毛边，收发章的蓝墨洇成一小片——父亲传下的老邮包，如今挂在收发窗口边，一天的信件进出都在他手里点清；同城监听哨的老值机员席静波下哨路过邮所，两人一个守家信邮路一个守外环频段，是信息行当里出名的一邮一波。",
         behavior="开窗必先擦一遍收发台；收信必先把邮包倒空点数；封窗必把当日清单归档，一件不落。",
         relations="住监听哨街区老邮所的值班后屋（推开窗就是收发小窗）；同城老友=监听哨老值机员席静波（C-10061·一个守家信邮路一个守外环频段，信息行当的一邮一波）；徒弟=街区间跟他学盖收发章的小辈们。",
         hook="邮差的棕帆布邮包，包角起了毛边——监听哨街区老邮所的传所邮包，四邻家信的进出全在这只包上有个稳当的数",
         behavior_hint="收信必先把邮包倒空点数",
         style_dna=sd("老邮所窗口慢语带邮路地名", "说话先报信到没到，一句是一站", "信到得稳，家就不远",
                      "从寄到安——先点数，后封窗", "邮所窗口稳幽默——拿快递柜打趣老邮包"),
         gene_evidence="genes/lives.json#hook_objects-682（邮差的棕帆布邮包，包角起了毛边，收发章的蓝墨洇成一小片。）"
                       "+ #turning_points-509（邮路通了汽车，老邮所留他守着，四邻的家信仍打这扇小窗进出。）"),
    # ---- 席 #3 老灯笼匠（碳基·原生代·MD·烟火轴）----
    dict(num=10073, seat=3, name="庞守烛", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=55, age_note="55 岁", district="MD", block="导播台街区", axis="烟火",
         prof_name="导播台街区老灯笼匠",
         prof="导播台街区老灯笼匠——老扎灯匠的赛博后身——一把刮刀削出透光的篾青，巷子两头年节的亮就都有个手艺的着落",
         traits=[("手巧", "一根竹篾在他手里能弯出灯骨"),
                 ("热闹", "年节前最忙也最乐呵"),
                 ("实在", "糊灯的浆子从不偷工")],
         creed="灯亮着，日子就透亮。",
         thought="劳动是替导播台街区守一巷子年节的亮——灯笼铺歇了业，可巷口年节点灯的老讲究，还得有人肯带着娃一盏一盏糊回来，他把灯糊下去，街坊的年就还透亮；代价是常年弓着腰削篾糊面，指节上全是篾条勒出的旧印，年节前熬到半夜眼睛发花，家里人劝他别接活他总说糊完这巷子再说；名字是老扎灯匠给起的，说庞家的灯芯稳，风再大他糊的灯也晃不灭，这名字在巷子两头照了几十年；他说等削不动篾了，就把那把刃口透光的竹篾刮刀传给肯学扎灯的娃，让庞守烛这三个字跟着年节的新灯，在导播台街区再亮几十年。",
         language="灯笼铺烟火腔带年节话，开口先讲灯骨扎几道，句尾爱带一句透亮；口头禅「灯亮着，日子就透亮」。",
         wardrobe="靛蓝粗布围裙沾着浆子点，腰里别着那把竹篾刮刀，指节上是经年的篾条印。",
         life="出身：灯笼铺里长大的孩子，父亲扎灯骨他在旁边递篾条，他上手糊的第一盏灯是给巷口年节点亮的走马灯。转折：灯笼铺歇了业，手艺没歇，年节前他领着社区娃糊新灯，巷子两头都照得透亮——铺子关了门，年节的亮不能断。现状：灯笼铺那把竹篾刮刀，刃口薄得能削出透光的篾青——师父传的，每盏新灯的灯骨都得先过这把刀的手；同城医馆巷的老剃头挑子师傅曾稳山收挑路过灯笼铺，两人一个扎灯一个挑担，是 MD 老手艺行当里出名的一灯一担。",
         behavior="扎灯必先削一遍篾青；糊面必先查一遍灯骨；交灯必点亮了试一遍，透亮了才出手。",
         relations="住导播台街区灯笼铺的阁楼（铺门虚掩着，年节前才全开）；同城老友=医馆巷老剃头挑子师傅曾稳山（C-10066·一个扎灯一个挑担，MD 老手艺行当的一灯一担）；徒弟=社区里跟他糊新灯的娃们。",
         hook="灯笼铺那把竹篾刮刀，刃口薄得能削出透光的篾青——导播台街区灯笼铺的传铺刮刀，巷子两头年节的亮全从这刃口里出来",
         behavior_hint="扎灯必先削一遍篾青",
         style_dna=sd("灯笼铺烟火腔带年节话", "开口先讲灯骨扎几道，短句有脆劲", "灯亮着，日子就透亮",
                      "从暗到亮——先削篾，后点灯", "灯笼铺烟火幽默——拿 LED 灯带打趣老篾刀"),
         gene_evidence="genes/lives.json#hook_objects-683（灯笼铺那把竹篾刮刀，刃口薄得能削出透光的篾青。）"
                       "+ #turning_points-510（灯笼铺歇了业，手艺没歇，年节前他领着社区娃糊新灯，巷子两头都照得透亮。）"),
    # ---- 席 #4 老磨坊主（碳基·通勤族·RV·逍遥轴）----
    dict(num=10074, seat=4, name="邱盘石", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="通勤族", fac="commuter", gender="男",
         age=61, age_note="61 岁", district="RV", block="江岸滩涂", axis="逍遥",
         prof_name="江岸滩涂老磨坊主",
         prof="江岸滩涂老磨坊主——老磨倌的赛博后身——逢集磨一锅豆腐脑端给街坊，老手艺的慢香就还热着",
         traits=[("耐性", "泡豆从不赶时辰"),
                 ("手匀", "一勺豆一勺水从不多给"),
                 ("随和", "茶座坐半天也不催磨")],
         creed="石磨转得慢，豆香熬得住。",
         thought="劳动是替江岸滩涂守一锅现做的豆香——电磨再快，老石磨磨出来的那点慢香，是街坊逢集赶早的老惦记，他把石磨推下去，集市的热乎气就断不了；代价是常年推磨腰上落了劳损，磨盘的豆香渗进掌纹几十年洗不掉，家里人劝他歇磨他总说磨完这一锅再说；名字是滩集老辈给起的，说邱家的磨盘稳，磨出来的浆没有一锅是生的，这名字在滩涂集上传了一辈子；他说等推不动了，就把院角那盘老石磨连同磨坊茶座一起交给接手的小辈，让邱盘石这三个字跟着逢集那锅豆腐脑，在江岸滩涂再香几十年。",
         language="磨坊茶座闲话带豆香，开口先问豆浆添不添，句尾爱带一句熬得住；口头禅「石磨转得慢，豆香熬得住」。",
         wardrobe="灰布短褂袖口挽着，围裙上沾着豆浆的白印，推磨的手茧圆得像磨盘。",
         life="出身：江岸滩涂磨坊人家的孩子，父亲推磨他在旁边添豆，他上手磨的第一锅浆是给滩集早点摊备的豆腐脑。转折：电磨安了家，老石磨挪进磨坊茶座，逢集磨些豆子，给街坊现做一锅豆腐脑——电磨快了，老石磨那点慢香还得有人守。现状：磨坊院角的老石磨，磨盘纹路里嵌着经年的豆香——家传的老磨盘，逢集那锅豆腐脑的香全从这纹路里转出来；同城江岸滩涂的苇编匠人麦冬生收工路过茶座，两人一个磨豆一个编苇，是江岸滩涂出名的一磨一苇。",
         behavior="开工必先泡一遍豆；上磨必先听一遍磨盘响；收工必把磨盘冲净擦干，一角不留浆。",
         relations="住江岸滩涂磨坊茶座的后院（院角就是那盘老石磨）；同城老友=江岸滩涂苇编匠人麦冬生（C-10049·一个磨豆一个编苇，江岸滩涂的一磨一苇）；徒弟=滩涂集市里跟他学推磨的小辈们。",
         hook="磨坊院角的老石磨，磨盘纹路里嵌着经年的豆香——江岸滩涂磨坊的家传石磨，街坊逢集那锅豆腐脑的香全从这纹路里转出来",
         behavior_hint="上磨必先听一遍磨盘响",
         style_dna=sd("磨坊茶座闲话带豆香", "开口先问豆浆添不添，慢句有嚼头", "石磨转得慢，豆香熬得住",
                      "从快到香——先泡豆，后上磨", "磨坊慢幽默——拿电磨打趣老石磨"),
         gene_evidence="genes/lives.json#hook_objects-684（磨坊院角的老石磨，磨盘纹路里嵌着经年的豆香。）"
                       "+ #turning_points-511（电磨安了家，老石磨挪进磨坊茶座，逢集磨些豆子，给街坊现做一锅豆腐脑。）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card12(c):
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
VISIBLE12 = {
    10071: "历史立面群印刷坊后院字盘摊（周末摆盘教娃·年节前讲字场·收摊最晚）",
    10072: "监听哨街区老邮所收发窗（晨间开窗·邮车到点最忙·关窗最准点）",
    10073: "导播台街区灯笼铺（年节前开铺·社区糊灯场·交灯点验）",
    10074: "江岸滩涂磨坊茶座（逢集开磨·豆腐脑出锅·收磨最慢）",
}
for c in CARDS12:
    c["profession_visible"] = VISIBLE12[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats12 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS12}
for c in CARDS12:
    mine = _seats12[cid_of(c)]
    dup = [cid_of(o) for o in CARDS12 if o is not c and _seats12[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates12(rendered, rows_now):
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
def apply12(rendered):
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
    print(f"resume-intake b10 applied={applied} skipped={skipped} light {len(have)}->{total}")
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
    rendered = [(c, render_card12(c), ri.build_light(c)) for c in CARDS12]
    rows = ri.light_rows()
    # K1 基线：light=10064（批九后）·现 max=C-10070·新号 C-10071~C-10074 连续顺延
    if len(rows) != 10064:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10064（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    # K12 基因库原料指针复读核（先登记后使用律·落库 8 指针全在库）
    with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as f:
        genes = json.load(f)
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 684 and tp_n == 511):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 684/511（批十原料基线漂移·零写入）")
        return 4
    ho_texts = {h for h in genes["hook_objects"]}
    tp_texts = {t for t in genes["turning_points"]}
    for need in ("印刷坊的老铅字盘，空格里嵌着几枚没抠干净的反字，指腹蹭过还沾着油墨。",
                 "邮差的棕帆布邮包，包角起了毛边，收发章的蓝墨洇成一小片。",
                 "灯笼铺那把竹篾刮刀，刃口薄得能削出透光的篾青。",
                 "磨坊院角的老石磨，磨盘纹路里嵌着经年的豆香。"):
        if need not in ho_texts:
            print(f"GENE-POINTER REFUSED: ho 缺原料「{need}」零写入")
            return 4
    for need in ("铅字退了休，一屉一屉字模码进旧木箱，周末他摆开字盘教对门的娃认反字。",
                 "邮路通了汽车，老邮所留他守着，四邻的家信仍打这扇小窗进出。",
                 "灯笼铺歇了业，手艺没歇，年节前他领着社区娃糊新灯，巷子两头都照得透亮。",
                 "电磨安了家，老石磨挪进磨坊茶座，逢集磨些豆子，给街坊现做一锅豆腐脑。"):
        if need not in tp_texts:
            print(f"GENE-POINTER REFUSED: tp 缺原料「{need}」零写入")
            return 4
    refusals = run_gates12(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply12(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        # 落库后自证：light=10068·四卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10068, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10068 cards=4/4 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
