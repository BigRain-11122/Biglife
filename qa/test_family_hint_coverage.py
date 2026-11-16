#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""R3226 (2026-11-16, T-20261115-04 同源): 族表 ↔ 人话 hint 覆盖契约闸。

病根（R2789 判例复发）：``ring_open_family.FAMILIES`` 是闸的族表，
``evolve_citizen.FAMILY_OPEN_HINTS`` 是喂给 4B 的人话说明。两表靠人手同步，
族表扩了而 hint 没跟 → 渲染点 ``FAMILY_OPEN_HINTS.get(f, f)`` 把英文族名
（``WIND_AGENT_OPEN``）当"人话"拼进提示词，模型读到机器码，既不知被禁什么，
又必然重入同族。2026-11-16 实测：当日 25 条拒稿里 ``WIND_AGENT_OPEN`` 11 条
（44%）为最大单一族，正落在这个空档里。

正负控：
  正控 1 族表每族都有 hint（族表 12 族，缺一族即红）；
  正控 2 hint 是人话（不含 ``下划线连写大写标识`` 机器码形态）；
  正控 3 hint 不照抄示例句（``PROMPT_EXAMPLE_ECHO`` 任一整句不得出现在 hint 里，
         否则 hint 自己变成 canned 句，R2760 判例）；
  负控   用虚构族名走一遍检测器 → 必须判红（证明本测试真能抓该缺陷形态）。

零 LLM / 零 GPU / 确定性。运行：python -X utf8 qa/test_family_hint_coverage.py
"""
import ast
import io
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "Tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import ring_open_family as rof  # noqa: E402  (轻量：仅 stdlib)

EVOLVE = os.path.join(TOOLS, "evolve_citizen.py")

# 机器码形态：ALL_CAPS_WITH_UNDERSCORES（族名原文的样子）
MACHINE_CODE = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")


def _const(node):
    """AST 常量求值：Constant / BinOp(+) / Dict / Tuple / List。"""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Dict):
        out = {}
        for k, v in zip(node.keys, node.values):
            out[_const(k)] = _const(v)
        return out
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_const(e) for e in node.elts)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _const(node.left) + _const(node.right)
    if isinstance(node, ast.JoinedStr):
        raise ValueError("f-string not supported in this contract test")
    raise ValueError("unsupported node: %s" % type(node).__name__)


def load_module_consts(path, names):
    """从源文件静态取模块级常量（不 import，避开 ollama 等运行期依赖）。"""
    with io.open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in names:
                    found[tgt.id] = _const(node.value)
    missing = names - set(found)
    if missing:
        raise AssertionError("常量未找到：%s" % sorted(missing))
    return found


def machine_codes_in(text):
    return MACHINE_CODE.findall(text or "")


class FamilyHintCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        consts = load_module_consts(
            EVOLVE, {"FAMILY_OPEN_HINTS", "PROMPT_EXAMPLE_ECHO"})
        cls.hints = consts["FAMILY_OPEN_HINTS"]
        cls.echoes = consts["PROMPT_EXAMPLE_ECHO"]
        cls.families = list(rof.FAMILIES.keys())

    # 正控 1 ---------------------------------------------------------------
    def test_every_family_has_hint(self):
        missing = [f for f in self.families if f not in self.hints]
        self.assertEqual(
            missing, [],
            "族表里有族没登记人话 hint（会被 .get(f, f) 当机器码拼进提示词）：%s"
            % missing)

    def test_no_orphan_hint(self):
        """反向：hint 表不得含族表里不存在的族（改名残留会让测谎失真）。"""
        orphans = [k for k in self.hints if k not in self.families]
        self.assertEqual(orphans, [], "hint 表含族表外族名：%s" % orphans)

    # 正控 2 ---------------------------------------------------------------
    def test_hints_are_human_readable(self):
        bad = {}
        for fam, text in self.hints.items():
            codes = machine_codes_in(text)
            if codes:
                bad[fam] = codes
        self.assertEqual(bad, {}, "hint 里出现机器码形态：%s" % bad)

    def test_hints_not_empty(self):
        empty = [k for k, v in self.hints.items() if not (v or "").strip()]
        self.assertEqual(empty, [], "空 hint：%s" % empty)

    # 正控 3 ---------------------------------------------------------------
    def test_hints_do_not_copy_example_sentences(self):
        """hint 不得内嵌 PROMPT_EXAMPLE_ECHO 的整句（否则 hint 自己成 canned 句）。"""
        leaked = {}
        for fam, text in self.hints.items():
            hits = [e for e in self.echoes if e and e in text]
            if hits:
                leaked[fam] = hits
        self.assertEqual(leaked, {}, "hint 照抄示例句：%s" % leaked)

    # 负控 -----------------------------------------------------------------
    def test_detector_catches_missing_hint(self):
        """负控：虚构族名（未登记）必须被判为缺失。"""
        fake = self.families + ["PHANTOM_FAMILY_FOR_NEGCTL"]
        missing = [f for f in fake if f not in self.hints]
        self.assertIn("PHANTOM_FAMILY_FOR_NEGCTL", missing)
        # 且它落到渲染点会真的吐出机器码
        rendered = self.hints.get("PHANTOM_FAMILY_FOR_NEGCTL",
                                  "PHANTOM_FAMILY_FOR_NEGCTL")
        self.assertTrue(machine_codes_in(rendered))

    def test_detector_catches_machine_code_hint(self):
        """负控：把 hint 写成族名原文 → 人话检测必须红。"""
        # 刻意构造缺陷样本（不取真实 hint，否则削弱负控强度）
        broken_hints = {"WIND_AGENT_OPEN": "WIND_AGENT_OPEN"}
        bad = {f: machine_codes_in(t) for f, t in broken_hints.items()
               if machine_codes_in(t)}
        self.assertIn("WIND_AGENT_OPEN", bad)

    # 第二句吸引子面（R3228：与开头族同型的双表同步坑）-------------------
    def test_second_attrs_have_label(self):
        """SECOND_ATTRS 增族而 SECOND_LABELS 未跟 → 同样漏机器码进提示词。"""
        missing = [f for f in rof.SECOND_ATTRS if f not in rof.SECOND_LABELS]
        self.assertEqual(missing, [], "第二句吸引子族缺 label：%s" % missing)

    def test_second_labels_are_human_readable(self):
        bad = {f: machine_codes_in(t) for f, t in rof.SECOND_LABELS.items()
               if machine_codes_in(t)}
        self.assertEqual(bad, {}, "第二句 label 出现机器码形态：%s" % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
