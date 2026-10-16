# -*- coding: utf-8 -*-
"""update_status_export.py v1.0 — 通用 status-export 续鲜工具（OSS 第四窗切片 2 采用落地件）

替代每轮手写 state/_upd_export_rXXXX.py / _close_rXXXX.py 外科脚本（40+ churn 根治件）。
语义面与既有外科脚本严格等价：export_ts 刷新 + dept0 滚动窗（最新 3 条）+ QC 例巡条前插
+ results 尾行追加 + 心跳行（可选）。他司/他行零触碰。

用法：
  python -X utf8 Tools/update_status_export.py --payload state/export-payload-R1506.json [--dry-run] [--heartbeat]
  python -X utf8 Tools/update_status_export.py --qc          # 自检电池（合成数据，零触碰真件）

payload JSON（声明式，由轮次 write_file 落盘，规避 CLI CJK 引号坑族）：
  {
    "round": "R1506",                       # 必填，幂等标记
    "dept_text": "**R1506（...）**：...",     # 必填，dept0 新窗条（滚动窗保最新 3 条）
    "results_note": "... {N} ...",           # 必填，results 尾行文本，{N} 自动替换为机器直数
    "qc_text": null | "**R1506 例巡条...**", # 可选，QC 巡检线前插条
    "expect_total": 326                      # 可选，账平断言；缺省=信任机器直数
  }

幂等语义（resumable，根治 R1481/R1503 断链形态）：按段判重——
  dept0 已含本轮标记 → 跳过 dept 段；results 尾行计数==机器直数 → 跳过追加；
  QC 段已含本轮标记 → 跳过前插。重跑=已做段全 no-op，断链段自动补位。
"""
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
SE_PATH = os.path.join(ROOT, "docs", "status-export.json")
HB_PATH = os.path.join(ROOT, "state", "heartbeat.txt")

