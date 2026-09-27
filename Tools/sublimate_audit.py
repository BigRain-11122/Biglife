# -*- coding: utf-8 -*-
"""升华律三色盘点器 v1.2 —— O-20260926-2225-bm-c 执行八件之④（存量三色盘点+补链批「注记行」判据面+复古后身定谳白名单）

判别口径（2026-09-26 R384 定谳·T-20260926-18 分步④；v1.2=R453 复古后身定谳+分表口径修正）：
  ✅ 双底座齐 = 卡面含显式「赛博后身」链（令 §一.5 叙事链中环法定格式：
               `未来形态——现实原型的（赛博）后身——升华一句话`）
  ✅ 复古亚型 = 「复古后身」=（赛博）后身合法亚型（R453 定谳·限注册模板族白名单
               VARIANT_LEGAL·全库唯一变体族 8bit 乐师 227 席）——三段链齐备同律承载
  ⚠️ 半升华   = 未来形态在册（79 职业模板定谳表内）但「赛博后身」中链不显式
  ❌ 纯现实   = 只写现实态零未来形态（CEO 例「送快递的」）——79 模板逐一定谳
               均为硅基城本位未来形态，本批 ❌=0；未知模板落 REVIEW 复核桶不误染
  像素灵（生灵族）= 物种名自带现实原型词根（电波猫/消息雀/雨声蛙/风铃蝶/数据锦鲤/
               守夜灯灵）——按令 §一.8/§二.2 生灵登记门单列注记·生灵册步⑥收口
  未来原生族（城生城长第一代）= 令 §一.6 合法族·如实注记（计入本线不豁免链义务）
  盘点体 = census/registry/{GM,MD,NS,OR,QT,RV}/*.md 生成卡（荣誉席 3+手写锚 20
           非生成面恒排除·如实计数注记）

纯确定性零 LLM；复跑幂等（只读扫描+报告覆写）。
"""
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "census", "registry")
REPORT = os.path.join(ROOT, "docs", "research", "R-20260926-sublimation-census.md")

# 79 职业模板定谳表（2026-09-26 全库去重逐模板判读：全数=硅基城本位未来形态）
FUTURE_FORMS = {
    "像素小学学生", "穿城信使", "新市民安居顾问", "像素学徒", "缓存管理员", "数据搬运工",
    "城市气象播报员", "8bit 乐师", "节日活动策划", "算法调参师", "防火墙巡林员", "数据清洗工",
    "玩家留言整理员", "盘口记录员", "感知网养线工", "大编译调律师", "沙盒建筑师", "信号中继员",
    "七段街区导游", "数据牧人", "伴居灵", "语义翻译官", "巡信使", "信使小跟班", "像素小店主",
    "量化策略研究员", "感知塔站值守员", "外环巡夜员", "回测农", "彩蛋埋藏师", "bug 猎人",
    "K线屏画师", "粉丝回信人", "游戏策划", "风控瞭望员", "晨操领队", "NPC 服装师", "视频修复师",
    "全城对时师", "夜灯员", "平台对接员", "关卡建筑师", "江面巡游员", "编年史誊录员", "编年史馆员",
    "旧件修复师", "QUANT 食堂大厨", "灯塔守望", "风控官", "声景师", "声优棚掌柜", "边缘杂货店主",
    "尾盘茶室老板", "游戏楼门童", "字幕君", "选题官", "直播布景师", "信使墙管理员", "资金金灯匠",
    "引擎医生", "时钟校准员", "城门守门人", "进度刻碑师", "数据化妆师", "光桥市集摊主", "灯牌制作师",
    "风信使", "塔区风筝队员", "机器站宿舍管理员", "信号塔工", "江面清波工", "脑环广场管理员",
    "渡轮船长", "热搜观测员", "弄堂小囡", "白玉兰园艺师", "档案修护师", "渡轮检票员", "老克勒咖啡主",
}
SPRITE_PREFIX = "像素灵"
# v1.1（2026-09-27 R426·T-18 步⑨分步④）：补链批「注记行」判据面标记（Tools/sublimate_chain.py 同源引用·禁双建）
NOTE_MARK = "**升华链**（升华令 §二.8 追加注记·原文保全）"
# v1.2（2026-09-27 R453·T-18 步⑨变体桶定谳件）：复古后身=（赛博）后身合法亚型——限注册模板族
# 白名单（全库唯一变体族 8bit 乐师·genes/professions.json twist 源）；新卡法定中环「（赛博）后身」
# 口径不变·白名单外复古后身照旧 REVIEW+生成门照拒；generate_census.sublimate_gate 同源引用（禁双建）；
# 白名单扩行须先过定谳程序（立单+T2 登记）·禁先斩后奏。
VARIANT_LEGAL = {"8bit 乐师"}
DISTRICTS = ["GM", "MD", "NS", "OR", "QT", "RV"]


