# 12h 全城开口配额闸·实弹负控（2026-11-16）

- 执行：`Tools/ring_quota_negctl.py`（R3204 协议可执行化·T-20261115-04 换靶线）
- 开关：运行时 env `BIGLIFE_QUOTA_GATE`（R3255）——A 臂=off，B 臂=on；闸代码常驻树内，工作树零写入（文本反向补丁基线漂移已废弃）
- 每臂席位：5
- 禁牌态：A 臂 active=7·最早到期 2026-11-16 20:14 ／ B 臂 active=7·最早到期 2026-11-16 20:14（A 臂关闸时恒为 0 条，非偏差）
- 禁牌快照：冻结 7 条（两臂共用同一集合·不受到期点约束）

## 两臂读数

| 臂 | 闸 | written | done | citywide-ban 命中 | 摘要行 |
|---|---|---|---|---|---|
| A | off | 5 | 5 | - | `OK evolved=5 of 5 due (written=5 skipped=0)` |
| B | on | 5 | 5 | 0 | `OK evolved=5 of 5 due (written=5 skipped=0)` |

## 判定

```
ok   两臂禁牌集合按快照冻结共用（n=0·墙钟到期混淆不适用）
note 无判别力：B 臂闸零命中（当时冻结禁牌 7 条）——该批没有任何「闸真的拦过一次」的证据，落环差与复读面读数不能用于留撤
```

**verdict: INCONCLUSIVE**　闸代码终态=常驻生效（= 起跑前状态·工作树无残留改动）

## 回退口（三条硬线）

1. B 臂 written < A 臂 written → 伤产线
2. B 臂命中率 > 30% → 闸过宽
3. 当日 wasted_calls / max_repeats 高于 A 臂前读数 → R3115 调度缺陷回归

## 本日两轮实测与仪器勘误（R3255·@BigLife-OSLoop）

- **第 1 轮（旧工装·作废）**：A 臂 written=10 / B 臂 written=9，判 `FAIL 落环数 9<10`。
  该 FAIL **不作数**，根因两条均在工装侧：
  1. `evolve_citizen` 的批下限会把 `--batch 5` 抬到 `batch-policy` 的 10（`args.batch = max(...)`），
     于是「每臂 5 席」从未生效，A 臂吃满 10 席、B 臂吃下一批 —— 两臂席位不可比；
  2. 「闸零命中」的 INCONCLUSIVE 判据排在落环差判定**之后**，B 臂闸一次没拦到时，
     1 席差（来自别的闸/别的 residents）被误判成「修法伤产线」。
- **修法（已落码）**：①新增 env `BIGLIFE_QUOTA_GATE`（A 臂 off / B 臂 on，闸代码常驻树内，
  不再翻文本补丁——`git apply -R` 基线漂移即 R3253 rc=2 根因）；②新增 env `BIGLIFE_BATCH_POLICY=off`
  让负控台压住策略批下限；③零命中判定前移为最高优先（无判别力即 INCONCLUSIVE，任何方向都不裁决）；
  ④A 臂关闸时打印 `quota-gate: off (env BIGLIFE_QUOTA_GATE)` 自证，负控台校验此行缺失即 CONFOUNDED。
- **第 2 轮（新工装·有效）**：两臂各 **5 席**、written 5/5、ban 命中 **0**，
  verdict=`INCONCLUSIVE`（冻结禁牌 7 条，但这批 10 次开口没有一次撞上）→ **不裁决，闸留存**。
- **结论与下一步**：闸的留/撤仍未有判别性证据。下一轮须在「禁牌确有命中」的窗口重跑
  （或提高每臂席位到 ≥8 并挑在近期拒稿密集时段），否则再跑仍是 INCONCLUSIVE；
  `--selftest` 现含 3b/4 面共 25 项（0 fail）。
