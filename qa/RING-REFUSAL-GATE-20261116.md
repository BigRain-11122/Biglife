# 年轮硬拒归因读数（2 生产日·2026-11-15 → 2026-11-16）

- 执行轮：R3205 @BigLife-OSLoop（2026-11-16 11:4x·让路窗内零 LLM）
- 数据源：`state/ring-refusals.jsonl`（R3115 起落盘）→ 归因面 `census/export/city-ring-refusals.json`（generated_at 2026-11-16 11:35:43）
- 复跑：`python -X utf8 Tools/round_daily.py --check`／`python -X utf8 Tools/build_ring_refusals.py`
- 对应任务：T-20261115-04「换靶」必办步——「跑满 2 个生产日取 gate 分布，**再**据分布决定改哪一处；禁无分布数据前动阈值或窗口」
- **本文件不出裁决**：裁决面属 R3204（跨席传染配额闸补丁 + 19:00 实弹负控协议）。本文只交读数与负控基线。

## 一、总量与分布

总量 80 条（11-15=55，11-16=25）。

单闸计数（一条可多闸同拒）：

| 闸 | 次数 | 占比 |
|---|---|---|
| `recent-dup-phrase` | 67 | 83.8% |
| `recent-family-opening` | 53 | 66.3% |
| `opening-family-quota` | 16 | 20.0% |
| `rain-invented` | 7 | 8.8% |
| `recent-dup-opening` | 6 | 7.5% |
| 其余 6 类（sky-mismatch / batch-dup-opening / signal-state / typhoon-invented / time-morning / mist-import） | 各 1 | — |

组合 Top：`recent-dup-phrase + recent-family-opening` = 50 条（62.5%）。

## 二、三组基线数（供 19:00 负控直接比对）

1. **同人重试面已归零**：`retry_livelock` 11-15 = rows 55 / 35 人 / 5 人重复 / max_repeats **15**（C-03117 同一 opening12 连撞 15 次）/ wasted_calls **20**；11-16 = rows 25 / **25 人** / 0 人重复 / max **1** / wasted **0**。⇒ R3115「逾期席硬拒后 next 推 +1d」实测生效。
2. **族闸不是主因**：`opening-family-quota` 仅 16/80=20%（原立单假设「族闸结构性失效」被数据否定）。
3. **跨席开口复用仍在**：11-16 25 条拒稿只对应 17 个不同 opening12，4 个开口被 ≥2 位居民各撞一次、多烧 8 条；头部 `风把塑料布吹得啪啦响，我`（4 人）/`这会儿手边最碍事的就是这`（3 人）/`风把雨棚掀得直响，我正把`（3 人）/`风撞在窗玻璃上闷响，我正`（2 人）。

## 三、对 19:00 负控的口径建议（不改既有协议，只加一条硬线）

既有协议（R3204）三数：hard-refuse 数 / `citywide-refusal-ban` 命中数 / 落环数；回退口＝落环数低于基线或命中数 >同批 30%。

**建议追加第四条硬回退口**：`retry_livelock.wasted_calls` 与 `max_repeats` 不得从本轮基线（0 / 1）升高。理由＝配额闸若实现为「命中即换人」，理论上同人面不会恶化；若实测升高，说明换人逻辑把同席又拉回队头，那就是把 R3115 已修好的调度缺陷重新引入——这比落环数更早暴露问题。

## 四、诚实边界

- 样本 2 生产日 / 80 条，且 11-15 有活锁污染（55 条中 20 条为重试浪费）——「占比」判据应在 11-17 满 3 日后复核一次再据以落任何永久阈值。
- 本条**未做任何代码改动**（`Tools/evolve_citizen.py` 保持 R3204 还原态，工作树零残留），是读数与基线交付，不是修复回执。
