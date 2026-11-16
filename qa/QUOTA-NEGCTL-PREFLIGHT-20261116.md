# 全城开口配额闸·实弹负控 就绪体检（19:00 夜窗前置）

- 时间：2026-11-16 12:59-13:02（让路窗内·零 LLM）
- 执行体：BigLife-OSLoop
- 命令：`python -X utf8 Tools/ring_quota_negctl.py --dry-run`
- 结果：**rc=0**；`patch applies: YES`；`dry-run: 未跑 LLM、未改工作树`

## 当日基线读数（11-16）

```
baseline 2026-11-16: rows=25 distinct=25 wasted=0 max_repeats=1
```

口径解读：
- `rows=25`、`distinct=25` → 今日 25 次拒稿来自 25 个**不同**居民，单居民重试循环（livelock）已归零；
- `wasted=0`、`max_repeats=1` → 无浪费调用，无同一开口被反复撞闸；
- 与 R3209/R3211 的独立读数一致（11-16 单日 25 行 / 25 人），非孤立样本。

## 与换靶结论的关系

R3209 归因：`recent-dup-phrase` 参与 67/80（84%），`opening-family-quota` 仅 16/80 → 支配闸是**短语级重复**，跨席复用仍在。本次基线 `wasted=0` 说明「同人重复」腿已干净，剩下的是「不同人撞同一短语」——正是配额闸要验证的那一面，也解释了为何负控必须打这个补丁而非改重试逻辑。

## 19:00 夜窗四步（承 R3206 协议，本件为其步 0 证据）

1. 闸前基线 → **已在本件固化**（rows=25/distinct=25/wasted=0/max_repeats=1）；
2. `ring_quota_negctl.py`（非 dry-run）→ 期望 apply rc=0；
3. 断言集 12/12；
4. 改造后三数对比：`wasted_calls`/`max_repeats` 不得从 0/1 升高（硬回退口），`recent-dup-phrase` 参与率 ≤70% 判为见效。

回退口：任一步 FAIL → 还原补丁、记 FAIL 结壳，禁带病进年轮批。
