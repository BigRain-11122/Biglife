# 年轮转折点池近重基线重推（T-20261112-06 收单证据）

- 时间：2026-11-12 15:2x @BigLife-OSLoop R2599
- 件号：T-20261112-06（P2·qc 既有 FAIL 非新引入）
- 改动文件：`Tools/gene_nearcheck.py`（+10/−4，仅注释与两处数值）

## 一、病根（实测复现）

`python -X utf8 Tools/gene_nearcheck.py --qc` → **15 PASS / 2 FAIL**（baseline-criterion、baseline-sentinel）。

`--baseline` 实读（n=660）：

| 池 | n | 自配对峰值 | 注册阈值 | criterion_ok |
|---|---|---|---|---|
| cp | 1442 | 91.667 | 92.0 | True |
| ho | 858 | 94.118 | 95.0 | True |
| ha | 68 | 69.565 | 70.0 | True |
| pr | 72 | 36.364 | 37.0 | True |
| **tp** | **660** | **53.968** | **50.0** | **False** |

tp 峰值对：
- 「把攒了半年的钱借给邻居应急，对方还的时候多塞了一包糖，那包糖他留到现在」
- 「把攒了三年的钱借给邻居救急，第二年对方真还了，从此肯信人」

判据语义：Layer B `flagged = best_ratio >= threshold`。旧阈 50.0 < 池内既有合法对 53.968 ⇒ **池里躺着一条按自家判据算「近重」的条目**，判据自相矛盾。

非新污染证据（承 R2597 立单实测）：`git show HEAD:genes/*.json` 隔离装载 659 条复算，峰值同为 53.968、最大对同为该对；b53 八条不参与任何峰值对。

## 二、修法（gate-rigor 惯例：略高于峰值）

阈值 50.0 → **55.0**（+1.9% 边距；同类既有边距 cp +0.36%／ho +0.94%／ha +0.63%／pr +1.75%，取上限侧保守值）。

sentinel 登记值 tp 48.889 → **53.968**，并在源码注释写明语义：三者均为「基线峰值登记值」，池合法追加会推高峰值，此时须**带隔离复算证据**重登记，禁无证据改数字（防「谁改都能改哨兵」）。

## 三、验证（正控/负控/边界）

| 项 | 命令 | 结果 |
|---|---|---|
| 全电池 | `gene_nearcheck.py --qc` | **17 PASS / 0 FAIL**（exit 0） |
| 基线判据 | `gene_nearcheck.py --baseline` | exit 0，五池 criterion_ok 全 True |
| 负控·fail-closed | `--candidate "tp|<池内原文>"` | ratio **100.0 ≥ T55** → FLAG，rc=1（闸未被改松到失效） |
| 边界·精确相似度 | `fuzz.ratio(峰值对)` | **53.968**：T=50 → flag=True（旧阈值误判既有对）；T=55 → **False**（新阈值放行） |
| 编译 | `python -X utf8 -m py_compile Tools/gene_nearcheck.py` | rc=0 |
| lint | `Tools/ruff_gate.py` | ADVISORY 4×SIM115（`open()` 既有调用点 L50/202/204/226，非本次引入，不阻塞） |

## 四、能力边界（诚实）

1. 本次只重推 **tp 单池**阈值；cp/ho/ha/pr 未动（各自 criterion_ok 仍真）。
2. 阈值放宽使 tp 池在 **50.0–53.968** 区间不再自触发——这正是修复目标（该区间的池内合法对不应被判近重），但客观上 Layer B 对 tp 的拦截下限上移 3.968pp。
3. 逐条候选门（Layer A 4-gram ∪ Layer B 阈值）机制与拒稿路径未变；b53 八条在新旧阈值下均为 CLEAN，本次改动不影响其状态。
4. 失效条件：池继续增长使峰值再上移超过 55.0 时，`--qc` 的 baseline-criterion 会再次 FAIL——届时按同一流程「重推阈值 + 带证据重登记峰值」，**禁**只删 FAIL 或放宽到不判。

## 五、复跑

```
cd C:/Users/sjs20/Desktop/FluxGroup/life/BigLife
python -X utf8 Tools/gene_nearcheck.py --qc
python -X utf8 Tools/gene_nearcheck.py --baseline
```
