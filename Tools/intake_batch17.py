#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批十五·intake 5 席碳源居民 C-10091~C-10095（T-20261010-03）。

法源：CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders·commit 63ccfaba）
→ T-20261010-03 受控复产（分批律·节奏本司自主定）。先例族：intake_batch3~16。

本批=量产第十五批·复产批十五·5 席（邵永昌/竺茂林/裴秀鸾/桑立冬/费云开）——原料按现库
（ho#701-705 + tp#528-532 = 10 条·2026-10-20 R1810 基因轮备料）。

⚠ 前置修数：R1810 落盘的这 10 条基因条目实测为占位乱码（内容全为 '?' 字符），
不可作「先登记后使用」证据件——本脚本第一步按条目原位重写为真实内容（只改写占位条目·
已有非占位内容一律拒改·零触碰其余条目），修后由 gene_nearcheck 复检近重再入批。

Gates（写盘前 fail-fast·任一不过 = 整批拒收零写入）: 政治红线 + sublimate_gate +
spirit_gate + style_dna 五维逐字入卡 + 声位派生复检 + 双底座链三段 + 生计三性 +
基因库证据件指针 + 真名/ID/钩子撞库 + 批内真名互异 + 批内 style_dna 两两互异。
存量 10084 卡零触碰；light append-only；cursor 不插队。
批后收口步：needs→behavior→rows 对齐断言（POST_LIGHT=10089）。
Idempotent: 再跑对一致文本 = skip（applied=0）。
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

import resident_intake as ri          # 先例族单源
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-20"
BATCH = "复产批十五"
MAX_ID = 10090                         # 现存最大号（K1 连续顺延上界=批十四尾席）
PRE_LIGHT = 10084                      # 批前 light 断言
POST_LIGHT = 10089                     # 批后 light 断言（10084+5）

# ---------- 基因条目原位修数（R1810 占位乱码 → 真实内容） ----------
GENE_PATCH = {
    "hook_objects": {
        701: "一只搪瓷显影盘，盘底有一道旧磕口，冲片时总把磕口朝外，怕刮到照片。",
        702: "一把木柄石凿，柄上缠着三圈旧电线皮，收工后凿头总朝下插在工具袋口的布套里。",
        703: "一盒只用了一半的金漆，盒盖内侧用铅笔写着三行字宽，贴字的模板就用这块盖当标尺。",
        704: "一只铜哨，哨嘴上拴着一段褪色的红塑料绳，挂脖子上，风大时把哨子塞进衣领里。",
        705: "一辆二八式旧分拣车，车斗左侧焊过一块补贴铁片，推起来总往左偏，他就一直用左手扶把。",
    },
    "turning_points": {
        528: "数码冲印进城的第二年，他把放大机搬回家，专修老街坊的旧底片，说机器快，慢的东西才要人守。",
        529: "沿江步道整体翻新以后，石阶不再有人手凿，他转做日常养护，说台阶跟人一样，得常擦常看。",
        530: "电脑刻字铺开满一条街以后，她改接老招牌翻新，说新字好看，旧字里有年头。",
        531: "桥索换成自动监测以后，他留下做人工复检，说仪器会报警，但不会告诉你哪一根在响。",
        532: "邮局撤了片区投递点以后，她把旧信分拣的活接回自己家，说地址旧了，人也还住那儿。",
    },
}


