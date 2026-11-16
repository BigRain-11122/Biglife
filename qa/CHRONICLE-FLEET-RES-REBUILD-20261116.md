# CHRONICLE 资源词存量重建回执 — R3199（2026-11-16 09:5x）

## 背景
R3170 已在 `Tools/city_chronicle.py` 落地三层资源词闸（derive_rows 写入口 / city_digest 读时 / 仅 RESIDENT_SAY 作用域），
但`--feed` 是 append-only，存量污染行留在谱内。此单多轮挂「待定夺」；本轮按自决律结案。

## 处置
`python -X utf8 Tools/city_chronicle.py --rebuild`（纯函数全量重派生，非手改数据）。

## 实测（可复跑）
| 项 | 值 |
|---|---|
| 重建前 rows | 2264 |
| 重建后 rows | 1836 |
| 净减 | 428（预演 would_drop=429 / would_add=1，完全对上） |
| 存量资源词行 前/后 | 429 / **0** |
| 确定性 | 双跑 md5 一致 `241F6B5327A7A0C0E3CA1CA4689D2094` |
| `--qc` | **PASS（0 fails）**，六判据 + 体量门（max 日 243、last3 median 9、458083 B） |
| digest 污染 | `FLEET_RES_RE.search(city_digest())` = **False** |
| 可见面 `census/export/city-chronicle.html` | 资源词命中 **0**，68754 B，随 dep-mtime 自动重建 |

## 影响
- 居民年轮 prompt 的城市大事块不再混入显存/VRAM 类机队报告，反向污染链条断在源头下游。
- 无其他行损失：预演差异只来自 RESIDENT_SAY 资源词行（+1 行为源事件新增正常行）。
- 回滚面：`git checkout HEAD -- cognition/city-chronicle.jsonl` 即时复原（重建幂等）。
