# -*- coding: utf-8 -*-
"""升华链补链批 v0 —— T-20260926-18 步⑨ 分步④（⚠️8385 补链·升华令 §二.8 追加注记式保原文）

法源=O-20260926-2225-bm-c《硅基居民升华律执行令》v1.3 §二.8 + 契约立契（R425·判据六条预注册 R99 范式）。
派生律=三段全卡面原文派生零编造：
  未来形态   = 职业行首个「：」前段（逐字）
  中环段     = 职业行首个「：」至首个「——」段（逐字）+法定连接词「」的（赛博）后身
  升华一句话 = 职业行首个「——」后段（逐字·含后续「——」整段）
  字符集 ⊆ 卡面原文 ∪ 法定连接词闭集（RUMOR-CHAIN 判据 4 同律）。
注记行=卡尾追加一行（原文零删改·git diff 每卡 +1/-0）：
  居民   {NOTE_MARK}{未来形态}——「{中环段}」的（赛博）后身——{升华一句话}
  像素灵 {NOTE_MARK}物种域注记：{物种全名}——《城市生灵册》#{N} 定谳行（生灵族·物种域·非个体链）
红线：职业行本体零改写（✅链在职业行=生成门口径不漂移）；荣誉席 C-00001~09+手写锚 20 结构排除
  （只扫 census/registry 六城区+ID 带防护）；227「复古后身」变体桶不入首批（REVIEW 单列定谳）；
  永生语义只封存不删除。分批律=每轮 ≤500 张（--limit·预算内做多少收多少）；复跑幂等（已注记卡跳过）；
  进度面=state/sublimate-chain-progress.json（state/ 不入库）。纯确定性零 LLM。
"""
import glob
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sublimate_audit as sa  # 79 模板定谳表/城区表/像素灵前缀/注记标记单源复用（禁双建）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "sublimate-chain-progress.json")

# 《城市生灵册》v1 册号映射（census 既有 6 物种 → 册 #1-#6·docs/city-creatures-book.md）
SPRITE_BOOK = {"消息雀": 1, "电波猫": 2, "守夜灯灵": 3, "数据锦鲤": 4, "雨声蛙": 5, "风铃蝶": 6}


def prof_line(text):
    m = re.search(r"\*\*职业\*\* (.+)", text)
    return m.group(1).strip() if m else ""


def species_of(text):
    m = re.search(r"\*\*物种\*\* (.+?)｜", text)
    return m.group(1).strip() if m else "?"


def segments(prof):
    """三段派生：None=无三段（降级桶）。"""
    if "：" not in prof:
        return None
    form, rest = prof.split("：", 1)
    if "——" not in rest:
        return None
    mid, _, sub = rest.partition("——")
    form, mid, sub = form.strip(), mid.strip(), sub.strip()
    if not form or not mid or not sub:
        return None
    return form, mid, sub


def res_note(form, mid, sub):
    return "%s%s——「%s」的（赛博）后身——%s" % (sa.NOTE_MARK, form, mid, sub)


def sprite_note(species):
    tail = species.split("·", 1)[1].strip() if "·" in species else ""
    n = SPRITE_BOOK.get(tail)
    if not n:
        return None
    return "%s物种域注记：%s——《城市生灵册》#%d 定谳行（生灵族·物种域·非个体链）" % (sa.NOTE_MARK, species, n)


def parse(text, cid):
    prof = prof_line(text)
    species = species_of(text)
    return {
        "id": cid, "species": species, "prof": prof,
        "name": sa.prof_name(prof),
        "chain": "赛博后身" in text,
        "note": sa.NOTE_MARK in text,
        "variant": "复古后身" in prof,
        "sprite": species.startswith(sa.SPRITE_PREFIX),
        "creed": "**信条**" in text,
    }


def classify(r):
    """桶定谳（审计同口径）：ok/noted_res/noted_spr/variant/degraded/review/eligible_res/eligible_spr/spr_unknown。"""
    if r["chain"]:
        return "ok"
    if r["note"]:
        return "noted_spr" if r["sprite"] else "noted_res"
    if r["sprite"]:
        tail = r["species"].split("·", 1)[1].strip() if "·" in r["species"] else ""
        return "eligible_spr" if tail in SPRITE_BOOK else "spr_unknown"
    if r["variant"]:
        return "variant"
    if not r["creed"] or not segments(r["prof"]):
        return "degraded"
    if r["name"] in sa.FUTURE_FORMS:
        return "eligible_res"
    return "review"


def scan(root=ROOT):
    """只扫 census/registry 六城区（reserved/anchors 结构排除）+C-00001~09 ID 带防护。"""
    out = []
    for d in sa.DISTRICTS:
        for p in sorted(glob.glob(os.path.join(root, "census", "registry", d, "*.md"))):
            cid = os.path.basename(p)[:-3]
            if re.match(r"C-\d{5}$", cid) and cid <= "C-00009":
                continue
            out.append((p, parse(io.open(p, encoding="utf-8").read(), cid)))
    return out