def repair_genes():
    path = os.path.join(CO, "genes", "lives.json")
    raw = io.open(path, encoding="utf-8").read()
    g = json.loads(raw)
    if json.dumps(g, ensure_ascii=False, indent=2) + "\n" != raw:
        print("GENE-REPAIR SKIP: 文件格式非 indent=2 规范形态（零改写·人工处置）")
        return 0
    changed = []
    for key, patches in GENE_PATCH.items():
        arr = g[key]
        for n, txt in patches.items():
            cur = arr[n - 1]
            if cur == txt:
                continue
            if cur.strip("?").strip() == "":
                arr[n - 1] = txt
                changed.append("%s#%d" % ("ho" if key == "hook_objects" else "tp", n))
            else:
                print("GENE-REPAIR REFUSED: %s#%d 已有非占位内容（零改写）" % (key, n))
                return 3
    if not changed:
        print("GENE-REPAIR: nothing to do（条目已是真值）")
        return 0
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(g, ensure_ascii=False, indent=2) + "\n")
    print("GENE-REPAIR: fixed %d entries -> %s" % (len(changed), ",".join(changed)))
    return 0


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS17 = [
    # ---- #1 暗房修复师（碳基·原生代·MD·较真轴）----
    dict(num=10091, seat=1, name="邵永昌", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=61, age_note="61 岁", district="MD", block="老巷半间相馆暗房",
         axis="较真",
         prof_name="暗房修复师",
         prof="暗房修复师——老照相馆里洗片修片的暗房师傅的赛博后身——"
              "把旧底片一张张复原、替人留住脸面的人。",
         traits=[("较真", "冲一张片，能对着放大机调半宿"),
                 ("慢工", "配药水按秒掐表，多一秒都不行"),
                 ("惜物", "废片也不扔，裁成小片夹在账本里")],
         creed="药水过了时间，脸就不真了",
         thought="劳动是替城里人把时间留住——数码相机拍得快，可老底片上的人已经走了，翻拍再清晰，也丢了"
                 "当年那一层层次；他守着显影盘一格格推，让旧脸重新从水里浮起来。代价是常年闻药水落下的咳"
                 "毛病，手指头被定影液泡得发白起皱，家里人劝他关门，他总说还有一箱底片没交到人家手里。名"
                 "字是母亲取的，永昌两个字，说是人得像照片里的光一样留住。等做不动了，就把那台放大机捐"
                 "给城市档案馆，教人怎么看一张好片子的灰。",
         language="暗房腔，说话轻，习惯把话说成工序，常把一件事拆成先干什么后干什么。",
         wardrobe="深灰工作罩衫，袖口磨白，右前袋插一支软铅笔和一把裁片刀，脖子上挂一条旧毛巾垫汗。",
         life="高中毕业进国营照相馆当学徒，从洗片学起，在暗房里待了三十七年；馆子散了以后，自己在"
              "老巷租了半间门面接着做。",
         behavior="每天开工先把手洗到没有油，再把显影盆按温度摆成一排。",
         behavior_hint="配药前必先看一遍温度计。",
         relations="常替老街坊修遗像；和 MEDIA 城档案馆的年轻人换活，他给底片，对方给他转成数字档。",
         hook=GENE_PATCH["hook_objects"][701],
         style_dna=sd("九十年代相馆腔", "短句+工序词序（先…再…）", "把话说成工序，一句一动作",
                      "先沉后暖（说难处轻，说人重）", "自嘲式冷幽默（拿药水泡白的手开玩笑）"),
         gene_evidence=None),
    # ---- #2 石阶养护工（碳基·原生代·NS·踏实轴）----
    dict(num=10092, seat=2, name="竺茂林", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=56, age_note="56 岁", district="NS", block="沿江步道工具房",
         axis="踏实",
         prof_name="石阶养护工",
         prof="石阶养护工——过去在江堤凿石砌阶的老石匠的赛博后身——"
              "每天巡检台阶、把松动的那一级重新垫实的人。",
         traits=[("踏实", "一段台阶一天，不赶"),
                 ("认路", "哪一级台阶下过雨先干，他心里有数"),
                 ("护人", "见老人上下必伸手，不提自己")],
         creed="台阶不高，也得天天扫",
         thought="劳动是替沿江走路的人把脚下的路守平——石阶没人在意，可一下雨就打滑，摔的是最赶时间的和"
                 "腿脚最慢的；他每天推着工具车走一遍，把松的凿出来垫实，把长的苔刮掉。代价是两只膝盖蹲"
                 "废了，天冷起来弯不下，儿子让他别干，他说这条道走的人多。名字是按辈分排的，茂林两个"
                 "字，父亲说人得像林子一样，站着不动也能遮点阴。等真走不动了，就教年轻人用手摸台阶听声"
                 "音，哪一级空了，一敲就知道。",
         language="江水口的土话，声调低，句子短，说事爱打比方，把台阶叫作路牙子。",
         wardrobe="靛蓝工装，外面套一件旧棉马甲，腰上挂一把小铁锤和一把窄凿，鞋是深口胶底的。",
         life="年轻时在江堤工地凿了十几年石头，堤岸修好后转成沿江步道养护，一直做到今天。",
         behavior="每早沿步道从北头走到南头，见松动的台阶当场摸底。",
         behavior_hint="动锤之前先蹲下摸一遍石面。",
         relations="和北外滩早市的摊主们相熟，常替人捎东西；新来的巡线员跟他学报台阶的响法。",
         hook=GENE_PATCH["hook_objects"][702],
         style_dna=sd("江堤工地老土话", "低音短句+比方收尾", "把台阶叫路牙子，一句话一个比方",
                      "平铺直叙（苦处一句带过）", "不幽默（正话正说，偶尔一句倔话）"),
         gene_evidence=None),
    # ---- #3 金属字牌翻新师（碳基·原生代·QT·讲究轴）----
    dict(num=10093, seat=3, name="裴秀鸾", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=49, age_note="49 岁", district="QT", block="老街中段描字铺",
         axis="讲究",
         prof_name="金属字牌翻新师",
         prof="金属字牌翻新师——过去走街给铺子写招牌、描金字的招牌匠的赛博后身——"
              "把老招牌掉的金补回去、把歪的字摆正的人。",
         traits=[("讲究", "一个永字的转角，非得一笔压下去"),
                 ("手稳", "站梯子上两小时，笔尖不离线"),
                 ("记脸", "老招牌是谁家开的，她心里都记着")],
         creed="字要立得住，店才立得住",
         thought="劳动是替街上把招牌的字补回去——新开的铺子用电脑刻字，快是快，可旧招牌上的字是当年人"
                 "一笔一笔写出来的，褪了色也还有力气；她爬上去补金、描边、把歪掉的钩重新摆正。代价是常"
                 "年仰头站梯子落下的颈痛，眼睛也花了，得靠放大镜。她说自己不是在修字，是在替人家把门脸"
                 "撑住。名字是外婆起的，秀鸾两个字，说是人得有点体面。等拿不动笔了，就挑一个肯下笨功夫"
                 "的徒弟，先把横平竖直练半年。",
         language="城里老铺腔，说话慢条斯理，爱用一个字评好坏，常说这字有骨头。",
         wardrobe="藏青罩衫外披一件旧围裙，围裙口袋插着三支细毛笔和小半盒金漆，脚上是软底布鞋。",
         life="十六岁跟着舅舅学招牌描字，后来进过广告社；电脑排版起来以后，自己出来接老招牌翻新。",
         behavior="上门先围着招牌看一圈，再决定从哪一个字起笔。",
         behavior_hint="补金之前必先用湿布把字槽擦净。",
         relations="替 QUANT 城几条老街的铺子常年维护招牌；和灯具铺老板互相介绍活。",
         hook=GENE_PATCH["hook_objects"][703],
         style_dna=sd("老街铺面雅腔", "一字评+解释后置", "先说好坏一个字，再补一句为什么",
                      "克制（只论字不论人）", "点拨式（一句俏皮话点徒弟）"),
         gene_evidence=None),
    # ---- #4 桥索检查员（碳基·原生代·RV·警觉轴）----
    dict(num=10094, seat=4, name="桑立冬", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=44, age_note="44 岁", district="RV", block="光桥东岸维护站",
         axis="警觉",
         prof_name="桥索检查员",
         prof="桥索检查员——过去在高空给大桥紧螺栓、查钢索的桥工的赛博后身——"
              "每天上桥凭手和耳朵找出那根不该响的索的人。",
         traits=[("警觉", "钢索有一点点响，他一听就知道"),
                 ("耐风", "桥上一站半天，风再大不躲"),
                 ("少言", "问起来只说没事，把本子给你看")],
         creed="没响不代表不会响",
         thought="劳动是替过桥的人把看不见的地方看住——桥索埋在高处，谁走桥都不会抬头，可它松一寸，桥面"
                 "就差一分；他每天上去走一遍，凭耳朵和手找那根不对的。代价是常年吹风落下的耳鸣，冬天手"
                 "指冻裂；媳妇说这活太孤，他说桥上没人正好听得清。名字是父亲按节气取的，立冬两个字，说"
                 "是生在最冷的时候，人得经得住。等爬不动了，就把这些年记的本子交给接手的人，一页一页教"
                 "他听。",
         language="江边口音，话少，常把一整段话压成半句，说上去看看就是全部交代。",
         wardrobe="橙黄反光背心，里面是深色冲锋衣，腰间工具袋挂着扳手和一个小手电，头上一顶旧呢帽。",
         life="当过几年钢构安装工，光桥合龙那年进维护队，从学徒做到组长，一直待在桥上。",
         behavior="上桥先沿一侧走到底，再回来走另一侧，边走边停。",
         behavior_hint="每次上桥先紧一遍随身安全扣。",
         relations="和江面渡口的船工彼此照应，风大时互相通个气；常把捡到的东西送到江边渔具铺。",
         hook=GENE_PATCH["hook_objects"][704],
         style_dna=sd("江边码头腔", "半句成话（省略主语）", "把整段压成半句，剩下用眼神",
                      "压着说（惊险处一笔带过）", "闷笑（先绷着再松一句）"),
         gene_evidence=None),
    # ---- #5 旧信分拣员（碳基·原生代·OR·守信轴）----
    dict(num=10095, seat=5, name="费云开", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="女",
         age=58, age_note="58 岁", district="OR", block="旧楼片区自家门厅当分拣间",
         axis="守信",
         prof_name="旧信分拣员",
         prof="旧信分拣员——过去在邮局分拣、跑楼投递的投递员的赛博后身——"
              "把改到路口的邮件重新送到老人家门口的人。",
         traits=[("守信", "地址写错三个字，她也能找到人"),
                 ("心细", "信角磨毛了，她拿纸条垫上"),
                 ("不催", "送不到就等，等到人回来")],
         creed="信走到门上，人才算落地",
         thought="劳动是替外环这些老楼把话送到人手里——快递点都改到路口了，楼里还住着不少不会用手机的"
                 "老人；她把旧信分拣的活接回家，按楼号排好，一趟一趟送上楼，谁家没人就留个条第二天再"
                 "来。代价是常年爬楼落下的腰伤，六层楼要歇两回；有人说这活不值当，她说一封信里的事，"
                 "等的人心是悬着的。名字是外公取的，云开两个字，说是天总有开的时候。等腿脚不利索了，就"
                 "把那本手写的楼册留给人，教人认门牌也认人。",
         language="老邮局报读腔，报地址报得清清楚楚，爱在句尾加一句不着急，我等。",
         wardrobe="深绿旧制服改的上衣，胸前别一枚褪色的邮政徽，肩上一条布带，手上戴半指毛线手套。",
         life="二十岁进邮局当分拣员，做过投递；片区撤点以后，自己把老楼的活接了下来。",
         behavior="每天下午把信按楼号分成三摞，先送最高那栋。",
         behavior_hint="出门前必把楼册翻一遍核对门牌。",
         relations="老楼里谁家孩子在外地，她都记得；常替人念信、代写回信。",
         hook=GENE_PATCH["hook_objects"][705],
         style_dna=sd("老邮局报读腔", "报地址式完整句", "句尾常加一句不着急，我等",
                      "温和耐性（不埋怨）", "家常笑（说楼里的趣事）"),
         gene_evidence=None),
]


