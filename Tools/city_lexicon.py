# -*- coding: utf-8 -*-
"""城市语言志：把语言线（六轴句/像素灵/问候/问答/负面脸）汇总成一张只读单页。

确定性零 LLM：只读 cognition/pools.json、cognition/greetings.json、
cognition/pools-negative.json 三份正本，不改任何数据，输出
census/export/city-lexicon.html。门闸口径与 Tools/pool_audit.py 一致。
"""
from __future__ import annotations

import json
import html
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COG = ROOT / "cognition"
OUT = ROOT / "census" / "export" / "city-lexicon.html"

CTX_LABEL = {
    "morning": "清晨", "dusk": "傍晚", "night": "夜里", "weekend": "周末",
    "rain": "雨天", "typhoon": "台风", "heatwave": "暑热", "coldsnap": "寒潮",
    "market_open": "开市", "market_close": "收市", "ceo_order": "派单日",
    "festival": "节庆",
    "first_meet": "初见", "reunion": "重逢", "smalltalk": "闲聊", "farewell": "告别",
}
NEG_LABEL = {
    "anwen": "安稳", "shengji": "生计", "shejiao": "社交",
    "haoqi": "好奇", "sprite": "像素灵",
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load(name: str):
    with open(COG / name, encoding="utf-8") as f:
        return json.load(f)


def ctx_label(k: str) -> str:
    return CTX_LABEL.get(k, k)


def card(cls: str, title: str, depth: str, samples: list[str]) -> str:
    lines = "".join(f"<q>{esc(s)}</q>" for s in samples)
    return (f'<div class="card {cls}"><h4>{esc(title)}'
            f'<em>{esc(depth)}</em></h4>{lines}</div>')


def section(sid: str, title: str, lead: str, body: str, nav_title: str) -> tuple[str, str]:
    nav = f'<a href="#{sid}">{esc(nav_title)}<em>{""}</em></a>'
    sec = (f'<section class="sec" id="{sid}"><h2>{esc(title)}'
           f'<span class="meta">{esc(lead)}</span></h2>{body}</section>')
    return nav, sec


def gate_verdict() -> str:
    """跑一次 Tools/pool_audit.py，取真实 verdict（不自称 PASS）。"""
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(ROOT / "Tools" / "pool_audit.py")],
            capture_output=True, text=True, encoding="utf-8", timeout=180,
        )
        for line in (r.stdout or "").splitlines():
            if line.startswith("verdict:"):
                return line.split(":", 1)[1].strip() or "UNKNOWN"
    except Exception as e:  # 门闸跑不动时如实标注，不冒充通过
        return f"UNAVAILABLE({type(e).__name__})"
    return "UNKNOWN"


