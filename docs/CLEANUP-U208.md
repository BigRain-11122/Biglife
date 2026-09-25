# BigLife 自域流程/规则文档清理整合台账（集团令 U208·P1）

- **法源**：集团正典 docs/orders.md 2026-09-25 ~14:08 行（MiniGame 登记簿 U208·「集团组织一次清理整合工作，把各个流程规则文档等全面梳理清理一下」·CEO 台 board-desk 痕 id=vc-20260925-140749-531·FluxVerse 事件流 CEO_ORDER 同 token 只读复现在案）。
- **任务单**：tasks/TASKS.md T-20260925-20。**对账窗**：2026-09-30 M5 治理日首窗（U178 首跑·与月度退役复审②同窗）·经 HQ-FEEDBACK 呈 CEO。
- **方法**：U188 指令整合判例四则（同义词归并 / 冲突终裁 / 时效态回落 / 上位吸收）。
- **红线**：①**原文保全铁律**——判例层=索引，原文永不删改；过时规则=标「已回落/已超期」+指针归档，非删除；②CEO 人设权保留面（docs/CODEX.md §十）与荣誉席卡面（census/reserved/）零触碰；③本清理件自身同样受原文保全铁律约束（本文件按分步追加，不改写已落段落）。
- **产出判据**：清理整合报告（冗余并籍数/冲突终裁数/过时回落数/指针归档数）+ 每域唯一速查正典索引面（判例§五范式）。

## 分步① 盘点建档（R235·2026-09-25 交付·实测枚举+行数）

### A 正典域（docs/·4 件）
| 文件 | 行数 | 角色 |
|---|---|---|
| docs/CODEX.md | 170 | 公司正典 §一~§十六（T2 登记面=§十二·版本行累计至 v3.17〔R219·否决窗 10-02〕——分步②全量核对行序/时效态/撞号双让路实录行） |
| docs/SILICON-LIFE.md | 40 | 硅基生命总纲（12 体征+八律+V2-A/A′/B/D 扩展面·律八=拟真度防火墙） |
| docs/global-benchmarks.md | 30 | 外部锚定基准面（P-70 派工遗产·失败面 404 在册） |
| docs/status-export.json | 130 | 状态导出面（轮末刷新·T-20260924-08 常设单·F3 律实据派生） |

另：docs/research/ R-件 6（R-20260923-citizen-design / R-20260924-bl-value-system / sl-agent-frontier / sl-honesty-industry / sl-life-cognition / R-20260925-bl-saturation-direction——调研行程律 P-65 件·全带结论应用表=常设律合规面）。

### B 契约域（cognition/·8 契约 MD+1 试点台账+5 数据面+1 任务包说明）
- 契约 MD 8：GREETINGS.md 25L（v1.0）·MOOD-DIRECTOR.md 18L（v1.0）·RUMOR-CHAIN.md 12L（v1.0）·NEEDS-CRASH.md 13L·PERSONA-v2.md 25L（v1.0）·QA-WHITELIST.md 33L（v1.1 六节）·VOICE-POOL.md 29L·README.md 48L（判据面·验收线 6）。
- 试点台账 1：value-ledger-pilot.md 6L（「一环一账」v0·回访窗 10-01）。
- 数据面 5：pools.json 1626L（1440 水位）·greetings.json 652L（518 实测=greet 476+faq 42）·pools-negative.json 64L（48 条）·fact-needs-registry.json 18L·mood-calendar.json 11L（法源指针律）。
- 任务包说明 1：package/README-PACKAGE.md（v1.0·副本漂移以仓内正典为准）。qa-samples-20260925.jsonl=实弹样本面（非规则·登记不清理）。

