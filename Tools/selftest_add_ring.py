# -*- coding: utf-8 -*-
"""T-20261114-02 落环返回值自测（零 GPU / 零网络 / 临时目录）。

验四件：
  A. 成功落环 -> add_ring() 返回 True（补齐前是 None，批调用方按拒写处理）
  B. 同日二次落环 -> 返回 False 且卡面字节不变（幂等闸仍然有效）
  C. 带内部事件码的行 -> 返回 False 且零写入（出生地拦截）
  D. 带 latin 机器词的行 -> 返回 False 且零写入

跑法：python -X utf8 Tools/selftest_add_ring.py   （rc=0 = 全绿）
"""
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evolve_citizen as ec  # noqa: E402

fails = []


def _check(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + name + " - " + detail, flush=True)
    if not ok:
        fails.append(name)


CARD = """# C-99999 测试居民

**人设**
测试用卡面，非真实居民。

**年轮**
- 2026-11-13 「昨天的一句话，写在这里做基数。」 [锚] 测试锚

**进化** v0.1 · 出生 2026-09-23 · 年轮 1 圈 · 锚定律见 docs/CODEX.md §九
"""


def _mk(tmp, name="C-99999.md"):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(CARD)
    return p


def _bytes(p):
    with open(p, "rb") as f:
        return f.read()


def case_a_b(tmp):
    p = _mk(tmp)
    ret = ec.add_ring(p, "C-99999", "今早把炉子重新点着了，火苗比昨天稳。", "测试锚")
    text = open(p, encoding="utf-8").read()
    today = ec.today()
    _check("A return-true", ret is True, "add_ring() -> %r" % (ret,))
    _check("A ring-landed", text.count("- %s " % today) == 1,
           "today ring lines = %d" % text.count("- %s " % today))
    m = re.search(r"\*\*进化\*\* v1\.(\d+)", text)
    _check("A ring-count", bool(m) and m.group(1) == "2",
           "进化 v1.%s (expect 2)" % (m.group(1) if m else "?"))
    before = _bytes(p)
    ret2 = ec.add_ring(p, "C-99999", "今早把炉子重新点着了，火苗比昨天稳。", "测试锚")
    _check("B dup-returns-false", ret2 is False, "second add_ring() -> %r" % (ret2,))
    _check("B bytes-unchanged", _bytes(p) == before,
           "card bytes %s" % ("unchanged" if _bytes(p) == before else "MUTATED"))


def case_c(tmp):
    p = _mk(tmp, "C-99998.md")
    before = _bytes(p)
    ret = ec.add_ring(p, "C-99998", "今早数了数柜上的 S12 罐子，还是那些。", "测试锚")
    _check("C event-code-refused", ret is False, "add_ring() -> %r" % (ret,))
    _check("C no-write", _bytes(p) == before,
           "card bytes %s" % ("unchanged" if _bytes(p) == before else "MUTATED"))


def case_d(tmp):
    p = _mk(tmp, "C-99997.md")
    before = _bytes(p)
    ret = ec.add_ring(p, "C-99997", "今早 commit 了一遍心里的事，像擦桌子。", "测试锚")
    _check("D latin-refused", ret is False, "add_ring() -> %r" % (ret,))
    _check("D no-write", _bytes(p) == before,
           "card bytes %s" % ("unchanged" if _bytes(p) == before else "MUTATED"))


tmp = tempfile.mkdtemp(prefix="addring-")
try:
    case_a_b(tmp)
    case_c(tmp)
    case_d(tmp)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("verdict: %s (%d fail)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(0 if not fails else 1)
