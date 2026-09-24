# R-20260924 · 数字城市居民智能工程前沿调研
- 溯源：CEO 令 2026-09-24 · 研究员：后台代理（CPH4 Labs）
- 版本：v4（终稿）。演进：v1 骨架+预研知识落盘→v2 对齐五层契约→v3 并入业界现状核验→v4 完成全部核验与勘误，覆盖式重写
- 基线（已有）：台词池 648 条（六轴 72 桶×8+像素灵 12 桶×6·确定性抽词）｜聚光灯=本地 qwen2.5:7b·224ms/句·≤40 字｜年轮 7 天冷却·[锚]定律｜大事播报 city_broadcast v2｜万人户籍 citizens-light 10,000 行｜零 API 零服务器｜10 分钟 OS 轮
- 五层大脑（官方名）：①行为查表层 ②台词池层 ③聚光灯层 ④年轮进化层 ⑤大事件反应层；Token 五律：能查表不生成·能共享不独占·能摘要不全卡·能离线不在线·能结构不散文
- 核验口径：[已验]=本报告 2026-09-24 web_fetch 已抓核对；[未验]=抓取失败或未抓到；[内置]=业界公知/训练知识未复核；[兄弟已验]=R-20260923 已网络验证，引用不重复
- 关联：`gaming/FluxVerse/docs/research/R-20260923-openworld-npc.md`（15 典范·AI LOD 分层）；`R-20260923-academic.md` S19（GA 已详析）；`life/BigLife/cognition/README.md`（五层总契约）

## 0. 结论速览
1. 业界 2025-26：「少数深智能」进化为**类型化五类**（助理/队友/敌人/市民/角色），其中 inZOI Smart Zois=「规划/行动/反思」的 AI 市民已进商业生活模拟——BigLife 同题赛道已被打开 [已验]；AI NPC 中间件风口退潮（Inworld 转型语音模型供应商 [已验]）。聚光灯席位制与业界同向，零服务器路线被印证。
2. 学术主线（GA 25 人→千人访谈模拟→Project Sid 千人文明）：涌现的燃料是持久记忆＋关系扩散＋异步批处理，不是更大的模型；GA 三维检索=我们「记忆优先级表」的完整版；千人模拟证实「访谈档案+摘要记忆」可复刻人格到 85% [已验]。
3. 五层大脑缺三层：动机层（需求效用·表驱动）、反思层（一行教训·年轮附加）、关系层（关系边表·播报路由）；全部可做成零 API 表结构，不违反 Token 五律与诚实律。
4. 最值钱的可搬件全部零模型成本：OCC 情绪机、需求效用评分、三维记忆检索、事件驱动反思、睡眠期作业——「能查表不生成」一次满足。
5. 万人扩展的正路是「批处理+压缩」：GA 25 人 2 天烧数千美元 [已验] 是反面教材；Project Sid 认知解耦 [内置] 与我们 10 分钟 OS 轮是正路——LLM 调用从「每人每事件」降到「每人每批次」。

## 1. Stanford Generative Agents（Park et al. 2023，arXiv:2304.03442）
**机制**（全文 HTML 已核验）：25 个 agent 住进 Sims 风小镇；架构三组件——
- 记忆流：一切经历以「自然语言+时间戳」入流；检索按三因子加权出子集：recency（按距上次检索的沙盒小时数指数衰减，**衰减系数 0.995** [已验]）＋importance（入流时评重要度，量程 1-10、反思触发阈值≈累计 150 [内置]）＋relevance（与当下情境的嵌入相关性）。
- reflection：把碎片记忆归纳为高阶推断（「Klaus 很投入研究」）回写记忆流，可递归成反思树 [内置]。
- planning：把结论+环境译成行为计划，日骨架→逐时→细分 [内置]。
- 成本 [已验原文]："simulate 25 agents for two days, costing thousands of dollars in token credits and taking multiple days to complete"。
**涌现**：情人节派对邀请沿对话链扩散、友谊与集体行为自组织 [内置；另见 academic.md S19 已详析]。
**可搬判定**：
- 可搬：三维检索——我们已有「记忆优先级（CEO 令＞城市里程碑＞自身大事＞日常）」=importance 维形；补 recency 算式（0.995^小时）与 relevance（本地 TF-IDF/bge 嵌入）即完整版，聚光灯组装 prompt 时用。
- 要改：reflection 挂年轮冷却（7 天批量、仅大事居民）；planning 降为「人设卡行为字段×真实情境」日程模板。
- 不可搬：逐观察 LLM 评 importance、分钟级计划、25×常驻调用——GA 自己都 2 天烧数千美元 [已验]，万人下算力爆炸。

