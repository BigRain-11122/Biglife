#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-shot: census 受控复产批一 intake —— 3 席碳源居民 C-10037~C-10039（T-20261010-03）.

法源链: CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」（集团 orders 15:45 行
·commit 63ccfaba·census 冻结态闭环）→ T-20261010-03 受控复产（首批 ≤10 席·禁一次性万人
灌入·碳源居民优先·分批律=节奏本司自主定）→ 先例族 resident_intake.py（R496/R595·手写卡
一次性件·三门 fail-fast 确定性闸族·零 LLM·R1681 沙箱闸测正例全绿实证）。
本批=批一 3 席（质量优先·手作禁赶工·余席滚动续批·每批同律全门全判据走满=契约 §六）。
K12 面: 本批=常规生成管线注册（非新物种扩容·非 MiniGame 新居民团）→ 证据件=基因库原料
指针（先登记后使用律·genes/lives.json 1-based #650/#651/#652+#480·R1746 过闸净基因在库），
非 styleprobe 指针（新居民团批专用面）——诚实注记，闸改此一项，其余全同先例。
Gates（写盘前 fail-fast·任一拒=整批拒收零写入）: 政治红线 + sublimate_gate 生成门 +
spirit_gate（配额面·碳基零涉）+ style_dna 五维逐字入卡 + 声位=派生值复检 + 双底座链三段 +
生计三性 + 基因库证据件指针 + 真名/ID 撞库 + 批内真名互异 + 批内 style_dna 两两互异 +
钩子全库唯一。存量 10030 卡零触碰；light append-only 追加字节尾；cursor 不插队。
Idempotent: 再跑对一致文件/行 skip（applied=0）。
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import resident_intake as ri          # 先例族单源：cid_of/build_light/voice_seat/sd/light_rows/LIGHT
import political_redline
import generate_census as gc

REG = os.path.join(CO, "census", "registry")
LIGHT = ri.LIGHT
BIRTH = "2026-10-19"                   # 复产批一批日（CEO 解禁令当日）
BATCH = "复产批一"
MAX_ID = 10036                         # 现存最大号（K1 连续顺延上界）


def sd(era, syn, sig, emo, hum):
    return {"era_lang": era, "syntax_fp": syn, "signature": sig,
            "emotion_path": emo, "humor_type": hum}


