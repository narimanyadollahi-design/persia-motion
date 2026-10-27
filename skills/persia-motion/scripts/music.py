#!/usr/bin/env python
"""Original music bed, synthesized (no samples, no copyright issues).

python -X utf8 music.py <project_dir> [--mode shur|esfahan|major] [--bpm 76]
Reads <project>/meta.json (dur, cstart) written by the render step, writes <project>/out/music.wav.
Plucked strings (Karplus-Strong, tar/setar-like) in a Persian mode with real quarter tones,
a drone, and a soft frame-drum (daf) pattern. Arc follows the scene starts:
intro = pluck only, drum enters at scene 3, lift at scene 6, resolve on the end card.
reel.py's mix step ducks it under the voice automatically when out/music.wav exists.
"""
import argparse, json, pathlib, wave
import numpy as np

SR = 48000
# semitone offsets from the tonic; .5 = koron (quarter-flat)
MODES = {"shur": [0, 1.5, 3, 5, 7, 8, 10, 12], "esfahan": [0, 2, 3, 5, 7, 8, 11, 12], "major": [0, 2, 4, 5, 7, 9, 11, 12]}


def pluck(freq, dur, bright=0.5, seed=0):
    n = int(dur * SR); p = max(2, int(SR / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p) * (0.6 + 0.4 * bright)
    out = np.empty(n); idx = 0
    decay = 0.996 - (1 - bright) * 0.004
    for i in range(n):
        out[i] = buf[idx]
        nxt = (idx + 1) % p
        buf[idx] = decay * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    # body resonance: gentle low-pass + fade
    out = np.convolve(out, np.ones(3) / 3, "same")
    return out * np.minimum(1, np.arange(n) / (0.002 * SR))


def dom():   # low frame-drum hit
    n = int(.5 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (62 + 30 * np.exp(-t * 25)) * t) * np.exp(-t * 7) +
            np.random.default_rng(1).normal(0, 1, n) * np.exp(-t * 40) * .15)


def bak():   # rim slap
    n = int(.15 * SR); t = np.arange(n) / SR
    x = np.random.default_rng(2).normal(0, 1, n); x = np.diff(x, prepend=0)
    return x * np.exp(-t * 45) * .35 + np.sin(2 * np.pi * 420 * t) * np.exp(-t * 30) * .15


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("project"); ap.add_argument("--mode", default="shur")
    ap.add_argument("--bpm", type=float, default=76); ap.add_argument("--tonic", type=float, default=146.83)  # D3
    a = ap.parse_args(); pd = pathlib.Path(a.project).resolve()
    meta = json.load(open(pd / "meta.json")); D = meta["dur"]; cs = meta["cstart"]
    N = int(D * SR); L = np.zeros(N); R = np.zeros(N)
    deg = MODES[a.mode]; f = lambda d, o=0: a.tonic * 2 ** ((deg[d % 7] + 12 * (d // 7) + 12 * o) / 12)
    beat = 60 / a.bpm; e8 = beat / 2

    def put(sig, t, g, pan=0.0):
        i = int(t * SR)
        if i >= N or i < 0: return
        s = sig[: N - i] * g; L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))

    drum_in = cs[2] if len(cs) > 2 else 4.0
    lift = cs[5] if len(cs) > 5 else D * .6
    end = cs[-1]
    # drone (tonic + fifth), slow swell
    t = np.arange(N) / SR
    dr = (np.sin(2 * np.pi * f(0, -1) * t) + .6 * np.sin(2 * np.pi * f(4, -1) * t) + .3 * np.sin(2 * np.pi * f(0) * t))
    dr *= (0.75 + .25 * np.sin(2 * np.pi * .1 * t)) * np.minimum(1, t / 3) * np.clip((D - t) / 2.5, 0, 1) * .045
    L += dr; R += dr
    # melody: a short Shur-like phrase (descending to the tonic), varied each bar
    phrases = [[4, 3, 2, 1, 2, 1, 0, -1], [2, 3, 4, 3, 2, 1, 1, 0], [4, 5, 4, 3, 2, 3, 1, 0], [7, 6, 5, 4, 3, 2, 1, 0]]
    k, tt, bar = 0, 0.3, 0
    while tt < end - .2:
        ph = phrases[bar % len(phrases)] if tt < lift else phrases[(bar % 2) + 2]
        for j, d in enumerate(ph):
            if tt >= end - .2: break
            dense = tt >= drum_in
            if j % 2 == 0 or dense:
                g = .30 if j % 2 == 0 else .18
                put(pluck(f(d), 1.6, bright=.65 if tt >= lift else .5, seed=k), tt, g, pan=(-.25 if j % 2 else .25))
                if tt >= lift and j % 4 == 0: put(pluck(f(d, -1), 1.8, .4, seed=k + 99), tt, .16)   # octave below
                k += 1
            # tremolo flourish (riz) on the bar's last note after the lift
            if tt >= lift and j == 7:
                for r in range(4): put(pluck(f(d), .4, .7, seed=k + r), tt + r * e8 / 4, .08)
            tt += e8
        bar += 1
    # frame drum from scene 3: dom on 1, bak on 2-and, dom on 3, bak on 4
    tt = drum_in
    while tt < end:
        put(dom(), tt, .55); put(bak(), tt + beat * 1.5, .4, .2); put(dom(), tt + beat * 2, .45); put(bak(), tt + beat * 3, .4, -.2)
        tt += beat * 4
    # resolve on the end card: open chord + low dom
    for d, g in [(0, .35), (4, .25), (7, .22), (0, .2)]:
        put(pluck(f(d, -1 if g == .2 else 0), 3.0, .55, seed=500 + d), end + .05, g)
    put(dom(), end + .05, .6)
    mix = np.stack([L, R], 1)
    mix /= max(1e-6, np.abs(mix).max()) / .85
    out = pd / "out"; out.mkdir(exist_ok=True)
    with wave.open(str(out / "music.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
    print("music ok ->", out / "music.wav", f"{D:.1f}s, mode={a.mode}, bpm={a.bpm}")


if __name__ == "__main__":
    main()
