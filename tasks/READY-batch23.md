# 批二十三·夜窗自领就绪单（R1818 · 2026-10-20 13:1x）

**文件**：`Tools/intake_batch23.py`（5 席碳基原生代 C-10121~C-10125）
**原料**：`genes/lives.json` ho#731-735 / tp#558-562（R1818 已登记，gene_nearcheck 0 近重）
**门闸**：`state/_dryrun_b23.py` 九门干跑 PASS（5 卡全过，零写盘；证据=本轮 shell 输出 CARD OK ×5）
**排程**：D-20261020-02 让路窗排程闸已入 main()（工作日 09:00-19:00 返回码 5 零写入）

## 夜窗执行指令

```
python -X utf8 Tools/intake_batch23.py
```

预期：`INTAKE BATCH23 OK: C-10121~C-10125 入册·post rows=10119`，随后
`POST-CLOSEOUT: needs rc=0 behavior rc=0 rows=10119`。

## 席位清单

| # | ID | 姓名 | 城区 | 职业 |
|---|----|------|------|------|
| 1 | C-10121 | 鲁守业 | MD 老城巷 | 木匠 |
| 2 | C-10122 | 谢连生 | OR 老街口 | 锁匠 |
| 3 | C-10123 | 尹伯言 | QT 秦淮坊 | 刻章匠 |
| 4 | C-10124 | 邵兰英 | GM 游戏城江堤 | 风筝匠 |
| 5 | C-10125 | 常景明 | NS 北外滩 | 修表匠 |

## 基线（跑前必须命中，否则 fail-fast）

PRE_LIGHT=10114 · MAX_ID=10120 · ho=735 · tp=562 · POST_LIGHT=10119