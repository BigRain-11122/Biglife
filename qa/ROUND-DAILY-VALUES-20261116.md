# ROUND-DAILY 值域断言接线回执（`--values`）

- 轮次：R3235 · 2026-11-16 16:1x-16:3x · @BigLife-OSLoop · 让路窗内确定性轮（零 LLM）
- 法源：集团 D-20261116-13「结构自洽即 PASS＝假绿，`--check` 必须含值域断言」
- 改动面：`Tools/round_daily.py` 新增只读模式 `--values`（默认 `--check` / `--run` 路径零变化）

## 病根（本司同族）

`round_daily` 原判据只问「输出是否比输入旧」（mtime / 自报时点 / 内容漂移 / 脚本哈希 / 依赖指纹），
不问「输出里到底有没有东西」。一个 0 记录的渲染器报错页只要 mtime 是今天，
本轮依旧印 `verdict: PASS` —— 这正是 10-27 起 12 个面静默停更 15 天未被发现的同一类失效面
（当时补的是「新鲜度」，本轮补的是「值域」）。

## 判据（三条，全为内容面，不看 mtime）

| 编号 | 断言 | 驳回码 |
|---|---|---|
| A1 | 页面体积 ≥ 512B（拦空骨架 / 报错页） | `hollow:<n>B` |
| A2 | `census/export` 下的面必须含今日日期串（静态人卡册 `dossiers` 豁免） | `no-today` |
| A3 | 至少一处记录级标记（`li/tr/article/section/img/td` 或 `card/item/toc` 类），或体积 ≥50KB（数据在 `<script>` 内由 JS 渲染的三面：地图 SVG / 陈列墙 / 人卡册） | `no-records:<n>B` |

未登记的 `.html` 一律 `missing`。

## 实跑读数

```
== round_daily (values) ==
faces=30 exempt=dossiers
verdict: VALUES-PASS n=30
rc=0
```

首跑曾报 5 面 `no-records`（rumors/map/gallery/growth/index）——逐面探针实读其 DOM 结构后
确认是「标记名未覆盖」（`article` / `class="card"` / `class="toc"`）与「JS 渲染无 DOM」两类假阳性，
非页面缺陷；据此定标后转绿，未放宽到 `任何非空即过`。

## 负控（gate-rigor）

把 `city-rumors.html` 替换为 66B 空壳页（含今日日期，模拟「渲染失败但日戳正确」），
判定逻辑给出 `_neg_rumors.html(hollow:66B)` → 拦下；原件未动（副本在 `state/`，不入库）。

## 诚实边界

- 本闸证明「面不空、带当日、有记录结构」，**不证明数据正确**（例：族分布算错仍会过）。
  数值正确性仍由 `qc_census` / `events_refresh --gate` / `ring_open_family --check` 三闸承担。
- 默认路径（`--run` / `--check`）字节级未变，OS 轮调用方无需改动。
- 三面 JS 渲染页走体积代理，属弱证据；若日后渲染器改为服务端直出，应把代理换成 DOM 断言。
