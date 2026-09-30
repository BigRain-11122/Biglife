#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""consumer_wiring.py v1.0 -- XL-17 消费方接线数判据扫描器
法源: D-20260930-06 全域改进清单 XL-17 BigLife「消费方接线数判据」·T-20260930-01 分步①②
判据: 消费方接线数 = 对 census/export 导出面存在实际程序化接线（代码/配置文件内容引用）
      的下游消费方仓计数。文档级引用（.md/.txt 等纯文档扩展）不计。
计数面: 通知族下游四仓（FluxVerse / MiniGame(Biggame) / BigDomain / BigStream）。
      cph4 = 集团工具面（审计探针可命中 census 字样）非下游消费方 → 证据仍录但不计入 wired_count。
红线: 兄弟仓只读扫描零写入（铁律④）·本司不代消费方写接线（反无消费方立项律）。
用法: python -X utf8 Tools/consumer_wiring.py            # 盘面直数输出（JSON+WIRED_COUNT）
      python -X utf8 Tools/consumer_wiring.py --qc      # 双跑逐字节一致 + 导出面存在性断言
"""
import os
import re
import sys
import json
import time
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # BigLife 仓根
GROUP = os.path.dirname(os.path.dirname(ROOT))                          # FluxGroup 集团根
EXPORT_DIR = os.path.join(ROOT, "census", "export")

# 导出面闭集 = census/export 12 jsonl 面 + 路径面（v1.0 与盘面文件一一对应）
SURFACES = [
    "citizens-light.jsonl", "citizen-needs.jsonl", "citizen-behavior.jsonl",
    "citizen-tasks.jsonl", "citizen-relations.jsonl", "citizen-anchors.jsonl",
    "citizen-assembly.jsonl", "citizen-initiatives.jsonl", "citizen-atlas.jsonl",
    "citizen-persona.jsonl", "citizen-goals.jsonl", "citizen-voice.jsonl",
    "census/export",
]
SURF_BYTES = [s.encode("ascii") for s in SURFACES]
HIT_RE = re.compile("|".join(re.escape(s) for s in SURFACES))

# 消费方仓闭集（通知族 T-20260923-01 五方 → 四仓映射：Biggame 量产线与 MiniGame 观测窗同仓）
CONSUMERS = [
    ("fluxverse", os.path.join(GROUP, "gaming", "FluxVerse"), True),
    ("biggame-minigame", os.path.join(GROUP, "gaming", "MiniGame"), True),
    ("bigdomain", os.path.join(GROUP, "domain"), True),
    ("bigstream", os.path.join(GROUP, "media"), True),
    ("cph4-tools", os.path.join(GROUP, "cph4"), False),   # 集团工具面·不计入
]

CODE_EXT = {".py", ".cs", ".js", ".ts", ".jsx", ".tsx", ".html", ".ps1", ".sh",
            ".bat", ".cmd", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
            ".csproj", ".lua", ".gd", ".php"}
SKIP_DIRS = {".git", ".codely-cli", ".codely", "Library", "library", "Temp", "temp",
             "Obj", "obj", "Bin", "bin", "node_modules", "Logs", "logs", "Log",
             "Build", "Builds", "build", ".vs", ".idea", "__pycache__",
             ".ruff_cache", "hf-cache", ".import", ".godot", "torchinductor_sjs20"}
MAX_FILE = 512 * 1024
EVIDENCE_CAP = 12


def _decode(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def scan_once(verbose=False):
    out = {"consumers": {}}
    for name, path, counts in CONSUMERS:
        t0 = time.time()
        ev, nfiles = [], 0
        exists = os.path.isdir(path)
        if exists:
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    if os.path.splitext(fn)[1].lower() not in CODE_EXT:
                        continue
                    fp = os.path.join(dirpath, fn)
                    try:
                        if os.path.getsize(fp) > MAX_FILE:
                            continue
                        with open(fp, "rb") as f:
                            raw = f.read()
                    except OSError:
                        continue
                    nfiles += 1
                    if not any(t in raw for t in SURF_BYTES):
                        continue
                    for i, line in enumerate(_decode(raw).splitlines(), 1):
                        if HIT_RE.search(line):
                            for tok in SURFACES:
                                if tok in line:
                                    ev.append({
                                        "file": os.path.relpath(fp, GROUP).replace("\\", "/"),
                                        "line": i, "token": tok,
                                        "excerpt": line.strip()[:110],
                                    })
                                    break
        out["consumers"][name] = {
            "root": os.path.relpath(path, GROUP).replace("\\", "/"),
            "exists": exists,
            "counts_in_wired": counts,
            "wired": bool(ev),
            "evidence_count": len(ev),
            "files_scanned": nfiles,
            "evidence": ev[:EVIDENCE_CAP],
        }
        if verbose:
            print("[scan] %-17s files=%d wired=%s ev=%d %.1fs"
                  % (name, nfiles, bool(ev), len(ev), time.time() - t0), flush=True)
    out["wired_count"] = sum(1 for c in out["consumers"].values()
                             if c["counts_in_wired"] and c["wired"])
    out["wired_list"] = [n for n, c in out["consumers"].items()
                         if c["counts_in_wired"] and c["wired"]]
    return out


def main():
    if "--qc" in sys.argv:
        a, b = scan_once(verbose=True), scan_once(verbose=False)
        ha = hashlib.md5(json.dumps(a, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        hb = hashlib.md5(json.dumps(b, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        missing = [s for s in SURFACES
                   if "/" not in s and not os.path.exists(os.path.join(EXPORT_DIR, s))]
        det_ok = ha == hb
        exp_ok = not missing
        print("QC determinism: %s (%s)" % ("PASS" if det_ok else "FAIL", ha))
        print("QC surface existence: %s (missing=%s)" % ("PASS" if exp_ok else "FAIL", missing))
        print("QC wired_count=%d wired_list=%s" % (a["wired_count"], a["wired_list"]))
        for n, c in a["consumers"].items():
            print("QC consumer %-17s exists=%s wired=%s evidence_count=%d files=%d counts_in_wired=%s"
                  % (n, c["exists"], c["wired"], c["evidence_count"], c["files_scanned"], c["counts_in_wired"]))
        sys.exit(0 if (det_ok and exp_ok) else 1)
    res = scan_once(verbose=True)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print("WIRED_COUNT=%d WIRED_LIST=%s" % (res["wired_count"], res["wired_list"]))


if __name__ == "__main__":
    main()
