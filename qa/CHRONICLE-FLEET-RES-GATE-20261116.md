# QA 回执：城区志台账机队资源污染闸（R3170·2026-11-16）

**触发**：任务板 T-20261116-01 open 单（城市志页与台账口径核对）。核对中发现更深一层缺陷。

## 一、原始单结论（T-20261116-01）

| 问 | 实测 | 判 |
|---|---|---|
| `census/export/city-chronicle.html` 是否缺 `cognition/city-chronicle.jsonl` 最近 5 行 summary | 页面 66375B / mtime 11-15 09:56，`显存/VRAM/G20-G08/城主早安` 命中均 **0** | 页面**是干净的**；这 5 行未被吸收属**正确过滤副作用**，不是缺陷 |

## 二、真缺陷（核对中挖出）

`cognition/city-chronicle.jsonl` 存量 **2256 行中 477 行（21.1%）** 含机队资源词（显存/VRAM/GPU/G20-G08/内存），跨 2026-09-24 ～ 2026-11-15。

**根因链**（与集团 D-20261115-01 同一缺陷的下游面）：
1. 上游 `gaming/FluxVerse/Tools/perceptor/probes/residents.ps1` 向 `RESIDENT_SAY` 注入 `vram_free_mb/vram_total_mb` → 台词退化为机队显存报告（集团已派城市线修，承诺 2026-11-16 18:00）。
2. 本司 `Tools/city_chronicle.py` 只有 `DEV_ID_RE`（轮次号）与 `C_ID_RE`（居民编号）两道内容闸，**没有资源词闸**；`RESIDENT_SAY` 类型权重=2 过门，资源报告直接入谱。
3. 入谱后经 `city_digest()` 进入年轮批 prompt 的「本周城市大事」喂入块 → 产品面（居民年轮）有被显存报告污染的风险。

## 三、修复（本司侧护栏，不跨司改上游）

`Tools/city_chronicle.py` 三层闸，同一正则 `FLEET_RES_RE = 显存|VRAM|vram|GDDR|G\d{2}-G\d{2}`，**仅作用于 `RESIDENT_SAY`**（其它类型如实录事件不筛）：

| 层 | 位置 | 作用 |
|---|---|---|
| 写入口 | `derive_rows()` | 新增行不再入谱 |
| 读时 | `city_digest()` | 存量脏行不进年轮喂入面（产品面立刻干净） |
| 幂等面 | 同上一处 | `--feed` 只增不改，存量 477 行按 append-only 契约**保留不删**（重建清理由 `--rebuild` 承担，需集团/CEO 定夺，本轮不动） |

## 四、验证证据（可复跑）

```
$ python -X utf8 Tools/city_chronicle.py --qc
QC PASS (0 fails)          # 断言电池 14 项全绿（含确定性双跑逐字节一致）

NEG-CTRL derived_rows=1835 fleet-res_rows=0      # 派生面零资源行
NEG-CTRL digest_has_fleet_res=False              # digest 面零资源行
POS-CTRL regex_hits_known_dirty=True             # 正控：脏样本必命中
POS-CTRL regex_passes_clean=True                 # 正控：干净样本不误杀
  clean sample = 「今早五点起，巷口豆浆摊开张，蒸笼白汽顺着檐角往上走。」

$ python -X utf8 Tools/city_chronicle.py --feed
feed appended=8 total=2264                       # 增量 8 行全部为 GITHUB_EVENT
new8_rows=8 new8_fleet_res=0                     # 增量面同样零资源词

$ python -X utf8 Tools/round_daily.py --run
chronicle_feed data rebuilt script-changed:city_chronicle.py
chronicle      faces rebuilt dep-mtime:cognition/city-chronicle.jsonl
verdict: PASS                                    # 页面已按新台账重建
```

## 五、遗留与边界（诚实记档）

1. **存量 477 行未清**：append-only 契约（文件头「永不删改」）优先；`--rebuild` 可一次性清理且确定性可复现（派生面已证明零资源行），但属台账历史改写，列入 TASKS 待集团/CEO 定夺。
2. **上游根治仍在上游**：本闸只挡本司入谱，FluxVerse `residents-prompt.txt` 台词面不改 → 机队其它消费方仍可能收到显存报告。D-20261115-01 承诺窗 2026-11-16 18:00 内由城市线负责。
3. `FLEET_RES_RE` 覆盖 `G\d{2}-G\d{2}`（机队游戏编号对），若未来出现同形正常城市文本（如「G20 展馆」不含连字符）不受影响；无连字符形态不匹配，已由正控干净样本验证。
