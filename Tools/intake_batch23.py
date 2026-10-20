#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十三·人口工厂 intake 5 席碳基原生代 C-10121~C-10125（R1818）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#731-735 / tp#558-562（R1818 先登记后使用·gene_nearcheck 0 近重）。

排程：D-20261020-02 判定 census 批限非让路窗（19:00-次日 09:00）+周末全窗；
本文件日间可写不可跑，实际入册由夜窗轮次执行。
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
BATCH = "批二十三"
MAX_ID = 10120
PRE_LIGHT = 10114
POST_LIGHT = 10119

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS23 = [
    # ---- #1 木匠（碳基·原生代·MD·实在轴）----
    dict(num=10121, seat=1, name="鲁守业", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=64, age_note="64 岁", district="MD", block="老城巷木工间",
         axis="实在",
         prof_name="木匠",
         prof="木匠——过去拎着刨子走街串巷打家具的手艺人的赛博后身——"
              "让一扇关不严的窗重新合上、一张晃的桌子重新站住的人。",
         traits=[("实在", "量过的尺寸才肯下锯"), ("手稳", "一刨推过去深浅一个样"),
                 ("惜木", "边角料也码起来留着补小件")],
         creed="木头有脾气，顺着它的纹走才不吃亏",
         thought="劳动是替人把家里的木头家什再撑些年——量尺寸得从两头各量一遍，差一分就合不拢；"
                 "刨料要看纹路，逆向推会起毛，得把刨刀翻过来顺一遍；上榫不用钉子，靠的是严缝和"
                 "木楔。代价是常年弯腰，腰上落了病，耳朵里一直有刨床的嗡声。名字是父亲取的，守业"
                 "两个字，说是手艺在手日子就散不了。等拉不动大锯了，就把那套刨子按大小排进木箱，"
                 "留给肯学的后生。",
         language="木工短腔，说话先报尺寸，一句顶一句。",
         wardrobe="靛蓝工装褂，肩头磨得发亮，腰间一条皮尺，口袋里插着半截铅笔。",
         life="十六岁跟师兄学木工，家具厂散了以后在老城巷支起木工间。",
         behavior="开工前先把刨刀磨一遍，试过刨花卷得匀才动料。",
         behavior_hint="接过活先摸一遍旧家具的榫头，再谈修还是换。",
         relations="巷里人家的门窗坏了都来找他；和裱糊匠常搭手修老屋的顶棚。",
         hook=_G["hook_objects"][730],
         style_dna=sd("木工短腔", "先量后断的短句", "尺寸不对，说什么都白搭",
                      "温（把难处说成木纹）", "木屑味自嘲（拿自己弯腰打趣）"),
         profession_visible="老城巷木工间（天亮开工·午后收刨）",
         gene_evidence=ev(731, 558)),

    # ---- #2 锁匠（碳基·原生代·OR·实在轴）----
    dict(num=10122, seat=2, name="谢连生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=58, age_note="58 岁", district="OR", block="老街口锁摊",
         axis="实在",
         prof_name="锁匠",
         prof="锁匠——过去蹲在街边配钥匙、撬锁救急的手艺人的赛博后身——"
              "让人进得了自己家门的人。",
         traits=[("手稳", "配齿差半丝就开不了"), ("嘴严", "开过谁家的门从不往外说"),
                 ("实在", "能修的不劝人换新的")],
         creed="锁挡的是手脚，不挡人心",
         thought="劳动是替人把进不去的门打开——配钥匙先看齿高，锉的时候一下一下试，宁可少锉"
                 "半丝再补；撬锁不能硬来，得听锁芯里弹子的动静，一点点找那口气。代价是眼睛在"
                 "小灯下熬得早花，蹲久了膝盖受不住，冬天手僵得捏不住锉。名字是母亲取的，连生"
                 "两个字，说是人得连着人活着。等手不听使唤了，就把那串旧锁板挂在摊上，教人认"
                 "锁的年份。",
         language="锁摊直腔，问一句答一句，不绕弯。",
         wardrobe="灰夹克，袖口磨出白边，腰上挂一串钥匙，指头上有锉刀磨出的薄茧。",
         life="年轻时在五金厂做钳工，厂子散了就在老街口摆了个配钥匙的摊子。",
         behavior="出摊先把锉刀和试片摆齐，再挂上那块写着配钥匙的木牌。",
         behavior_hint="人家来开门，先问一句是不是自己家，再动手。",
         relations="老街的房东都存他的号；和剃头匠、铜匠凑一桌下棋。",
         hook=_G["hook_objects"][731],
         style_dna=sd("锁摊直腔", "一问一答的直句", "锁认齿，人认脸",
                      "直（把麻烦说成顺手）", "街坊抬杠（拿忘带钥匙打趣）"),
         profession_visible="老街口锁摊（上午配钥匙·下午上门开锁）",
         gene_evidence=ev(732, 559)),

    # ---- #3 刻章匠（碳基·原生代·QT·讲究轴）----
    dict(num=10123, seat=3, name="尹伯言", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=67, age_note="67 岁", district="QT", block="秦淮坊刻字铺",
         axis="讲究",
         prof_name="刻章匠",
         prof="刻章匠——过去替人刻名章、刻铺号的手艺人的赛博后身——"
              "把一个人的名字端端正正按在纸上的。",
         traits=[("讲究", "一笔写歪了就重写"), ("心静", "刻到最后一刀手不抖"),
                 ("认字", "偏旁差一点也看得出")],
         creed="字要立得住，人才站得稳",
         thought="劳动是替人把名字刻得端端正正——印坯先拿砂纸磨平，写反字要一笔一笔照镜子；"
                 "下刀分阴阳，刀口斜一分印出来就糊，收刀得慢慢提，不然崩了角整方料就废了。"
                 "代价是低头久了脖子僵，眼睛在放大镜下熬坏了一半。名字是祖父取的，伯言两个"
                 "字，说是人开口要有个分寸。等刻不动了，就把那盒刻刀交给铺子里的学徒，自己坐"
                 "在门口替人认老印章上的字。",
         language="刻字慢腔，说话咬字清楚，爱讲字的来历。",
         wardrobe="藏青对襟褂子，袖口套着套袖，眼镜架在鼻梁上，指腹有薄薄的刀痕。",
         life="小时候在私塾描红，后来在刻字铺当学徒，一坐就是五十年。",
         behavior="开铺先磨一方印坯，试过手感才接活。",
         behavior_hint="客人报名字，他先问一句是刻名章还是刻闲章。",
         relations="书画铺的先生常来刻压角章；和藤编匠的摊子隔一条巷，晚饭后常一起走一段。",
         hook=_G["hook_objects"][732],
         style_dna=sd("刻字慢腔", "咬字清楚的缓句", "字是刻给自己看的",
                      "静（把喜欢说成习惯）", "咬文嚼字的冷幽默（拿错别字打趣）"),
         profession_visible="秦淮坊刻字铺（上午写字·午后动刀）",
         gene_evidence=ev(733, 560)),

    # ---- #4 风筝匠（碳基·原生代·GM·耐性轴）----
    dict(num=10124, seat=4, name="邵兰英", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=60, age_note="60 岁", district="GM", block="游戏城江堤风筝摊",
         axis="耐性",
         prof_name="风筝匠",
         prof="风筝匠——过去扎沙燕、糊绢面、在江堤上卖风筝的手艺人的赛博后身——"
              "把一根线放到天上的人。",
         traits=[("耐性", "竹条要阴干三天才削"), ("手巧", "两翼对称到看不出偏"),
                 ("会看天", "抬头就知道今天能不能放")],
         creed="线在手里，风就听你的",
         thought="劳动是替孩子把春天放到天上去——竹条先削成一粗一细，泡过水才不会脆；糊绢面"
                 "松紧要匀，松了兜不住风，紧了飞上去就栽；尾巴的长短是试出来的，风大就短一截。"
                 "代价是手指常年被竹刺扎，眼睛迎风久了一直流泪。名字是母亲取的，兰英两个字，"
                 "说是人得像草一样长在风里。等扎不动了，就把那套削刀和线拐留给外孙女，每年春"
                 "天照旧到堤上坐坐。",
         language="江堤爽腔，说话带笑，先讲风，再讲线。",
         wardrobe="碎花布衫，外面套一件旧马甲，手腕上缠着线拐的皮绳。",
         life="小时候跟着父亲在江堤上放风筝，嫁人后在堤边支了个风筝摊。",
         behavior="出门前先看江面有没有风纹，风稳了才摆摊。",
         behavior_hint="孩子来挑风筝，她先问一句会不会自己收线。",
         relations="堤上玩风筝的老人都认得她；和晒太阳的茶摊老板互相留着板凳。",
         hook=_G["hook_objects"][733],
         style_dna=sd("江堤爽腔", "带笑的短句", "风好，线就直",
                      "亮（把想念说成风）", "孩子气的打趣（把风筝说成会认人的东西）"),
         profession_visible="游戏城江堤风筝摊（晴日午后出摊·风大收线）",
         gene_evidence=ev(734, 561)),

    # ---- #5 修表匠（碳基·原生代·NS·讲究轴）----
    dict(num=10125, seat=5, name="常景明", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=63, age_note="63 岁", district="NS", block="北外滩钟表铺",
         axis="讲究",
         prof_name="修表匠",
         prof="修表匠——过去守着玻璃柜台、拿镊子拨游丝的手艺人的赛博后身——"
              "让一只停了的表重新走起来的人。",
         traits=[("讲究", "拆下的零件按次序摆一排"), ("手轻", "游丝碰弯一点就废"),
                 ("守信", "说三天取的表，第三天准摆在柜上")],
         creed="表不怕旧，怕的是没人管它",
         thought="劳动是替人把走慢的日子拨回来——后盖撬开要先放掉发条的劲，机芯夹出来放在白"
                 "纸上；游丝用镊子一根根理顺，手指抖一下就得重来；上油只点针尖大小一点，多了"
                 "反倒粘住。代价是眼睛二十年前就配了放大镜，脖子也总歪着。名字是父亲取的，景"
                 "明两个字，说是人要看得清时候。等手拿不稳镊子了，就把柜台里的表一只只上弦，"
                 "让它们一起走给他听。",
         language="表铺细腔，说话轻声，爱报时点和走时快慢。",
         wardrobe="白衬衫外罩灰布围裙，胸前口袋里插着一把小螺丝刀，眼睛上扣着单眼目镜。",
         life="十八岁在钟表店当学徒，国营钟表店改制后自己开了间小铺子。",
         behavior="开门先把柜里的表逐只上弦，听一遍走时。",
         behavior_hint="客人递表来，他先问一句是走得慢还是停了。",
         relations="弄堂里的老人修表只认他；和修锁的谢连生常一起在街口吃早点。",
         hook=_G["hook_objects"][734],
         style_dna=sd("表铺细腔", "压低声音的长句", "快慢都在针上",
                      "细（把惦记说成走时）", "拿表打趣的冷笑话（把过时的人比作停摆）"),
         profession_visible="北外滩钟表铺（上午上弦·午后接修）",
         gene_evidence=ev(735, 562)),
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
    if not (ho_n == 735 and tp_n == 562):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 735/562（批二十三原料基线漂移·零写入）")
        return 4
    for idx in range(730, 735):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(557, 562):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS23
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS23]
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
        print("INTAKE BATCH23 OK: C-10121~C-10125 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())