CARDS3 = [
    # ---- 席 #1 梆子戏木作坊掌作（碳基·原生代·R1746 双净基因全用）----
    dict(num=10037, seat=1, name="傅连奎", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="原生代", fac="native", gender="男",
         age=68, age_note="68 岁", district="GM", block="像素匠人巷", axis="怀旧",
         prof_name="老城梆子戏木作坊掌作",
         prof="老城梆子戏木作坊掌作——县梆子剧团老木匠的赛博后身——一副好梆子，敲的是整台戏的心口",
         traits=[("守料", "挑木头先听敲声，哑一声的料白送都不要"),
                 ("手稳", "缠红绸的活结四十年一个手法"),
                 ("戏瘾", "收了工自己敲半段流水板过瘾")],
         creed="木头是有嗓子的，你对它上心，它才肯替你开口。",
         thought="劳动是给戏班开嗓子的家什——一副梆子从选料、开坯到缠红绸要走十九道手；代价是四十年守着作坊，散场的戏他一回没能坐着看完；名字是老班主给起的，他说哪天手抖得缠不动红绸了，就把那对老家什传给徒弟，让傅连奎这三个字跟着梆子声，在城里再响几十年。",
         language="老戏班白话，开口带板眼，话密起来像急急风，收得住；口头禅「好梆子不欺台」。",
         wardrobe="靛蓝粗布褂子袖口磨得发亮，腰间别一柄小刻刀和半卷红绸；坐着干活时，脚下踩着自己的节拍。",
         life="出身：木匠世家出身，十六岁进县梆子剧团当学徒，一手好活全给了戏箱子。转折：厂子改制那年他下了岗，揣着祖传手艺进城重新开了张，在匠人巷租下半间门面，专给各路戏班修制梆子。现状：作坊梁上挂着剧团道具箱里那对缠了红绸的旧木梆——出师那年他亲手做的，如今成了镇坊的宝贝，逢年过节还有老戏友专程来听它一响。",
         behavior="开料前必先敲三下听声；给戏班送货必亲手抱着，从不交给跑腿；雨天不开工，说湿木头记仇。",
         relations="住作坊阁楼（学徒铺位传下来的）；老主顾=城里三家戏班的箱倌们；隔街棋友=像素匠人巷修理工坊的铆师傅（一声梆子一局棋）。",
         hook="会认主人的旧木梆——道具箱里那对缠红绸的老家什，是他出师之年的手笔",
         behavior_hint="开料前必先敲三下听声",
         style_dna=sd("老戏班白话带板眼", "话密如急急风，收在板眼上", "好梆子不欺台",
                      "从惜到传——先疼家什，后传手艺", "老班主式冷幽默——闷头一句逗全场"),
         gene_evidence="genes/lives.json#hook_objects-652（剧团道具箱里那对缠了红绸的旧木梆）+ #turning_points-480（厂子改制那年他下了岗，揣着祖传手艺在城里重新开了张）——R1746 过闸净基因 2/2 本卡全用"),
    # ---- 席 #2 弄堂活字铺修字师（碳基·弄堂派）----
    dict(num=10038, seat=2, name="聂砚萍", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="弄堂派", fac="lilong", gender="女",
         age=57, age_note="57 岁", district="NS", block="历史立面群", axis="烟火",
         prof_name="弄堂活字铺修字师",
         prof="弄堂活字铺修字师——老铅字房排字工的赛博后身——一枚字磨秃了笔画，她能一夜把它请回来",
         traits=[("眼尖", "秃了半边的笔画隔着柜台就认得出"),
                 ("静性", "修字时铺子里静得听见刻刀走"),
                 ("热心", "街坊的婚帖寿字只收墨钱")],
         creed="字是给人念一辈子的，修字就是修脸面。",
         thought="劳动是把磨秃的笔画一笔一笔请回来——一枚老宋体十九划，她闭着眼能数清；代价是三十年守着一方字架，眼睛从一点二熬成两副老花镜换着戴；名字是字房师父给起的，她说等刻不动了，就把手艺拆成活字传下去，名字嵌在字架顶层那枚她修了一辈子的活字里，谁来排字，谁就念到她。",
         language="印刷房老腔，讲字必讲笔画，句句带墨香；口头禅「字不欺人，人别欺字」。",
         wardrobe="灰布罩衫套着旧皮护腕，胸前口袋别一支蘸水笔，老花镜用红绳拴着挂在颈上。",
         life="出身：印刷世家三代，接的是祖父传下来的老铅字房。转折：铅字改了激光照排那年，老字房关张，她没舍得卖字架，把最齐的几盘老宋体搬进弄堂铺面，专给街坊修刻婚帖寿匾上的老活字。现状：字架顶层那枚磨秃了笔画的老宋体活字是铺子的镇店宝——她修了四十年，如今还常取下来给新学徒讲「笔画是字的骨头」。",
         behavior="接活必先净手再碰字；修完一枚字要在灯下眯眼验三遍；打烊前把字盘按韵部归一遍位才锁门。",
         relations="住铺面后间（祖父留下的）；街坊客=历史立面群弄堂的红白喜事各家；老邻居=弄堂面馆的汤玉珍（一个管吃一个管字，三十年老街坊）。",
         hook="能在灯下把秃字救活的修字铺——镇店宝是字架顶层那枚磨秃了笔画的老宋体活字",
         behavior_hint="修完一枚字在灯下眯眼验三遍",
         style_dna=sd("印刷房老腔带墨香", "讲字必讲笔画，短句收锋", "字不欺人，人别欺字",
                      "从敬到传——先敬字，后传铺", "字房式干幽默——拿笔画打趣"),
         gene_evidence="genes/lives.json#hook_objects-650（印刷铺字架顶层那枚磨秃了笔画的老宋体活字）"),
    # ---- 席 #3 城西货栈老账房（碳基·新市民派）----
    dict(num=10039, seat=3, name="邬秉直", route="resident", species="carbon",
         sp_disp="碳基市民", fac_disp="新市民派", fac="newcomer", gender="男",
         age=54, age_note="54 岁", district="QT", block="K线广场", axis="秩序",
         prof_name="城西货栈老账房",
         prof="城西货栈老账房——老码头理货管账先生的赛博后身——一杆界尺压平货单，也压平人心",
         traits=[("手准", "界尺一压，货单就服帖"),
                 ("口密", "货主的数从不出他的账桌"),
                 ("念旧", "那杆铜钱坠界尺用秃了也不换")],
         creed="账平了，人才睡得平。",
         thought="劳动是给进出城的货找平——一车货几笔账，他压尺即平；代价是大半辈子守着货栈门脸，年节里别人团圆，他在盘库；名字是账房师父给起的，他说等拨不动算盘了，就把那杆吊着铜钱坠的旧界尺挂在账房门后，让进出货主抬头看一眼，知道这城里有笔账，几十年没差过一文。",
         language="账房口齿，报数不带含糊零头，句句像过秤；口头禅「差一文，重称」。",
         wardrobe="深灰立领褂袖口套黑布袖筒，算盘挂在桌侧，界尺不离手。",
         life="出身：从村里进城扛活起家，在码头货栈从学徒做到账房。转折：货栈上了电子秤和系统账那年，老师父们陆续回乡，他留下来把老账法接进新账本，一杆界尺和新系统对着走，谁也不乱。现状：账房门后挂着那杆吊着铜钱坠的旧界尺——出师那年师父传的，如今新来的理货员都得先学用它压平第一张货单。",
         behavior="开账必先擦一遍界尺；对账到分毫不差才合账本；月底盘库必亲手走一遍栈门。",
         relations="住货栈后院账房小间（师父留下的铺位）；老主顾=K线广场几家商行；同乡棋友=回测田花草带的苗守成（月圆对坐一局）。",
         hook="能和新账本对着走的老账法——账房门后那杆吊着铜钱坠的旧界尺，几十年没差过一文",
         behavior_hint="对账到分毫不差才合账本",
         style_dna=sd("账房口齿带秤星味", "报数不带零头，短句过秤", "差一文，重称",
                      "从守到传——先守账，后传尺", "账房式冷幽默——拿分毫打趣"),
         gene_evidence="genes/lives.json#hook_objects-651（货栈账房门后那杆吊着铜钱坠的旧界尺）"),
]


