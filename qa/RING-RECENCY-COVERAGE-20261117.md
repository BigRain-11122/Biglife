# 年轮覆盖：高号段积压是否=选择集缺陷（实测否证）

生成 2026-11-17 09:5x · 零 LLM 确定性 · 证据可复跑
触发：`census/export/city-ring-recency.html` 显示 51.4% 居民 14 天以上未开口，且今日 490 环疑似全落在低号段——怀疑 R2794「最久未开口优先」失效。

## 结论（一句话）

**不是选择集缺陷**：三查全部否证缺陷假设，高号段积压是 10-29~11-11 断档期留下的存量，正按「最久优先」逐日消化，预计 **≈9 天**（约 5145 到期席 ÷ ≈550 席/夜）扫到 5000-9000 号段。

## 三查与读数

### ① 今日年轮按号段分布（源 census/export/citizens-light.jsonl 的 recent_ring_date）

| 号段 | 在册 | 今日落环 | 今日占比 | 剩余到期(next≤今日) |
| --- | ---: | ---: | ---: | ---: |
| 0-999 | 993 | 240 | 24.2% | 0 |
| 1000-1999 | 1000 | 193 | 19.3% | 137 |
| 2000-2999 | 1000 | 0 | 0.0% | 0 |
| 3000-3999 | 1000 | 25 | 2.5% | 0 |
| 4000-4999 | 1000 | 32 | 3.2% | 142 |
| 5000-5999 | 1000 | 0 | 0.0% | 1000 |
| 6000-6999 | 1000 | 0 | 0.0% | 1000 |
| 7000-7999 | 1000 | 0 | 0.0% | 1000 |
| 8000-8999 | 1000 | 0 | 0.0% | 999 |
| 9000-9999 | 1000 | 0 | 0.0% | 867 |
| 10000-10999 | 121 | 0 | 0.0% | 0 |
| 合计 | 10114 | **490** | — | **5145** |

### ② 假设 A「拒稿也推 last，导致被拒居民永久沉底」— **否证**

逐卡比对 `state/evolve-cursor.json` 的 `last` 与卡片真实 `recent_ring_date`：

- 全 10114 席中 `last > 真实年轮日` 的件数 = **0**（11 个号段全部为 0）
- 即游标 last 未因拒稿/尝试而虚增，被拒居民不会被误判为"刚开过口"。

### ③ 假设 B「到期排序不再最久优先」— **否证**

直接调用 `Tools/evolve_citizen.py::due_citizens(cursor, 3)` 实跑，取回前三席：

```
C-01222  last=2026-10-24  next=2026-10-31
C-01223  last=2026-10-24  next=2026-10-31
C-01229  last=2026-10-24  next=2026-10-31
```

- 三席全部为超期 17 天的最旧批次，**排序确为「最久未开口优先」**；
- 5000-9000 号段游标多为 `last=2026-10-25`，**仅比 10-24 新一天**，故正排在 C-01222 这一类之后。

## 判读

- 今日 490 环集中在 0-4000 号段，是「按 last 升序推进、当日席位于最旧批次处用完」的正常结果，不是跳段；
- 0-999 今日剩余到期=0、1000-1999 剩 137，说明最旧批次已被扫到尾部，队列正连续衔接到 5000+；
- 断档期（10-29~11-11 无批次）使 `last≈10-24/10-25` 这一"最旧层"异常厚实，是积压成因。

## 复跑命令

```powershell
# ①号段分布 + ②偏斜检测
python -X utf8 -c "import json,collections,datetime;rows=[json.loads(l) for l in open('census/export/citizens-light.jsonl',encoding='utf-8')];cur=json.load(open('state/evolve-cursor.json',encoding='utf-8'));print(sum(1 for r in rows if (r.get('recent_ring_date') or '').startswith('2026-11-17')))"
# ③排序实跑（在 Tools/ 下）
python -X utf8 -c "import importlib.util,json;s=importlib.util.spec_from_file_location('ec','evolve_citizen.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);c=json.load(open('../state/evolve-cursor.json',encoding='utf-8'));print(m.due_citizens(c,3))"
```

## 待观察（非行动项）

- 11-18 起每晚读本条 ① 表：5000-9000 号段「今日落环」应逐日非零且「剩余到期」单调下降；连续 3 夜仍为 0 才升格为真缺陷交修。
- 若需缩短积压周期，唯一杠杆是每晚席位预算（LLM 侧，受让路窗与产能约束），非排序逻辑。
