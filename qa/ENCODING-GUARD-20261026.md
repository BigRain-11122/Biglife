# 全库编码守卫落件与首次全库取证（D-20261026-13 执行回执）

- 时间：2026-10-26 15:0x（@BigLife-OSLoop 交互轮）
- 派单来源：集团 decisions.md D-20261026-13（@BigLife 12h 内修透 GBK/UTF-8 混档问题）
- 落件：`Tools/encoding_guard.py`（新，可跑算具；此前只有 `Tools/tasks_board.py` 守任务板单点 + `Tools/repair_tasks_utf8.py` 一次性修复器）

## 一、派单面核查结论（先核后改，实测）

| 对象 | 实测结果 |
|---|---|
| `HQ-FEEDBACK.md` | 188041 字节，`decode('utf-8')` **严格通过**，U+FFFD=0，行数 248（>242，追加型只增不减） |
| `tasks/TASKS.md` | 89028 字节，严格通过，U+FFFD=0 |
| `qa/EVENTS-REPLAY-REPORT.md` | 严格通过，U+FFFD=0 |

结论：派单所述「242 行中 241 行 UTF-8 + 1 行 GBK」在 **R2220 已修复**，本轮复核确认无残留；本轮工作转为「防复发 + 全库可巡检」（派单正文要求的全库 decode 巡检与写口编码纪律）。

## 二、工具能力（`python -X utf8 Tools/encoding_guard.py`）

1. `--check`：git 跟踪的文本文件全库严格 UTF-8 体检（自动跳过二进制/空文件，跳过 state/logs/media 不入库面）。
   硬失败=非 UTF-8 字节 / BOM / U+FFFD；告警=疑似 GBK 乱码字与整段 GBK 误解码（可给还原建议）。
2. `--expect-lines path=N`（精确）/ `path>=N`（追加型日志只增不减，防整档重写吞段）。
3. `--append <file> --from-file|--stdin`：安全追加——写前拒损坏片段、拒已损坏目标，写后复验全档严格可解（出生地拦截，与 `tasks_board.py` 同律但可复用于任意文本档）。

## 三、首次全库实跑（证据）

```
VERDICT PASS: 20990 个文本文件严格 UTF-8 / 无 BOM / U+FFFD=0（空文件跳过 0，乱码字告警 3）
行数断言: HQ-FEEDBACK.md>=242, tasks/TASKS.md>=87 全部相符
```

告警 3 文件（均属历史/引用，非本轮损伤，按「历史禁改写」不动）：
- `HQ-FEEDBACK.md`：1 处乱码字——为 F-20260924-BL01 里**引用的证据原文**（世界事件流源头乱码），属合法内容；
- `docs/watermark-v2.json`：条目 ID `閿樼房-20260909-05`（历史 GBK 误解码 ID，已被水位集合当作字符串消费，改动会破水位差集，不动）；
- `tasks/archive/TASKS-2026-09.md`：历史月档 53 处乱码字（10-25 整卡归档带过来的旧损伤）。

## 四、双向自测（闸门有效性证据）

| 用例 | 输入 | 结果 |
|---|---|---|
| 拒 U+FFFD 片段 | UTF-8 原文按 GBK errors=replace 回写 | FAIL，RC=2，拒绝写入 |
| 拒纯 GBK 乱码片段 | `灞呮皯骞磋疆`（= `居民年轮` 被 GBK 误解码） | FAIL，RC=2，并给出还原建议 `居民年轮` |
| 拒已损坏目标 | 目标档内含上述乱码行 | FAIL，RC=2，要求先修再追加 |
| 正常片段 | `- 正常追加行` | OK，行数 4 → 6 |
| 正常中文零误报 | README/CODELY/BLUEPRINT/TASKS/CODEX 五档 | PASS，告警 0 |

判据演进留痕（自测抓出的两个真缺口）：
1. 首版靠固定乱码字表 → 纯 GBK 乱码（无字表内字符）漏检；
2. 第二版「GBK 可编码且 UTF-8 可解码」启发式 → 正常中文大量误报（`职业` 往返得到希伯来字符）；
   终版加「还原结果本身须像正常中文（CJK+ASCII ≥0.9 且 CJK ≥0.3）」绝对判据，误报归零、漏检归零。

## 五、本轮并行的常规产物（同轮取证）

- QC 巡检：`census/QC-REPORT.md` 刷新——卡片 10114 / 已进化 8157 / 异常 0 / 逐字重复环 37-37（观测面）。
- 事件流回放闸：`derive OK cards=10111 events=39241 shards=2`；`replay events=39241 cards=10111 replayed=10111 schema_errors=0 mismatch=0 -> PASS`。
- 语言线池审计：72 轴桶 + 12 像素灵桶全达标，`verdict: PASS`（自终止律，本轮不补池）。
- 年轮线：命中工作日让路窗（D-20261020-02，09:00-19:00 延后 19:00 后），本轮按令顺延。

## 六、后续接线建议（下轮/他窗可执行）

- 车道轮末（轮末收尾纪律处）加一条 `python -X utf8 Tools/encoding_guard.py --check --expect-lines "HQ-FEEDBACK.md>=242"`，把「编码健康」纳入每轮机械门；
- 任何新增文本写口（脚本追加/生成）优先复用 `--append`，禁 `open(mode='a')` 裸写。