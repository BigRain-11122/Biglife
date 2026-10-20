#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十二·人口工厂 intake 5 席碳基原生代 C-10116~C-10120（R1817）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#726-730 / tp#553-557（R1817 先登记后使用·gene_nearcheck 0 近重）。
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
BATCH = "批二十二"
MAX_ID = 10115
PRE_LIGHT = 10109
POST_LIGHT = 10114

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS22 = [
    # ---- #1 铜匠（碳基·原生代·NS·实在轴）----
    dict(num=10116, seat=1, name="邹德水", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="NS", block="北外滩老街铜器铺",
         axis="实在",
         prof_name="铜匠",
         prof="铜匠——过去守着炉子敲打铜壶铜盆的手艺人的赛博后身——"
              "让一件瘪了的铜器重新立得住、盛得住的人。",
         traits=[("实在", "敲打的活先给人看底子"), ("手稳", "一锤下去不偏半寸"),
                 ("守规矩", "该回炉的绝不当新的卖")],
         creed="铜是活的，敲对了它自己会应声",
         thought="劳动是替人把家里的旧铜器再敲十年——铜壶瘪了先退火，软了再拿木槌一点点顶回来，"
                 "焊缝要用硼砂兑水，火候不到接口就发黑；代价是耳朵被锤声磨得背，右手虎口起了一层"
                 "硬茧。名字是父亲取的，德水两个字，说是做人得像水一样把德行放低。等敲不动了，就把"
                 "那套錾子按大小排进木盒，留给愿意学的人。",
         language="打铜的短腔，说话像落锤，一句一顿。",
         wardrobe="靛蓝围裙，袖口卷到肘上，腰间挂着皮手套，耳后别一小截粉笔。",
         life="十六岁进城跟师傅学打铜，国营五金厂关停后在老街支了个炉子。",
         behavior="每天先升炉看火色，火不匀就重搭一次炭。",
         behavior_hint="接过旧铜器先掂一掂分量，再问人家想留着做什么用。",
         relations="隔壁箍桶的、修锁的都把铜活推给他；街坊嫁女儿打铜盆，都来他这儿排队。",
         hook=_G["hook_objects"][725],
         style_dna=sd("炉边短腔", "落锤式短句", "先看火色，再谈活",
                      "温（把难处说成火候）", "粗声的玩笑（拿自己背耳朵打趣）"),
         profession_visible="北外滩老街铜器铺（日出升炉·午后收锤）",
         gene_evidence=ev(726, 553)),

    # ---- #2 藤编匠（碳基·原生代·QT·耐性轴）----
    dict(num=10117, seat=2, name="何秀云", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=57, age_note="57 岁", district="QT", block="秦淮坊藤器巷口",
         axis="耐性",
         prof_name="藤编匠",
         prof="藤编匠——过去蹲在巷口编藤椅藤篮的女匠人的赛博后身——"
              "把一根根藤条盘成能坐能拎的物件的人。",
         traits=[("耐性", "一根藤能泡三天等它软"), ("手细", "编出的花纹两面一样齐"),
                 ("惜料", "断了的藤头也留着编篮底")],
         creed="藤条认手，你急它就断",
         thought="劳动是替人家把坐的地方编出来——藤条先得泡软，太软了编不紧，太硬了一弯就裂，"
                 "手上的劲要匀着给；编到转角处得停一停，让藤自己记住这个弯。代价是十个指头常年带"
                 "口子，右手无名指弯不直。名字是母亲取的，秀云两个字，说是手要巧心要软。等眼睛不"
                 "济了，就把巷口那架旧藤椅搬进屋，教邻居家的姑娘学起头。",
         language="江南软腔，话里爱带慢慢来，说活先说来料。",
         wardrobe="月白斜襟布衫，外面套一件旧毛线背心，手腕上缠着布条防磨。",
         life="小时候跟外婆编鸡笼，后来在藤器巷接活，一编就是四十年。",
         behavior="开摊前先把藤条按粗细分成三堆。",
         behavior_hint="客人挑样子，她先问是坐着用还是拎着用。",
         relations="巷口卖菜的和修伞的都爱把零活交给她；隔壁裱糊匠的窗纸破了，她顺手帮着糊。",
         hook=_G["hook_objects"][729],
         style_dna=sd("江南软语", "慢句叠句", "指头比嘴会说话",
                      "温（把等说成养）", "家常幽默（拿藤条说人）"),
         profession_visible="秦淮坊藤器巷口藤器摊（日头出来开摊·落雨收工）",
         gene_evidence=ev(727, 554)),

    # ---- #3 裱糊匠（碳基·原生代·MD·讲究轴）----
    dict(num=10118, seat=3, name="郝长顺", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=61, age_note="61 岁", district="MD", block="老城巷纸活铺",
         axis="讲究",
         prof_name="裱糊匠",
         prof="裱糊匠——过去给人糊窗糊顶棚、裱画心的师傅的赛博后身——"
              "让一张纸平平整整贴在它该在的地方的人。",
         traits=[("讲究", "一张纸对得上花纹才肯糊"), ("手轻", "糨糊刷过去不留一道褶"),
                 ("守信", "说三天交的活，两天半就送到")],
         creed="纸糊得住窗，糊不住心虚",
         thought="劳动是替人把屋里的风挡住——纸要裁得比窗框大出一指，糨糊刷匀了先晾到半干，"
                 "贴上去从中间往四边推，褶子赶出去才服帖；顶棚最难，仰着脸举着笤帚，一层一层"
                 "压实，落下来的糨糊点子在脸上干了才知道。代价是腰常年直不起来，冬天指节疼。"
                 "名字是爷爷取的，长顺两个字，说是日子别求快，求顺。等举不动笤帚了，就把裁纸的"
                 "规矩写成一张纸，贴在门后给学徒看。",
         language="纸活腔，说话轻，讲活先讲纸的厚薄。",
         wardrobe="灰布罩衣，袖口套着蓝布袖套，手指上常沾一点干糨糊。",
         life="年轻时在裱画铺当学徒，后来专做糊窗、糊顶棚的活。",
         behavior="出门前先看天，风大就不裁纸。",
         behavior_hint="量窗先量两遍，第二遍从另一头量。",
         relations="老城巷的街坊办喜事都请他糊喜字窗；和藤编匠的摊子挨着，互相搭手。",
         hook=_G["hook_objects"][726],
         style_dna=sd("纸活软腔", "先量后说的长句", "纸分三层，活分三步",
                      "温（把急躁说成风）", "自嘲（说自己糊了一辈子还没糊明白）"),
         profession_visible="老城巷纸活铺（上午接活·下午上门糊）",
         gene_evidence=ev(728, 555)),

    # ---- #4 剃头匠（碳基·原生代·OR·和气轴）----
    dict(num=10119, seat=4, name="秦广林", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=70, age_note="70 岁", district="OR", block="老街口剃头棚",
         axis="和气",
         prof_name="剃头匠",
         prof="剃头匠——过去在老街口支棚子、一把剃刀走天下的师傅的赛博后身——"
              "让人坐下来时皱着眉、站起来时舒口气的人。",
         traits=[("和气", "再难缠的客人也笑着送出门"), ("手稳", "剃刀贴着皮走不破口"),
                 ("记性好", "谁的头型谁的习惯都记得")],
         creed="剃头是给人顺气，不是给头发过不去",
         thought="劳动是替人把一天的疲惫剃下去——椅子放平，热毛巾敷上脸，刀先在皮子上试一下"
                 "温度，顺着发根走，逆着就疼；耳后那一道最难，得用指头把皮绷住。代价是站一天"
                 "腿肿，眼睛被碎头发扎得常流泪。名字是母亲取的，广林两个字，说是人得站得开、"
                 "扎得住根。等手抖了，就把那把剃刀磨好收进木盒，棚子留给徒弟。",
         language="市井热络腔，话密，爱拿天气起头。",
         wardrobe="白布褂子，肩上搭一条洗得发白的毛巾，围裙口袋里插着两把推子。",
         life="十四岁在剃头棚当学徒，公私合营后一直在老街口支棚子。",
         behavior="一早先把剃刀在磨刀石上走几遍，试过手感才开张。",
         behavior_hint="客人坐下先问一句最近睡得怎么样。",
         relations="老街的老人只认他这一把刀；和铜匠是几十年的棋友。",
         hook=_G["hook_objects"][728],
         style_dna=sd("市井热络腔", "问答式短句", "手上有准，嘴上有数",
                      "热（把闲话说成关心）", "街坊段子（拿老主顾的白头发打趣）"),
         profession_visible="老街口剃头棚（天亮开棚·天黑收刀）",
         gene_evidence=ev(729, 556)),

    # ---- #5 糊纸灯笼匠（碳基·原生代·GM·讲究轴）----
    dict(num=10120, seat=5, name="温素秋", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=62, age_note="62 岁", district="GM", block="游戏城后巷纸灯铺",
         axis="讲究",
         prof_name="糊纸灯笼匠",
         prof="糊纸灯笼匠——过去给街坊扎灯、正月里挂满一条巷子的手艺人的赛博后身——"
              "让一盏纸灯在风里稳稳亮着的人。",
         traits=[("讲究", "一盏灯的骨要正，歪一点就重扎"), ("心细", "糊纸从中间往四边推"),
                 ("不怕慢", "一天只出三盏")],
         creed="灯要亮得稳，不能亮得急",
         thought="劳动是替人把夜里的路照出来——篾条先削得一样薄，扎骨时对称着收口，歪一毫"
                 "灯就斜；糊纸要从中间往四边推，糨糊刷薄了不牢，厚了透光不匀。代价是长年低头，"
                 "脖子僵，糨糊把手上的皮绷得发亮。名字是外婆取的，素秋两个字，说是人得像秋天"
                 "一样干净。等扎不动了，就把那套篾刀留给孩子，铺子里的灯照旧亮着。",
         language="纸灯腔，说话慢，爱讲灯亮起来的样子。",
         wardrobe="藏青布褂，手指上套着顶针，围裙口袋里装着糨糊刷。",
         life="娘家做纸扎，嫁过来后在游戏城后巷开了间纸灯铺。",
         behavior="每天先检查篾条干透没有，潮了就搁到炉边烘一烘。",
         behavior_hint="客人订灯，她先问灯笼挂在哪、朝哪边。",
         relations="巷子里的孩子正月都来讨一盏小灯；和改衣摊的潘月娥常互相照看摊子。",
         hook=_G["hook_objects"][727],
         style_dna=sd("灯铺慢腔", "叠句缓收", "先看骨，再看纸",
                      "静（把高兴说成灯亮）", "孩子气的比喻（把灯比作会喘气的东西）"),
         profession_visible="游戏城后巷纸灯铺（上午扎骨·傍晚糊纸）",
         gene_evidence=ev(730, 557)),
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
    ho_n, tp_n = len(genes["hook_objects"]), len(genes["turning_points"])
    if not (ho_n == 730 and tp_n == 557):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 730/557（批二十二原料基线漂移·零写入）")
        return 4
    for idx in range(725, 730):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(552, 557):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS22
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS22]
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
    if rc == 0:
        print("INTAKE BATCH22 OK: C-10116~C-10120 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())