## 2. MemGPT/Letta（Packer et al. 2023，arXiv:2310.08560）
**机制**（摘要已核验）：借鉴传统 OS 分级内存提出 virtual context management——LLM 上下文窗=RAM、外部存储=磁盘；MemGPT 智能管理多级 memory tiers，在有限窗内提供扩展上下文；用 **interrupts 管理控制流** [已验]；两域评估：文档分析（远超上下文窗的大文档）与多 session 长程对话——agent「remember, reflect, and evolve dynamically」[已验原文]。core/recall/archival 三级与自我编辑函数调用 [内置]；Letta 公司化后：记忆块、agent-as-file、上下文压缩、睡眠期计算（→§8.2）。
**对「年轮+摘要」的升级启示**：年轮=磁盘、brain_digest=核心块，存储已够；缺的是**自编辑**——年轮节点应能合并/修订/淘汰并沉淀进核心块，而非只追加压缩。
**可搬判定**：
- 要改：self-edit 不做每居民实时函数调用（7b 工具链不稳），改 10 分钟轮「记忆整理作业」：合并重复、刷新 brain_digest、给事实打 valid_from/valid_to 时间戳（Zep 式）。
- 不可搬：万人级每居民常驻 agent-loop（内存+推理开销）；依赖强模型的长程自编辑。
- URL：https://arxiv.org/abs/2310.08560 [已验] · https://www.letta.com [未验]

## 3. Voyager 技能库 + Reflexion 语言化反思
**机制** [内置]：Voyager（Wang et al. 2023，Minecraft）：①automatic curriculum 自动课程（按状态+进度提下一个目标）②**skill library**——把成功行为固化为「可执行代码技能」，带嵌入描述存库，可检索、可组合、越攒越强 ③iterative prompting（环境报错→自验证→修复）。Reflexion（Shinn et al. 2023，arXiv:2303.11366）：任务失败后用自然语言写一行「哪里错了/下次怎么办」存 episodic 缓冲，下次尝试注入——语言强化学习，不动梯度。
**可搬性**：
- 立刻可搬：Reflexion 一行反思——大事后 7b 生成一句「教训」附进年轮（[锚]定律合规：教训=对真实事件的归因，不编新事实），聚光灯注入；成本≈一次短补全。
- 要改：技能库从「代码」降维为「行为脚本模板库」（日程模板/事件响应模板，本地嵌入检索+组合，产出 behavior_hint 候选）。
- 不可搬：GPT-4 自动课程与代码生成执行（7b 能力边界+无执行面）。
- URL：https://arxiv.org/abs/2305.16291 [未验·抓取失败，摘要页被导航噪音覆盖] · https://voyager.minedojo.org [未验] · https://arxiv.org/abs/2303.11366 [内置]

## 4. Project Sid（Altera，2024-11，arXiv:2411.00114）
**机制**（题录已验；机制细节 [内置]）：正式题「Project Sid: Many-agent simulations toward **AI civilization**」[已验]，35 页 14 图 [已验]。Minecraft 上 1000+ agent 组成聚落长跑。认知架构 **PIANO**：感知/规划/社交/说话/执行并行线程，conversability 模块决定何时开口；认知与服务器 tick 解耦（异步批出队）。
**涌现**：投票立宪与政教分离、宗教传播与改宗、宝石货币/集市/分工/通胀的市场经济、偷窃与帮派等失序；代价是万美元级 API 开销与幻觉失焦。
**对「城市涌现观察」的意义**：涌现=可观测的城市层指标（政策/信仰/物价/流行语）——大事件反应层 V3 的素材方向；且证明「低频批处理+认知解耦」足以维持涌现，与 10 分钟 OS 轮同构。
**可搬判定**：
- 要改：城市涌现指标面板（婚恋/迁徙/口头禅/自组织节日）；大事播报按关系图路由而非全城广播。
- 不可搬：千级持续 LLM 调用与云 API 经济（零 API 红线）；PIANO 高频并行（万人本地机不可行）。
- URL：https://arxiv.org/abs/2411.00114 [已验·题录] · https://www.altera.al [未验]

