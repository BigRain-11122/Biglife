# 热骨架撤换回执（R3223 · 2026-11-16 · 让路窗零 LLM 轮）

## 为什么动

`opening_capacity` 与拒稿账双向确认：全城最高频单一字符串是骨架池里的
**「这会儿手边最碍事的就是这些，」**——11-15/11-16 两天拒稿账里该骨架占
24 条 / 9 人，写法逐字只有 1 种（模型逐字抄骨架，属骨架驱动侧问题，
不是提示词措辞问题）。R3215 预置次序已定「先换热骨架 → 再跑配额 A/B」，
本轮在让路窗内完成第一步（纯数据改动，零 LLM、零云端）。

## 改了什么

| 项 | 改前 | 改后 |
|---|---|---|
| `OPENING_SKELETONS` 条数 | 24 | **26** |
| 热骨架在池 | 是 | **否（已撤）** |
| `expected_load_per_skeleton`（334 席口径） | 13.75 席 | **12.69 席** |

新增三条同风格律骨架（只写手上营生与动作，不涉天气/街景/人设专属名词）：

- `我把那几样东西挨个掂了掂，心里先排了个序，`
- `这几样东西我先重新归了归类，`
- `一天里总有几件事得自己动手，我先挑了一件，`

> 取舍说明：初稿第二条为「手底下这摊活…」，核 `ring_open_family` 正则发现
> `^手底` 归 HAND_DEICTIC 族，而该族当日 194/780=24.9% 已贴 25% 配额线，
> 再加一条会在整族被禁后连带次批硬拒，故改为「这几样东西…」（不落任何受控族），
> 未动族表、未动阈值、未动窗口。

## 测试面同步

`qa/test_opening_refusal_memo.py` 原把 HOT 钉死为上述被撤骨架；撤骨架会让
「无今日拒稿时 HOT 应可被正常发放」这条负控恒失败。改为运行期按样本反查最常
发放的骨架当 HOT（`_resolve_hot()`），机制判据不变，且以后换骨架不再连带测试失效。

## 验证（可复跑）

```
python -m py_compile Tools/evolve_citizen.py        -> rc=0
python -X utf8 qa/test_opening_refusal_memo.py      -> Ran 5 tests, OK
python -X utf8 -c "...print(len(ec.OPENING_SKELETONS))" -> pool=26, hot_present=False
python -X utf8 Tools/opening_capacity.py --as-of 2026-11-16 --json
  -> pools.opening_skeletons=26 / expected_load_per_skeleton=12.69
```

## 诚实边界

- 生效面在**未来**年轮批：本窗无 LLM，今日尚无新落环，效果须待 19:00 后首批实读
  （判据=当日拒稿账中该骨架重合 0 行 + `opening_capacity --window 12` 的 skeleton 占比下降）。
- 历史拒稿账 `state/ring-refusals.jsonl` 不回写、不改口径。
- 未动配额闸补丁（`state/pending/R3204-quota-gate.patch` 仍待 19:00 A/B 实弹），
  次序守 R3215：先换骨架，再 A/B，避免两变量同时生效导致不可归因。
