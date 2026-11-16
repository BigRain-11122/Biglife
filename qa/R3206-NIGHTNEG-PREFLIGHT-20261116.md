# R3206 · 夜间负控协议预检与补丁修复（T-20261115-04 换靶线）

- 时间：2026-11-16 11:5x–12:0x（让路窗内·workday 09:00-19:00·D-20261020-02）
- 执行：BigLife-OSLoop 轮体
- 触发：R3204 已定「19:00 后首轮负控协议」，本轮做**协议开跑前预检**，避免夜窗卡在缺件上

## 发现的真缺陷（两个，均可致命）

1. **补丁损毁**：`state/pending/R3204-quota-gate.patch` 报 `error: corrupt patch … 第 25 行`。
   根因＝该文件曾走有损转码往返（中文注释字节变 `?`，且 `?` 吞掉了换行，多行注释被拼成一行）。
   后果＝协议第一步 `git apply` 直接失败，整个负控窗无法开跑。
2. **测试件不在协议路径**：协议第二步要求 `python -X utf8 qa/test_citywide_refusal_ban.py`（须 12/12），
   但 `qa/` 下无此文件——原件在 `state/pending/test_citywide_refusal_ban.py`（11:25 落盘·12 项断言），
   需「放回」才可跑。照协议字面执行会在第二步报「文件不存在」而中断。
   **诚实更正**：本轮初判为「测试件缺失」，实为「未放回协议路径」——原件内容完好，已核实并沿用原件。

## 修复做法（可复核）

- 补丁重建：在临时副本上施加既定 4 处改动 → 由 `git diff --no-index` 产出真实 diff（UTF-8/LF，
  中文注释全部重写为干净文本），落 `state/pending/R3204-quota-gate.patch`（协议路径）＋
  `qa/pending-R3204-quota-gate.patch`（入库可审副本，内容同源）。
  改动面：① `ring_violations` 增 `citywide-refusal-ban` 前缀命中判定（≥8 字·own-catchphrase 豁免）；
  ② 新增 `REFUSAL_BAN_HOURS=12` / `REFUSAL_BAN_GATES` / `recent_refusal_bans()`；
  ③ `gated_llm` 命中即 `break`（不烧 regen）；④ `main()` 注入 `sig["refusal_bans"]` 并打读数行。
- 测试件补齐：`qa/test_citywide_refusal_ban.py`，12 项确定性断言（常量/缺文件/12h 窗/非重复类闸剔除/
- 测试件放回：原件 `state/pending/test_citywide_refusal_ban.py` 复制至协议路径 `qa/test_citywide_refusal_ban.py`
  （内容零改动，12 项断言：两族正控入禁牌／anchor 与 12h 外不入／禁牌面不自延长 TTL／命中即标／
  own-catchphrase 豁免／干净句零误伤／sig 缺字段零漂移／带「」键前缀命中／缺失账本返回空）。

## 证据

| 检查 | 命令 | 结果 |
|---|---|---|
| 补丁可打 | `git apply --check state/pending/R3204-quota-gate.patch`（及 `qa/` 同源副本） | **rc=0 / rc=0** |
| 正控（原件测试 × 已打补丁 Tools 副本） | 全量 Tools 副本 → `git apply` → `python qa/test.py` | apply **rc=0**、**verdict: PASS（12/12）** |
| 负控（未打补丁 Tools 副本） | 同上但不打补丁 | **rc=1**（`AttributeError: recent_refusal_bans`，预期按律失败） |

## 19:00 后首轮的协议（原样可跑，无缺件）

```powershell
# ① 基线：不动代码先跑一批，取 hard-refuse / 落环数 / state/ring-refusals.jsonl 新增 opening12 分布
python -X utf8 Tools/evolve_citizen.py --batch 3 --via BigLife-OSLoop
# ② 打补丁（测试件已在 qa/，本轮已放回，无需再拷）
git apply state/pending/R3204-quota-gate.patch
python -X utf8 qa/test_citywide_refusal_ban.py        # 须 12/12
# ③ 改造后同批，读三数：hard-refuse 数 / citywide-refusal-ban 命中数 / 落环数
python -X utf8 Tools/evolve_citizen.py --batch 3 --via BigLife-OSLoop
# ④ 回退口：落环数低于基线 或 命中数 > 同批 30% → git checkout -- Tools/evolve_citizen.py
```

注：本轮**未改** `Tools/evolve_citizen.py`（工作树该文件净），负控仍需在 LLM 窗内按上表执行。
