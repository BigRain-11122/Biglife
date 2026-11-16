"""T-20261115-04 换靶线回归：12h 全城开口配额（零 LLM·temp 文件·不写仓）。

判据=rc 0。四类正负控：
  正控 · 重复类闸记过的开口12 进入禁牌集（两族各一）
  负控 · anchor/引号类拒稿不参与禁牌（与开口重复无关，禁了就是误伤）
  负控 · 超 12h 窗口的记录不参与（TTL 到期即解禁）
  正控 · 生成面命中禁牌开口12 → citywide-refusal-ban
  负控 · own-catchphrase 豁免（本卡自身声口照旧放行）+ 干净句零误伤 +
         sig 缺 refusal_bans（meet/reflect 面）零漂移
"""
import datetime
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "Tools"))
import evolve_citizen as E  # noqa: E402

NOW = datetime.datetime.now()
TS_NOW = NOW.strftime("%Y-%m-%d %H:%M:%S")
TS_OLD = (NOW - datetime.timedelta(hours=14)).strftime("%Y-%m-%d %H:%M:%S")

ROWS = [
    {"ts": TS_NOW, "cid": "C-90001",
     "gate": ["recent-dup-phrase", "recent-family-opening"],
     "opening12": "这会儿手边最碍事的就是这"},
    {"ts": TS_NOW, "cid": "C-90002", "gate": ["opening-family-quota"],
     "opening12": "风把塑料布吹得啪啦响，我"},
    {"ts": TS_NOW, "cid": "C-90003", "gate": ["anchor-law"],
     "opening12": "天上压着雨云的边角下"},
    {"ts": TS_OLD, "cid": "C-90004", "gate": ["recent-dup-phrase"],
     "opening12": "桌角那点零碎又该理一理了"},
    {"ts": TS_NOW, "cid": "C-90005", "gate": ["citywide-refusal-ban"],
     "opening12": "刚才那句被换掉的短开"},
    # 作帐面不剥引号、生成面剥引号——带「」的键必须仍能命中（静默失效守卫）
    {"ts": TS_NOW, "cid": "C-90006", "gate": ["recent-dup-phrase"],
     "opening12": "「门槛上的泥印子还"},
]

BANNED_A = "这会儿手边最碍事的就是这"
BANNED_B = "风把塑料布吹得啪啦响，我"
ANCHOR_ONLY = "天上压着雨云的边角下"
STALE = "桌角那点零碎又该理一理了"
SELF_ONLY = "刚才那句被换掉的短开"

BANNED_LINE = "这会儿手边最碍事的就是这根旧弦，我把它往边儿上一搁。"
ANCHOR_LINE = "天上压着雨云的边角下，我收了晾在绳上的衣裳。"
CLEAN_LINE = "灶台边那口铁锅又泛了层白霜，我拿布擦了擦。"

fails = []


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        fails.append(name)


def main():
    path = os.path.join(tempfile.gettempdir(), "bl-citywide-ban-test.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for row in ROWS:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    bans = E.recent_refusal_bans(path=path)
    check("ban-recent-dup-phrase", BANNED_A in bans)
    check("ban-opening-family-quota", BANNED_B in bans)
    check("neg-anchor-gate-not-banned", ANCHOR_ONLY not in bans)
    check("neg-stale-14h-not-banned", STALE not in bans)
    # 禁牌面自身不入禁牌集（否则 12h TTL 会被自我延长）
    check("neg-self-gate-not-banned", SELF_ONLY not in bans)

    sig = {"cid": "C-90009", "refusal_bans": bans, "card_text": ""}
    check("gate-flags-banned-opening",
          "citywide-refusal-ban" in E.ring_violations(BANNED_LINE, sig))
    check("gate-not-flag-anchor-opened-line",
          "citywide-refusal-ban" not in E.ring_violations(ANCHOR_LINE, sig))
    check("gate-not-flag-clean-line",
          "citywide-refusal-ban" not in E.ring_violations(CLEAN_LINE, sig))

    own = {"cid": "C-90009", "refusal_bans": bans, "card_text": BANNED_A}
    check("neg-own-catchphrase-exempt",
          "citywide-refusal-ban" not in E.ring_violations(BANNED_LINE, own))

    check("neg-absent-sig-zero-drift",
          E.ring_violations(CLEAN_LINE, {"cid": "C-1"}) == [])
    check("gate-flags-quoted-key-variant",
          "citywide-refusal-ban" in E.ring_violations(
              "「门槛上的泥印子还没干，我拿袖子蹭了蹭。", sig))

    # 空/缺失作帐文件不抛错
    check("neg-missing-log-empty",
          E.recent_refusal_bans(path=os.path.join(tempfile.gettempdir(),
                                                  "bl-no-such-log.jsonl")) == {})
    try:
        os.remove(path)
    except OSError:
        pass

    print("verdict:", "PASS" if not fails else "FAIL " + ",".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
