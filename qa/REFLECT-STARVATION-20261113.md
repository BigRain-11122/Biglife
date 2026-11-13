# 反思线静默断供取证与接线（T-20261113-05）

- 轮次：R2799 @BigLife-OSLoop 2026-11-13 18:2x-18:5x（周五工作日让路窗内·零 LLM 确定性面）
- 结论：**反思线（`Tools/reflect_citizen.py` → `census/reflections.jsonl`）从未接入轮次规程**，
  属「假设存在而实际无步骤」类断供——与 T-20261112-02（流言录）、T-20261112-03（互聊台账）同一病根族。

## 一、实测读数（可复跑）

| 指标 | 实测值 | 命令 |
|---|---|---|
| reflections.jsonl 总行数 | **61** | `(Get-Content census/reflections.jsonl).Count` |
| 末行日期 | **2026-10-27**（停更 17.6 天） | 尾部 date 分组 |
| 覆盖居民数 | **61 / 10114 = 0.60%** | `existing()` 键数 |
| 候选可供性 | `pick_ids(8)` 立即返回 8 席 | 见下「验证命令」 |
| 规程内步骤 | **0 处**（`Tools/iteration_prompt.txt` 1/1B/2..8 均无 reflect） | `Select-String iteration_prompt.txt -Pattern "reflect\|反思"` → 空 |

## 二、为什么历轮没发现

历轮轮记（R2774 / R2781 / R2786 / R2798 等）均写「年轮/相遇/**反思**三条 LLM 面按 D-20261020-02
让路窗结构性推迟」——把反思当成已接线、只是被让路窗推迟的腿。实际让路窗闸在
`reflect_citizen.main()` 内部（09:00-19:00 直接返回），但**没有任何一轮在 19:00 后调用它**，
于是「推迟」永久生效。这是记账假设与规程事实分叉导致的静默断供，非脚本缺陷。

## 三、覆盖缺口算术

低频率律设计为「每居民 30 天至多 1 条」（`COOLDOWN_DAYS=30`）。要覆盖 10114 人需 ≈**337 条/日**；
按本轮接线步 1C 的批 5/日推算，仅能维持 **150 人/月 = 1.5%** 覆盖。故本单只解决「有产出、不停更」，
**不宣称覆盖达标**——是否提高批量为覆盖目标，属产能口径，须委员会/CEO 定（避免让路窗挤占 CEO 车道）。

## 四、本轮落地（接线）

1. `Tools/iteration_prompt.txt` 新增步 **1C**（19:00 后至多 1 次 `reflect_citizen.py --batch 5`，
   含病根注记与验收条款）——把「靠记性」改为「规程内固定步骤」。
2. 立单 T-20261113-05（P1·复发防御），验收=连续 3 生产日 reflections.jsonl 尾部 date=当日。

## 五、验证命令（负控/正控）

```powershell
# 正控：候选池真能选出人（证明不是「无人可选」的假因）
python -X utf8 -c "import importlib.util,sys;sys.path.insert(0,'Tools');
s=importlib.util.spec_from_file_location('rc','Tools/reflect_citizen.py');
m=importlib.util.module_from_spec(s);s.loader.exec_module(m);
print(len(m.pick_ids(8)), list(m.existing())[:3])"
# 实测输出：eligible_sample=8 ['C-00010',...] / citizens_with_reflection=61

# 让路窗负控：当前时点在 09:00-19:00 → 应原样返回 yield-window 且零写入
python -X utf8 Tools/reflect_citizen.py --batch 5
```

## 六、诚实边界

- 本件只证明「接线缺失 + 候选可供」，**不证明洞察质量**；质量线由 `--qc`（6 gate cases + containment +
  prompt determinism）与月度 spotlight 抽验承担。
- 未在让路窗内强跑反思批（违反 D-20261020-02 CEO 车道优先）；首条实批产出 ETA 2026-11-13 19:00 后夜窗。
- 存量 61 条不回改；覆盖率数字按实测，不按设计值推算。
