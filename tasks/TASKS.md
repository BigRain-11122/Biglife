# BigLife 任务板（自领制·认领置 in-progress 署名+时间）

## 转办件跟踪

- [ ] **T-20260923-01**（集团进化台账 P-22 转办@FluxVerse-DevLoop）：M2 NPC 引擎与 CityWatch 消费 census 导出面（`census/export/citizens-light.jsonl` 只读）——本司侧义务=导出字段变更须 T2 登记+通知；DevLoop 侧自领时此处回执。
  - status: open（2026-09-23 立）

## 自领池（OS 循环/交互会话按优先级自领）
- [ ] **T-20260923-03** 基因轮首轮：为 lives.json 补 20 条转折点、10 条习惯；professions.json 补 5 个外环/江面职业（先登记后使用）。
- [ ] **T-20260923-04** 城主保留席受理程序：CEO 点名荣誉市民时按 census/reserved/README.md 落卡（人设权 CEO，AI 只执行落卡与正典引文登记）。
- [ ] **T-20260923-05**（v2 路线·已部分落地 2026-09-23 认知层批）台词池：barks 池已产（cognition/pools.json·六轴×12情境+像素灵池）；待续=标准台词层（45min 冷却级）与城市大事播报层（大事件模板）——消费契约见 CODEX §十二 v1.1。
- [ ] **T-20260923-06** 素材面：居民像素立绘需求出现时走集团 Art Assets AA 登记制（候选 AA-016 现代人物生成器 L2 直用通道），禁双建禁双购。
- [ ] **T-20260923-07**（认知层批·2026-09-23 立）OS 循环低频任务：①台词池扩容/换季维护（`Tools/pool_gen.py --append` 幂等·CODEX §十二 v1.1 诚实纪律）；②draw.py 确定性回归抽查（同参两跑逐字节一致）；③spotlight 抽验（只提所喂事实·≥2 例/月）。

## 已结

- [x] **T-20260923-02** 进化台词收紧（@BigLife-OSLoop 2026-09-23 22:52）：build_prompt 与 meet prompt 均追加「具体事逐字来自事件清单」硬约束；抽验=全查有年轮卡 4/4（全库现仅 4 卡有年轮，C-00010~13）——C-00011/C-00012 合规；C-00013 修复（越权声称执行集团令 O-20260923-2245-bm-a→改旁观编目视角，锚指向具体 CEO_ORDER）；C-00010 旧环「新音乐」联想坐实（当时清单实为 BigStream "BGM sourcing research v1.0" 提交且事发今日非昨晚）→改纯日常。原句均存 git 史（档案不毁字节）。证据：Tools/evolve_citizen.py prompt 段、census/anchors/C-00010.md、C-00013.md 年轮区。
- [x] T-20260923-00 成立批 root（07f1f1c）：万人户籍+进化引擎+OSLoop 点火。
