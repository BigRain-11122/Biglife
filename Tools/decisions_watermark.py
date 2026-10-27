"""决策水位 v2（元组指纹）· D-20261025-08 接入件

水位格式 v2 = {repo, path, commit_sha, blob_bytes, sha256} + 可复现取件命令 + consumed 清单。
比对方按 repo+commit_sha+blob_bytes 先比，再比 sha256；源变了=stale
（stale 时不前进消费水位，只记一行）。
旧水位 state/decisions-watermark.txt（逗号 ID 串）保持不动=向后兼容。

用法:
  python -X utf8 Tools/decisions_watermark.py --update   # 读取集团 origin 实况并复写元组
  python -X utf8 Tools/decisions_watermark.py --check    # 只比不写，stale 退出码 2
  python -X utf8 Tools/decisions_watermark.py --verify   # 按水位件取件命令重放并校验 sha256
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
V2_FILE = STATE / "decisions-watermark-v2.json"
V1_FILE = STATE / "decisions-watermark.txt"
CHECK_LOG = STATE / "watermark-v2-check.log"
SRC_PATH = "docs/decisions.md"
SRC_REPO = "FluxGroup"


def _repo_ident() -> str:
    """来源三元之一：优先用远端 URL，取不到回落目录名。"""
    try:
        url = _git(["remote", "get-url", "origin"], GROUP_REPO).strip()
        return url or GROUP_REPO.name
    except RuntimeError:
        return GROUP_REPO.name


def _git(args: list[str], cwd: Path) -> str:
    out = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip() or "git failed")
    return out.stdout.decode("utf-8", "replace")


def _resolve_group_root() -> Path:
    """D-20261028-04 组根解析律：活树只认 `git rev-parse --show-toplevel`，
    多候选时取 cph4/evolution-ledger.md mtime 最新者；禁 `..\\..` 跳层与硬编码镜像路径
    （镜像 D:\\FluxGroup 已陈旧，读它会静默拿旧台账）。
    """
    cands = [ROOT.parent.parent]  # life/BigLife -> life -> 组根（工作树推定，非跳层解析）
    env = os.environ.get("BIGLIFE_GROUP_ROOT")
    if env:
        cands.insert(0, Path(env))
    best: tuple[float, Path] | None = None
    for c in cands:
        if not c.is_dir():
            continue
        try:
            top = Path(_git(["rev-parse", "--show-toplevel"], c).strip())
        except RuntimeError:
            continue
        if not (top / "cph4").is_dir():
            continue
        ledger = top / "cph4" / "evolution-ledger.md"
        mtime = ledger.stat().st_mtime if ledger.is_file() else 0.0
        if best is None or mtime > best[0]:
            best = (mtime, top)
    return best[1] if best else ROOT.parent.parent


GROUP_REPO = _resolve_group_root()


def current_tuple() -> dict:
    commit_sha = _git(["rev-parse", "origin/main"], GROUP_REPO).strip()
    blob = _git(["show", f"origin/main:{SRC_PATH}"], GROUP_REPO).encode("utf-8")
    return {
        "repo": _repo_ident(),
        "path": SRC_PATH,
        "commit_sha": commit_sha,
        "blob_bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
    }


def fetch_commands(commit_sha: str) -> dict:
    """可复现取件（验收面：重放后 blob 与 sha256 一致）。

    禁止 shell 文本管道（PowerShell 会把字节转码，实测 222683→144258 假 sha），
    一律走 python subprocess 直取字节。
    """
    py = (
        'python -X utf8 -c "import hashlib,subprocess,sys;'
        f"b=subprocess.run(['git','-C',r'{GROUP_REPO}','show','{commit_sha}:{SRC_PATH}'],"
        'capture_output=True).stdout;'
        'print(len(b), hashlib.sha256(b).hexdigest())"'
    )
    return {
        "fetch": f'git -C "{GROUP_REPO}" show {commit_sha}:{SRC_PATH}',
        "fetch_origin_main": f'git -C "{GROUP_REPO}" show origin/main:{SRC_PATH}',
        "verify_sha256": py,
        "note": "verify_sha256 必须整条跑（禁经 PowerShell 文本管道，字节会被转码）",
    }


def load_v2() -> dict | None:
    if not V2_FILE.exists():
        return None
    try:
        return json.loads(V2_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def consumed_ids() -> list[str]:
    if not V1_FILE.exists():
        return []
    raw = V1_FILE.read_text(encoding="utf-8", errors="replace")
    ids = [p.strip() for p in raw.replace("\n", ",").split(",") if p.strip()]
    seen: set[str] = set()
    uniq: list[str] = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            uniq.append(i)
    return uniq


def stale_reason(recorded: dict | None, now: dict) -> str:
    """比对序=先来源三元，再内容指纹；返回 '' 即不 stale。"""
    if not recorded:
        return "no-record"
    for key in ("repo", "path", "commit_sha", "blob_bytes"):
        if recorded.get(key) != now.get(key):
            return f"source-mismatch:{key}"
    if recorded.get("sha256") != now.get("sha256"):
        return "content-mismatch:sha256"
    return ""


def is_stale(recorded: dict | None, now: dict) -> bool:
    return bool(stale_reason(recorded, now))


def log_check(now: dict, reason: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    head = "OK" if not reason else f"STALE({reason})"
    with CHECK_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp} watermark-v2 {head} sha={now['sha256'][:12]} "
                 f"bytes={now['blob_bytes']} commit={now['commit_sha'][:12]}\n")


def verify_record(recorded: dict | None) -> tuple[bool, str]:
    """按水位件取件命令重放，blob 字节与 sha256 必须与记录一致。"""
    if not recorded or not recorded.get("commit_sha"):
        return False, "no-record"
    try:
        blob = _git(["show", f"{recorded['commit_sha']}:{recorded['path']}"], GROUP_REPO).encode("utf-8")
    except RuntimeError as exc:
        return False, f"fetch-failed:{exc}"
    if len(blob) != recorded.get("blob_bytes"):
        return False, f"bytes-mismatch:{len(blob)}!={recorded.get('blob_bytes')}"
    digest = hashlib.sha256(blob).hexdigest()
    if digest != recorded.get("sha256"):
        return False, f"sha-mismatch:{digest[:12]}!={str(recorded.get('sha256'))[:12]}"
    return True, f"reproduced sha={digest[:12]} bytes={len(blob)}"


def main() -> int:
    if "--verify" in sys.argv:
        ok, detail = verify_record(load_v2())
        print(f"watermark-v2: {'VERIFY-OK' if ok else 'VERIFY-FAIL'} {detail}")
        return 0 if ok else 3

    mode = "--check" if "--check" in sys.argv else "--update"
    now = current_tuple()
    recorded = load_v2()
    reason = stale_reason(recorded, now)

    if mode == "--check":
        log_check(now, reason)
        print(f"watermark-v2: {'STALE' if reason else 'OK'} ({reason or 'all-keys-match'}) "
              f"recorded={ (recorded or {}).get('sha256', '-')[:12] } now={now['sha256'][:12]}")
        return 2 if reason else 0

    payload = dict(now)
    payload["fetch_commands"] = fetch_commands(now["commit_sha"])
    payload["consumed"] = consumed_ids()
    payload["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    if reason and reason != "no-record":
        payload["last_stale_reason"] = reason
    V2_FILE.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    V2_FILE.write_text(body, encoding="utf-8")
    # 仓库内镜像：state/ 不入库，集团抽验需可入库镜像（D-20261025-08 验收面 ⑤）
    mirror = ROOT / "docs" / "watermark-v2.json"
    mirror.parent.mkdir(parents=True, exist_ok=True)
    mirror.write_text(body, encoding="utf-8")
    log_check(now, reason)
    ok, detail = verify_record(payload)
    print(f"watermark-v2: written consumed={len(payload['consumed'])} "
          f"bytes={now['blob_bytes']} sha={now['sha256'][:12]} was_stale={bool(reason)} "
          f"repro={'OK' if ok else 'FAIL'}({detail})")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())