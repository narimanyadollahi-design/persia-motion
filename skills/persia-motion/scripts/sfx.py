#!/usr/bin/env python
"""Per-element sound design, synthesized (no samples, no copyright issues).

python -X utf8 sfx.py <project_dir>
Reads <project>/meta.json › sfx  = [{"t": seconds, "k": kind, "g": gain?, "p": pitch?, "pan": -1..1?}, ...]
(the scene template fills window.SFX; the render step writes it to meta.json), writes <project>/out/sfx.wav.
reel.py's mix step uses out/sfx.wav instead of its basic whoosh/click when the file exists.
Rule: every visible action gets the sound of its own material — a typed key ticks, a lock clicks, a stamp thuds.
Kinds: whoosh swish shutter flash pop tick type lock stamp flip paper buzz ding chime sparkle tap riser thud click
"""
import json, pathlib, sys, wave
import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def T(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.normal(0, 1, int(d * SR))
def env(t, a=.002, d=.1): return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)
def lp(x, k): return np.convolve(x, np.ones(k) / k, "same")          # cheap low-pass
def hp(x, k): return x - lp(x, k)                                    # cheap high-pass
def bp(x, lo, hi): return lp(hp(x, lo), hi)


def tone(f, d, dec, a=.001, harm=((1, 1),)):
    t = T(d); return sum(g * np.sin(2 * np.pi * f * m * t) for m, g in harm) * env(t, a, dec)


def whoosh(p=1):
    t = T(.55); x = lp(noise(.55), 10); return x * np.sin(np.pi * t / t[-1]) ** 2 * .5
def swish(p=1):   # scene/background swap: band-passed noise with a fast sweep
    t = T(.35); x = bp(noise(.35), 3, 6); return x * np.sin(np.pi * t / t[-1]) ** 3 * .45
def shutter(p=1):   # mirror slap + curtain: two clicks 60 ms apart with a noise tail
    out = np.zeros(int(.25 * SR))
    for k, (o, g) in enumerate([(0, 1), (.06, .7)]):
        c = hp(noise(.05), 3) * env(T(.05), .0005, .008) * g + tone(1800 - 600 * k, .05, .01) * .3 * g
        i = int(o * SR); out[i:i + len(c)] += c
    return out * .8
def flash(p=1):   # capacitor whine + pop
    t = T(.3); f = 2000 + 6000 * t / t[-1]; return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / t[-1]) * .05
def pop(p=1):
    t = T(.12); return np.sin(2 * np.pi * (700 * p - 380 * t / t[-1]) * t) * env(t, .001, .025) * .55
def tick(p=1):   # wooden tick, pitch rises with p (calendar cells)
    return tone(1100 * p, .08, .012, harm=((1, 1), (2.7, .4))) * .5 + hp(noise(.08), 2) * env(T(.08), .0003, .004) * .3
def type_(p=1):   # one key: plastic click + tiny thock, randomized
    q = p * rng.uniform(.85, 1.2)
    # laptop / phone keyboard: crisp key-down click (band-passed 2-7 kHz, ~4 ms) + small plastic ring,
    # then a quieter key-up click 45-75 ms later; no low thump (that reads as tapping, not typing). p<0.8 = space bar.
    space = p < .8; out = np.zeros(int(.12 * SR))
    def clk(g, dec):
        return bp(noise(.02), 2, 4) * env(T(.02), .0001, dec) * g
    down = clk(.55, .004 if not space else .006) + tone((1900 if not space else 900) * q, .02, .006) * (.12 if not space else .16)
    out[:len(down)] += down
    up = clk(.22, .003); i = int(rng.uniform(.045, .075) * SR); out[i:i + len(up)] += up
    return out * 1.6
