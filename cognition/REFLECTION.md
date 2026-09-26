# REFLECTION —— 高层记忆合成契约 v1.0（Generative Agents 反思腿·Phase3 拉前）

> 溯源：CEO 调研落实令 2026-09-26 ~09:4x（orders/O-20260926-0942-bm-c）；R-20260925-resident-full-intelligence §一文献锚【A 级】「synthesize higher-level reflections」直译件。
> 定位：居民记忆架构的中腿——**从自有年轮合成一句比单条记忆更高一层的感悟**。零编造构造：prompt 只喂自有环+人设壳，别无他物。
> 与年轮分界：年轮=[锚] 事实记忆（事件）；反思=对事实的**主观综合**（标 derived，不入 [锚] 面板）。

## 一、构造律（零编造 by construction）

- 喂入面=自有年轮尾 10 条（memory_index.load_rings）+姓名壳——**无任何外部事实可编**。
- 机审门：G1 长度/ASCII｜G2 占位词｜G3 天体（环面本无天体）｜G6 越权；**G4 闭包律**：输出含 雨/雪/风/热/冷 字样而喂入环中无同字 → 拦（天气词只能来自自己经历过的记录）。
- 产出：≤40 字感悟一句·temperature 0.7（主观综合允许措辞多样·事实面仍受闭包门）。

## 二、产线件

- 引擎=`Tools/reflect_citizen.py`（本地 Ollama 7b·零云端·--qc 6 例+闭包+确定性）。
- 产物=`census/reflections.jsonl`（**committed append-only**·字段=id/name/date/rings_used/insight/v）。
- **节律律**：每民 30 天冷却（低频 LLM 经济）+环数 ≥2 门槛（v0 实况值·环史加深后升 3）；荣誉席 blocked。
- 消费方：**memory_index v1.6 已接线**（2026-09-26·反思并入召回候选·重要性 1.5 加权·kind=reflection 标记感悟面·citizen_qa prompt 感悟标签渲染——禁当 [锚] 事实面）｜档案页「人生感悟」｜讲师包素材。

## 三、判据

1. `--qc` 6 门+闭包断言全 PASS；实弹试点 ≥3 民零编造（感悟句可追溯至自有环语义）。
2. append-only 永不改旧行；冷却期内 --force 除外（试点用）。

## 四、验收实录

- 2026-09-26（调研落实批·bm-c 会话）：--qc PASS；实弹 4 民试点=3 过 1 跳（C-00022 环数不足门槛行为正确）——顾阿凤「顾客如流，珍惜眼前。」（源=开档卖粢饭+小林馆员买粢饭两环的综合）/苏梓涵「游戏设计之路，充满挑战与温度。」（首试 G1-ascii 重生成过）/王多多「不断挑战，乐在其中。」；G4 闭包门在案。
- 2026-09-26（memory v1.6 三腿闭环收口·任务单 T-20260926-07·T2=CODEX §十二 v3.24）：memory_index v1.6 反思并入召回候选（importance ×1.5·同分同日感悟先于环·QC +5 例全 PASS：join/加权/零词交排除/双跑确定性/无反思回归+实盘文件读）；citizen_qa v1.1 接线（answer 载反思候选·prompt 感悟标签「（你自己的人生感悟）」·QC tag 用例过）；实弹=顾阿凤「对顾客有什么心得」唯命中感悟句（环面零词交=正确行为）+「粢饭生意如何」环事实驱动双问零门拦——**Generative Agents 三腿 记录→反思→检索 全链闭环**。
