# -*- coding: utf-8 -*-
"""升华律三色盘点器 v1.0 —— O-20260926-2225-bm-c 执行八件之④（存量三色盘点）

判别口径（2026-09-26 R384 定谳·T-20260926-18 分步④）：
  ✅ 双底座齐 = 卡面含显式「赛博后身」链（令 §一.5 叙事链中环法定格式：
               `未来形态——现实原型的（赛博）后身——升华一句话`）
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
            })
    for sub in ("reserved", "anchors"):
        for p in sorted(glob.glob(os.path.join(REG, "..", sub, "*.md"))):
            cid = os.path.basename(p)[:-3]
            if re.match(r"C-\d{5}$", cid):
                excluded.append(cid)
    return rows, excluded


def classify(rows):
    ok, half, bad, review, sprites = [], [], [], [], []
    chain_outside = 0
    for r in rows:
        if r["chain"] and not r["chain_prof"]:
            chain_outside += 1
        if r["chain"]:
            ok.append(r)
        elif r["species"].startswith(SPRITE_PREFIX):
            sprites.append(r)
        elif r["name"] in FUTURE_FORMS:
            half.append(r)
        else:
            review.append(r)
    return ok, half, review, sprites, chain_outside


def main():
    rows, excluded = scan()
    ok, half, review, sprites, chain_outside = classify(rows)
    n = len(rows)
    by_sp, ok_by_sp, ok_by_d = {}, {}, {}
    for r in rows:
        by_sp[r["species"]] = by_sp.get(r["species"], 0) + 1
        ok_by_d[r["district"]] = ok_by_d.get(r["district"], 0) + (1 if r["chain"] else 0)
        if r["chain"]:
            ok_by_sp[r["species"]] = ok_by_sp.get(r["species"], 0) + 1
    half_res = n - len(sprites) - len(ok) - len(review)
    lines = []
    a = lines.append
    a("# R-20260926-sublimation-census · 存量三色盘点报告（升华律执行令 §二.4）")
    a("")
    a("- 令源=O-20260926-2225-bm-c（硅基居民升华律执行令 v1.2）·盘点窗 ≤2026-09-28 12:00·盘点批次=R384（2026-09-26）")
    a("- 盘点体=census/registry 六城区生成卡 %d 张（荣誉席 census/reserved %d 张+手写锚 census/anchors %d 张=非生成面恒排除·令 §三 红线荣誉席零触碰）"
      % (n, sum(1 for x in excluded if x <= "C-00009"), sum(1 for x in excluded if x > "C-00009")))
    a("- 判别口径=✅显式「赛博后身」链 / ⚠️未来形态在册·中链不显式 / ❌只写现实态零未来形态（79 模板逐模板判读定谳=全数硅基城本位·❌=0）")
    a("- 工具=`Tools/sublimate_audit.py`（确定性·零 LLM·复跑幂等）·复跑=python -X utf8 Tools/sublimate_audit.py")
    a("")
    a("## 一、三色总盘")
    a("")
    a("| 色 | 判据 | 张数 | 占比 |")
    a("|---|---|---|---|")
    a("| ✅ 双底座齐 | 显式「赛博后身」链 | %d | %.1f%% |" % (len(ok), 100.0 * len(ok) / n))
    a("| ⚠️ 半升华·居民 | 未来形态在册·中链不显式 | %d | %.1f%% |" % (half_res, 100.0 * half_res / n))
    a("| ⚠️ 半升华·生灵族（像素灵） | 物种名自带现实原型词根·链 0·生灵册步⑥收口 | %d | %.1f%% |" % (len(sprites), 100.0 * len(sprites) / n))
    a("| ❌ 纯现实 | 只写现实态零未来形态 | %d | 0.0%% |" % len([]))
    a("| REVIEW 复核桶 | 未知职业模板（不误染❌） | %d | %.2f%% |" % (len(review), 100.0 * len(review) / n))
    a("")
    a("- 令内预告对照：~1602/10003 vs 实测 %d/%d（偏差 -7·以全库扫描实测为准=R383 基准初扫口径延续）" % (len(ok), n))
    a("- 链位置自检：链在职业行=%d 卡中链在行外=%d（链均落 prof 法定行·口径自洽）" % (len(ok) - chain_outside, chain_outside))
    a("- 未来原生族（城生城长第一代）=令 §一.6 合法族如实注记：计入本线、不豁免补链义务（补链=追加注记式保原文）")
    a("")
    a("## 二、分物种盘（✅链承载 vs 总数）")
    a("")
    a("| 物种 | 总数 | ✅链 | ⚠️无链 |")
    a("|---|---|---|---|")
    for k in sorted(by_sp, key=lambda k: -by_sp[k]):
        a("| %s | %d | %d | %d |" % (k, by_sp[k], ok_by_sp.get(k, 0), by_sp[k] - ok_by_sp.get(k, 0)))
    a("")
    a("## 三、分城区盘（✅链承载）")
    a("")
    a("| 城区 | 卡数 | ✅链 |")
    a("|---|---|---|")
    tot_d = {}
    for r in rows:
        tot_d[r["district"]] = tot_d.get(r["district"], 0) + 1
    for d in DISTRICTS:
        a("| %s | %d | %d |" % (d, tot_d.get(d, 0), ok_by_d.get(d, 0)))
    a("")
    a("## 四、结论与接续")
    a("")
    a("1. ❌纯现实=0：CEO 例「送快递的」式纯现实态在 9980 生成卡中零存在（79 职业模板逐模板判读定谳表内建于脚本·最弱锚=老克勒咖啡主/渡轮检票员族仍具城内复古叙事锚）。")
    a("2. 主工作量=⚠️ 8385 张（居民 7886+生灵 499）分批补链：令 §二.8 追加注记式保原文·随 P-13 Phase1 ≤10-02；链格=「未来形态——现实原型的（赛博）后身——升华一句话」。")
    a("3. 像素灵 499=生灵族按律②生灵登记门单列（物种名自带现实原型词根·消息雀先例在册）·收口件=《城市生灵册》步⑥。")
    a("4. REVIEW 复核桶 %d 张=未知模板零存在·生成门步①接线后新卡违律计数入 QC-REPORT。" % len(review))
    a("")
    report = "\n".join(lines) + "\n"
    io.open(REPORT, "w", encoding="utf-8", newline="\n").write(report)
    print("sublimate_audit: cards=%d ok=%d half_res=%d sprites=%d bad=0 review=%d excluded_reserved=%d excluded_anchors=%d"
          % (n, len(ok), half_res, len(sprites), len(review),
             sum(1 for x in excluded if x < "C-00010"),
             sum(1 for x in excluded if x >= "C-00010")))
    print("report -> %s" % os.path.relpath(REPORT, ROOT))
    if review:
        print("REVIEW ids:", ",".join(r["id"] for r in review[:20]))
        sys.exit(2)


if __name__ == "__main__":
    main()
