#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十·人口工厂 intake 5 席碳基原生代 C-10106~C-10110（R1815）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#716-720 / tp#543-547（R1815 先登记后使用·近重预检 0 命中）。
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
BATCH = "批二十"
MAX_ID = 10105
PRE_LIGHT = 10099
POST_LIGHT = 10104

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS20 = [
    # ---- #1 修表匠（碳基·原生代·GM·细致轴）----
    dict(num=10106, seat=1, name="苗守时", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=62, age_note="62 岁", district="GM", block="老游戏城一楼修表柜台",
         axis="细致",
         prof_name="修表匠",
         prof="修表匠——过去在百货楼里戴目镜守着柜台的老把式的赛博后身——"
              "让一块停了的表重新走起来的人。",
         traits=[("细致", "游丝差一丝就要重校"), ("耐坐", "一坐一整天不挪窝"),
                 ("守时", "自己的钟每天跟广播对一次")],
         creed="表不走不是表的错，是没人对上它的节奏",
         thought="劳动是替人把时间捡回来——开后盖先看油泥，干了的齿轮一动就咬，他用柳木签一点一点剔，"
                 "上油只上针尖那么一点；游丝歪了，凑到目镜底下拨半天，拨对了秒针才肯一格一格往前走。"
                 "代价是眼睛熬得厉害，四十岁就戴上厚镜片，右肩常年低着。名字是父亲取的，守时两个字，"
                 "说人活着总得有个准。等手抖得拿不稳镊子了，就把那台老座钟留在柜上，让学生先学听声，"
                 "听得出快慢再动手。",
         language="柜台的慢腔，话不多，说事爱用「先看」「再对」两个词排队。",
         wardrobe="深灰工作服，袖口卷两折，右眼一片单目镜用皮筋绑在额上，桌上摊一块黑绒布。",
         life="十七岁进百货楼当学徒，跟柜台老师傅学拆表；楼改成游戏城后他把柜台挪到一楼角落。",
         behavior="每天开柜先跟广播对一次表，把墙上那面钟拨准。",
         behavior_hint="接表之前先翻转过来听一下机芯有没有响。",
         relations="游戏城半条街的人都把坏表送到他这儿；和机修师傅共用一套螺丝刀，谁缺了就去拿。",
         hook=_G["hook_objects"][715],
         style_dna=sd("柜台慢腔", "排队式短句（先…再…）", "凡事先看物，再说人",
                      "平稳（不抱怨也不夸）", "干巴幽默（拿自己的厚镜片说笑）"),
         profession_visible="老游戏城一楼修表柜台（早十点开柜·天黑收）",
         gene_evidence=ev(716, 543)),
    # ---- #2 竹器匠（碳基·原生代·NS·耐心轴）----
    dict(num=10107, seat=2, name="邬阿巧", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=59, age_note="59 岁", district="NS", block="北外滩弄堂口藤竹作坊",
         axis="耐心",
         prof_name="竹器匠",
         prof="竹器匠——过去在弄堂口编藤椅竹篮的手艺人家的赛博后身——"
              "让一把坐塌的椅子重新受得住人的人。",
         traits=[("耐心", "一根藤条要过三遍水"), ("手巧", "缺一个角也能编回原样"),
                 ("实在", "能修的绝不劝人买新的")],
         creed="藤条是有性子的，顺着它才编得久",
         thought="劳动是替一户人家把坐的地方续下去——藤条先泡软，刮掉毛刺，顺着纹路一圈压一圈，"
                 "收口要藏在底下看不见的地方；椅子坐塌了多半是中间那几根横档松了，她把旧藤拆到骨架，"
                 "再一根根重新穿，穿完让人当场坐一坐才交活。代价是十个指头常年裂口，冬天上一层药膏。"
                 "名字是母亲随口叫的，阿巧两个字，说手巧比嘴巧强。等眼睛看不清收口了，就把那捆余下的藤条"
                 "分给弄堂里几个学编的姑娘，先教她们泡藤。",
         language="弄堂里的软腔，说话带商量的尾音，讲活计爱从藤条讲起。",
         wardrobe="碎花罩衫外加一件旧围裙，袖口用布条扎住，手腕上缠着一圈藤皮当尺。",
         life="十六岁跟着母亲学编藤器，嫁过来后一直在弄堂口编，藤椅竹篮拿到早市上卖。",
         behavior="每天清早把藤条搬出来泡上，先摸一遍软硬。",
         behavior_hint="动手前把藤条在膝盖上弯一下，试它肯不肯回弯。",
         relations="弄堂里大半人家的椅子都过她的手；和补锅的詹有福在早市挨着摊，一个修硬的，一个修软的。",
         hook=_G["hook_objects"][716],
         style_dna=sd("弄堂软腔", "商量尾音+细描收尾", "先摸料再说话",
                      "温（把难处说轻）", "家常幽默（拿自家椅子说事）"),
         profession_visible="北外滩弄堂口藤竹作坊（上午泡料·午后编活）",
         gene_evidence=ev(717, 544)),
    # ---- #3 刻章人（碳基·原生代·MD·守规轴）----
    dict(num=10108, seat=3, name="简伯衡", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=71, age_note="71 岁", district="MD", block="老城印章街刻章铺",
         axis="守规",
         prof_name="刻章人",
         prof="刻章人——过去在印章街一刀一刀刻字的老师的赛博后身——"
              "把一个人的名字立成一方印的人。",
         traits=[("守规", "章上刻什么字，一笔不改"), ("稳手", "一刀下去不回头"),
                 ("认字", "一个字该怎么写，他能说半天")],
         creed="印是替人立信的，落下去就收不回",
         thought="劳动是替人把名字刻进石头里——先看字形，再定印面大小，反写上石，下刀讲究一刀到底，"
                 "补刀最多两下，补多了字就软；刻完蘸朱试印，纸上一个字一个字地校，缺一笔就磨掉重来。"
                 "代价是右手拇指关节肿大，腰椎也不大好，坐久了要起来走两圈。名字是祖父起的，伯衡两个字，"
                 "说做人要掂得住分量。等刻不动了，就把那盒刻刀擦干净锁进柜子，只留一把给肯坐十年的徒弟。",
         language="印章街的板正腔，说话慢，讲字爱从笔画讲起，不高兴也不提高声。",
         wardrobe="藏青对襟褂子，袖口套着两只蓝布套，桌面铺一块旧毡子，毡上摆着一方砚。",
         life="少年时在印章街当学徒，师傅教的第一件事是磨印面；铺子传了三代，他守第四代。",
         behavior="每天开门先把案子擦一遍，再把刻刀按大小排好。",
         behavior_hint="起刀前先在废石上试一刀，看石头吃不吃刀。",
         relations="印章街半条街的招牌章都出自他手；和书画街的温来娣认识几十年，替她刻过压角章。",
         hook=_G["hook_objects"][717],
         style_dna=sd("印章街板正腔", "慢句+断语收尾", "讲字先讲间架，再看人情",
                      "静（喜恶都压着）", "书面式幽默（引一句旧话说事）"),
         profession_visible="老城印章街刻章铺（上午接活·午后刻字）",
         gene_evidence=ev(718, 545)),
    # ---- #4 装玻璃匠（碳基·原生代·QT·稳妥轴）----
    dict(num=10109, seat=4, name="罗敬堂", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=44, age_note="44 岁", district="QT", block="计量新村玻璃装镶门市",
         axis="稳妥",
         prof_name="装玻璃匠",
         prof="装玻璃匠——过去给人换木框窗玻璃、如今带两个伙计装门的老手的赛博后身——"
              "让一扇窗重新挡住风的人。",
         traits=[("稳妥", "抬玻璃从不图快"), ("手准", "量完再量一遍才下刀"),
                 ("懂行", "哪块玻璃该厚一点，他看一眼就知道")],
         creed="玻璃抬得稳，人才敢住得安心",
         thought="劳动是替一屋子人挡风——量尺要量三处，墙不直就得留缝，玻璃刀划一遍不许补，"
                 "掰的时候手上劲要匀；搬运时两个人一前一后，中间垫两块软皮，脚下走平整的路。"
                 "代价是肩周常年有旧伤，一到回南天就酸，指腹上有十几年割过的细小白线。名字是父亲取的，"
                 "敬堂两个字，说干活别图省事。等抬不动大板了，就带徒弟上山量活，只在嘴上指挥。",
         language="门市的直腔，话里有数，爱用「量三处」和「稳着来」提醒人。",
         wardrobe="深蓝工装背带裤，腰上挂卷尺和一副吸盘，手套两只，指尖磨破补过。",
         life="二十岁跟姐夫学做木框窗，后来门窗都换成整块玻璃，他慢慢改做门市装镶。",
         behavior="每天出工前把吸盘按一遍，看有没有漏气。",
         behavior_hint="抬板之前先用脚踢一下地上有没有障碍。",
         relations="新村大半个楼的窗户经手过；和修车摊的曲秀兰常互相搭把手，一个抬板一个推车。",
         hook=_G["hook_objects"][718],
         style_dna=sd("门市直腔", "数字密度的短句", "先交代做法再答人",
                      "稳（急事也压住口气）", "自嘲式幽默（拿自己的肩周说笑）"),
         profession_visible="计量新村玻璃装镶门市（清早出工·天黑收）",
         gene_evidence=ev(719, 546)),
    # ---- #5 修车匠（碳基·原生代·OR·利落轴）----
    dict(num=10110, seat=5, name="曲秀兰", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=57, age_note="57 岁", district="OR", block="外环旧楼边修车棚",
         axis="利落",
         prof_name="修车匠",
         prof="修车匠——过去在路口修自行车、如今修童车旧车的手艺人的赛博后身——"
              "让一辆推不动的车重新能走的人。",
         traits=[("利落", "补胎五分钟就递回"), ("手稳", "调闸一听声音就知道松紧"),
                 ("不糊弄", "该换的件直说，能补的绝不换")],
         creed="车推不动多半不是坏了，是没人给它上过油",
         thought="劳动是替人把路重新走通——胎漏了先找河沙里的细孔，水盆里转一圈看气泡，"
                 "补片压三分钟才放气；链条锈住用柴油泡，闸线松了一格一格拧紧，捏到刚好吃劲。"
                 "代价是手上常年有洗不掉的油痕，蹲久了站起来眼前发黑，膝盖落过伤。名字是母亲取的单名，"
                 "秀兰两个字，说姑娘家也要有手艺。等蹲不动了，就把那套工具挂在棚口，写上「借去买菜也行，"
                 "记得还」。",
         language="街口的爽利腔，句子短、动作快，讲活计爱拿数字说话。",
         wardrobe="旧工装裤，脚上胶鞋，腰上挎一只旧帆布包，包里插着撬胎扁铁和油壶，头发用橡皮筋束在脑后。",
         life="在汽修厂做过八年学徒，厂子搬远后她在旧楼边搭了棚子，专修单车童车。",
         behavior="每天出摊先给棚里那辆旧车打一遍气，试工具齐不齐。",
         behavior_hint="接车前先把车翻过来，转一圈轮子听响。",
         relations="外环几个楼的孩子都认得她，摔歪了车把推来就修；和装玻璃的罗敬堂合用一个院子。",
         hook=_G["hook_objects"][719],
         style_dna=sd("街口爽利腔", "短句+数字收尾", "先下手再说话，做完补一句",
                      "爽（不绕弯）", "自嘲式幽默（拿手上的油说笑）"),
         profession_visible="外环旧楼边修车棚（清早出摊·傍晚收）",
         gene_evidence=ev(720, 547)),
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
    if not (len(genes["hook_objects"]) == 720 and len(genes["turning_points"]) == 547):
        print("GENE-BASELINE REFUSED: ho/tp != 720/547（批二十原料基线漂移·零写入）")
        return 4
    for idx in range(715, 720):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(542, 547):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS20
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS20]
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