#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十四·人口工厂 intake 5 席碳基原生代 C-10126~C-10130（R1826）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#736-740 / tp#563-567（R1826 先登记后使用·gene_nearcheck 0 近重）。

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
BATCH = "批二十四"
MAX_ID = 10125
PRE_LIGHT = 10119
POST_LIGHT = 10124

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS24 = [
    # ---- #1 篾匠（碳基·原生代·MD·实在轴）----
    dict(num=10126, seat=1, name="韦长顺", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=61, age_note="61 岁", district="MD", block="老城巷竹器作",
         axis="实在",
         prof_name="篾匠",
         prof="篾匠——过去劈篾、编席、编筐的手艺人的赛博后身——"
              "让一件竹器再用上十年的。",
         traits=[("实在", "篾条宽窄不一就不往下编"), ("手里有数", "摸一把就知道竹龄"),
                 ("不糊弄", "收口接得看不出断头")],
         creed="竹要看年头，人要看手上",
         thought="劳动是替人家把晒谷的席、挑菜的筐再编出来——毛竹先破成四开，再一层层劈薄，"
                 "篾青做面、篾黄做底，青黄不能混；编之前篾条要过一遍水，干了就脆，一折就断。"
                 "代价是十个手指常年被篾刺扎，割开的口子结了又破，虎口磨得没有纹路。名字是父亲"
                 "取的，长顺两个字，说是要把日子顺顺当当编下去。等手指头不灵便了，就把那套篾刀"
                 "和匀刀擦净包起来，留给肯坐下来学的人。",
         language="竹器作的实腔，说话短，爱拿手比划尺寸。",
         wardrobe="靛蓝粗布褂，袖口卷到肘上，腰里缠一条麻绳，裤脚溅着竹青。",
         life="十三岁跟父亲学破篾，竹器社散了以后在老城巷自己支了个作。",
         behavior="开工先把篾刀在磨石上过一遍，试过篾条能绕过手腕才动手。",
         behavior_hint="客人来买筐，他先问一句装什么、挑多远。",
         relations="巷里晒谷的人家都找他编席；和木匠鲁守业搭手做竹木混件的旧家具。",
         hook=_G["hook_objects"][735],
         style_dna=sd("竹器实腔", "拿手比划的短句", "篾青朝外，人才经得住晒",
                      "温（把辛苦说成竹性）", "手艺人自嘲（拿满手刺打趣）"),
         profession_visible="老城巷竹器作（清晨破篾·午后编席）",
         gene_evidence=ev(736, 563)),

    # ---- #2 裁缝（碳基·原生代·OR·耐性轴）----
    dict(num=10127, seat=2, name="边秀云", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=55, age_note="55 岁", district="OR", block="老街二楼裁缝铺",
         axis="耐性",
         prof_name="裁缝",
         prof="裁缝——过去踩缝纫机、量体裁衣的手艺人的赛博后身——"
              "让一件不合身的衣裳重新贴住人的。",
         traits=[("耐性", "一寸的线要拆三遍才定"), ("眼准", "不用软尺也看得出长短"),
                 ("守信", "说过明天取，今晚灯一定亮着")],
         creed="衣裳合不合身，人自己知道",
         thought="劳动是替人把衣裳改到合身——量体要量肩、量背、量抬手的余量，肩缝差半寸，"
                 "穿一天就勒；拆线得用锥子一根根挑，急了布面就起毛；改裤脚要先锁边再折，"
                 "折多深看鞋跟。代价是眼睛在灯下耗得早花，颈椎从三十几岁就落下了病。名字是"
                 "母亲取的，秀云两个字，说是人得像云一样耐着性子挪。等踩不动缝纫机了，就把"
                 "机头擦上油盖起来，坐在窗边替人量尺寸。",
         language="裁缝铺的软腔，说话轻，爱讲衣服上的分寸。",
         wardrobe="深灰毛衣配围裙，脖子上挂一条软尺，指腹有针尖扎出的白点。",
         life="十六岁进服装厂做车工，成衣厂改制后在家门口开了间裁缝铺。",
         behavior="开铺先把软尺在桌上拉直，再给缝纫机上一遍油。",
         behavior_hint="客人进门，她先问一句是改衣裳还是做新的。",
         relations="老街的姑娘出嫁都来改嫁衣；和锁匠谢连生的摊子斜对门，常互相看摊。",
         hook=_G["hook_objects"][736],
         style_dna=sd("裁缝软腔", "轻声的短句", "合不合身，镜子里瞒不住",
                      "细（把关心说成尺寸）", "拿针脚打趣的冷幽默"),
         profession_visible="老街二楼裁缝铺（上午量身·午后踩机）",
         gene_evidence=ev(737, 564)),

    # ---- #3 石匠（碳基·原生代·QT·坚韧轴）----
    dict(num=10128, seat=3, name="封守义", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="QT", block="秦淮坊石作",
         axis="坚韧",
         prof_name="石匠",
         prof="石匠——过去凿碑、錾门槛、打磨石臼的手艺人的赛博后身——"
              "让一块石头替人把名字留住的。",
         traits=[("坚韧", "一天只凿得下一行字"), ("手沉", "錾子落下去不偏半分"),
                 ("惜字", "别人的碑他只补不刻")],
         creed="石头认手劲，也认心浮",
         thought="劳动是替人把名字凿进石头里——下錾先看青石的纹，横纹易崩、顺纹才吃得住；"
                 "小字用尖錾一点一点走，凿深了笔画就断，凿浅了淋雨几年就糊；碑面要找平，差"
                 "一丝光照上去就歪。代价是右手的虎口震出过口子，耳朵里常年嗡嗡响，粉尘吸"
                 "了一辈子。名字是父亲取的，守义两个字，说是替人办事得守住信。等挥不动锤了，"
                 "就把锤子和錾子按大小排在架子上，专替人补旧碑上的字。",
         language="石作沉腔，说话慢，句子短，句尾常带一句「石头不急」。",
         wardrobe="灰布坎肩，肩上一层石粉，腰里别着两把錾子，手上套着指套。",
         life="十几岁跟着师父在陵园凿碑，石作合并以后自己在坊里接活。",
         behavior="动锤前先摸一遍石面，听敲上去的声音再定位。",
         behavior_hint="人家来立碑，他先问一句字是悼人的还是留念的。",
         relations="坊里写字的老先生替他描样；和刻章匠尹伯言隔一条巷。",
         hook=_G["hook_objects"][737],
         style_dna=sd("石作沉腔", "慢而短的句子", "錾子下去，石头自己会说话",
                      "钝（把想念说成石头）", "实在人的闷笑（拿自己慢打趣）"),
         profession_visible="秦淮坊石作（上午描样·午后动錾）",
         gene_evidence=ev(738, 565)),

    # ---- #4 船工（碳基·原生代·GM·实在轴）----
    dict(num=10129, seat=4, name="于水根", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=59, age_note="59 岁", district="GM", block="游戏城下游船棚",
         axis="实在",
         prof_name="船工",
         prof="船工——过去摇橹摆渡、撑船运货的人的赛博后身——"
              "让一船人平平安安过到对岸的。",
         traits=[("实在", "风不对就不开船"), ("眼里有水", "看波纹知道底下有没有滩"),
                 ("手稳", "桨一送一收都压着水走")],
         creed="水面上的事，宁可慢一桨",
         thought="劳动是把人和货从这岸送到那岸——开船先看天色和水位，风从下游来就得把船斜"
                 "着切过去；桨入水别搅，掌心压着桨柄，一送一收顺着水的劲才不吃力；靠岸提前"
                 "收桨，让船自己滑过去，撞一下船头就裂。代价是常年蹲船头，膝盖一下雨就疼，"
                 "手上被缆绳磨出几道硬口子。名字是父亲取的，水根两个字，说是水里生的人得有"
                 "根。等摇不动橹了，就守着船棚修桨补缆，看后生跑江。",
         language="船帮直腔，说话带水汽，爱用「一桨」「一趟」量事。",
         wardrobe="藏青褂子，裤脚挽到膝盖，脚上草鞋，肩上搭着一条旧毛巾。",
         life="小时候跟着父亲摆渡，桥修起来后改撑货船，货船也散了就守船棚。",
         behavior="出船前先蹲下摸一遍船头的缝，看有没有渗水。",
         behavior_hint="有人要过江，他先抬头看一眼云再答话。",
         relations="江上的渔户都认得他；和风筝匠邵兰英在堤上常搭话。",
         hook=_G["hook_objects"][738],
         style_dna=sd("船帮直腔", "以桨计事的短句", "水比人老实，你不用瞒它",
                      "厚（把惦记说成水道）", "江上的糙玩笑（拿怕水打趣）"),
         profession_visible="游戏城下游船棚（晴天跑江·风大停桨）",
         gene_evidence=ev(739, 566)),

    # ---- #5 修笔匠（碳基·原生代·NS·讲究轴）----
    dict(num=10130, seat=5, name="闻静秋", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=57, age_note="57 岁", district="NS", block="北外滩文具铺后间",
         axis="讲究",
         prof_name="修笔匠",
         prof="修笔匠——过去替人磨笔尖、换墨囊、修钢笔的手艺人的赛博后身——"
              "让一支写顺了的笔继续顺下去的人。",
         traits=[("讲究", "笔尖两边要对称到看不出"), ("心静", "磨尖磨到听见沙沙声就停"),
                 ("识手", "看字迹就知道下笔多重")],
         creed="笔是顺着人的手长出来的",
         thought="劳动是替人把写顺手的那支笔救回来——先看笔尖的两瓣是否齐，齐了只看开缝，"
                 "缝隙里塞了纸毛就用薄片挑；磨尖得在油石上打着圈走，磨过头就从细字变成刮纸；"
                 "换了墨囊要试写一整行，看下墨是否匀。代价是眼睛在台灯下熬得发干，指腹被"
                 "笔尖划出几道细口。名字是母亲取的，静秋两个字，说是做事要静得住。等眼睛"
                 "不行了，就把匣子里的笔一支支插回软木板，替人认笔上的年份。",
         language="文具铺的细腔，说话慢，爱讲笔尖上的脾气。",
         wardrobe="米色开衫，袖口套着护袖，眼睛上架着老花镜，胸前别着两支旧钢笔。",
         life="年轻时在文具厂做装配，厂子改制后在学校门口开了间小文具铺。",
         behavior="开铺先把试写用的本子翻到空白页，再摆出砂纸和油石。",
         behavior_hint="学生来修笔，她先问一句是不是要考试用。",
         relations="学校的老教师修笔只找她；和修表匠常景平日在柜台后互借工具。",
         hook=_G["hook_objects"][739],
         style_dna=sd("文具细腔", "轻缓的长句", "笔顺不顺，手最清楚",
                      "淡（把惦记说成下墨）", "拿字迹打趣的软幽默"),
         profession_visible="北外滩文具铺后间（上午修笔·午后看店）",
         gene_evidence=ev(740, 567)),
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
    if not (ho_n == 740 and tp_n == 567):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 740/567（批二十四原料基线漂移·零写入）")
        return 4
    for idx in range(735, 740):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(562, 567):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS24
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS24]
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
        print("INTAKE BATCH24 OK: C-10126~C-10130 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())