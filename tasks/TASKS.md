# BigLife 任务板（自领制·认领置 in-progress 署名+时间）

## 转办件跟踪

- [ ] **T-20260923-01**（集团进化台账 P-22 转办@FluxVerse-DevLoop）：M2 NPC 引擎与 CityWatch 消费 census 导出面（`census/export/citizens-light.jsonl` 只读）——本司侧义务=导出字段变更须 T2 登记+通知；DevLoop 侧自领时此处回执。
  - status: open（2026-09-23 立）

## 自领池（OS 循环/交互会话按优先级自领）
- [ ] **T-20260923-04** 城主保留席受理程序：CEO 点名荣誉市民时按 census/reserved/README.md 落卡（人设权 CEO，AI 只执行落卡与正典引文登记）。
- [ ] **T-20260923-05**（v2 路线·已部分落地 2026-09-23 认知层批）台词池：barks 池已产（cognition/pools.json·六轴×12情境+像素灵池）；待续=标准台词层（45min 冷却级）与城市大事播报层（大事件模板）——消费契约见 CODEX §十二 v1.1。
- [ ] **T-20260923-06** 素材面：居民像素立绘需求出现时走集团 Art Assets AA 登记制（候选 AA-016 现代人物生成器 L2 直用通道），禁双建禁双购。
- [ ] **T-20260923-07**（认知层批·2026-09-23 立）OS 循环低频任务：①台词池扩容/换季维护（`Tools/pool_gen.py --append` 幂等·CODEX §十二 v1.1 诚实纪律）；②draw.py 确定性回归抽查（同参两跑逐字节一致）；③spotlight 抽验（只提所喂事实·≥2 例/月）。
- [ ] **T-20260923-08**（认知层 v1.2 迭代契约·工具缺口修复·2026-09-23 OSLoop 轮立单）cognition/README.md v1.2 迭代判据点名的三件实现缺口，致语言线池轮与行为线镜像均无法按文档执行：
  ① `Tools/pool_audit.py` 不存在——判据2 点名「语言线唯一门禁」（欠深桶判定 六轴<8/像素灵<6 + 全库零重复/零数字/行长4-24/禁词零命中 + 抽词确定性双跑内建回归）；无门禁则池轮禁 commit（判据2 门禁条款）。
  ② `Tools/pool_gen.py` usage 文档承诺 `--target 8 --sprite-target 6`（v1.2 判据1 池深度水位），argparse 实未实现该二参，且 append 逻辑硬编码 `got[:6]`/`got[:5]` 截断——按文档命令原样跑会 unrecognized arguments。
  ③ `Tools/sync_rings.py` 不存在 + `census/export/citizens-light.jsonl` 万行零 `recent_ring`/`recent_ring_date` 字段（2026-09-23 23:3x grep 实测零命中）——判据4（进化批落环后自动镜像 recent_ring≤80字·无年轮=空串·万人字段齐备）完全未落地；今日 C-00014~16、C-00017~19 两批年轮均未进行为面。
  验收=三缺口闭合后：`pool_audit.py` 报全桶达标或欠深清单、`pool_gen.py --append --target 8 --sprite-target 6` 原样可跑且 PASS 才 commit、evolve 落环后 export `recent_ring` 当轮齐备。
  证据：cognition/README.md v1.2 迭代判据/维护段、Tools/ 目录清单（本单立单时实测无 pool_audit/sync_rings）、pool_gen.py argparse 段与 got[:6]/got[:5] 截断行。
  **【23:33 轮内更新】** 单据陈述以立单观察时点为准，随后有外部会话（并发实例或交互侧，无 round.lock/无心跳记录）于 23:24:51–23:25:52 在**未提交工作树**落地 `Tools/pool_audit.py`（门禁完整设计：欠深桶/零重复/零数字/行长/禁词/同版本双跑确定性）与 `Tools/sync_rings.py`（增量镜像 recent_ring·自带 --via 尾标），并改写 `pool_gen.py`（--target/--sprite-target 落地+state/pool.lock 单写锁+像素灵禁词）与 `make_digests.py`/`cognition/README.md`/`docs/CODEX.md`；至本轮末仍未提交、编辑仍在途。**本单收口动作改为**：下轮验证外部实现与 v1.2 判据功能等效（判据先行），确认其 commit 归属与尾标后关单；若外部会话 30 分钟内未提交，由 OSLoop 认领按「先验证后提交」收口（档案不毁字节，不重写其文件）。

## 已结

- [x] **T-20260923-03** 基因轮首轮（@BigLife-OSLoop 2026-09-23 23:15 认领并当轮完成）：lives.json +20 转折点（60→80）+10 习惯（28→38）；professions.json +5 外环/江面职业（RV 航道灯语员/滩涂像素苇农/趸船茶炉工·OR 感知塔擦镜工/边缘菜园农）。验=计数核对 80/38/94+全库零重复+新职业 schema/districts/bands 校验通过；纯文本定点追加、既有基因零字节改动（先登记后使用，未触发任何重生成）。证据：commit cf57e4f、genes/lives.json turning_points/habits 尾段、genes/professions.json 尾段。
- [x] **T-20260923-02** 进化台词收紧（@BigLife-OSLoop 2026-09-23 22:52）：build_prompt 与 meet prompt 均追加「具体事逐字来自事件清单」硬约束；抽验=全查有年轮卡 4/4（全库现仅 4 卡有年轮，C-00010~13）——C-00011/C-00012 合规；C-00013 修复（越权声称执行集团令 O-20260923-2245-bm-a→改旁观编目视角，锚指向具体 CEO_ORDER）；C-00010 旧环「新音乐」联想坐实（当时清单实为 BigStream "BGM sourcing research v1.0" 提交且事发今日非昨晚）→改纯日常。原句均存 git 史（档案不毁字节）。证据：Tools/evolve_citizen.py prompt 段、census/anchors/C-00010.md、C-00013.md 年轮区。
- [x] T-20260923-00 成立批 root（07f1f1c）：万人户籍+进化引擎+OSLoop 点火。
