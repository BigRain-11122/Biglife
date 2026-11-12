# 年轮品质验收证据 · 2026-11-13（T-20261112-01 第 2 日窗口）

生成：2026-11-13 04:0x @BigLife-OSLoop（确定性脚本取证，零 LLM）
命令：`python -X utf8 Tools/ring_material_check.py`、`python -X utf8 Tools/ring_quality_trend.py --days 7`

## 一、验收线 1：素材有效量（连续 3 生产日）

| 日期 | motif 名义/有效 | rumor 名义/有效 | 判定 |
|---|---|---|---|
| 2026-11-11 | 0/0 | 0/0 | MISSING |
| 2026-11-12 | 8/8 | 7/7 | ready |
| 2026-11-13 | 8/8 | 3/3 | ready |

`streak=2/3` → **IN-PROGRESS**（第 3 日窗口未到，验收未结）。有效量列由 evolve_citizen 的 trigger-free 过滤器直接 import，口径单源。

## 二、验收线 2：tmpl 缺陷率 <10%

| 日期 | 环数 | 缺陷率 |
|---|---|---|
| 2026-11-12 | 729 | 16.0% |
| **2026-11-13** | **247** | **3.2%** |

`recent7_rate=31.6%`，历史最好值刷新为 **3.2%（2026-11-13）**，此前最好 14.3%（10-20），最差 63.8%（10-12）。
→ **单日已首次跌破 <10% 验收线**；但验收要求 3 生产日窗口齐备，且 11-13 环数仅 247（样本偏小、当日未跑满），**本项记「首验达标·待 3 日复验」，不结单**。

## 三、新发现（未修·只观测）：开场族 HAND_DEICTIC 25.1%

`opening-family: 2026-11-13 247 环 HAND_DEICTIC=25.1%（线 25%）verdict=OVER`

- 量级：247 × 25% = 61.75，即 **62 环比线多 1 环**（边际越线，非结构性崩坏）。
- 批内配额闸（`evolve_citizen.py` L3465-3475，家族占比 >25% 即封该族给后续座位）按「落环后计数」正确实现，昨日 42.8%→今日 25.1% 说明该闸**已在工作**。
- 越线 1 环的候选解释（**未验证，禁据此改闸**）：相遇轮/反思轮写卡走的是批外路径，可能不消费本批 `today_family_counts` 家族台账；若成立，趋势面统计到的手族增量包含批外环。
- 下轮动作：按来源拆分当日 247 环（evolve 批 / meet / reflect 各自开口族占比）复算，确认越线归属后再决定是补台账还是维持只观测（承 T-20261112-05「吸引子只观测待判」纪律，禁为 1 环改闸换绿）。

## 四、同轮门禁实况

- 事件回放闸：`cards=10111 events=42230 replayed=10111 schema_errors=0 mismatch=0 coverage unexpected_missing=0` → **PASS**
- QC 巡检：`cards=10114 evolved=10114 problems=0 dup_rings=37/37` → **PASS**
- 语言池：`72/72 + 12/12 + greet 28 + faq 7 + neg 6·6，hard_fails=0` → **PASS / SELF_TERMINATE**
- 日更面：`round_daily --run` 30 项，stale=1（dashboard 重建）、ran=2、failed=0 → **PASS**

## 五、诚实边界

缺陷率 3.2% 是「模板句/重复短语」口径，不等于「好看」；本档只证明机械缺陷显著收敛，审美与情感面仍由 CEO 终审与 spotlight 抽验把守。
