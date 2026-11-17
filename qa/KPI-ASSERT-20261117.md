# KPI-ASSERT · 当日面数字一致性断言（2026-11-17 R336x）

## 立单缘由（实测发现，非假设）

`round_daily.py` 现有两道闸都管不到「数字落后」：

| 闸 | 判据 | 漏什么 |
|---|---|---|
| `_is_stale` | 输出 mtime vs 输入 mtime | 页面 13:09 生成、13:2x 又落年轮 → mtime 仍是今日，判 fresh |
| `--values` A1-A4 | 非空壳/带当日/有记录/可返回 | 数字错了（489 写成 500）四检全过 |

与 2026-10-27「12 面静默停更 15 天」同族：**闸问的是「有没有生」，不问「生得对不对」**。

## 交付物

- `Tools/daily_kpi_assert.py`（新增，零 LLM·确定性·只读）——直接 `import build_daily_issue`
  复用 `load`/`card_paths`/`MEET_RE`，口径唯一来源，不重复实现相遇行与三源卡判定。
- `Tools/round_daily.py` v0.30——`--values` 分支末尾接 KPI 断言（try/except 包裹，
  缺件/异常不阻塞既有守卫）；常规 `--check`/`--run` 路径零改动。

## 断言口径（5 项）

今日年轮（排除相遇行）／今日相遇／今日开口的居民（unique id）／居民卡总数／城区数，
逐项与 `build_daily_issue` 实算比对。不一致 rc=1 并打印差值正法命令；面缺失 rc=2。

## 验收记录

| 项 | 命令 | 结果 |
|---|---|---|
| 自测（真实面） | `daily_kpi_assert.py` | 489/6/490/10114/6 全 OK → verdict PASS rc=0 |
| 负控（篡改副本） | `--page %TEMP%\kpi-neg.html`（489→500） | 今日年轮 MISMATCH，其余 OK → rc=1，临时件已删 |
| 接线（聚合闸） | `round_daily.py --values` | faces=30 + 5 KPI 全 PASS，VALUES-PASS rc=0 |
| 语法 | `py_compile` 两文件 | rc=0 |
| 规范 | `ruff_gate.py` | 2 file(s) CLEAN（SIM115/RUF059 已修） |
| 回归（常规路径） | `round_daily.py --check` / `--run` | stale=0 ran=0 failed=0 verdict PASS，行为零变化 |

## 边界

- 只断言 `daily` 档的 today 面；其余 29 面仍由 `--values` A1-A4 守卫（kpi 面按需扩）。
- 页面口径变更（KPI 标签改字）时断言会报 MISMATCH → 属预期，改标签须同步断言件。
