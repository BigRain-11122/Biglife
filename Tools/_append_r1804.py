import io, os

entry = """
- **R1804**·2026-10-20 08:39~08:55 @BigLife-OSLoop 轮实录：轮首 git pull=Already up to date；决策水位差集 NEW=0（已覆盖至 D-20261020-07），orders 物理件区无涉本司新行；本轮 08:4x 属非让路窗（<09:00）年轮批合法。**产品增量=年轮 10 卡**：evolve_citizen --batch 3 实跑，涨至 C-00941~C-00950（逐卡 [锚] 注脚+当日 FluxVerse 实况+年轮计数），脚本自提交 f7d52934；行为线 sync_rings 收口 rows_changed=10 ring_synced=10（6611af4e）；两笔已 push（8b167e15..6611af4e）→ origin。census/export/citizens-light.jsonl 已随批刷新（08:45:50）。语言线 today pool_audit=PASS/SELF_TERMINATE(DONE) 跳过；相遇轮今日 meet-cap 已满 SKIP；QC 今日已跑 problems=0 不重复。
  - 三行实况：当前活=年轮线晨窗批收尾（09:00 起进让路窗停重批）；最近实物=census/registry/*/C-00941~C-00950.md（10 张年轮卡·2026-10-20 08:44 前后落环+行为线镜像）；下个里程碑=19:00 让路窗解后夜窗年轮续批 + intake_batch14 造人批（4 席·原料已备）。
  - 未做（留单·如实）：①造人批仍未做（R1797 起连续留单·原料已备·待夜窗）；②T-20261020-01 静默超时缺陷本轮三度实证（5min 无 stdout 被前端取消，落 10 卡后中断）——start/skip/heartbeat 三处 flush 改造仍待办，建议夜窗前优先修。
  - tokens: local=10 api=0 api_reason=-（10 席年轮本地模型生成；池审/行为线收口=确定性零 LLM；全轮零云端）
"""

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tasks", "TASKS.md")
data = open(path, "rb").read()
if b"R1804" in data:
    print("SKIP already present")
else:
    with open(path, "ab") as f:
        if not data.endswith(b"\n"):
            f.write(b"\n")
        f.write(entry.encode("utf-8"))
    print("APPENDED")