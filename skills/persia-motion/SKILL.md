---
name: persia-motion
description: Build a 9:16 Persian motion-graphics reel/teaser (coded UI mockups, animated cursor, word-by-word karaoke subtitles, synced Persian voiceover, SFX, chapter progress bar) from an idea or text. Asks about brand identity, tone and anything unclear first, rewrites the idea as a pain→solution story, shows the script for approval, and only builds after the user says yes. موشن‌گرافیک ۹:۱۶ فارسی با صدای همگام از روی ایده/متن. Use when the user says "persia-motion", "ریل فارسی", "موشن فارسی", "تیزر معرفی", "موشن با صدای فارسی", or gives an idea/script and wants a Persian motion video.
---

# persia-motion

Generic Persian motion-reel engine. Everything on screen is code (HTML → Chrome frames → ffmpeg). No stock footage, no video-AI.

## HARD RULES (read first)
1. **Never render before the user explicitly approves the final script + scenario.** Questions first, script second, approval third, build last.
2. **Never invent facts** (numbers, results, prices, testimonials, claims). Use only what the user gave. If a number would help, ask for it.
3. **Never put an API key in chat, code or files you share.** ElevenLabs keys live only in `.env.local`.
4. Ask the user's questions in Persian unless they wrote in another language; keep questions short and batched (use `AskUserQuestion` when available, ≤4 per round).

## Step 1 — Intake (ask only what is missing)
Read what the user already gave (idea, text, brand files, screenshots). Then ask about every gap. Never guess these:
- **Identity:** brand/product name (fa + latin for the HUD), colors (paper/ink/accent hex — or "use neutral default"), font (default Vazirmatn), monogram/logo (image logo is not supported yet → monogram letter), tagline. If the user has a brand guide/skill/file, read it instead of asking.
- **Tone:** formal / friendly-colloquial / bold / calm-luxury; words to use or avoid; address form (تو / شما).
- **Audience & pain:** who watches, what hurts, what they already tried.
- **Offer & proof:** what the product does, 1–3 verified facts (only user-supplied).
- **Goal & CTA:** ONE action (comment a word → DM, visit link, save…). Which keyword.
- **Voice:** `edge` free (Farid/Dilara) or ElevenLabs (needs `.env.local`; free plan = premade voices only, e.g. Daniel; paid plan = Persian library voices like Arash). Preferred gender.
- **Length/platform:** default ≈30 s Instagram/TikTok 9:16.
If the request is vague ("make a video for my shop"), ask for the product, the audience's biggest frustration and the desired action before anything else.

## Step 2 — Narrativize (turn idea/text into a story)
Write the script as a **story that holds the viewer to the last second**: pain → felt need → solution → payoff → action. Map it onto the engine's 7 beats (one spoken line = one scene, ≤ ~9 words, ≤ 2 s, spoken/colloquial Persian):

| Beat | Scene | Job | Emotion |
|---|---|---|---|
| 0 | s0 hook grid | Name the pain in the viewer's own words, as a question | "that's me" |
| 1 | s1 two cards | Reframe the root cause ("not you — it's X") | relief + curiosity |
| 2 | s2 intro avatar | Introduce who/what solves it | trust |
| 3 | s3 fields | First concrete step of how it works | clarity |
| 4 | s4 desire cards | The benefit made desirable ("I want that too") | desire |
| 5 | s5 growth chart | Lasting outcome / long-term | confidence |
| 6 | s6 comment→DM + end card | One clear CTA | action |

Rules: pain before product (product appears by ~second 8–10); one metaphor max; one idea per line; no feature lists; no price lists in the video; end on the CTA. Every line is also the headline source — write each scene's on-screen headline (≤ 2 lines, ~22 chars/line) with one accent character `*؟*`/`*.*`.

## Step 3 — Approval gate (mandatory)
Show the user, in one message:
1. **Brand/tone summary** (name, colors, font, tone, voice engine).
2. **Edited script**, numbered by scene: spoken line · on-screen headline · what appears visually (window title, labels, chips) · emotion.
3. **Facts used** (and anything you left out because it was not supplied).
4. Estimated length.
Then ask: "تأیید می‌کنی بسازم؟" Wait. Apply edits and re-show until the user clearly says yes. Silence, "ok maybe", or a partial answer is NOT approval.

## Step 4 — Build (only after approval)
1. Prereqs: `pip install -r requirements.txt` (playwright, edge-tts, elevenlabs, python-dotenv), Google Chrome, ffmpeg/ffprobe. Check; install what's missing (ask before installing system software).
2. Make a project folder; copy `examples/sample-product/project.json` → edit `lines` (7) and every `copy.s0…s7` field with the approved text. Write `brand.json` there if the identity differs from `brand/brand.json`.
3. Run (Windows needs `-X utf8`; set `python` to your interpreter):
   ```
   python -X utf8 skills/persia-motion/scripts/reel.py <project> --engine edge --steps tts,render --probe
   ```
   Look at the probe stills yourself (clipped text, RTL order, overflow, covered labels). Fix copy/lengths if needed.
4. Full build: `python -X utf8 .../reel.py <project> --engine edge` (or `--engine eleven --voice <id>`). Output: `<project>/out/reel.mp4` (1080×1920, 30 fps, −14 LUFS). The `qc` step must print `PASS`.
5. Deliver the file and say honestly what you verified (frames, QC, STT of the voice) and what you could not (how the voice sounds, motion feel).

## Scene types and copy fields (`project.json › copy`)
`s0` {h[2], window, bubble} · `s1` {h[2], card1, card2, card2sub} · `s2` {h[2], chips[2]} · `s3` {h[2], window, fields[3]} · `s4` {h[1-2], chip} · `s5` {h[2], window, marks[3]} · `s6` {h[2], window, typed, dm} · `s7` {cta}. Brand tokens (`brand.json`): hud, name_fa, monogram, tagline, colors{paper,ink,acc,gray}, fonts, chapters[8].
Timing constants (`LEAD 0.5s, GAP 0.4s, tail 2.7s`) must match between `template/index.html` and `scripts/reel.py`.

## Known limits
Exactly 7 spoken lines/scenes + end card · monogram instead of image logo · no photo/screenshot scenes yet · synthetic pad instead of real music · voice naturalness can only be judged by a human ear · needs Chrome + ffmpeg.

## Files
`template/index.html` scenes & animation (data-driven) · `scripts/reel.py` TTS→render→mix→QC · `brand/brand.json` neutral identity · `examples/sample-product/` fictional sample · `fonts/` Vazirmatn (OFL) · `LESSONS.md` pitfalls.
