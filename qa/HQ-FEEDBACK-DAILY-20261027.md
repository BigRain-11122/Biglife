# HQ-FEEDBACK 日闸自测证据 · 2026-10-27

## gap #84 · 日清 spam 收口

**现象（判例）**：步 8「每日 23:00 前的一轮写一行」被轮体逐轮执行，2026-10-27 00:05–02:59 两小时内 HQ-FEEDBACK.md 新增 15 行
（R2288 / R2289 / R2293 / R2294 / R2295 / R2299 / R2300 / R2301 …每轮一行），
违反「每日一次」+ 记账预算（≤5 处/轮）。

**修法**：新增机械闸 `Tools/hq_feedback_daily.py`
- `--check`：报当日行数与 OPEN / ALREADY_REPORTED
- `--text "<正文>"`：由闸代写（自带 `- [YYYY-MM-DD HH:MM]` 戳、UTF-8、自动补行尾换行）
- `--force`：仅当日出现真实新阻塞项时追一行
提示词 `Tools/iteration_prompt.txt` 步 8 已接线；存量 15 行按诚实律不删，留作判例。

## 自测实录（2026-10-27 03:0x · 本机）

```
$ python -X utf8 Tools/hq_feedback_daily.py --check
day=2026-10-27 lines=15 ALREADY_REPORTED

$ python -X utf8 Tools/hq_feedback_daily.py --text "自测行（不应写入）"
SKIP: day=2026-10-27 already reported (15 line(s)) - daily duty satisfied

$ git diff --stat HQ-FEEDBACK.md
(空 —— 零落盘)
```

判据：ALREADY_REPORTED 时写入请求必须零落盘；`git diff` 空即证明闸生效。