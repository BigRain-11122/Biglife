# MEET-NEGCTL — 相遇写盘出生地拦截 · 负控证据（T-20261116-16）

- 日期：2026-11-16 20:2x @BigLife-OSLoop
- 目标：为 T-20261116-16（相遇写侧自校验）补齐验收要求的负控证据
- 工装：`Tools/meet_negctl.py`（新增·零 LLM·零网络·零仓内卡片改动）

## 一、实读结论：拦截已在树内（本单原描述已部分过时）

`Tools/evolve_citizen.py` meet 分支实读：

| 面 | 位置 | 机制 |
|---|---|---|
| 写前查重 | L4004-4012 `meet-dup:` 出口 | `_meet_ring_today(card)` 命中当日已有相遇即 `return`，发生在 prompt 构造与 `gated_llm` **之前**（不烧 LLM） |
| 写前快照 | L4001-4003 | `originals[p] = f.read()` 每人一份原文，回滚原料 |
| 写后双向断言 | L4040-4049 `meet-asymmetry` 出口 | `_meet_pair_check(ids)` 判任一侧未指名对手 → 按 `originals` 整文件回写 → `sys.exit(1)`，零 commit |
| 检测侧 | `Tools/qc_census.py`（T-20261116-15） | 术后 `meet_new_bad` 计 problems |

即「单向不得留存」「同日同对象不得重复」两条要求在写侧均已落地实现，缺的只是**证明拦截会响**的负控。

## 二、负控实跑（`python -X utf8 Tools/meet_negctl.py`）

```
== meet_negctl（相遇写盘拦截负控）==
  [ok] C1-dup-detected            _meet_ring_today(今日已有相遇)='C-00002' 期望 C-00002
  [ok] C2-stale-not-dup           _meet_ring_today(旧日相遇)=None 期望 None
  [ok] C3-one-sided-flagged       _meet_pair_check(单向)=['C-00002->None(want C-00001)'] 期望 1 条且指向 C-00002
  [ok] C4-symmetric-clean         _meet_pair_check(双向)=[] 期望 []
  [ok] C5-originals-snapshot      写侧须在首次落环前缓存 originals（回滚原料）
  [ok] C6-rollback-branch-present 写侧须保留 meet-asymmetry 回滚分支与 rc=1 退出
  [ok] C7-dup-before-llm          meet-dup@211338 < gated_llm@213833 < prompt@211679
verdict: PASS (7 checks, 0 fail)
rc=0
```

关键两条：

- **C3**＝T-20261116-16 描述的真实缺陷形态（第二卡写失败留单向）。夹具造出「A 指名 B／B 不指名 A」后，`_meet_pair_check` 立即返回 1 条不对称 → 生产路径据此走回滚，单向留存被堵在出生地。
- **C4**＝闸不常红的反证：双向齐全时返回 `[]`，不会误杀正常相遇轮（防「改完更严但把好活也拦掉」）。

工装自证：所有卡面在 `tempfile.TemporaryDirectory()` 内构造、`find_card` 被临时替换后 `finally` 还原，**未触碰仓内任何 `census/cards/`**；`evolve_citizen` 以 `importlib` 加载（0.6s，无副作用）。

## 三、剩余未竟（不宣称完成）

- `qc_census.py` 的 `meet_new_bad=0` 需**持续 3 生产日**才算验收全过：观察窗起算 2026-11-16，到期 2026-11-18 后读数结案。
- 本单状态：负控子项 **done**（2026-11-16 20:2x），观察窗子项 in-progress。
