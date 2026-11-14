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
