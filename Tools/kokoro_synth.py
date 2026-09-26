#!/usr/bin/env python3
"""kokoro_synth.py - neural voice synthesis, third source (8 zh timbres).

Order O-20260926-0942-bm-c follow-up, task T-20260926-06 (kokoro multi-source),
CEO self-decision 2026-09-26 ("你自己科学决策"): the HF gated wall (voices-v1.0.bin
401) is NOT cracked - the public k2-fsa/sherpa-onnx release route is used instead
(Apache-2.0 Kokoro-82M v1.0 multi-lang ONNX bundle, GitHub release assets, 8 zh
base voices zf_*/zm_* + espeak-ng-data + dict). Local compute law: CPU inference,
zero cloud.

Per-citizen derivation stays deterministic (VOICE-POOL.md law):
  gender        -> voice pool (female/undefined -> zf_*, male -> zm_*)
  md5(id)       -> in-pool pick (same id = same timbre, forever)
  rate band     -> speed = 100/(100+rate)  (piper pilot law, length_scale)
Honored seats C-00001~03: blocked, never synthesized.
No pitch param on kokoro timbres - honest note: timbre difference replaces the
SAPI pitch-band modulation; speed modulation keeps the rate band.

Usage:
  python -X utf8 kokoro_synth.py --id C-00010 --text "..." [--engine fp32|int8] [--out DIR]
  python -X utf8 kokoro_synth.py --pilot [--engine fp32|int8]   (8 anchor A/B clips)
  python -X utf8 kokoro_synth.py --qc                            (no model needed)
"""
import argparse, datetime, hashlib, json, os, sys, wave

HERE = os.path.dirname(os.path.abspath(__file__))
CO = os.path.dirname(HERE)

KOKORO_DIR = os.environ.get("KOKORO_DIR", r"K:\Fluxgroup\.tools\kokoro")
BUNDLES = {"fp32": "kokoro-multi-lang-v1_0", "int8": "kokoro-int8-multi-lang-v1_0"}
VOICE_FILE = os.path.join(CO, "census", "export", "citizen-voice.jsonl")
PILOT_REF = os.path.join(CO, "census", "export", "voice-pilot-piper", "manifest.json")
PILOT_DIR = os.path.join(CO, "census", "export", "voice-pilot-kokoro")
HONORED = ("C-00001", "C-00002", "C-00003")

ZF = ["zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi"]
ZM = ["zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang"]
# Authoritative sid map, kokoro-multi-lang-v1_0 (53 speakers) - official table:
# https://k2-fsa.github.io/sherpa/onnx/tts/pretrained_models/kokoro.html
# 45->zf_xiaobei 46->zf_xiaoni 47->zf_xiaoxiao 48->zf_xiaoyi
# 49->zm_yunjian 50->zm_yunxi 51->zm_yunxia 52->zm_yunyang
SID_MAP = {"zf_xiaobei": 45, "zf_xiaoni": 46, "zf_xiaoxiao": 47, "zf_xiaoyi": 48,
           "zm_yunjian": 49, "zm_yunxi": 50, "zm_yunxia": 51, "zm_yunyang": 52}


def md5(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def voice_for(cid, gender):
    pool = ZF if gender in ("女", "female", "无定") else ZM
    return pool[int(md5(cid)[:2], 16) % len(pool)]


def speed_for(rate):
    return round(100.0 / (100.0 + rate), 3)


def load_row(cid):
    if not os.path.isfile(VOICE_FILE):
        sys.stderr.write("citizen-voice.jsonl missing - run Tools/voice_manifest.py first\n")
        sys.exit(2)
    with open(VOICE_FILE, encoding="utf-8") as f:
        for ln in f:
            if '"id":"%s"' % cid in ln or '"id": "%s"' % cid in ln:
                r = json.loads(ln)
                if r.get("id") == cid:
                    return r
    return None


def bundle_dir(engine):
    d = os.path.join(KOKORO_DIR, BUNDLES[engine])
    if not os.path.isdir(d):
        sys.stderr.write("bundle missing: %s - download sherpa-onnx release first\n" % d)
        sys.exit(2)
    model = None
    for cand in ("model.onnx", "model.int8.onnx"):
        if os.path.isfile(os.path.join(d, cand)):
            model = os.path.join(d, cand)
            break
    if not model:
        sys.stderr.write("no model.onnx under %s\n" % d)
        sys.exit(2)
    return d, model


def make_tts(engine):
    import sherpa_onnx
    d, model = bundle_dir(engine)
    # sherpa bundle ships voices.bin (single file, all 53 voices) - no HF
    # voices-v1.0.bin needed at all; lexicons are comma-joined (official docs)
    voices = os.path.join(d, "voices.bin")
    if not os.path.isfile(voices):
        sys.stderr.write("voices.bin missing under %s\n" % d)
        sys.exit(2)
    lex = ",".join(os.path.join(d, x) for x in ("lexicon-us-en.txt", "lexicon-zh.txt")
                   if os.path.isfile(os.path.join(d, x)))
    if not lex:
        sys.stderr.write("lexicons missing under %s\n" % d)
        sys.exit(2)
    fsts = ",".join(os.path.join(d, x) for x in ("date-zh.fst", "number-zh.fst")
                    if os.path.isfile(os.path.join(d, x)))
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=model,
                voices=voices,
                tokens=os.path.join(d, "tokens.txt"),
                data_dir=os.path.join(d, "espeak-ng-data"),
                lexicon=lex,
                dict_dir=os.path.join(d, "dict"),
            ),
            num_threads=4,
            debug=False,
            provider="cpu"),
        rule_fsts=fsts)
    return sherpa_onnx.OfflineTts(cfg)


