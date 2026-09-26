# AGENCY —— 自发性与行动意图契约 v1.0（九维第③维·agency v0）

> 溯源：CEO 调研落实令 2026-09-26 ~09:4x「去落实调研内容」（orders/O-20260926-0942-bm-c）；R-20260925-resident-full-intelligence §二第③维（自主性=最大缺口）+§五应用表第 2 行；研究正源=GOAP 式「需求→目标→行动」（M 级稳定惯例·工程化为确定性模板）。
> 定位：**每日自发动作清单**——GOAP 的确定性轻量实现：needs 强度（needs.py 现役面）→ 轴目标 → 动作模板（带 persona 个性化填色）。
> **与行为面五环互补分界（防双建）**：behavior.py=「此刻在哪」（位置状态·循环 v3.18~3.21 五环）；agency=「今天打算」（意图清单）。意图句=计划非断言（C-0012 判别式族）——不携带天气/时段/天体/场次/信号灯任何状态声称（模板池静态过 GATE_TOKEN 扫描）。

## 一、派生律（确定性·md5(id+date)·零 LLM 零云端）

- **崩溃态优先**：needs.crash 非空 → 恢复类动作池（律八③ 恢复叙事同源）。
- **常态**：top 轴（强度 ≥1）→ 主动作 1 条；第二强轴（≥1）以 50% 哈希概率加次动作（≤2 条/日）。
- **零强度日**：温和默认动作 1 条（五环不断链）。
- **个性化**：{likes} 用画像 v2 喜好填色；1/3 概率带句式 tic 前缀（persona 面）。
- **荣誉席 C-00001~03：blocked 不派生**（三面全 blocked 律）。

## 二、产线件

- 引擎=`Tools/agency.py`（needs/persona R3 面缺席自动重生·契约同 behavior.py 族）。
- 输出=`census/export/citizen-initiatives.jsonl`（**R3 再生面**·gitignored·按需跑 ~5s·字段=id/date/top/crash/initiatives[1-2]/blocked）。

## 三、判据（--qc 内建·机器可验）

1. rows=10003·blocked=3·活跃 10000 全带 1-2 条动作。
2. 每条 4-36 字·模板池静态扫描零 GATE_TOKEN（雨/雪/月/星/台风/开盘/收盘/今早/今晚/今夜/深夜）。
3. 同 (id,date) 双跑逐字节一致；崩溃态必为恢复池动作。

## 四、消费方

城市播报层「今日打算」段（city_broadcast 可选接入）｜CityWatch 居民档案页｜M2 NPC 日程意图｜QA 问答可引用（喂入面可选）。

## 五、验收实录

- 2026-09-26（调研落实批·bm-c 会话）：首跑 rows=10003·QC PASS；证据=本批 commit+播报层样例行。
