# GENE-FREEZE-20261115 · 世代池冻结实装证据（T-20261115-03）

- 立单/承单：T-20261115-02 决策 (b)（R3067 2026-11-15 10:4x）→ 实装 R3069 2026-11-15 10:4x
- 结论：**已实装并验收通过（4/4）**；老居民习惯分配漂移 99.10%/99.49% → **0.00%**

## 实装件

| 文件 | 改动 |
|---|---|
| `Tools/persona_generations.py` | 新建。世代快照同步器：读现池（habits/likes/dislikes/address_terms/seed_wrappers/tics_openers/tics_closers）+ 现最大 cid；池有增长则追加新世代（旧世代只增不改）。`--sync` 落盘、`--check` 有欠同步则 rc=1。零 LLM、确定性。 |
| `Tools/persona_enrich.py` | 新增 `generations()` / `pool_for(cid, key, current)`；`derive()` 的 habits/hb2/likes/dislikes/address/tic/closer 与 `seed_line()` 的 seed_wrappers 全部改走 `pool_for`。缺世代档=退回现池（行为不变）。 |
| `Tools/persona_drift.py` | 新增 `gen_freeze` 测式，把生产实路纳入同一把尺子量。 |
| `genes/persona-pool-generations.json` | 新建：gen 1，cutoff `C-10120`（= 当前最大 cid），habits 快照 137 条，created 2026-11-15。 |

## 验收四条（全员实跑）

1. **实装前后老居民 persona 面逐字节一致**：带世代档 vs 移除世代档两次重算，
   md5 均 = `C483FE55F174AA7667431531ECD40B49` → **一致**（冻结对现役人口零副作用）。
   附注（诚实）：与更早的历史导出 `C6410B98…` 不同——原因是该导出早于最近一轮基因增补已陈旧，
   与本次改动无关（世代快照=当前池，取模结果必然相同）。
2. **`persona_drift.py` 对老居民报 moved=0**：`hb/gen_freeze 0/10114 (0.00%)`、
   `hb2/gen_freeze 0/10114 (0.00%)`；对照组同跑 `mod_len 99.10% / 99.49%`、
   `default_bucket 0.30% / 0.26%`（但 head_share 46.94%/47.00% 判负不采用）。
3. **新增一条探针基因后老居民习惯零变化**：即上条的探针跑（`PROBE` 加入 habits 池尾部）。
4. 证据落盘：本文件 + `census/export/persona-drift.json`（gitignored 派生面）。

## 负控三态（防「闸装反了」）

```
old_uses_snapshot   = True   # C-00001 → 读生日世代快照
new_uses_current    = True   # C-99999 → 读现池（新居民吃得到新基因）
missing_key_falls_back = True # 快照缺该池 → 退回现池，不 KeyError
```

## 门禁

- `Tools/ruff_gate.py` 3 file(s) **CLEAN**（F401,F811,F841,SIM115,RUF059）
- `py_compile` 3 文件 rc=0
- `persona_enrich.py --qc` **PASS**（rows=10114 bad=0 blocked=3 active=10111，双跑逐字节一致）
- `persona_generations.py --check` rc=0（pending_sync=none）

## 运维口径（防再犯）

- 每次基因轮（步 6 补基因）后跑一次 `python -X utf8 Tools/persona_generations.py --sync`；
  `--check` rc=1 即欠同步（可作 CI/巡检钩子）。
- 新居民自动读最新快照，无需任何登记动作；cid 单调递增是本方案的前提（现 census 编号规则已满足）。