## 5. NVIDIA ACE / Inworld / Ubisoft NEO NPC（2025-26 现状·官方渠道已核验）
背景：R-20260923 已证维基无 ACE/Inworld 词条；本报告 2026-09-24 直抓官方渠道，得三个实况：
- **NVIDIA ACE**（developer.nvidia.com/ace，中文页已验）：定位=「模型+开发者工具组合」，构建「具备知识、可执行行动、可自然对话」的游戏内角色，覆盖语音/智能/动画，可集成「云端和本地设备」；主打小型模型+设备端推理优化，NVIGI 插件跨图形负载调度推理。**五类角色案例**：助理（Total War: PHARAOH，本地小语言模型挂游戏数据）｜队友（KRAFTON《绝地求生》CPC/Ally，自然语言交流、像人类队友自主行动）｜敌人（MIR5 AI BOSS，学习玩家战术）｜**市民（KRAFTON《inZOI》Smart Zois：「规划、行动和反思」决策的 AI 居民）**｜角色（Dead Meat 讯问游戏，自由提问嫌疑人）。模型栈多已开源：Audio2Face-3D SDK（MIT）、Audio2Face-3D 模型（ONNX-TRT 开放权重）、Audio2Emotion-3D（从音频推断情绪）、Chatterbox TTS（Resemble AI 350M/500M 开源）。旧 GeForce 营销页已 404 [已验·负结果]。
- **Inworld 已转型**（官网 2026-05 状态页已验）：AI NPC 中间件→实时语音模型供应商（Realtime TTS/STT/Router/API；inworld/user-aware、inworld/context-aware 模型；一 API 跨 OpenAI/Anthropic/Google 与 220+ 模型路由）；游戏只是其五分之一解决方案板块；另与 Streamlabs 合做直播助手（见 ACE 页）。⇒ 2023-24「AI NPC 平台」风口 2026 已退潮。
- **Ubisoft NEO NPC→Teammates**（官方新闻+GDC 2024 新闻稿 PDF+Variety 2025，均已验）：NEO NPC=巴黎工作室 R&D×La Forge×Inworld（LLM+环境知识）×NVIDIA（Audio2Face）；NPC「Bloom/Iron」带背景故事+知识库+对话风格，但静态场景 [官方引语已验]；2025 演进「Teammates」=首个**可玩**生成式 AI 研究项目：AI 队友 Jaspar 进 FPS 玩法场景，「respond dynamically to real-time voice commands」[官方引语已验]。
**策略共识（2026-09 视角）**：①「少数深智能」进化为**类型化深智能**——五类角色、每类 1-2 个；②「市民」类=inZOI Smart Zois（规划/行动/反思）——AI 市民已进商业生活模拟，与 BigLife 同题；③一切深智能案例仍绑云/GPU/引擎全栈，唯一例外倾向=ACE 的设备端小型模型。
**可搬判定**：
- 可搬（战略）：聚光灯席位制=业界同款；inZOI 证明「AI 市民」有市场叙事；设备端小模型路线与我们零服务器同向。
- 不可搬：语音/表情/动画全栈（UE5+GPU 运行时）；一切云依赖（零 API 红线）；Audio2Emotion 类模型（我们用更便宜的表驱动 OCC 替代，→§6）。
- URL：https://developer.nvidia.com/ace [已验] · https://inworld.ai [已验] · news.ubisoft.com（Teammates）+GDC 2024 新闻稿 PDF [已验] · https://www.nvidia.com/en-us/geforce/technologies/ace/ [已验·404]

