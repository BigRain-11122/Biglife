# 消费方接线数判据 v1.0（CONSUMER-WIRING）

- **法源**：D-20260930-06 全域改进清单 **XL-17 BigLife「消费方接线数判据」**（回执窗 2026-10-07·ack=F-20260930-BL03）·任务单 T-20260930-01 分步①②
- **工具**：`Tools/consumer_wiring.py` v1.0（只读扫描器·字节预过滤·分消费方进度输出·--qc 双跑一致+导出面存在性断言）
- **刷新节律**：status-export results 区常设行（盘面直数非转录·每轮随刷）·复核窗 10-07

## 一、定义与计数规则

**消费方接线数** = 对 census/export 导出面存在**实际程序化接线**（代码/配置文件内容引用）的下游消费方仓计数。

1. **导出面闭集**（12 jsonl 面+1 路径面·与 census/export 盘面文件一一对应）：citizens-light / citizen-needs / citizen-behavior / citizen-tasks / citizen-relations / citizen-anchors / citizen-assembly / citizen-initiatives / citizen-atlas / citizen-persona / citizen-goals / citizen-voice（.jsonl）+ `census/export` 路径面。
2. **消费方仓闭集**（通知族 T-20260923-01 五方→四仓映射·Biggame 量产线与 MiniGame 观测窗同仓）：gaming/FluxVerse、gaming/MiniGame、domain（BigDomain）、media（BigStream）。
3. **计数规则**：仓内代码/配置扩展（.py/.cs/.js/.ts/.html/.ps1/.json/.yaml 等 20 类）文件内容命中 ≥1 导出面 token → wired=True，count=wired 仓数。**文档级引用（.md/.txt）不计**。
4. **排除规则**：cph4=集团工具面（审计/研究探针可命中 census 字样）非下游消费方 → 证据仍录但**不计入 wired_count**；消费方仓内废弃会话日志（docs/_trash/ auto-save）命中=噪声记档不计入判读。
5. **证据指针**：file:line+摘录 ≤110 字符（--qc 断言·append-only 无状态）。

## 二、诚实基线与首跑实测（2026-09-30 12:4x~12:5x @R770）

- **集团审计基线**：D-20260930-06 全域账定谳 BigLife「下游仅文档级消费」（文档级口径=0）。
- **本判据首跑代码级实测：消费方接线数 = 3**（扫描 12,491 代码文件）：
  - **fluxverse wired**（13 证）：`watch/city-watch.ps1`+`watch/population-check.ps1`+`Tools/perceptor/probes/census.ps1`（读 citizens-light.jsonl）+`Tools/perceptor/probes/street_behavior.ps1`（读 citizen-behavior.jsonl）+`Tools/city/bake-resident-identity.ps1`/`bake-resident-street.ps1`+`City/Assets/Editor/ResidentIdentityProof.cs`（Unity 侧身份校验）。
  - **biggame-minigame wired**（14 证·主证=`tools/PixelTownBoard.ps1` L1204 读 citizen-persona.jsonl；辅证=`硅基生命元宇宙-data.js` 窗口数据镜像 12 处含 census/export 全 face 名）。
  - **bigdomain wired**（8 证·主证=`src/sandbox/lobby/city.py` L87+`config.json` 读 citizens-light.jsonl〔参观端 lobby〕；`docs/_trash` auto-save 3 证=废弃会话日志噪声记档）。
  - **bigstream 未接线**（0 证=诚实态·素材接口 docs/bigstream-material-interface.md 点单制文档级·与判据口径自洽）。
  - **cph4-tools**（2 证·`research/sprites-20260924/bake-residents.ps1`+`atlas/atlas-residents.ps1` 研究工具读 light 面）=集团工具面**不计入**。
- **口径差异如实记**：审计「文档级消费 0」vs 本判据「代码级接线 3」——判据以代码级证据指针为准（D-20260930-08「探针输出为唯一权威」同律），差异面随回执窗 10-07 呈报。

## 三、红线

兄弟仓只读零写入（铁律④）·本司不代消费方写接线（反无消费方立项律）·分步③=与 FluxVerse M2/CityWatch/City3D 消费窗口对接期对齐（消费方需求单驱动）。

## 四、待收口

- `--qc` 双跑逐字节一致+导出面存在性断言（R770 预算尽留单下轮跑）。
- 分步③ 消费方窗口对齐（随消费方需求单）。

*登记：本件=判据设计件（D-20260930-06 授权窗·定义面零 census 数据面变更=T2 免登记 R405 判例）·status-export results 行=R619 先例零新 T2。*
