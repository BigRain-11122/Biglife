# 派生面漂移审计（2026-11-13 11:24:09）

- verdict：**DRIFT**
- 漂移面：persona, initiatives, relations
- 重建：growth, life, ops, relations

| 派生面 | 产物 | 状态 | 说明 |
|---|---|---|---|
| anchors | `citizen-anchors.jsonl` | SAME | wrote 10114 rows -> census\export\citizen-anchors.jsonl |
| assembly | `citizen-assembly.jsonl` | SAME | wrote 10114 rows -> census\export\citizen-assembly.jsonl |
| persona | `citizen-persona.jsonl` | DRIFT | persona v2 rows=10114 bad=0 blocked=3 -> C:\Users\sjs20\Desktop\FluxGroup\life\BigLife\census\export\citizen-persona.jsonl |
| voice | `citizen-voice.jsonl` | SAME | voice manifest rows=10114 bad=0 blocked=3 -> C:\Users\sjs20\Desktop\FluxGroup\life\BigLife\census\export\citizen-voice.jsonl |
| atlas | `citizen-atlas.jsonl` | SAME | rows=10114 bad=0 dup=0 bytes=2060842 avg=203B sp=carbon:7608,silicon:2003,sprite:503 |
| initiatives | `citizen-initiatives.jsonl` | DRIFT | agency rows=10114 active=10111 date=2026-11-13 -> C:\Users\sjs20\Desktop\FluxGroup\life\BigLife\census\export\citizen-initiatives.jsonl |
| relations | `citizen-relations.jsonl` | DRIFT | written: census\export\citizen-relations.jsonl |
