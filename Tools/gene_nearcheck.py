#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BigLife 基因轮近重预检常设件 v1.0 —— 近重候选清单器（T-20260927-01 分步②·rapidfuzz 开源采用落点件）

法源: T-20260927-01（P-2026-09-26-08 开源借力机制令·oss-harvest §五 落点强制·R416 切片 2 采用
rapidfuzz→本件=工作流变更落点）；分步① 阈值定谳=R417（数据锚定=阈值略高于各池自配对基线峰值）。
双层判据: Layer A=候选 4-gram 对基因库全文本池重叠扫描（跨池命中合法报——R417「自己退到后」跨池
判例·Layer A 扫全文本池非仅同型池）；Layer B=同型池 rapidfuzz fuzz.ratio 全串阈值层（高于池内
任意两条既有条目间最高相似度=统计离群=近重候选·THRESHOLDS cp92/ho95/tp44=R417 基线
91.667/94.118/43.902 定谳值）。
红线: 不替换既有禁触发词扫描面（SKILL 查二）与跨面撞句扫描（查三），只加近重候选层；史前近重对
零触碰只记档（基因库既有条目零字节改动）；预检纯确定性零 LLM。
用法: --file <候选清单>（每行 `type|text`·type∈cp/ho/tp）或 --candidate "type|text"（可多参）——
近重候选 exit 1=须换句再验；--baseline 三池自配对基线复核（漂移监控）；--qc 断言电池。
"""
import io, os, sys, json, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
GENES = os.path.join(CO, "genes")

# 同型池注册表（type -> (池键, Layer B 阈值)·阈值=R417 分步①定谳·再定谳走 CODEX §十二 T2）
TYPE_POOLS = {
    "cp": ("language.catchphrases", 92.0),
    "ho": ("lives.hook_objects", 95.0),
    "tp": ("lives.turning_points", 44.0),
}


def load_pools():
    """全文本池装载：genes/language.json+lives.json 全部文本池（Layer A 扫描面）。

    dict 条目=text 面（catchphrases {text,axis}）或词面展开（dialects {name,words,note}）；
    households 等结构面 dict 无文本面不入扫描。键排序保确定性。
    """
    pools = {}
    for fname in ("language.json", "lives.json"):
        data = json.load(io.open(os.path.join(GENES, fname), encoding="utf-8"))
        for key in sorted(data.keys()):
            val = data[key]
            if not isinstance(val, list):
                continue
            texts = []
            for e in val:
                if isinstance(e, dict):
                    if "text" in e:
                        texts.append(e["text"])
                    elif "words" in e:
                        texts.extend(str(w) for w in e["words"])
                else:
                    texts.append(str(e))
            if texts:
                pools[f"{fname[:-5]}.{key}"] = texts
    return pools


def grams4(text):
    """候选 4-gram 滑窗序列（<4 字返空——短条目天然不入 Layer A）。"""
    return [text[i:i + 4] for i in range(len(text) - 3)] if len(text) >= 4 else []


def layer_a(candidate, pools):
    """Layer A：候选 4-gram 对全文本池逐池重叠扫描。返回命中行（池序=键序·条目序=池内序）。"""
    hits = []
    for pool_key in sorted(pools.keys()):
        for idx, entry in enumerate(pools[pool_key]):
            matched = [g for g in grams4(candidate) if g in entry]
            if matched:
                hits.append({"pool": pool_key, "idx": idx, "entry": entry, "grams": matched})
    return hits


def layer_b(candidate, pool_texts, threshold, top=3):
    """Layer B：同型池 rapidfuzz fuzz.ratio 全串阈值层（统计离群=近重候选）。纯 C++ 同输入同输出。"""
    try:
        from rapidfuzz import process, fuzz
    except ImportError:
        print("ERROR rapidfuzz 未安装（T-16 切片 2 依赖·pip install rapidfuzz）", file=sys.stderr)
        sys.exit(3)
    res = process.extract(candidate, pool_texts, scorer=fuzz.ratio, limit=top)
    best_ratio = round(res[0][1], 3) if res else 0.0
    return {"threshold": threshold, "best_ratio": best_ratio,
            "top": [{"entry": e, "ratio": round(r, 3)} for e, r, _ in res],
            "flagged": bool(res) and res[0][1] >= threshold}


def check_candidates(cands, pools):
    """候选清单全检：[{type,text}] -> 报告（flag=Layer A ∪ Layer B 任一命中）。"""
    report = []
    for typ, text in cands:
        if typ not in TYPE_POOLS:
            report.append({"type": typ, "text": text, "error": "unknown-type"})
            continue
        a = layer_a(text, pools)
        b = layer_b(text, pools[TYPE_POOLS[typ][0]], TYPE_POOLS[typ][1])
        report.append({"type": typ, "text": text, "layerA_hits": a, "layerB": b,
                       "flag": bool(a) or b["flagged"]})
    return report


def parse_candidate_line(line):
    """`type|text` -> (type,text)；格式违例 -> (None,raw)。"""
    if "|" not in line:
        return None, line
    typ, text = line.split("|", 1)
    return typ.strip(), text.strip()


def baseline(pools):
    """三注册池自配对全量基线（史前近重对零触碰只记档·判据=max<T 成立才有效）。"""
    out = {}
    for typ in sorted(TYPE_POOLS):
        pool_key, threshold = TYPE_POOLS[typ]
        entries = pools[pool_key]
        best, pair = 0.0, None
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                from rapidfuzz import fuzz
                r = fuzz.ratio(entries[i], entries[j])
                if r > best:
                    best, pair = r, (entries[i], entries[j])
        out[typ] = {"pool": pool_key, "n": len(entries), "max_ratio": round(best, 3),
                    "top_pair": list(pair) if pair else [], "threshold": threshold,
                    "criterion_ok": best < threshold}
    return out


def qc():
    ok = [0, 0]

    def check(name, cond):
        ok[0 if cond else 1] += 1
        print(f"{'PASS' if cond else 'FAIL'} {name}")

    pools = load_pools()
    # 1) 4-gram 滑窗正确性
    check("gram-extract", grams4("旧钥匙开新门") == ["旧钥匙开", "钥匙开新", "匙开新门"]
          and grams4("三字") == [])
    # 2) Layer A 夹具命中/零命中/跨池（合成池·不依赖真实库）
    fx = {"fixture.a": ["旧钥匙开了三十年的锁"], "fixture.b": ["帮人帮到底，送佛送到西。"]}
    check("layerA-fixture-hit", len(layer_a("旧钥匙开新门", fx)) == 1
          and layer_a("旧钥匙开新门", fx)[0]["pool"] == "fixture.a")
    check("layerA-fixture-miss", layer_a("铜壶嘴里的白汽把冬天烫出一个洞", fx) == [])
    check("layerA-cross-pool", layer_a("今天也想帮人帮到底", fx)[0]["pool"] == "fixture.b")
    # 3) Layer A 真实库判例锚（R406/R413/R417 拦实录·史前池内子串逐字在位）
    hit_cp = layer_a("规矩立在先", pools)
    check("layerA-real-R413", any(h["pool"] == "language.catchphrases" for h in hit_cp))
    check("layerA-real-R406", any(h["pool"] == "language.catchphrases"
                                  for h in layer_a("帮人帮到底", pools)))
    check("layerA-real-crosspool", any(h["pool"] == "lives.presents"
                                       for h in layer_a("自己退到后", pools)))
    # 4) Layer B 边界判例（池外新句与史前近重对成员 ratio 91.667<T=92 不触发 B·Layer A 兜住）
    rep = check_candidates([("cp", "热汤进肚，啥事都好商量。")], pools)[0]
    check("layerB-historic-boundary", rep["layerB"]["best_ratio"] == 91.667
          and not rep["layerB"]["flagged"] and bool(rep["layerA_hits"]) and rep["flag"])
    # 5) Layer B 精确重复候选（=既有条目·ratio 100 必拦）
    cp0 = pools["language.catchphrases"][0]
    rep2 = check_candidates([("cp", cp0)], pools)[0]
    check("layerB-exact-dup", rep2["layerB"]["best_ratio"] == 100.0 and rep2["flag"])
    # 6) 未注册 type=报错行不崩
    rep3 = check_candidates([("xx", "随便一句")], pools)[0]
    check("unknown-type-reject", "error" in rep3 and rep3["error"] == "unknown-type")
    # 7) 基线判据成立（阈值仍高于池内自配对峰值=注册判据在效·漂移监控）
    base = baseline(pools)
    check("baseline-criterion", all(v["criterion_ok"] for v in base.values()))
    # 8) 史前近重对哨兵（cp 91.667/ho 94.118/tp 43.902 三峰值在位=既有条目零触碰在证）
    check("baseline-sentinel", base["cp"]["max_ratio"] == 91.667
          and base["ho"]["max_ratio"] == 94.118 and base["tp"]["max_ratio"] == 43.902)
    # 9) 行解析：type|text 切分+违例行检出
    check("parse-line", parse_candidate_line("cp| 慢慢来 ") == ("cp", "慢慢来")
          and parse_candidate_line("无竖线行")[0] is None)
    # 10) 同输入双跑一致（真库全检·rapidfuzz 纯 C++ 同输入同输出）
    cands = [("cp", "规矩立在先"), ("tp", "自己退到后")]
    r1 = json.dumps(check_candidates(cands, pools), ensure_ascii=False)
    r2 = json.dumps(check_candidates(cands, pools), ensure_ascii=False)
    check("double-run", r1 == r2)
    # 11) 候选清单文件回路（临时件跑后即删）
    tmp = os.path.join(tempfile.gettempdir(), "gene_nearcheck_qc.txt")
    io.open(tmp, "w", encoding="utf-8", newline="\n").write("# 注释行\ncp|规矩立在先\n\nho|电波猫\n")
    parsed = [parse_candidate_line(l.strip()) for l in
              io.open(tmp, encoding="utf-8").read().splitlines()
              if l.strip() and not l.strip().startswith("#")]
    os.remove(tmp)
    check("file-roundtrip", parsed == [("cp", "规矩立在先"), ("ho", "电波猫")])
    print(f"== gene_nearcheck --qc: {ok[0]} PASS, {ok[1]} FAIL ==")
    return ok[1] == 0


def main():
    args = sys.argv[1:]
    if "--qc" in args:
        sys.exit(0 if qc() else 1)
    if "--baseline" in args:
        pools = load_pools()
        base = baseline(pools)
        print(json.dumps(base, ensure_ascii=False, indent=1))
        sys.exit(0 if all(v["criterion_ok"] for v in base.values()) else 1)
    cands, mode = [], None
    i = 0
    while i < len(args):
        if args[i] == "--file" and i + 1 < len(args):
            mode = "file"
            for line in io.open(args[i + 1], encoding="utf-8-sig").read().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    cands.append(parse_candidate_line(line))
            i += 2
        elif args[i] == "--candidate" and i + 1 < len(args):
            mode = "cand"
            cands.append(parse_candidate_line(args[i + 1]))
            i += 2
        else:
            i += 1
    if not cands:
        print(__doc__)
        sys.exit(2 if mode else 0)
    pools = load_pools()
    bad = [c for c in cands if c[0] is None or c[0] not in TYPE_POOLS]
    if bad:
        print(f"ERROR 候选行格式/类型违例（须 `type|text`·type∈{'/'.join(TYPE_POOLS)}）: {bad}",
              file=sys.stderr)
        sys.exit(2)
    report = check_candidates(cands, pools)
    flags = 0
    for r in report:
        mark = "FLAG" if r["flag"] else "CLEAN"
        line_out = f"[{mark}] {r['type']}|{r['text']}"
        if r["flag"]:
            flags += 1
            for h in r["layerA_hits"]:
                line_out += f"\n    A: {h['pool']}[{h['idx']}] {h['grams']} ⊂ {h['entry']}"
            if r["layerB"]["flagged"]:
                t = r["layerB"]["top"][0]
                line_out += f"\n    B: ratio {t['ratio']} ≥ T{r['layerB']['threshold']:.0f} vs {t['entry']}"
        print(line_out)
    print(f"== gene_nearcheck: {len(report)} 候选, {flags} 近重候选 ==")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
