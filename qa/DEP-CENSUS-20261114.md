# 可见面依赖边普查（v0.25 全量收口）

- 轮次：R2908 · 2026-11-14 11:0x-11:3x @BigLife-OSLoop
- 病根：T-20261112-04 同族第 11-20 面（R2905 诚实边界留下的普查活）
- 判据：faces/daily 档只问产物自身年龄（`age>1.0`／`mdate!=today`），不问喂它的数据源改没改
- 后果：数据每轮重生而页面在 24h 内永远「看起来新」，CEO 面停在上一批环/行为线之前的口径

## 一、实测：十面全部陈旧于其源（修复前）

| face | out mtime | 最新源 mtime | gap |
|---|---|---|---|
| coverage | 11-13 13:44 | 11-14 11:10 | **-21.4h** |
| objects | 11-13 13:46 | 11-14 11:10 | **-21.4h** |
| social_graph | 11-13 16:24 | 11-14 11:10 | -18.8h |
| growth | 11-13 17:50 | 11-14 11:10 | -17.3h |
| ops | 11-13 17:39 | 11-14 11:10 | -17.5h |
| meets | 11-14 01:02 | 11-14 11:10 | -10.2h |
| reflections | 11-14 01:42 | 11-14 11:10 | -9.5h |
| meet_candidates | 11-14 09:31 | 11-14 11:10 | -1.7h |
| voices | 11-14 10:10 | 11-14 11:10 | -1.0h |
| map | 11-14 10:10 | 11-14 11:10 | -1.0h |

修复前 `round_daily --check` 对这十面全部判 `fresh`。

## 二、修法

1. `Tools/round_daily.py` v0.25：`DEPENDS` 补十面源登记（源类型三分：行为线每轮重写的
   `citizens-light.jsonl`／每日 `--regen` 派生面／append-only 台账；`objects`/`meets` 扫
   registry 年轮行故并补 `evolve-cursor` 主信号）。
2. `DEPENDS_FLOOR_OVERRIDE`：除 `map`(864KB)、`social_graph`(1.6MB) 保持 60min 冷却防
   churn 外，其余八面冷却归零（≤95KB、重建 <1s，源每轮变）。
3. `Tools/refresh_census_index.py`：幂等分支（内容相同不写文件）补 `os.utime`，消除
   `census_index` 每轮 dep-mtime 假红（`--check` 只读不 touch）。

## 三、负控（判据灵敏度，非假绿）

- NEG-A：`touch state/evolve-cursor.json` → `objects`/`meets` 精确报
  `dep-mtime:state/evolve-cursor.json`（依赖边真在工作）。
- NEG-B：`city-voices.html` 回拨 -2d → 报 `outdated:2d`（日期判据未被新逻辑破坏）。
- NEG-C（幂等）：内容不变的 `census/INDEX.md` 重建后 `--check` 不再报红（stale 1→0）。

## 四、结论

- 修复后 `--run` stale=12 ran=13 failed=0 PASS；`--check` **stale=0 PASS**。
- 十面重建全部由真实数据变更驱动（git diff 非空），非空转刷新。
- 诚实边界：PASS 为闸门证据非内容质量判定；本轮零云端调用。
