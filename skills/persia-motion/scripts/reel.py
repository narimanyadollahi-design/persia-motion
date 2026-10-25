#!/usr/bin/env python
"""Persian product reel engine.

python reel.py <project_dir> [--engine edge|eleven] [--voice ID] [--model ID]
                             [--steps tts,render,mix,qc] [--probe]

<project_dir> contains project.json (+ optional brand.json, fonts/). Output: <project_dir>/out/reel.mp4
Run with:  python -X utf8 reel.py ...   (Windows console safe)
"""
import argparse, asyncio, base64, json, pathlib, subprocess, sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
GAP, LEAD, TAIL, FPS = 0.4, 0.5, 2.7, 30


def load_project(pd):
    pj = json.load(open(pd / "project.json", encoding="utf8"))
    bf = pd / "brand.json"
    brand = json.load(open(bf if bf.exists() else SKILL / "brand" / "brand.json", encoding="utf8"))
    pj["brand"] = {**brand, **pj.get("brand", {})}
    return pj


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


# ---------------------------------------------------------------- TTS
def tts_edge(pj, pd, voice, out):
    import edge_tts
    voice = voice or "fa-IR-FaridNeural"

    async def one(i, text):
        c = edge_tts.Communicate(text, voice, boundary="WordBoundary")
        words, path = [], out / f"s{i}.mp3"
        with open(path, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio": f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    words.append({"w": ch["text"], "s": ch["offset"] / 1e7, "e": (ch["offset"] + ch["duration"]) / 1e7})
        return {"text": text, "file": str(path), "dur": dur(path), "words": words}

    async def main(): return [await one(i, t) for i, t in enumerate(pj["lines"])]
    return asyncio.run(main())


def tts_eleven(pj, pd, voice, model, out):
    # key is read from <project>/.env.local (never printed, never stored in code)
    from dotenv import load_dotenv
    for p in (pd / ".env.local", pd.parent / ".env.local", pathlib.Path.cwd() / ".env.local"):
        if p.exists(): load_dotenv(p); break
    from elevenlabs import ElevenLabs, VoiceSettings
    c = ElevenLabs()
    voice = voice or pj.get("voice", {}).get("eleven_voice", "onwK4e9ZLuTAKqWW03F9")  # Daniel: premade, works on free plan
    model = model or pj.get("voice", {}).get("eleven_model", "eleven_v4")
    res = []
    for i, text in enumerate(pj["lines"]):
        r = c.text_to_speech.convert_with_timestamps(
            voice_id=voice, text=text, model_id=model, language_code="fa", output_format="mp3_44100_128",
            voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.8))
        path = out / f"s{i}.mp3"; path.write_bytes(base64.b64decode(r.audio_base_64))
        a = r.alignment or r.normalized_alignment
        words, cur, s0, e0 = [], "", None, None
        for ch, s, e in zip(a.characters, a.character_start_times_seconds, a.character_end_times_seconds):
            if ch.isspace():
                if cur: words.append({"w": cur, "s": s0, "e": e0}); cur, s0 = "", None
                continue
            if s0 is None: s0 = s
            cur += ch; e0 = e
        if cur: words.append({"w": cur, "s": s0, "e": e0})
        res.append({"text": text, "file": str(path), "dur": dur(path), "words": words})
    return res


def step_tts(pj, pd, a):
    out = pd / "audio"; out.mkdir(exist_ok=True)
    t = tts_eleven(pj, pd, a.voice, a.model, out) if a.engine == "eleven" else tts_edge(pj, pd, a.voice, out)
    json.dump(t, open(pd / "timing.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print("tts ok:", [round(x["dur"], 2) for x in t])


# ---------------------------------------------------------------- render
def build_html(pj, pd):
    tim = json.load(open(pd / "timing.json", encoding="utf8"))
    html = (SKILL / "template" / "index.html").read_text(encoding="utf8")
    fonts = pj["brand"].get("fonts", {"regular": "Vazirmatn-Regular.ttf", "bold": "Vazirmatn-Bold.ttf"})
    fdir = pd / "fonts"
    if not fdir.exists(): fdir = SKILL / "fonts"
    css = (f"@font-face{{font-family:V;src:url({(fdir / fonts['regular']).as_uri()});font-weight:400}}"
           f"@font-face{{font-family:V;src:url({(fdir / fonts['bold']).as_uri()});font-weight:800}}")
    html = (html.replace("/*FONTS*/", css)
                .replace("/*TIMING*/null", json.dumps(tim, ensure_ascii=False))
                .replace("/*PROJECT*/null", json.dumps(pj, ensure_ascii=False)))
    (pd / "_built.html").write_text(html, encoding="utf8")
    return pd / "_built.html"


def step_render(pj, pd, a):
    from playwright.sync_api import sync_playwright
    built = build_html(pj, pd); out = pd / "out"; out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 720, "height": 1280}, device_scale_factor=1.5)
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(built.as_uri()); pg.wait_for_function("window.READY===true", timeout=20000)
        D, cs, sfx = (pg.evaluate(f"window.{k}") for k in ("DUR", "CSTART", "SFX"))
        json.dump({"dur": D, "cstart": cs, "sfx": sfx}, open(pd / "meta.json", "w"))
        if a.probe:   # two mid-scene stills per scene for review
            pr = pd / "probe"; pr.mkdir(exist_ok=True)
            for i, t in enumerate(cs):
                for off in (1.2, 2.8):
                    pg.evaluate(f"seek({min(t + off, D - .05)})"); pg.screenshot(path=str(pr / f"s{i}_{off}.png"))
            print("probe frames ->", pr)
        else:
            n = int(D * FPS)
            ff = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                                   "-vf", "scale=1080:1920", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                                   "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(out / "silent.mp4")],
                                  stdin=subprocess.PIPE)
            for f in range(n):
                pg.evaluate(f"seek({f / FPS})"); ff.stdin.write(pg.screenshot(type="jpeg", quality=95))
            ff.stdin.close(); ff.wait()
        if errs: print("PAGE ERRORS:", errs)
        b.close()
    print("render ok")


