# -*- coding: utf-8 -*-
"""城市声音馆生成器（确定性·零 LLM·幂等）。

读 census/export/voice-samples|voice-pilot-kokoro|voice-pilot-kokoro-int8 三份
manifest.json + citizens-light.jsonl，产出 census/export/city-voices.html：
八位试点居民的三种合成档对照（可离线试听 / 体积与时长对照 / 引擎参数）。

公开面口径（census/export/PUBLIC-WHITELIST.md）：只用 name / species /
profession / district / creed 等公面字段；试音文本=creed + 自称句，不含
recent_ring / hook 深水面。

用法: python -X utf8 Tools/build_city_voices.py
"""
import datetime
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "census", "export")
LIGHT = os.path.join(EXP, "citizens-light.jsonl")
OUT = os.path.join(EXP, "city-voices.html")

# (子目录, 短名, 说明)
TRACKS = [
    ("voice-samples", "参数档", "pitch / rate / vol 参数微调"),
    ("voice-pilot-kokoro", "Kokoro fp32", "kokoro-fp32 内置音色"),
    ("voice-pilot-kokoro-int8", "Kokoro int8", "同一音色 int8 量化档"),
]
SPECIES_CN = {"carbon": "碳基", "silicon": "硅基", "sprite": "灵体"}