def lock(p=1):   # metal shackle: two sharp transients + bright ring
    out = np.zeros(int(.35 * SR))
    for o, g in [(0, .7), (.045, 1)]:
        c = hp(noise(.03), 2) * env(T(.03), .0002, .004) * g; i = int(o * SR); out[i:i + len(c)] += c
    r = tone(3150, .3, .06, harm=((1, 1), (1.51, .5), (2.3, .25))) * .2; i = int(.045 * SR); out[i:i + len(r)] += r[:len(out) - i]
    return out * .9
def stamp(p=1):   # rubber stamp: low thud + paper slap
    return tone(85, .4, .09) * 1.0 + lp(noise(.4), 4) * env(T(.4), .001, .03) * .6
def thud(p=1): return tone(60, .5, .12) * 1.1 + lp(noise(.5), 8) * env(T(.5), .001, .05) * .3
def flip(p=1):   # card/page flick
    out = np.zeros(int(.18 * SR))
    for o in (0, .05):
        c = bp(noise(.06), 2, 5) * env(T(.06), .001, .012); i = int(o * SR); out[i:i + len(c)] += c
    return out * .8
def paper(p=1):   # paper sweep / backdrop unroll
    t = T(.7); return bp(noise(.7), 4, 9) * np.sin(np.pi * t / t[-1]) ** 2 * .35
def buzz(p=1):   # soft "wrong": two low detuned square-ish tones
    t = T(.32); x = np.sign(np.sin(2 * np.pi * 150 * t)) * .5 + np.sign(np.sin(2 * np.pi * 156 * t)) * .5
    return lp(x, 14) * env(t, .005, .12) * .22
def ding(p=1):   # soft "right": bell
    return tone(1318 * p, 1.0, .35, harm=((1, 1), (2, .35), (3.01, .15))) * .35
def chime(p=1):   # rising arpeggio (∞ / reveal)
    out = np.zeros(int(1.4 * SR))
    for k, f in enumerate([784, 988, 1175, 1568]):
        c = tone(f * p, 1.0, .3, harm=((1, 1), (2, .3))) * .22; i = int(k * .07 * SR); out[i:i + len(c)] += c
    return out
def sparkle(p=1):
    out = np.zeros(int(.8 * SR))
    for k in range(7):
        c = tone(rng.uniform(2500, 5200), .25, .05) * .1; i = int(rng.uniform(0, .5) * SR); out[i:i + len(c)] += c
    return out
def tap(p=1):   # finger on a glass button
    x = tone(520, .12, .02) * .5; c = hp(noise(.03), 2) * env(T(.03), .0002, .004) * .3; x[:len(c)] += c; return x
def riser(p=1):
    t = T(.9); f = 300 + 1500 * (t / t[-1]) ** 2; return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / t[-1]) ** 2 * .08 + bp(noise(.9), 2, 4) * (t / t[-1]) ** 3 * .15
def click(p=1): return tone(1400, .08, .015) * .45


LIB = {k: v for k, v in globals().items() if callable(v) and k in __doc__.split("Kinds:")[1].split()}
LIB["type"] = type_


def main():
    pd = pathlib.Path(sys.argv[1]).resolve(); meta = json.load(open(pd / "meta.json"))
    D = meta["dur"]; N = int(D * SR) + SR; L = np.zeros(N); R = np.zeros(N)
    for e in meta["sfx"]:
        sig = LIB[e["k"]](e.get("p", 1)) * e.get("g", 1); i = int(max(0, e["t"]) * SR); pan = e.get("pan", 0)
        if i >= N: continue
        s = sig[: N - i]; L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))
    mix = np.stack([L, R], 1)[: int(D * SR)]
    pk = np.abs(mix).max()
    if pk > .95: mix *= .95 / pk
    out = pd / "out"; out.mkdir(exist_ok=True)
    with wave.open(str(out / "sfx.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    kinds = sorted({e["k"] for e in meta["sfx"]})
    print("sfx ok ->", out / "sfx.wav", f"{len(meta['sfx'])} events:", ",".join(kinds))


if __name__ == "__main__":
    main()
