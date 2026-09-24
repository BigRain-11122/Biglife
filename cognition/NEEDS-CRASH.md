# NEEDS-CRASH 需求崩溃态契约 v1.0（判据先行·2026-09-24 R130 立契）

> T-20260924-16 **d 分单**。法源=R-20260924-silicon-aliveness §四增量 5（cph4/research/ 只读：「needs 长期失衡→可见负面行为（抱怨/错误率↑/怠工）+恢复叙事，全部由阈值派生零新系统」·消费点=needs.py 阈值分支+台词池负面池·档：零）+T-16d 分单判据+SILICON-LIFE **律八③ 明指本单落阈值**（「负面态冷却与限幅……阈值随 T-20260924-16d 崩溃态单判据落」）。
> 定位：Sims/Tamagotchi 谱系——需求长期得不到满足的居民出现可见负面行为，被满足后给出恢复叙事。全阈值派生，零 LLM 零网络零新工具件；「长期」由确定性恒再现涌现，非历史存储。本契约为引擎验收判据，全过才关分单。

## 一 崩溃态定义（闭集·纯阈值函数·needs.py 单点分支）

needs.py 现役输出 NEED_KEYS 四轴向量（anwen/shengji/shejiao/haoqi·0-2 确定性派生标尺·T-16a 查表化后事实面=fact-needs-registry 命中）。每居民每轮派生加法字段 `crash`/`crash_axis`：

- **crash（失衡）**：存在轴强度 ≥ CRASH_T（缺省 2.0=0-2 标尺顶档·参数化·引擎轮按实测分布校准后记档）且该轴本轮无 registry 可满足命中 → `crash="crash"`。
- **recovering（恢复叙事）**：该轴强度仍 ≥ RECOVER_T（缺省 1.5）且本轮 registry 命中已满足该轴 → `crash="recovering"`=「长期失衡刚被满足」转好面（翻转纯由阈值跨界+事实命中派生，零历史文件）。
- 其余 → `crash=null`。
- 轴→负面行为闭集映射表（确定性·参数化）：anwen→fumble（心神不宁·错误率↑）/ shengji→slump（生计无着·怠工）/ shejiao→grumble（孤独·抱怨）/ haoqi→slump（兴致受挫·怠工）。

## 二 可见面接线（三既有工具各加确定性分支·零新件）

1. **needs.py**：输出行加法字段 `crash`/`crash_axis`——现役 needs 向量派生语义零改（冻结快照等价哈希零漂移=T-16a 同法）。
2. **behavior.py（律八② 行为面）**：crash 行入 STATES 闭集新增三态 slump/grumble/fumble（选型=轴映射表）；slump=工位在岗降档、grumble=摊位/广场可见、fumble=工位在岗带错（slot 文本标注）；recovering 不改 state 只加 `recovering` 标志。citizen-behavior.jsonl（R3 再生面）QC schema 白名单随件同步。
3. **draw.py 台词面**：crash 居民路由负面桶、recovering 居民路由恢复叙事桶；非崩溃居民路由零变更。

## 三 负面池（数据件·随件生成）

`cognition/pools-negative.json`：4 轴负面桶+像素灵负面桶+恢复叙事桶（floor 6·风格化短句 ≤40 字·零具体事实零环境词=问候库 env 门同律）；生成走 pool_gen 既有扩展（--negative·floor/target 达标自停）；audit 闸随件（floor/重复/env 全检）。恢复句=转好口吻零具体事实。

## 四 验收判据（门禁·全过才关分单）

1. **纯阈值触发零新系统**：崩溃/恢复翻转均由阈值跨界或 registry 命中派生·零 LLM 零网络·源码静态断言（urllib/requests 零引用）。
2. **确定性**：同输入 needs/behavior/draw 三面双跑逐字节一致（md5 派生·`python hash()` 进程随机化禁用=behavior.py 同律）。
3. **长期性与恢复**：同 (persona, 实况) 恒同 crash 态=失衡期间逐轮恒再现；registry 命中当轮 recovering·恢复句同 id 冷却。
4. **behavior.py 可见面**：三负面态入 citizen-behavior.jsonl 且过 QC schema；现役非崩溃行全量零漂移。
5. **律八③ 冷却限幅阈值落本单**：同 id 同槽负面句不连发（draw 槽级冷却：相邻槽禁重抽负面桶·同 (id,槽) 恒同句）；**城区负面密度上限=同城区同刻 crash 可见居民 ≤ CRASH_CAP（缺省 5%·参数化·超额按 (轴强度, hash(id)) 确定性截断）**；全城 crash 人口 ≤ CITY_CAP（缺省 3%·防 Oblivion 式连锁崩坏）。
6. **荣誉席排除**：C-00001~03 恒 crash=null（人设权保留面·rumor_chain 同律）。
7. **零编造**：负面/恢复句零具体事实（清单外事零出现）·风格化 ≤40 字律沿用（律八①）。
8. **现役零回归**：needs 向量冻结等价+behavior 非崩溃行全量零漂移+draw 非崩溃路由零漂移+pool_audit/behavior QC 全回归。

## 五 红线与登记

- 红线：FluxVerse 事件流只读零写回；万卡零触碰（活户籍防护）；needs.py 现役派生语义零改（crash=纯加法）；荣誉席人设面零触碰；负面句永不升格痛苦叙事（风格化短句内·律八① 沿用）。
- 引擎+三面接线+负面池生成+T2 登记（CODEX §十二）留下轮落件（R99 契约先行范式）；CRASH_T/RECOVER_T/CRASH_CAP/CITY_CAP 全参数化=CEO 一句话可翻案面。