# ---------------------------------------------------------------- mix
def step_mix(pj, pd, a):
    tim = json.load(open(pd / "timing.json", encoding="utf8")); meta = json.load(open(pd / "meta.json"))
    D = meta["dur"]; out = pd / "out"
    starts, t = [], LEAD
    for l in tim: starts.append(t); t += l["dur"] + GAP
    inp, ch, lab, n = [], [], [], 0
    for i, l in enumerate(tim):
        ms = int(starts[i] * 1000); inp += ["-i", l["file"]]
        ch.append(f"[{n}:a]aresample=48000,volume=1.6,adelay={ms}|{ms}[v{i}]"); lab.append(f"[v{i}]"); n += 1
    for j, e in enumerate(meta["sfx"]):
        ms = max(0, int(e["t"] * 1000))
        if e["k"] == "whoosh":
            inp += ["-f", "lavfi", "-t", "0.5", "-i", "anoisesrc=d=0.5:c=pink:r=48000:a=0.5"]
            ch.append(f"[{n}:a]highpass=f=500,lowpass=f=5000,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.3,volume=0.35,adelay={ms}|{ms}[x{j}]")
        else:
            inp += ["-f", "lavfi", "-t", "0.08", "-i", "sine=f=1400:d=0.08:r=48000"]
            ch.append(f"[{n}:a]afade=t=out:st=0.01:d=0.07,volume=0.45,adelay={ms}|{ms}[x{j}]")
        lab.append(f"[x{j}]"); n += 1
    inp += ["-f", "lavfi", "-t", str(D), "-i", f"sine=f=110:d={D}:r=48000", "-f", "lavfi", "-t", str(D), "-i", f"sine=f=165:d={D}:r=48000"]
    ch.append(f"[{n}:a][{n+1}:a]amix=inputs=2:normalize=0,volume=0.05,tremolo=f=0.2:d=0.4,afade=t=in:d=1.5,afade=t=out:st={D-2}:d=2[pad]"); lab.append("[pad]")
    ch.append("".join(lab) + f"amix=inputs={len(lab)}:normalize=0:dropout_transition=0,alimiter=limit=0.9,apad,atrim=0:{D}[out]")
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", *inp, "-filter_complex", ";".join(ch), "-map", "[out]", "-ar", "48000", "-ac", "2", str(out / "audio_mix.wav")])
    subprocess.check_call(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(out / "silent.mp4"), "-i", str(out / "audio_mix.wav"),
                           "-af", "loudnorm=I=-14:TP=-1.5:LRA=7", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                           "-shortest", "-movflags", "+faststart", str(out / "reel.mp4")])
    print("mix ok ->", out / "reel.mp4")


# ---------------------------------------------------------------- QC
QC_JS = """(T)=>{seek(T);const out=[];
const vis=[...document.querySelectorAll('.sc')].filter(e=>getComputedStyle(e).display!=='none');const sc=vis[vis.length-1];
sc.querySelectorAll('.hl .w,.chip,#nm2,#d7,#ty6,.sub span,.bar span,#want,text').forEach(el=>{
 if(+getComputedStyle(el).opacity<.5||!el.textContent.trim())return;
 const r=el.getBoundingClientRect(); if(r.width<2||r.right<0||r.left>720)return;
 const top=document.elementsFromPoint(r.left+r.width/2,r.top+r.height/2)[0];
 if(top&&!(el===top||el.contains(top)||top.contains(el))) out.push([el.textContent.trim().slice(0,14),String(top.getAttribute('class')||top.tagName)]);
 const rg=document.createRange();rg.selectNodeContents(el);const tr=rg.getBoundingClientRect();
 if(tr.width>1&&(tr.left<8||tr.right>712)) out.push([el.textContent.trim().slice(0,14),'CLIPPED_AT_EDGE']);});return out}"""


def step_qc(pj, pd, a):
    from playwright.sync_api import sync_playwright
    bad = {}
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome"); pg = b.new_page(viewport={"width": 720, "height": 1280})
        pg.goto((pd / "_built.html").as_uri()); pg.wait_for_function("window.READY===true")
        D = pg.evaluate("window.DUR"); t = 0.0
        while t < D:
            for o in pg.evaluate(QC_JS, t): bad.setdefault(tuple(o), []).append(round(t, 2))
            t += 0.1
        b.close()
    real = {k: v for k, v in bad.items() if len(v) > 1}     # single-sample hits = iris-wipe transition frames
    for k, v in real.items(): print("QC FAIL", k, f"{v[0]}s-{v[-1]}s")
    print("qc:", "PASS" if not real else f"{len(real)} issue(s)")
    return not real


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--engine", default="edge", choices=["edge", "eleven"])
    ap.add_argument("--voice"); ap.add_argument("--model"); ap.add_argument("--probe", action="store_true")
    ap.add_argument("--steps", default="tts,render,mix,qc")
    a = ap.parse_args(); pd = pathlib.Path(a.project).resolve(); pj = load_project(pd)
    for s in a.steps.split(","):
        {"tts": step_tts, "render": step_render, "mix": step_mix, "qc": step_qc}[s](pj, pd, a)
