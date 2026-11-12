# 派生面内容级漂移审计（T-20261112-04 同族补全）

- 轮次：R2595 · 2026-11-12 14:2x · @BigLife-OSLoop
- 窗位：CEO 用机让路窗（machine-state paused 13:04 · D-20261020-02 09:00-19:00 结构性让路）
- 性质：确定性零 LLM 零 GPU · 单轮 llm=0

## 一、病根（实测发现）

round_daily v0.5 只给 `citizen-goals.jsonl` 一个派生面加了闸，其余七个 R3 派生面
**无任何轮次引用**，盘面实测停在 10-26/10-27：

| 派生面 | 盘上 mtime | 滞后 | 依赖的可见面 |
|---|---|---|---|
| citizen-anchors.jsonl | 2026-10-27 18:49 | 16d | city-map.html |
| citizen-assembly.jsonl | 2026-10-27 18:49 | 16d | （FluxVerse M2 外部消费） |
| citizen-persona.jsonl | 2026-10-27 15:43 | 16d | city-ops.html |
| citizen-relations.jsonl | 2026-10-26 16:41 | 17d | city-relations.html / city-growth.html |
| citizen-voice.jsonl | 2026-10-26 15:26 | 17d | city-growth.html |
| citizen-initiatives.jsonl | 2026-10-26 15:28 | 17d | city-life.html |
| citizen-atlas.jsonl | 2026-09-24 21:57 | 49d | （FluxVerse M2 外部消费） |

而这些可见面当日全部照常重建（10:06 / 01:12）⇒ **页面 mtime 是今天的，读到的数据是半个月前的**
——与 T-20261112-04「页面新鲜/数据陈旧」同一病灶的第二批受害者。

## 二、为什么不能照搬 mtime 闸

七个面均为 `md5(id)` 确定性派生（各生成器头注释自带「双跑字节一致」契约）。
输入不变时再生结果逐字节相同，若按「当日必新」判，等于每天白写 190MB
（relations 2.85M 行 / 285 万边）却零信息。故新闸判**内容漂移**而非 mtime。

## 三、实测漂移（本轮再生比对）

| 派生面 | 再生耗时 | md5 前→后 | 判定 |
|---|---|---|---|
| citizen-anchors.jsonl | 0.3s | 4C6E4EE9→4C6E4EE9 | SAME |
| citizen-assembly.jsonl | 0.3s | E98241D0→E98241D0 | SAME |
| citizen-persona.jsonl | 3.2s | E0C3E093→E0C3E093 | SAME |
| citizen-voice.jsonl | 0.3s | 926BE7EA→926BE7EA | SAME |
| citizen-atlas.jsonl | 0.3s | A7D02D15→**EE5A682B** | **DRIFT** |
| citizen-initiatives.jsonl | 0.5s | D25D45B3→**FAE7C2A3** | **DRIFT** |
| citizen-relations.jsonl | 14.5s | 重写 2851580 行（block 2832760/buddy 15131/household 3629/meet 60） | 已再生 |

结论：**atlas 与 initiatives 是真实内容漂移**（页面此前读的是旧画像/旧意向），
其余五个只是 mtime 陈旧、内容未变 —— 这正是「mtime 闸会误判」的实证。

## 四、修法与接线

- 新工具 `Tools/derive_audit.py` v1.0：逐个再生派生面 → 比对 md5 → 判定
  SAME/DRIFT/CREATED/ERROR → **仅在漂移时**重建 dependents（调用
  `round_daily --run --only <面键>`）；输出 `state/derive-audit.json`。
- 接线：`round_daily.py` v0.6 的 INPUTS 档新增 `derive_audit`（data tier，`--run`），
  先于可见面重建执行 ⇒ 此后每轮自动审计，不再依赖人偶然发现。

## 五、验证

正控（注入漂移）：向 citizen-voice.jsonl 追加一行 `{"id":"TAMPER","drift":"probe"}`
→ 审计报 `voice DRIFT` + `verdict: DRIFT drifted=2 rebuilt=growth`；
同时 assembly 因依赖 atlas 换新连带 DRIFT（依赖链正确传播），growth 面按漂移重建。

负控（陈旧检出）：回拨 `state/derive-audit.json` mtime −2d
→ `round_daily --check` 报 `outdated:2d stale=1`；`--run --only derive_audit` 报 `rebuilt`。

幂等：二次跑全部 SAME、`verdict: PASS drifted=0`；注入脏行已被再生抹除
（citizen-voice.jsonl md5 复原 926BE7EA，anchors 4C6E4EE9 / persona E0C3E093 不变）。

自检：`derive_audit.py --selftest` 4/4 PASS（MISSING / 同内容 / 改内容 / 改回复原）。
门禁：`py_compile` rc=0；`ruff_gate` 2 file CLEAN(F401,F811,F841,SIM115,RUF059)。

## 六、诚实边界

1. 本轮只保证「派生面内容与可见面读数一致」，不保证派生规则本身正确
   （如 relations 的 285 万边分布是否合理，属关系模型面，未在本轮判定）。
2. relations 全量再生 14.5s 但写盘 190MB —— 若后续高频轮次触发，属磁盘写放大；
   当前漂移日才重建依赖面，稳定日只付 16s 读盘。
3. atlas/assembly 无本仓可见面消费（面向 FluxVerse M2 外部），其漂移只进报告，
   不产生页面动作；对外一致性依赖 M2 侧按需再生（T-20260923-01 通知面口径不变）。
4. 未做 LLM/GPU 任何调用（让路窗），不涉及年轮/相遇/反思文本质量。