### C 工具契约面（Tools/·21 py+6 配置/运行件）
- 契约头注 py 21：evolve_citizen.py 791L（机审门 v0.22）·generate_census.py 557L·pool_gen.py 482L·citizen_qa.py 324L·draw.py 301L·mood_director.py 293L·pool_audit.py 292L·needs.py 264L·behavior.py 405L·relations_manifest.py 206L·rumor_chain.py 208L·persona_enrich.py 179L·atlas_manifest.py 130L·city_broadcast.py 109L·spotlight.py 111L·make_digests.py 119L·voice_manifest.py 118L·memory_index.py 94L·sync_rings.py 73L·add_honored_seats.py 71L·qc_census.py 60L。
- 配置/运行件 6：batch-policy.json（批策略 10）·iteration_loop.ps1 108L·voice_synth.ps1 80L·InvisibleRunner.vbs 15L·register_loop_task.ps1 19L·iteration_prompt.txt 2L。

### D 登记制（orders/·10 件）
O-20260923-2200-bm-a·O-20260923-2313-bm-a·O-20260924-1020-bm-a·O-20260924-1105-bm-a·O-20260924-1115-bm-a·O-20260924-1620-bm-a·O-20260925-1138-bm-c·O-20260925-1152-bm-c·O-20260925-1202-bm-c·O-20260925-1416-bm-c（末件=创始家庭令）+被动接收面（Group Patrol 周班·首个周一班 09-28）。

### E 台账/治理面（根+census·9 项）
tasks/TASKS.md（自领制章法+轮实录=本板）·census/INDEX.md·census/QC-REPORT.md（QC 随轮再生）·census/export/PUBLIC-WHITELIST.md（v1.0·形象面默认深水）·census/reserved/（C-00001~03+README=**CEO 人设权保留面·红线零触碰域·仅登记**）·HQ-FEEDBACK.md（集团回执面）·README.md（仓说明）·BLUEPRINT.md（公司蓝图）·.gitignore（state//logs//R3 面隔离）。CODELY.md=Codely 记忆面（非规则文档·不入清理域）。

