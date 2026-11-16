# 族表 ↔ 人话 hint 覆盖闸（R3227·2026-11-16）

## 病根（R2789 同型复发·非新缺陷）

`Tools/ring_open_family.py` 的 `FAMILIES` 是配额闸的族表（v1.6 已 12 族），
`Tools/evolve_citizen.py` 的 `FAMILY_OPEN_HINTS` 是喂给 4B 的人话说明。
两表靠人手同步，渲染点第 3268 行是 `FAMILY_OPEN_HINTS.get(f, f)`——
**族表扩了而 hint 没跟，就把英文族名当"人话"拼进提示词**。

2026-11-16 实况：族表 12 族，hint 只登记 5 族（HAND_DEICTIC／TIME_OPEN／
WEATHER_ABSTRACT／PROP_DEICTIC／RAIN_SETTING_DEICTIC），空档 7 族为
BOOK_LEDGER_DEICTIC／STOVE_EDGE_DEICTIC／DOOR_PROP_DEICTIC／WIND_AGENT_OPEN／
WIND_SCENE_OPEN／DISTRICT_ANCHOR_OPEN／FIRST_PERSON_ACTION_OPEN。

当日 `state/ring-refusals.jsonl` 25 行族分布实算：**`WIND_AGENT_OPEN` 11 条
（44%）为最大单一族**，正落在空档里——模型当日被风族闸拦下，收到的却是
``WIND_AGENT_OPEN`` 这串机器码，既不知被禁什么，也必然重入同族
（gap #68「同提示词 → 同吸引子 → 三次用尽 → 席位留 due」的复现条件）。

## 修法（两处代码 + 一处上闸）

1. `FAMILY_OPEN_HINTS` 补登记 7 族人话 hint，措辞与既有 5 族同风格
   （只给"以「X」「Y」起句"的词组形状，**不给整句**——避免 hint 自己变成
   canned 句被照抄，R2760 判例）。
2. `family_blk` 尾部原恒写「第一个短句不要从「手」字起、不要用「我正」起句」，
   当日禁的是风族时该句与 hint 正面矛盾（R2588 同型自相矛盾）。改为族感知：
   `HAND_DEICTIC` 在场 → **逐字保留原句（零漂移）**；其余族 → 中性表述
   「但第一个短句不要落进上面点名的任何一种起句形状。」
3. 上闸：新增 `qa/test_family_hint_coverage.py`（9 项正负控）。族表每增一族、
   hint 未同步 → 测试即红，逼同批登记，永不再靠人手记性。
4. 同型空档一并收口：第二句吸引子面 `ring_open_family.SECOND_ATTRS` 与
   `SECOND_LABELS` 也是两表人工同步（渲染点 `second_label` 走
   `.get(name, name)`），同样在闸内加 `SECOND_ATTRS ⊆ SECOND_LABELS` 与
   "label 无机器码形态"两项（R3228）。

### 全仓 `.get(x, x)` 扫描结论（为何不扩大修面）

本轮扫 `Tools/*.py` 同类同键兜底共 **30 处**，其中 28 处是 `SPECIES_CN`／
`DISTRICT_CN`／`STATE_CN`／`NEED_CN`／`flag_zh`／`labels` 这类**显示面中文映射表**
（兜底给 code 属正确行为，且这些串不进 LLM 提示词）。真正"值进提示词"的面只有
`FAMILY_OPEN_HINTS` 与 `SECOND_LABELS` 两处，均已在闸内。属修病灶不修同形。

## 证据（本轮实跑）

| 项 | 结果 |
|---|---|
| `py_compile Tools/evolve_citizen.py` | rc=0 |
| `qa/test_family_hint_coverage.py` | **Ran 9 tests … OK**（正控：12 族全覆盖／无孤儿 hint／hint 无机器码形态／非空／不照抄示例句／`SECOND_ATTRS ⊆ SECOND_LABELS`／second label 无机器码；负控 2：虚构族名被判缺失且渲染出机器码／hint 写成族名原文必红） |
| 渲染冒烟（`build_prompt` 实测 8 族） | 逐族 `machine_code_in_prompt=False`、`hint_rendered=True`；`FAIL=[]`、rc=0 |
| 零漂移校验 | HAND 在场：`hand_legacy_sentence_kept=True`（原句逐字保留）；风族在场：中性句命中 |
| 回归 `test_opening_refusal_memo` | Ran 5 tests OK |
| 回归 `test_citywide_refusal_ban` | 12 项全 PASS（verdict: PASS） |
| 回归 `test_round_daily_dep_fp_skip` | Ran 7 tests OK |

## 判据与失效条件

- 唯一判据：`ring_open_family.FAMILIES` 键集合 ⊆ `FAMILY_OPEN_HINTS` 键集合，
  且每条 hint 不含 `ALL_CAPS_UNDERSCORE` 机器码形态。
- 能力边界：本闸只保证"模型收到的是人话描述"，**不保证**模型会因此换族——
  族占比是否真下降，须待 19:00 后落环批次用 `opening_capacity --window 12`
  复测（目标：`WIND_AGENT_OPEN` ≤25%）。
- 失效条件：族改名后 hint 表残留旧名 → `test_no_orphan_hint` 会红。
