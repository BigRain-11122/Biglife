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

---

# 追加（R3247·同日 17:4x）：两臂禁牌快照冻结——把「19:14 悬崖」从时间压力改成构造保证

## 6. 为什么还要改

R3242 的席位预算闸只治「席位不足」，而同一族的第二个污染源没治：**禁牌在 A→B 之间到期**。
实读 `--dry-run`：active=10、soonest_expiry **19:14**、latest 20:45。旧设计要求两臂都跑在
19:14 之前，否则判 CONFOUNDED——即把「实验有效性」押在「两臂能否在 14 分钟内跑完」这个
不确定量上（每臂 5 席，任一处重试就会跨点，跨点=整窗作废）。

正确解法不是预测耗时，而是**消除变量**：让两臂看到逐字相同的禁牌集合。

## 7. 改法（默认开启·默认路径零改变）

- `Tools/evolve_citizen.py` 新增纯函数 `parse_frozen_bans(raw)` 与取面函数
  `load_refusal_bans(env_path=None)`：env `BIGLIFE_REFUSAL_BANS_FROZEN` 指向快照则用快照，
  **未设时逐字回落到 `recent_refusal_bans()`**（生产行为不变）。
- 调用点打印可证伪来源标记：`refusal-bans source: frozen|live-12h n=N`。
- `Tools/ring_quota_negctl.py`：新增 `freeze_bans_file()`（起跑时把 active 禁牌写成 JSON
  快照）、`--no-freeze`（仅用于复核冻结面本身）、`_run(..., env=)`／`arm(..., env=)` 传环境；
  两臂共用同一快照，`finally` 删临时文件。
- 判据加硬校验：两臂来源必须同为 `frozen` 且 `n` 相等，否则判 CONFOUNDED（防「以为冻了其实没冻」）。
  报告新增一行「禁牌快照：冻结 N 条（两臂共用同一集合·不受到期点约束）」。

## 8. 负控（全零 LLM·23 检 PASS）

| 面 | 读数 |
|---|---|
| `--selftest` | **PASS（0 fail·23 检）**，新增 4 检：`parse_frozen_bans` 正常解析／坏值跳过／快照文件可读／`load_refusal_bans` 走快照且无损 |
| 冻结实弹 | `frozen n=10`；`load_refusal_bans(env_path=快照)` 与 `recent_refusal_bans()` **逐键相同**；env 未设回落结果**亦相同**（默认路径未受污染） |
| 生产面零回归 | `evolve_citizen --audit-due` → `due=10 leaked=0 PASS`（rc=0）；`py_compile` 两文件 rc=0 |
| 起点修复未回退 | `patch_steps`／`_set_patch` 四检仍 PASS |

## 9. 效果与诚实边界

- 效果：19:00 实弹**不再受 19:14 到期点约束**，B 臂零命中的概率也下降（冻结集合里 12h 内被拒的
  开口仍被拦），即同时缓解第 3 节的 INCONCLUSIVE 陷阱。
- 边界一：冻结态是「实验臂配置」，比生产实时窗口**更严**（本已解禁的开口仍算禁）——报告里
  写明「冻结 N 条」，不得当作生产口径读数。
- 边界二：`refusal-bans source:` 这行只在真正进入年轮批时打印，让路窗内无法实跑验证其输出；
  已验证的是其取数函数两侧（冻结／实时）与回落路径，标签行属 3 行常量拼接（compile 已过）。
- 边界三：本轮仍未跑实弹，配额闸留/撤**仍未裁决**。

## 10. 自查补丁（同窗发现冻结与判据自相矛盾·已修）

首版冻结只改了「喂给两臂的集合」，却把 `judge()` 的墙钟比对原样留着：冻结下两臂本该
**按构造**同集，但 `snap_a`／`snap_b` 仍各取一次墙钟禁牌集合——任何禁牌在两臂之间到期，
判据就会把**有效读数**判成 CONFOUNDED，等于冻结白做。

修法：`judge(..., frozen=True)` 时跳过到期/携带判定，改记
`ok 两臂禁牌集合按快照冻结共用（n=N·墙钟到期混淆不适用）`；`main` 按 `bool(freeze_path)` 传入。
另把来源校验改为**只在该校验可知时生效**（两臂标签均为已知值才比对），标签缺失时降级为
一行 note 而不是判 CONFOUNDED——避免「stdout 吞行」把好数据判废。

负控 2 检（现共 **25 检 PASS**）：
`judge 冻结下不按墙钟到期判混淆`（same vs expired，frozen=True → **PASS**）、
`judge 非冻结下到期仍判 CONFOUNDED`（同输入 frozen=False → **CONFOUNDED**）。

## 11. 端到端走真 main 路径（桩 LLM 臂·零盘污·E2E PASS）

`--dry-run` 在「建冻结快照」之前就 return，故该段（快照生成→env 传给两臂→来源校验→
报告写入→finally 删快照）从未被执行过；这正是 19:00 最可能炸的地方。用桩件跑真 `main()`：

- 桩：`arm()` 返回固定读数（written=5／ban_hits=1／ban_src=frozen／ban_n=读快照文件行数），
  `_set_patch()` 返回成功不落盘，`QA` 指向 `tempfile.mkdtemp()`，`sys.argv` 无开关。
- 读数：`rc=0`；**A/B 两臂收到同一快照路径且非空**（同路径=True）；快照条数 **10/10**；
  **快照已清理=False 的否定式**＝文件确实被 finally 删除；报告落到临时目录且含「禁牌快照」行；
  报告末行 `**verdict: PASS**　补丁终态=生效（= 起跑前状态·工作树无残留改动）`；
  明细含 `ok 两臂禁牌集合按快照冻结共用（n=10·墙钟到期混淆不适用）`。
- **E2E_CHECK PASS**；跑后 `git status` 净（未触碰真 qa/、未动机补丁态）。
- 仍存的缺口（如实）：`arm()` 被桩替换，故「真子进程收到 env 后是否按 frozen 打印」这一步
  仍属未验；但 `load_refusal_bans()` 两侧取值与回落已单测，且 E2E 证实 env 键与路径正确到达。