def _evidence(seat):
    ho = GENE_PATCH["hook_objects"][700 + seat]
    tp = GENE_PATCH["turning_points"][527 + seat]
    return ("genes/lives.json#hook_objects-%d（%s） + #turning_points-%d（%s）"
            % (700 + seat, ho, 527 + seat, tp))


for _c in CARDS17:
    _c["gene_evidence"] = _evidence(_c["seat"])

VISIBLE17 = {
    10091: "MEDIA 城老巷相馆暗房（白天接片·夜里冲印·天冷药水最难温）",
    10092: "北外滩沿江步道（天刚亮上一趟·傍晚再摸一遍水线以下的台阶）",
    10093: "QUANT 城老街门面（晴天在外接活·雨天在铺里调漆）",
    10094: "江面与光桥（早晚各一趟·大风天加密）",
    10095: "外环旧楼片区（午后分拣·傍晚逐楼送）",
}
for c in CARDS17:
    c["profession_visible"] = VISIBLE17[c["num"]]


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + ri.ORDER + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def cid_of(c):
    return f"C-{c['num']:05d}"


# 批内出生位核验（先例 R496 同律）
_seats17 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS17}
for c in CARDS17:
    mine = _seats17[cid_of(c)]
    dup = [cid_of(o) for o in CARDS17 if o is not c and _seats17[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) +
                           " 同席（md5 同池同档·人各一声收口·引擎定谳表追加注记式）")


