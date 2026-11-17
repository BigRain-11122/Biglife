#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""git_guard.py - honest-clean check for the round-start git status step.

T-20261117-01 (R3311): this box runs 19 long-lived `git fsmonitor--daemon`
processes shared across the workspace repos. For a repo that still has
`core.fsmonitor` unset, the daemon feeds a stale index over IPC and plain
`git status --porcelain` reports an EMPTY tree while
`git -c core.fsmonitor=false status --porcelain` reports ~30 modified files.
Rounds R3308/R3310 recorded "census/registry zero change" off the false-clean
reading, which is exactly the failure mode 铁律② (only targeted `git add` on a
dirty tree) is meant to prevent: on a fake-clean tree the round concludes it
has nothing to stage and silently drops its own product.

The local fix (`git config core.fsmonitor false`) must be repeated per clone,
so the repository-level answer is a check the round can run instead of a
setting it has to remember. This tool compares both readings and fails loudly
when they disagree; a consistent tree is reported as PASS either way.

Usage:
  python -X utf8 Tools/git_guard.py            # check this repo
  python -X utf8 Tools/git_guard.py --repo PATH
  python -X utf8 Tools/git_guard.py --selftest # negative control, zero disk writes
Exit 0 = readings agree (clean or dirty, but honest); 1 = FALSE-CLEAN risk;
2 = git could not be queried (unusable state, not a verdict).
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)


def run_git(args, cwd):
    """Return (rc, stdout) for a git command; rc=-1 means it could not run."""
    try:
        p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001 - report, never crash the round
        return -1, str(exc)
    return p.returncode, p.stdout or ""


def split_paths(porcelain_text):
    """Porcelain v1 lines -> {path: status_code}.

    A rename shows as `R  old -> new`; the destination path is what a caller
    would stage, so key on that.
    """
    out = {}
    for raw in porcelain_text.splitlines():
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        code, _, path = line[:2], line[2:], line[3:] if len(line) > 3 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        out[path.strip()] = code.strip() or "?"
    return out


def compare(default_map, stable_map):
    """Return (missing_in_default, extra_in_default).

    `missing_in_default` are files the flighty reading hid - the false-clean
    signal. `extra_in_default` is the reverse (rare: the daemon reports a file
    the stable read already saw as clean; still a divergence worth printing).
    """
    missing = sorted(set(stable_map) - set(default_map))
    extra = sorted(set(default_map) - set(stable_map))
    return missing, extra


def daemon_state(cwd):
    """Best-effort `git fsmonitor--daemon status`; never fatal.

    That subcommand exits 1 for the ordinary "this worktree is not watched"
    answer, so the decision is made on the text, not the exit code.
    """
    rc, out = run_git(["fsmonitor--daemon", "status"], cwd)
    text = (out or "").strip().lower()
    if not text:
        return "unknown (rc=%d)" % rc
    if "not watching" in text or "not running" in text:
        return "not-watching"
    if "watching" in text or "running" in text:
        return "watching"
    return text.splitlines()[0][:60]


def check(repo, quiet=False):
    rc, top = run_git(["rev-parse", "--show-toplevel"], repo)
    if rc != 0 or not top.strip():
        print("git_guard: not a git work tree: %s (%s)" % (repo, top.strip()))
        return 2
    top = top.strip()

    rc_a, out_a = run_git(["status", "--porcelain"], top)
    rc_b, out_b = run_git(["-c", "core.fsmonitor=false", "status", "--porcelain"], top)
    if rc_a != 0 or rc_b != 0:
        print("git_guard: unable to read status (default rc=%d, stable rc=%d)"
              % (rc_a, rc_b))
        return 2

    default_map = split_paths(out_a)
    stable_map = split_paths(out_b)
    missing, extra = compare(default_map, stable_map)
    dstate = daemon_state(top)

    if not quiet:
        print("repo: %s" % top)
        print("default status: %d path(s) | fsmonitor-off status: %d path(s)"
              % (len(default_map), len(stable_map)))
        print("fsmonitor daemon: %s" % dstate)

    if not missing and not extra:
        if not quiet:
            print("verdict: PASS - both readings agree (%s tree)"
                  % ("clean" if not default_map else "dirty"))
        return 0

    print("verdict: FALSE-CLEAN RISK - readings disagree")
    for path in missing[:20]:
        print("  hidden by default status: %s (%s)" % (path, stable_map[path]))
    if len(missing) > 20:
        print("  ... %d more hidden" % (len(missing) - 20))
    for path in extra[:10]:
        print("  only in default status: %s (%s)" % (path, default_map[path]))
    print("fix: git config core.fsmonitor false   # per clone, not committed")
    return 1


def selftest():
    """Negative control: the comparator must catch a hidden file."""
    fails = []

    stable = split_paths(" M census/a.md\n M census/b.md\n?? new.md\n")
    fake_clean = split_paths("")
    missing, extra = compare(fake_clean, stable)
    if missing != ["census/a.md", "census/b.md", "new.md"]:
        fails.append("A hidden-everything not detected: %r" % (missing,))
    if extra:
        fails.append("A spurious extra: %r" % (extra,))

    # Healthy input: identical readings must produce no complaint.
    missing, extra = compare(stable, split_paths(" M census/a.md\n M census/b.md\n?? new.md\n"))
    if missing or extra:
        fails.append("B identical readings flagged: %r / %r" % (missing, extra))

    # Rename lines key on the destination path.
    renamed = split_paths("R  old/x.md -> new/x.md\n")
    if list(renamed) != ["new/x.md"]:
        fails.append("C rename path wrong: %r" % (list(renamed),))

    # Partial hide (the R3308 shape): a clean default read with a dirty stable read.
    missing, extra = compare(split_paths(""), split_paths(" M TASKS.md\n"))
    if missing != ["TASKS.md"]:
        fails.append("D partial hide not detected: %r" % (missing,))

    for line in fails:
        print("FAIL git-guard-selftest:", line)
    if fails:
        print("git-guard-selftest: FAIL %d case(s)" % len(fails))
        return 1
    print("git-guard-selftest: PASS 4/4 (hidden-all / identical / rename-path / partial-hide)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Honest-clean check for git status")
    ap.add_argument("--repo", default=CO, help="repo path (default: this repo)")
    ap.add_argument("--quiet", action="store_true", help="print only on divergence")
    ap.add_argument("--selftest", action="store_true", help="run the comparator negative control")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return check(args.repo, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
