# -*- coding: utf-8 -*-
"""citizen_assembly.py v1.0 — census polygon 角色装配映射表生成器
（O-2026-0929-020 居民形象职能定谳令·BigLife 总责 polygon 角色装配+换装·T-20260929-06 step④）

契约（R3 再生面·gitignored·确定性零 LLM）:
  输入  = census/export/citizens-light.jsonl（只读·census 冻结面零触碰）
          + census/export/citizen-atlas.jsonl（调色单源·五 hex 数据行制 v2.4 零改动·只读引用）
  输出  = census/export/citizen-assembly.jsonl（一行一居民=N 居民=N 确定性形象档案·O-020 ①③）
  派生  = md5(id::biglife-assembly-v1) 确定性 seed——同居民永远同外观（禁随机人模·同输入双跑字节一致）
  匹配律（O-020 ③ census 匹配律·三层）:
    族源三分 = carbon→碳源（琥珀 LED 眼·生活暖装系）/ silicon→硅源（电光青 LED 眼·机房冷灰+电路纹
               ·AD-018 赛博变体恒配）/ sprite+artifact-spirit+memory-spirit+imagery-spirit→城源
               （城市自生·惯例琥珀·谱系形态《灵族志》）
    年龄→体型与儿童件 = band() 镜像 behavior.py L265 同源阈值（child≤17/young≤25/mid<60/elder·
               非整数年龄→mid）——child 档恒配 AD-024 儿童池部件·adult 档零儿童件
    性格身份→服装风格 = 思想六轴 axis→风格闭集（烟火→生活暖装/秩序→规整通勤/求新→新潮尝鲜/
               怀旧→旧料怀旧/侠气→硬朗工装/逍遥→轻便闲逸/null→中性常服）·硅源族系特征优先于个性
  装配管线（O-020 ②）= AD-042 基模（19 件在册·seeded 取件 0..18）+ AD-011 换装料库（722 件在册·
               seeded 取件 0..721）+ AD-024 儿童池（件数未入册=seeded rank 按库实际件数取模投影·
               对账窗入册后锁值）+ AD-018 赛博变体（同 rank 律·硅源恒配）
  换装  = 数据驱动投影律（O-020 ④·职业/季节/事件→外观更新）——本面=静态形象档案事实源，
          引擎照投影律消费（BigLife=事实源不变·CODEX §七.3 材质映射/atlas 五 hex 单源律延续）
  调色  = atlas v2.4 五 hex（skin/hair/cloth/eye/badge）逐位镜像入行（palette.src 指针在行）——
          atlas 缺席席（CEO 入城批 C-10010~36 共 27 席）= palette null+如实注记（零发明·待 atlas 扩行窗）
  荣誉席 = C-00001~03（faction=honored）= CEO 保留面：status=reserved·assembly 零代创
          （化身样式=CEO 一句话拍板·CODEX §十/§七.3 批 2 出库闸维持）
  消费方 = City3D polygon 角色装配/FluxVerse R0-R6（O-020 BigLife 总责·投影律消费）
  T2    = CODEX §十二 v3.56（消费方通知走 T-20260923-01 字段变更程序族）
"""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIGHT = os.path.join(ROOT, "census", "export", "citizens-light.jsonl")
ATLAS = os.path.join(ROOT, "census", "export", "citizen-atlas.jsonl")
OUT = os.path.join(ROOT, "census", "export", "citizen-assembly.jsonl")
BASIS = "biglife-assembly-v1"

AD042_SIZE = 19    # AD-042 Synty 都市人物基模（在册件数）
AD011_SIZE = 722   # AD-011 换装料库（O-020 令文在册件数）
RANK_MOD = 10000   # AD-024/AD-018 件数未入册：seeded rank 按库实际件数取模投影（对账窗锁值）

ORIGIN = {"carbon": "carbon-origin", "silicon": "silicon-origin",
          "sprite": "city-origin", "artifact-spirit": "city-origin",
          "memory-spirit": "city-origin", "imagery-spirit": "city-origin"}
