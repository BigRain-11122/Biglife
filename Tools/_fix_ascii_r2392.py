# -*- coding: utf-8 -*-
"""一次性修复：ASCII '?' 顶替正文（R2392 判例·T-20261020-04 第三类损伤）。

证据来源（不编造）：每条修复均取自行内容 ASCII 骨架 + 该行引入 commit 的提交说明。
修复后行尾标注修复轮次与证据指针，便于回溯。脚本幂等：已含修复标记的行跳过。

覆盖：tasks/TASKS.md 行 733/765（commit 082f15160 / 75fd65c69）
      HQ-FEEDBACK.md 行 116（commit 18e51661）
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = "〔ASCII 顶替修复"
OLD_MARK = "〔R2392 依 commit "  # 首版标记用了未经核实的轮号，一律就地改成时间+证据式
NEW_MARK = "〔ASCII 顶替修复 2026-10-27 10:0x·按 commit "

REPAIRS = [
    (
        "tasks/TASKS.md",
        733,
        "- R2326 2026-10-27 04:5x ??:",
        "- R2326 2026-10-27 04:5x 轮记：年轮 10 席(C-08823~C-08832)+行为镜像 rows=10/ring=8826"
        "+回放闸 PASS(39918/0/0)+看板重建 rings=8826/人口10114/cards=160+QC problems=0"
        "+回放闸 PASS 全量+状态导出三行刷新+residents；tokens: local=10 api=0 api_reason=-"
        "〔R2392 依 commit 082f15160 证据修复·原文为 ASCII 顶替〕",
    ),
    (
        "tasks/TASKS.md",
        765,
        "[2026-10-27 05:5x R2333] ???git pull=Already up to date",
        "[2026-10-27 05:5x R2333] 轮首 git pull=Already up to date；决策水位差集 NEW=0"
        "（D-20261027-01~07 全已消费）；orders 无涉本司新令；TASKS 无 open 新单；"
        "HQ 日清=ALREADY_REPORTED。产出=年轮 evolved=10/10（C-08922~C-08931，其中 4 席 "
        "soft-concession recent-dup-phrase 复核过闸）commit 0a9e55701；行为镜像 rows=10 ring=8925"
        " ← 7cddfbee4；回放闸 PASS（cards=10111 / events=40017 / replayed=10111 / schema=0 / "
        "mismatch=0）；池 pool_audit=PASS 自终止 SELF_TERMINATE（axes72/sprite12/greet28/faq7/neg6）"
        "hard_fails=0；相遇 3/3 满额；QC 巡检 04:32 批 problems=0；基因 b34 批 12 条 nearcheck："
        "5 CLEAN、7 需复核（ho 817/tp 623/cp 1381 阈值下 4-gram 近重），候选落 "
        "state/gene-cand-b34*.txt。tokens: local=10 api=0 api_reason=- [via BigLife-OSLoop]"
        "〔R2392 依 commit 75fd65c69 证据修复·原文为 ASCII 顶替〕",
    ),
    (
        "HQ-FEEDBACK.md",
        116,
        "| F-20261020-BL03 | 10-20 | **10-20 ??????**",
        "| F-20261020-BL03 | 10-20 | **10-20 日清（无待报）**——轮首三步/决策水位差集 NEW=0"
        "（watermark 至 D-20261020-07）；产出=基因批 10 条（ho#701-705 / tp#528-532）"
        "过近重闸入册 commit 25a27acb；让路窗 09:00-19:00 停 evolve/census LLM 批"
        "（口径=D-20261020-02），改道件=intake_batch17 补 5 条落库，19:00 后恢复 | 无需上报"
        " | P3 | closed（R1810 收口）〔R2392 依 commit 18e51661 证据修复·原文为 ASCII 顶替〕 |",
    ),
]


def main():
    ok = True
    by_file = {}
    for path, lineno, prefix, new in REPAIRS:
        by_file.setdefault(path, []).append((lineno, prefix, new))
    for path, items in by_file.items():
        full = os.path.join(ROOT, path)
        with open(full, "rb") as f:
            text = f.read().decode("utf-8")
        lines = text.split("\n")
        changed = False
        for lineno, prefix, new in items:
            cur = lines[lineno - 1]
            if OLD_MARK in cur:
                lines[lineno - 1] = cur.replace(OLD_MARK, NEW_MARK)
                changed = True
                print("OK %s:%d 标记勘正为时间+证据式" % (path, lineno))
                continue
            if MARK in cur:
                print("SKIP %s:%d 已修复" % (path, lineno))
                continue
            if not cur.startswith(prefix):
                print("FAIL %s:%d 前缀不匹配，拒绝改写：%r" % (path, lineno, cur[:60]))
                ok = False
                continue
            lines[lineno - 1] = new
            changed = True
            print("OK %s:%d 修复 %d -> %d 字" % (path, lineno, len(cur), len(new)))
        if changed:
            out = "\n".join(lines).encode("utf-8")
            tmp = full + ".tmp"
            with open(tmp, "wb") as f:
                f.write(out)
            os.replace(tmp, full)
            print("OK 写回 %s utf-8 无 BOM 字节=%d" % (path, len(out)))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())