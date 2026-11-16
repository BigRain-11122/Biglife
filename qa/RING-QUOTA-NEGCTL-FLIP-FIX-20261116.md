# 配额闸 A/B 工装·补丁翻转缺陷修复与假绿闸（R3246·2026-11-16）

关联：T-20261116-13（19:00 实弹执行单）／T-20261115-04（换靶线·12h 全城开口配额闸）

## 1. 缺陷（会让 19:00 窗口白烧）

`state/pending/R3204-quota-gate.patch` 已于 **2026-11-16 14:23 commit efc562b9f** 入 HEAD。
但 `Tools/ring_quota_negctl.py` 的 main 流程仍按「补丁待打」前提编排：

1. `patch_applied()` 返回 True（代码里已有 `citywide-refusal-ban`）→ 直接判 `ok=True`；
2. 打印 `arm A (patch OFF)` 后 **不撤补丁就跑了 A 臂** → A 臂实测的是「闸已生效」的行为；
3. A 臂跑完才 `git apply PATCH` → 补丁已在库里，`git apply` 必然失败 → `return 2` 中止。

结果：A 臂烧掉 5 席 LLM 产出、B 臂从未开跑、无 verdict、窗口作废；且报告里 A 臂会被
贴成「补丁=否」，读数含义被写反。

实证：`git apply --check` → `patch does not apply`（RC=1）；`git apply -R --check` → RC=0
（反向撤退干净，说明只是编排逻辑错，不是补丁损坏）。

## 2. 修法（编排层·不动任何闸阈值/族表）

- 新增纯函数 `patch_steps(started_applied) -> (A 臂态, B 臂态, 收尾态)`
  = `(False, True, started_applied)`：A 臂恒「未生效」、B 臂恒「生效」、收尾回起跑态——
  与补丁来自工作树还是已入 HEAD 无关。
- 新增幂等设态 `_set_patch(desired)`：已达目标态直接返回 `already ...`，否则走
  `git apply` / `git apply -R`。
- main：A 臂前 `_set_patch(A 态)`（已入 HEAD 时=先反向撤回）→ 跑 A → `_set_patch(B 态)`
  → 跑 B → `finally` 恒还原到 `started_applied`（不再依赖 verdict 决定是否撤补丁）。
- 删去 `verdict_is_fail()`（其「按失败撤补丁」语义在补丁已入库的场景下会把已提交的闸
  撤回成脏工作树）。

## 3. 假绿闸（同轮发现·第二条）

旧 `judge()` 只要满足「B 落环 ≥ A」「命中率 ≤30%」「复读面未升高」即判 PASS。
**B 臂零命中时这三条会全部满足**——闸一次都没开火，却输出 PASS，等于「用没开过火的闸
证明闸可用」。H2 场景（等全部禁牌到期后再跑，snap 两臂皆空）必踩。
修法：`ok` 且 `b.ban_hits == 0` → 返回 **INCONCLUSIVE**（rc=1·不判 PASS），并在明细里写明
当时生效禁牌条数，供判「样本不足」还是「闸无靶」。

## 4. 负控与验证（全零 LLM）

| 面 | 命令 | 结果 |
|---|---|---|
| 编译 | `python -X utf8 -m py_compile Tools/ring_quota_negctl.py` | rc=0 |
| 回归电池 | `python -X utf8 Tools/ring_quota_negctl.py --selftest` | **PASS（0 fail·19 检）** |
| 补丁翻转实弹 | 临时脚本调 `_set_patch(False)`→`_set_patch(False)`→`_set_patch(True)`→还原 | revert rc=0（applied=False）／幂等第二次回 `already reverted`／reapply rc=0（applied=True）／`git status` 回到仅本轮自有改动（`Tools/evolve_citizen.py` 无残留） |
| 编排可读面 | `--dry-run` | 新增 `patch plan: 起跑=applied A 臂=reverted B 臂=applied 收尾=applied` |

电池新增 6 检：`patch_steps` 两态、A 臂恒 off、B 臂恒 on、零命中→INCONCLUSIVE、零命中≠PASS。

## 5. 19:00 执行协议（更新后）

```
python -X utf8 Tools/ring_quota_negctl.py        # 先跑本单，再跑常规年轮批
```

- 补丁无需手动打/撤，工具自管；`state/pending/R3204-quota-gate.patch` 仅作反向撤退依据，
  **不要再手动 `git apply`**。
- 禁牌混淆窗：`--dry-run` 实测 active=10、soonest_expiry=**19:14**、latest=20:45。
  两臂须在 19:14 前跑完，否则判 CONFOUNDED（数据不可用于裁决，非补丁之过）。
- 每臂席位由 due 自动收敛（当前 due=10 → 每臂 5），勿加 `--batch` 抬高。
- verdict 语义：`PASS`=补齐可用；`FAIL`=三硬线任一破（工具自动还原补丁态）；`INCONCLUSIVE`=
  零命中、本批无判别力，需在有生效禁牌且样本够时重跑，**不得当通过用**。