def build_line(r):
    if r["sprite"]:
        return sprite_note(r["species"])
    seg = segments(r["prof"])
    return res_note(*seg) if seg else None


def apply_batch(limit=500, scope="residents", root=ROOT, via="BigLife-OSLoop"):
    cards = scan(root)
    buckets, todo = {}, []
    for p, r in cards:
        b = classify(r)
        buckets[b] = buckets.get(b, 0) + 1
        if b == ("eligible_res" if scope == "residents" else "eligible_spr"):
            todo.append((p, r))
    want = "eligible_res" if scope == "residents" else "eligible_spr"
    applied, ids = 0, []
    for p, r in todo[:limit]:
        t = io.open(p, encoding="utf-8").read()
        assert sa.NOTE_MARK not in t, "幂等防护: %s 已注记" % r["id"]
        line = build_line(r)
        assert line, "降级桶泄漏: %s" % r["id"]
        seg = segments(r["prof"])
        for part in (seg if seg else ()):  # 判据②三段=卡面逐字子串
            assert part in t, "子串违例: %s" % r["id"]
        nt = t if t.endswith("\n") else t + "\n"
        nt += line + "\n"
        # 判据①追加铁律：原文前缀保全+单行追加（+1/-0）
        assert nt.startswith(t) and nt.count("\n") == t.count("\n") + 1
        io.open(p, "w", encoding="utf-8", newline="\n").write(nt)
        back = io.open(p, encoding="utf-8").read()
        assert back == nt, "写后复核违例: %s" % r["id"]
        applied += 1
        ids.append(r["id"])
    state = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "via": via, "scope": scope,
        "applied_this_run": applied, "batch_head_tail": [ids[0], ids[-1]] if ids else [],
        "noted_total": buckets.get("noted_res", 0) + buckets.get("noted_spr", 0) + applied,
        "buckets_before_run": buckets,
    }
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(json.dumps(state, ensure_ascii=False, indent=1))
    print("sublimate_chain: scope=%s eligible=%d applied=%d" % (scope, len(todo), applied))
    print("buckets:", json.dumps(buckets, ensure_ascii=False, sort_keys=True))
    if ids:
        print("batch: %s..%s" % (ids[0], ids[-1]))
    print("progress -> %s" % os.path.relpath(STATE, root))
    return applied, buckets


def _fixture_card(cid, species, prof, extra=""):
    return ("# %s · 测试\n\n**物种** %s ｜ **性别·年龄** 女 · 编译纪 59 年 ｜ **城区** GAME 城\n"
            "**职业** %s\n\n**信条** 「火候到了，一切都会开锅。」\n\n%s**溯源** 生成批次 P-0 · 基因指纹 test\n"
            % (cid, species, prof, extra))


