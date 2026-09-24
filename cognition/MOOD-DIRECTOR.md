# MOOD-DIRECTOR 城市情绪导演契约 v1.0（判据先行·2026-09-24 R127 立契）

> T-20260924-16 **c 分单**。法源=R-20260924-silicon-aliveness §四增量 4（cph4/research/ 只读）+集团 P-75 行（09-24 ~21:45 明文点名「流言链/情绪导演=本件消费面向」）。
> 定位：按时段+事件密度确定性编排全城情绪曲线（纪念日/坏消息日）——城市有了集体心情，个体台词与聚光灯随之偏移。导演态只调**城市面参数**，永不改个体人设（人设权 CEO 保留席零触碰）。
> 引擎=`Tools/mood_director.py`（下轮落件·零 LLM 零 API·纯确定性）；本契约为引擎验收判据，全过才关分单。

## 一 导演态（闭集·纯确定性函数）

`mood = f(日期, 时段, 事件密度)`，闭集五态：`steady`（平日基调）/`lively`（事件密集）/`festive`（纪念日）/`somber`（坏消息日）/`hushed`（深夜静城）。

优先序（负面信号优先=draw.py derive_context 同律）：**somber > festive > lively > hushed > steady**：

1. **somber 坏消息日**：只读事实源命中闭集——事件类型 `WEATHER_ALERT` 或 world-state `weather_kind ∈ {typhoon, gale, storm}`（真实数据激活，零推测负面）。
2. **festive 纪念日**：纪念日表（`cognition/mood-calendar.json` 数据面）按日期命中；**表行必带法源指针**（无法源指针的行=QC 拒收——禁编造纪念日，诚实律）。
3. **lively 事件密集**：只读 FluxVerse world-events 尾 24h 事件数 ≥ `--dense-at`（默认 12·参数化）。
4. **hushed 深夜静城**：00:00–05:00 深夜窗。
5. **steady**：以上皆不中=平日基调。

## 二 接口（按需调用面·非 R3 再生面·不入 census/export 正典面）

```
python -X utf8 Tools/mood_director.py [--at "YYYY-MM-DD HH:MM"] [--events N] \
  [--dense-at 12] [--calendar 路径] [--qc] [--out 路径]
```

输出：JSON 一对象=`{at, mood, source, event_density, dense_at, spotlight_max, weights, engine_v}`；`--out` 落文件，缺省 stdout。`--at`/`--events` 注入档专供测试与消费方回放（默认=真实时间+只读实数）。

## 三 消费参数（导演态三出口·全有界）

1. **台词池加权抽取**：每态一张语境桶权重表（draw.py CONTEXTS 12 桶），乘子 ∈ **[0.5, 2.0] 闭集有界**（如 festive→festival/market 桶 ×2·somber→夜桶 ×2/市集桶 ×0.5）；加权后**选词域 ⊆ 原桶**（零编造零新词）。
2. **聚光灯阈值浮动**：`spotlight_max` 浮动带 **[24, 40]**——上顶 40=正典「风格化短文本 ≤40 字聚光灯律」（SILICON-LIFE 律八沿用·只可收紧永不越顶）。
3. **全城情绪曲线输出**：同 (日期, 时段, 密度) 恒同态=消费方可按日预渲染曲线（M2 城市氛围层）。

## 四 验收判据（门禁·--qc 全过才 PASS）

1. **确定性**：同 (at, events, 参数) 双跑输出逐字节一致——全派生走 md5（`python hash()` 进程随机化禁用=behavior.py 同律）。
2. **纯函数零 LLM**：同输入恒同 mood；源码零网络调用（urllib/requests 零引用·静态断言）。
3. **权重闭集有界**：乘子 ∈ [0.5, 2.0]·加权抽词双跑一致·选词域 ⊆ 原桶。
4. **阈值浮动有界**：`spotlight_max ∈ [24, 40]` 五态逐态断言。
5. **纪念日法源指针律**：表行无法源指针=拒收（QC 注入测试行实证）。
6. **边界与优先序**：密度 N-1/N 界·深夜窗 05:00/05:01 界·somber>festive 叠日断言·`--at` 注入档全态可回放。

## 五 消费点与红线

- 消费方=draw.py `--auto` 加权接线 + spotlight.py 阈值接线（引擎落件轮一并·接口变更随件 T2 登记）+FluxVerse M2 城市氛围层（情绪曲线按日渲染）。
- 红线：FluxVerse 事件流只读零写回；导演态只调城市面参数**永不改个体人设/荣誉席**；契约本身零接口变更零登记义务（引擎轮随件办）；权重/阈值表全参数化留 CEO 一句话可翻案面。
