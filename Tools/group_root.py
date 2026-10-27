"""组根解析·D-20261028-04 组根解析律

集团根一律以 `git rev-parse --show-toplevel` 认活树，禁止盲 `..\\..` 跳层与硬编码镜像路径
（镜像 D:\\FluxGroup 已陈旧，读它会静默拿旧台账）。多候选时取 cph4/evolution-ledger.md
mtime 最新者；全部候选不可用则回落本仓上两级（保证旧环境仍可跑，不 fail-hard）。
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _toplevel(path: Path) -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path), capture_output=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    top = out.stdout.decode("utf-8", "replace").strip()
    return Path(top) if top else None


def resolve() -> str:
    cands: list[Path] = []
    env = os.environ.get("BIGLIFE_GROUP_ROOT")
    if env:
        cands.append(Path(env))
    cands.append(REPO_ROOT.parent)  # life/
    cands.append(REPO_ROOT.parent.parent)

    best: tuple[float, Path] | None = None
    for cand in cands:
        if not cand.is_dir():
            continue
        top = _toplevel(cand)
        if top is None or not (top / "cph4").is_dir():
            continue
        ledger = top / "cph4" / "evolution-ledger.md"
        mtime = ledger.stat().st_mtime if ledger.is_file() else 0.0
        if best is None or mtime > best[0]:
            best = (mtime, top)
    return str(best[1]) if best else str(REPO_ROOT.parent.parent)