def main() -> int:
    pools = load("pools.json")
    greetings = load("greetings.json")
    negative = load("pools-negative.json")

    axes = pools["axes"]
    sprite = pools["sprite"]
    g_axes = greetings["greet"]["axes"]
    g_sprite = greetings["greet"]["sprite"]
    faq = greetings["faq"]
    neg = negative["negative"]
    recovering = negative["recovering"]

    n_axes = sum(len(v) for a in axes.values() for v in a.values())
    n_sprite = sum(len(v) for v in sprite.values())
    n_greet = sum(len(x) for a in g_axes.values() for x in a.values())
    n_greet_sprite = sum(len(x) for x in g_sprite.values())
    n_faq_pairs = sum(len(v) for v in faq.values())
    n_neg = sum(len(v) for v in neg.values())

    navs, secs = [], []

    # 一、六轴句：人物性格轴 × 十二情境
    body = []
    for axis, ctxs in axes.items():
        body.append(f'<h3 class="axis">{esc(axis)}<span class="meta">'
                    f'{len(ctxs)} 情境 · {sum(len(v) for v in ctxs.values())} 句</span></h3>')
        cards = []
        for ctx, lines in ctxs.items():
            cards.append(card("", ctx_label(ctx), f"{len(lines)}/18", lines))
        body.append('<div class="grid">' + "".join(cards) + "</div>")
    nav, sec = section("axes", "一、六轴句", f"{len(axes)} 轴 × {len(next(iter(axes.values())))} 情境 · 共 {n_axes} 句",
                       "".join(body), f"六轴句 {n_axes}")
    navs.append(nav); secs.append(sec)

    # 二、像素灵：城市情境声音
    cards = [card("sp", ctx_label(k), f"{len(v)}/12", v) for k, v in sprite.items()]
    nav, sec = section("sprite", "二、像素灵", f"{len(sprite)} 情境 · 共 {n_sprite} 句",
                       '<div class="grid">' + "".join(cards) + "</div>", f"像素灵 {n_sprite}")
    navs.append(nav); secs.append(sec)

    # 三、问候：人物 × 场合
    body = []
    for axis, ctxs in g_axes.items():
        body.append(f'<h3 class="axis">{esc(axis)}<span class="meta">'
                    f'{len(ctxs)} 场合 · {sum(len(v) for v in ctxs.values())} 句</span></h3>')
        cards = []
        for ctx, lines in ctxs.items():
            cards.append(card("", ctx_label(ctx), f"{len(lines)}/17", lines))
        body.append('<div class="grid">' + "".join(cards) + "</div>")
    cards = [card("", ctx_label(k), f"{len(v)}句", v) for k, v in g_sprite.items()]
    body.append('<h3 class="axis">像素灵<span class="meta">4 场合</span></h3>'
                '<div class="grid">' + "".join(cards) + "</div>")
    nav, sec = section("greet", "三、问候语", f"6 轴 × 4 场合 + 像素灵 4 场合 · 共 {n_greet + n_greet_sprite} 句",
                       "".join(body), f"问候 {n_greet + n_greet_sprite}")
    navs.append(nav); secs.append(sec)

    # 四、问答
    body = []
    for axis, pairs in faq.items():
        body.append(f'<h3 class="axis">{esc(axis)}<span class="meta">{len(pairs)} 对</span></h3>')
        rows = "".join(
            f'<div class="qa"><span class="q">{esc(p.get("q", ""))}</span>'
            f'<span class="a">{esc(p.get("a", ""))}</span></div>'
            for p in pairs
        )
        body.append(f'<div class="qabox">{rows}</div>')
    nav, sec = section("faq", "四、问答", f"{len(faq)} 组 · 共 {n_faq_pairs} 对",
                       "".join(body), f"问答 {n_faq_pairs}")
    navs.append(nav); secs.append(sec)

    # 五、负面脸与回转
    body = ['<div class="grid">']
    for k, lines in neg.items():
        body.append(card("neg", NEG_LABEL.get(k, k), f"{len(lines)}/8", lines))
    body.append("</div>")
    body.append('<h3 class="axis">回转句<span class="meta">'
                f'{len(recovering)} 句 · 负面情绪回收面</span></h3>')
    body.append('<div class="qabox">' + "".join(
        f'<div class="qa"><span class="a">{esc(x)}</span></div>' for x in recovering
    ) + "</div>")
    nav, sec = section("neg", "五、负面脸与回转", f"{len(neg)} 类 · {n_neg} 句 + 回转 {len(recovering)} 句",
                       "".join(body), f"负面 {n_neg}")
    navs.append(nav); secs.append(sec)

    total = n_axes + n_sprite + n_greet + n_greet_sprite + n_faq_pairs * 2 + n_neg + len(recovering)
    verdict = gate_verdict()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市语言志 · 硅基生命</title>
