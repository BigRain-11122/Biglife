# 流言供给端同口径修复（T-20261112-01 有效供给 0/8 → 7/7）

- 时间：2026-11-12 15:4x @BigLife-OSLoop（R2601）
- 病例：`ring_material_check.py` 修复后暴露「名义 8/8、有效 0/8 BLOCKED」——文件每日新鲜，但整批被年轮 ingest 拦掉。

## 1. 病根

消费面 `evolve_citizen.rumor_line_for` 有 trigger-free 纪律（`RUMOR_TRIGGERS` 含 风/雨/云/雾/月/星…），
而供给面 `build_rumors.pick()` 是纯 md5 随机抽，不校验可消费性。今日 465 条候选年轮里仅 7 条不含 trigger 词，
随机抽 8 条自然全数落在被拦区间 → 有效供给恒 0 的闭环。

## 2. 修法（只动供给侧，判据不动）

`Tools/build_rumors.py`：

- 新增 `_ingest_filters()`：从 `evolve_citizen` 直接取 `RUMOR_TRIGGERS` / `RUMOR_DEV_ID`（判据单源，禁重抄表）；
- 新增 `consumable()`：与 `rumor_line_for` 过滤段逐字同口径；
- `pick()` 增加 `ok` 谓词，按城区独立指针顺延跳过不合格候选（不占名额、不改变确定性）；
- 输出行新增 `pool=` / `eligible=` 两列，供给余量可见。

## 3. 实证

```
python -X utf8 Tools/build_rumors.py --per-day 8
  chains=7 hops=25 pool=465 eligible=7
python -X utf8 Tools/ring_material_check.py
  2026-11-12 motif=8/8 eff  rumor=7/7 eff  ready    streak=1/3
```

- 幂等：同参数重跑，jsonl SHA256 一致（`idempotent=True`）。
- 门禁：`py_compile` rc=0；`round_daily --run` stale=0 ran=0 PASS；`events_refresh --gate` PASS（cards=10111/events=41699/mismatch=0/schema_errors=0）。
- 诚实边界：per-day 目标 8，实得 7——当日可消费候选硬上限 7，缺口不伪造，明天池子回补即恢复 8。

## 4. 附带清理（抽样人读发现）

人读 7 条时发现 1 条泄漏原始编号：「与 C-09875 相遇：苏阿果，你画的城门那幅…」——编号不该出现在城里人的口头话里。
`clean_text()` 增 `MEET_PREFIX` 剥离（须在去「」之后执行，年轮正文常被引号包住），现 7 条 `id_leak=0`，
该条变为「苏阿果，你画的城门那幅，我看了三遍，盘扣是歪的。」，语义完整不削句。

## 5. 影响面

晚间年轮批（19:00 后）拿到的流言素材从「整批不可用」变为「7 条全可用」，直接喂 prompt 候选事实面。
