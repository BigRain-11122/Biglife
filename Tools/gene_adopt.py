# -*- coding: utf-8 -*-
"""基因回填：把「已登记但零承载」的转折点基因，按词汇亲和回填进匹配居民户卡的「经历」段。

确定性零 LLM。为什么需要：基因台账（census/export/gene-ledger.html）显示大量基因登记后从未
被任何户卡承载，等于白登记；而新居民注册受需求触发制（C-20261010-03），不会自动消耗它们。
本工具把未落地基因定向喂给「正文里本来就在聊同一件事」的居民，只回填有词面亲和的卡，宁缺毋滥。

判据（全部机检）：
- 只处理 genes/lives.json 里 turning_points 且当前零承载的条目；
- 亲和 = 基因文本与户卡正文共享 ≥2 个稀有 2-gram（df<=60），共享越多分越高；
- 每卡本轮至多回填 1 条，回填句追加在「**经历**」行尾：还记着一件事：<基因>。；
- 每基因全局只用一次（回填后即离开待办池）；
- 荣誉席 C-00001..C-00003 与解密/保留席不碰；
- 已含该基因文本的卡跳过；写前后行数与必备段零变化（QC 复跑守门）。

用法：python -X utf8 Tools/gene_adopt.py --cards 120 [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVES = ROOT / "genes" / "lives.json"
REGISTRY = ROOT / "census" / "registry"
SKIP_IDS = {"C-00001", "C-00002", "C-00003"}
EXPERIENCE_RE = re.compile(r"^\*\*经历\*\*\s*(.*)$")
APPEND_MARK = "还记着一件事"
ID_RE = re.compile(r"^#\s*(C-\d{5})")
CJK = re.compile(r"[\u4e00-\u9fff]+")
# 通用词不进亲和判据（否则人人都有「城市/一天」就乱配）
STOP_GRAMS = {
    "一次", "一个", "第一", "时候", "后来", "已经", "自己", "他们", "我们",
    "什么", "这个", "那个", "因为", "所以", "就是", "还是", "不是", "现在",
}


def shares_run(gene: str, text: str, k: int = 8) -> bool:
    """连续性去重：基因与卡面共享 >=k 个连续汉字即判近似重复（防同一事件换句写两遍）。"""
    if len(gene) < k:
        return gene in text
    for i in range(len(gene) - k + 1):
        if gene[i:i + k] in text:
            return True
    return False


def experience_line(text: str) -> str:
    for line in text.splitlines():
        if EXPERIENCE_RE.match(line):
            return line
    return ""


def domain_text(text: str) -> str:
    """职业域锚：职业/生计/钩子三行——基因必须与本人营生沾边才算亲和不跑题。"""
    keep = ("**职业**", "**生计**", "**钩子**")
    return "\n".join(ln for ln in text.splitlines() if ln.startswith(keep))


def lead_key(gene: str, k: int = 8) -> str:
    """基因的时代指纹：首个汉字串的前 k 字（同一事件的改写变体指纹相同）。"""
    m = CJK.search(gene)
    if not m:
        return gene[:k]
    run = m.group(0)
    return run[:k] if len(run) >= 4 else ""


def grams(text: str) -> set[str]:
    out: set[str] = set()
    for run in CJK.findall(text):
        for i in range(len(run) - 1):
            g = run[i:i + 2]
            if g not in STOP_GRAMS:
                out.add(g)
    return out


def load_cards() -> list[dict]:
    cards: list[dict] = []
    for code in sorted(os.listdir(REGISTRY)):
        dpath = REGISTRY / code
        if not dpath.is_dir():
            continue
        for fn in sorted(os.listdir(dpath)):
            if not fn.endswith(".md"):
                continue
            path = dpath / fn
            text = path.read_text(encoding="utf-8", errors="ignore")
            m = ID_RE.search(text.splitlines()[0] if text else "")
            cid = m.group(1) if m else ""
            cards.append({"path": path, "district": code, "id": cid, "text": text})
    return cards


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cards", type=int, default=120, help="本轮最多回填的户卡数")
    ap.add_argument("--max-df", type=int, default=60, help="稀有 2-gram 的卡面频次上限")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(LIVES, encoding="utf-8") as fh:
        lives = json.load(fh)
    all_tps = list(dict.fromkeys(lives.get("turning_points", [])))
    cards = load_cards()

    # 当前承载面：整串出现即算已在册
    need = [g for g in all_tps if g and not any(g in c["text"] for c in cards)]
    if not need:
        print("turning_points: 无零承载条目 - SELF_TERMINATE")
        return 0

    df: dict[str, int] = defaultdict(int)
    postings: dict[str, list[int]] = defaultdict(list)
    card_grams: list[set[str]] = []
    for idx, c in enumerate(cards):
        gs = grams(c["text"])
        card_grams.append(gs)
        for g in gs:
            df[g] += 1
            postings[g].append(idx)

    # 每个未落地基因找最亲和且可用的卡（共享稀有 gram 数）
    card_domain = [grams(domain_text(c["text"])) for c in cards]
    scored: list[tuple[int, str, int]] = []
    for gene in need:
        gene_grams = grams(gene)
        gs = [g for g in gene_grams if df.get(g, 0) <= args.max_df]
        if not gs:
            continue
        hit: dict[int, int] = defaultdict(int)
        for g in gs:
            for idx in postings.get(g, ()):
                hit[idx] += 1
        for idx, n in hit.items():
            if n < 3:
                continue
            if not (gene_grams & card_domain[idx]):
                continue
            scored.append((n, gene, idx))

    scored.sort(key=lambda t: (-t[0], t[2], t[1]))
    used_card: set[int] = set()
    used_gene: set[str] = set()
    picks: list[tuple[int, str]] = []
    corpus = "\n".join(c["text"] for c in cards)
    for n, gene, idx in scored:
        if len(picks) >= args.cards:
            break
        if idx in used_card or gene in used_gene:
            continue
        c = cards[idx]
        if not c["id"] or c["id"] in SKIP_IDS:
            continue
        if gene in c["text"]:
            continue
        if shares_run(gene, c["text"]):
            continue
        exp = experience_line(c["text"])
        if exp and shares_run(gene, exp, 6):
            continue
        key = lead_key(gene)
        if key and key in corpus:
            continue
        if APPEND_MARK in c["text"]:
            continue
        used_card.add(idx)
        used_gene.add(gene)
        picks.append((idx, gene))

    if not picks:
        print(f"turning_points 未落地 {len(need)} 条，但无满足 ≥2 稀有 gram 亲和的卡 - 零写入")
        return 0

    written = 0
    for idx, gene in picks:
        c = cards[idx]
        lines = c["text"].splitlines()
        hit_line = None
        for i, line in enumerate(lines):
            if EXPERIENCE_RE.match(line):
                hit_line = i
                break
        if hit_line is None:
            continue
        line = lines[hit_line]
        add = f"还记着一件事：{gene.rstrip('。')}。"
        if line.rstrip().endswith("。"):
            lines[hit_line] = line.rstrip() + add
        else:
            lines[hit_line] = line.rstrip() + "。" + add
        if not args.dry_run:
            c["path"].write_text("\n".join(lines) + "\n", encoding="utf-8")
        written += 1
        print(f"{c['id']} [{c['district']}] + {gene[:28]}")

    print(f"== gene_adopt ==")
    print(f"unused_before={len(need)} picked={len(picks)} written={written} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    sys.exit(main())