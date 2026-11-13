# 心跳状态行丢失可见化守卫（T-20261113-01 结案证据）

- 日期：2026-11-13 16:5x
- 席位：BigLife-OSLoop R2795
- 缺陷来源：tasks/TASKS.md T-20261113-01（R2736 立）

## 一、缺陷（两层，第二层是本轮新发现）

1. **残渣行**：`state/heartbeat.txt` 中 R2734 行实文以 `%s |` 开头——格式化串漏参，状态行开头带字面量 `%s`。
2. **静默丢弃**（更严重）：该行**没有时间戳**。`Tools/build_city_ops.py::heartbeats()` 的正则要求 `YYYY-MM-DD HH:MM:SS ` 前缀，不匹配即 `continue`——整条状态行从看板上凭空消失，不报错、不留痕。CEO 可见面表现为「少了一轮」，属产品优先律 §5 可读性/可核对性的直接破坏。
3. 同批扫出第二条同类：心跳文件**首行带 U+FEFF BOM**（`round=R2675` 行），同样被丢弃。

写方不可控：状态行由外部启动器/会话壳拼装（全仓 `rg -F "lane=" -g "*.py"` 零命中），本仓不盲改壳。

## 二、修法

### 1. 渲染层：丢失可见化（出生地拦不住，就把丢失变成看得见）

`Tools/build_city_ops.py`：

- 抽出纯函数 `parse_heartbeat_text(text) -> (rows, orphans)`；`heartbeats()` 变为薄包装。
- 新增 `ORPHAN_PAT`：无时间戳但含 `round=R\d+` / `当前活=` / `最近实物=` / `lane=` 的行计入 `orphans`。
- 解析时 `lstrip("\ufeff")`，BOM 不再吞行。
- 看板新增 KPI 卡「无时间戳状态行（被丢弃，需修）」，>0 标红；心跳表头明示条数。
- stdout 增加 `orphans=N` 字段，便于轮末核对。

### 2. 数据侧：回填两条

| 行 | 修法 |
|---|---|
| 首行 `round=R2675` | 剥 U+FEFF |
| `%s \| round=R2734` | 补 `2026-11-13 10:20:00`（邻行夹逼：上 10:19:56 / 下 10:29:28），行内标 `ts=回填@R2795（邻行夹逼 …）` |

`state/` 为 gitignored，回填仅本地生效；代码守卫与本文入库。

## 三、验证

```
$ python -X utf8 Tools/build_city_ops.py --selftest
selftest: 6 probes, 0 fail
```

探针集合：正常行 / 残渣行 / 无关文本 / 1 好 1 坏混合 / 非法时间戳（负控）/ BOM 行。

重建前后实测：

| 指标 | 修前 | 修后 |
|---|---|---|
| 有效心跳行 `hb` | 106 | **108** |
| 无时间戳状态行 `orphans` | 2 | **0** |
| `city-ops.html` 含 `%s` | — | False |
| 看板 KPI「无时间戳状态行」 | — | 0 |

## 四、边界（诚实声明）

- 本守卫**不让坏行变得合法**，只让坏行不再无声消失：坏行数 >0 时看板标红，逼下一轮去修数据或修壳。
- 根治仍在写方（外部启动器模板补时间戳）。本仓能做的是把它变成可核对项——已做到。

## 五、同批自伤事件与出生地闸（16:5x 追加）

**现象**：本轮把缺陷写进 `docs/status-export.json` 的 dept 文案时，为了说明问题**引述**了那个字面量占位符，于是 CEO 面又多出一条带 `%s` 的句子——自己把刚修的病重新引回界面（自查时 `has_pct_s: True` 抓到）。

**处置**：
1. 就地改写成中文说法（「格式化串残渣行」），JSON 解析自证通过，`replaced=1 pct_s_left=False R2795=True`。
2. **出生地拦截**：`Tools/update_status_export.py` 新增 `TEXT_PLACEHOLDER_GUARD`——`dept_text / qc_text / top_text / results_note` 任一含裸 `%s/%d/%i/%f/%r` 直接拒写（措辞要求改中文），避免「引述缺陷」把缺陷搬回对外面。

**验证**：
- 自检电池 `QC_BATTERY 6/6 PASS`。
- 负控：payload 的 `top_text` 塞入裸占位符 → 真被拒（`TEXT_PLACEHOLDER_GUARD ... contains bare %s-like token`）。
- 收尾复核：`docs/status-export.json` `pct_s=False` 且保留 `R2795`；`city-ops.html` `pct_s=False`、`orphans=0`。

**教训**：对外面的"引述"与"残渣"在读者眼里没有区别——描述缺陷时要换词，不要复刻病征。

