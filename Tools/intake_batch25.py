#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批二十五·人口工厂 intake 5 席碳基原生代 C-10131~C-10135（R1830）

复用 intake_batch17 的渲染器与门闸（同源不复制逻辑），本文件只声明本批卡片与基线。
原料：ho#741-745 / tp#568-572（R1830 先登记后使用·gene_nearcheck 0 近重）。

排程：D-20261020-02 判定 census 批限非让路窗（19:00-次日 09:00）+周末全窗；
本文件日间可写不可跑，实际入册由夜窗轮次执行（批二十三/二十四在前，按序入册）。
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
BATCH = "批二十五"
MAX_ID = 10130
PRE_LIGHT = 10124
POST_LIGHT = 10129

with io.open(os.path.join(CO, "genes", "lives.json"), encoding="utf-8") as _f:
    _G = json.load(_f)


def ev(ho_n, tp_n):
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (ho_n, _G["hook_objects"][ho_n - 1], tp_n, _G["turning_points"][tp_n - 1]))


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS25 = [
    # ---- #1 白铁匠（碳基·原生代·MD·实在轴）----
    dict(num=10131, seat=1, name="贾德顺", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=58, age_note="58 岁", district="MD", block="老城巷白铁作",
         axis="实在",
         prof_name="白铁匠",
         prof="白铁匠——过去敲水桶、打簸箕、卷烟囱弯头的手艺人的赛博后身——"
              "让一件铁皮家什再用上十年的。",
         traits=[("实在", "咬口不严就整只重敲"), ("耳尖", "听敲声辨得出薄厚"),
                 ("不糊弄", "焊缝一律折边再咬")],
         creed="铁皮薄，手上有寸才不薄",
         thought="劳动是替人把漏了的家什敲回能用——先看铁皮是镀锌的还是冷轧的，锌层一伤就"
                 "先补锡；下料照旧件摊平画样，剪口要直，歪一分咬口就咬不上；折边得垫在砧"
                 "上一寸一寸敲，咬口咬三折才不漏，最后拿木锤把鼓的地方找平。代价是两只耳"
                 "朵被敲击声磨得发闷，右手腕常年贴着膏药。名字是父亲取的，德顺两个字，说"
                 "是手上有德，日子才顺。等听不准薄厚了，就把那套剪子、木锤按大小挂在墙上。",
         language="白铁作的硬腔，短促，爱带数字说尺寸。",
         wardrobe="藏蓝工作服，袖口卷起，腕上缠着护带，裤脚溅着锡点。",
         life="十六岁进五金社学敲白铁，社散后在老城巷自己支了间作。",
         behavior="开工先拿剪子试一张边角料，听声音再看剪刀口。",
         behavior_hint="客人拿漏桶来，他先问一句是装水还是装油。",
         relations="巷里人家的水桶、簸箕都找他；和箍桶匠狄长庚换着修桶身与桶箍。",
         hook=_G["hook_objects"][740],
         style_dna=sd("白铁硬腔", "短促带数字的句子", "铁皮再薄，也得给人用到老",
                      "实（把关心说成尺寸）", "手艺人自嘲（拿耳朵背打趣）"),
         profession_visible="老城巷白铁作（清晨下料·午后咬口）",
         gene_evidence=ev(741, 568)),

    # ---- #2 箍桶匠（碳基·原生代·OR·耐性轴）----
    dict(num=10132, seat=2, name="狄长庚", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=63, age_note="63 岁", district="OR", block="老街河埠桶作",
         axis="耐性",
         prof_name="箍桶匠",
         prof="箍桶匠——过去拼桶板、上铁箍、修澡盆的手艺人的赛博后身——"
              "让一只桶再担十年水的。",
         traits=[("耐性", "一只桶要箍三遍才服帖"), ("眼里有缝", "板缝对上光才叫严"),
                 ("惜旧", "旧板的纹路能配就配")],
         creed="桶不漏，不在箍紧，在板服",
         thought="劳动是替人把散了的桶重新箍住——桶板要先按弧度和木纹配对，直纹做侧板、斜"
                 "纹做底板，配错了受水就胀裂；上箍前得把板缝刮净，塞进竹青与桐油灰，箍一"
                 "道转一圈，敲实了再紧下一道；箍完注水浸三天，看哪条缝先渗。代价是常年蹲"
                 "着干活，膝盖落下了病，手上全是铁丝划出的细口。名字是族里先生取的，长庚"
                 "两个字，取的是耐得住长夜的意思。等弯不下腰了，就把箍圈一只只挂上梁，替"
                 "人认桶的年头。",
         language="河埠的慢腔，说话拖尾音，爱讲木头的性子。",
         wardrobe="洗得发白的青布褂，膝盖上缝着两块补丁，腰里挂一把小斧。",
         life="小时候在河埠看父亲箍桶，木器社散了以后接了父亲那套箍圈。",
         behavior="动手前把桶板在河埠水里泡一遍，摸过纹路才拼。",
         behavior_hint="人家抬桶来修，他先问一句是挑水还是腌菜。",
         relations="河埠挑水的、酱园腌菜的都找他；和木匠甘守业常换木料。",
         hook=_G["hook_objects"][741],
         style_dna=sd("河埠慢腔", "拖尾音的缓句", "板服了，箍才吃得住",
                      "厚（把耐心说成木头）", "拿桶打趣的闷幽默"),
         profession_visible="老街河埠桶作（上午泡板·午后上箍）",
         gene_evidence=ev(742, 569)),

    # ---- #3 弹棉花匠（碳基·原生代·NS·温厚轴）----
    dict(num=10133, seat=3, name="茅德生", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=57, age_note="57 岁", district="NS", block="北外滩弹花铺",
         axis="温厚",
         prof_name="弹棉花匠",
         prof="弹棉花匠——过去弹被胎、翻旧被、絮棉袄的手艺人的赛博后身——"
              "让一床被子重新暖起来的。",
         traits=[("温厚", "谁家办喜事都不催工钱"), ("手匀", "弹出来的絮厚薄一致"),
                 ("心细", "被面旧了先问要不要留")],
         creed="被子暖不暖，看絮松不松",
         thought="劳动是替人把结了块的旧被重新弹松——先把被面拆下来单洗衣晾，被胎撕成小"
                 "块摊在案上，弓弦贴着絮走，手腕一压一松，絮就炸开；弹完要铺成方，四边"
                 "拉齐再罩纱，纱线走斜格才不跑絮。代价是吸了一辈子棉尘，肺上落了毛病，"
                 "肩上常年勒着弓背的印。名字是母亲取的，德生两个字，说是做人得积德才有"
                 "生路。等背不动弓了，就把弓弦解下来收进柜子，替人挑旧棉袄里的絮。",
         language="弹花铺的暖腔，说话慢，爱打比方说棉花的性子。",
         wardrobe="灰白旧棉袄，肩上一块厚垫布，眉毛上常挂着细棉绒。",
         life="十七岁跟着堂叔学弹花，棉站撤了以后在北外滩开了间弹花铺。",
         behavior="开铺先把案上的絮扫净，再给弓弦上一层蜡。",
         behavior_hint="人家抱被来，他先问一句是翻新还是加厚。",
         relations="办喜事的人家都来弹新被；和裁缝边秀云常换布头。",
         hook=_G["hook_objects"][742],
         style_dna=sd("弹花暖腔", "慢而长的软句", "絮松了，夜就短了",
                      "暖（把惦记说成被子）", "拿自己被呛打趣的憨幽默"),
         profession_visible="北外滩弹花铺（上午拆被·午后弹花）",
         gene_evidence=ev(743, 570)),

    # ---- #4 铅字排版工（碳基·原生代·GM·讲究轴）----
    dict(num=10134, seat=4, name="汤秀琴", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=60, age_note="60 岁", district="GM", block="游戏城印刷所",
         axis="讲究",
         prof_name="铅字排版工",
         prof="铅字排版工——过去检字、拼版、校红的手艺人的赛博后身——"
              "让一张纸上的字站得端正的。",
         traits=[("讲究", "行距差一齿就重排"), ("眼毒", "错一个偏旁一眼挑出"),
                 ("手稳", "字粒夹起来不磕角")],
         creed="字站得正，人才认得清",
         thought="劳动是替人把一篇稿子排成能印的版——先按稿数好字数，算出每栏能放多"
                 "少行；检字时字粒要从字架上反着认，手托端平，拣起来放进版盘，行与行"
                 "之间垫铅条，字要压到线，松一颗印出来就是歪的；拼完刷一遍红，对着原"
                 "稿逐字校，标点也校。代价是常年低头，脖子僵得转不动，手指被铅字磨得"
                 "发黑。名字是父亲取的，秀琴两个字，说是字要秀气，做事要像琴弦有条理。"
                 "等铅字架拆了，她把最后一盘字粒按部首排好，教人认反字。",
         language="印刷所的书面腔，说话完整，爱纠字音。",
         wardrobe="深灰套袖罩衫，胸前别一支红蓝铅笔，指腹沾着洗不掉的墨。",
         life="十八岁进印刷厂当检字工，厂子改胶印后留下整理旧铅字。",
         behavior="开工先把版盘擦一遍，再把字架上的字粒按部首对齐。",
         behavior_hint="人家送稿来，她先问一句急不急，急的她只接短稿。",
         relations="所里的老编辑都认她的手；和修笔匠常静秋隔着半条街。",
         hook=_G["hook_objects"][743],
         style_dna=sd("排字书面腔", "完整有层次的复句", "字要对得起纸",
                      "敬（把认真说成字）", "拿错字打趣的冷幽默"),
         profession_visible="游戏城印刷所（上午检字·午后校红）",
         gene_evidence=ev(744, 571)),

    # ---- #5 钉秤匠（碳基·原生代·QT·公道轴）----
    dict(num=10135, seat=5, name="卫秉公", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=66, age_note="66 岁", district="QT", block="秦淮坊市口秤摊",
         axis="公道",
         prof_name="钉秤匠",
         prof="钉秤匠——过去做杆秤、钉秤星、校砝码的手艺人的赛博后身——"
              "让一笔买卖两头都不亏的。",
         traits=[("公道", "谁的秤都按同一套砝码校"), ("手准", "秤星差半粒也重钉"),
                 ("直", "短斤两的秤他不接")],
         creed="秤要平，人心才平",
         thought="劳动是替人做一杆能服众的秤——先挑硬木做秤杆，刨圆了晾半个月，木头"
                 "干透才不走形；定秤纽要按秤量算位置，位置偏一点，称重的准头就全歪；钉"
                 "秤星得先用砝码一档档试，找出零点，再拿铜丝一粒粒嵌进去，磨平了才看得"
                 "清。代价是眼睛在刻度上耗得早花，右手拇指被铜丝扎出一层硬茧。名字是祖父"
                 "取的，秉公两个字，说是做秤的人心里得有杆秤。等眼力不够了，他就只校不"
                 "做，替人验老秤准不准。",
         language="市口的直腔，说话干脆，爱讲准头。",
         wardrobe="深褐对襟褂，腰里挂着砝码袋，眼睛上架着老花镜。",
         life="十六岁跟祖父学钉秤，衡器社散了以后在市口摆了张秤摊。",
         behavior="开工先拿标准砝码校一遍自己的老秤。",
         behavior_hint="人家来做秤，他先问一句是卖菜还是收粮。",
         relations="市口卖菜的、收粮的都找他校秤；和铁匠铺的老匠人共用一个风箱。",
         hook=_G["hook_objects"][744],
         style_dna=sd("市口直腔", "干脆的短句", "秤星不哄人",
                      "正（把认真说成公道）", "拿缺斤两打趣的硬幽默"),
         profession_visible="秦淮坊市口秤摊（上午校秤·午后钉星）",
         gene_evidence=ev(745, 572)),
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
    if not (ho_n == 745 and tp_n == 572):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 745/572（批二十五原料基线漂移·零写入）")
        return 4
    for idx in range(740, 745):
        if genes["hook_objects"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(567, 572):
        if genes["turning_points"][idx].strip("? ") == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4

    b17.CARDS17 = CARDS25
    b17.BATCH = BATCH
    rendered = [(c, b17.render_card17(c), ri.build_light(c)) for c in CARDS25]
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
        print("INTAKE BATCH25 OK: C-10131~C-10135 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())