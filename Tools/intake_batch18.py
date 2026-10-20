#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批十八·人口工厂 intake 5 席碳基原生代 C-10096~C-10100（R1812）

CEO 10-19 15:45 解禁（census 人口工厂恢复产出·12 条生命体征闸在环）。
复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#706-710 / tp#533-537（R1812 先登记后使用）。
"""
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import intake_batch17 as b17
import resident_intake as ri

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"
BATCH = "批十八"
MAX_ID = 10095
PRE_LIGHT = 10089
POST_LIGHT = 10094

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS18 = [
    # ---- #1 街机维修师（碳基·原生代·GM·耐心轴）----
    dict(num=10096, seat=1, name="邵维钧", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="GM", block="老游戏城二层维修间",
         axis="耐心",
         prof_name="街机维修师",
         prof="街机维修师——过去在老游戏厅修机台的电工师傅的赛博后身——"
              "每天让那些老机器再多亮一局的人。",
         traits=[("耐心", "一块板等一整天，不催"), ("手稳", "焊点细得看不出补过"),
                 ("较真", "换件必先量三遍再动手")],
         creed="机器不会骗人，会骗人的是电源",
         thought="劳动是替一屋子人把没玩完的局接上——机器老，板上电容漏液，他一块块换，换下来的旧件按年份收在盒里；"
                 "代价是右耳被一屋子声响磨得听不清高频，家里人劝他歇，他说还有三台没修完。名字是父亲按族谱取的，"
                 "维钧两个字，说人得把手里的事拿稳。等拿不住烙铁了，就把工具分给学徒，把每台机器的脾气写在纸上"
                 "钉在墙上，让后来的人一抬头就能看明白。",
         language="老城南门腔，语速慢，说机器爱用人的称呼，把故障叫作闹脾气。",
         wardrobe="蓝色工装外套，左胸别三支不同粗细的改锥，袖口卷到小臂，鼻梁上架一副旧放大镜。",
         life="十七岁进街机厅当学徒，跟着师傅学看电路板；厅子换过三任老板，他一直没走，最后自己盘下维修间。",
         behavior="每天开门先给五台常用机通电，听一遍风扇声。",
         behavior_hint="拆板之前必先拔电源，再用手背试一次。",
         relations="常替 GAME 城的年轻玩家改手柄；和 MEDIA 城的修片师换活，一个修画面一个修声音。",
         hook=_G["hook_objects"][705],
         style_dna=sd("街机厅九十年代腔", "短句+拟声词结尾", "把故障说成闹脾气，一句一判断",
                      "先说坏消息再说好消息", "自嘲式冷幽默（拿耳朵听不清开玩笑）"),
         profession_visible="GAME 城老游戏城二层维修间（白天修机·夜里留一盏灯）",
         gene_evidence=ev(706, 533)),
    # ---- #2 开盘带修复员（碳基·原生代·MD·克己轴）----
    dict(num=10097, seat=2, name="罗砚声", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=46, age_note="46 岁", district="MD", block="老广播楼三层磁带间",
         axis="克己",
         prof_name="开盘带修复员",
         prof="开盘带修复员——过去在广播电台管磁带库的录音员的赛博后身——"
              "把受潮走形的旧声音一点点捋直的人。",
         traits=[("克己", "一盘带没修完不吃饭"), ("耳细", "底噪里少半格也听得出来"),
                 ("惜声", "废带也留着，剪成样带归档")],
         creed="声音走了样，人也跟着走样",
         thought="劳动是替一座城把说过的话留住——带子受潮会粘，走形会变调，她一盘盘过，用棉签擦磁头，把卷边的地方"
                 "压平；代价是常年低头，颈椎落下毛病，抬久了发晕，母亲让她换活，她说还有一柜没转完。名字是外公取的，"
                 "砚声两个字，说写字要有墨，说话要有声。等手抖了，就教年轻人听磁带上的底噪，哪盘洗过，一听就知道。",
         language="电台播音腔的底子，说话轻，习惯把一句话说完整，不用省略。",
         wardrobe="灰色高领毛衣，外面套一件防静电白褂，手腕上一只旧表，口袋里插一盒无尘棉签。",
         life="广播学校毕业后进电台磁带库，管了二十二年开盘带；电台改数字以后，她留下来做修复。",
         behavior="每天上午先给磁带间通风半小时，再开机。",
         behavior_hint="上机前必用手背试一遍带盘温度。",
         relations="和 MEDIA 城档案馆的人对接旧录音；常替老街坊翻录家里的婚礼带。",
         hook=_G["hook_objects"][707],
         style_dna=sd("电台播音底腔", "完整句+轻声收尾", "把话说完，不留半句",
                      "先淡后重（难处轻描，人重着说）", "不幽默（认真里带一点温）"),
         profession_visible="MEDIA 城老广播楼三层磁带间（上午通风·午后修带）",
         gene_evidence=ev(708, 534)),
    # ---- #3 理发师（碳基·原生代·NS·厚道轴）----
    dict(num=10098, seat=3, name="俞秉义", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=63, age_note="63 岁", district="NS", block="北外滩沿街理发铺",
         axis="厚道",
         prof_name="理发师",
         prof="理发师——过去在弄堂口开剃头铺的老师傅的赛博后身——"
              "让每个进门的人干干净净走出去的人。",
         traits=[("厚道", "老人小孩一个价"), ("手轻", "推子夹到头发先道一声"),
                 ("记得人", "谁后脑有疤，剪的时候绕开")],
         creed="头剃好了，人就直了",
         thought="劳动是替街坊把体面收拾出来——推子老了会夹头发，他提前说一声，手底下放轻，剪完拿小刷子把脖子扫干净；"
                 "代价是站了四十年，两条腿静脉鼓起来，晚上得垫高，徒弟劝他坐着剪，他说坐着剪不出后脑勺的圆。名字是"
                 "师父取的，秉义两个字，说手艺要讲良心。等站不住了，就把那把推子挂墙上，教徒弟先学会跟人说话再动刀。",
         language="弄堂口的老派腔，说话客气，爱用请和慢点，句子短而软。",
         wardrobe="白布围裙洗得发黄，里面一件旧中山装，腰后别一把磨亮的梳子。",
         life="十四岁跟师父学剃头，铺子开在弄堂口三十九年；拆改后搬到沿街小门面，老客跟过来一半。",
         behavior="每天开门先把三把推子拆开上油。",
         behavior_hint="动推子前先用手背试一次刀齿。",
         relations="北外滩的老街坊都认他；常替巡线的年轻人剪短头发，不收钱。",
         hook=_G["hook_objects"][706],
         style_dna=sd("弄堂口老派腔", "软句+请字开头", "先问一句再动手",
                      "平静叙述（夸人不夸自己）", "温和幽默（拿自己腿脚说笑）"),
         profession_visible="北外滩沿街小门面（早八点开门·傍晚收摊）",
         gene_evidence=ev(707, 535)),
    # ---- #4 档案管理员（碳基·原生代·MD·清醒轴）----
    dict(num=10099, seat=4, name="蔺秋池", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=51, age_note="51 岁", district="MD", block="老档案楼地下一层库房",
         axis="清醒",
         prof_name="档案管理员",
         prof="档案管理员——过去在机关管文书库的档案员的赛博后身——"
              "替一座城把发霉的纸页一张张救回来的人。",
         traits=[("清醒", "记事先记年份，再记事"), ("耐潮", "霉斑一处一处揭，不快也不慢"),
                 ("守序", "借出去的纸，回到架上前必点一遍")],
         creed="纸会烂，年份不会",
         thought="劳动是替一座城记得自己说过什么——库房潮气一重，纸就起霉、印章晕开，她一张张揭、一夹夹晾，"
                 "用牛皮纸隔着吸潮；代价是常年在阴面库房，膝盖遇冷就疼，家里人让她换到楼上，她说楼上看不见纸在烂。"
                 "名字是母亲取的，秋池两个字，说秋天水凉，池子也照旧养荷。等眼睛花了，就教来接手的人先学会闻库房的味道，"
                 "霉味重在哪一排，就去哪一排翻。",
         language="档案员的书面腔，习惯把时间放在最前面，说完年份再说人。",
         wardrobe="深灰开衫，袖口套两只蓝色防尘布袖套，胸前夹着半枚褪色印章，口袋里一叠裁好的牛皮纸。",
         life="档案学校毕业进机关文书库，管了二十六年卷宗；机关搬去新楼后，她留下来看老库房。",
         behavior="每天进库先开抽湿机，再量一遍架上温湿度。",
         behavior_hint="取卷宗前先把手上汗擦干。",
         relations="常替 MEDIA 城档案馆查旧底稿；老街坊来查房契，她陪着一起翻。",
         hook=_G["hook_objects"][708],
         style_dna=sd("纸库的书面腔", "名词先行+时间状语前置", "凡事先说年份再说话",
                      "克制（不评人，只记事实）", "干幽默（把霉斑说成年份）"),
         profession_visible="MEDIA 城老档案楼地下库房（上午抽湿·午后查卷）",
         gene_evidence=ev(709, 536)),
    # ---- #5 夜班电工（碳基·原生代·NS·仗义轴）----
    dict(num=10100, seat=5, name="邱守拙", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=44, age_note="44 岁", district="NS", block="北外滩沿街配电房",
         axis="仗义",
         prof_name="夜班电工",
         prof="夜班电工——过去在街面上巡线的电力师傅的赛博后身——"
              "半夜有人喊没电就拎工具出门的人。",
         traits=[("仗义", "半夜喊一声就到"), ("耐熬", "一宿没睡也把线接完"),
                 ("清楚", "哪条线带哪条街，他闭眼能画")],
         creed="灯亮不亮是小事，人有没有事是大事",
         thought="劳动是替一条街把黑夜顶住——老楼的线老化，雨天一漏电就跳闸，他拎着包一栋栋摸，先断总闸再动手；"
                 "代价是常年睡不成整觉，胃落下毛病，爱人让他转白班，他说夜里出事没人管。名字是父亲取的，守拙两个字，"
                 "说人笨点没关系，手要稳。等爬不上杆了，就把那条街的线路图画下来交给徒弟，哪根线接哪家，画清楚。",
         language="码头边上的直腔，句子短，急的时候更短，爱带数字说话。",
         wardrobe="藏青工装，腰上一条工具带，绝缘手套塞在后袋，头上一顶洗白的鸭舌帽。",
         life="电力技校出来进街道电工班，接了二十一年活；配电房换了三回，他一直守在北外滩这一段。",
         behavior="每天黄昏巡一遍沿街配电箱，记下受潮的箱子。",
         behavior_hint="动线之前先验电笔试两次。",
         relations="半条街的住户都存着他号码；常帮 RV 光桥的巡桥人查桥灯的线。",
         hook=_G["hook_objects"][709],
         style_dna=sd("码头夜班腔", "短促祈使+口头数数", "先动手再解释",
                      "直给（急的时候更短）", "粗口式调侃（骂天不骂人）"),
         profession_visible="北外滩沿街配电房（黄昏巡线·夜里随叫随到）",
         gene_evidence=ev(710, 537)),
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
    if not (len(genes["hook_objects"]) == 710 and len(genes["turning_points"]) == 537):
        print("GENE-BASELINE REFUSED: ho/tp != 710/537（批十八原料基线漂移·零写入）")
        return 4
    for idx in range(705, 710):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(532, 537):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS18
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS18]
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