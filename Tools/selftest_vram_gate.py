# -*- coding: utf-8 -*-
"""T-20261114-05 暖探针闸自测（零 GPU / 零外网，只用本机回环桩）。

验五件：
  A. 暖探针能应答 -> True（桩 200，1 token 请求布尔判定）
  B. 端口无人监听 -> False（不抛异常、快速返回）
  C. 桩慢于预算 -> False（预算 1s，桩睡 3s = 模拟加载期等显存）
  D. 闸台账确实落 "starved" 行且带 offenders/free 可查字段
  E. 看板汇总把 starved 计入阻断、degraded 不再被丢行（R2961 的降级探针此前被 read_gate_rows 过滤掉）

跑法：python -X utf8 Tools/selftest_vram_gate.py   （rc=0 = 全绿）
"""
import datetime
import json
import os
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import evolve_citizen as ec  # noqa: E402
import build_city_ops as ops  # noqa: E402

fails = []


def _check(name, ok, detail):
    print(("PASS " if ok else "FAIL ") + name + " - " + detail, flush=True)
    if not ok:
        fails.append(name)


def _stub(delay=0.0):
    class H(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - http.server contract
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            if delay:
                time.sleep(delay)
            payload = b'{"choices":[{"message":{"content":"ok"}}]}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *a):  # keep the console clean
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def case_a():
    srv = _stub()
    ec._SEAT = ("http://127.0.0.1:%d/v1/chat/completions" % srv.server_port, "stub-model")
    t0 = time.time()
    got = ec.llm_warm_probe(budget=5)
    _check("A warm-probe answers", got is True, "True in %.2fs" % (time.time() - t0))
    srv.shutdown()


def case_b():
    srv = _stub()
    port = srv.server_port
    srv.shutdown()
    srv.server_close()
    ec._SEAT = ("http://127.0.0.1:%d/v1/chat/completions" % port, "stub-model")
    t0 = time.time()
    got = ec.llm_warm_probe(budget=3)
    _check("B warm-probe dead port", got is False,
           "False in %.2fs (no raise)" % (time.time() - t0))


def case_c():
    srv = _stub(delay=3)
    ec._SEAT = ("http://127.0.0.1:%d/v1/chat/completions" % srv.server_port, "stub-model")
    t0 = time.time()
    got = ec.llm_warm_probe(budget=1)
    dt = time.time() - t0
    _check("C warm-probe slow seat", got is False and dt < 2.5,
           "False in %.2fs (budget 1s)" % dt)
    srv.shutdown()


def case_d():
    orig = ec.GATE_LEDGER
    tmpdir = tempfile.mkdtemp(prefix="vramgate-")
    path = os.path.join(tmpdir, "vram-gate.jsonl")
    try:
        ec.GATE_LEDGER = path
        ec._SEAT = ("http://127.0.0.1:1/v1/chat/completions", "stub-model")
        ec.record_gate_probe("starved", 11881.0, 12282.0, 11881.0 / 12282.0, 0.90)
        with open(path, encoding="utf-8") as f:
            row = json.loads(f.readline())
        ok = (row.get("state") == "starved"
              and "offenders" in row
              and row.get("used_mib") == 11881
              and row.get("total_mib") == 12282)
        _check("D ledger starved row", ok, json.dumps(row, ensure_ascii=False)[:120])
    finally:
        ec.GATE_LEDGER = orig


def case_e():
    now = datetime.datetime.now()
    ts = now.strftime("%Y-%m-%dT%H:%M:%S")
    rows = [
        {"ts": ts, "state": "ok"},
        {"ts": ts, "state": "yield"},
        {"ts": ts, "state": "starved"},
        {"ts": ts, "state": "degraded"},
    ]
    g = ops.gate_summary(rows, now=now)
    ok = (g["probes"] == 4 and g["yields"] == 1 and g["starved"] == 1
          and abs(g["share"] - 0.5) < 1e-9 and g["last_state"] == "degraded")
    _check("E summary counts", ok, json.dumps(
        {k: g[k] for k in ("probes", "yields", "starved", "share", "last_state")},
        ensure_ascii=False))

    tmpdir = tempfile.mkdtemp(prefix="vramrows-")
    path = os.path.join(tmpdir, "vram-gate.jsonl")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    kept = ops.read_gate_rows(path)
    _check("E reader keeps new states", len(kept) == 4,
           "kept=%d of 4 (degraded/starved no longer dropped)" % len(kept))


case_a()
case_b()
case_c()
case_d()
case_e()
print("verdict: %s (%d fail)" % ("PASS" if not fails else "FAIL", len(fails)))
sys.exit(0 if not fails else 1)