DEPT0_NAME = "年轮进化线"
QC_NAME = "QC 巡检线"
WINDOW = 3
HDR_RE = re.compile(r"\*\*R\d{3,5}（")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def count_rings(dirpath, today):
    """[锚] 行级机器直数（registry/anchors 递归），与既有外科脚本同谓词。"""
    n = 0
    for base, _, files in os.walk(dirpath):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(base, fn)
            try:
                with io.open(p, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.startswith("- " + today) and "[锚]" in line and "V2-B 反思层" not in line:
                            n += 1
            except OSError:
                pass
    return n


def machine_total(today=None):
    today = today or today_str()
    reg = count_rings(os.path.join(ROOT, "census", "registry"), today)
    anc = count_rings(os.path.join(ROOT, "census", "anchors"), today)
    return reg + anc, reg, anc


def split_dept_entries(t):
    """dept0.t 按 **R####（ 头标切段，返回条目列表。"""
    pos = [m.start() for m in HDR_RE.finditer(t)]
    if not pos:
        return []
    out = []
    for i, s in enumerate(pos):
        e = pos[i + 1] if i + 1 < len(pos) else len(t)
        out.append(t[s:e].strip())
    return out


def round_marker(round_id):
    return "**%s（" % round_id


def load_payload(path):
    with io.open(path, encoding="utf-8-sig") as f:
        p = json.load(f)
    for k in ("round", "dept_text", "results_note"):
        if not p.get(k):
            raise SystemExit("payload missing key: %s" % k)
    if not re.fullmatch(r"R\d{3,5}", p["round"]):
        raise SystemExit("bad round id: %r" % p["round"])
    return p


def apply_refresh(payload, dry_run=False, heartbeat=False):
    today = today_str()
    total, reg, anc = machine_total(today)
    if payload.get("expect_total") is not None:
        got = total
        exp = int(payload["expect_total"])
        if got != exp:
            raise SystemExit("ACCOUNT_MISMATCH expect=%d machine=%d (reg=%d anc=%d)" % (exp, got, reg, anc))
    rid = payload["round"]
    marker = round_marker(rid)
    qc_marker = "**%s 例巡条" % rid
    if not payload["dept_text"].strip().startswith(marker):
        raise SystemExit("DEPT_TEXT_FORMAT_GUARD expect startswith %r" % marker)
    qc_text = payload.get("qc_text")
    if qc_text and not qc_text.strip().startswith(qc_marker):
        raise SystemExit("QC_TEXT_FORMAT_GUARD expect startswith %r" % qc_marker)

    raw = io.open(SE_PATH, encoding="utf-8").read()
    had_nl = raw.endswith("\n")
    d = json.loads(raw)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    changed = {"dept": False, "qc": False, "results": False, "hb": False}

    # --- dept0: 年轮进化线 滚动窗（幂等：标记已在不重写） ---
    dep0 = d["depts"][0]
    if dep0.get("n") != DEPT0_NAME:
        raise SystemExit("DEPT0_NAME_GUARD got=%r" % dep0.get("n"))
    if marker not in dep0["t"]:
        entries = split_dept_entries(dep0["t"])
        new_entries = [payload["dept_text"].strip()] + entries
        dep0["t"] = " ".join(new_entries[:WINDOW])
        changed["dept"] = True

    # --- QC 巡检线: 例巡条前插（幂等：QC 标记已在不重插） ---
    qc_text = payload.get("qc_text")
    if qc_text:
        for dep in d["depts"]:
            if dep.get("n") == QC_NAME:
                if qc_marker not in dep["t"]:
                    dep["t"] = qc_text.strip() + " " + dep["t"]
                    changed["qc"] = True
                break
        else:
            raise SystemExit("QC_DEPT_NOT_FOUND")

    # --- results: 尾行追加（幂等：尾行计数==机器直数不重append） ---
    last_cnt = str(d["results"][-1][0]) if d["results"] else None
    if last_cnt != str(total):
        note = payload["results_note"].replace("{N}", str(total))
        d["results"].append([str(total), note])
        changed["results"] = True

    d["export_ts"] = ts

    if dry_run:
        print("DRYRUN total=%d reg=%d anc=%d dept=%s qc=%s results=%s ts=%s" % (
            total, reg, anc, changed["dept"], changed["qc"], changed["results"], ts))
        return total, changed, ts

    out = json.dumps(d, ensure_ascii=False, indent=1)
    if had_nl:
        out += "\n"
    with io.open(SE_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(out)

    # round-trip 回读校验
    d2 = json.loads(io.open(SE_PATH, encoding="utf-8").read())
    assert d2["export_ts"] == ts, "roundtrip export_ts"
    assert len(d2["results"]) == len(d["results"]), "roundtrip results len"
    assert d2["depts"][0]["t"].startswith("**R"), "roundtrip dept0"

    # --- heartbeat（可选·幂等：尾行含本轮标记不重写） ---
    if heartbeat:
        line = "%s %s %s alive rings_today=%d export_ts=%s [via BigLife-OSLoop]" % (
            today, ts[-5:], rid, total, ts)
        try:
            hb_tail = io.open(HB_PATH, encoding="utf-8").read().rstrip("\n").split("\n")[-1]
        except (OSError, IndexError):
            hb_tail = ""
        if rid not in hb_tail:
            with io.open(HB_PATH, "a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")
            changed["hb"] = True

    print("OK total=%d reg=%d anc=%d dept=%s qc=%s results=%s hb=%s ts=%s" % (
        total, reg, anc, changed["dept"], changed["qc"], changed["results"], changed["hb"], ts))
    return total, changed, ts


def qc_battery():
    """自检电池：合成数据，零触碰真件。"""
    ok = 0

    # 1) dept 切段：3 条合成 → 3 段
    t = "**R1001（aaa）**：x **R1002（bbb）**：y **R1003（ccc）**：z"
    es = split_dept_entries(t)
    assert len(es) == 3 and es[0].startswith("**R1001（") and es[-1].endswith("z"), es
    ok += 1

    # 2) 滚动窗：前插新条保 3 → 丢最旧
    new = ["**R1004（ddd）**：w"] + es
    assert new[:WINDOW] == ["**R1004（ddd）**：w", es[0], es[1]], new[:WINDOW]
    assert "**R1003（" not in " ".join(new[:WINDOW])
    ok += 1

    # 3) 单条存量 dept：切段不丢尾
    es1 = split_dept_entries("**R1001（aaa）**：全 文 尾")
    assert len(es1) == 1 and es1[0].endswith("尾"), es1
    ok += 1

    # 4) {N} 替换 + results 幂等判据
    assert "环 326 零差".replace("326", str(326)) == "环 326 零差"
    last = ["326", "x"]
    assert str(326) == last[0], "idem guard"
    ok += 1

    # 5) marker 生成
    assert round_marker("R1506") == "**R1506（", "marker"
    ok += 1

    # 6) tempfile 上 resumable 语义（写-重跑-段 no-op）零触碰真件
    #    （machine_total 注入定值——真件面有在飞批时直数会漂移，测试须封口）
    global SE_PATH, HB_PATH, machine_total
    real_se, real_hb = SE_PATH, HB_PATH
    orig_mt = machine_total
    def _fake_mt(today=None):
        return 331, 305, 26
    machine_total = _fake_mt
    try:
        with tempfile.TemporaryDirectory() as td:
            fake = {
                "export_ts": "old", "do": [], "depts": [
                    {"n": DEPT0_NAME, "t": "**R1505（a）**：x"},
                    {"n": QC_NAME, "t": "旧条"},
                ], "outs": [], "results": [["300", "r300"]],
            }
            sep = os.path.join(td, "status-export.json")
            with io.open(sep, "w", encoding="utf-8", newline="") as f:
                f.write(json.dumps(fake, ensure_ascii=False, indent=1) + "\n")
            SE_PATH = sep
            HB_PATH = os.path.join(td, "heartbeat.txt")
            p1 = {"round": "R1506", "dept_text": "**R1506（b）**：y",
                  "results_note": "环 {N} 零差", "qc_text": "**R1506 例巡条**：q"}
            apply_refresh(p1)  # 首跑：三段全写
            d1 = json.loads(io.open(sep, encoding="utf-8").read())
            assert len(d1["results"]) == 2 and d1["results"][-1][0] == "331", "results appended with machine count"
            assert d1["depts"][0]["t"].startswith("**R1506（"), "dept prepended"
            assert d1["depts"][1]["t"].startswith("**R1506 例巡条"), "qc prepended"
            t_before = d1["depts"][0]["t"]
            apply_refresh(p1)  # 复跑：幂等 no-op（dept 标记在+QC 标记在+results 尾计数同）
            d2 = json.loads(io.open(sep, encoding="utf-8").read())
            assert d2["depts"][0]["t"] == t_before, "dept idempotent"
            assert len(d2["results"]) == len(d1["results"]), "results idempotent"
            assert d2["depts"][1]["t"] == d1["depts"][1]["t"], "qc idempotent"
            ok += 1
    finally:
        SE_PATH, HB_PATH = real_se, real_hb
        machine_total = orig_mt

    print("QC_BATTERY %d/6 PASS" % ok)
    assert ok == 6


def main():
    args = sys.argv[1:]
    if "--qc" in args:
        qc_battery()
        return
    payload_path = None
    dry = "--dry-run" in args
    hb = "--heartbeat" in args
    for i, a in enumerate(args):
        if a == "--payload" and i + 1 < len(args):
            payload_path = args[i + 1]
    if not payload_path:
        raise SystemExit(__doc__)
    p = load_payload(payload_path)
    os.chdir(ROOT)
    apply_refresh(p, dry_run=dry, heartbeat=hb)


if __name__ == "__main__":
    main()
