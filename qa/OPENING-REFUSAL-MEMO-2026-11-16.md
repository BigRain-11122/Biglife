# 拒稿回灌闸（R3220）· 2026-11-16

## 缺陷（实读证据）

`state/ring-refusals.jsonl` 全窗 80 条、11-15 16:59 → 11-16 08:45。按开头归集：

| 开口（opening12） | 拒稿行 | 涉及居民 | 不同写法 |
|---|---|---|---|
| `这会儿手边最碍事的就是这` | 24 | 9 | **1（逐字同句）** |
| `桌角那点零碎又该理一理` | 6 | 6 | 1 |

单条热骨架吃掉 30/80＝38% 的拒稿。抽样轨迹：C-03117 在 16:59 / 17:04 / 17:14 / 17:18 / 17:25 / 17:34
六连拒，`gate=['recent-dup-phrase','recent-family-opening']`，12 字开口每一次都逐字相同。

根因两层：
1. **拒稿只作帐不消费**——`_note_refusal()` 写盘后再无人读；`opening_seed_block()` 的排除集只含
   「今日已采纳开口」，被拒的骨架因此永远不在排除集里，当天照发不误（第二个、第三个居民继续撞）。
2. **重试尾注只禁不给**——`recent-family-opening` / `opening-family-quota` 两处尾注说「禁止再用这个开头」，
   却没给替代落点；4B 于是在同一条吸引子上连续重写（与 gap #68/#70/#79 同病）。
   `Tools/opening_capacity.py` 读数：`waste_ratio=0.55`（80 次调用里 44 次是重复开口）。

## 修法（零 LLM·仅拒稿路径生效）

- `today_refused_openings(day=None)`：读回今日拒稿开口（口径与闸一致：去空白取前 12 字）。
- `opening_seed_block()`：排除集从「今日已采纳」扩到「已采纳 ∪ 今日已拒 ∪ 全城近期用滥」；
  新增 `_opening_is_dead()` 做 12 字精确 + 8 字前缀容忍（模型抄走样时仍能命中）。
- `retry_skeleton(sig, attempt, banned)`：给重试尾注一条**具体可用的替用骨架**（排除今日已采纳/已拒/
  全城用滥/当日禁族，按 cid+attempt 稳定散列），把禁令变成可执行指令。
- 两处尾注（`recent-family-opening`/`opening-family-quota`）追加该替用骨架；池被排空则不加该句。

## 验证

`python -X utf8 qa\test_opening_refusal_memo.py` → **Ran 5 tests OK**：

- 正控：今日拒稿 → 60 个 cid 无一人再拿到该骨架；`retry_skeleton` 非空、不等于被拒骨架、不在排除集、
  同一 cid 四次重试拿到不止一条替用。
- 负控：昨日拒稿不跨日误伤（HOT 仍可正常发放）；无拒稿文件时 60 个 cid 的选择与旧算法**逐字相同**；
  8 字前缀容忍不误删其他 23 条骨架。

实跑：`evolve_citizen.py --audit-due --batch 3` → `due=10 leaked=0 PASS`；`py_compile` 通过。

## 验收（下一生产窗）

19:00 窗批次落地后：①`state/ring-refusals.jsonl` 当日新增行里，与 `这会儿手边最碍事` 重合的行应为 **0**；
②`Tools/opening_capacity.py --window 12` 的 `attribution.skeleton` 占比应低于今日 38%；③`waste_ratio` 应下降。

## 诚实边界

本轮为让路窗（D-20261020-02），未调用 LLM，因此**今日无新落环**；本修复的效果自今晚 19:00 首批起可测。
未改任何闸阈值、未改软让步（`SOFT_ONLY_VIOLATIONS`）、未改骨架池内容。