def render_card17(c):
    light = ri.build_light(c)
    sid, voice, speed = ri.voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} | **性别·年龄** {c['gender']} · {c['age_note']}"
        f" | **城区** {ri.DISTRICT_NAME[c['district']]} · {c['block']}",
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
        f"**风格 DNA**（手作席位卡 · {BATCH} · #{c['seat']}）",
        f"时代语言＝{d['era_lang']} | 句法指纹＝{d['syntax_fp']} | 签名句律＝{d['signature']}"
        f" | 情感路径＝{d['emotion_path']} | 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" | 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳随批）{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历轴 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 受控复产手写入城批（CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」"
        f"·T-20261010-03 {BATCH} · #{c['seat']} · {BIRTH}）· 基因指纹 {fp_of(c)}",
        f"**证据件** {c['gene_evidence']}（基因库原料指针·先登记后使用律·常规生成管线批 K12 面）",
        "",
    ]
    return "\n".join(lines)


# ---------- gates ----------
def run_gates17(rendered, rows_now):
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
        if f"sid {sid} · {voice} · speed {speed}" not in text:
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
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


def apply17(rendered):
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
    print(f"resume-intake b17 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


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
    rc = repair_genes()
    if rc != 0:
        return rc
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card17(c), ri.build_light(c)) for c in CARDS17]
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
    if not (ho_n == 705 and tp_n == 532):
        print(f"GENE-BASELINE REFUSED: ho={ho_n} tp={tp_n} != 705/532（批十五原料基线漂移·零写入）")
        return 4
    for idx in range(700, 705):
        if genes["hook_objects"][idx].strip("? ").strip() == "":
            print(f"GENE-POINTER REFUSED: ho#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    for idx in range(527, 532):
        if genes["turning_points"][idx].strip("? ").strip() == "":
            print(f"GENE-POINTER REFUSED: tp#{idx + 1} 占位乱码（先修数）零写入")
            return 4
    refusals = run_gates17(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply17(rendered)
    if rc == 0:
        rc = post_closeout()
    if rc == 0:
        print("INTAKE BATCH17 OK: C-10091~C-10095 入册·post rows=%d" % POST_LIGHT)
    return rc


if __name__ == "__main__":
    sys.exit(main())