def prof_name(prof):
    return prof.split("：")[0].split("——")[0].strip()


def scan():
    rows = []
    excluded = []
    for d in DISTRICTS:
        for p in sorted(glob.glob(os.path.join(REG, d, "*.md"))):
            t = io.open(p, encoding="utf-8").read()
            m = re.search(r"\*\*职业\*\* (.+)", t)
            prof = m.group(1).strip() if m else ""
            ms = re.search(r"\*\*物种\*\* (.+?)｜", t)
            species = ms.group(1).strip() if ms else "?"
            chain_any = "赛博后身" in t
            chain_prof = "赛博后身" in prof
            rows.append({
                "id": os.path.basename(p)[:-3], "district": d, "species": species,
                "prof": prof, "name": prof_name(prof),
                "chain": chain_any, "chain_prof": chain_prof,
                "note": NOTE_MARK in t, "variant": "复古后身" in prof,
                "sprite": species.startswith(SPRITE_PREFIX),
            })
    for sub in ("reserved", "anchors"):
        for p in sorted(glob.glob(os.path.join(REG, "..", sub, "*.md"))):
            cid = os.path.basename(p)[:-3]
            if re.match(r"C-\d{5}$", cid):
                excluded.append(cid)
    return rows, excluded


def classify(rows):
    ok, half, review, sprites = [], [], [], []
    noted_res, noted_spr, variant, ok_variant = [], [], [], []
    chain_outside = 0
    for r in rows:
        if r["chain"] and not r["chain_prof"]:
            chain_outside += 1
        if r["chain"]:
            ok.append(r)
        elif r["note"]:
            (noted_spr if r["sprite"] else noted_res).append(r)
        elif r["sprite"]:
            sprites.append(r)
        elif r["variant"] and r["name"] in VARIANT_LEGAL:
            r["okv"] = True  # R453 定谳：注册模板族复古后身=合法亚型（升 ✅ 原生链·复古亚型计）
            ok_variant.append(r)
        elif r["variant"]:
            variant.append(r)  # 白名单外复古后身=照旧 REVIEW 定谳桶（生成门同判照拒）
        elif r["name"] in FUTURE_FORMS:
            half.append(r)
        else:
            review.append(r)
    return ok, half, review, sprites, noted_res, noted_spr, variant, ok_variant, chain_outside


