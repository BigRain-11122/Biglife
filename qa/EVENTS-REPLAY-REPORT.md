# 事件流回放验收报告（events → vitals）

- 生成器：Tools/events_derive.py → events/YYYY-MM.jsonl（可重建数据面）
- 回放器：Tools/events_replay.py（本次运行）
- 事件总数：40262｜居民卡：10111｜回放居民：10111
- schema 错误：0｜回放-卡片不一致：0
- 判定：PASS

## 校验口径
逐居民比对：年轮条数=卡「年轮 N 圈」、末次年轮日期、关系对端集合、家户号。