<style>
:root{{--bg:#0f1114;--fg:#e8e6e1;--dim:#8b8f96;--line:#232830;--acc:#c8a06a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.75 "Songti SC",Georgia,"Noto Serif SC",serif}}
header{{padding:28px 20px 12px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:22px;letter-spacing:.06em;font-weight:600}}
.sub{{color:var(--dim);font-size:13px}}
.kpi{{display:flex;gap:22px;flex-wrap:wrap;padding:14px 20px;border-bottom:1px solid var(--line)}}
.kpi div{{font-size:13px;color:var(--dim)}}
.kpi b{{display:block;font-size:20px;color:var(--fg);font-weight:600}}
.ok b{{color:#8fb37a}}
.search{{padding:12px 20px;border-bottom:1px solid var(--line)}}
input{{width:100%;max-width:420px;padding:8px 10px;background:#151a20;border:1px solid var(--line);
color:var(--fg);border-radius:4px;font:14px/1.4 inherit}}
.wrap{{display:grid;grid-template-columns:190px 1fr;align-items:start}}
nav{{position:sticky;top:0;max-height:100vh;overflow:auto;padding:14px 10px;border-right:1px solid var(--line)}}
nav a{{display:block;padding:5px 8px;color:var(--dim);text-decoration:none;
font:12px/1.5 ui-monospace,monospace;border-radius:3px}}
nav a:hover{{background:#161b22;color:var(--fg)}}
main{{padding:10px 26px 60px;max-width:1080px}}
.sec{{padding:20px 0;border-bottom:1px dashed var(--line)}}
.sec h2{{display:flex;justify-content:space-between;align-items:baseline;margin:0 0 14px;font-size:17px}}
.meta{{font-size:12px;color:var(--dim);font-weight:400}}
h3.axis{{margin:18px 0 8px;font-size:15px;color:var(--acc);font-weight:600;
display:flex;justify-content:space-between;align-items:baseline;border-left:3px solid var(--acc);padding-left:8px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px}}
.card{{background:#14181e;border:1px solid var(--line);border-radius:5px;padding:10px 12px}}
.card h4{{margin:0 0 6px;font-size:13px;display:flex;justify-content:space-between;
align-items:baseline;color:#cfcabf;font-weight:600}}
.card h4 em{{font-style:normal;font:11px/1 ui-monospace,monospace;color:#6a7078}}
.card q{{display:block;font-size:13.5px;color:#dedbd4;padding:3px 0;quotes:none;line-height:1.65}}
.card q::before,.card q::after{{content:""}}
.card.sp{{border-left:3px solid #5a7f9a}}
.card.neg{{border-left:3px solid #8a5a5a}}
.qabox{{border:1px solid var(--line);border-radius:5px;padding:6px 12px;background:#14181e}}
.qa{{display:grid;grid-template-columns:1fr 1.4fr;gap:14px;padding:6px 0;
border-bottom:1px dotted #1e242c;font-size:13.5px}}
.qa:last-child{{border-bottom:0}}
.q{{color:#cfcabf}}
.a{{color:#9aa0a6}}
.hide{{display:none}}
footer{{padding:18px 26px;color:#6a7078;font-size:12px;border-top:1px solid var(--line)}}
@media(max-width:760px){{.wrap{{grid-template-columns:1fr}}
nav{{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--line);
display:flex;flex-wrap:wrap;gap:4px}}nav a{{padding:2px 6px}}.qa{{grid-template-columns:1fr}}}}
</style></head><body>
<header><h1>城市语言志</h1>
<div class="sub">语言线正本汇总 · 六轴句 / 像素灵 / 问候 / 问答 / 负面脸 —— 确定性只读汇总，零 LLM · 生成 {now}</div></header>
<div class="kpi">
<div><b>{n_axes}</b>六轴句（{len(axes)} 轴 × 12 情境）</div>
<div><b>{n_sprite}</b>像素灵句（{len(sprite)} 情境）</div>
<div><b>{n_greet + n_greet_sprite}</b>问候句</div>
<div><b>{n_faq_pairs}</b>问答对</div>
<div><b>{n_neg}</b>负面脸句</div>
<div class="ok"><b>{esc(verdict)}</b>门闸（Tools/pool_audit.py 实跑 verdict）</div>
</div>
<div class="search"><input id="q" placeholder="按词检索：豆浆 / 台风 / 重逢 / 收摊…" autocomplete="off"></div>
<div class="wrap"><nav>{"".join(navs)}</nav><main>{"".join(secs)}</main></div>
<footer>本页由 Tools/city_lexicon.py 确定性生成，零 LLM；数据正本 cognition/pools.json ·
cognition/greetings.json · cognition/pools-negative.json（共 {total} 条语料）。改语料请改正本后重跑，
本页不含任何生成态文本。</footer>
<script>
(function(){{
 var q=document.getElementById('q'),cards=[].slice.call(document.querySelectorAll('.card,.qa'));
 function run(){{
  var k=q.value.trim().toLowerCase(),hit=0;
  cards.forEach(function(c){{
   var ok=!k||c.textContent.toLowerCase().indexOf(k)>=0;
   c.classList.toggle('hide',!ok); if(ok)hit++;
  }});
  document.title='城市语言志 · '+hit+' 条';
 }}
 q.addEventListener('input',run);
}})();
</script>
</body></html>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    print(f"city-lexicon: {OUT.relative_to(ROOT)}  {len(page.encode('utf-8'))/1024:.1f} KB")
    print(f"corpus: axes={n_axes} sprite={n_sprite} greet={n_greet + n_greet_sprite} "
          f"faq_pairs={n_faq_pairs} neg={n_neg} recovering={len(recovering)} total={total} "
          f"gate={verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())