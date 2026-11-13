# 开头族闸「已开仍越线」归因 · 第一轮实测（T-20261113-03）

日期：2026-11-13 14:4x ｜ 执行：@BigLife-OSLoop R2783 ｜ 零 LLM ｜ 让路窗内

## 结论速览

三条待查候选：**①部分证伪、②证伪、③不成立**。范围收窄到 `gated_llm` 重试/兜底路径与 `add_ring` 调用点面。

## 实测读数（本机实跑）

```
entries=541 total=552 unclassified=159
  HAND_DEICTIC      221   40.0%
  PROP_DEICTIC      171   31.0%
  TIME_OPEN           1    0.2%
ban_set= ['HAND_DEICTIC', 'PROP_DEICTIC']
```

`ban_set_from_openings(today_ring_openings())` 在 14:4x **确实返回两个越线族** —— 闸的判据函数是活的，不是死码。

## 逐条判定

### 候选① `FAMILY_MIN_DENOM` 致小批不生成禁用集 —— 部分证伪

读码实证（`evolve_citizen.py` L3384-3401）：`--batch 3` 起批时，`sig["today_family_total"]` 与 `sig["today_family_counts"]` **不是从 0 初始化**，而是先按当日全量台账（`today_ring_openings()`，实时扫 `census/registry` 当日年轮行，无缓存）累加，再调 `ban_set_from_openings(_tcount)`。

推论：批开始时 `_tot` 已是 552 量级，`FAMILY_MIN_DENOM=8` 恒满足，所以「小批不生成禁用集」不成立。批内滚动（L3517-3528）同样以全日 total 为分母。

**但留一个真缺口**：`over_quota` 用严格 `>`，25.0% 不触发。批内落 2 席 HAND 后即越线，第 3 席才被拦 —— 每批仍可让 HAND 净增 1 席。这个「贴着线爬」的窗口是真的，但它**只能解释 +1 席/批**，不能解释实测 +140 席。

### 候选② `opening-family-quota` 被软放 —— 证伪

`SOFT_ONLY_VIOLATIONS = {"recent-dup-opening", "recent-dup-phrase"}`（L716），`opening-family-quota` 不在集合内；落环分支 `if v and set(v) <= SOFT_ONLY_VIOLATIONS` 因此不会对族配额软放。evolve 批路径上是硬拒。

### 候选③ PROP 族 12:09 才立族 —— 不足以解释 HAND

PROP 立族前的产出可以解释 PROP 的 31% 构成，但 HAND 立族更早，40% 不由此解释。维持原判断。

## 剩下的唯一嫌疑面（下一轮直接查这里）

**算术边界本身就是证据**：05:31 读数 25.0%（≈138/552 量级），14:2x 达 40.0%（221）。若闸严格按上述逻辑工作，HAND 每批最多净增 1 席；从 05:31 到 14:2x 期间总量仅增 232 席（≈77 批 × 3 席），HAND 净增上限约 77 席，**实测增 140 席 → 超出闸允许上限约 1.8 倍**。

即：存在一批 HAND 环是在 `today_ban_families` 已含 HAND 的情况下仍然落环的。待查点（按成本排序）：

1. `gated_llm()` 重试耗尽后的兜底行为 —— 是否在 `line is None` 之外还有一条「最后一次尝试直接返回」的分支（L3497 的 `if line is None: continue` 只处理 None）。
2. `add_ring()` 的全部调用点 —— 除批主路径外，是否有 fallback/修复路径直接写卡而不过 `ring_violations`（`meet` 路径已判 4 环、reflect 不产年轮行，但仍需穷举确认）。
3. `_ring_family_of` 对**重写后**句子的识别率 —— 若重写把「手上」换成闸未登记的新起句骨架（落入 unclassified 159 席里的某一族），判据看不见，模型便可无限重写「换个马甲的同族」。
4. `save_today_openings()` 落盘的台账与 `today_ring_openings()` 实扫是否同源（L3432 显示前者被写入 `state/`，若下游有消费方读的是这个快照而快照存在批内滞后，则又是一条口径分叉）。

## 诚实边界

- 本轮**未改任何阈值、未改任何闸逻辑**（承「禁改阈值换绿」）。
- 本轮只给读数与判据证伪，**未宣称修复**；40%/31% 仍越线。
- 未跑 LLM、未落环、未触碰 census 数据面。

## 复跑

```
python -X utf8 -c "import sys,collections;sys.path.insert(0,'Tools');import evolve_citizen as ec,ring_open_family as rf;tc,tg=ec.today_ring_openings(with_grams=True);print(sum(tc.values()),sorted(rf.ban_set_from_openings(tc)))"
```