## 6. OCC 情绪模型（Ortony-Clore-Collins 1988）
**机制**（多源已验）：情绪=对「事件后果/他人行为/客体特征」三类评价的效价反应，层级共 **22 类基本情绪**（课题记 20 类，取整引用即可）——Ortony 本人论文原句 "distinguishes 22 emotion types" [已验]：
- 事件后果分支（如 joy/pity），其下分组 Well-being / Prospect-based / Fortunes-of-others [已验·剑桥书页]
- 他人行为分支（如 pride/reproach）；客体特征分支（如 love/hate）；部分分支组合成 compound emotions（gratitude/anger 等）[已验·IDSIA KI09 revisited]
轻量状态机：事件→三维度打分→取最强情绪标签→按半衰期衰减→输出语气参数与行为权重。2022 年出第 2 版（30 年后修订）[已验·剑桥]。
**可搬判定（零模型纯表，「能查表不生成」）**：立刻可搬——事件→情绪标签→在既有 72 桶间做消费端加权路由（情绪极性×六轴），**不改池行**（池 append-only 永不改旧行）；冲突按强度半衰期归一。业界呼应：NVIDIA 用 Audio2Emotion-3D 模型从音频推情绪（→§5），我们用表从事件推情绪，零成本且可解释。补上「大事件反应」之后的持续余波，而非播报完即归零。
- URL：people.idsia.ch/~steunebrink/Publications/KI09_OCC_revisited.pdf [已验] · Ortony 2013 PDF（users.cs.northwestern.edu）[已验] · 剑桥大学出版社书页 [已验] · en.wikipedia.org/wiki/OCC_model [已验·404 负结果]

## 7. Sims 需求-动机（简查）+ AutoGen/CAMEL（居民提案 V3 参考）
- Sims（2000, Will Wright）[内置；兄弟报告同源：维基抓取污染转内置]：8 需求（饥饿/精力/娱乐/社交/卫生/膀胱/舒适/环境）随时间衰减；核心 **smart terrain**——设施对路过 Sim「广告」自己能补哪条需求，Sim 按效用=缺口×补益×距离成本选动作；微效用决策而非全局规划。
- AutoGen（微软 2023，arXiv:2308.08155）[内置]：多 agent 会话框架，角色分工+群聊管理器+代码执行器，擅长「提案-批评-修订」结构化辩论。
- CAMEL（KAUST 2023，arXiv:2303.17760）[内置]：双 agent 角色扮演+inception prompting 锁任务防跑偏。
**可搬判定**：
- 立刻可搬（诚实律版）：Sims 需求效用——需求**不得虚构**（R-20260923 §四.7 禁编造需求动机）：需求值=人设卡（六轴倾向）×真实情境（时间/天气/事件）确定性计算，输出增强 behavior_hint；效用=缺口×设施补益×距离/成本。
- 要改：AutoGen 辩论协议→「提案事件触发的一次性聚光灯剧本」（提案→2 轮质疑→修订→投票，token 封顶、单会话自终止）；CAMEL inception prompting 用于锁「只谈真实事件」诚实律。
- URL：https://arxiv.org/abs/2308.08155 · https://arxiv.org/abs/2303.17760 [内置]

