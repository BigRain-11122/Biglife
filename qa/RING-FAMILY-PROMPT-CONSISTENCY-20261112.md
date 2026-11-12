# 开头族闸 ↔ 提示词一致性（R2588 · 2026-11-12）

## 一句话

v0.65 的「开头骨架族 >25% 即拒稿」硬闸上线时，提示词在**五处**把模型往同一族推，
且从未告诉模型禁哪一族 —— 今日基线 42.8% OVER，19:00 首批会按 gap #68 的
「同提示词重入同一吸引子」路径把应产席位全部留 due。本轮把闸与提示词拉齐，闸不变。

## 实测（12:59，`Tools/ring_open_family.py --check 2026-11-12`）

| 族 | 条数 | 占比 | 判定 |
|---|---|---|---|
| HAND_DEICTIC | 200 / 467 | 42.8% | **OVER**（线 25%） |
| TIME_OPEN | 1 / 467 | 0.2% | OK |
| WEATHER_ABSTRACT | 0 / 467 | 0.0% | OK |

→ 今日 `today_ban_families = {HAND_DEICTIC}`，即今晚首批每一次「手上/手在/手心/
手掌/手肘/手背/我正」起句都会被硬拒。

## 矛盾清单（修前）

1. `city_phr_blk`：改从你此刻身上、**手上**的具体细节写起
2. `today_blk`：请从你自己此刻**手上**正在做的具体小动作写起
3. `second_blk`：改从你自己此刻**手上**、身上的具体细节写起
4. regen 尾注 batch-dup-opening：先写本居民此刻**手上**正在做的一件小事
5. regen 尾注 recent-dup-opening：开头第一句换成你此刻**手上**的一个具体小动作
6. `opening_seed_block` 24 条骨架里 2 条本身落在被禁族
   （「手上的活儿排到第三件…」HAND_DEICTIC／「这会儿手边最碍事的就是这些，」TIME_OPEN）
7. `ring_open_family` 的 `opening-family-quota` 违例**没有专属 regen 尾注** ——
   被拒后重写用的仍是那条把模型推向该族的提示词

## 修法（v0.68，闸不动）

- `FAMILY_OPEN_HINTS`：族名 → 人话禁令（覆盖 FAMILIES 全部族，T7 机检）；
  `_hand_word(sig)`：被禁当天把三处「手上」改说「身上」，无禁时逐字零漂移（T3）。
- `opening_seed_block`：发骨架前先按族过滤，绝不把被禁族骨架递给模型（T1/T2）。
- `family_blk`：尾部新增硬约束块，明确「禁的是起句形状不是内容」，并给三种替换开头
  （物的状态／正在看的另一样东西／去处）；空集 → 空串（面缺失即关闭律）。
- `gated_llm`：新增 `opening-family-quota` 专属尾注，点名被拒开头 + 列出禁用起句形状
  + 允许身体细节后置（T5/T6：硬闸未削弱，句中描写零误伤）。

## 验证

- `python -X utf8 qa/test_family_prompt_consistency.py` → **8/8 PASS，rc=0**
  （常驻回归件；承 T-20261027-01「临时探针升格常驻脚本」判例）
- `py_compile` rc=0；`Tools/ruff_gate.py` 2 文件 CLEAN
- `Tools/ring_open_family.py --selftest` PASS（12 探针 0 fail，闸口语义未动）

## 诚实边界

- 本轮在让路窗内，**没有真跑 LLM**：T1-T8 只证「提示词与闸不再自相矛盾、且无禁时零漂移」，
  不证今晚文本变好。效果判据仍是 T-20261112-04 的 3 生产日观测窗（≤25%）。
- 家话禁令假设 4B 能读懂「不要从『手』字起」；若今晚仍全灭，下一步是把
  `opening-family-quota` 加入软让步（仅对「正文含合法身体描写」的席位）而非放开整族。
