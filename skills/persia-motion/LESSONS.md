# Lessons (each bug became a rule)
1. Text hidden behind a shape: give floating labels an explicit z-index; QC checks `elementsFromPoint` every 0.1 s.
2. Headline overflow: 58 px, ≤ 2 lines; long Persian lines clip at 74 px.
3. Accent markup: use `*x*` in copy, not HTML spans (the headline splitter breaks on spaces).
4. Always print `pageerror`; a missing `()` on an IIFE fails silently.
5. Run ffmpeg with `-nostdin` (hangs in background otherwise).
6. ElevenLabs free plan: library voices return 402; use premade voices or upgrade.
7. Windows: run Python with `-X utf8`.
8. Edge clipping test must measure text with a Range, not the element box.
9. Don't reuse one template for every story: design scenes from the subject's own world (camera, light, material).
10. Nested `<svg>` inside a global `svg{overflow:visible}` rule spills out of its box — set `overflow:hidden` on nested viewports.
11. Check stills at 30%/70%/97% of every scene (not just mid-scene) to catch transition artifacts.
12. Sidechain ducking: never `asplit` the voice into both the final mix and the compressor key in one graph (ffmpeg deadlocks); render voice.wav first and read it twice. Pad the key to the full length or the music stops at the last word.
13. Measure the mix in segments (intro, mid, end card) — a silent end card is easy to miss by ear.
14. Fix mispronunciations with diacritics on the spoken line and regenerate only that line.
