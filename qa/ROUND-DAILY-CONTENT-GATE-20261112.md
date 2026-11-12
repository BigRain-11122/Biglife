# 日更闸内容级判据·第二面补登记（「此刻城市」页）

- 日期：2026-11-12 16:3x
- 轮次：R2607 @BigLife-OSLoop
- 触发：R2604 记录「fresh 判据不感知内嵌快照时点」候选缺陷，本轮实证并修复
- 关联：T-20261112-02（12 面静默停更 15 天）同族第三面；T-20261112-04（判据只看文件龄）

## 一、实证（缺陷真实存在）

| 证据 | 读数 |
|---|---|
| `census/export/city-today.html` mtime | 2026-11-12 **10:06:25**（当日 ⇒ round_daily 判 fresh） |
| 页面正文内印 | 「此刻城市 … **面生成 2026-11-12 09:38**」 |
| 真实来源 `state/behavior-last.json` | mtime **15:13:04**，内文 `"ts": "2026-11-12T15:13:02+08:00"` |
| 行为数据 `census/export/citizen-behavior.jsonl` | mtime **15:13:04**（已刷新） |

结论：页面标题写「**此刻**城市」、正文承诺「当下各槽位人数」，但内容落后真实数据 **5 小时 35 分**。
该页正文（时段/天气/六槽位人数与代表居民）**全部**来自 `state/behavior-last.json`，
所以内嵌时点不是装饰，而是内容新鲜度的唯一自证。

## 二、病根

`Tools/round_daily.py` 的内容级判据 `SNAPSHOT_SPECS`（旧名 `SNAPSHOT_SOURCES`）
只登记了 `city-dashboard.html → citizens-light.jsonl` 一对。
其余页面即使内嵌源时点，也只过 mtime 判据 —— mtime 只证明「页面被重写过」，
不证明「页面读的是新鲜源」。

## 三、修法（零 LLM·确定性）

1. `SNAPSHOT_SOURCES`（dict）→ `SNAPSHOT_SPECS`（列表）：每项 =（页面名, 来源绝对路径, 时点正则, 精度）。
   - 支持来源在 `export/` 之外（本例在 `state/`）；
   - 支持分钟精度页面（`面生成 YYYY-MM-DD HH:MM` 与秒精度 `数据截至 …:SS` 并存）。
2. 新增 `_fmt_mtime(path, precision)`：按页面精度截断来源 mtime 后比对。
3. 补登记第二项：
   `city-today.html ← state/behavior-last.json`，正则 `面生成\s*(\d{4}-\d\d-\d\d \d\d:\d\d)`，精度 `min`。
4. **未登记**的两处（有意识跳过，非遗漏）：`meet-candidates.html` / `city-coverage.html`
   内嵌时点属装饰（正文数据不来自该源），登记后会让源每刷一次就触发一次零信息量重建。
   代码注释已写明该判据，防后人误加。

## 四、验证（三态 + 收敛）

| 步骤 | 结果 |
|---|---|
| `py_compile Tools/round_daily.py` | rc=0 |
| `--check`（修后未重建） | `today daily skipped-check content-stale:city-today.html src=2026-11-12 15:13` → **stale=1**（抓得到） |
| `--run` | `today daily rebuilt content-stale:…` → stale=1 ran=2 failed=0 |
| `--check`（重建后） | **stale=0 ran=0 failed=0 verdict=PASS**（修得了·收敛） |
| 页面复核 | 内嵌时点 09:38 → **15:13**，与 `behavior-last.json` 一致 |

## 五、门禁（同轮）

- 事件回放闸：`cards=10111 events=41699 replayed=10111 schema_errors=0 mismatch=0 → PASS`；chronicle gap=0d；coverage unexpected_missing=0
- QC 不变量：`cards=10114 evolved=10114 problems=0 dup_rings=37/37`
- 语言池：`pool_audit` 全桶达标 SELF_TERMINATE（axes 72/72、sprite 12/12、greet 28、faq 7、neg 6/6、hard_fails=0）

## 六、余留（下轮不做，如实记）

- 同类「内嵌时点」页面尚未穷举。本轮只处理了**正文等于该源数据**的页面；
  其余页面若正文派生自某日更档，须先确认口径再登记（登记错会制造无谓重建）。
- `state/behavior-last.json` 自身的刷新频率由 `Tools/behavior.py` 的 QC-passing run 决定，
  本闸不改变其节奏，只保证页面不落后于它。
