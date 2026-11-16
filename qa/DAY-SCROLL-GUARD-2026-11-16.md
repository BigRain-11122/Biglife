# 跨日失效闸（DAY_SCROLL）落地回执 — 2026-11-16 R3213

## 要解决的问题（实证）

`Tools/round_daily.py` 的 faces 档原有两条新鲜度判据：
1. `age > 1 天` → stale；
2. 源 mtime 前进 / 自时间戳 / 脚本指纹 / 依赖指纹变化 → stale。

「今日 N 环 / 近 14 日逐日 / 分钟前」这类页面的渲染值由**构建时刻的
`date.today()`** 算出。日界翻转时源通常一动不动：`_dep_mtime_stale()` 直接
`return None`（源 mtime 未前进），`age` 也只到 0.5 天 —— 于是页面可以整整
**24 小时**继续对 CEO 显示昨天的「今日」。这与 R3212 已修的「同内容重写造成
指纹一致」是同一缺陷的两个形态，前者管小时内漂移，后者管跨日。

## 改动（最小、可回退）

`Tools/round_daily.py`：

- 新增 `DAY_SCROLL` 九面（每项均按代码实读确认按构建时刻 today 算当日量/窗口）：
  `dashboard`（近 7 日窗口 + 今日新增年轮 KPI + 空窗段）、`proposals`（今日新增）、
  `reflections`（今日新增 + 近 14 日 + 近 7 日日均）、`ring_refusals`（今日 KPI + 逐日逐时）、
  `ring_recency`（今日落环 / 叙龄分档）、`ring_quality`（`cut = today - N` 窗口）、
  `ring_trend`（近 N 日窗口）、`ring_openings`（窗口相对 today）、
  `ops`（分钟前 / 小时前相对时距）。
- 新增 `_date_rollover_stale(key, out_paths, now_date)`：产物构建日 != 今日 → `stale`，
  理由串 `date-rollover:YYYY-MM-DD->YYYY-MM-DD`。
- 仅接在 faces 档（daily/input/data 档本就以构建日判新，不重复）。

## 验证（可复跑）

```
python -X utf8 qa\test_round_daily_dep_fp_skip.py
→ Ran 7 tests ... OK
```
- 正控：日滚动面构建日=昨天（age≈0.5d，不触发 age>1d）→ 返回 `date-rollover:*`。
- 负控：非日滚动面同样构建日=昨天 → 返回 None（不冤判）。
- 正控：日滚动面当日已重建 → None（不每轮空重建）。
- 注册面反例：`growth` 的「今日」只出现在 docstring → 不入集合（防 churn）。

当日实跑（13:29）：

```
python -X utf8 Tools\round_daily.py --run
→ stale=0(首跑) / stale=1 ran=2(写状态面后：dashboard+index 重建) failed=0 verdict=PASS
```

## 诚实边界

- 本闸修的是「跨日不刷新」，不证明页面内容质量；不改变既有 60 分钟冷却与
  指纹压制对普通面的防 churn 语义。
- 今日全天各处页面均为当日构建，故本改动在**今日无可见数值变化**；收益在
  次日 00:0x 起生效（届时上述九面自动重建）。
- 未纳入 `ring_picks`（day 取 `max(per_day)` 由数据决定）与 `today/rumors/life`
  （daily 档已按构建日判新），避免无谓重建。