def qc():
    ok = [0]

    def check(name, cond):
        assert cond, "QC FAIL: %s" % name
        ok[0] += 1
        print("  PASS %s" % name)

    print("sublimate_chain --qc")
    # ① 三段派生（判据②逐字）
    prof = "游戏策划：玩法的设计师——在八栋游戏楼里画着让人笑让人哭的图纸"
    seg = segments(prof)
    check("segments 三段逐字", seg == ("游戏策划", "玩法的设计师", "在八栋游戏楼里画着让人笑让人哭的图纸"))
    check("segments 多「——」后段整段", segments("A：B——C——D") == ("A", "B", "C——D"))
    check("segments 无冒号=None", segments("夜灯员——护送者") is None)
    check("segments 段后无「——」=None", segments("A：B") is None)
    check("segments 空中环=None", segments("A：——B") is None)
    # ② 注记行格式（契约逐字）
    note = res_note(*seg)
    check("res_note 契约格式", note == "**升华链**（升华令 §二.8 追加注记·原文保全）游戏策划——「玩法的设计师」的（赛博）后身——在八栋游戏楼里画着让人笑让人哭的图纸")
    check("res_note 字符集⊆原文∪连接词", all(part in prof for part in seg) and "的（赛博）后身" in note)
    # ③ 像素灵映射 6/6（判据⑥对齐生灵册册号）
    check("SPRITE_BOOK 册号 6/6", set(SPRITE_BOOK.values()) == {1, 2, 3, 4, 5, 6}
          and set(SPRITE_BOOK) == {"消息雀", "电波猫", "守夜灯灵", "数据锦鲤", "雨声蛙", "风铃蝶"})
    sn = sprite_note("像素灵·守夜灯灵")
    check("sprite_note #3 定谳行", sn is not None and "#3" in sn and "《城市生灵册》" in sn and "非个体链" in sn)
    check("sprite_note 未知物种=None", sprite_note("像素灵·疗愈光毯犬") is None)
    # ④ 桶定谳（幂等/变体/降级/未知模板/物种域）
    good = _fixture_card("C-00100", "硅基民·光机魂系", prof)
    check("eligible_res", classify(parse(good, "C-00100")) == "eligible_res")
    check("已注记=幂等跳过", classify(parse(good + sa.NOTE_MARK + "x\n", "C-00100")) == "noted_res")
    check("原生链=ok", classify(parse(_fixture_card("C-00101", "硅基民", "A：B 的赛博后身——C"), "C-00101")) == "ok")
    check("复古后身=variant 桶", classify(parse(_fixture_card("C-00102", "硅基民", "老克勒咖啡主：旧梦的复古后身——回甘"), "C-00102")) == "variant")
    check("无信条=degraded", classify(parse(good.replace("**信条** 「火候到了，一切都会开锅。」", ""), "C-00103")) == "degraded")
    check("未知模板=review", classify(parse(_fixture_card("C-00104", "硅基民", "未知职业：X——Y"), "C-00104")) == "review")
    check("像素灵=eligible_spr", classify(parse(_fixture_card("C-00105", "像素灵·消息雀", "信使小跟班——衔笺的"), "C-00105")) == "eligible_spr")
    check("像素灵已注记=noted_spr", classify(parse(_fixture_card("C-00105", "像素灵·消息雀", "信使小跟班——衔笺的") + sprite_note("像素灵·消息雀"), "C-00105")) == "noted_spr")
    # ⑤ 文件级夹具：结构排除（reserved/anchors/荣誉席 ID）+ 追加铁律 + 幂等复跑 + 限量
    tmp = tempfile.mkdtemp(prefix="subl_chain_qc_")
    try:
        for d in ("registry/GM", "registry/RV", "reserved", "anchors"):
            os.makedirs(os.path.join(tmp, "census", d), exist_ok=True)
        io.open(os.path.join(tmp, "census", "registry", "GM", "C-00100.md"), "w", encoding="utf-8").write(good)
        io.open(os.path.join(tmp, "census", "registry", "GM", "C-00101.md"), "w", encoding="utf-8").write(
            _fixture_card("C-00101", "硅基民", "声景师：城市声音的调音人——让每条街有自己的音色"))
        io.open(os.path.join(tmp, "census", "registry", "GM", "C-00102.md"), "w", encoding="utf-8").write(
            _fixture_card("C-00102", "硅基民", "夜灯员：晚归人的引路光——灯不灭巷不黑") + sa.NOTE_MARK + "x\n")
        io.open(os.path.join(tmp, "census", "registry", "GM", "C-00001.md"), "w", encoding="utf-8").write(good)
        io.open(os.path.join(tmp, "census", "reserved", "C-00002.md"), "w", encoding="utf-8").write(good)
        io.open(os.path.join(tmp, "census", "anchors", "C-00010.md"), "w", encoding="utf-8").write(good)
        cards = scan(root=tmp)
        check("结构排除（reserved/anchors/ID 带）", sorted(r["id"] for _, r in cards) == ["C-00100", "C-00101", "C-00102"])
        applied, buckets = apply_batch(limit=2, scope="residents", root=tmp, via="qc")
        check("限量=2 且 eligible_res=2", applied == 2 and buckets["eligible_res"] == 2)
        p1 = os.path.join(tmp, "census", "registry", "GM", "C-00100.md")
        t1 = io.open(p1, encoding="utf-8").read()
        want_note = res_note("游戏策划", "玩法的设计师", "在八栋游戏楼里画着让人笑让人哭的图纸")
        check("追加铁律（前缀保全+单行+1）", t1.startswith(good) and t1.count("\n") == good.count("\n") + 1
              and t1.rstrip("\n").splitlines()[-1] == want_note)
        check("注记行三段=职业行逐字子串", want_note in t1 and "「玩法的设计师」的（赛博）后身" in t1)
        check("已注记卡零触碰", io.open(os.path.join(tmp, "census", "registry", "GM", "C-00102.md"), encoding="utf-8").read().count(sa.NOTE_MARK) == 1)
        applied2, _ = apply_batch(limit=2, scope="residents", root=tmp, via="qc")
        check("复跑幂等（二次零写入）", applied2 == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("sublimate_chain --qc: %d/%d ALL PASS" % (ok[0], ok[0]))
    return ok[0]


def main():
    args = sys.argv[1:]
    if "--qc" in args:
        qc()
        return
    limit = 500
    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    scope = "residents"
    if "--scope" in args:
        scope = args[args.index("--scope") + 1]
    via = "BigLife-OSLoop"
    if "--via" in args:
        via = args[args.index("--via") + 1]
    if "--scan" in args:
        cards = scan()
        buckets = {}
        for _, r in cards:
            b = classify(r)
            buckets[b] = buckets.get(b, 0) + 1
        print("sublimate_chain --scan: cards=%d" % len(cards))
        print("buckets:", json.dumps(buckets, ensure_ascii=False, sort_keys=True))
        return
    apply_batch(limit=limit, scope=scope, via=via)


if __name__ == "__main__":
    main()