## 8. 2025-26 记忆/长程能力新进展（自选 3 个最有用）
**8.1 千人模拟**（Park, Zhi et al., arXiv:2411.10109，2024-11，多源已验）：1052 名真人各做 2 小时 AI 语音访谈→每位生成 GPT-4o agent（记忆=访谈转录）；「在 GSS 上复刻达真人两周后自我复述的 85% 一致」，并能预测人格特质、经济博弈与实验反应 [已验·多源引文]；开源 StanfordHCI/genagents [已验]。关键佐证：**interview-summary 变体**（GPT-4o 把转录压成要点摘要再建 agent）同样有效——**摘要化记忆路线可行**，直接支持我们 brain_digest 的哲学。Park 2025 博士论文续推 population-scale simulations [已验·官网]。
- 要改可搬：用 7b 离线批量生成「访谈式户籍档案」（自述+人生转折点+偏好清单），一次性成本；档案质量↑→聚光灯演技↑。
**8.2 Sleep-time Compute**（Letta，arXiv:2504.13171，2025-04，题录已验）：主张算力从 test-time 挪到 idle「睡眠期」——夜里预计算/重组记忆，白天更准更省；代码开源 github.com/letta-ai/sleep-time-compute [已验]；具体提升百分比 [内置·摘要页被导航噪音覆盖]。
- 立刻可搬（概念）：10 分钟 OS 轮低峰段=睡眠期：跑年轮压缩、反思预生成、OCC 衰减；聚光灯 224ms 基线不破。
**8.3 inZOI Smart Zois 与设备端小型模型**（2025-26 商业前沿，ACE 官方页已验，详见 §5）：AI 市民以「规划、行动、反思」进商业生活模拟；ACE 主打设备端小模型+开源权重；官方教程含「如何利用编程智能体大幅降低游戏运行时的推理成本」——与我们「能查表不生成」同构。
- 可搬（方向）：本地小模型+席位制+表驱动降推理成本=三重同向；情绪推断用表驱动 OCC 替代 Audio2Emotion-3D。
- 备选 [内置·未验]：Mem0——记忆增/改/删操作替代追加式流；Zep——时序知识图（valid_from/valid_to）做关系层。

## § 可搬清单
**A. 立刻可搬（本地 7b+现轮节律，零 API，全部表驱动）**
1. OCC 情绪状态机：事件→三维度→标签→半衰期→消费端池路由加权+语气参数（不改池数据）。
2. Sims 需求效用层（诚实律版）：需求=人设卡×真实情境确定性计算；设施=smart terrain；效用=缺口×补益×距离→behavior_hint。
3. 三维记忆检索（GA）：已有「记忆优先级」+recency 0.995^小时+相关性本地嵌入；聚光灯 prompt 组装用。
4. Reflexion 一行教训：大事后 7b 一句归因附年轮（[锚]合规），聚光灯注入。
5. Sleep-time 作业：OS 轮低峰段跑年轮压缩/反思预生成/情绪衰减。

**B. 要改可搬**
6. MemGPT 自编辑→定时「记忆整理作业」（合并/修订/valid_from-valid_to 时间戳，Zep 式）。
7. GA 反思树→年轮冷却批量反思（仅大事居民，7 天一批）。
8. Voyager 技能库→行为脚本模板库（嵌入检索+组合，产出 behavior_hint 候选）。
9. AutoGen/CAMEL→居民提案 V3 一次性辩论剧本（聚光灯会话、token 封顶、自终止）；参照 Ubisoft Teammates，提案面做成「协作行动」而非纯对话。
10. 日卷积批处理+印象式压缩记忆（**本报告工程建议，非单篇论文**；依据=GA 成本教训 [已验]＋Project Sid 认知解耦 [内置]＋10 分钟 OS 轮现成节律）：依赖排序（先起床后上班）+分波批处理+非大事日只存「一日印象」。
11. 千人访谈→7b 离线生成户籍访谈档案（一次性批量，扩 brain_digest；摘要路线已获 interview-summary 论文佐证 [已验]）。

**C. 不可搬**
12. GA 原版逐观察 LLM 评分与分钟级计划（算力；GA 自己 25 人 2 天烧数千美元 [已验]）。
13. Project Sid 千级持续 LLM+云 API（零 API 红线+成本）。
14. ACE/Inworld 语音表情全栈与云 SaaS（零服务器红线；Inworld 已转语音基建，路线更远；语音栈另立项）。
15. Voyager/MemGPT 实时代码生成与工具调用循环（7b 能力边界）。

