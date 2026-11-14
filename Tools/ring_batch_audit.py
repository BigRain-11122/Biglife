# -*- coding: utf-8 -*-
"""年轮批净增核验闸（T-20261114-03 结单件·零 LLM / 零网络）。

病根（R2977 判负误报）：年轮批脚本自带 commit（`commit_files`），所以批跑
完之后 `git diff HEAD -- census/registry` 恒为空。用工作树 diff 判「净增」
会把每一批真写入都读成零净增 —— 判据错，不是代码错。

正判据 = 该批自己的提交：`git show --stat <sha>` 里 census/registry 的改动
文件数应等于提交消息列出的居民数，且每张卡的当日年轮行真的在。

跑法：
  python -X utf8 Tools/ring_batch_audit.py                # 审今日最新一批
  python -X utf8 Tools/ring_batch_audit.py --commit <sha> # 审指定提交
  python -X utf8 Tools/ring_batch_audit.py --date 2026-11-14
rc=0 PASS / rc=1 FAIL（任一不一致即 FAIL）
"""
import argparse
import datetime
import os
import re
import subprocess
import sys

CO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CID_RE = re.compile(r"C-\d{5}")
REG_PREFIX = "census/registry/"


def git(*args):
    return subprocess.run(["git", "-C", CO] + list(args),
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def find_commit(commit, date):
    if commit:
        return commit
    r = git("log", "--all", "--grep=^年轮环", "--format=%H%x1f%ad%x1f%s",
            "--date=short", "-n", "80")
    if r.returncode != 0:
        return None
    for line in r.stdout.splitlines():
        parts = line.split("\x1f")
        if len(parts) < 3:
            continue
        sha, cdate, subject = parts[0], parts[1], parts[2]
        if cdate == date and "年轮环" in subject:
            return sha
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--commit", default=None)
    args = ap.parse_args()

    sha = find_commit(args.commit, args.date)
    if not sha:
        print("FAIL no 年轮环 commit found for %s" % args.date)
        return 1

    subj = git("log", "-1", "--format=%s", sha).stdout.strip()
    ids = CID_RE.findall(subj)
    files = [p for p in git("show", "--name-only", "--pretty=format:", sha)
             .stdout.splitlines() if p.strip().startswith(REG_PREFIX)]

    print("commit  %s" % sha)
    print("subject %s" % subj[:160])
    print("listed  citizens=%d  changed_registry_files=%d" % (len(ids), len(files)))

    fails = []
    if len(ids) != len(files):
        fails.append("count-mismatch listed=%d files=%d" % (len(ids), len(files)))

    changed = {p.strip().replace("\\", "/") for p in files}
    for cid in ids:
        hit = [p for p in changed if p.endswith("/%s.md" % cid)]
        if not hit:
            fails.append("missing-card %s" % cid)
            continue
        body = git("show", "%s:%s" % (sha, hit[0])).stdout
        if not re.search(r"(?:^|\n)- %s 「" % re.escape(args.date), body):
            fails.append("no-ring-line %s@%s" % (cid, args.date))

    if fails:
        for f in fails:
            print("FAIL " + f)
        print("verdict: FAIL (%d)" % len(fails))
        return 1
    print("verdict: PASS (written=%d 全部落卡净增)" % len(ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
