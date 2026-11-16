# 世代池漂移证据面接线回执（R3244·2026-11-16 17:2x）

## 缺陷（出生地=可见面静默陈旧）
- 事实：genes 今日连开世代 gen3/gen4/gen5/gen6（habits 137→163），而
  `census/export/persona-drift.json` 停在 **2026-11-15 11:39:28 / pool_len=138**（gen2 口径）。
- 影响：T-20261115-02 决策 b「老居民按旧快照取模零漂移」的唯一机器证据面陈旧，
  读者（含 CEO）打开看到的是两天前的分母与池长；gen3–6 四次增补无漂移证据。
- 病根同族：T-20261112-02（有生成器、有产物、无任何轮次引用）。`persona_drift.py`
  从未进 `round_daily.py` 登记表，只能靠人手想起去跑。

## 修法（最小·零 LLM·幂等）
1. `Tools/round_daily.py` FACE 登记表新增：
   `("persona_drift", "faces", "persona_drift.py", ["persona-drift.json"])`
2. `DEPENDS` 新增依赖源：`genes/persona-pool-generations.json`（每次 sync 改写）+ `census/registry`
   （新人入册改分母）。无基因变更的日子靠冷却下限（60min）+ 依赖指纹抑制，不白跑。
3. 证据面先行手工刷新：`python -X utf8 Tools/persona_drift.py` → `pool_len=163 -> wrote
   census\export\persona-drift.json`（耗时 0.80s）。

## 当日读数（gen6 后）
| 指标 | 读数 | 判读 |
|---|---|---|
| pool_len | 163 | 与 `persona_generations --check` habits=163 同口径 |
| citizens | 10114 | 与 QC 实巡同数 |
| hb/gen_freeze moved | 0 / 10114（share 0.00%） | 老居民零漂移**成立** |
| hb2/gen_freeze moved | 0 / 10114（share 0.00%） | 同 |
| hb/mod_len moved | 10063 / 10114（99.50%） | 若不冻结世代则几乎全员漂移（对照=冻结必要性） |

## 负控（实跑）
- 正控：`round_daily --check` → `persona_drift faces skipped-check fresh`，全表 `stale=0 verdict: PASS`。
- 负控①（年龄分支）：把产物 mtime 改回 `2026-11-15 11:39:28` → `outdated:1d`，
  `verdict: STALE remaining=1 persona_drift(outdated:1d)`；`--only persona_drift --run` → `rebuilt`，
  再 `--check` → `stale=0 PASS`。**闸有效**。
- 负控②（值域分支不受影响）：`round_daily --values` → `VALUES-PASS n=30`（JSON 面不参与 HTML 值域闸，零回归）。
- 依赖分支：合成触发被冷却下限+依赖指纹正确抑制（内容未变不重建），
  与 `gene_ledger`/`lexicon` 同代码路径；未改基因正本，故未做破坏性触发。

## 诚实边界
- 本回执证明「证据面已接入轮次 + 陈旧可被机器判出 + 当日读数为零漂移」，
  不证明历史 gen3–gen5 每次增补当时都有证据（实则没有，本条即补上的缺口）。
- 漂移指标的语义（mod_len 99.5% vs gen_freeze 0%）沿用 `persona_drift.py` 既有口径，本次未改判据。
