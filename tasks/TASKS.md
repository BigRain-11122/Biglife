# BigLife 任务板（自领制·认领置 in-progress 署名+时间）

## 转办件跟踪

- [ ] **T-20260923-01**（集团进化台账 P-22 转办@FluxVerse-DevLoop）：M2 NPC 引擎与 CityWatch 消费 census 导出面（`census/export/citizens-light.jsonl` 只读）——本司侧义务=导出字段变更须 T2 登记+通知；DevLoop 侧自领时此处回执。
  - status: open（2026-09-23 立）
  - **v1.2 字段变更通知**（2026-09-23 迭代批·T2 登记=CODEX §十二 v1.2·否决窗至 09-30）：导出面新增 `recent_ring`+`recent_ring_date`（最近年轮镜像·≤80字+日期·无年轮=空串）——纯增量字段，消费方零 breaking；DevLoop 回执时一并确认。

## 自领池（OS 循环/交互会话按优先级自领）
- [ ] **T-20260923-04** 城主保留席受理程序：CEO 点名荣誉市民时按 census/reserved/README.md 落卡（人设权 CEO，AI 只执行落卡与正典引文登记）。
- [ ] **T-20260923-06** 素材面：居民像素立绘需求出现时走集团 Art Assets AA 登记制（候选 AA-016 现代人物生成器 L2 直用通道），禁双建禁双购。
- [ ] **T-20260923-07**（迭代批·2026-09-23 已接线）OS 循环持续任务（CODEX §十四 人口生态自迭代律）：①语言线池轮=先 `Tools/pool_audit.py` 看欠深桶（六轴<8/像素灵<6），有欠深才 `pool_gen.py --append --target 8 --sprite-target 6`，audit PASS 才 commit，全达标自停（已入 OSLoop mandate 第 2 项）；②确定性回归=pool_audit 内建同版本双跑逐字节一致；③spotlight 抽验（只提所喂事实·≥2 例/月）——结果记此单证据行。
  - [2026-09-23 23:55 @BigLife-OSLoop] 语言线闸实跑：pool_audit verdict=PASS（硬项 0 失败·确定性 168 对零漂移），但 84 桶全欠深（axes 72 桶均 6/8·sprite 12 桶均 4/6）→ **pool_gen 补深留单下轮执行**（本轮预算不足 84 次 LLM 调用·mandate 预算律「勿硬撑」；下轮：pool_gen --append --target 8 --sprite-target 6 → 复跑 audit → PASS 才 commit）。
  - [2026-09-23 23:55 @BigLife-OSLoop] spotlight 月度抽验 2/2 例：C-00010 顾阿凤「侬晓得伐，今朝粢饭加辣点儿嘞！」、C-00022 何雨欣「今晚的流量小高潮，我就是那盏不熄的灯。」——均零编造零越权（纯人设日常，未提清单外具体事、未声称执行集团任务），验收线 6「只提所喂事实」PASS。
  - [2026-09-23 23:59 @BigLife-OSLoop] 池轮补深收口：pool_gen --append --target 8 --sprite-target 6 实跑 TOTAL=648 FAIL=NONE（72桶×8+12桶×6）→ 复跑 pool_audit verdict=PASS（hard_fails 0·84/84 全达标·确定性 168 对零漂移）→ 语言线水位 8/6 达标自停（自终止律）。实跑抓到并当轮修复第 5 缺口：--append 预载去重把 sprite 的 ctx→list 当 ctx→dict 用必崩（T-08 上轮仅 --help 实测未实跑 append；崩在任何生成前=零写入零污染）；同轮补 save_pools 每桶原子落盘（原实现全跑完才一次性写盘，预算杀=零落盘，「做多少收多少」不成立；现断点续跑成立，契约不变：水位跳桶/软帽/单写锁保留）。QC 巡检（每 6 轮）R6 到期，下轮执行。
  - [2026-09-24 00:20 @BigLife-OSLoop] 迭代批实录：①年轮线 C-00026/27/28 三环落卡（4b9e358·sync aab526f rows=3·ring_citizens=19）；②QC 巡检 R6 实跑 problems=0（万卡全过·QC-REPORT 随轮入库）；③相遇轮 GM 对 C-00020×C-00021 双卡互引（9e42ee3）——验真=U153-D05/C408 均逐字坐实于 FluxVerse 活跃流（world-events.jsonl L127/L823·只读核查）零编造 PASS；实弹抓到 meet 面**第 6 缺口**：meet prompt「居民甲/乙」占位标签被 LLM 原样写进台词（d6d043d 相遇件无此缺陷=T-02 收紧只盖了事件真实性、没盖称谓自然性）→ 双修：prompt 加「禁止出现居民甲/乙字样」硬约束 + 两卡人称自然化（台词内容逐字保留·原句存史 9e42ee3）→ sync 复跑 rows=2·QC 复扫 problems=0。语言线 09-24 00:00 轮已达标自停，本轮语言线合规跳过。
  - [2026-09-24 00:19 @BigLife-OSLoop] 迭代批实录：①年轮线 C-00029/30/31 三环落卡（4d3b619·[锚]齐备零越权零占位词·sync 52527d9 rows=3·ring_citizens=22）；②语言线 09-24 已达标自停、QC R12 未到期、相遇轮今日已做、聚光灯 9 月 2/2 已满——四线合规跳过；③基因轮（低频）：口头禅 +6（60→66·六轴各 11 平衡）+钩子物件 +4（116→120），全库零重复、纯尾部定点追加既有基因零字节改动；④T-05 台词池 v2 两待续层（标准台词层 45min 冷却级+城市大事播报层）=特性开发超本轮预算，留单未认领。
  - [2026-09-24 00:40 @BigLife-OSLoop] 迭代批实录：①年轮线 C-00032/33/34 三环落卡（a24dbb3·sync 672c06b rows=3·ring_citizens=25）；②语言线 09-24 已达标自停、QC R12 未到期、相遇轮今日已做、聚光灯 9 月 2/2 已满——四线合规跳过；③T-05 认领交付关单（台词池 v2 两层·b6cea2f·见已结 T-05 证据行）。
  - [2026-09-24 00:52 @BigLife-OSLoop] 迭代批实录：①年轮线 C-00035/36/37 三环落卡（6e2f0ea·sync 2b504af rows=3·ring_citizens=28）；抽验三卡 [锚] 齐备零占位词零越权，其中 C-00037「听说 FluxGroup 又有新动向」联想句核验=坐实（world-events.jsonl 尾 30 行实含 FluxGroup PushEvent 多条+BigMoney/Bigmedia 真实 commit·只读核查·旁观吃瓜姿态无时间细节错）——T-02 程序下零修复需；②语言线 09-24 已达标自停、QC R12 未到期、相遇轮今日已做、聚光灯 9 月 2/2 已满、基因轮上轮刚补（00:19 实录）低频跳过——全余线合规；③集团 orders.md 无 09-24 新令。

