# 看板「今日新增年轮」把相遇行重复计成年轮 — 2026-11-17 14:3x

## 症状（CEO 可见面自相矛盾）

同一天两个 CEO 可见面报不同数：

| 面 | 报数 | 生成时刻 |
|---|---|---|
| `census/export/city-dashboard.html`「今日新增年轮」 | **495** | 10:29（本轮重建前） |
| `census/export/city-today.html`「今日年轮」 | **489** | 13:09 |

年轮浮增是 append-only，两个数不可能同时正确。

## 根因

相遇轮让双方各写一句「年轮式互动」，落卡行格式与年轮行完全相同：

```
- 2026-11-17 「与 C-03646 相遇：水位计浮子卡在第三格，我正伸手去拨。」 [锚] ...
```

- `Tools/build_daily_issue.py`（city-today）：`RING_RE` 取行后**排除 `MEET_RE`**，
  `n_ring = 489`、`n_meet = 6` —— 正确口径（注释写死「相遇单列，否则当天联结的居民会被算成两环」）。
- `Tools/build_city_dashboard.py`（看板）：`ring_day_counts()` 只用 `RING_LINE = ^- (\d{4}-\d{2}-\d{2}) ` 计数，
  **没有排除相遇行** → 489 + 6 = 495。

差额 6 与当日相遇数 6 完全吻合。

## 实证

```
今日卡面行总数=495　相遇=0（按「日期后直接与」口径）← 该口径错，相遇行在「」内
按 city-today 口径（RING_RE + MEET_RE.match(text)）：
  MEET rows today = 6
  → 年轮本体 489，相遇 6
```

复现脚本（口径唯一来源 = import build_daily_issue）：
`dash=495 / city-today=495 / delta=0`（该脚本按行首日期直数，与看板同病，故两数相同——
这正是「同源断言测不出同源缺陷」的活样本）。

## 修法

`Tools/build_city_dashboard.py`

1. 新增 `MEET_LINE = ^- \d{4}-\d{2}-\d{2}\s*「\s*与\s*C-\d+\s*相遇[:：]`
2. `ring_day_counts()` 逐行先 `if MEET_LINE.match(line): continue`

口径与 `build_daily_issue` 对齐，看板历史曲线同样受益（凡有相遇行的日子此前都被高估）。

## 断言件补盲（`Tools/daily_kpi_assert.py`）

原断言件只验 city-today，看板的错因此长期「两闸全绿」。本轮：

- 新增 `check_dashboard()`：看板「今日新增年轮」必须等于同一实算值；
- 勘正原 docstring 的归因错误（原文称 489 为错、495 为真值，实为相反）；
- 默认运行同时断言两面，任一面漂移即 FAIL。

## 验收（实弹）

```
$ python -X utf8 Tools/daily_kpi_assert.py
今日年轮     page=489 data=489 OK
今日相遇     page=6 data=6 OK
今日开口的居民  page=490 data=490 OK
居民卡总数    page=10114 data=10114 OK
城区       page=6 data=6 OK
看板今日年轮 page=489 data=489 OK
verdict: PASS
```

负控 3 例（闸未被改松）：

| 负控 | 手法 | 期望 | 实得 |
|---|---|---|---|
| N1 | 今日页「今日年轮」篡改为 500 | FAIL | FAIL n=1 |
| N2 | 看板「今日新增年轮」篡改为 495 | FAIL | FAIL n=1 |
| N3 | 两面对齐后原样 | PASS | PASS |

历史值回归：重建后 11-16=570（与 city-today「昨日年轮 570」一致），11-12/13/14/15 = 745/792/1082/1237 未变。

## 出生地拦截

同类病（「同源断言掩盖同源缺陷」）已在断言件层面收口：断言件通过
`import build_daily_issue` 复用唯一口径，且覆盖面从 1 个扩展到 2 个可见面。
新增 CEO 可见面若沿用旧 RING_LINE 直数口径，需在本断言件登记。
