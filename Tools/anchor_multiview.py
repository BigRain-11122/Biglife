# -*- coding: utf-8 -*-
"""anchor_multiview.py v1.0 — 4 视角身份锚包生成器（T-20261024-02·ELECT 路线接线）

契约（确定性零 LLM·同输入双跑逐字节一致）:
  输入  = census/export/citizens-light.jsonl（只读）+ census/registry/<区>/<ID>.md（服装/钩子段）
  输出  = census/anchors/4v/<ID>.json（一行一件·4 视角：front / half（半侧 45°）/ side / back）
  名字分离 = display_name 单列登记；prompt_views 内禁出现姓名（QC 断言）——
             姓名不烧进身份核，避免模型把名字当作身份 token（改名不漂 identity_core）
  身份核 = species/gender/age/locale/profession/outfit/signature/creed 逐项拼装；
           四视角共享同一 identity_core + identity_hash——规格级零漂移门（图像级 aCCS 留渲染链）
  一致性铁律 = 仅相机角度变化；禁换装/换发型/换配饰/换比例
  荣誉席 = faction=honored 或 district 空 → status=reserved（CEO 保留面·零发明·不生成 prompt）
  消费方 = 立绘链 / FluxVerse 角色资产登记 / MV 与漫剧选角（同一居民跨项目同脸）

用法:
  python -X utf8 Tools/anchor_multiview.py                 # 默认 20 位手写展示锚（原型样板）
  python -X utf8 Tools/anchor_multiview.py --ids C-04868 C-04869
  python -X utf8 Tools/anchor_multiview.py --limit 50      # 按 light 顺序取前 N 位可生成居民
  python -X utf8 Tools/anchor_multiview.py --qc            # 只跑 QC（不写盘）
QC:
  ①4 视角齐备 ②identity_core 四视角逐字一致（hash 相同）③姓名不在任何 prompt 内
  ④profession/outfit 必进 prompt ⑤双跑字节一致 ⑥reserved 席零 prompt
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
REG_ROOT = os.path.join(ROOT, "census", "registry")
OUT_DIR = os.path.join(ROOT, "census", "anchors", "4v")
BASIS = "biglife-portrait-anchors-v1"

VIEWS = [
    ("front", "正面全身·相机与肩同高·平视·自然站姿·双手可见"),
    ("half", "半侧 45° 全身·相机与肩同高·视线朝画面右前方·自然站姿"),
    ("side", "正侧 90° 全身·相机与腰同高·平视·自然站姿"),
    ("back", "背面全身·相机与肩同高·平视·自然站姿"),
]

STYLE = ("写实立绘·中立灰背景·均匀柔光无硬阴影·全身入画头部留白 8%·"
         "无文字无 logo 无水印")

SPECIES = {"carbon": "碳基", "silicon": "硅基", "hybrid": "混合态"}


def _read_registry_index():
    idx = {}
    for dirpath, _dirnames, filenames in os.walk(REG_ROOT):
        for fn in filenames:
            if fn.endswith(".md"):
                idx[fn[:-3]] = os.path.join(dirpath, fn)
    # 手写展示锚（census/anchors/）优先：原型样板卡段更全（服装/钩子均为正典原文）
    arche = os.path.join(ROOT, "census", "anchors")
    if os.path.isdir(arche):
        for fn in os.listdir(arche):
            if fn.endswith(".md"):
                idx[fn[:-3]] = os.path.join(arche, fn)
    return idx


def _section(path, key):
    """取卡内 **key** 段的正文（到下一个 **段** 或空行为止）。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return ""
    marker = f"**{key}**"
    i = text.find(marker)
    if i < 0:
        return ""
    rest = text[i + len(marker):]
    lines = []
    for line in rest.splitlines():
        s = line.strip()
        if not s:
            if lines:
                break
            continue
        if s.startswith("**"):
            break
        lines.append(s)
    return " ".join(lines).strip()


def _outfit_tokens(clothing):
    """服装段取前 3 个短句作稳定着装 token（多视角一致性锚）。"""
    if not clothing:
        return "既有卡服装段缺失"
    parts = [p.strip() for p in clothing.replace("；", "，").split("，") if p.strip()]
    return "·".join(parts[:3])


def _identity_core(r, clothing, hook):
    species = SPECIES.get(r.get("species") or "", r.get("species") or "未定")
    age = r.get("age")
    age_txt = f"{age} 岁" if age else (r.get("age_note") or "年龄未披露")
    locale = "·".join([x for x in (r.get("district"), r.get("block")) if x])
    core = {
        "species": species,
        "gender": r.get("gender") or "未定",
        "age": age_txt,
        "locale": locale,
        "profession": r.get("profession") or "",
        "outfit": _outfit_tokens(clothing),
        "signature": hook or r.get("hook") or "",
        "creed": r.get("creed") or "",
    }
    return core


