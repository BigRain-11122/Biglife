# 配额闸 A/B 工装三前置实装（T-20261116-13 收口件·2026-11-17）

## 背景（为什么必须修工装，而不是再跑一次）

`qa/RING-QUOTA-NEGCTL-20261117.md`（04:40 实弹）两臂读数是 **written=0 / done=0**，
摘要行 `(no summary line)`。旧 `arm()` 把「读不到摘要行」写成 `written=0`，于是：

- 「臂没产出」与「臂输出无法解析」在账面上**长得一样**；
- 两臂 0/0 被当成「退化但可比」，判成 INCONCLUSIVE —— 实际是 **工装故障**；
- 逐席拒稿理由（哪道闸挡了谁）全丢，只能重烧席位复现（R3290 判例）。

T-20261116-13 留单三个前置，本轮一次落地。

## 三项改动（`Tools/ring_quota_negctl.py`）

### ① arm stdout 落盘

`_dump_arm()` 新增：每臂 stdout/stderr 全文写 `state/negctl/arm-<YYYYMMDD>-<臂>.log`
（含 rc 行）。`arm(..., day=...)` 在实弹路径自动调用。

实弹验证（本轮 09:0x 冒烟）：

```
state/negctl/arm-20261117-A.log   193B
### day=2026-11-17 arm=A rc=0
### --- stdout ---
yield-window: workday 09:00-19:00 CEO lane-priority - evolve/meet/reflect deferred ...
```

### ② due 口径比对

`due_consistency(before, after, attempted)`：拒稿席也推 +1d（R3115），故「尝试」
即消耗 due。两臂跑完而 due 一个没减 → 席位供给与 `--audit-due` 不同源，
written 比对无解释力 → 判 `TOOLING_ERROR`，不裁补丁留撤。

### ③ TOOLING_ERROR 分型

- `arm()` 无摘要行时 `written/done` 返回 **None**（不再伪造成 0）；
- `judge()` 首段：任一臂 `written is None` → verdict=`TOOLING_ERROR`，并把
  该臂 rc + 输出尾部写进报告判据块，绝不当 PASS/FAIL 用；
- `main()` 判定链顺序改为：臂读数不可解析 → 关闸自证 → **due 口径** → 冻结面
  → 判据。避免把「读不到」说成 `CONFOUNDED`。

### 报告面新增

`qa/RING-QUOTA-NEGCTL-<day>.md` 增 `## 口径与原始输出（TOOLING_ERROR 可复现面）`：
due 口径行、A/B 臂日志指针；无摘要行时附该臂诊断尾部（≤1200 字）。

## 验收证据

| 项 | 命令 | 结果 |
|---|---|---|
| 编译 | `py_compile Tools/ring_quota_negctl.py` | rc=0 |
| 自检电池 | `--selftest` | **PASS (0 fail)**，含新增 7 检 |
| 席位预算 | `--dry-run` | due=10 → 每臂 5 席（请求 8，收敛） |
| 让路窗守卫 | 实弹 `--batch 8` | rc=3 `yield-window`，0 LLM / 工作树零写入 |
| 落盘实证 | 上述实跑后读日志 | `state/negctl/arm-20261117-A.log` 193B 含原文 |

新增自检项（此前无覆盖）：

- `judge 双臂无摘要行 -> TOOLING_ERROR` / `单臂 -> TOOLING_ERROR`
- `judge TOOLING_ERROR 不得冒充 PASS/FAIL`
- `due 一致(10->4) -> ok` / `due 未消耗(10->10) -> 不 ok` / `due 不可读 -> 不 ok`
- `report 含 due 口径行` / `含臂原始输出落盘指针` / `未落盘臂标 (未落盘)`
- `_dump_arm` 产出/内容/命名三检

## 状态（诚实边界）

- 三前置 **DONE**；T-20261116-13 剩余约束只到「实弹窗口」：本轮在 09:0x 让路窗内，
  A/B 不可跑（rc=3 已证），**实弹裁决仍待 ≥19:00 夜窗**（每臂 5 席，禁牌冻结 55 条）。
- 本轮**未**据此改动任何闸阈值或族表；不宣称闸有效性 PASS/FAIL。
