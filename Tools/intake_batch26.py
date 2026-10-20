#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十六·人口工厂 intake 5 席碳基原生代 C-10136~C-10140（R1833）

复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#746-750 / tp#573-577（R1832 先登记后使用·gene_nearcheck 0 近重）。
域：篾匠 / 补锅匠 / 剃头匠 / 修伞匠 / 糖画匠。

排程：D-20261020-02 判定 census 批限非让路窗（19:00-次日 09:00）+周末全窗；
本文件日间可写不可跑，实际入册由夜窗轮次执行（批二十三/二十四/二十五在前，按序入册）。
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
BATCH = "批二十六"
MAX_ID = 10135
PRE_LIGHT = 10139
POST_LIGHT = 10144

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS26 = [
    # ---- #1 篾匠（碳基·原生代·MD·手稳轴）----
    dict(num=10136, seat=1, name="韦竹生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=61, age_note="61 岁", district="MD", block="老城巷竹器行",
         axis="手稳",
         prof_name="篾匠",
         prof="篾匠——过去破竹、劈篾、编篮编席的手艺人的赛博后身——"
              "让一只竹篮再用上五年的。",
         traits=[("手稳", "破篾一剖到梢不断丝"), ("惜料", "边角篾条留着扎箍"),
                 ("静", "编起活来一整天不吭声")],
         creed="篾条顺了，家什才服手",
         thought="劳动是替人把一把散了的竹篮重新编住——先拿篾刀破竹，一刀下去要吃进两节，"
                 "破偏了整根就废；破开的竹片再分青篾黄篾，青篾韧做面，黄篾硬做骨；刮篾要"
                 "贴着竹皮刮到一样厚，厚一分编出来就鼓；起底先从四角压头，篾条一上一下交"
                 "替走，走到转角处要闷一闷再折，折不闷就要炸丝。代价是十根手指被篾口拉出"
                 "一层细伤，眼睛在细篾上耗得早花，天阴时手指发僵。名字是父亲取的，竹生两"
                 "个字，说是吃竹子饭的人，得像竹子一样立着。等手抖得劈不直篾了，他就只刮"
                 "篾不编，替人把旧篮的断篾补上。",
         language="竹器行的低腔，话少，爱拿竹子打比方。",
         wardrobe="灰蓝旧布衫，腰上系一条竹篾围裙，指节上缠着胶布。",
         life="十四岁跟父亲在竹器行学破竹，塑料筐挤走竹篮后改编茶席小件、补老竹椅的断篾。",
         behavior="开工先破一节青竹试篾性，听篾条弹回来的声音。",
         behavior_hint="人家提旧篮来，他先问一句是装菜还是走亲戚。",
         relations="茶席店家认他的手；和箍桶匠狄长庚都买同一家的竹料。",
         hook=_G["hook_objects"][745],
         style_dna=sd("竹器低腔", "短句夹一声停顿", "篾断一根，我就重劈一节",
                      "静（把关心说成料）", "拿自己不吭声打趣的冷幽默"),
         profession_visible="老城巷竹器行（清晨破竹·午后编篮）",
         gene_evidence=ev(746, 573)),

    # ---- #2 补锅匠（碳基·原生代·OR·惜物轴）----
    dict(num=10137, seat=2, name="翁德昌", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=64, age_note="64 岁", district="OR", block="老街河埠炉摊",
         axis="惜物",
         prof_name="补锅匠",
         prof="补锅匠——过去熔铁补锅、换锅底、打把耳的手艺人的赛博后身——"
              "让一口旧锅再熬十年的饭的。",
         traits=[("惜物", "裂一道口也舍不得让人换新锅"), ("眼毒", "一眼看出裂纹往哪儿走"),
                 ("耐热", "三伏天也守着炉子")],
         creed="锅修得住，灶就散不了",
         thought="劳动是替人把一口漏了底的铁锅重新补上——先拿小锤敲锅沿听声，声音发闷的"
                 "地方就是暗裂；裂缝两端各钻一个小孔止住，不然熔铁一浇裂纹还往前爬；坩埚"
                 "里化生铁，火要拉到发白才浇得匀，浇口时手腕不能抖，抖一下补丁就起砂眼；"
                 "浇完在砧上敲平，抹一层泥浆，注水试三遍不渗才算成。代价是常年烤火，脸上"
                 "毛孔粗，右眼被火星溅过留了个白点，夏天一站炉边就头晕。名字是师父取的，"
                 "德昌两个字，说是手里积德，日子才昌。等端不动坩埚了，他就只换把耳、上铆"
                 "钉，替人修旧铁锅的边。",
         language="炉边粗腔，声音大，爱带火气说笑。",
         wardrobe="油黑围裙罩着旧棉褂，护目镜挂在脖子上，手上套着厚布手套。",
         life="十六岁跟师父学补锅，铝锅兴起后收了炉子，改替人补铜壶、修旧铁锅的把耳。",
         behavior="开工先拿小锤绕锅沿敲一圈，把暗裂一处一处听出来。",
         behavior_hint="人家拎锅来，他先问一句是烧柴还是烧气。",
         relations="河埠做饭的人家都回来找他；和铁匠铺共用一个风箱。",
         hook=_G["hook_objects"][746],
         style_dna=sd("炉边粗腔", "大声的整句带一声笑", "火不白，补丁就虚",
                      "热（把心疼说成火候）", "拿火星溅脸打趣的粗幽默"),
         profession_visible="老街河埠炉摊（午后化铁·黄昏浇补）",
         gene_evidence=ev(747, 574)),

    # ---- #3 剃头匠（碳基·原生代·NS·和顺轴）----
    dict(num=10138, seat=3, name="祁顺发", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=59, age_note="59 岁", district="NS", block="北外滩巷口理发摊",
         axis="和顺",
         prof_name="剃头匠",
         prof="剃头匠——过去推头、刮脸、掏耳朵的手艺人的赛博后身——"
              "让一个头面清爽地过日子的。",
         traits=[("和顺", "谁坐下都能搭上话"), ("手轻", "刮脸客人睡着都不惊"),
                 ("眼准", "刀走一遍不留茬")],
         creed="刀口朝自己，客人才放心",
         thought="劳动是替人把一头乱发剪得服帖——先问清要长要短，再看脸型定分头线，线定"
                 "偏了，一整个月都别扭；推子从鬓角推起，手腕提着走，推到底要停一下再抬，"
                 "不然会啃出一道坑；刮脸得先用热毛巾敷软，鐾刀布上正反各鐾十几下，刀口朝"
                 "自己斜着贴皮走，逆着胡茬才刮得净，力道过一分就见血。代价是站一天腿肿，"
                 "手指关节被推子震得发木，冬天手上裂口。名字是母亲取的，顺发两个字，说是"
                 "做人顺顺当当。等手抖得拿不稳刀了，他就只推头，替人修鬓角。",
         language="摊头闲腔，说话热络，爱问家常。",
         wardrobe="白布围裙，袖口用布带扎紧，兜里插着两把推子。",
         life="十七岁跟巷口的老剃头师傅学了三年，师傅去世后接了那张木凳和那面镜子。",
         behavior="开工先把鐾刀布挂好，再把手在热水里泡一遍。",
         behavior_hint="客人坐下，他先问一句要不要连脸一块儿刮。",
         relations="巷里的老人都认他这把刀；和修鞋匠隔着三个摊位，常替对方捎话。",
         hook=_G["hook_objects"][747],
         style_dna=sd("摊头闲腔", "热络的对话句", "头面清爽，人就抬得起头",
                      "和（把关心说成家常）", "拿客人打瞌睡打趣的软幽默"),
         profession_visible="北外滩巷口理发摊（上午推头·午后刮脸）",
         gene_evidence=ev(748, 575)),

    # ---- #4 修伞匠（碳基·原生代·GM·细密轴）----
    dict(num=10139, seat=4, name="孟广和", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=62, age_note="62 岁", district="GM", block="游戏城修伞摊",
         axis="细密",
         prof_name="修伞匠",
         prof="修伞匠——过去换伞骨、绷伞面、熬桐油的手艺人的赛博后身——"
              "让一把旧伞再撑一季雨的。",
         traits=[("细密", "一根竹骨削到分毫不歪"), ("识骨", "竹骨铁骨折了都能配"),
                 ("慢", "宁可多留一天也不糊弄")],
         creed="伞撑不撑得住，看骨头正不正",
         thought="劳动是替人把一把散了架的伞重新撑起来——先拆伞面，把伞骨一根根摊平看，"
                 "断在中段的削接一段竹骨，接头要开槽咬住再用铜丝缠，缠三圈才不吃力；铁骨"
                 "折了要退火再弯，冷弯必裂；伞面破洞剪一块同色的布，翻边缝压两道线，缝密"
                 "了才不漏；最后绷面要沿八根骨对齐，绷歪了收伞就夹。代价是桐油味熏了一辈"
                 "子，肺上落了毛病，冬天手上裂口，指甲缝里全是油。名字是父亲取的，广和两"
                 "个字，说是广结善缘、和气过日子。等手抖得缠不了铜丝了，他就只验骨不修面，"
                 "替人看伞还能不能救。",
         language="摊头细腔，说话慢，爱拆开给人看内部。",
         wardrobe="深蓝布褂，膝上铺一块油布，脚边一只装铜丝的旧铁盒。",
         life="十五岁跟舅舅学修伞，新伞便宜到坏一把扔一把后，改替汉服店复原老式油纸伞。",
         behavior="开工先把手里的伞倒过来抖三下，看伞骨有没有松。",
         behavior_hint="人家递伞来，他先问一句是天天撑还是留着过节用。",
         relations="汉服店和旧货摊主都来找他；和篾匠韦竹生同买一家的竹料。",
         hook=_G["hook_objects"][748],
         style_dna=sd("摊头细腔", "慢条斯理的分层句", "骨正了，面才绷得平",
                      "细（把耐心说成骨头）", "拿自己的慢打趣的自嘲"),
         profession_visible="游戏城修伞摊（上午拆伞·午后绷面）",
         gene_evidence=ev(749, 576)),

    # ---- #5 糖画匠（碳基·原生代·QT·灵巧轴）----
    dict(num=10140, seat=5, name="苗巧云", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=47, age_note="47 岁", district="QT", block="秦淮坊糖画摊",
         axis="灵巧",
         prof_name="糖画匠",
         prof="糖画匠——过去熬糖、走勺、画龙画凤的手艺人的赛博后身——"
              "让一个孩子攥着一只甜蝴蝶回家的。",
         traits=[("灵巧", "不用稿，勺一落就是形"), ("记性好", "看过的图样默得出来"),
                 ("会哄小孩", "哭着的孩子也能逗笑")],
         creed="糖凉得快，手要跟得上",
         thought="劳动是替人把一勺糖浇成看得见的欢喜——先熬糖，白糖加水小火熬到琥珀色，"
                 "熬过一分就发苦，欠一分就粘牙；青石板上抹一层薄油，糖才不粘；走勺要贴着"
                 "板面画，勺离得高就断线，走慢一点糖就凝在勺口；龙身要一气走完，中间停了"
                 "再接就有疙瘩；最后趁热压上竹签，等凉透了才起片，起早了断，起晚了碎。代"
                 "价是手腕上烫出一层旧疤，夏天守在炉边一站半天，眼前发花。名字是母亲取"
                 "的，巧云两个字，说是手巧，日子才过得像云一样轻。等手慢了画不成龙了，她"
                 "就只画蝴蝶和小兔，替孩子挑图案。",
         language="摊头亮腔，话说得脆，爱跟孩子一起数数。",
         wardrobe="杏色围裙罩着碎花衬衫，袖子挽到手肘，腕上缠着防烫布。",
         life="十九岁跟着街口的老师傅学熬糖，老师傅走不动以后接了那口铁皮炉。",
         behavior="开摊先把青石板抹上油，再把铜勺在糖罐里温一遍。",
         behavior_hint="孩子踮脚看，她先问一句要龙还是要蝴蝶。",
         relations="坊口卖糖葫芦的常替她看着摊位；和弹棉花匠茅德生的女儿同姓苗，两家常来往。",
         hook=_G["hook_objects"][749],
         style_dna=sd("摊头亮腔", "脆生生的短句带笑", "糖化在嘴里，才叫甜",
                      "欢（把好意说成甜）", "跟小孩逗趣的顽皮幽默"),
         profession_visible="秦淮坊糖画摊（午后熬糖·黄昏走勺）",
         gene_evidence=ev(750, 577)),
]


def main():
    # D-20261020-02 排程闸：census 批限非让路窗（19:00-次日 09:00）+周末全窗（BigLife 侧自管）。
    import evolve_citizen
    if evolve_citizen.yield_window_active() and "--force" not in sys.argv:
        print("YIELD-WINDOW: intake 排程闸拒绝（工作日 09:00-19:00 让路窗·零写入·夜窗自领）")
        return 5
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
    if not (ho_n == 750 and tp_n == 577):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 750/577（批二十六原料基线漂移·零写入）")
        return 4
    for idx in range(745, 750):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(572, 577):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS26
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS26]
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
        print("INTAKE BATCH26 OK: C-10136~C-10140 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())