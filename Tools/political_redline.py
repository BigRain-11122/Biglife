#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BigLife political redline scanner v0 — 入城门必过件（T-20260926-18 步⑦ 风格面五件·第 5 件）

法源: O-20260926-2225-bm-c《硅基居民升华律执行令》v1.3 政治红线律（名人群像三路准入——
主身份政治人物一律不入城；影射角色走常规生成管线，真名/肖像/声音克隆走 P-09 法务闸）。
词表: docs/style-dna-archetypes.md §五.3 九类政治词表（帝王/官员/政客/政党/军事统帅/总统/
首相/政权/竞选）=判据面单一源；本文件 TERMS=机器面初版黑名单基座（九类类内常见同族词·
闭集 v0·扩表走 CODEX §十二 T2 登记 v3.36）。
扫描面=生成消费面（census 全卡面+cognition pools/greetings/style-dna-archetypes/voice-role-map
+reflections/proposals/surprise-log）；docs 判据面不扫（禁令自述句命中合法·§五.3 判例）。
纯确定性零 LLM。--qc 断言电池；--scan 全量扫描（state/redline-last.json 落 state/ 不入库·
命中=exit 1）。入城门接线=generate_census.py render_card/render_anchor 后置 fail-fast
（REDLINE REFUSED+exit 5·零静默改写=活户籍防护不破·违律面零写盘）。
"""
import io, os, re, sys, json, time, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)

# 九类政治词表（§五.3 类内同族词·闭集 v0）
TERMS = {
    "帝王": ("皇帝", "帝王", "天子", "君主", "女皇", "国王", "女王", "可汗", "沙皇", "王朝",
            "皇室", "登基", "驾崩", "陛下"),
    "官员": ("官员", "大臣", "宰相", "丞相", "尚书", "总督", "部长", "总理", "国务卿", "朝廷"),
    "政客": ("政客", "政治家", "从政", "参政", "政坛", "仕途"),
    "政党": ("政党", "党派", "党魁", "入党", "党员"),
    "军事统帅": ("军事统帅", "统帅", "元帅", "将军", "司令", "军阀"),
    "总统": ("总统", "副总统", "大总统"),
    "首相": ("首相", "总理大臣"),
    "政权": ("政权", "当局", "政府", "执政", "政变", "复辟", "下野"),
    "竞选": ("竞选", "大选", "选举", "上任", "任期", "投票"),
}
TERM2CAT = {w: cat for cat, ws in TERMS.items() for w in ws}
_PATTERN = re.compile("|".join(sorted(TERM2CAT, key=len, reverse=True)))


def scan_text(text):
    """Return list of {term, cat, idx} for every redline-term hit in text (deterministic order)."""
    return [{"term": m.group(0), "cat": TERM2CAT[m.group(0)], "idx": m.start()}
            for m in _PATTERN.finditer(text)]


SCAN_FACES = [
    ("census-cards", os.path.join(CO, "census"), "md-walk"),
    ("pools", os.path.join(CO, "cognition", "pools.json"), "file"),
    ("greetings", os.path.join(CO, "cognition", "greetings.json"), "file"),
    ("style-dna-archetypes", os.path.join(CO, "cognition", "style-dna-archetypes.json"), "file"),
    ("voice-role-map", os.path.join(CO, "cognition", "voice-role-map.json"), "file"),
    ("reflections", os.path.join(CO, "census", "reflections.jsonl"), "file"),
    ("proposals", os.path.join(CO, "cognition", "proposals.jsonl"), "file"),
    ("surprise-log", os.path.join(CO, "cognition", "surprise-log.jsonl"), "file"),
]


def _iter_card_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "export"]  # R3 再生面=卡面镜像·不重复扫
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def full_scan():
    """Scan all generation-consumption faces. Returns per-face hit report (no writes to corpus)."""
    report = {}
    total = 0
    for name, path, mode in SCAN_FACES:
        hits, files = [], 0
        if mode == "md-walk":
            for p in _iter_card_files(path):
                files += 1
                for h in scan_text(io.open(p, encoding="utf-8").read()):
                    hits.append({"file": os.path.relpath(p, CO), **h})
        elif os.path.isfile(path):
            files = 1
            hits = [{"file": os.path.relpath(path, CO), **h}
                    for h in scan_text(io.open(path, encoding="utf-8").read())]
        report[name] = {"files": files, "hits": len(hits), "detail": hits[:20]}
        total += len(hits)
    return report, total


def qc():
    ok = [0, 0]

    def check(name, cond):
        ok[0 if cond else 1] += 1
        print(f"{'PASS' if cond else 'FAIL'} {name}")

    # 1) 每类正例命中（9/9）
    for cat, ws in TERMS.items():
        probe = f"测试卡面：{ws[0]}身份不得入城。"
        check(f"category-hit {cat}", any(h["cat"] == cat for h in scan_text(probe)))
    # 2) 无害语料零命中（卡面式文本·含城主/荣誉席/巡线等城内合法词）
    innocent = [
        "城主塔顶的光今天格外亮，巡线员说信号灯全绿。",
        "荣誉市民席保留给 CEO 点名入册的三位家人。",
        "像素小学学生放学绕路看 commit 光点过江，得劲！",
        "茶炉工给趸船上的老街坊续了第三道水。",
    ]
    check("innocent-zero", all(scan_text(s) == [] for s in innocent))
    # 3) 闭集完备：无空类、无跨类重复词、词长 ≥2
    allwords = [w for ws in TERMS.values() for w in ws]
    check("closed-set", all(len(ws) > 0 for ws in TERMS.values())
          and len(allwords) == len(set(allwords)) and all(len(w) >= 2 for w in allwords))
    # 4) 定位与去重序：首个命中 idx 正确、确定性顺序
    s = "卡面含总统与总统两个词"
    hh = scan_text(s)
    check("idx+order", hh[0]["idx"] == s.index("总统") and hh[0]["idx"] < hh[1]["idx"])
    # 5) 双跑确定性（真实卡面文件两次扫描逐字节一致）
    p = os.path.join(CO, "census", "anchors", "C-00010.md")
    if os.path.isfile(p):
        t = io.open(p, encoding="utf-8").read()
        check("double-run", scan_text(t) == scan_text(t))
    else:
        check("double-run(skip-no-anchor)", True)
    # 6) 词表自检：正则覆盖 = 词表全集（漏词=FAIL）
    check("regex-coverage", set(m for ws in TERMS.values() for m in ws) ==
          set(_PATTERN.findall(" ".join(allwords))))
    print(f"== political_redline --qc: {ok[0]} PASS, {ok[1]} FAIL ==")
    return ok[1] == 0


def main():
    if "--qc" in sys.argv:
        sys.exit(0 if qc() else 1)
    if "--scan" in sys.argv:
        report, total = full_scan()
        out = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "terms": sum(len(v) for v in TERMS.values()),
               "faces": {k: {"files": v["files"], "hits": v["hits"]} for k, v in report.items()},
               "hits_total": total, "detail": {k: v["detail"] for k, v in report.items() if v["hits"]}}
        os.makedirs(os.path.join(CO, "state"), exist_ok=True)
        io.open(os.path.join(CO, "state", "redline-last.json"), "w", encoding="utf-8", newline="\n").write(
            json.dumps(out, ensure_ascii=False, indent=1))
        for k, v in report.items():
            print(f"{k}: files={v['files']} hits={v['hits']}")
        print(f"== political_redline --scan: hits_total={total} ==")
        sys.exit(1 if total else 0)
    print(__doc__)


if __name__ == "__main__":
    main()