**D. 对照五层大脑：缺口与模块建议**
- ①行为查表层：缺需求效用与检索排序——现按「人设卡×真实时间/天气」直查；建议加 needs 状态（确定性计算）+效用选择，行为不再只由时刻表驱动。
- ②台词池层：缺情绪维度——池 append-only 不改旧行；情绪做消费端路由（OCC 标签在既有桶间加权/排序），零数据变更。
- ③聚光灯层：prompt 组装升级——brain_digest（核心块，interview-summary 式摘要已证可行 [已验]）+recent_ring+一行教训+关系边，固定预算内注入。
- ④年轮进化层：从「压缩归档」升级为「压缩+反思+整理作业」（教训产出、合并、时间戳）。
- ⑤大事件反应层：加情绪余波（OCC 衰减曲线）与关系图路由（谁被波及、播报给谁），替代纯全城广播。
- **缺口1 动机层（最大）**：无持久需求状态，行为靠固定时刻表 → 模块 `needs.py`：表驱动衰减+效用选择；数据源=人设卡+真实事件流（禁 LLM 编造动机）；纯本地零成本，优先级最高。
- **缺口2 反思层**：年轮只压缩不学习 → 模块 `reflexion_job`：大事触发一行教训（[锚]合规）。
- **缺口3 关系层**：无「谁认识谁/好感/恩怨」持久图 → 模块 `relationship_edges`（带时间有效区间，Zep 式）；Project Sid 的治理/信仰/经济涌现皆以此为前提；也是 Radiant Story 式「挑提案人」（R-20260923 模式 8）的数据基础。
- 新增建议：城市涌现指标面板（婚恋/迁徙/物价/口头禅/自组织节日）=大事播报 V3 与居民提案 V3 的共同素材源；inZOI 证明 AI 市民是可讲的市场故事 [已验]。

## 附 · 来源清单与核验状态
[1] Park et al., Generative Agents, arXiv:2304.03442——全文 HTML 已抓：衰减 0.995、25 人 2 天数千美元 [已验]；importance 量程/阈值、反思树、涌现细节 [内置·另见 academic.md S19]
[2] Packer et al., MemGPT, arXiv:2310.08560——摘要已抓：OS 式虚拟上下文/多级记忆/interrupts/文档+多 session [已验]；letta.com [未验]
[3] Voyager, arXiv:2305.16291 [未验·抓取失败]；voyager.minedojo.org [未验]；Reflexion, arXiv:2303.11366 [内置]
[4] Project Sid, arXiv:2411.00114——题录已验（Many-agent simulations toward AI civilization·35 页 14 图）；机制数字 [内置]；altera.al [未验]
[5] NVIDIA ACE：developer.nvidia.com/ace [已验·2026-09 中文页，含 inZOI Smart Zois/PUBG CPC/PHARAOH/MIR5/Dead Meat/NVIGI/Audio2Face-3D/Audio2Emotion-3D/Chatterbox]；GeForce ACE 旧页 [已验·404]；Inworld 官网 [已验·2026-05 状态]；Ubisoft NEO NPC GDC 2024 新闻稿 PDF+官方 Teammates 新闻+Variety 2025 [已验]；Todd Howard 2026-02 [兄弟已验]
[6] OCC：IDSIA KI09 revisited（22 类/三分支/组合）[已验]；Ortony 2013 PDF（"distinguishes 22 emotion types"）[已验]；剑桥书页（三组+2022 第 2 版）[已验]；OCC_model 维基 [已验·404 负结果]
[7] AutoGen, arXiv:2308.08155；CAMEL, arXiv:2303.17760 [内置]；Sims smart terrain [内置·兄弟报告维基污染转内置]
[8] 千人模拟, arXiv:2411.10109 [已验·多源：arXiv 摘要/Stanford AI4PB「1,052 real individuals」/scispace「two-hour」/geometor「GSS 85%」/StanfordHCI/genagents 开源]；Sleep-time Compute, arXiv:2504.13171 [已验·题录+letta-ai/sleep-time-compute]；Park dissertation 2025（population-scale）[已验·官网]；Mem0/Zep [内置·未验]
[勘误] 调研中曾误记「100 天 10 秒」卷积调度论文与千人模拟的 arXiv 编号（2504.06416 与 2503.09990 抓取实为扩散模型与量子物理论文）；千人模拟正确编号 2411.10109 已多源验证；「100 天 10 秒」论文未能定位可靠来源，相关建议已改标为工程推断（B10）。本文件为本次任务唯一写入物，未运行修改性代码、未做 git 操作。
