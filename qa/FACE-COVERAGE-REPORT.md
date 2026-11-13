# 面覆盖自动发现报告（2026-11-13 11:19:33）

> 零 LLM 只读扫描。判据=「Tools 里有生成器字面量、盘上有产物、但 round_daily 登记表里没有它」。登记表是唯一权威，本报告只做差集。

- 已登记面：35
- 扫描候选产物名：134
- 未登记且超 1 天：**0**
- 未登记但新鲜：3
- append-only 台账供料缺口：2
- 未登记且盘上无产物：30（其中**未解释 0**）

## 未登记但新鲜（窗口内，观察）

- 0.0d `EVENTS-REPLAY-REPORT.md` <= events_replay.py
- 1.0d `MEET-SYMMETRY-REPORT.md` <= meet_asymmetry_scan.py
- 0.1d `RING-SIMILE-REPORT.md` <= ring_simile_audit.py

## append-only 台账供料缺口

> 按上游事件增长，不是按日重建的确定性面——本表只报事实与上游，不自动重建（重建会写假行）。年龄大＝该线上游已停产。

| 静默 | 台账 | 最后追加 | 生成器 |
|---|---|---|---|
| 19.6 天 | `proposals.jsonl` | 2026-10-24 20:03 | evolve_citizen.py, political_redline.py |
| 1.4 天 | `city-chronicle.jsonl` | 2026-11-12 02:25 | city_chronicle.py, events_refresh.py |

## 盘上无产物候选（已归因）

> 归因只解释「为什么不落盘」，不改判据。**unexplained 非零＝真缺口，必须人看**；新候选落不进任何一类就会出现在这里。

- 分类计数：external-readonly=2／inert-input=25／placeholder=3

**unexplained = 0**（当前无真缺口，本轮无动作）