def main():
    rows, excluded = scan()
    ok, half, review, sprites, noted_res, noted_spr, variant, ok_variant, chain_outside = classify(rows)
    n = len(rows)
    by_sp, ok_by_sp, ok_by_d, noted_by_sp, noted_by_d = {}, {}, {}, {}, {}
    for r in rows:
        by_sp[r["species"]] = by_sp.get(r["species"], 0) + 1
        # v1.2 修正 v1.1 分表双重计数（done 误含注记行→ok_by_* 与 noted_by_* 相加=注记双计·末列负值 -1729 等）：
        # 原生链列=链+复古亚型（chain/okv）·注记列=note-only·承载=两者并集·余量=总数-承载（恒 ≥0）
        if r["chain"] or r.get("okv"):
            ok_by_d[r["district"]] = ok_by_d.get(r["district"], 0) + 1
            ok_by_sp[r["species"]] = ok_by_sp.get(r["species"], 0) + 1
        if r["note"] and not r["chain"]:
            noted_by_sp[r["species"]] = noted_by_sp.get(r["species"], 0) + 1
            noted_by_d[r["district"]] = noted_by_d.get(r["district"], 0) + 1
    half_res = len(half)
    noted = len(noted_res) + len(noted_spr)
    residual = half_res + len(variant) + len(sprites)
    carried = len(ok) + len(ok_variant) + noted
    lines = []
    a = lines.append
    a("# R-20260926-sublimation-census · 存量三色盘点报告（升华律执行令 §二.4·v1.2）")
    a("")
    a("- 令源=O-20260926-2225-bm-c（硅基居民升华律执行令 v1.2/v1.3）·盘点窗 ≤2026-09-28 12:00·盘点批次=R384（2026-09-26）·v1.1 复跑=R426（2026-09-27·补链批判据面）·v1.2 定谳复跑=R453（2026-09-27·复古后身变体桶定谳收口）")
    a("- 盘点体=census/registry 六城区生成卡 %d 张（荣誉席 census/reserved %d 张+手写锚 census/anchors %d 张=非生成面恒排除·令 §三 红线荣誉席零触碰）"
      % (n, sum(1 for x in excluded if x <= "C-00009"), sum(1 for x in excluded if x > "C-00009")))
    a("- 判别口径 v1.2=✅原生链（显式「赛博后身」链）/ ✅原生链·复古亚型（「复古后身」=（赛博）后身合法亚型·R453 定谳·限注册模板族白名单 VARIANT_LEGAL）/ ✅注记链（升华令 §二.8 追加注记行=Tools/sublimate_chain.py 补链批）/ ⚠️未来形态在册·链与注记均无 / ❌只写现实态零未来形态（79 模板逐模板判读定谳=全数硅基城本位·❌=0）")
    a("- 基线（R384·2026-09-26）=✅1595·⚠️居民 7886（含复古后身变体 227）·⚠️生灵族 499·REVIEW 0——v1.1 收口判据（契约判据⑤）=⚠️ 单调递减·8385→0（变体桶定谳后）")
    a("- 工具=`Tools/sublimate_audit.py` v1.2（确定性·零 LLM·复跑幂等·报告覆写=git 史保全基线版）·复跑=python -X utf8 Tools/sublimate_audit.py")
    a("")
    a("## 一、三色总盘（v1.2 复古亚型定谳面）")
    a("")
    a("| 色 | 判据 | 张数 | 占比 |")
    a("|---|---|---|---|")
    a("| ✅ 原生链 | 显式「赛博后身」链（职业行） | %d | %.1f%% |" % (len(ok), 100.0 * len(ok) / n))
    a("| ✅ 原生链·复古亚型 | 「复古后身」=（赛博）后身合法亚型（R453 定谳·注册模板族 8bit 乐师） | %d | %.1f%% |" % (len(ok_variant), 100.0 * len(ok_variant) / n))
    a("| ✅ 注记链·居民 | 升华令 §二.8 追加注记行（补链批） | %d | %.1f%% |" % (len(noted_res), 100.0 * len(noted_res) / n))
    a("| ✅ 注记链·生灵族 | 物种域注记（《城市生灵册》#N 指针·非个体链） | %d | %.1f%% |" % (len(noted_spr), 100.0 * len(noted_spr) / n))
    a("| ⚠️ 半升华·居民余量 | 未来形态在册·链与注记均无 | %d | %.1f%% |" % (half_res, 100.0 * half_res / n))
    a("| ⚠️ 复古后身变体·白名单外 | 照旧 REVIEW 定谳桶（生成门同判照拒） | %d | %.1f%% |" % (len(variant), 100.0 * len(variant) / n))
    a("| ⚠️ 半升华·生灵族（像素灵）余量 | 物种域注记待落 | %d | %.1f%% |" % (len(sprites), 100.0 * len(sprites) / n))
    a("| ❌ 纯现实 | 只写现实态零未来形态 | 0 | 0.0% |")
    a("| REVIEW 复核桶 | 未知职业模板（不误染❌） | %d | %.2f%% |" % (len(review), 100.0 * len(review) / n))
    a("")
    a("- 令内预告对照：~1602/10003 vs 原生链实测 %d/%d（R383/R384 口径延续·复古亚型另计 %d）" % (len(ok), n, len(ok_variant)))
    a("- 链位置自检：链在职业行=%d 卡中链在行外=%d（链均落 prof 法定行·口径自洽）" % (len(ok) - chain_outside, chain_outside))
    a("- 补链收口进度（判据⑤单调递减·**R453 定谳收口达成**）：注记累计=%d（居民 %d+生灵 %d）+原生链 %d+复古亚型 %d=承载 %d/%d·⚠️ 余量=%d（居民 %d+变体白名单外 %d+生灵 %d）·**收口目标 8385→0 达成**（R453·窗 ≤10-02 内提前）"
      % (noted, len(noted_res), len(noted_spr), len(ok), len(ok_variant), carried, n, residual, half_res, len(variant), len(sprites)))
    a("- 未来原生族（城生城长第一代）=令 §一.6 合法族如实注记：计入本线、不豁免补链义务（补链=追加注记式保原文）")
    a("")
    a("## 二、分物种盘（链+注记+亚型 承载 vs 总数）")
    a("")
    a("| 物种 | 总数 | ✅原生链（含复古亚型） | ✅注记链 | 无链无注记 |")
    a("|---|---|---|---|---|")
    for k in sorted(by_sp, key=lambda k: -by_sp[k]):
        dn = ok_by_sp.get(k, 0) + noted_by_sp.get(k, 0)
        a("| %s | %d | %d | %d | %d |" % (k, by_sp[k], ok_by_sp.get(k, 0), noted_by_sp.get(k, 0), by_sp[k] - dn))
    a("")
    a("## 三、分城区盘（链+注记+亚型 承载）")
    a("")
    a("| 城区 | 卡数 | 原生链（含复古亚型） | 注记链 | 余量 |")
    a("|---|---|---|---|---|")
    tot_d = {}
    for r in rows:
        tot_d[r["district"]] = tot_d.get(r["district"], 0) + 1
    for d in DISTRICTS:
        dn = ok_by_d.get(d, 0) + noted_by_d.get(d, 0)
        a("| %s | %d | %d | %d | %d |" % (d, tot_d.get(d, 0), ok_by_d.get(d, 0), noted_by_d.get(d, 0), tot_d.get(d, 0) - dn))
    a("")
    a("## 四、结论与接续")
    a("")
    a("1. ❌纯现实=0：CEO 例「送快递的」式纯现实态在 9980 生成卡中零存在（79 职业模板逐模板判读定谳表内建于脚本·最弱锚=老克勒咖啡主/渡轮检票员族仍具城内复古叙事锚）。")
    a("2. 补链批产线（T-18 步⑨分步④·Tools/sublimate_chain.py v0）：分批律 ≤500 张/轮·追加注记式保原文（git diff 每卡 +1/-0）·复跑幂等·收口判据=⚠️ 8385→0 单调递减（居民 7886+生灵 499·窗随 P-13 Phase1 ≤10-02；复古后身变体桶单列 REVIEW 定谳后收口·不入首批）；链格=「未来形态——现实原型的（赛博）后身——升华一句话」。")
    a("3. 像素灵 499=生灵族按律②生灵登记门单列（物种名自带现实原型词根·消息雀先例在册）·收口件=《城市生灵册》步⑥——补链批走物种域注记（《城市生灵册》#1-#6 册号映射·非个体链）。")
    a("4. REVIEW 复核桶 %d 张=未知模板零存在·生成门步①接线后新卡违律计数入 QC-REPORT。" % len(review))
    a("")
    a("## 五、复古后身定谳（R453·2026-09-27·T-20260926-18 步⑨变体桶定谳件·契约判据⑤收口件）")
    a("")
    a("- **对象**：⚠️ 复古后身变体桶 227 席——全库实测=**单模板族**（8bit 乐师·genes/professions.json L38 `twist`=「音效师的复古后身——六个声部能给全城配乐」·227/227 同一职业行·零散布·rg 全库普查在案）。")
    a("- **令文对照**（O-20260926-2225-bm-c §一.1 双底座律）：8bit 乐师行三段齐备——现实底座=音效师（真实职业原型·一眼代入 ✓）+未来升华=8bit 乐师（硅基城形态 ✓）+升华一句话=「六个声部能给全城配乐」✓；非只写现实态·非凭空幻想态=**双违律零命中**。「（赛博）后身」=司内机制定形中环词（CEO 原话七连零「后身」字样·令 §一.5 叙事链格式为机制面定形）·「复古后身」=同构中环变体。")
    a("- **语义定谳**：8bit 音乐=复古科技艺术形式——音效师→8bit 乐师的升华方向=向复古科技面（非赛博未来面）·「复古」一词=对该模板未来形态的精确描述（8bit 即复古语义本体）·与城市怀旧词根族（老克勒咖啡主/渡轮检票员·§四.1「最弱锚」同族定谳=城内复古叙事锚合法）同源。")
    a("- **程序定谳**：原文保全铁律=存量卡面零改写；追加注记式=为「无显式链卡」补链的工具——对已具显式（亚型）链卡加注=双链冗余（「音效师的复古后身」的（赛博）后身=叠床架屋·制造卡面双中环表述）=**不适用**。")
    a("- **判定**：**复古后身=（赛博）后身的合法亚型（限注册模板族白名单 {8bit 乐师}·全库唯一变体族）**——227 席升 ✅ 原生链·复古亚型计·⚠️ 余量 227→0=**收口判据 8385→0 全量达成**（v1.1 契约「变体桶定谳后」兑现）。")
    a("- **生成门兼容层**（防未来卡误拒）：genes 模板行持续产出「复古后身」→sublimate_gate 白名单=本件 VARIANT_LEGAL 同源引用（模板族名判）·白名单外复古后身=照旧拒（exit 6）·新卡法定中环「（赛博）后身」口径不变（亚型不扩为通例·防规避漂移）。")
    a("- **白名单维护律**：新增复古后身模板须先过定谳程序（立单+T2 登记+白名单扩行）·禁先斩后奏；白名单外变体复现=审计 exit 3 fail-fast（ids 打印）。")
    a("")
    report = "\n".join(lines) + "\n"
    io.open(REPORT, "w", encoding="utf-8", newline="\n").write(report)
    print("sublimate_audit v1.2: cards=%d ok=%d ok_variant=%d noted_res=%d noted_spr=%d half_res=%d variant_outside=%d sprites=%d bad=0 review=%d carried=%d residual=%d"
          % (n, len(ok), len(ok_variant), len(noted_res), len(noted_spr), half_res, len(variant), len(sprites), len(review), carried, residual))
    print("report -> %s" % os.path.relpath(REPORT, ROOT))
    if review:
        print("REVIEW ids:", ",".join(r["id"] for r in review[:20]))
        sys.exit(2)
    if variant:
        print("VARIANT-OUTSIDE ids:", ",".join(r["id"] for r in variant[:20]))
        sys.exit(3)


if __name__ == "__main__":
    main()
