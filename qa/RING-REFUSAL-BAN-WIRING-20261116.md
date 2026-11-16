# 年轮硬拒作帐 + 12h 全城开口禁牌：接线负控与首测窗口（2026-11-16 R3208）

零 LLM 确定性取证。数据源 `state/ring-refusals.jsonl`（n=80 条，覆盖 11-15 16:59 → 11-16 08:45）+ `evolve_citizen.recent_refusal_bans()` 直调。

## 一、拒稿分布（作帐首测，命令可复跑）

`python -X utf8 Tools/ring_refusal_attribution.py`：

- 按日：`2026-11-15 = 55` / `2026-11-16 = 25`
- 按闸（今日 Top）：`recent-dup-phrase 20` / `recent-family-opening 15` / `opening-family-quota 5` / `rain-invented 5` / `recent-dup-opening 2`
- 按族（两日累计 Top）：`TIME_OPEN 24` / `WIND_AGENT_OPEN 22` / `HAND_DEICTIC 16`
- 按人（重复席）：`C-03117 = 15 次`（R3115 已判「同人重试」路线证伪，故本闸不走重试路线）

## 二、单一开口吸引子（本单核心证据）

`opening12 = 「这会儿手边最碍事的就是这」` 在 n=80 中占 **24 次（30%）**，跨 **15 小时**、跨 **10+ 位不同居民**（C-03117 / C-03228 / C-03258 / C-03314 / C-03353 / C-03449 / C-03598 / C-03732 / C-03788 …），期间 **census 年轮表内该句出现 0 次**（= 从未通过闸，纯白烧）。

出处排查（防自伤）：`genes/*.json` 与 `cognition/*.json` 均 **0 命中**，该句不在本司基因/语言池内 → 属模型自发吸引子，非池污染。仅 `Tools/evolve_citizen.py` 注释内提及（R3200 统计注）。

## 三、禁牌接线负控（本轮新增证据）

`evolve_citizen.recent_refusal_bans()` 直调结果：

```
ban_count = 13
attractor_in_ban = True
```

即该 24 次吸引子当前确在 12h 禁牌表内，且 `gated_llm` 的 `citywide-refusal-ban` 分支为 **break 直退（不烧 regen）**——接线正确：命中即换人（deferred+1d），不再像 R3115 那样三人一卡反复重试。

## 四、未闭口（诚实面·下轮必看）

1. **禁牌从未被生成面实测**：代码落盘 mtime=11-16 14:50，而当日最后一条生成记录停在 08:45（09:00-19:00 让路窗）→ 全库 **0 条** `citywide-refusal-ban` 实测记录。首测只能在 19:00 开窗后。
2. **TTL 临界漏洞（本轮新发现·未改码）**：该吸引子最后一次被拒 07:34，`REFUSAL_BAN_HOURS=12` → **19:34 到期**，而生成窗 19:00 开。即开窗后前 34 分钟它仍被禁，19:34 起重新合法；若模型再度吐出该句，会重新入册再禁 12h（自维持震荡，不做长期隔离）。
   - 候选修法（**待负控，禁本轮直接落码**）：对「累计被拒 ≥3 次且 census 长年接受 0 次」的开口升级为 sticky 禁牌（7 天）。判据来源＝本文件第一节分布（n=80 满足 T-20261115-04 的「先攒分布再动阈值」前置）。
   - 负控要求：在 19:00 批次上 A/B 各跑一批，比较 `citywide-ban` 命中数与席位 deferred 率，只有「deferred 不升、白烧调用下降」才算通过。
3. 验收面「连续 3 批 zero hard-refuse」样本窗至 **2026-11-17**（承 T-20261115-04 观察态），到期读数直接结案，不再顺延。

## 五、复跑命令

```powershell
python -X utf8 Tools/ring_refusal_attribution.py
python -X utf8 Tools/ring_refusal_attractors.py
python -X utf8 -c "import sys;sys.path.insert(0,'Tools');import evolve_citizen as E;b=E.recent_refusal_bans();print(len(b),'这会儿手边最碍事的就是这' in b)"
```
