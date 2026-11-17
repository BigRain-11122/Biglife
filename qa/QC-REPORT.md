# QC 证据卡（qa/）

**正身产物 = `census/QC-REPORT.md`（由 `Tools/qc_census.py` 生成，随轮入库）**；本文件只登记本轮实测数字与配套闸结论，不重复正文。

## 2026-11-14 05:52 @BigLife-OSLoop

| 项 | 实测 |
|---|---|
| `qc_census.py` | cards=10114 / evolved=10114 / problems=0 / dup_rings=37/37 → PASS |
| `events_refresh.py --gate` | cards=10111 events=43131 shards=3 / replayed=10111 / schema_errors=0 / mismatch=0 → PASS；unexpected_missing=0 |
| `round_daily.py --run` | stale=2 ran=3 failed=0 → PASS（重建 city-dashboard.html / gene-ledger.html / index.html） |
| `pool_audit.py` | verdict=PASS，under_target: NONE - SELF_TERMINATE（全桶达标） |

结论：本日 QC 全项 PASS，无新增异常，不立修复单。

## 2026-11-15 07:5x @BigLife-OSLoop (R3048)

| 项 | 实测 |
|---|---|
| `qc_census.py` | cards=10114 / evolved=10114 / problems=0 / dup_rings=37/37 -> PASS (与 11-14 基线同值，无新增异常) |
| `events_refresh.py --gate` | cards=10111 events=44224 shards=3 / replayed=10111 / schema_errors=0 / mismatch=0 -> PASS；coverage unexpected_missing=0，chronicle gap=0d |
| `round_daily.py --run` | stale=12 ran=13 failed=0 -> PASS (dashboard/voices/coverage/ops/objects/goals/gene_ledger/growth/meets/reflections/meet_candidates/index 重建) |
| `pool_audit.py` | verdict=PASS，under_target: NONE - SELF_TERMINATE (轴 72/72·像素 12/12·greet 28/28·faq 7/7·负例 6/6) |
| `rings_recount.py (本轮新增)` | 机器直数行=357 居民=355，心跳 350，delta=+7 = 本轮落环 7 席 -> OK (R3042 计数口径单结案) |

结论：本日 QC 全项 PASS，无新增异常，不立修复单；R3042/R3043/R3044 计数口径单以 rings_recount.py 账面证据结案。

## 2026-11-15 21:4x @BigLife-OSLoop (R3134)

| 项 | 实测 |
|---|---|
| `evolve_citizen.py --batch 3` | evolved=10/10 due (written=10 skipped=0)；gate soft-concession 4 席（recent-dup-phrase/opening 自动降级落环）；新居民 0（既有迭代） |
| `events_refresh.py --gate` | cards=10111 events=44982 shards=3 / replayed=10111 / schema_errors=0 / mismatch=0 -> PASS；coverage unexpected_missing=0，chronicle gap=0d |
| `round_daily.py --run` | stale=13 ran=14 failed=0 -> PASS（objects/goals/gene_ledger/growth/meets/reflections/meet_candidates/index + 分页面重建） |
| `persona_generations.py --check` | rc=0，gen 2 / cutoff C-10120 / habits=138 / pending_sync=none |
| `pool_audit.py` | verdict=PASS，under_target: NONE - SELF_TERMINATE（轴 72/72·像素 12/12·greet 28/28·faq 7/7·负例 6/6；determinism mismatch=0） |
| `reflect_citizen.py --batch 5` | daily-cap: 今日已写 3 条（上限 1 趟/夜）-> 跳过，健康 |
| `evolve_citizen.py --meet` | meet-cap: 今日已 3 场（上限 3）-> 跳过 |
| `qc_census.py` | cards=10114 / evolved=10114 / problems=0 / dup_rings=37/37 -> PASS |

结论：本日 QC 全项 PASS，无新增异常，不立修复单；年轮/事件/日更/世代/池六线全绿，反思与相遇按日限自停。
## 2026-11-16 02:5x @BigLife-OSLoop (R3158)

| 项 | 实测 |
|---|---|
| `evolve_citizen.py --batch 3` | llm-starved：warm probe 60s 无应答（gpu 11752/12282 MiB，free 530）→ batch skipped，0 席位燃烧（T-20261114-05 让路闸生效） |
| `round_daily.py --run` | stale=1 ran=2 failed=0 -> PASS（重建 ops / index） |
| `persona_generations.py --check` | rc=0，gen 2 / cutoff C-10120 / habits=138 / pending_sync=none |
| `pool_audit.py` | verdict=PASS，under_target: NONE - SELF_TERMINATE（轴 72/72·像素 12/12·greet 28/28·faq 7/7·负例 6/6；determinism mismatch=0） |
| `qc_census.py` | cards=10114 / evolved=10114 / problems=0 / dup_rings=37/37 -> PASS（与基线同值，无新增异常） |
| `reflect_citizen.py` | 不在夜窗（02:53 < 19:00）→ 未启 |

结论：日更/世代/池/QC 四线 PASS；年轮线因桌面占用显存让路零损耗跳过，非故障；不立修复单。

## 2026-11-17 11:2x @BigLife-OSLoop (R3347)

| 项 | 实测 |
|---|---|
| `evolve_citizen.py --batch 3` | yield-window（工作日 09:00-19:00·D-20261020-02）→ 顺延夜窗 |
| `round_daily.py --run` | 38 面 skipped-fresh / stale=0 / ran=0 / failed=0 -> PASS |
| `persona_generations.py --check` | rc=0，gen 8 / cutoff C-10120 / habits=170 / pending_sync=none |
| `pool_audit.py` | verdict=PASS，under_target: NONE - SELF_TERMINATE（轴 72/72·像素 12/12·greet 28/28·faq 7/7·负例 6/6；determinism mismatch=0） |
| `events_refresh.py --gate` | cards=10111 / events=46181 / replayed=10111 / schema_errors=0 / mismatch=0 -> PASS |
| `qc_census.py` | cards=10114 / evolved=10114 / problems=0 / dup_rings=37/37 / meet_new_bad=0 / 相遇面 169 行 167 对（单向 1·重复 2 均早于门限日·不回溯改卡） |

结论：全项 PASS，无新增异常，不立修复单；年轮/相遇/反思三维受工作日让路闸约束顺延 19:00，非故障。
