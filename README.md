# persia-motion

A Claude Code / agent skill that turns an idea or text into a **9:16 Persian motion-graphics reel**: coded UI mockups, animated cursor, word-by-word karaoke subtitles, synced Persian voiceover, SFX and a chapter progress bar. Every frame is code (HTML → Chrome → ffmpeg).

یک اسکیل برای ساخت **ریل/تیزر موشن‌گرافیک فارسی ۹:۱۶** از روی ایده یا متن، با صدای فارسی همگام و زیرنویس کلمه‌به‌کلمه.

## How it works / نحوه‌ی کار
1. You give an idea or text and call the skill.
2. It **asks** about brand identity, tone, audience, offer and CTA — anything unclear.
3. It rewrites your text as a **pain → need → solution → payoff → action** story.
4. It shows you the script + scenario. **Nothing is built until you approve.**
5. It renders `out/reel.mp4` (1080×1920, 30 fps, −14 LUFS) and runs an automatic layout QC.

## Install
```bash
npx skills add <your-github-user>/persia-motion
# or copy skills/persia-motion into ~/.claude/skills/
pip install -r skills/persia-motion/requirements.txt
python -m playwright install chromium   # or use installed Google Chrome
```
Requires Google Chrome, `ffmpeg`/`ffprobe`, Python 3.10+.

## Use
Say e.g. *"با persia-motion یک ریل فارسی برای فروشگاه آنلاین چای من بساز"* and answer the questions.

CLI (after approval):
```bash
python -X utf8 skills/persia-motion/scripts/reel.py my-project --engine edge        # free Persian voice
python -X utf8 skills/persia-motion/scripts/reel.py my-project --engine eleven      # ElevenLabs (key in .env.local)
```

## Customize
This is the generic edition (neutral brand, fictional sample). Personalize `brand/brand.json`, `template/index.html` (scenes) and your project's `project.json`, or ask your agent to upgrade the skill with your brand identity and tone.

## Limits
7 spoken lines/scenes + end card · monogram instead of image logo · no photo scenes yet · voice naturalness needs a human ear.

## Licenses
Code: MIT. Font Vazirmatn: SIL OFL 1.1 (`skills/persia-motion/fonts/OFL.txt`). Inspired by the structure of a public Persian product teaser; no third-party footage or assets are included.