## 已结

- [x] **T-20260923-05**（@BigLife-OSLoop 2026-09-24 00:28 认领·00:40 交付关单）台词池 v2 两待续层（b6cea2f）：①**标准台词层**=`draw.py --tier standard`（45 分钟槽粒度确定性抽词·同 (id,日期,slot,情境)→逐字节一致·槽内零变句=引擎 45min 台词冷却级·每日 32 槽轮换；抽桶路由同 barks：六轴/像素灵/锚民烟火默认）；②**城市大事播报层**=`Tools/city_broadcast.py`（7 事件族模板头条零事实+多数居民轴桶零 LLM 抽词+每城区≤N 位聚光灯事实级应答；触发=derive_context 真实事实门 事件>天气>时钟·FluxVerse 只读·**无大事件静默**；聚光灯选人=同 (城区,日期,事件) 确定性哈希）。**池数据零变更**（骨架够用即停·水位 8/6 锁定）。验收五判据全 PASS：standard/barks 双跑哈希一致（barks seed 不变=回归零漂移）、三路由实测抽桶正确（求新 C-00030→求新桶/像素灵 C-00028→sprite 桶/锚民 C-00010→烟火默认桶）、typhoon 模板 7 组（六轴+像素灵）采样、auto 门判 ambient night event=null 静默、spotlight 接线单点 C-00010「侬晓得伐，今朝的豆浆加糖伐？」（沪语人设一致零编造）。顺手修预存显示瑕疵：锚民 axis 空误显 'sprite'→标签对齐实际抽桶「烟火」。登记：CODEX §十二 v1.3（T2·否决窗至 2026-10-01）+ cognition/README 台词池 v2 分层节（验收判据+实录）。证据：b6cea2f（代码+契约）、a24dbb3/672c06b（同轮年轮线）、cognition/README 验收实录节。

