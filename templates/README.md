# Templates

HTML templates — each one a self-playing slideshow recorded by `scripts/record_video.py`. Pick a **template** (structural layout) and a **style pack** (visual language) independently. Files live in `templates/<template-name>-<format>.html` where format is `square` (1080×1080) or `vertical` (1080×1920).

See [CONTRACT.md](CONTRACT.md) for the rules every template must respect so the style packs / channel variants / marker sync all work.

## Templates available

| Template | For | Structure | Placeholders |
|---|---|---|---|
| `tour-pages` (default) | Web with multiple pages: home + products/services + contact | 3 slides — home iframe (9s) → products iframe (14s) → CTA (5s). Hand-tuned scroll-tour on each page. | `{{HOME_URL}}`, `{{PRODUCTS_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |
| `multi-product` | Ecommerce / catalogue / brands with featured products | Home (6s) → Catálogo (6s) → Producto 1 (6s) → Producto 2 (5s) → CTA (5s). Simulates a real user journey through a product site. 8 subtitle lines, 2 per slide except CTA. Each iframe MUST be a distinct URL or the story breaks. | `{{HOME_URL}}`, `{{CATALOG_URL}}`, `{{URL_1}}`, `{{URL_2}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |
| `single-page-tour` | SaaS landings / one-pagers where everything lives in `/` | One 23s slide doing a cinematic scroll through hero → features → testimonials → pricing → footer → CTA (5s). 8 subs paced to scroll-tour stops. Hand-tune the `translateY` values to match where YOUR sections live. | `{{PAGE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |
| `feature-spotlight` | Landings with 3 key sections/features to highlight | Three 7-second zoom-and-hold spotlights on the SAME URL (each iframe pans to a different section + zooms ~1.08x) → CTA (7s). 6 subs, 2 per spotlight. Hand-tune the per-spotlight `translateY` to land on each feature. | `{{PAGE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |
| `split-mobile-desktop` | Agencies showing responsive design / multi-device builds | One 23s split slide with two device frames (desktop + mobile shaped iframes) loading independent URLs. Square = side-by-side, vertical = stacked. 8 subs over the split slide. | `{{DESKTOP_URL}}`, `{{MOBILE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |
| `before-after` | Redesigns / migrations / rebrands | One 23s slide split 50/50 (square = left/right, vertical = top/bottom) with "ANTES" and "AHORA" badges + glowing divider. Each half loads its own URL. 8 subs framing the comparison. | `{{BEFORE_URL}}`, `{{AFTER_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}` |

Use:

```bash
python scripts/record_video.py my-client/                                   # tour-pages, both formats
python scripts/record_video.py my-client/ --template multi-product          # multi-product, both formats
python scripts/record_video.py my-client/ vertical --template multi-product --style bold --channel tiktok
```

Output filenames are suffixed when the template is non-default (`marketing-square-multi-product.mp4`).

## What to replace per client

Search-and-replace these placeholder strings. The exact set depends on the template — see the **Placeholders** column in the table above. Common across all templates:

| Placeholder | What to put | Where |
|---|---|---|
| `{{LOGO_FILENAME}}` | Filename of the client's logo PNG (relative to the HTML) | CTA slide `<img src>` |
| `{{CLIENT_NAME}}` | Display name for the logo's `alt` text | CTA slide |
| `{{CTA_PHONE}}` | Client's contact (phone, WhatsApp, email) | CTA slide pill |
| `{{CTA_TAGLINE}}` | Short brand tagline shown above the phone | CTA slide |

Per-template URL placeholders are in each template's top comment.

## What to hand-tune per client

These are NOT search-and-replaceable — they need creative judgment per client:

### 1. Per-page scroll-tour keyframes (`tour-pages` only)

Each slide in `tour-pages` has its own `@keyframes scroll-tour-N`. The percentages and `translateY()` values are hand-tuned to land on visually-important sections at the right moment.

Test pattern: render once with the defaults, watch the result, then adjust the `translateY()` distances based on where the page actually has content. Sites differ — a long e-commerce homepage scrolls differently than a minimalist landing page.

`multi-product` doesn't use scroll-tour — each slide is a short, static iframe view of one product URL.

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

## Optional layers — only add when they earn their place

### Style packs

Four coherent visual languages, applied via `<body class="style-<name>">`. The user picks ONE per video. Don't mix.

| Pack | For | What changes |
|---|---|---|
| `cinematic` (default) | SaaS / B2B / agencies / fintech | Dark navy + cyan, restrained crossfades, breathing CTA |
| `bold` | D2C / ecommerce / lifestyle / retail | Magenta + coral palette, punch transitions, pop-entrance subtitles, elastic stat callouts |
| `editorial` | Podcasts / content brands / news / thought leadership | Warm sepia + amber palette, serif italic, letterbox bars (7% top/bottom), lower-third subtitle band (no centered pill), slow cross-dissolves |
| `tech` | AI / dev tools / cybersecurity | Matrix-green (#0AFF6A) + monospace, scanline overlay, glitch-step subtitle reveal, `> ` prompt prefix on CTA & subs, hue-rotate on inactive slides |

Use:

```bash
python scripts/record_video.py my-client/ --style bold
python scripts/record_video.py my-client/ vertical --style bold --channel tiktok
```

Output filenames are suffixed when the pack is non-default (`marketing-square-bold.mp4`). `--style`, `--channel`, and `--template` combine freely — template controls structure, style controls visual language, channel controls subtitle placement for the target platform.

**Adding a new pack:** add the name to `SUPPORTED_STYLES` in `scripts/record_video.py`, then add a `body.style-<name>` CSS block in every `templates/<template>-<format>.html`. Same pattern as channel variants.

### Motion overlays / callouts

The iframe scrolls, but nothing tells the viewer's eye **what** matters on screen. Callouts solve that. Three variants are built into both templates:

| Variant | Use case | Example |
|---|---|---|
| `callout--ring` | Pulsing circle around a single feature on screen (a CTA button, a chatbot icon, an icon) | Highlight the "Sign up" button at second 4 |
| `callout--box` | Rectangular highlight around a region (a pricing card, a product image) | Wrap a testimonial card |
| `callout--stat` | Floating number / claim — has its own background, doesn't need an element behind it | `+47% conversión` floating top-right |

Per-instance positioning and timing are set via inline CSS variables — no need to write a new CSS rule per callout:

```html
<!-- Pulsing ring centered at 70% across, 42% down, active 3.2s → 5.2s -->
<div class="callout callout--ring"
     style="--x: 70%; --y: 42%; --start: 3.2s; --end: 5.2s;"></div>

<!-- Highlight box, 480×260px, centered, active 4.0s → 7.5s -->
<div class="callout callout--box"
     style="--x: 50%; --y: 60%; --w: 480px; --h: 260px;
            --start: 4.0s; --end: 7.5s;"></div>

<!-- Stat callout with text, top-right, active 12.5s → 15.0s -->
<div class="callout callout--stat"
     style="--x: 76%; --y: 30%; --start: 12.5s; --end: 15.0s;">
  +47% conversión
</div>
```

The templates ship with a commented `<!-- ... -->` block of these examples right before the subtitles section — uncomment, position, and time per client.

**Rules of thumb:**

- **Max two callouts on screen at once.** More than that = noise; the viewer can't decide where to look.
- **Position them OFF the scrolling region's center.** The iframe is doing one job (showing the product), callouts do another (annotating it). Overlap = clutter.
- **Time them to the voice phrase that mentions them.** If your voiceover says "convierte un 47% más" at second 12.8, the `+47%` stat should appear 0.2–0.4s before and stay 1.5–2s after. The eye should arrive at the number while the ear is still hearing it.
- **All callouts auto-hide during the CTA outro** (`body.cta-active`). Don't fight this — the CTA is the final scene, no annotations belong there.

### Sound design / SFX

A whoosh on each transition + a click sync'd to the fake cursor + a sub-bass impact on the drone landing pushes the perceived production value noticeably. The pipeline supports this through an **optional** `sfx.json` next to your `voiceover.mp3` / `music.mp3`:

```
my-client/
  voiceover.mp3
  music.mp3
  sfx.json           ← cue list — optional
  sfx/
    whoosh-soft.mp3
    sub-bass-impact.mp3
```

Schema (JSON array):

```json
[
  { "file": "sfx/sub-bass-impact.mp3", "time": 0.4,  "volume": 0.50 },
  { "file": "sfx/whoosh-soft.mp3",     "time": 8.6,  "volume": 0.45 },
  { "file": "sfx/ui-click-tap.mp3",    "time": 8.78, "volume": 0.55 }
]
```

- `file` — path relative to the project folder
- `time` — seconds in **slideshow-time** (t=0 = the first frame the viewer sees)
- `volume` — 0.0–1.0 linear (default 0.4)

If `sfx.json` is missing, the pipeline behaves exactly as before. Full guide and sourcing in [`docs/sound-design.md`](../docs/sound-design.md). A copy-pasteable starter cue list is in [`sfx.example.json`](sfx.example.json).

### Channel variants (vertical only)

Vertical videos go to three very different surfaces. Their native UIs cover different parts of the frame, so the same subtitle placement that looks clean on LinkedIn gets eaten by TikTok's likes/share rail. The pipeline solves this with a `--channel <name>` flag on the recorder; the value is applied as a `body class` before the slideshow starts, and the vertical template has CSS rules per channel.

```bash
python scripts/record_video.py my-client/ vertical --channel tiktok
python scripts/record_video.py my-client/ vertical --channel linkedin
python scripts/record_video.py my-client/ vertical --channel youtube
```

Output filenames are suffixed with the channel name (`marketing-vertical-tiktok.mp4`) so you can render all three in sequence without overwriting each other.

| Channel | What changes vs default | Why |
|---|---|---|
| `tiktok` | Subtitles move from `bottom: 240px` to `top: 58%` (vertical center-upper), font size +0.25rem | TikTok's likes/share/comments column covers the bottom ~25% of the frame |
| `linkedin` | No change from default — placement is already correct | LinkedIn's feed has minimal UI at the bottom |
| `youtube` | Subtitles move slightly lower (`bottom: 140px` instead of `240px`) | YouTube Shorts auto-hides bottom controls, more cinematic frame |

Render all three in one go (PowerShell):

```powershell
foreach ($ch in 'tiktok', 'linkedin', 'youtube') {
  python scripts/record_video.py my-client/ vertical --channel $ch
}
```

**Adding a new channel:** add the name to `SUPPORTED_CHANNELS` in `scripts/record_video.py` and a `body.channel-<name>` CSS block in every `templates/<template>-vertical.html`. The class is injected automatically.

## Then run

```bash
python scripts/record_video.py <project-folder>/
```

It auto-detects the templates by filename, records each, and muxes audio.