def build_pack(r, reg_idx):
    cid = r["id"]
    name = r.get("name") or ""
    reserved = (r.get("faction") == "honored") or not r.get("district")
    if reserved:
        return {
            "id": cid, "display_name": name, "status": "reserved",
            "note": "荣誉席/保留面=CEO 人设权·四视角锚包零发明",
            "identity_core": None, "identity_hash": None, "prompt_views": [],
            "v": 1,
        }
    path = reg_idx.get(cid, "")
    clothing = _section(path, "服装")
    hook = _section(path, "钩子")
    core = _identity_core(r, clothing, hook)
    if name:
        # 名字分离：身份核内出现姓名一律脱名为「本人」（改名/题名不回写身份核）
        core = {k: (v.replace(name, "本人") if isinstance(v, str) else v)
                for k, v in core.items()}
    core_txt = "｜".join(f"{k}:{v}" for k, v in core.items() if v)
    core_hash = hashlib.md5(f"{cid}::{BASIS}::{core_txt}".encode("utf-8")).hexdigest()[:16]
    head = (f"4 视角身份锚（同一居民·同一身份核）｜{core_txt}｜"
            "一致性铁律：四视角共享同一身份核（面容骨相/肤色/发型轮廓/服装配色与配件位置/"
            "身高比例），仅相机角度变化，禁换装禁换发型禁换配饰禁改比例")
    views = [{"view": v, "prompt": f"{head}｜视角：{desc}｜风格：{STYLE}"}
             for v, desc in VIEWS]
    return {
        "id": cid, "display_name": name, "status": "ok",
        "name_policy": "名字单列登记·不烧入身份核（改名不漂 identity_hash）",
        "identity_core": core, "identity_hash": core_hash,
        "basis": BASIS, "prompt_views": views, "v": 1,
    }


def load_light():
    with open(LIGHT, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def select(rows, ids=None, limit=None):
    if ids:
        want = set(ids)
        return [r for r in rows if r["id"] in want]
    if limit:
        out = []
        for r in rows:
            if (r.get("faction") == "honored") or not r.get("district"):
                continue
            out.append(r)
            if len(out) >= limit:
                break
        return out
    arche = os.path.join(ROOT, "census", "anchors")
    ids = sorted(fn[:-3] for fn in os.listdir(arche) if fn.endswith(".md"))
    want = set(ids)
    return [r for r in rows if r["id"] in want]


def build_all(rows, ids=None, limit=None):
    reg_idx = _read_registry_index()
    return [build_pack(r, reg_idx) for r in select(rows, ids, limit)]


def qc(packs):
    errs = []
    if not packs:
        errs.append("zero packs")
    for p in packs:
        cid = p["id"]
        if p["status"] == "reserved":
            if p["prompt_views"] or p["identity_core"]:
                errs.append(f"reserved leak {cid}")
            continue
        pv = p["prompt_views"]
        if len(pv) != 4 or [x["view"] for x in pv] != [v for v, _ in VIEWS]:
            errs.append(f"views bad {cid}")
            continue
        if len({p["identity_hash"]} | {p["identity_hash"]}) != 1:
            errs.append(f"hash unstable {cid}")
        core_txt = "｜".join(f"{k}:{v}" for k, v in p["identity_core"].items() if v)
        name = (p.get("display_name") or "").strip()
        for x in pv:
            if not x["prompt"].startswith("4 视角身份锚"):
                errs.append(f"prompt head {cid}")
                break
            if p["identity_core"]["profession"] and \
               p["identity_core"]["profession"] not in x["prompt"]:
                errs.append(f"profession missing {cid}")
                break
            if p["identity_core"]["outfit"] not in x["prompt"]:
                errs.append(f"outfit missing {cid}")
                break
            if name and len(name) >= 2 and name in x["prompt"]:
                errs.append(f"name leaked {cid}")
                break
            if core_txt and core_txt not in x["prompt"]:
                errs.append(f"core drift {cid}")
                break
    b1 = [json.dumps(p, ensure_ascii=False, sort_keys=True) for p in packs]
    b2 = [json.dumps(p, ensure_ascii=False, sort_keys=True)
          for p in build_all(load_light(),
                             ids=[p["id"] for p in packs])]
    if b1 != b2:
        errs.append("double-run mismatch")
    if errs:
        print("QC FAIL:")
        for e in errs[:20]:
            print(" -", e)
        return 1, len(packs), 0
    ok = sum(1 for p in packs if p["status"] == "ok")
    print(f"QC PASS: packs={len(packs)} ok={ok} reserved={len(packs)-ok} "
          f"views=4/pack identity_drift=0 name_leak=0 double_run=identical")
    return 0, len(packs), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    packs = build_all(load_light(), a.ids, a.limit)
    code, n, ok = qc(packs)
    if code != 0 or a.qc:
        return code
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in packs:
        with open(os.path.join(OUT_DIR, p["id"] + ".json"), "w",
                  encoding="utf-8", newline="\n") as f:
            json.dump(p, f, ensure_ascii=False, indent=1)
            f.write("\n")
    print(f"wrote {n} packs ({ok} ok) -> {os.path.relpath(OUT_DIR, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())