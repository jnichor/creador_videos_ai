# Templates

Two HTML templates — square (1080×1080) and vertical (1080×1920). Each is a self-playing slideshow that gets recorded by `scripts/record_video.py`.

## What to replace per client

Search-and-replace these placeholder strings. They appear in BOTH templates.

| Placeholder | What to put | Where |
|---|---|---|
| `{{HOME_URL}}` | Client's homepage URL | iframe `src` attribute, slide 1 |
| `{{PRODUCTS_URL}}` | Client's products / services / value page URL | iframe `src`, slide 2 |
| `{{LOGO_FILENAME}}` | Filename of the client's logo PNG (relative to the HTML) | CTA slide `<img src>` |
| `{{CTA_PHONE}}` | Client's contact (phone, WhatsApp, email) | CTA slide pill |
| `{{CTA_TAGLINE}}` | Short brand tagline shown above the phone | CTA slide |

## What to hand-tune per client

These are NOT search-and-replaceable — they need creative judgment per client:

### 1. Per-page scroll-tour keyframes

Each slide has its own `@keyframes scroll-tour-N`. The percentages and `translateY()` values are hand-tuned to land on visually-important sections at the right moment.

Test pattern: render once with the defaults, watch the result, then adjust the `translateY()` distances based on where the page actually has content. Sites differ — a long e-commerce homepage scrolls differently than a minimalist landing page.

### 2. Subtitle text (`.sub-N` divs)

Replace each `<div class="sub sub-N">...</div>` text to MATCH what your `voiceover.mp3` actually says (use `transcript.json` from whisper.cpp as truth).

### 3. Subtitle CSS timing (`.sub-N` rules)

The `subFadeIn`/`subFadeOut` `forwards Xs` values come from `transcript.json` word timestamps. Either:

- Run `node scripts/transcript_convert.mjs` (after whisper transcription) and use the values manually, or
- Use the auto-generation snippet in [`SKILL.md` § 5 Phrase grouping](../SKILL.md)

### 4. Fake cursor position (`left`, `top`)

The cursor instances (`cursor-1`, `cursor-2`, ...) have hardcoded `left`/`top` for where the click pulse lands. Adjust based on:
- Where the iframe is scrolled at the click moment
- What clickable element is visible at that position

If you're unsure, place the cursor at center-bottom (e.g., `left: 540px; top: 850px` for square). Most CTAs land there visually.

## Then run

```bash
python scripts/record_video.py <project-folder>/
```

It auto-detects the templates by filename, records each, and muxes audio.
