# 年轮素材「有效通过」判据修复（T-20261112-01 假绿堵口）

- 时间：2026-11-12 15:3x @BigLife-OSLoop（R2600）
- 触发：T-20261112-01 验收窗口复查（streak 名义 1/3）
- 结论：**名义 ready 是假绿——今日流言素材有效通过 0/8**

## 1. 实锚（实跑，可复现）

```
python -X utf8 Tools/ring_material_check.py          # 修复前
  2026-11-12 motif=8 rumor=8 ready          → streak=1/3
python -X utf8 Tools/ring_material_check.py          # 修复后
  2026-11-12 motif=8/8 eff  rumor=0/8 eff BLOCKED → streak=0/3
```

逐条量通过率（同一趟）：

```
rumor_rows=8 effective_pass=0 blocked=8
blocked_tokens={风:8, 雨:1, 雾:1}
```

## 2. 病根（两层）

1. **消费面纪律是对的**：`evolve_citizen.rumor_line_for` 走 RUMOR-CHAIN 判据 4 的
   trigger-free 纪律（`RUMOR_TRIGGERS` 含 风/雨/云/雾/霜/雷…；另挡 `R轮次号/X片区号`），
   含天气词的流言整条不进 prompt——这是防「年轮抄天气预报」的既有护栏，不动。
2. **供给侧持续生产护栏挡掉的句子**：今日 8 条流言里 8 条都带「风」，因为流言文本
   取自居民年轮（年轮 WIND_ACTION 开头族 49.9%、句中风叙述同样密集），
   于是形成 **年轮吸引子 → 流言文本 → 被 ingest 拦 → 回到只剩天气** 的闭环。
   名义文件每天新鲜、有效供给恒 0 —— 只看「文件存在 + mtime 当日」的闸无法察觉。

## 3. 本轮修法（只动判据，不动护栏）

`Tools/ring_material_check.py` 增「有效量」两列：

- `motif_eff`：按 `load_life_motifs` 同口径（type=LIFE_MOTIF + 非空 + 含中文）计数；
- `rumor_eff`：按 `rumor_line_for` 同口径（`RUMOR_TRIGGERS` + `RUMOR_DEV_ID`）计数；
- 过滤器**从 evolve_citizen 直接 import**（判据单源，禁在本文件重抄一份 trigger 表）；
- `ready` 改为「名义 ≥1 **且** 有效 ≥1」，输出 MISSING / BLOCKED / ready 三态。

## 4. 门禁面

- `py_compile` rc=0；
- 正负控：无天气词句 PASS、含风/雨句 BLOCK、纯动作句 PASS → `POSNEG_CONTROL=PASS`
  （证明闸非恒红，含合法叙事不被误杀）；
- `--json` 机读面可用（含 motifs_eff / rumors_eff 字段），退出码语义不变：达标 0、进行中 2。

## 5. 诚实边界

- 本件只把**判据**对齐到消费面实际口径，**没有**提高供给质量：今日有效供给仍为 0，
  T-20261112-01 因此由「1/3 进度」诚实回退为「0/3」，它是真值不是退步。
- 未处理供给侧治本（流言文本去天气触发词 / 母题池扩日供量），已立 T-20261112-07，
  带本次量化证据；改供给会动文本质量，需单独一轮带抽样人读，不与判据修复混做。
- 母题侧 `out[:4]` 每批只取 4 条，本件不假设这点已够用（属 T-20261112-07 范围）。
