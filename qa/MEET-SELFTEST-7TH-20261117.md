# 相遇写侧第七例负控常驻化（T-20261116-16 遗留子项收口）

- 日期：2026-11-17（R3307 轮，@BigLife-OSLoop）
- 来源：R3306 遗留「建议下一轮把本例并入 selftest_meet() 常驻（本轮预算已尽，未做，如实记）」

## 改了什么

1. 写入段抽成模块级函数 `_meet_write_all(ids, lines, originals, anchor_note, finder=None)`
   - 任一半 `add_ring` 抛异常 → 按 `originals` 逐文件复原（`newline="\n"`）→ 重新抛出
   - `main()` 相遇分支改为调用该函数，异常仍走原 `meet-write-error` + `sys.exit(1)`（零 commit）
   - 抽函数的理由：此前第七例只能用「复制的代码」验，抽出来自检直接驱动**真实写入路径**
2. `selftest_meet()` 新增第七例 G（`mid-write-exception`）
   - 临时目录造两张卡，把模块全局 `add_ring` 换成「第一次正常写、第二次抛异常」的桩
   - 断言 ①异常必须向上抛 ②两卡必须逐字节复原；`finally` 还原真实 `add_ring`、`rmtree` 清理
3. 输出行 `PASS 6/6` → `PASS 7/7 (… / mid-write-exception)`

## 验证

| 项 | 命令 | 结果 |
|---|---|---|
| 编译 | `python -m py_compile Tools/evolve_citizen.py` | rc=0 |
| 正控 | `python -X utf8 Tools/evolve_citizen.py --selftest-meet` | `PASS 7/7` rc=0 |
| 负控（守卫失效） | 把 `_meet_write_all` 换成「只写第一卡不还原」的桩后调 `selftest_meet()` | `FAIL 1 case(s): G rollback left a partial write: C-00011.md` rc=1 |

负控证明：该例不是恒绿装饰——回滚一旦失效，G 立即报错。

## 真库读数（未受改动影响）

`python -X utf8 Tools/qc_census.py` → `cards=10114 evolved=10114 problems=0 dup_rings=37/37 dup_new=0 meet=169 one_sided=1 meet_dup=2 meet_new_bad=0`

观察窗 D2/3（11-16 起算，11-18 读 D3 结案）维持：今日 `meet_new_bad=0`。
