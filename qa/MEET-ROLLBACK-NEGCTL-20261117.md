# T-20261116-16 出生地拦截补口 · 负控回执（2026-11-17 05:0x R3306）

## 结论

`Tools/evolve_citizen.py` 相遇写入段的**残留出生地漏洞已补**，负控 PASS 0 fail。

## 起点核对（如实）

T-20261116-16 的两个子项**在树内已实装**（代码注释署名 T-20261027-01）：

| 子项 | 实装位置 | 状态 |
|---|---|---|
| 两卡同日互引双向断言 + 不对称回滚 | `_meet_pair_check(ids)` + `originals` 复原，`meet-asymmetry` 分支 | 已实装 |
| 写前同日同对象查重 | `_meet_ring_today(find_card(cid))` 前置闸，`meet-dup` 分支 | 已实装 |

故本单主体不需重做，只补一处**真实的残留缺口**：

## 补的缺口

原写入循环无异常兜底：

```python
for cid, line in zip(ids, lines):
    add_ring(...)              # 若此调用抛异常（非「拒绝返回」）而非静默拒绝
    paths.append(p)
bad = _meet_pair_check(ids)    # ← 异常在此前已打断，断言根本不执行
```

后果：A 卡已写入、B 抛异常 → 循环中断、异常上冒、双向断言被绕过 → **单向落卡且不回滚**，恰是本单要消灭的形态。

修法=写入段整体 `try/except`，任一半失败即复原 `originals` 并 `sys.exit(1)`，**不 commit**——与既有 `meet-asymmetry` 分支完全同构收口。

## 负控（临时夹具 · 零盘污 · 跑完 rmtree）

| 检项 | 期望 | 实测 |
|---|---|---|
| 新分支存在 + 位于不对称分支之前 | 是 | PASS |
| 回滚四要素齐备（originals 遍历 / newline="\n" / f.write / sys.exit(1)） | 是 | PASS |
| 错误分支内无 `commit_files`（禁带病提交） | 是 | PASS |
| 动态：A 写成功 + B 抛异常 → rc=1 且 A/B 双卡字节复原 | 是 | PASS |

`static 3/3 + dynamic 3/3 = PASS 0 fail`；`py_compile` rc=0。

## 诚实边界

- 存量违律 3 处（1 单向 C-08226→C-08319 / 2 重复 C-00010·C-00011）为 **2026-10-27 闸上线前历史数据**，按既有裁决不修（不伪造对方台词、不删历史行），仅作观测。
- `qc_census` 实测 `meet=169 one_sided=1 meet_dup=2 meet_new_bad=0` → **闸后新增违律 0**，与本补口的定位一致。
- 本负控是**等价逻辑仿真**（复制同构回滚段跑夹具），非真库触发真 `add_ring` 异常；真库不制造故障是正确取向。行为面真跑证据=下一次真实相遇轮 trace。
