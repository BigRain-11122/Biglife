# census 公开白名单 · PUBLIC-WHITELIST v1.0

> **法源**：集团令 2026-09-24 ~15:00「实验室开始进行服务器端技术，适配我的硅基生命体城市运行」（服务器端城市运行线开工·承建转办三司@ledger P-52 之「BigLife census 白名单定稿」）——令文初版原则：recent_ring/hook 留深水区·荣誉市民席空席零渲染·界面敏感面律适用。本件=定稿交付。
> **登记**：CODEX §十二 v1.6 · T2 否决窗至 2026-10-01 · 2026-09-24 @BigLife-OSLoop

## 一、适用边界

- 适用面=**服务器端公面**（参观只读/大厅/census 查询/居民之声投喂）对 `census/export/` 的一切公开渲染——git 只读通道（citysync）消费方：FluxVerse server 城市线、BigDomain P-47。
- **零改变**：M2 NPC 引擎消费契约（`citizens-light.jsonl` 只读·P-22 转办件=T-20260923-01 跟踪中）；导出面字段集零增删（本件=公私分层契约·非字段变更·非数据变更）。

## 二、白名单三分表（citizens-light.jsonl · 现行 19 字段全量）

| 层 | 字段 | 规则 |
|---|---|---|
| **公面白名单**（16 · 可渲染） | `id` `name` `species` `faction` `gender` `age` `age_note` `district` `block` `profession` `axis` `creed` `v` `anchor` `brain_digest` `behavior_hint` | 公面可读可渲染（人设基本面+大脑摘要+行为提示） |
| **深水区**（3 · git 可载 · 公面禁渲染） | `recent_ring` `recent_ring_date`（v1.2 镜像对·随环同深）`hook` | 年轮记忆与独有钩子=深互动内容，参观只读层禁渲染；深水面何时何层可启=按集团后续令 |
| **默认深水** | 未来新增字段 | 一律默认深水区——须 T2 登记+本名单显式收录方可入公面（防新面静默泄漏） |

## 三、席位与分层律

- **荣誉市民席 C-00001~09**（CEO 人设权·CODEX §十）：常设保留·**不在 census/export/ 导出面**（结构性空席零渲染·rg 实测零命中）；按 census/reserved/README.md 受理落卡后，是否入公面=CEO 决定·默认不入。
- **实锚居民层不入 census**：census=叙事市民层专属（诚实律·CODEX §一 三层模型）；服务器端实锚面走 FluxVerse residents 探针契约，与本名单无关。
- **动机需求面 `citizen-needs.jsonl`**（v1.4）：R3 再生面·gitignored·不入 git 通道=天然非公面，契约不变。
- **界面敏感面律适用**：公面渲染涉及身份/隐私敏感面按集团界面敏感面律执行（律文归集团正典）。

## 四、变更制

本名单即消费契约：名单变更=T2 登记+7 天否决窗（CODEX §十二）；消费方按本名单执行过滤；争议面=呈集团决策轮。
