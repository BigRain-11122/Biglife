# 相遇写入路径出生地拦截 —— 常驻回归自测（T-20261116-16 / R3291）

- 时间：2026-11-17 03:4x @BigLife-OSLoop（夜窗·零 LLM）
- 前置：R3252（T-20261116-15）只建了**检测面**（`qc_census.py` 两条不变量），出生地拦截留单 T-20261116-16。

## 实读结论：守卫本体已在，缺的是可执行负控

`Tools/evolve_citizen.py` 的相遇写入路径已有三道面（T-20261027-01，晚于历史缺陷 C-08226→C-08319 当日）：

| 面 | 落点 | 行为 |
|---|---|---|
| 写前同日预检 | `_meet_ring_today()` + main() 候选过滤 | 任一方当日已有相遇行 → `meet-dup` 提前返回，**不花 LLM** |
| 写后双向断言 | `_meet_pair_check(ids)` | 任一方未指向对方 → 列出 `<id>-><partner>(want <other>)` |
| 字节级回滚 | main() 断言失败分支 | 用 `originals` 覆盖回两张卡 → 不 commit → rc=1 |

问题在于这三面**没有常驻回归**：改坏后只有等真跑相遇轮才暴露，而相遇轮每日 ≤1 次、失败形态是静默单向。本轮补的是这一层。

## 改动

1. `_meet_pair_check(ids, finder=None)`：查找器可注入（默认 `find_card`），使夹具无需触碰 census 树。
2. 新增 `selftest_meet()` + `--selftest-meet` 旗标：临时目录夹具，六例负控，跑完 rmtree，**零 LLM 零盘污**。

## 六例负控（实跑）

```
meet-selftest: PASS 6/6 (healthy / half-write / wrong-partner /
              same-day-precheck / stale-ring / rollback-bytes)
rc=0
```

| 例 | 夹具 | 期望 | 实测 |
|---|---|---|---|
| A 健康互引 | 双方同日各写对方 | `[]` | ✅ |
| B 半写（A 落 B 未落） | B 当日只有普通年轮 | 具名 `C-00002->None` | ✅ |
| C 写错对象 | B 写「与 C-00003 相遇」 | 具名 `C-00002->C-00003` | ✅ |
| D 同日预检 | A 已有当日相遇行 | `_meet_ring_today` 返回 `C-00002` | ✅ |
| E 跨日不误伤 | A 只有昨日相遇行 | 返回 `None`（不阻塞今日候选） | ✅ |
| F 回滚字节一致 | 追加半截行后回写 `before` | 逐字节相同 | ✅ |

`py_compile` rc=0。

## 真库实况（本轮 QC 复读）

```
QC done cards=10114 evolved=10114 problems=0 dup_rings=37/37 dup_new=0 \
        meet=169 one_sided=1 meet_dup=2 meet_new_bad=0
```

- `one_sided=1`（C-08226 2026-10-27）与 `meet_dup=2`（C-00010/C-00011 2026-10-11）仍是**历史观测面**，按 T-20261116-15「历史不回溯改卡」口径不修。
- **闸后新增违律 `meet_new_bad=0`** —— 守卫在真数据上连续无新增，与自测互证。

## 诚实边界

- 本次**未改**守卫逻辑本身（三道面按原样保留），只补可执行负控与注入点；若判定「守卫已足够」，后续不得因「没有显式单测」再次重开本单。
- 自测只覆盖写入路径的三道面，不覆盖 `sync_light` 下游（导出面）一致性——那属 QC 巡检面。