def load_jsonl(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                rows[d["id"]] = d
    return rows


def load_manifest(sub):
    path = os.path.join(EXP, sub, "manifest.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def kb(n):
    return "%.0f KB" % (n / 1024.0) if n >= 1024 else "%d B" % n


def card(k, v, n=""):
    return (
        '<div class="card"><div class="k">%s</div><div class="v">%s</div>'
        '<div class="n">%s</div></div>' % (html.escape(k), html.escape(str(v)), html.escape(n))
    )


def bar(name, cnt, total, unit=""):
    pct = (cnt / total * 100) if total else 0
    return (
        '<div class="row"><span class="lab">%s</span>'
        '<span class="track"><i style="width:%.1f%%"></i></span>'
        '<span class="num">%s%s · %.0f%%</span></div>'
        % (html.escape(name), pct, cnt, unit, pct)
    )


def main():
    citizens = load_jsonl(LIGHT)
    tracks = []
    for sub, label, note in TRACKS:
        man = load_manifest(sub)
        if man:
            tracks.append((sub, label, note, {e["id"]: e for e in man}))

    ids = sorted({i for _, _, _, m in tracks for i in m})
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    total_bytes = sum(e.get("bytes", 0) for _, _, _, m in tracks for e in m.values())
    total_dur = sum(e.get("dur_s", 0) for _, _, _, m in tracks for e in m.values())

    # 引擎侧对照：同 id 在 fp32 / int8 两档的体积与时长
    fp32 = dict((tracks[1][3]) if len(tracks) > 1 else {})
    int8 = dict((tracks[2][3]) if len(tracks) > 2 else {})
    cmp_rows = []
    ratios = []
    for cid in sorted(set(fp32) & set(int8)):
        a, b = fp32[cid], int8[cid]
        if not a.get("bytes") or not b.get("bytes"):
            continue
        ratio = b["bytes"] / a["bytes"]
        ratios.append(ratio)
        dd = abs(b.get("dur_s", 0) - a.get("dur_s", 0))
        cmp_rows.append(
            "<li><b>%s · %s</b><span class=\"d\">%s / %s</span>"
            "<span class=\"x\">%.0f%% 体积 · 时长差 %.2fs · 实时倍率 %.2fx / %.2fx</span></li>"
            % (
                cid,
                html.escape(str(a.get("name", ""))),
                kb(a["bytes"]),
                kb(b["bytes"]),
                ratio * 100,
                dd,
                (a.get("gen_s") or 0) / (a.get("dur_s") or 1),
                (b.get("gen_s") or 0) / (b.get("dur_s") or 1),
            )
        )
    mean_ratio = sum(ratios) / len(ratios) if ratios else 0

    voice_names = []
    for e in fp32.values():
        v = e.get("voice")
        if v and v not in voice_names:
            voice_names.append(v)

    # 逐人卡
    blocks = []
    for cid in ids:
        c = citizens.get(cid, {})
        sp = SPECIES_CN.get(c.get("species", ""), c.get("species", ""))
        head = "%s · %s · %s · %s" % (
            cid,
            c.get("name", "?"),
            sp,
            c.get("profession", "?"),
        )
        sub = "%s / %s　·　信条：%s" % (
            c.get("district", "?"),
            c.get("block", "?"),
            c.get("creed", ""),
        )
        players = []
        for _, label, note, man in tracks:
            e = man.get(cid)
            if not e:
                players.append(
                    '<div class="trk"><span class="tag">%s</span>'
                    '<span class="miss">无样本</span></div>' % html.escape(label)
                )
                continue
            detail = []
            if "voice" in e:
                detail.append("音色 %s · 语速 %.2f" % (e["voice"], e.get("speed", 1.0)))
            if "pitch" in e:
                detail.append("pitch %+d / rate %+d / vol %d" % (e["pitch"], e["rate"], e["vol"]))
            if "dur_s" in e:
                detail.append("时长 %.2fs · 生成 %.2fs" % (e["dur_s"], e.get("gen_s", 0)))
            players.append(
                '<div class="trk"><span class="tag">%s</span>'
                '<audio controls preload="none" src="%s/%s"></audio>'
                '<span class="meta">%s · %s</span>'
                '<div class="det">%s</div></div>'
                % (
                    html.escape(label),
                    html.escape(_),
                    html.escape(e.get("file", "")),
                    kb(e.get("bytes", 0)),
                    html.escape(e.get("engine", note)),
                    html.escape(" · ".join(detail)),
                )
            )
        blocks.append(
            '<div class="vcard"><h3>%s</h3><div class="sub">%s</div>'
            '<div class="say">“%s”</div>%s</div>'
            % (
                html.escape(head),
                html.escape(sub),
                html.escape(next((man.get(cid, {}).get("text", "") for _, _, _, man in tracks if cid in man), "")),
                "".join(players),
            )
        )

    sw = sum(e.get("bytes", 0) for _, label, _, m in tracks if label == "参数档" for e in m.values())
    kw = sum(e.get("bytes", 0) for _, label, _, m in tracks if label == "Kokoro fp32" for e in m.values())
    iw = sum(e.get("bytes", 0) for _, label, _, m in tracks if label == "Kokoro int8" for e in m.values())

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市声音馆 · 硅基城市</title>
<style>
:root{{--bg:#0f1216;--fg:#e8ecf1;--dim:#8b97a6;--line:#232a33;--acc:#6fb3ff;--warn:#e0a45e}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.65 "Microsoft YaHei",system-ui,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-size:26px;margin:0 0 6px}}
.sub{{color:var(--dim);font-size:13px;margin-bottom:22px}}
h2{{font-size:17px;margin:34px 0 12px;padding-bottom:8px;border-bottom:1px solid var(--line)}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
.card{{background:#151a21;border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.card .k{{color:var(--dim);font-size:12px}}
.card .v{{font-size:24px;font-weight:600;margin:4px 0 2px}}
.card .n{{color:var(--dim);font-size:12px}}
.vcard{{background:#151a21;border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}}
.vcard h3{{margin:0 0 4px;font-size:15px}}
.vcard .sub{{margin:0 0 10px}}
.say{{color:#cfd9e4;font-size:14px;margin:0 0 12px;padding-left:10px;border-left:2px solid var(--acc)}}
.trk{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:7px 0;border-top:1px solid #1b222b}}
.trk:first-of-type{{border-top:0}}
.tag{{width:104px;flex:none;font-size:12px;color:#9fb0c2;font-variant-numeric:tabular-nums}}
audio{{height:34px;flex:1;min-width:220px;filter:invert(.9) hue-rotate(180deg)}}
.meta,.miss{{color:var(--dim);font-size:12px;flex:none}}
.det{{flex-basis:100%;color:#7d8a99;font-size:12px;padding-left:114px}}
.row{{display:flex;align-items:center;gap:10px;margin:6px 0}}
.lab{{width:150px;flex:none;color:#c9d4e0;font-size:13px}}
.track{{flex:1;height:8px;background:#1c232c;border-radius:5px;overflow:hidden}}
.track i{{display:block;height:100%;background:linear-gradient(90deg,#4a86c8,#6fb3ff)}}
.num{{width:120px;flex:none;text-align:right;color:var(--dim);font-size:12px;font-variant-numeric:tabular-nums}}
ul{{margin:0;padding-left:0;list-style:none}}
li{{display:flex;gap:12px;padding:6px 0;border-top:1px solid #1b222b;font-size:13px;flex-wrap:wrap}}
li:first-child{{border-top:0}}
li b{{width:230px;flex:none;font-weight:500}}
li .d{{width:150px;flex:none;color:var(--dim);font-variant-numeric:tabular-nums}}
li .x{{color:#a9b6c4}}
.note{{background:#1a1712;border:1px solid #3a3020;border-radius:10px;padding:14px 16px;color:#c9bb9f;font-size:13px}}
.note b{{color:var(--warn)}}
.foot{{margin-top:40px;color:#5f6b7a;font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>城市声音馆</h1>
<div class="sub">八位试点居民 · 三档合成对照（可试听） · 生成 {now} · 数据源 census/export/voice-* manifest.json</div>

<div class="cards">
{card("试点席位", len(ids), "全城 %d 人中的选样" % len(citizens))}
{card("合成档", len(tracks), " / ".join(t[1] for t in tracks))}
{card("样本总量", kb(total_bytes), "三档合计 %d 条" % sum(len(m) for _, _, _, m in tracks))}
{card("可听总时长", "%.1fs" % total_dur, "含量化档重复计时")}
</div>

<h2>一 · 试听</h2>
{''.join(blocks)}

<h2>二 · 档位体积对照</h2>
{bar("参数档", sw, total_bytes, "B")}
{bar("Kokoro fp32", kw, total_bytes, "B")}
{bar("Kokoro int8", iw, total_bytes, "B")}
<div class="sub" style="margin-top:10px">int8 / fp32 平均体积比 {mean_ratio * 100:.0f}%（同文本同音色）· 音色清单：{html.escape(" / ".join(voice_names))}</div>

<h2>三 · 逐条量化对照</h2>
<ul>
{''.join(cmp_rows) if cmp_rows else '<li><span class="x">无可用对照行</span></li>'}
</ul>

<h2>四 · 读法说明</h2>
<div class="note">
<p><b>这不是声纹克隆。</b>音色全部取自引擎内置说话人（zf_xiaoxiao / zm_yunjian 等），
文本=居民自己的信条句 + 自称句，不含一个人的真实录音，也不含年轮/钩子等深水面内容。</p>
<p><b>样本是选样试点，不是全量。</b>全城 {len(citizens)} 位居民中仅 {len(ids)} 位有试音，
按物种覆盖 {len({citizens.get(i, {}).get('species') for i in ids})} / 3 类；其余居民的声音面尚未开工。</p>
<p><b>听感判断留给人耳。</b>本页只做档位与体积对照，不做「像不像这个人」的自动评分；
参数档与 Kokoro 档的优劣由听者自己定。</p>
</div>

<div class="foot">本页由 Tools/build_city_voices.py 扫描三份 manifest.json 生成（确定性·零 LLM·幂等）· 音频文件位于 census/export/voice-*/</div>
</div></body></html>
"""
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print("wrote %s (%d ids, %d tracks, %.0f KB)" % (OUT, len(ids), len(tracks), len(page.encode("utf-8")) / 1024))


if __name__ == "__main__":
    main()