"""决策水位 v2（元组指纹）· D-20261025-08 接入件

水位格式 v2 = {repo, path, commit_sha, blob_bytes, sha256} + consumed 清单。
比对方按 repo+commit_sha+blob_bytes 先比，再比 sha256；源变了=stale。
旧水位 state/decisions-watermark.txt（逗号 ID 串）保持不动=向后兼容。

用法:
  python -X utf8 Tools/decisions_watermark.py --update   # 读取集团 origin 实况并复写元组
  python -X utf8 Tools/decisions_watermark.py --check    # 只比不写，stale 退出码 2
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
V2_FILE = STATE / "decisions-watermark-v2.json"
V1_FILE = STATE / "decisions-watermark.txt"
GROUP_REPO = Path(r"C:\Users\sjs20\Desktop\FluxGroup")
SRC_PATH = "docs/decisions.md"
SRC_REPO = "FluxGroup"


def _git(args: list[str], cwd: Path) -> str:
    out = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip() or "git failed")
    return out.stdout.decode("utf-8", "replace")


def current_tuple() -> dict:
    commit_sha = _git(["rev-parse", "origin/main"], GROUP_REPO).strip()
    blob = _git(["show", f"origin/main:{SRC_PATH}"], GROUP_REPO).encode("utf-8")
    return {
        "repo": SRC_REPO,
        "path": SRC_PATH,
        "commit_sha": commit_sha,
        "blob_bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
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


def is_stale(recorded: dict | None, now: dict) -> bool:
    if not recorded:
        return True
    for key in ("repo", "path", "commit_sha", "blob_bytes"):
        if recorded.get(key) != now.get(key):
            return True
    return recorded.get("sha256") != now.get("sha256")


def main() -> int:
    mode = "--check" if "--check" in sys.argv else "--update"
    now = current_tuple()
    recorded = load_v2()
    stale = is_stale(recorded, now)

    if mode == "--check":
        print(f"watermark-v2: {'STALE' if stale else 'OK'} "
              f"(recorded={ (recorded or {}).get('sha256', '-')[:12] } now={now['sha256'][:12]})")
        return 2 if stale else 0

    payload = dict(now)
    payload["consumed"] = consumed_ids()
    payload["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    V2_FILE.parent.mkdir(parents=True, exist_ok=True)
    V2_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"watermark-v2: written consumed={len(payload['consumed'])} "
          f"bytes={now['blob_bytes']} sha={now['sha256'][:12]} was_stale={stale}")
    return 0


if __name__ == "__main__":
    sys.exit(main())