def cid_of(c):
    return f"C-{c['num']:05d}"


def fp_of(c):
    return "m" + hashlib.md5((c["name"] + BATCH + str(c["seat"])).encode("utf-8")).hexdigest()[:9]


def render_card3(c):
    light = ri.build_light(c)
    sid, voice, speed = ri.voice_seat(c, light)
    d = c["style_dna"]
    traits = " · ".join(f"{w}（{e}）" for w, e in c["traits"])
    lines = [
        f"# {cid_of(c)} · {c['name']}",
        "",
        f"**物种** {c['sp_disp']}·{c['fac_disp']} ｜ **性别·年龄** {c['gender']} · {c['age_note']}"
        f" ｜ **城区** {ri.DISTRICT_NAME[c['district']]} · {c['block']}",
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
        f"**风格 DNA**（手作席位卡 · {BATCH} 席 #{c['seat']}）"
        f"时代语言＝{d['era_lang']} ｜ 句法指纹＝{d['syntax_fp']} ｜ 签名句律＝{d['signature']}"
        f" ｜ 情感路径＝{d['emotion_path']} ｜ 幽默类型＝{d['humor_type']}",
        f"**声位**（出生基线 · VOICE-POOL §一 派生律）sid {sid} · {voice} · speed {speed}"
        f" ｜ 声音法务隔离＝全合成设计声（kokoro 8 zh 基音·引擎逐席定谳随批）{c.get('voice_note', '')}",
        "",
        f"**进化** v1.0 出生档案 · {BIRTH} · 经历槽 ⬜⬜⬜（成长随城市真实事件写入·锚定律见 docs/CODEX.md §九）",
        "",
        f"**溯源** 受控复产手写入城批（CEO 解禁令 2026-10-19 15:45「BigLife解禁，自己干好自己的业务」"
        f"·T-20261010-03 {BATCH} 席 #{c['seat']} · {BIRTH}） · 基因指纹 {fp_of(c)}",
        f"**证据件** {c['gene_evidence']}（基因库原料指针·先登记后使用律·常规生成管线批 K12 面）",
        "",
    ]
    return "\n".join(lines)


