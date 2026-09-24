# BigLife 池/问候库 异机可执行任务包 v1.0

法源：集团 P-2026-09-24-55 机队总动员派工③「可借池生成任务包→空窗 GPU 认领」·T-20260924-06⑤。
交付时点：池水位 v1.8 达标（1200·2026-09-24 R102）后按单约定「待②补深后一并打包」落件（2026-09-24 R103）。

## 一、布局（解包即跑）

脚本按 `Tools/ → 包根` 相对解析路径，包内已保持同构布局：

```
package/
├── Tools/            pool_gen.py · pool_audit.py · draw.py · city_broadcast.py（副本）
├── cognition/        pools.json（快照 1200 条）· greetings.json（快照 301 条）
└── README-PACKAGE.md 本件
```

解包到任意目录后，在**包根**执行下列命令即可。

## 二、依赖分级

- **核心任务（池/问候补深 + audit）**：Python 3.10+（纯标准库，零 pip）+ 本地 Ollama（http://localhost:11434，模型 `qwen2.5:7b`）。零仓外依赖。
- **扩展任务（draw --auto / city_broadcast）**：另需 BigLife 仓 clone（census export 只读 + FluxVerse world 只读）。无仓面时不可跑，属分级外任务。

## 三、命令

```bash
# 补深（幂等·断点续跑·每桶原子落盘·单写锁自动管理）
python -X utf8 Tools/pool_gen.py --append --target 15 --sprite-target 10
# 问候面（契约 = cognition/GREETINGS.md v1.0：greet floor 6/target 10·faq floor 2/target 3）
python -X utf8 Tools/pool_gen.py --greetings
# 审计（判据门：verdict=PASS 才算数，hard_fails=0 为硬项）
python -X utf8 Tools/pool_audit.py
```

## 四、计量与纪律（token-economy · 本地算力律）

- 一切生成走本地 Ollama；随产出记录计量行 `tokens: local=N api=0 api_reason=-`。
- 三闸不动（令④）：①问候面零环境词（天气/天体/时段词族禁入）②面内+跨面（对 pools.json）零重复（audit hard 项）③audit PASS 才可回灌。

## 五、回灌流程（勿另建通道）

1. 异机产出 `pools.json` / `greetings.json`；
2. 本仓 `Tools/pool_audit.py` 复跑，verdict=PASS 才收；
3. 定向 commit 入本仓 `cognition/` 正典（无人值守轮 commit 尾标身份律=cph4/versioning §4.1）。

包内 `Tools/` 副本仅为「即领即跑」便利；**演进正典=本仓 `Tools/` 与 `cognition/`**，副本漂移一律以正典为准。

## 六、基线指纹（快照源=2026-09-24 R103 commit 态）

| 数据件 | 实测计数 | 说明 |
|---|---|---|
| pools.json | **1200 条**（axes 72 桶×15 + sprite 12 桶×10） | v1.8 水位·CODEX §十二·达标自停（重开触发=新事件族/节日/CEO 令） |
| greetings.json | **301 条**（greet 28 桶×10 + faq 7 桶×3） | 实测计数；R100 台账 322 为回滤前口径差异，以本实测与 audit PASS 为准；∈令面 [200,500] |

消费方：FluxVerse M2 NPC 引擎 / CityWatch（经 census 导出面间接消费）·集团空窗 GPU 认领机。