LED = {"carbon": "amber", "silicon": "cyan"}          # 城源=惯例琥珀（§七.2 不变面）
FORM = {"sprite": "半透明发光小体·机源徽记", "artifact-spirit": "器灵·老物件成灵形态",
        "memory-spirit": "记忆灵·城市记得形态", "imagery-spirit": "意象灵·真天气具象形态"}
STYLE = {"烟火": "生活暖装", "秩序": "规整通勤", "求新": "新潮尝鲜",
         "怀旧": "旧料怀旧", "侠气": "硬朗工装", "逍遥": "轻便闲逸", None: "中性常服"}
HEX_KEYS = ("skin", "hair", "cloth", "eye", "badge")


def band(age):
    # 镜像 behavior.py band() 同源阈值（v3.19 年龄带·对账=QC 断言组）
    if not isinstance(age, int):
        return "mid"
    if age <= 17:
        return "child"
    if age <= 25:
        return "young"
    if age < 60:
        return "mid"
    return "elder"


def _h(cid, salt):
    return hashlib.md5(f"{cid}::{BASIS}::{salt}".encode("utf-8")).digest()


def _pick(cid, salt, size):
    return int.from_bytes(_h(cid, salt)[0:4], "big") % size


def _rank(cid, salt):
    return int.from_bytes(_h(cid, salt)[0:4], "big") % RANK_MOD


def _style(r):
    if r["species"] == "silicon":
        return "机房冷灰+电路纹"       # 硅源族系特征优先（§七.1）
    if r["species"] in FORM:
        return "光体谱系形态"
    return STYLE.get(r.get("axis"), "中性常服")


def load_atlas():
    pal = {}
    with open(ATLAS, encoding="utf-8") as f:
        for line in f:
            a = json.loads(line)
            pal[a["id"]] = {k: a.get(k) for k in HEX_KEYS}
    return pal


