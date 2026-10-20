#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批十九·人口工厂 intake 5 席碳基原生代 C-10101~C-10105（R1814）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#711-715 / tp#538-542（R1814 先登记后使用·近重预检 0 命中）。
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import intake_batch17 as b17
import resident_intake as ri

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"
BATCH = "批十九"
MAX_ID = 10100
PRE_LIGHT = 10094
POST_LIGHT = 10099

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS19 = [
    # ---- #1 磨刀匠（碳基·原生代·NS·实在轴）----
    dict(num=10101, seat=1, name="韩德茂", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=68, age_note="68 岁", district="NS", block="北外滩巷口青石摊",
         axis="实在",
         prof_name="磨刀匠",
         prof="磨刀匠——过去挑着长凳走街串巷的磨刀师傅的赛博后身——"
              "让一条巷子的刀都回到能切豆腐的人。",
         traits=[("实在", "磨前先说这刀还能用几年"), ("手准", "角度一分不差"),
                 ("不急", "一把刀压三遍石，不赶工")],
         creed="刀钝了不怪刀，怪没人磨",
         thought="劳动是替一条巷子把日子磨快——刀用久了刃口卷，他先看钢火再看木柄，粗石开锋细石收口，"
                 "磨完在围裙上蹭三下再递回去；代价是腰弯得久了直不起来，冬天手裂口子，儿子让他别干了，"
                 "他说巷子里喊一声还得有人应。名字是父亲按辈分取的，德茂两个字，说人要厚，家才茂。等推不动石了，"
                 "就把那块青石立在门口，谁来磨都自己动手，他坐在旁边看着说两句。",
         language="巷口的老实腔，话少，一句顶一句，爱用「能用」和「值当」两个词下判断。",
         wardrobe="深蓝布围裙，两只袖套，腰间一挂帆布包，里面插着粗细两块磨刀石。",
         life="十六岁跟着挑长凳的师傅走街，后来在巷口支了个固定摊，一摆四十多年。",
         behavior="每天清早把青石泡透，先磨自己那把菜刀试石头。",
         behavior_hint="磨之前先用拇指横着刮一遍刃口，听有没有卷。",
         relations="北外滩半条巷子的刀都从他摊上过；和弄堂茶馆的掌柜换茶叶，他帮人磨刀不收钱。",
         hook=_G["hook_objects"][710],
         style_dna=sd("巷口老实腔", "短句+判断词收尾", "先看东西再说话，一句一个准",
                      "平稳（不夸不贬）", "干巴幽默（拿自己的石头说事）"),
         profession_visible="北外滩巷口青石摊（清早出摊·午后收）",
         gene_evidence=ev(711, 538)),
    # ---- #2 裱画师（碳基·原生代·MD·细致轴）----
    dict(num=10102, seat=2, name="温来娣", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=55, age_note="55 岁", district="MD", block="老城书画街裱画间",
         axis="细致",
         prof_name="裱画师",
         prof="裱画师——过去在书画街给人托画心的装裱师傅的赛博后身——"
              "让一张软塌塌的纸站起来见人的人。",
         traits=[("细致", "一道边对三次"), ("稳重", "手上湿气重就不碰画心"),
                 ("认人", "谁家的画收过，心里有本账")],
         creed="画的命在纸背，不在正面",
         thought="劳动是替人把心头的东西挂起来——画心薄，一上手就要定住，她用排笔一遍遍刷浆，把气泡擀干净，"
                 "上墙绷平，等干透了再揭；代价是常年弯腰，眼睛也熬得近，配镜一年比一年厚。母亲说这活养不出家，"
                 "她也没换。名字是外婆按旧俗起的，来娣两个字，说人来了就热闹。等手上抖了，就教来学的年轻人"
                 "先学洗排笔，笔洗不干净，画就活不成。",
         language="书画街的软腔，说话轻，爱用「慢慢」和「别急」，讲活计爱从纸讲起。",
         wardrobe="浅灰罩衫，袖口自己缝的松紧，指腹上一层薄浆痕，头上别一根木簪。",
         life="十九岁进书画街当学徒，跟着老师傅学托裱；老师傅走了以后，她把那间小间租下来自己干。",
         behavior="每天进门先洗手，再把案上的湿布换一遍。",
         behavior_hint="碰画心之前先在手背上试一次浆的稠度。",
         relations="常替老街坊裱家传的字；和 MEDIA 城的修片师换纸，一个修画一个修照片。",
         hook=_G["hook_objects"][711],
         style_dna=sd("书画街软腔", "轻句+劝语收尾", "凡事先说纸，再说人",
                      "温（难处一笔带过）", "淡幽默（拿自己的镜片说笑）"),
         profession_visible="老城书画街裱画间（上午绷画·午后装框）",
         gene_evidence=ev(712, 539)),
    # ---- #3 锁匠（碳基·原生代·GM·沉稳轴）----
    dict(num=10103, seat=3, name="裴永栓", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=49, age_note="49 岁", district="GM", block="老游戏城后巷配钥铺",
         axis="沉稳",
         prof_name="锁匠",
         prof="锁匠——过去在街边配钥匙开锁的师傅的赛博后身——"
              "让人能进自己家门的人。",
         traits=[("沉稳", "开了不催，进不去也不慌"), ("守信", "开了哪家门，从不往外说"),
                 ("清楚", "哪一排老楼的锁芯是什么牌子，他记得")],
         creed="钥匙是给出去的信，得认得回来",
         thought="劳动是替人把一道门重新打开——老锁芯卡住是弹子磨偏了，他拿听针贴着锁面一点点拨，"
                 "拨对了手上会有一声轻响；代价是常年弯着脖子凑近锁孔，颈椎不好，晚上得仰着睡。"
                 "名字是爷爷取的，永栓两个字，说门上的栓要能一直栓得牢。等手不稳了，就把那台旧锉机擦干净"
                 "摆回门口，写上「自助配钥匙，钱放铁盒」，让忘带卡的人自己来。",
         language="后巷的干脆腔，说话短，答话只答一半，剩下的用动作补。",
         wardrobe="深灰夹克，腰间挂一串样钥匙，右手食指关节有块老茧，帽檐压得低。",
         life="跟着舅舅学开锁配钥匙，二十岁在游戏城后巷支了铺子；电子门禁普及后，他兼着修门锁。",
         behavior="每天开门先把铁盒里的零钱数一遍，记在小本上。",
         behavior_hint="开锁前先问一句「屋里有人的东西你都知道吗」。",
         relations="后巷半条街的住户都认得他；替老游戏城的机修师傅配过机箱钥匙，两个人常换烟换茶。",
         hook=_G["hook_objects"][712],
         style_dna=sd("后巷干脆腔", "半句+动作补足", "先办事再开口",
                      "克制（不打听别人家事）", "冷幽默（把锁说成有脾气）"),
         profession_visible="老游戏城后巷配钥铺（早开门·夜里接急活）",
         gene_evidence=ev(713, 540)),
    # ---- #4 补锅匠（碳基·原生代·RV·豁达轴）----
    dict(num=10104, seat=4, name="詹有福", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=72, age_note="72 岁", district="RV", block="江边旧货棚补锅摊",
         axis="豁达",
         prof_name="补锅匠",
         prof="补锅匠——过去在江边敲铁皮补锅的老师傅的赛博后身——"
              "让一口漏锅再多烧几年的人。",
         traits=[("豁达", "补不好也笑着退钱"), ("手快", "一个洞三锤就封"),
                 ("会算", "补三次的钱还不够买新锅，她直说")],
         creed="锅漏了不怕，怕的是人嫌麻烦",
         thought="劳动是替人家把还能用的东西留住——铁锅裂了缝，她先拿剪子把缝口剪齐，再贴一块铁皮，"
                 "从里往外敲，一锤一锤把边咬死，敲完灌水试漏；代价是耳朵被锤声磨得发闷，手指头上常年有烫过的旧痕。"
                 "名字是丈夫起的，有福两个字，说这一生有个饭碗就够。等敲不动了，就把锤子挂在棚子上，"
                 "谁来借都行，只交代一句「敲轻点，锅薄」。",
         language="江边的爽利腔，说话带笑，爱把价钱和人情一起算清。",
         wardrobe="靛蓝罩褂，头上包一块蓝布，小铁锤插在腰间的绳结里，脚上一双胶鞋。",
         life="年轻时在江边航运社做后勤，跟着老师傅学补锅；退休后在旧货棚里支摊，替人修锅修桶。",
         behavior="每天出摊先烧一壶水，试今天补的第一口锅。",
         behavior_hint="敲之前先敲一下锅底，听声音薄不薄。",
         relations="江边渔民常拿桶来找她；和渡轮检票员换鱼换菜，一个补锅一个捎带。",
         hook=_G["hook_objects"][713],
         style_dna=sd("江边爽利腔", "笑头+明白话收尾", "先算给人听，再动手",
                      "豁达（赔了也笑）", "自嘲式幽默（拿自己的耳朵说事）"),
         profession_visible="江边旧货棚补锅摊（上午出摊·午后收）",
         gene_evidence=ev(714, 541)),
    # ---- #5 说书先生（碳基·原生代·NS·念旧轴）----
    dict(num=10105, seat=5, name="方鹤鸣", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="NS", block="弄堂茶馆二楼说书角",
         axis="念旧",
         prof_name="说书先生",
         prof="说书先生——过去在茶馆里一拍醒木开讲的说书人的赛博后身——"
              "让一屋子人一起记起同一段事的人。",
         traits=[("念旧", "老段子一句不改"), ("记性好", "三百回书，人名一个不错"),
                 ("看人", "一屋子什么心思，他扫一眼就知道")],
         creed="故事讲得再旧，只要有人听就是新的",
         thought="劳动是替一屋子人守着一个共同的记性——开讲前先看座，人多讲长的，人少讲短的，讲到关节处"
                 "把扇子一收，留一口气等人追；代价是嗓子磨得哑，秋冬一到就咳嗽，徒弟劝他录下来放，"
                 "他说放出来的没有屋里的回声。名字是母亲取的，鹤鸣两个字，说声音要传得远。等讲不动了，"
                 "就把那把缺骨扇交给来听书听得最久的年轻人，让他接着敲醒木。",
         language="说书的腔，句子有起落，爱用「话说」「且听」起头，讲完必留一句扣子。",
         wardrobe="藏青长衫，袖口磨白，桌上一把缺骨折扇，扇边压着一块旧醒木。",
         life="少年时在弄堂茶馆听书，跟着老说书人抄本子；老说书人走了，他接下了那张桌。",
         behavior="每天午后先到茶馆坐一刻钟，听楼下人说话。",
         behavior_hint="开讲前把醒木在手掌上掂两下，试手感。",
         relations="弄堂茶馆的掌柜给他留着二楼那张桌；常和磨刀的韩德茂换一段巷子里的新鲜事。",
         hook=_G["hook_objects"][714],
         style_dna=sd("说书腔", "起落句+扣子收尾", "先看座再开口，讲三分留七分",
                      "热（到关节处会慢下来）", "说书式幽默（抖包袱不解释）"),
         profession_visible="弄堂茶馆二楼说书角（午后一场·晚了收）",
         gene_evidence=ev(715, 542)),
]


def main():
    freeze = os.path.join(CO, "state", "registry-freeze.lock")
    if os.path.isfile(freeze):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
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
    if not (len(genes["hook_objects"]) == 715 and len(genes["turning_points"]) == 542):
        print("GENE-BASELINE REFUSED: ho/tp != 715/542（批十九原料基线漂移·零写入）")
        return 4
    for idx in range(710, 715):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(537, 542):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS19
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS19]
    refusals = b17.run_gates17(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = b17.apply17(rendered)
    if rc == 0:
        b17.POST_LIGHT = POST_LIGHT
        rc = b17.post_closeout()
    return rc


if __name__ == "__main__":
    sys.exit(main())