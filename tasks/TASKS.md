# BigLife 任务板（自领制·认领置 in-progress 署名+时间）

## 转办件跟踪

- [ ] **T-20260923-01**（集团进化台账 P-22 转办@FluxVerse-DevLoop）：M2 NPC 引擎与 CityWatch 消费 census 导出面（`census/export/citizens-light.jsonl` 只读）——本司侧义务=导出字段变更须 T2 登记+通知；DevLoop 侧自领时此处回执。
  - status: open（2026-09-23 立）
  - **v1.2 字段变更通知**（2026-09-23 迭代批·T2 登记=CODEX §十二 v1.2·否决窗至 09-30）：导出面新增 `recent_ring`+`recent_ring_date`（最近年轮镜像·≤80字+日期·无年轮=空串）——纯增量字段，消费方零 breaking；DevLoop 回执时一并确认。

## 自领池（OS 循环/交互会话按优先级自领）
- [ ] **T-20260923-04** 城主保留席受理程序：CEO 点名荣誉市民时按 census/reserved/README.md 落卡（人设权 CEO，AI 只执行落卡与正典引文登记）。
- [ ] **T-20260923-05**（v2 路线·已部分落地 2026-09-23 认知层批）台词池：barks 池已产（cognition/pools.json·六轴×12情境+像素灵池）；待续=标准台词层（45min 冷却级）与城市大事播报层（大事件模板）——消费契约见 CODEX §十二 v1.1。
- [ ] **T-20260923-06** 素材面：居民像素立绘需求出现时走集团 Art Assets AA 登记制（候选 AA-016 现代人物生成器 L2 直用通道），禁双建禁双购。
- [ ] **T-20260923-07**（迭代批·2026-09-23 已接线）OS 循环持续任务（CODEX §十四 人口生态自迭代律）：①语言线池轮=先 `Tools/pool_audit.py` 看欠深桶（六轴<8/像素灵<6），有欠深才 `pool_gen.py --append --target 8 --sprite-target 6`，audit PASS 才 commit，全达标自停（已入 OSLoop mandate 第 2 项）；②确定性回归=pool_audit 内建同版本双跑逐字节一致；③spotlight 抽验（只提所喂事实·≥2 例/月）——结果记此单证据行。
  - [2026-09-23 23:55 @BigLife-OSLoop] 语言线闸实跑：pool_audit verdict=PASS（硬项 0 失败·确定性 168 对零漂移），但 84 桶全欠深（axes 72 桶均 6/8·sprite 12 桶均 4/6）→ **pool_gen 补深留单下轮执行**（本轮预算不足 84 次 LLM 调用·mandate 预算律「勿硬撑」；下轮：pool_gen --append --target 8 --sprite-target 6 → 复跑 audit → PASS 才 commit）。
  - [2026-09-23 23:55 @BigLife-OSLoop] spotlight 月度抽验 2/2 例：C-00010 顾阿凤「侬晓得伐，今朝粢饭加辣点儿嘞！」、C-00022 何雨欣「今晚的流量小高潮，我就是那盏不熄的灯。」——均零编造零越权（纯人设日常，未提清单外具体事、未声称执行集团任务），验收线 6「只提所喂事实」PASS。
  - [2026-09-23 23:59 @BigLife-OSLoop] 池轮补深收口：pool_gen --append --target 8 --sprite-target 6 实跑 TOTAL=648 FAIL=NONE（72桶×8+12桶×6）→ 复跑 pool_audit verdict=PASS（hard_fails 0·84/84 全达标·确定性 168 对零漂移）→ 语言线水位 8/6 达标自停（自终止律）。实跑抓到并当轮修复第 5 缺口：--append 预载去重把 sprite 的 ctx→list 当 ctx→dict 用必崩（T-08 上轮仅 --help 实测未实跑 append；崩在任何生成前=零写入零污染）；同轮补 save_pools 每桶原子落盘（原实现全跑完才一次性写盘，预算杀=零落盘，「做多少收多少」不成立；现断点续跑成立，契约不变：水位跳桶/软帽/单写锁保留）。QC 巡检（每 6 轮）R6 到期，下轮执行。

## 已结

- [x] **T-20260923-08**（认知层 v1.2 工具缺口·验证后关单 @BigLife-OSLoop 2026-09-23 23:58）：外部会话三件全部验实等效——①pool_audit.py 实跑 verdict=PASS（硬项 0 失败·确定性 168 对零漂移·欠深清单正确报出）；②pool_gen.py --help 实测认 --append/--target/--sprite-target，代码等效（水位达标即跳·got[:target] 软帽·state/pool.lock 单写锁）；③sync_rings.py 实跑 rows_changed=3 入库（[via] 尾标·1ef11c7）。验证中抓到并当轮修复**第 4 缺口**：evolve_citizen save_cursor 原在 sync_light 之后→批 e53d220 落 3 环零镜像（判据4 破）→接线已修+补跑 sync；同批 C-00022 越权环（声称「接了 CEO 的新任务」·令实为别司对话）按 T-02 程序改旁观视角（00a9755·原句存史）。池轮完整补深=语言线常规轮（见 T-07 证据行·留单下轮），非工具缺口。外部件归属已确认（a1239ad·author=junsheng.sun·交互会话无 [via] 义务=versioning §4.1）。证据：00a9755、1ef11c7、pool_audit 实跑输出、spotlight 抽验行（T-07）。

- [x] **T-20260923-03** 基因轮首轮（@BigLife-OSLoop 2026-09-23 23:15 认领并当轮完成）：lives.json +20 转折点（60→80）+10 习惯（28→38）；professions.json +5 外环/江面职业（RV 航道灯语员/滩涂像素苇农/趸船茶炉工·OR 感知塔擦镜工/边缘菜园农）。验=计数核对 80/38/94+全库零重复+新职业 schema/districts/bands 校验通过；纯文本定点追加、既有基因零字节改动（先登记后使用，未触发任何重生成）。证据：commit cf57e4f、genes/lives.json turning_points/habits 尾段、genes/professions.json 尾段。
- [x] **T-20260923-02** 进化台词收紧（@BigLife-OSLoop 2026-09-23 22:52）：build_prompt 与 meet prompt 均追加「具体事逐字来自事件清单」硬约束；抽验=全查有年轮卡 4/4（全库现仅 4 卡有年轮，C-00010~13）——C-00011/C-00012 合规；C-00013 修复（越权声称执行集团令 O-20260923-2245-bm-a→改旁观编目视角，锚指向具体 CEO_ORDER）；C-00010 旧环「新音乐」联想坐实（当时清单实为 BigStream "BGM sourcing research v1.0" 提交且事发今日非昨晚）→改纯日常。原句均存 git 史（档案不毁字节）。证据：Tools/evolve_citizen.py prompt 段、census/anchors/C-00010.md、C-00013.md 年轮区。
- [x] T-20260923-00 成立批 root（07f1f1c）：万人户籍+进化引擎+OSLoop 点火。