def build_rows():
    atlas = load_atlas()
    rows = []
    with open(LIGHT, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cid, sp = r["id"], r["species"]
            if r.get("faction") == "honored":
                rows.append({"id": cid, "species": sp, "faction": "honored",
                             "status": "reserved", "assembly": None,
                             "note": "CEO 保留面·化身样式=CEO 一句话拍板（CODEX §十/§七.3 批 2）零代创",
                             "v": 1})
                continue
            b = band(r.get("age"))
            p = atlas.get(cid)
            row = {
                "id": cid, "species": sp, "origin": ORIGIN[sp],
                "faction": r.get("faction", ""), "gender": r.get("gender", ""),
                "age": r.get("age"), "age_note": r.get("age_note", ""),
                "band": b, "profession": r.get("profession", ""),
                "base": {"lib": "AD-042", "pick": _pick(cid, "base", AD042_SIZE),
                         "size": AD042_SIZE, "ratio": "chibi"},
                "body": ({"type": "child", "parts_lib": "AD-024",
                          "rank": _rank(cid, "child")}
                         if b == "child" else {"type": "adult"}),
                "outfit": {"lib": "AD-011", "pick": _pick(cid, "outfit", AD011_SIZE),
                           "size": AD011_SIZE, "style": _style(r)},
                "variant": ({"lib": "AD-018", "rank": _rank(cid, "variant")}
                            if sp == "silicon" else None),
                "form": FORM.get(sp),
                "led_eye": {"family": LED.get(sp, "amber"),
                            "hex": (p or {}).get("eye"),
                            "impl": "emission+bloom"},
                "palette": ({"src": "citizen-atlas.jsonl", **p} if p else None),
                "status": "ok", "v": 1,
            }
            if p is None:
                row["palette_note"] = "atlas v2.4 无行（CEO 入城批）——零发明·待 atlas 扩行窗"
            rows.append(row)
    return rows


def write(rows, path=OUT):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def qc():
    with open(LIGHT, encoding="utf-8") as f:
        light = [json.loads(l) for l in f]
    rows = build_rows()
    atlas = load_atlas()
    errs = []
    if len(rows) != len(light):
        errs.append(f"rows {len(rows)} != light {len(light)}")
    reserved = 0
    for r, l in zip(rows, light):
        cid = r["id"]
        if r["id"] != l["id"]:
            errs.append(f"id order fail {cid}"); break
        if l.get("faction") == "honored":
            reserved += 1
            if r["status"] != "reserved" or r["assembly"] is not None:
                errs.append(f"honored not reserved {cid}"); break
            continue
        # 匹配律①族源三分闭集
        if r["origin"] != ORIGIN.get(l["species"]):
            errs.append(f"origin fail {cid}"); break
        # 匹配律②年龄→体型与儿童件（band 同源阈值）
        if r["band"] != band(l.get("age")):
            errs.append(f"band fail {cid}"); break
        if (r["body"]["type"] == "child") != (r["band"] == "child"):
            errs.append(f"body-band fail {cid}"); break
        if r["band"] == "child" and r["body"].get("parts_lib") != "AD-024":
            errs.append(f"child parts missing {cid}"); break
        if r["band"] != "child" and "parts_lib" in r["body"]:
            errs.append(f"adult has child parts {cid}"); break
        # 匹配律③性格身份→服装风格 + 装配管线域
        if not (0 <= r["base"]["pick"] < AD042_SIZE and r["base"]["lib"] == "AD-042"):
            errs.append(f"base pick fail {cid}"); break
        o = r["outfit"]
        if not (0 <= o["pick"] < AD011_SIZE and o["lib"] == "AD-011"):
            errs.append(f"outfit pick fail {cid}"); break
        if o["style"] not in set(STYLE.values()) | {"机房冷灰+电路纹", "光体谱系形态"}:
            errs.append(f"style not closed set {cid}"); break
        # 族系特征：硅源恒配变体/碳源城源零变体/LED 家族三分
        is_si = l["species"] == "silicon"
        if is_si != (r["variant"] is not None):
            errs.append(f"variant fail {cid}"); break
        exp_led = LED.get(l["species"], "amber")
        if r["led_eye"]["family"] != exp_led:
            errs.append(f"led family fail {cid}"); break
        # 调色单源：atlas 有行=五 hex 逐位镜像/无行=null+注记
        a = atlas.get(cid)
        if a is None:
            if r["palette"] is not None or "palette_note" not in r:
                errs.append(f"atlas-missing note fail {cid}"); break
        else:
            if r["palette"] is None or any(r["palette"][k] != a[k] for k in HEX_KEYS):
                errs.append(f"palette mirror fail {cid}"); break
            if r["led_eye"]["hex"] != a["eye"]:
                errs.append(f"eye hex fail {cid}"); break
    # 确定性：同 seed 同脸机检=双跑逐字节一致
    b1 = [json.dumps(x, ensure_ascii=False) for x in rows]
    b2 = [json.dumps(x, ensure_ascii=False) for x in build_rows()]
    if b1 != b2:
        errs.append("double-run mismatch")
    if errs:
        print("QC FAIL:"); [print(" -", e) for e in errs]; return 1
    from collections import Counter
    oc = Counter(x.get("origin") for x in rows)
    kids = sum(1 for x in rows if x.get("band") == "child")
    si_v = sum(1 for x in rows if x.get("variant"))
    pal_null = sum(1 for x in rows if x.get("status") == "ok" and x.get("palette") is None)
    print(f"QC PASS: rows={len(rows)} light={len(light)} reserved={reserved} "
          f"ok={len(rows)-reserved} origins={dict(oc)} children={kids} "
          f"silicon_variants={si_v} atlas_missing={pal_null} double_run=identical")
    return 0


def main():
    if "--qc" in sys.argv:
        sys.exit(qc())
    rows = build_rows()
    write(rows)
    print(f"wrote {len(rows)} rows -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
