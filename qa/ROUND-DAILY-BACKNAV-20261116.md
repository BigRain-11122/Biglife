# round_daily 值域闸 A4「可返回」断言接线（R3236·2026-11-16 16:2x）

## 病根
2026-11-16 16:03（R3234/R3235 窗口）发现 `city-ring-openings.html`、`city-dashboard.html` 两页
由索引链入却无返回索引入口——CEO 打开后走不回来。当时靠人眼巡检补导航，闸不守则下次新面照犯。
`--values`（R3235 v0.27）只断言 A1 非空壳 / A2 带当日 / A3 有记录，**不问页面可达性**。

## 改动（Tools/round_daily.py v0.29）
`_value_audit()` 增 A4：除 `index.html` 外的登记面，页面正文必须含 `index.html` 引用，
否则 `VALUE-FAIL <rel>(no-backnav)`。只读不改盘，默认路径（`--check`/`--run`）行为零变化。

## 证据
| 项 | 命令 | 结果 |
|---|---|---|
| 正例 | `python -X utf8 Tools/round_daily.py --values` | `faces=30 exempt=dossiers` / **VALUES-PASS n=30** rc=0 |
| 负控 1（无效） | 把 `index.html` 替换为 `x-index.html` | 仍 PASS —— 替换串仍含子串，**该负控本身失效，不计为证据** |
| 负控 2（有效） | 把 `city-rumors.html` 内 `index.html` 全替换为 `zzz-nolink.html` | **VALUE-FAIL city-rumors.html(no-backnav) n=1/30** rc=2 |
| 还原 | 备份覆盖回原文件 | VALUES-PASS n=30；`git status --porcelain census/` 空＝逐字节还原 |

## 诚实边界
- 断言为弱式：只查「文本中出现 index.html」，不校验该引用是可见导航还是注释/CSS 内串；
  强式（解析 `<a href="index.html">` 且可见）留待有真实漏检材料时再升。
- 覆盖面＝`REGISTRY` 登记的 30 个面（即 round_daily 自身会重建的面）；
  export 目录下另 9 个非登记面不在本闸射程。
- A4 只防「孤儿页重新出现」，不证明页面内容正确；内容正确性仍由 A1-A3 + qc_census + events gate 承担。