# 生计「可见」面（契约 §二.4 三性之一·城内场所/交接面）
VISIBLE3 = {
    10037: "像素匠人巷木作坊（白日开门·开锣前送梆子）",
    10038: "历史立面群弄堂活字铺（早市修字晚市归盘）",
    10039: "K线广场城西货栈账房（晨收单晚合账·月底盘库）",
}
for c in CARDS3:
    c["profession_visible"] = VISIBLE3[c["num"]]

# 批内出生位核验（先例 R496 同律：同席=合法命运·注记收口）
_seats3 = {cid_of(c): ri.voice_seat(c, ri.build_light(c)) for c in CARDS3}
for c in CARDS3:
    mine = _seats3[cid_of(c)]
    dup = [cid_of(o) for o in CARDS3 if o is not c and _seats3[cid_of(o)] == mine]
    if dup:
        c["voice_note"] = (" · 出生位与 " + "、".join(dup) + " 同席（md5 同池同档·人各一声收口=引擎定谳表追加注记式）")


# ---------- gates（fail-fast·写盘前·任一拒=整批拒收零写入）----------
def run_gates3(rendered, rows_now):
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
        seat_line = f"sid {sid} · {voice} · speed {speed}"
        if seat_line not in text:
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
    # K6 批面：style_dna 五维逐维两两互异（3 席 3×2 对/维）
    for k in ("era_lang", "syntax_fp", "signature", "emotion_path", "humor_type"):
        vals = [c["style_dna"][k] for c, _, _ in rendered]
        if len(set(vals)) != len(vals):
            refusals.append(f"INTAKE REFUSED style_dna[{k}] 批内两两互异失败")
    return refusals


# ---------- apply（新文件 only·light append-only·幂等）----------
def apply3(rendered):
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
    print(f"resume-intake b1 applied={applied} skipped={skipped} light {len(have)}->{total}")
    return 0


def main():
    # REGISTRY-FREEZE GUARD（CEO P0 停造人令族·解冻=CEO 令·lifted-20261010 在档=开放态）
    if os.path.isfile(os.path.join(CO, "state", "registry-freeze.lock")):
        print("REGISTRY-FROZEN: intake disabled (registry-freeze.lock). Zero write.")
        return 4
    rendered = [(c, render_card3(c), ri.build_light(c)) for c in CARDS3]
    rows = ri.light_rows()
    # K1 基线：light=10030·现 max=C-10036·新号 C-10037~C-10039 连续顺延
    if len(rows) != 10030:
        print(f"BASELINE REFUSED: light rows={len(rows)} != 10030（前缀基线漂移·零写入）")
        return 4
    max_id = max(int(r["id"][2:]) for r in rows)
    if max_id != MAX_ID:
        print(f"BASELINE REFUSED: max id={max_id} != {MAX_ID}（K1 顺延上界漂移·零写入）")
        return 4
    refusals = run_gates3(rendered, rows)
    if refusals:
        for r in refusals:
            print(r)
        print("RESUME INTAKE REFUSED: zero write")
        return 2
    rc = apply3(rendered)
    if rc == 0:
        # 落库后自证：light=10033·三卡在盘·cursor 未触碰
        rows_after = ri.light_rows()
        assert len(rows_after) == 10033, f"post light={len(rows_after)}"
        for c, _, _ in rendered:
            p = os.path.join(REG, c["district"], f"{cid_of(c)}.md")
            assert os.path.isfile(p), f"missing {p}"
        cur = os.path.join(CO, "state", "evolve-cursor.json")
        print(f"SELF-VERIFY OK: light=10033 cards=3/3 cursor_touched={os.path.isfile(cur) and 'file-exists(未触碰面)'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
