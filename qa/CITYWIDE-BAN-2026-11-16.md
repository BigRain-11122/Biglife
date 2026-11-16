# 全城开口 12h 配额闸落地回执（2026-11-16）

## 换靶背景
`opening_capacity --window 12` 实读：waste=7/21（33.3%）、invented 归因 95%、top3 invented 各自 rows=3/cids=3（风把雨棚掀得直响…／这会儿手边最碍事的就是这…／风把塑料布吹得啪啦响…）。
即：拒稿后同一开口 12 字仍被不同居民反复发明，单卡级去重闸拦不住跨卡复读。

## 本轮实物
- `Tools/evolve_citizen.py` +81 行（补丁 `state/pending/R3204-quota-gate.patch`，`git apply --check` rc=0 后落地）：
  - 新增 `recent_refusal_bans(hours=12)`：从拒稿账取「重复类闸」记过的开口 12 字作禁牌集，TTL 12h 到期自解禁，禁牌面自身（citywide-refusal-ban）不入集（防自我延长）。
  - `ring_violations` 增 `citywide-refusal-ban` 判定：前缀命中禁牌键即拒，own-catchphrase（本卡声口、已在卡文中）豁免。
  - 接线点 `L4091 sig["refusal_bans"] = recent_refusal_bans()` —— 非死码，逐卡注入。
- `qa/test_citywide_refusal_ban.py`（零 LLM、temp 文件、不写仓）12 项正负控。

## 证据
| 项 | 结果 |
|---|---|
| `py_compile Tools/evolve_citizen.py` | rc=0 |
| `qa/test_citywide_refusal_ban.py` | 12/12 PASS，verdict PASS |
| `qa/test_opening_refusal_memo.py` | Ran 5 tests OK |
| `qa/test_round_daily_dep_fp_skip.py` | Ran 7 tests OK |
| `evolve_citizen.py --batch 1` 入口 | yield-window（让路窗如期自闸，未误启） |

## 负控要点
anchor 族拒稿不入禁牌（防误伤）、14h 旧记录不入集（TTL）、own-catchphrase 豁免、`sig` 缺 `refusal_bans`（meet/reflect 面）零漂移、带「」引号的键仍能命中（作帐面不剥引号 vs 生成面剥引号）、作帐文件缺失返回 `{}` 不抛错。

## 待验（诚实）
效果判据=19:00 后首批落环：当日拒稿账中该三族重合行应下降、`opening_capacity` waste% 低于 33.3%。本轮未能验证（让路窗内无新环），不得宣称已改善。
