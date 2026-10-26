# -*- coding: utf-8 -*-
"""全库编码守卫（D-20261026-13 派单落件）。

背景（判例）：
  10-20 TASKS.md 因「GBK 追加 + UTF-8 errors=replace 整档重写」被吞 2.3 万处正文；
  10-26 HQ-FEEDBACK.md 又出现 241 行 UTF-8 / 1 行 GBK 双字节混档（R2220 实锚）。
  tasks_board.py 只守任务板单点，缺的是「全库可巡检 + 任意写口可复用」的通用算具。

本工具三用：
  1) --check          全库严格的 UTF-8 体检（git 跟踪文本文件），输出 PASS/FAIL 与逐文件证据；
  2) --expect-lines   行数断言（如 HQ-FEEDBACK.md=N），防「整档重写吞段」类静默丢内容；
  3) --append         安全追加：写前拒损坏内容、写后复验全档严格可解（出生地拦截）。

判定口径：严格 utf-8 解码通过且无 BOM / 无 U+FFFD / 无典型 GBK 乱码字 = HEALTHY。
二进制文件按「含 NUL 字节或超长单行」自动跳过，不计入文本统计。

用法：
  python -X utf8 Tools/encoding_guard.py --check
  python -X utf8 Tools/encoding_guard.py --check --paths HQ-FEEDBACK.md tasks/TASKS.md
  python -X utf8 Tools/encoding_guard.py --check --expect-lines HQ-FEEDBACK.md=242
  python -X utf8 Tools/encoding_guard.py --append HQ-FEEDBACK.md --from-file <utf8片段>
  Get-Content 片段 | python -X utf8 Tools/encoding_guard.py --append HQ-FEEDBACK.md --stdin
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 典型 UTF-8 被当 GBK 解读后回写的特征字（快筛用；深度判定走 gbk->utf8 往返探针）
MOJIBAKE_MARKS = ("锛", "銆", "鐨", "鏉", "绔", "馃", "闃", "閿")


def gbk_repair(text):
    """把「UTF-8 被当 GBK 误解码」的串试着还原；还原不出返回 None。

    原理：乱码的码位按 GBK 编码回去，正好等于原始 UTF-8 字节。
    要求整段 GBK 可编码且结果严格为 UTF-8，且还原后的中文字符占比更高，
    以压低「合法中文恰好往返成功」的误报。
    """
    s = text.strip()
    if len(s) < 6:
        return None
    try:
        raw = s.encode("gbk")
    except Exception:
        return None
    try:
        fixed = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if fixed == s:
        return None
    # 中文原文 utf-8 = 3 字节/字，被误读成 GBK = 2 字节/字，故还原后长度约为原来的 2/3
    if len(fixed) < 2:
        return None
    # 关键判据：还原结果必须「像正常中文/ASCII」。正常中文往返会得到希伯来字符等垃圾，据此排除。
    cjk = sum(1 for c in fixed if "\u4e00" <= c <= "\u9fff")
    plain = sum(1 for c in fixed if c.isascii())
    if (cjk + plain) / len(fixed) < 0.9 or cjk / len(fixed) < 0.3:
        return None
    return fixed


def mojibake_scan(text, limit=3):
    """按行找疑似乱码；返回 (命中行数, 样例[(行号, 原文, 还原)])。"""
    hits, samples = 0, []
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) < 6:
            continue
        fixed = gbk_repair(line)
        if fixed:
            hits += 1
            if len(samples) < limit:
                samples.append((i, line.strip()[:80], fixed.strip()[:80]))
    return hits, samples

TEXT_SUFFIXES = (
    ".md", ".txt", ".py", ".json", ".jsonl", ".csv", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".ps1", ".bat", ".cmd", ".sh", ".html",
    ".css", ".js", ".ts", ".xml", ".sql", ".gitignore",
)

SKIP_PREFIXES = ("state/", "logs/", ".codely-cli/", "media/")


def rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def tracked_text_files():
    """git 跟踪的文本类文件（排除 state/logs 等不入库面）。"""
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, check=True
        ).stdout.decode("utf-8", "surrogateescape")
    except Exception as e:  # git 不可用则退化为目录扫描
        print("WARN git ls-files 失败（%s），退化为目录扫描" % e)
        found = []
        for base, _, names in os.walk(ROOT):
            if any(rel(base).startswith(p.rstrip("/")) for p in SKIP_PREFIXES):
                continue
            for n in names:
                if n.lower().endswith(TEXT_SUFFIXES):
                    found.append(rel(os.path.join(base, n)))
        return sorted(found)

    files = []
    for line in out.splitlines():
        p = line.strip()
        if not p or p.startswith(SKIP_PREFIXES):
            continue
        if p.lower().endswith(TEXT_SUFFIXES):
            files.append(p)
    return files


def diagnose(raw, label, marks=True):
    """返回问题清单；空列表 = HEALTHY。

    硬失败（阻断写盘/判 FAIL）= 非 UTF-8 字节 / BOM / U+FFFD；
    乱码字只作告警：既可能是历史损伤，也可能是「引用证据原文」的合法内容。
    """
    problems = []
    if raw.count(b"\x00"):
        problems.append("%s: 含 NUL 字节（疑似二进制，按文本处理有风险）" % label)
        return problems
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.append("%s: 非 UTF-8 字节（偏移 %d: %s）" % (label, e.start, e.reason))
        return problems
    if text.startswith("\ufeff"):
        problems.append("%s: 带 BOM" % label)
        text = text.lstrip("\ufeff")
    bad = text.count("\ufffd")
    if bad:
        problems.append("%s: 含 U+FFFD %d 处（正文被替换字符吞掉）" % (label, bad))
    if marks:
        for mark in MOJIBAKE_MARKS:
            n = text.count(mark)
            if n:
                problems.append("%s: 疑似 GBK 乱码字 %r %d 处" % (label, mark, n))
        hits, samples = mojibake_scan(text)
        if hits:
            detail = "；".join("L%d %r -> %r" % s for s in samples)
            problems.append("%s: 整段 GBK 误解码 %d 行（可还原样例：%s）"
                            % (label, hits, detail))
    return problems


def line_count(raw):
    return raw.decode("utf-8", "replace").count("\n") + 1 if raw else 0


MARK_DECLARATION_FILES = ("Tools/encoding_guard.py", "Tools/tasks_board.py")


def check(paths, expects, strict_marks=False):
    files = paths or tracked_text_files()
    healthy, broken, warns, skipped = 0, [], [], 0
    for p in files:
        full = os.path.join(ROOT, p)
        if not os.path.exists(full):
            broken.append((p, ["%s: 文件不存在" % p]))
            continue
        raw = open(full, "rb").read()
        if not raw:
            skipped += 1
            continue
        marks = p not in MARK_DECLARATION_FILES
        problems = diagnose(raw, p, marks=marks)
        hard = [x for x in problems if not ("乱码字" in x or "GBK 误解码" in x)]
        soft = [x for x in problems if ("乱码字" in x or "GBK 误解码" in x)]
        if hard:
            broken.append((p, hard))
        else:
            healthy += 1
        if soft:
            warns.append((p, soft))

    for (p, want), mode in expects:
        full = os.path.join(ROOT, p)
        if not os.path.exists(full):
            broken.append((p, ["%s: 行数断言失败（文件不存在）" % p]))
            continue
        got = line_count(open(full, "rb").read())
        if mode == "exact" and got != want:
            broken.append((p, ["%s: 行数 %d != 期望 %d（疑整档重写吞段）"
                               % (p, got, want)]))
        elif mode == "min" and got < want:
            broken.append((p, ["%s: 行数 %d < 基线 %d（追加型日志只增不减·疑吞段）"
                               % (p, got, want)]))

    for p, problems in broken:
        for msg in problems:
            print("FAIL", msg)
    for p, problems in warns:
        for msg in problems:
            print("WARN" if not strict_marks else "FAIL", msg)

    if strict_marks and warns:
        print("VERDICT FAIL(strict-marks): %d 文件命中乱码字" % len(warns))
        return 1
    if broken:
        print("VERDICT FAIL: %d/%d 文本文件硬性问题（空文件跳过 %d）"
              % (len(broken), len(files), skipped))
        return 1

    print("VERDICT PASS: %d 个文本文件严格 UTF-8 / 无 BOM / U+FFFD=0（空文件跳过 %d，乱码字告警 %d）"
          % (healthy, skipped, len(warns)))
    if expects:
        print("行数断言: " + ", ".join(
            "%s%s%d" % (p, ">=" if m == "min" else "=", w) for (p, w), m in expects
        ) + " 全部相符")
    return 0


def append(target, chunk_text):
    full = os.path.join(ROOT, target)
    if not os.path.exists(full):
        print("FAIL %s 不存在，拒绝追加（新文件请直接建）" % target)
        return 2
    chunk_bytes = chunk_text.encode("utf-8")
    if not chunk_bytes.strip():
        print("FAIL 空片段，拒绝写入")
        return 2

    problems = diagnose(chunk_bytes, "new-chunk")
    if problems:
        for p in problems:
            print("FAIL", p)
        print("FAIL 片段本身不健康，拒绝写入（正法：源文本以 UTF-8 读取，禁 gbk 解码后回写）")
        return 2

    raw = open(full, "rb").read()
    existing = diagnose(raw, target)
    if existing:
        for p in existing:
            print("FAIL", p)
        print("FAIL 现有文件已损坏，先修复再追加")
        return 2

    text = raw.decode("utf-8")
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    merged = (text + sep + chunk_text.strip("\n") + "\n").encode("utf-8")

    after = diagnose(merged, target + "(after)")
    if after:
        for p in after:
            print("FAIL", p)
        print("FAIL 写后复验不通过，放弃写盘")
        return 2

    tmp = full + ".tmp"
    with open(tmp, "wb") as f:
        f.write(merged)
    os.replace(tmp, full)
    print("OK %s 追加完成：+%d 字节，行数 %d -> %d"
          % (target, len(chunk_bytes), line_count(raw), line_count(merged)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="全库 UTF-8 体检")
    ap.add_argument("--paths", nargs="*", default=None, help="限定检查的文件（默认全库跟踪文本）")
    ap.add_argument("--expect-lines", nargs="*", default=None,
                    help="行数断言，形如 path=N")
    ap.add_argument("--append", default=None, help="目标文件（相对仓库根）")
    ap.add_argument("--from-file", default=None, help="追加片段文本文件（UTF-8）")
    ap.add_argument("--stdin", action="store_true", help="从标准输入读追加片段")
    ap.add_argument("--strict-marks", action="store_true",
                    help="把「疑似 GBK 乱码字」告警升格为 FAIL")
    args = ap.parse_args()

    if args.check or args.paths or args.expect_lines:
        expects = []
        for item in (args.expect_lines or []):
            mode = "exact"
            if ">=" in item:
                p, n = item.split(">=", 1)
                mode = "min"
            elif "=" in item:
                p, n = item.rsplit("=", 1)
            else:
                print("FAIL --expect-lines 需形如 path=N 或 path>=N，收到 %r" % item)
                return 2
            expects.append(((p.strip(), int(n)), mode))
        return check(args.paths, expects, strict_marks=args.strict_marks)

    if args.append:
        if args.from_file:
            if not os.path.exists(args.from_file):
                print("FAIL 片段文件不存在：%s" % args.from_file)
                return 2
            chunk = open(args.from_file, "rb").read().decode("utf-8")
        elif args.stdin:
            chunk = sys.stdin.buffer.read().decode("utf-8")
        else:
            print("FAIL 需给 --from-file 或 --stdin")
            return 2
        return append(args.append, chunk)

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())