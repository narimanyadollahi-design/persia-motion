# Lessons (each bug became a rule)
1. Text hidden behind a shape: give floating labels an explicit z-index; QC checks `elementsFromPoint` every 0.1 s.
2. Headline overflow: 58 px, ≤ 2 lines; long Persian lines clip at 74 px.
3. Accent markup: use `*x*` in copy, not HTML spans (the headline splitter breaks on spaces).
4. Always print `pageerror`; a missing `()` on an IIFE fails silently.
5. Run ffmpeg with `-nostdin` (hangs in background otherwise).
6. ElevenLabs free plan: library voices return 402; use premade voices or upgrade.
7. Windows: run Python with `-X utf8`.
8. Edge clipping test must measure text with a Range, not the element box.
