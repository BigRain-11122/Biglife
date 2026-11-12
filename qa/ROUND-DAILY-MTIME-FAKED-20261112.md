# round_daily v0.9：mtime 伪造面判据（T-20261112-04 同族第三面）

日期：2026-11-12 17:0x
轮次：R2609 @BigLife-OSLoop
类型：判据缺陷修复（零 LLM / 零 GPU）

## 病根

git 提交与检出会把文件 mtime 刷成当日，内容却停在半个月前。
faces 档判据 `age > 1.0` 只看 mtime ⇒ 面被永久判 fresh、日更闸永久跳过。

实证两例（本轮开修前实测）：

| 页面 | 页脚自报 | 文件 mtime | 真实停更 |
|---|---|---|---|
| census/export/city-growth.html | 生成 2026-10-28 03:43 | 11-12 01:12（R2513 提交刷新） | 15 天 |
| census/export/city-meets.html | 生成 2026-10-28 04:05 | 11-12 01:12（同一提交） | 15 天 |

页面内日期分布佐证：city-growth.html 全文仅 1 处 `2026-10-28`；city-meets.html 为
`2026-10-28`×2 + 09-30 + 09-29 —— 无任何 11 月内容。

## 修法

`Tools/round_daily.py` v0.9 新增 `_SELF_TS` + `_self_ts_stale()`：

- 判据 = **页面自报生成时点 vs 该页自身 mtime**，自报旧于 mtime 超 1 天即 `mtime-faked`。
- 只比页面内部两处口径、不与源文件比对 ⇒ 源频繁刷新不会诱发零信息量重建
  （沿用 SNAPSHOT_SPECS 注释里「时点纯属装饰的面勿登记」的既有取舍）。
- daily/input/data 档与 faces 档**均接入**（此前 faces 档完全没有内容校验）。

## 验证（全部实跑）

1. `py_compile` rc=0。
2. 五探针 selftest **5/5 PASS**：正控 15 天伪造→报；自报与 mtime 同分钟→不报；
   无时点→不报；非 html→跳过；边界 25h→报。
3. 活体负控：复制真实 `city-meets.html`，页脚回拨为 `2026-10-28 04:05`、mtime 保持今天
   → 返回 `mtime-faked:city-meets.html claimed=2026-10-28 04:05 mtime=2026-11-12 17:03`；
   未篡改的原页面→`None`（零误报）。
4. `Tools/ruff_gate.py` → `1 file(s) CLEAN (F401,F811,F841,SIM115,RUF059)`。
5. 重建后 `round_daily --check` → `stale=0 ran=0 failed=0 verdict: PASS`。

## 本轮盘面变化（CEO 可见）

- `census/export/city-growth.html` 内容 10-28 → **11-12 17:02**（pages=11 卡=10111 覆盖=100.0%）。
- `census/export/city-meets.html` 内容 10-28 → **11-12 17:01**（meets=90 scenes=48 dates=21 people=10091）。
- 两个 15 天停更的可见面恢复当日口径。

## 诚实边界

- 只覆盖「页面正文自报生成时点」的面；完全不写时点的面仍只能靠 mtime（无内容可比对）。
- 阈值 1 天为刻意宽松：容忍生成器写页脚与落盘之间的分钟级偏差，只抓天级伪造。
- 本轮为让路窗内（工作日 09:00-19:00）确定性作业，年轮/相遇线零改动。
