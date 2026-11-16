# 配额闸负控台·席位预算闸（防 due 不足造出的假 FAIL）

- 时间：2026-11-16 17:1x @BigLife-OSLoop（R3242）
- 对象：`Tools/ring_quota_negctl.py`
- 关联：T-20261115-04 换靶线 / R3204 补丁（`state/pending/R3204-quota-gate.patch`）

## 一、实读发现的隐患（会在今晚 19:00 直接触发）

```
python -X utf8 Tools/evolve_citizen.py --audit-due
-> audit-due: due=10 leaked=0 -  |  PASS
```

违约台默认参数 `--batch 8`：A 臂 8 席 + B 臂 8 席 = 需要 **16** 个到期席位，而当日只有 **10**。

关键在于**拒稿也消耗席位**：`evolve_citizen.py` L4217 起的 hard-refuse 分支把该席 `next` 推 +1d
（R3115 调度修法），即 due 按「尝试」消耗而非「写成功」消耗。于是：

- A 臂 attempt 8 → due 剩 2；
- B 臂请求 8 但只有 2 席可领 → written 至多 2；
- 判据硬线 1「B written < A written → 修法伤产线」成立 → **自动 `git apply -R` 还原补丁**。

结论：按原参数跑，今晚会得到一个**纯由席位供给造成的假 FAIL**，并据此错误地撤掉一个可能有效的补丁。
这与 R3208 的禁牌 TTL 问题是同一族的「环境量污染结论」，只是污染源从时间换成了席位。

## 二、改法

1. 新增 `plan_batch(due, want)` 纯函数：`eff = min(want, due // 2)`；
   `eff < 2` 直接返回 None（不足即拒绝开跑，避免跑出无意义的两臂差）。
2. 新增 `due_count()`：跑 `evolve_citizen --audit-due`（零 LLM）解析 `due=N`，不可读返回 None 并**沿用请求值 + 明示风险**（不静默放行、也不误拦）。
3. 两臂、判据、报告一律用收敛后的 `batch`，dry-run 同步打印 `due budget:` 一行；不足时 dry-run 即返回 2 并给出原因。

## 三、负控（五例，纯函数，一次性件已删）

| 例 | due | 请求 | 期望 eff | 实测 |
|---|---|---|---|---|
| 1 | 10 | 8 | 5（收敛） | PASS |
| 2 | 16 | 8 | 8（充足） | PASS |
| 3 | 4 | 8 | 2（收敛） | PASS |
| 4 | 3 | 8 | None（不足→拒跑） | PASS |
| 5 | 不可读 | 8 | 8 + 风险注 | PASS |

`py_compile` rc=0；端到端 `--dry-run` 实测输出 `due budget: 席位预算收敛：due=10 → 每臂 5 席（请求 8）`。

## 四、对今晚 19:00 的执行要求（顺序会改变样本量）

- **先跑 A/B，再跑年轮批**：若先跑常规年轮批 3 席，due 从 10 降到 7，A/B 自动收敛成每臂 3 席，
  样本更小；反过来则拿满每臂 5 席。
- 当日上限＝**每臂 5 席**（due=10 决定，不是参数选择）；想要更大样本须等次日 due 回升后重跑。
- 禁牌侧：dry-run 现在读 `active=11 soonest=17:30 latest=20:45`，两臂须连跑且不跨到期点，否则判 CONFOUNDED。

## 五、诚实边界

- 本闸只消除「席位供给不足」这一种假 FAIL；判据本身（written/命中率/wasted）未改动。
- `eff=5` 是当日上限，小样本下 PASS/FAIL 的统计强度有限——报告里已按实际席位数写出，不冒充 8 席结论。
- 未在真实 LLM 臂上验证（让路窗内禁跑）；实弹仍待 19:00。
