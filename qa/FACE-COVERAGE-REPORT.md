# 面覆盖自动发现报告（2026-11-17 13:09:06）

> 零 LLM 只读扫描。判据=「Tools 里有生成器字面量、盘上有产物、但 round_daily 登记表里没有它」。登记表是唯一权威，本报告只做差集。

- 已登记面：44
- 扫描候选产物名：157
- 未登记且超 1 天：**0**
- 未登记但新鲜：2
- append-only 台账供料缺口：1
- 未登记且盘上无产物：38（其中**未解释 5**）

## 未登记但新鲜（窗口内，观察）

- 0.0d `EVENTS-REPLAY-REPORT.md` <= events_replay.py
- 0.1d `RING-SIMILE-REPORT.md` <= ring_simile_audit.py

## append-only 台账供料缺口

> 按上游事件增长，不是按日重建的确定性面——本表只报事实与上游，不自动重建（重建会写假行）。年龄大＝该线上游已停产。

| 静默 | 台账 | 最后追加 | 生成器 |
|---|---|---|---|
| 0.5 天 | `proposals.jsonl` | 2026-11-17 01:05 | build_city_proposals.py, evolve_citizen.py, political_redline.py |

## 盘上无产物候选（已归因）

> 归因只解释「为什么不落盘」，不改判据。**unexplained 非零＝真缺口，必须人看**；新候选落不进任何一类就会出现在这里。

- 分类计数：external-readonly=2／inert-input=28／placeholder=3／unexplained=5

### unexplained（真缺口）

| 候选 | 生成器 |
|---|---|
| `a.md` | git_guard.py |
| `b.md` | git_guard.py |
| `new.md` | git_guard.py |
| `nonexistent.json` | ring_quota_negctl.py |
| `x.md` | git_guard.py |

