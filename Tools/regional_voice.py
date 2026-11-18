# -*- coding: utf-8 -*-
"""来处与说话方式：给每个居民一个稳定的地域底子 + 语言习惯锚。

Why（CEO 2026-11-18「每个人的个性要更强，各地的人都有」）：
  现有档案的人设很足（性格三条带解释 / 信条 / 思想 / 语言含底色词+行话+口头禅+语气），
  但实测 1750 条里口头禅出现率极低，句子全是"我把手边的X挪了挪"这种通用叙述——
  素材在，没用上。地域更是完全没有，整座城读起来像同一条弄堂。

本模块做两件事：
  1) 按 cid 的稳定 md5 分配「来处」（8 个地域带，不随机漂移，同一人永远同一处）
  2) 给出该地域的说话特征（词尾、语气、称呼习惯），供 prompt 注入

设计纪律：
  - 只给"语言底子"，不给刻板印象剧情（不写"东北人都爱喝酒"这类）
  - 迁移到城里 N 年，口音会被同化一点 —— 提示词里明确"别刻意模仿"
  - 与派系（弄堂派/新市民派）不冲突：弄堂派更多留江南底，新市民派更多外来底

用法：
  python -X utf8 Tools/regional_voice.py --id C-01222
  python -X utf8 Tools/regional_voice.py --stats
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)
LIGHT = os.path.join(CO, "census", "export", "citizens-light.jsonl")

# (地区, 底色词 3-4 个, 说话特征, 生活底子一句)
REGIONS = [
    ("东北", ["整", "干啥", "贼", "老鼻子"],
     "话直、句短、尾音往上挑，爱用「整」「干啥」这类动词开路的说法",
     "冬天屋里暖气烧得足，说话嗓门大是因为隔着屋子喊惯了"),
    ("西北", ["嘛", "咋", "美得很", "嫽"],
     "慢条斯理，爱把话说圆，常用「嘛」收尾",
     "面食做得好，一顿饭能磨蹭一个钟头"),
    ("西南", ["要得", "巴适", "搞啥子", "安逸"],
     "尾音拖长，句子里爱插「嘛」「哦」，听着松快",
     "爱坐街边，一壶茶能坐一下午"),
    ("岭南", ["唔该", "得唔得", "搞掂", "好耐"],
     "句子短促，语尾干脆，偶尔漏出一两个粤语词",
     "煲汤是正经事，火要小、时间要够"),
    ("闽台", ["有影", "真赞", "啦", "歹势"],
     "说话软，句尾常带「啦」，客气话多",
     "爱泡茶，一杯一杯地续"),
    ("中原", ["中", "得劲", "恁", "扎实"],
     "稳当，爱说「中」表示应下，句子不慌不忙",
     "讲究实在，东西好不好上手一摸就知道"),
    ("江南", ["一眼眼", "毛毛雨", "覅", "适意"],
     "软糯，尾音轻，话里常带「一眼眼」这类小词",
     "过日子精细，一碗面也要讲究浇头"),
    ("北方", ["您", "甭", "得嘞", "瓷实"],
     "干脆，客气话用「您」，不啰嗦",
     "做事讲究利索，不喜欢拖泥带水"),
]


def region_of(cid, faction=None):
    """稳定分配：同一 cid 永远同一地区。弄堂派略偏江南，新市民派偏外来。"""
    h = hashlib.md5(("region|%s" % cid).encode("utf-8")).hexdigest()
    n = int(h[:8], 16)
    # 弄堂派：江南权重更高（老城底子）；新市民派：外来七区均分
    if faction and "弄堂" in str(faction):
        if n % 10 < 4:            # 40% 江南
            return REGIONS[6]
        return REGIONS[n % 7 if n % 7 < 6 else 0]
    idx = n % len(REGIONS)
    return REGIONS[idx]


def years_in_city(cid):
    """来城年数（稳定 1-30 年），让「口音被同化一点」有依据。"""
    h = hashlib.md5(("years|%s" % cid).encode("utf-8")).hexdigest()
    return 1 + int(h[:4], 16) % 30


def block_for_prompt(cid, faction=None):
    """返回可直接拼进 prompt 的一段（自然、不刻板）。"""
    name, words, voice, life = region_of(cid, faction)
    yrs = years_in_city(cid)
    w = "、".join("「%s」" % x for x in words[:3])
    return (
        "【你的来处·说话底子】你从%s来，在这城里住了 %d 年。说话带着那儿的底子：%s；%s。"
        "底子只在顺口时自然带出来——住了这么多年，早被城里的日子磨圆了，别刻意学口音、"
        "别把方言当口头禅反复念，也别拿它当身份标签。%s。\n"
        % (name, yrs, voice, w, life))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if a.id:
        print("cid=%s" % a.id)
        print(block_for_prompt(a.id))
        return 0
    if a.stats:
        names = {}
        try:
            with open(LIGHT, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        o = json.loads(line)
                        names[o.get("id")] = o.get("faction")
                    except ValueError:
                        continue
        except OSError:
            pass
        cnt = collections.Counter()
        for cid, fac in names.items():
            cnt[region_of(cid, fac)[0]] += 1
        print("居民 %d 人，来处分布：" % len(names))
        for k, v in cnt.most_common():
            print("  %-4s %5d  (%4.1f%%)" % (k, v, 100.0 * v / max(1, len(names))))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
