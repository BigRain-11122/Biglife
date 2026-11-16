# 风句限位（R3229·2026-11-16）

## 一、靶面实读

- `opening_capacity --window 12`：`skeletons=26 / examples=6`，`attribution: invented=20 (100%)`，
  `waste: rows=20 distinct=13 multi=4 cross_cid=4 wasted=7 (35.0%)`。
  invented top3 中两条为风形（`风把塑料布吹得…`、`风把雨棚掀得…` 各 rows=3/cids=3）。
- `state/ring-refusals.jsonl` 当日 25 行：族分布 `WIND_AGENT_OPEN 11`（44%，最大单一族）、
  `HAND_DEICTIC 4`、`DOOR_PROP_DEICTIC 3`、`TIME_OPEN 3`；闸分布
  `{recent-dup-phrase, recent-family-opening}=14`、`opening-family-quota=5`、
  `rain-invented` 掺入 4。
- 今日真实开口合并面（accepted 323 + refused 80 = 403，12 字截断口径）：含风断言形状 81 条（20%）。

## 二、诊断（含一次自我纠错）

**先错后正**：本轮起初用**自造 sig**（`cloud 18.3°C`，无 wind 字段）测影响面，据此判「实况无风速数据→
全城风断言是编造」，方向错误。实跑 `real_signals()` 得
`sig["weather"] = "cloud 18.1°C wind 9.8m/s"`——真实风速有值，且 9.8 m/s 属大风天，
风句合法。**教训**：影响面测算必须用本仓真实 sig 构造器，禁用手搓 sig 当实况
（与 M204「什么都慢≠什么都不在」同族：数据没读到 ≠ 数据不存在）。

真正病根=**提示词位置冲突**，不是诚实缺陷：

1. `weather_recap` 钉在提示词**尾部**（离输出位最近，权重最高），大风天它要求「风只许按实况量级措辞」
   并给出 `WIND_BIG_HINTS` 整句示例（形如「风把雨棚掀得直响」）；
2. 中部骨架指令要求「按分配到的骨架从手上营生写起」。
3. 两条指令同权重时，模型选了离输出位更近的那条——于是风句成了开头。
   当日最大拒稿族 44% 与 9 条重复开口全部由此而来。

## 三、修法（两件，最小改动）

1. **提示词限位（主修法）**：`weather_recap` 的风分支新增一句
   「风句只许放在第二个短句或句中，严禁用风句开头（开头句按上面分配给你的骨架写）。」
   大风/小风两支都生效；空实况（`wx=""`）仍返回 `""`（零漂移律）。
2. **闸侧对齐（backstop）**：`ring_violations` 的 `wind-nodata` 原先只认量级词
   （风大不大/微风/风轻），现补认施事/布景形状（风把/掀/撞/扯/刮/灌/扑/卷/钻/顶/推/扫/裹/吹、
   风从窗/门/巷/缝…），并先掩掉器物名与专名（风控/台风/风扇/风筝/风铃/风衣/风箱/风车/风镜/
   风油精/风机/风湿/风干/风门）；`风声/风里/风凉` 放行（消息/旧习惯语/风凉话，语义歧义）。
   该支**只在实况确实无风速读数时**生效，与提示词既有的「完全不提风」同口径；
   有读数日不介入（量级闸 wind-under/wind-over 照旧）。

## 四、验证（本轮实跑）

- `python -X utf8 -m py_compile Tools/evolve_citizen.py` → rc=0。
- 新增 `qa/test_wind_nodata_face.py` → **Ran 8 tests OK**
  （正控 3：施事 6 句全拒／量级词不回归／有读数不误拒；负控 1：8 条器物与专名零误伤；
  提示词 4：大风/小风/无读数/空实况）。
- qa 全量回归：`test_citywide_refusal_ban` PASS、`test_family_hint_coverage` 9 OK、
  `test_family_prompt_consistency` 10/10 ALL PASS、`test_opening_refusal_memo` 5 OK、
  `test_self_dup_near` 4 OK、`test_round_daily_dep_fp_skip` 7 OK、`test_meet_mutual_ref` PASS。

## 五、诚实边界

- 本轮为让路窗（工作日 09:00-19:00），零 LLM、无新落环，**效果未在生产上验证**。
- 生效时点=19:00 首批年轮；验收判据＝次日 `ring-refusals` 当日新增中 `WIND_AGENT_OPEN` 占比
  低于今日 44%，且 `opening_capacity --window 12` 的 `waste` 低于今日 35%、invented top3
  不再被风形占两席。
- 未改族配额阈值（`FAMILY_QUOTA=0.25`）、未改 `TABLE_EPOCH`（族表未动）、未动骨架池 26 条。