def sid_of(tts, voice):
    sid = SID_MAP.get(voice)
    if sid is None or not (0 <= sid < tts.num_speakers):
        sys.stderr.write("sid mapping broken for %s\n" % voice)
        sys.exit(3)
    return sid


def synth(tts, cid, text, out_path, engine):
    row = load_row(cid)
    if not row:
        return {"id": cid, "error": "no citizen row"}
    if cid in HONORED or row.get("blocked"):
        return {"id": cid, "error": "honored seat blocked"}
    v = row["voice"]
    name = voice_for(cid, row.get("gender", "无定"))
    speed = speed_for(v.get("rate", 0))
    t0 = datetime.datetime.now()
    audio = tts.generate(text, sid=sid_of(tts, name), speed=speed)
    dt = (datetime.datetime.now() - t0).total_seconds()
    samples = audio.samples
    if not samples:
        return {"id": cid, "error": "empty samples"}
    import numpy as np
    pcm = (np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(audio.sample_rate)
        w.writeframes(pcm.tobytes())
    dur = len(samples) / float(audio.sample_rate)
    return {"id": cid, "name": row["name"], "gender": row.get("gender"),
            "text": text, "voice": name, "speed": speed, "engine": "kokoro-%s-%s" % (engine, name),
            "file": os.path.basename(out_path), "bytes": os.path.getsize(out_path),
            "dur_s": round(dur, 2), "gen_s": round(dt, 2), "sample_rate": audio.sample_rate, "v": 1}


def pilot(tts, engine, out_dir):
    if not os.path.isfile(PILOT_REF):
        sys.stderr.write("piper pilot manifest missing\n")
        sys.exit(2)
    with open(PILOT_REF, encoding="utf-8") as f:
        items = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    out = []
    for it in items:
        p = os.path.join(out_dir, it["id"] + ".wav")
        rec = synth(tts, it["id"], it["text"], p, engine)
        if rec.get("error"):
            print("%s SKIP: %s" % (it["id"], rec["error"]))
            continue
        out.append(rec)
        print("%s %s [%s speed=%s] %.2fs -> %s (%dB, gen %.1fs)" % (
            it["id"], rec["name"], rec["voice"], rec["speed"], rec["dur_s"],
            rec["file"], rec["bytes"], rec["gen_s"]))
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return out


def qc():
    fails = []
    # pool mapping law
    if voice_for("C-00010", "女") not in ZF:
        fails.append("zf-pool-female")
    if voice_for("C-00011", "男") not in ZM:
        fails.append("zm-pool-male")
    if voice_for("C-00017", "无定") not in ZF:
        fails.append("zf-pool-undefined")
    # determinism: same id -> same timbre forever, double-run equal
    if voice_for("C-00013", "男") != voice_for("C-00013", "男"):
        fails.append("voice-determinism")
    # 8 anchors must cover all 8 zh timbres? no law - but distinct ids may collide;
    # determinism + pool law is the contract. sanity: anchors spread over pools
    got = {voice_for(i, g) for i, g in
           [("C-00010", "女"), ("C-00015", "女"), ("C-00028", "女"),
            ("C-00011", "男"), ("C-00013", "男"), ("C-00019", "男")]}
    if not (got & set(ZF)) or not (got & set(ZM)):
        fails.append("anchor-pool-coverage")
    # speed law (piper pilot law)
    if speed_for(-14) != 1.163 or speed_for(0) != 1.0 or speed_for(20) != 0.833:
        fails.append("speed-law")
    # authoritative sid map: bijective over 45..52 for the 8 zh timbres
    if sorted(SID_MAP.values()) != list(range(45, 53)) or set(SID_MAP) != set(ZF + ZM):
        fails.append("sid-map")
    # honored seats never synthesize - enforced in synth(); qc covers the guard data
    if HONORED != ("C-00001", "C-00002", "C-00003"):
        fails.append("honored-roster")
    if fails:
        print("QC FAIL: " + "; ".join(fails))
        return 1
    print("QC PASS (pool law/determinism/speed law/sid map/honored guard)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--engine", default="fp32", choices=["fp32", "int8"])
    ap.add_argument("--out", default="")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--qc", action="store_true")
    a = ap.parse_args()
    if a.qc:
        sys.exit(qc())
    if a.pilot:
        out_dir = a.out or PILOT_DIR + ("-int8" if a.engine == "int8" else "")
        pilot(make_tts(a.engine), a.engine, out_dir)
        return
    if not a.id or not a.text:
        print("need --id and --text")
        sys.exit(2)
    out_dir = a.out or os.path.join(CO, "census", "export", "voice-kokoro-cache")
    os.makedirs(out_dir, exist_ok=True)
    rec = synth(make_tts(a.engine), a.id, a.text,
                os.path.join(out_dir, "%s.wav" % a.id), a.engine)
    print(json.dumps(rec, ensure_ascii=False))
    if rec.get("error"):
        sys.exit(3)


if __name__ == "__main__":
    main()