- [x] **T-20260923-08**（认知层 v1.2 工具缺口·验证后关单 @BigLife-OSLoop 2026-09-23 23:58）：外部会话三件全部验实等效——①pool_audit.py 实跑 verdict=PASS（硬项 0 失败·确定性 168 对零漂移·欠深清单正确报出）；②pool_gen.py --help 实测认 --append/--target/--sprite-target，代码等效（水位达标即跳·got[:target] 软帽·state/pool.lock 单写锁）；③sync_rings.py 实跑 rows_changed=3 入库（[via] 尾标·1ef11c7）。验证中抓到并当轮修复**第 4 缺口**：evolve_citizen save_cursor 原在 sync_light 之后→批 e53d220 落 3 环零镜像（判据4 破）→接线已修+补跑 sync；同批 C-00022 越权环（声称「接了 CEO 的新任务」·令实为别司对话）按 T-02 程序改旁观视角（00a9755·原句存史）。池轮完整补深=语言线常规轮（见 T-07 证据行·留单下轮），非工具缺口。外部件归属已确认（a1239ad·author=junsheng.sun·交互会话无 [via] 义务=versioning §4.1）。证据：00a9755、1ef11c7、pool_audit 实跑输出、spotlight 抽验行（T-07）。

- [x] **T-20260923-03** 基因轮首轮（@BigLife-OSLoop 2026-09-23 23:15 认领并当轮完成）：lives.json +20 转折点（60→80）+10 习惯（28→38）；professions.json +5 外环/江面职业（RV 航道灯语员/滩涂像素苇农/趸船茶炉工·OR 感知塔擦镜工/边缘菜园农）。验=计数核对 80/38/94+全库零重复+新职业 schema/districts/bands 校验通过；纯文本定点追加、既有基因零字节改动（先登记后使用，未触发任何重生成）。证据：commit cf57e4f、genes/lives.json turning_points/habits 尾段、genes/professions.json 尾段。
- [x] **T-20260923-02** 进化台词收紧（@BigLife-OSLoop 2026-09-23 22:52）：build_prompt 与 meet prompt 均追加「具体事逐字来自事件清单」硬约束；抽验=全查有年轮卡 4/4（全库现仅 4 卡有年轮，C-00010~13）——C-00011/C-00012 合规；C-00013 修复（越权声称执行集团令 O-20260923-2245-bm-a→改旁观编目视角，锚指向具体 CEO_ORDER）；C-00010 旧环「新音乐」联想坐实（当时清单实为 BigStream "BGM sourcing research v1.0" 提交且事发今日非昨晚）→改纯日常。原句均存 git 史（档案不毁字节）。证据：Tools/evolve_citizen.py prompt 段、census/anchors/C-00010.md、C-00013.md 年轮区。
- [x] T-20260923-00 成立批 root（07f1f1c）：万人户籍+进化引擎+OSLoop 点火。
