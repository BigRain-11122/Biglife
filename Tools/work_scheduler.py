# -*- coding: utf-8 -*-
"""排单哨兵：主产线（年轮）没活时，按优先级把算力排给下一个有活的内容面。

Why（CEO 2026-11-17「没活闲着的时候排单，科学生产」）：
  COOLDOWN_DAYS=2 → 每天 5055 人到期，600 条/小时算只需 8 小时，剩下 16 小时空转。
  空转不是"没算力"，是"没排单"。本哨兵按质量价值排序，逐面探活：

    1 年轮批     rings    无上限（受 due 供给）  ← 主产，素材最全
    2 反思线     reflect  每日 ≤3               ← 高层洞察，最能出"人味"
    3 池轮       pool     每日 ≤1               ← 扩充语言素材，间接提质
    4 相遇轮     meet     每日 ≤3（脚本内 cap）  ← 人物关系，需选人，最复杂

探活全部零 LLM：
  rings   → evolve --audit-due 解析 due=N
  reflect → corpus.db 里「年轮≥3 且不在 30 天冷却内」的人数
  pool    → pool_audit 输出是否含「全桶达标」
  meet    → meet-candidates.jsonl 候选数 ≥2

配额状态：state/scheduler-state.json（按日重置）

用法：
  python -X utf8 Tools/work_scheduler.py --probe      # 只报各面有无活
  python -X utf8 Tools/work_scheduler.py --run-next   # 跑下一个有活的面
  python -X utf8 Tools/work_scheduler.py --stats
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
STATE = os.path.join(CO, "state")
DB = os.path.join(STATE, "corpus.db")
SSTATE = os.path.join(STATE, "scheduler-state.json")
REFLECTIONS = os.path.join(CO, "census", "reflections.jsonl")
MEET_CAND = os.path.join(CO, "census", "export", "meet-candidates.jsonl")
PY = sys.executable
NO_WINDOW = 0x08000000 if os.name == "nt" else 0

REFLECT_MIN_RINGS = 3
REFLECT_COOLDOWN_DAYS = 30
# 2026-11-17 实测供给: 反思 4085 人(年轮>=3 且过 30 天冷却)、相遇 60 对、池轮欠深桶。
# 夜窗（CEO 下班放开）: reflect 20->60, pool 2->5；meet 受 evolve 脚本内 hard cap 3。
DAILY_CAP = {"rings": 10 ** 9, "reflect": 60, "pool": 5, "meet": 3}


def _run(cmd, timeout=600, cwd=CO):
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("BIGLIFE_MODEL", "qwen3.5:9b")
    env.setdefault("BIGLIFE_LLM_URL", "http://127.0.0.1:11434/v1/chat/completions")
    env.setdefault("BIGLIFE_IGNORE_YIELD_WINDOW", "1")
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              cwd=cwd, env=env, creationflags=NO_WINDOW)
    except subprocess.TimeoutExpired:
        class R:  # noqa: D401 - 简易替身
            returncode = 124
            stdout = ""
            stderr = "timeout"
        return R()


def load_state():
    today = datetime.date.today().isoformat()
    try:
        with open(SSTATE, encoding="utf-8") as f:
            st = json.load(f)
        if st.get("date") != today:
            st = {"date": today, "counts": {}}
    except (OSError, ValueError):
        st = {"date": today, "counts": {}}
    st.setdefault("counts", {})
    return st


def save_state(st):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(SSTATE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def probe_rings():
    r = _run([PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"), "--audit-due"], timeout=300)
    m = re.search(r"due=(\d+)", (r.stdout or "") + (r.stderr or ""))
    return int(m.group(1)) if m else 0


def probe_reflect():
    """可反思人数：年轮≥3 且不在 30 天冷却。"""
    if not os.path.exists(DB):
        return 0
    done = {}
    try:
        with open(REFLECTIONS, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    o = json.loads(line)
                    done[o.get("cid") or o.get("id")] = o.get("date") or ""
                except ValueError:
                    continue
    except OSError:
        pass
    cutoff = (datetime.date.today() - datetime.timedelta(days=REFLECT_COOLDOWN_DAYS)).isoformat()
    try:
        con = sqlite3.connect(DB)
        ids = [r[0] for r in con.execute(
            "SELECT id FROM citizens WHERE ring_count >= ?", (REFLECT_MIN_RINGS,))]
        con.close()
    except Exception:  # noqa: BLE001
        return 0
    fresh = 0
    for cid in ids:
        last = done.get(cid)
        if not last or last < cutoff:
            fresh += 1
    return fresh


def probe_pool():
    r = _run([PY, "-X", "utf8", os.path.join(HERE, "pool_audit.py")], timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    return 0 if "全桶达标" in out else 1


def probe_meet():
    try:
        with open(MEET_CAND, encoding="utf-8", errors="replace") as f:
            n = sum(1 for line in f if line.strip())
        return n
    except OSError:
        return 0


def probe_all():
    st = load_state()
    counts = st["counts"]
    rows = []
    rings = probe_rings()
    rows.append(("rings", rings, DAILY_CAP["rings"] - counts.get("rings", 0), "due=%d" % rings))
    ref = probe_reflect()
    rows.append(("reflect", ref, DAILY_CAP["reflect"] - counts.get("reflect", 0),
                 "candidates=%d" % ref))
    pool = probe_pool()
    rows.append(("pool", pool, DAILY_CAP["pool"] - counts.get("pool", 0), "欠深桶" if pool else "达标"))
    meet = probe_meet()
    rows.append(("meet", meet, DAILY_CAP["meet"] - counts.get("meet", 0),
                 "candidates=%d" % meet))
    return rows


def run_face(name):
    """执行某一面，返回 (rc, 摘要)。"""
    if name == "rings":
        r = _run([PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
                  "--batch", "3", "--via", "BigLife-Scheduler"], timeout=2400)
    elif name == "reflect":
        r = _run([PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
                  "--reflect", "--via", "BigLife-Scheduler"], timeout=900)
    elif name == "pool":
        r = _run([PY, "-X", "utf8", os.path.join(HERE, "pool_gen.py"),
                  "--append", "--target", "18", "--sprite-target", "12"], timeout=1800)
    elif name == "meet":
        # 相遇要选人：交给 evolve 的 --meet 需要两个 id，这里挑候选里前两个
        ids = []
        try:
            with open(MEET_CAND, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        o = json.loads(line)
                        pair = o.get("ids") or o.get("pair") or []
                        if len(pair) >= 2:
                            ids = pair[:2]
                            break
                    except ValueError:
                        continue
        except OSError:
            pass
        if len(ids) < 2:
            return 2, "no meet pair"
        r = _run([PY, "-X", "utf8", os.path.join(HERE, "evolve_citizen.py"),
                  "--meet", ids[0], ids[1], "--via", "BigLife-Scheduler"], timeout=1200)
    else:
        return 2, "unknown face"
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    return r.returncode, "\n".join(out.splitlines()[-6:])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--run-next", action="store_true")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    rows = probe_all()
    st = load_state()
    if a.stats or a.probe or not a.run_next:
        print("date=%s" % st["date"])
        for name, work, quota, note in rows:
            print("  %-8s work=%-5s quota_left=%-10s %s" % (name, bool(work), quota, note))
        if a.probe or not a.run_next:
            return 0

    # 按优先级挑第一个「有活 且 未超配额」的面
    picked = None
    for name, work, quota, note in rows:
        if work and quota > 0:
            picked = name
            break
    if not picked:
        print("NO-WORK: all faces exhausted (rings/reflect/pool/meet)")
        return 0

    rc, summary = run_face(picked)
    st["counts"][picked] = st["counts"].get(picked, 0) + 1
    save_state(st)
    print("RAN %s rc=%d\n%s" % (picked, rc, summary))
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