### 出域声明（不入清理域·如实登记）
genes/ 9 件=生产资料数据面（非流程/规则文档）·census/ 万卡=活户籍（U208 红线）·census/export/*.jsonl=R3 再生面（消费前重生·非文档）·state//logs/=不入库运行面。

### 盘点计数
A 4+research 6｜B 8+1+5+1=15｜C 21+6=27｜D 10｜E 9 项（reserved 4 件红线域仅登记）→ **规则/契约/登记面合计 75 件**（py 与数据面全量登记；是否属「流程/规则/协议」清理对象=分步②按判域筛裁，登记本身即建档）。

### 冗余/冲突初步候选（7 项·留分步②扫描定谳）
1. **池水位判据多载**：T-07 单内旧水位行（8/6）vs cognition/README 现役判据（18/12·CEO 定向批后）→候选：单面时效态回落标注。
2. **CODEX §十二 T2 版本行叠加**：v1.x→v3.17 累计 30+ 行（含撞号双让路实录）→候选：上位吸收为索引面（原文保全·判例层索引化）。
3. **问候库计量口径差**：GREETINGS.md 契约估算 ≈322 vs 实测 518（CEO 定向批 floor/target 多版本并存）→候选：冲突终裁+指针归档。
4. **任务包双载**：cognition/package/ 快照 vs 仓内正典→README-PACKAGE 已声明「以正典为准」→候选：零新规则·指针化即可。
5. **Tools 头注版本号 ↔ CODEX §十二版本行对应关系**未逐件对照→分步②逐件核对 21 py。
6. **人设权保留面双述**：census/reserved/README ↔ CODEX §十 同一保留域→候选：同义词归并（指针互引·原文保全）。
7. **BLUEPRINT.md ↔ README.md 职责分界**（公司蓝图 vs 仓说明）→分步②检冲突/吸收关系。

## 分步计划
② 同义词/冲突扫描（09-26）→ ③ 终裁与回落标注（09-27~09-28）→ ④ 索引面+清理整合报告落件（09-29）→ **09-30 治理日首窗对账呈 CEO（经 HQ-FEEDBACK）**。

## 分步② 同义词/冲突扫描（R236·2026-09-25 部分交付·5/7 候选定谳）

> 本节按原文保全铁律=追加不改写已落段落；证据=当轮实读（文件+行号在册）。

| # | 候选 | 证据（实读） | 定谳 | 分步③ 动作 |
|---|---|---|---|---|
| 1 | 池水位判据多载（mandate 8/6 → T-07 单 15/10 → 现役 18/12） | cognition/README.md L58=现役 18/12 且自带「旧水位 8/6=648 与 15/10=1200 均已锁历史」（README 面已自带回落标注=权威面）；tasks/TASKS.md T-20260923-07 行=「六轴<15/像素灵<10·--target 15 --sprite-target 10」（v1.8 时点滞留）；Tools/iteration_prompt.txt mandate 第 2 项=「六轴<8 / 像素灵<6·--target 8 --sprite-target 6」（最旧层·启动器文本） | **真实时效态冲突（三层并存）**。现役权威面=README L58+工具默认（R203 裸调用即新水位）；CLI 显式旧值实跑无害（--append 幂等·桶已在 18>旧目标=零动作） | T-07 单行加回落标注+指针指向 README L58；iteration_prompt.txt mandate 行=启动器文本，随 T2 评估后分步③ 更新（谨慎面·勿裸改） |
| 3 | 问候库计量口径差（≈322 vs 301 实测 vs 518 现役） | cognition/GREETINGS.md L19=「旧水位 10（≈322 条）已锁历史」；cognition/package/README-PACKAGE.md L53=「R100 台账 322 为回滤前口径差异，以本实测与 audit PASS 为准」 | **非未解冲突——双面已自带终裁标注**（322=回滤前口径·301=v1.0 包实测·518=现役） | 零动作（报告计「已解决面」·台账 R100 行=判例层不改） |
| 4 | 任务包双载（package/ 快照 vs 仓内正典） | cognition/package/README-PACKAGE.md L46=「演进正典=本仓 `Tools/` 与 `cognition/`，副本漂移一律以正典为准」 | **非冲突——指针已内建**（快照=打包时点·声明覆盖漂移） | 零动作（报告计「指针化已备」） |
| 6 | 人设权保留面双述（reserved/README ↔ CODEX §十） | census/reserved/README.md L7=CEO 人设权留白+不代笔+不入进化轮；docs/CODEX.md L157=「## 十、CEO 保留席（人设权·硬红线）」 | **真实同域双载**——U188 同义词归并：docs/ 正典（CODEX §十）=上位权威面；reserved/README=卡面局部操作说明 | reserved/README 加指针行「权威面=CODEX §十」（只加指针·原文零删改） |
| 7 | BLUEPRINT.md ↔ README.md 职责分界 | README.md（16 行）=仓说明/导航面（「蓝图=BLUEPRINT.md·人口正典=CODEX」指针已内建）；BLUEPRINT.md（58 行）=生产纲领+进化路线+治理（自述「人口设计法=CODEX」） | **非冲突——导航面→纲领面→正典面三级分界互指清晰** | 零动作（报告计「分界清晰面」） |

### 留分步②续（下轮小步·勿硬撑）
- 候选 #2：CODEX §十二 T2 版本行 30+ 行叠加全量核对（行序/时效态/撞号双让路实录行）——重件拆步。
- 候选 #5：Tools 21 py 头注版本号 ↔ CODEX §十二版本行逐件对照——重件拆步。
- 全域同义词扫描余面（SILICON-LIFE ↔ CODEX 条款重复度/cognition 契约间重叠）——随②续。

### 分步②部分计数（本节）
冲突定谳：真实冲突 2（#1 时效态三层·#6 同域双载）·已自带解决 3（#3/#4/#7）·待续 2（#2/#5）+全域余扫。
