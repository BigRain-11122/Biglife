# -*- coding: utf-8 -*-
"""任务板写入闸（出生地拦截）。

2026-10-20 判例（T-20261020-02/03）：tasks/TASKS.md 曾因追加脚本按 GBK 写入、
随后又按 UTF-8 errors=replace 整档重写，导致 2.3 万处正文被替换为 U+FFFD。
本工具把「写入即校验」固定到出生地：任何追加都走这里，写前拒损坏内容，写后复验全档。

用法：
  python -X utf8 Tools/tasks_board.py --check
  python -X utf8 Tools/tasks_board.py --append-file <utf8片段文件>
  Get-Content 片段 | python -X utf8 Tools/tasks_board.py --append-stdin
"""
import argparse
import os
import re
import sys

BOARD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks", "TASKS.md")

# 典型 UTF-8 被当成 GBK 再回写的乱码特征字（只用于新增内容体检，不改历史）
MOJIBAKE_MARKS = ("锛", "銆", "鐨", "鏉", "绔", "馃")

# ASCII 顶替（第三类损伤·R2392 判例）：正文中文被写成 '?'（编码通道降级为 ascii+errors=replace），
# 特征是整行零 CJK 且残留「??」连段——正常中文疑问句不会连写两个问号。
QMARK_RUN = re.compile(r"\?{2,}")


def read_board_bytes():
    with open(BOARD, "rb") as f:
        return f.read()


def ascii_mangled(text):
    """返回 (行号, '?' 连段数) 清单：整行零 CJK 且出现 >=2 段 '??' = ASCII 顶替候选。"""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        runs = QMARK_RUN.findall(line)
        if len(runs) < 2:
            continue
        if any("\u4e00" <= c <= "\u9fff" for c in line):
            continue
        hits.append((i, len(runs)))
    return hits


def diagnose(raw, label="board"):
    """返回问题清单；空列表=健康。"""
    problems = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return ["%s: 非 UTF-8 字节（偏移 %d: %s）" % (label, e.start, e.reason)]
    if text.startswith("\ufeff"):
        problems.append("%s: 带 BOM" % label)
    bad = text.count("\ufffd")
    if bad:
        problems.append("%s: 含 U+FFFD %d 处（正文已被替换字符吞掉）" % (label, bad))
    for mark in MOJIBAKE_MARKS:
        n = text.count(mark)
        if n:
            problems.append("%s: 疑似 GBK 乱码字 %r %d 处" % (label, mark, n))
    mangled = ascii_mangled(text)
    if mangled:
        nums = ",".join(str(n) for n, _ in mangled[:10])
        problems.append(
            "%s: %d 行疑似 ASCII '?' 顶替 CJK 正文（行 %s；编码通道降级为 ascii）"
            % (label, len(mangled), nums)
        )
    return problems


def check():
    problems = diagnose(read_board_bytes())
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    text = read_board_bytes().decode("utf-8")
    print(
        "OK tasks/TASKS.md: utf-8 无 BOM / U+FFFD=0 / 乱码字=0 / ASCII顶替=0 / 行数=%d"
        % (text.count("\n") + 1)
    )
    return 0


def append(chunk_bytes):
    if not chunk_bytes:
        print("FAIL 空片段，拒绝写入")
        return 2
    problems = diagnose(chunk_bytes, "new-chunk")
    if problems:
        for p in problems:
            print("FAIL", p)
        print("FAIL 片段本身不健康，拒绝写入（正法：源文本以 UTF-8 读取，禁 gbk 解码后回写）")
        return 2

    raw = read_board_bytes()
    existing = diagnose(raw)
    if existing:
        for p in existing:
            print("FAIL", p)
        print("FAIL 现有任务板已损坏，先修复再追加")
        return 2

    chunk = chunk_bytes.decode("utf-8")
    tail = raw.decode("utf-8")
    sep = "" if tail.endswith("\n\n") else ("\n" if tail.endswith("\n") else "\n\n")
    merged = (tail + sep + chunk.strip("\n") + "\n").encode("utf-8")

    after = diagnose(merged)
    if after:
        for p in after:
            print("FAIL", p)
        return 2

    tmp = BOARD + ".tmp"
    with open(tmp, "wb") as f:
        f.write(merged)
    os.replace(tmp, BOARD)
    print("OK 追加完成：+%d 字节，行数=%d" % (len(chunk_bytes), merged.decode("utf-8").count("\n") + 1))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--append-file")
    ap.add_argument("--append-stdin", action="store_true")
    args = ap.parse_args()

    if args.check:
        return check()
    if args.append_file:
        with open(args.append_file, "rb") as f:
            return append(f.read())
    if args.append_stdin:
        data = sys.stdin.buffer.read()
        return append(data)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())