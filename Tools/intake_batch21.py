#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十一·人口工厂 intake 5 席碳基原生代 C-10111~C-10115（R1816）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#721-725 / tp#548-552（R1816 先登记后使用·gene_nearcheck 0 近重）。
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
BATCH = "批二十一"
MAX_ID = 10110
PRE_LIGHT = 10104
POST_LIGHT = 10109

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS21 = [
    # ---- #1 改衣匠（碳基·原生代·GM·惜物轴）----
    dict(num=10111, seat=1, name="潘月娥", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=63, age_note="63 岁", district="GM", block="老游戏城二楼改衣摊",
         axis="惜物",
         prof_name="改衣匠",
         prof="改衣匠——过去在成衣厂踩缝纫机、如今替人改裤脚的师傅的赛博后身——"
              "让一件旧衣裳重新合身的人。",
         traits=[("惜物", "一件衣裳能改三回"), ("手稳", "裤脚两只量成一个长短"),
                 ("不催人", "再急的活也等熨平才交")],
         creed="衣裳旧了未必就该丢，改一改还能再穿几年",
         thought="劳动是替人把一件衣裳再穿几年——先看肩缝，再看袖口，线头松了用同色的线走一遍暗针，"
                 "裤脚长短要两只一块量，缝完倒过来熨一遍，不让人一眼看出改过。代价是颈椎不好，"
                 "低头久了要仰一仰，指头上有针眼留下的硬点。名字是外婆取的，月娥两个字，"
                 "说姑娘家得守得住手里的活。等眼花了，就把那台脚踏缝纫机搬到摊口，让学生先学踩空车。",
         language="摊子上的软腔，说话慢半拍，讲活爱从布料的厚薄讲起。",
         wardrobe="灰蓝罩衫外面系一条围裙，口袋里插着软尺和一小卷线，脖子上挂一把小剪用绳拴着。",
         life="十七岁在成衣厂踩缝纫机，厂子搬到郊区后她在游戏城二楼租了半个摊位改衣。",
         behavior="每天上摊先把缝纫机空踩两脚，听声音顺不顺。",
         behavior_hint="接过衣裳先翻里子看缝口松没松。",
         relations="楼上楼下的人都把改裤脚的活交到她这儿；和一楼修表的苗守时挨着，谁的灯泡坏了互相借梯子。",
         hook=_G["hook_objects"][720],
         style_dna=sd("摊子软腔", "慢句+对照收尾", "先看缝口，再谈人",
                      "温（把难处说成小事）", "家常幽默（拿自己踩空车说笑）"),
         profession_visible="老游戏城二楼改衣摊（上午十点开摊·天黑收）",
         gene_evidence=ev(721, 548)),
    # ---- #2 补锅匠（碳基·原生代·NS·实在轴）----
    dict(num=10112, seat=2, name="詹守炉", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="NS", block="北外滩老街补锅铺",
         axis="实在",
         prof_name="补锅匠",
         prof="补锅匠——过去挑着风箱走街串巷锔锅的手艺人的赛博后身——"
              "让一口漏了的锅重新盛得住水的人。",
         traits=[("实在", "能锔的不劝人换"), ("手上准", "补丁压边不差一线"),
                 ("肯吃亏", "街坊的锅先修后收钱")],
         creed="锅是吃饭的家伙，能补的就不该当废铁扔",
         thought="劳动是替一户人家把灶上的活续下去——漏眼先用小锤把边敲平，补丁贴合了再一圈一圈敲实，"
                 "铆钉要砸得刚好，砸重了铁皮就裂；铝锅薄，火候只在锤尖上，手劲过头就成筛子。"
                 "代价是两只耳朵背得早，常年听锤声；右腕落下老伤，阴天就疼。名字是户口本上的，"
                 "守炉两个字，说守着灶别断了火。等站不动了，就把那只小铁砧留在铺门口，让人知道这行还有人。",
         language="老街的实腔，话不多，一句是一句，讲活爱用「敲三下」「差一线」。",
         wardrobe="深蓝旧布褂，腰上系一条皮带挂小锤，袖子挽到手肘，手臂上一片旧烫痕。",
         life="十六岁跟着父亲挑担补锅，后来街面固定下来，他在老街租了半间铺面。",
         behavior="每天开门先把风箱拉两下，看火膛通不通。",
         behavior_hint="接锅先倒半碗水，看从哪个角渗出来。",
         relations="老街几户人家的锅都过他的手；和弄堂口编藤椅的邬阿巧在早市挨着摊。",
         hook=_G["hook_objects"][721],
         style_dna=sd("老街实腔", "短句+数字收尾", "先说做法，再答人",
                      "稳（急也不喊）", "干巴幽默（拿自己的耳背说笑）"),
         profession_visible="北外滩老街补锅铺（清早开门·天黑收）",
         gene_evidence=ev(722, 549)),
    # ---- #3 冲印师（碳基·原生代·QT·讲究轴）----
    dict(num=10113, seat=3, name="岑明远", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=52, age_note="52 岁", district="QT", block="计量新村楼里暗房冲印房",
         axis="讲究",
         prof_name="冲印师",
         prof="冲印师——过去在照相馆暗房里调药水、晒放大的老师的赛博后身——"
              "让一张纸上的影像慢慢长出来的人。",
         traits=[("讲究", "药水温度差半度就重配"), ("沉得住", "守一整夜不挪窝"),
                 ("眼毒", "一张底片该补多少光他一眼看出")],
         creed="影像得慢慢出来，急不得也骗不得",
         thought="劳动是替人把一天留住——显影液温到二十度，纸放下去先用夹子压住一角，"
                 "看影子一格一格浮上来，到七成捞出来，定影再走两遍；放大时把镜头一点一点对焦，"
                 "脸上的高光不能糊。代价是暗房红灯下守了三十年，眼睛怕亮，出门总戴一副深色镜。"
                 "名字是父亲取的，明远两个字，说看清楚远处才有近处。等眼睛撑不住了，就把那套药盆擦干净，"
                 "只留一台放大机，让学徒一台一台地练。",
         language="暗房里的低声，句子干净，讲活爱报数字，说事从温度说起。",
         wardrobe="深灰棉布工装，袖口收紧，胸前口袋里插一支蜡笔和一张对光纸，手上常年带一点药水味。",
         life="二十岁进照相馆当学徒学洗照片；数码相机普及后照相馆关门，他在新村的楼里留了一间暗房。",
         behavior="每天进暗房先把温度计插进药盆里看一眼。",
         behavior_hint="取底片之前先把手在毛巾上擦干。",
         relations="新村大半人家的证件照和老照片都经他的手；和玻璃装镶门的罗敬堂是邻居，替他换过窗上的玻璃。",
         hook=_G["hook_objects"][722],
         style_dna=sd("暗房低声", "数字密度的短句", "先报参数，再说判断",
                      "静（喜恶都收着）", "书面式幽默（拿红灯下待久说事）"),
         profession_visible="计量新村楼里暗房冲印房（午后开工·夜里出片）",
         gene_evidence=ev(723, 550)),
    # ---- #4 磨刀匠（碳基·原生代·OR·踏实轴）----
    dict(num=10114, seat=4, name="邵阿虎", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=68, age_note="68 岁", district="OR", block="外环早市磨刀摊",
         axis="踏实",
         prof_name="磨刀匠",
         prof="磨刀匠——过去扛着长凳走街吆喝的磨刀人的赛博后身——"
              "让一把钝了的刀重新吃得住劲的人。",
         traits=[("踏实", "一天磨几十把也不糊弄"), ("有手感", "刀口到哪一步该停手他知道"),
                 ("话直", "钝了就说钝了")],
         creed="刀口听机器磨不出手上那道劲",
         thought="劳动是替人把切菜的力气省下来——先用粗石开刃，角度压住不松，磨到卷边起来再换细石抛光，"
                 "最后在布条上荡两下；切肉的刀要留一点齿，切菜的刀要薄，剪刀中间那道内刃最难，"
                 "得用小圆石一点一点拱。代价是指节磨得粗大，冬天裂口，肩膀常年发酸。名字是母亲叫的，"
                 "阿虎两个字，说名字硬一点好养活。等推不动砂轮了，就把那条长凳摆在早市口，坐着磨。",
         language="早市上的粗腔，说得快，爱用「再两下」「差一点」。",
         wardrobe="旧棉袄外面套一件围裙，腰上挂一只水罐，凳脚边压着一块旧布。",
         life="年轻时在食堂后厨切菜，后来跟着街口的老师傅学磨刀，一磨四十年。",
         behavior="每天出摊先在长凳上坐下来晃两下，试凳腿稳不稳。",
         behavior_hint="接过刀先用拇指横着刮一下刃口，听那点涩。",
         relations="外环早市卖菜的都找他磨刀；和修车棚的曲秀兰共用早市一角，一个磨刀一个补胎。",
         hook=_G["hook_objects"][723],
         style_dna=sd("早市粗腔", "短句+动作起头", "先动手再下判断",
                      "直（不绕弯也不伤人）", "自嘲式幽默（拿手上的裂口说笑）"),
         profession_visible="外环早市磨刀摊（清早出摊·八点收）",
         gene_evidence=ev(724, 551)),
    # ---- #5 修伞匠（碳基·原生代·MD·和气轴）----
    dict(num=10115, seat=5, name="陆阿翠", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=55, age_note="55 岁", district="MD", block="老城巷口伞铺",
         axis="和气",
         prof_name="修伞匠",
         prof="修伞匠——过去在伞铺换伞骨、上桐油的师傅的赛博后身——"
              "让一把撑歪了的伞重新挡得住雨的人。",
         traits=[("和气", "再急的人来她也不催"), ("手细", "换一根骨不留痕"),
                 ("不将就", "伞面漏一处就整块补")],
         creed="一把伞撑得起三年，就别急着换新的",
         thought="劳动是替人把雨挡回去——先撑开看是哪根骨折了，把断口剪齐，用细钢丝接头，"
                 "钳子夹住一点点收紧；伞面破了要顺着织纹剪，补丁熨平，边上走一道密针；"
                 "最后在伞头那圈钢丝上抹一点油，撑开才顺。代价是手指关节磨出茧，眼睛看细线看得发酸。"
                 "名字是娘取的，阿翠两个字，说女孩子手稳就是福。等戴不上针了，就把那盒钢丝分给巷里愿意学的孩子。",
         language="伞铺的和气腔，末句爱加一个「啊」，讲活从伞骨讲起。",
         wardrobe="藏青布褂外罩一件碎花围裙，袖口扎着，头发在脑后盘成一个髻，胸口别一根别针挂着细钳。",
         life="十七岁跟着娘在伞铺里学换骨，铺子开在老城巷口，一开三十多年。",
         behavior="每天开门先把门口那把样品伞撑开又收上，看顺不顺。",
         behavior_hint="接伞先抖两下，让水珠落尽再看。",
         relations="老城巷里的人都认得她这门手艺；常给印章街的简伯衡送修好的伞。",
         hook=_G["hook_objects"][724],
         style_dna=sd("伞铺和气腔", "长句+尾音收", "先看伞骨，再讲话",
                      "暖（对方的急先接住）", "家常幽默（拿自己的茧手说笑）"),
         profession_visible="老城巷口伞铺（上午开门·雨天最忙）",
         gene_evidence=ev(725, 552)),
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
    if not (len(genes["hook_objects"]) == 725 and len(genes["turning_points"]) == 552):
        print("GENE-BASELINE REFUSED: ho/tp != 725/552（批二十一原料基线漂移·零写入）")
        return 4
    for idx in range(720, 725):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(547, 552):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS21
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS21]
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