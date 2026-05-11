---
name: creador_videos_ai
description: Build a 30-second cinematic marketing video for any website URL using the Causal AI Digital pipeline (Playwright iframe scroll tour + ElevenLabs voice off + whisper.cpp word-level synced subtitles + FFmpeg audio mux). Use when the user asks to generate a promotional/marketing video for a website, create a cinematic camera tour of a webpage, sync burned-in subtitles to a voice over from a transcript, or render multi-format social media videos (square, vertical, horizontal) from an HTML template. Outputs deterministic MP4s for LinkedIn, Instagram, TikTok, Reels, YouTube. Do NOT invoke for animated infographics, kinetic typography, data-driven slideshows, podcast/audio editing, or videos longer than 60 seconds — those need a different stack.
---

# creador_videos_ai — Marketing Video Pipeline

Turns any public website URL into a polished marketing MP4 by combining a self-playing HTML cinematic tour (live `<iframe>` scrolled by CSS keyframes) with whisper.cpp-derived burned-in subtitles, then renders to multiple social-media formats.

**Source of truth:** the project's `PIPELINE.md` has the full workflow with diagrams, FFmpeg flag rationale, voice presets per language, and troubleshooting. Read it before authoring a new template if the user is starting from scratch. This skill is the trigger + the rules; the doc has the long-form detail.

## When to invoke

Trigger this skill when the user asks for any of:

- "Make a marketing/promo video for this site/URL"
- A cinematic scrolling tour of a webpage with voice off
- Burned-in subtitles synced to a voice over
- Multi-format social media video (square / vertical / horizontal) from a website
- "Vídeo para Reels/TikTok/LinkedIn" tied to a website URL

Do NOT invoke for:

- Animated infographics, kinetic typography, data-driven bar charts (different stack — HyperFrames or Remotion)
- Podcast / audio editing
- Videos longer than 60 seconds (out of scope — the pipeline is tuned for 25–35 s)
- Pure motion graphics with no real-website footage

## Inputs to gather BEFORE starting

Confirm with the user; do NOT invent these. Six are REQUIRED — do NOT proceed without all of them. Claude cannot generate voice off or music itself; the user must produce these and place the files where Claude can read them.

### Required (6) — block until provided

1. **Live website URL** — must be public, no login walls, no localhost, no `X-Frame-Options: DENY`
2. **Brand logo PNG with transparent background** — ~1500×500 or square. File path required (e.g. `videos/<client>-logo.png`)
3. **Contact info** for the CTA — phone, WhatsApp, or email
4. **Voice script** — text in any language, **45–55 words** for ~25 s voice off. Used both to write the captions and as reference for the user's TTS generation
5. **Voice off MP3** — `videos/voiceover.mp3` already generated. Claude does NOT have ElevenLabs credentials and cannot generate this. If the user doesn't have it, walk them through the ElevenLabs steps (Voice presets table in section 9.1) and STOP — wait for them to download the MP3 and confirm before continuing
6. **Background music MP3** — `videos/music.mp3` already downloaded. Royalty-free source (YouTube Audio Library, Pixabay, Mixkit). If the user doesn't have one, give them search filters (Cinematic / Corporate / Inspirational, 1+ min) and STOP — wait for the file before continuing

### Required (1 more) — block until decided

7. **Style pack** (regla #23) — visual lenguage of the video. Four packs, one is mandatory. ALWAYS show the user the Style Pack Selector table (next section) and ASK which pack to use BEFORE customizing HTML. Default if the user has no opinion: `cinematic`. The chosen pack drives palette, transitions, subtitle treatment, and callout entrance — it's a single coherent decision, not a checkbox list.

### Optional (4) — sensible default if missing

8. **Multi-page tour subpages** — 2–3 URLs to include beyond the homepage (e.g., `/products`, `/about`, `/contact`). If the user has none in mind, OFFER auto-discovery (Playwright scrapes the nav menu — see "Auto-discovery of subpages" section). Default if they decline both: homepage-only.

9. **SFX cues** (regla #20) — `sfx.json` + `sfx/*.mp3` files in the project folder. If the user wants the audio layer with whoosh / click / sub-bass, ASK them to drop SFX files into `sfx/` and write the cue list. The cue palette and free SFX sources are in `docs/sound-design.md`. If missing, pipeline mixes voice + music only — DO NOT block on this.

10. **Motion overlays / callouts** (regla #21) — only relevant if the user wants to call attention to a specific feature, stat, or region of the scrolling page. The templates ship with a commented example block right before the subtitles. If the user has stats / claims worth surfacing visually, ask for them and uncomment+position the callouts; otherwise leave the block commented and ship without.

11. **Channel target** (regla #22) — `--channel tiktok` / `linkedin` / `youtube` flag on the recorder, applies only to vertical renders. If the user names TikTok / Reels / Shorts specifically, ALWAYS use `--channel tiktok` (subtitles must avoid the bottom UI). Default is fine for LinkedIn or general use.

### Hard gate

If ANY of (1)–(6) is missing, STOP and ASK. Do NOT write a single line of HTML, do NOT modify the template, do NOT run a render. The pipeline depends on all six being on disk before Step 4 (HTML customization) begins.

Common user mistake: they say "ya tengo todo" but `voiceover.mp3` is actually still in their Downloads folder, or `music.mp3` doesn't exist yet. ALWAYS verify the files physically exist:

```bash
ls -lh videos/voiceover.mp3 videos/music.mp3 videos/<client>-logo.png
```

If any returns "No such file", stop and ask the user to provide it before proceeding.

## Style Pack Selector (mandatory step)

Right after the 6 required inputs are collected and BEFORE you customize a single line of HTML, show this table to the user and ask which pack to use. The user picks ONE. The pack is then applied as `body.style-<name>` via `record_video.py --style <name>` — no manual CSS surgery per client.

| Pack | For | Personality |
|---|---|---|
| **cinematic** (default) | SaaS, B2B, agencies, consultoras, fintechs, brands selling trust | Dark navy + cyan, drone landing, restrained crossfades, breathing CTA. Looks like Apple's product launch trailers. |
| **bold** | D2C, ecommerce, restaurantes, fitness, lifestyle, retail | Magenta + coral palette, punch transitions, pop-entrance subtitles, elastic stat callouts. Looks like a Glossier / Gymshark / DTC video. |
| **editorial** | Podcasts, newsletters, content brands, thought leadership, periodismo digital | Warm sepia + amber palette, serif italic CTA, letterbox bars (top/bottom), lower-third subtitle band (no centered pill), slow cross-dissolves. Looks like a BBC documentary intro. |
| **tech** | AI startups, dev tools, infra, ciberseguridad | Matrix-green (#0AFF6A) on near-black, JetBrains Mono / Fira Code, scanline overlay, glitch-step subtitle reveal, `> ` prompt prefix on CTA & subs, hue-rotate on inactive slides. Looks like a hacker movie. |

How to phrase the question:

> "Vamos a elegir la dirección visual. Tenés 4 packs:
> - **cinematic** — la apuesta segura: dark, cinematográfico, sobrio. Va con casi todo
> - **bold** — magenta + coral, pop, energético. Para ecommerce y lifestyle
> - **editorial** — lower-third tipo BBC, cinematic ratio, serif italic. Para contenido / podcasts
> - **tech** — terminal, glitch, matrix-green mono. Para AI / dev tools
>
> ¿Cuál encaja con la marca?"

Rules for this step:

- **Always show all 4 — don't pre-filter.** Even if the brand looks "obviously cinematic," the user might be repositioning.
- **Never invent a 5th pack on the fly.** If the user wants something off-menu (e.g., "neon retro 80s synthwave"), explain that we'd add it as a real `style-<name>` selector and that's a follow-up engagement, not a per-client customization.
- **One pack per video.** Don't try to mix `bold` with `cinematic` subtitles — packs are coherent design systems, mixing them defeats the purpose.

## Non-negotiable rules

These are mistakes that look correct in code but break the result. Never violate:

1. **Subtitle CSS pattern: TWO animations per subtitle, never one.** Use `subFadeIn` (fires at phrase start) + `subFadeOut` (fires at phrase end). Never use a single `subFade` keyframe with `0%/15%/85%/100%` opacity stops — that ties fade duration to phrase duration, breaking short and long phrases differently.

   ```css
   .sub-1 {
     animation:
       subFadeIn  0.18s ease-out forwards 0.13s,   /* phrase.start */
       subFadeOut 0.22s ease-in  forwards 1.60s;   /* phrase.end */
   }
   ```

2. **Whisper model: multilingual `small`, NEVER `small.en`.** `.en` models *translate* non-English audio into English instead of transcribing it. For Spanish/Portuguese/French/etc voice off, always use `ggml-small.bin` with `-l <code>`.

3. **FFmpeg audio: `amix=inputs=2:duration=longest`, NOT `-shortest`.** Music must continue past the voice end into the CTA outro. `-shortest` cuts at voice end and feels abrupt.

4. **Trim Chromium init flash with `-ss 0.3` on the VIDEO input only.** Audio still starts at 0. Without this, you get a 0.3 s white frame at the start.

5. **Camera tour easing: `linear`, never `ease-in-out`.** Cubic-bezier eases make the scroll feel like an old PowerPoint. Linear is the cinematic choice.

6. **Iframe width must MATCH the site's natural design width.** Most modern responsive sites (Tailwind/Bootstrap/Next.js) render correctly at the wrapper width — use `width: 1080px` for both square and vertical (matches the wrapper, no horizontal crop, clean encuadre). Force `width: 1920px` ONLY for sites with strict desktop-only layouts that break below 1280px (rare). When in doubt, render at 1080 first and check the encuadre — if you see mobile/hamburger nav or stacked content where the desktop has a row, then bump to 1920 and add `margin-left: -420px` to crop. NEVER blindly force 1920 — it cuts off the left/right 420px of any responsive site that already adapts to 1080.

7. **Two HTML files, one per format. Do NOT use CSS media queries for square↔vertical.** Vertical needs subtitles 480 px from bottom (not 90 px), larger font (76 px not 1.7 rem), stacked CTA layout, and different iframe wrapper height. Splitting keeps each layout cleanly tunable.

8. **Pixel format: `yuv420p`.** Social platforms reject `yuv444p`. No exceptions.

9. **Phone numbers spoken phonetically in the script.** ElevenLabs reads `+51 999 888 777` as "fifty-one nine hundred ninety-nine...". Write phonetically: `más cincuenta y uno, nueve nueve nueve, ocho ocho ocho, siete siete siete` (Spanish) or its English equivalent. Test with TTS preview before committing.

10. **Windows file-lock retry stays in `record_video.py`.** Playwright holds the `.webm` briefly after `browser.close()`. The `latest.rename(raw_webm)` call must be wrapped in a 10-attempt retry loop with `time.sleep(0.5)` on `PermissionError`. Never remove this.

11. **Subtitle text must match the voice EXACTLY.** Whisper transcribes what was actually said. If the script differs from the voice off (because ElevenLabs dropped a word, or the user re-recorded with edits), use whisper's transcription as truth, not the original script.

12. **Hide subtitles during the CTA slide.** The slideshow scheduler must add `body.cta-active` when the CTA slide activates, and `body.cta-active .subtitles { opacity: 0 }` must be in the CSS. Otherwise the last subtitle bleeds into the brand outro.

13. **Multi-page tour: each subpage is its own `<div class="slide demo-slide">` with its own iframe.** Never put multiple URLs into one iframe with JS-driven `src` swaps — the browser fires a re-render flash, breaks the scroll animation, and may load a CORS-blocked frame mid-flight. Stack pages as separate slides; the existing `setTimeout` scheduler does the transitions.

14. **Verify each subpage iframe-embeds before adding to the tour.** Check `X-Frame-Options` and `Content-Security-Policy: frame-ancestors` with `curl -I <url>`. If a page is blocked, FALL BACK to a static full-page screenshot (Playwright `page.screenshot({ fullPage: true })`) and Ken-Burns it as a `<img>` instead of an `<iframe>`. NEVER ship a video with blank-frame slides.

15. **Fake cursor overlay is VISUAL ONLY. Never call `.click()` or dispatch real events to the iframe.** Cross-origin iframes block it; same-origin iframes that DO accept clicks would break the slideshow scheduler if you wired real navigation. The cursor's job is to suggest causality ("user clicked → next page loaded"), nothing more. Always hide it during the CTA slide via `body.cta-active .fake-cursor { opacity: 0 }`.

16. **Auto-discovered subpages must be same-origin and same-language.** When scraping `<nav>` / `<header>` `<a href>` values, filter to URLs whose hostname matches the input domain. Drop external links (social media, third-party tools, language switches), drop fragment-only anchors (`#section`), drop the homepage itself. ALWAYS show the discovered list to the user for approval before wiring it into the HTML — auto-discovery is a starting point, not a final answer.

17. **Subpages must MATCH the brand's video aesthetic.** Before adding a discovered page to the tour, eyeball its background. If the rest of the video is dark cinematic (`#050a14` / dark navy) and a candidate subpage has a WHITE/LIGHT background, REJECT it — the dark→white→dark flash breaks the cinematic flow more than the breadth of pages helps. Either skip that subpage, or warn the user and offer alternatives (stay on a longer dark page, apply a CSS overlay/filter, or use a screenshot with a Ken Burns crop). Two consistent dark pages beat four with a jarring white page in the middle.

18. **Fake cursor SVG must use a strong stroke (≥ 2.5 px) and dual drop-shadow** so it stays visible on ANY background. White fill alone disappears on light pages; thin strokes vanish in compression. The combination `fill: white; stroke: black; stroke-width: 3; stroke-linejoin: round` plus `filter: drop-shadow(0 0 6px rgba(0,0,0,0.9)) drop-shadow(0 4px 10px rgba(0,0,0,0.7))` is the proven pattern. Never use a single drop-shadow or stroke under 2 px — they fail on white-on-white.

19. **Never declare a render "done" without running the QA review process (Step 7).** A successful render exit code does NOT mean the video is correct — Playwright recordings frequently have iframe-load white frames, cursor invisibility on bright backgrounds, subtitle drift, misframing, and white-page flashes that pass the render but fail visually. The ONLY way to catch these is to extract critical frames with FFmpeg, READ them via the Read tool, and inspect them against the error pattern table in Step 7c. If you skip this step and tell the user "listo", you'll either: (a) ship a broken video they discover later, or (b) waste rounds when they ask "did you check?". Always inspect before declaring done. Rendering is fast; iteration on a missed bug is slow.

20. **SFX layer is OPTIONAL and additive — never required.** When the user provides `sfx.json` in the project folder, `record_video.py` mixes the cues into the audio via `adelay` + `amix`. SFX timings are in **slideshow-time** (t=0 = first frame the viewer sees), NOT wall-clock recording time. Voice = 1.0, music = 0.18, SFX should be ≤ 0.6 (sub-bass excepted up to 0.7). Click SFX must fire 0.05–0.10 s AFTER the cursor pulse start, never before — perfect sync feels mechanical. Never stack 3+ SFX in the same 0.5 s window. If `sfx.json` is missing, the pipeline runs as before with voice + music only. Full guide: `docs/sound-design.md`.

21. **Callouts are accents, not decoration.** The `.callout--ring` / `.callout--box` / `.callout--stat` system in the templates exists to point the viewer's eye at WHAT matters on the scrolling iframe. Rules: max **2 callouts on screen at once** (more = noise), position OFF the iframe's visual center (the iframe is doing its job, the callout annotates it), and **time the callout to the voice phrase that names it** (the eye should arrive at the number while the ear is still hearing it). Callouts auto-hide during the CTA outro via `body.cta-active .callout` — never override this. If a slide has no specific element to point at, ship without callouts on that slide; an unmotivated callout reads as clutter.

22. **Channel variants for vertical are body-class overrides, not template forks.** When the user asks for a TikTok / Reels / Shorts video, run `record_video.py --channel tiktok` (or `linkedin` / `youtube`); the recorder injects `body.channel-<name>` via Playwright before the slideshow starts, and the vertical template's CSS shifts subtitle placement to avoid the platform's native UI. **TikTok subtitles MUST move from `bottom: 240px` to `top: 58%`** — the bottom 25% of a TikTok vertical frame is covered by the likes/share/comments rail, so default placement gets eaten. LinkedIn keeps defaults (clean bottom-feed UI). YouTube Shorts moves subtitles slightly lower (`bottom: 140px`) for a more cinematic frame since its bottom controls auto-hide on play. Render output filenames carry the suffix (`marketing-vertical-tiktok.mp4`) — never overwrite a channel render with a different channel render.

23. **Style packs are mandatory and asked BEFORE HTML customization.** The skill ships 4 visual style packs: `cinematic` (default — SaaS/B2B), `bold` (D2C/lifestyle/retail), `editorial` (content brands / podcasts — warm sepia + serif + letterbox), `tech` (AI/dev tools — matrix-green + monospace + glitch). Before editing the HTML template, ALWAYS show the Style Pack Selector table (next section) and ASK which pack to use. The pack maps to a `body.style-<name>` class injected by `record_video.py --style <name>`. **One coherent pack per video — never mix.** Render output filenames are suffixed when the pack is non-default (`marketing-square-bold.mp4`, `marketing-vertical-tech.mp4`).

## Workflow (condensed — see PIPELINE.md for full detail)

### 1. Verify prerequisites

- Python + `playwright` package + `python -m playwright install chromium`
- FFmpeg in `PATH` (or `imageio-ffmpeg` Python package as fallback — the script auto-detects)
- whisper.cpp at `C:\whisper\whisper-cli.exe` on Windows (or built locally on macOS/Linux)
- Whisper model `ggml-small.bin` at `C:\whisper\models\` (~466 MB)
- ElevenLabs free account at https://elevenlabs.io

### 2. Generate voice off (ElevenLabs)

Voice presets by language:

| Language | Voice | Style | Speed | Stability |
|---|---|---|---|---|
| Spanish (LATAM) | Mateo Aragon | 30–40 | 0.9–0.95 | 50 |
| Spanish (Spain) | Bea | 30–40 | 0.95 | 60 |
| English (US) | Adam | 50–60 | 0.9 | 50 |
| English (UK) | Dorothy | 30–40 | 0.95 | 60 |
| Portuguese (BR) | Antoni | 40 | 0.95 | 55 |
| French | Charlotte | 40 | 0.9 | 55 |

Save as `videos/voiceover.mp3` in the project.

### 3. Transcribe with whisper.cpp

```powershell
C:\whisper\whisper-cli.exe -m C:\whisper\models\ggml-small.bin -l <lang> -oj -of transcript voiceover.mp3
```

The whisper.cpp JSON has a nested schema (`transcription[].tokens[]`). Convert to flat `[{text, start, end}]`:

```javascript
const data = require('./transcript.json');
const words = [];
for (const seg of data.transcription) {
  for (const w of seg.tokens || []) {
    if (!w.text || w.text.startsWith('[')) continue;
    words.push({ text: w.text.trim(), start: w.offsets.from / 1000, end: w.offsets.to / 1000 });
  }
}
require('fs').writeFileSync('transcript.json', JSON.stringify(words, null, 2));
```

### 4. Customize HTML template

Copy `videos/video-marketing-services.html` (square 1080×1080) and `video-marketing-services-vertical.html` (vertical 1080×1920). Per client, edit:

- `<iframe src="...">` → client URL
- `.demo-frame-wrapper iframe { height: ... }` → match target site's full scroll length
- `@keyframes scroll-tour` percentages → hand-tune (see Camera tour rules below)
- `<img class="cta-logo" src="...">` → client logo file
- `.cta-phone` content → client contact
- `<div class="sub sub-N">...` → match exact whisper transcription
- `.sub-N` CSS rules → use `subFadeIn`/`subFadeOut` with whisper word timestamps

### 5. Phrase grouping for subtitles

- **3–5 words per phrase** (conversational default)
- 2–3 words for hype/launch energy
- 4–6 words for educational/measured
- Break on sentence boundaries, commas with ≥150 ms pause, natural breath units
- ONE subtitle on screen at a time
- 12 phrases is the typical count for a 25 s voice off

Generate the CSS programmatically from `transcript.json` instead of typing by hand:

```javascript
const words = require('./transcript.json');
const phrases = [
  ["Hay webs que se ven.",            0,  4],
  ["Hay webs que se sienten.",        5,  9],
  ["Y hay webs que venden por ti.",  10, 16],
  // ...
];
phrases.forEach(([text, s, e], i) => {
  const start = words[s].start.toFixed(2);
  const end   = words[e].end.toFixed(2);
  console.log(`.sub-${i+1} { animation: subFadeIn 0.18s ease-out forwards ${start}s, subFadeOut 0.22s ease-in forwards ${end}s; }`);
});
```

### 6. Render

```bash
cd videos
python record_video.py            # both formats, cinematic style, default channel
python record_video.py square     # only square
python record_video.py vertical   # only vertical
python record_video.py . --style bold                          # bold pack (both formats)
python record_video.py . vertical --style bold --channel tiktok # bold + TikTok placement
python record_video.py . vertical --channel linkedin
python record_video.py . vertical --channel youtube
```

Each format takes ~30 s. Both formats: ~80 s total. Each channel or style variant adds one extra pass; render multiple variants in sequence to produce platform-tuned + brand-tuned outputs without overwriting (filenames are suffixed: `marketing-vertical-bold-tiktok.mp4`).

If `sfx.json` is present in the project folder, SFX cues are mixed into the audio automatically — no extra flag needed.

`--style` and `--channel` are orthogonal: style controls the visual lenguage (palette, transitions, subtitle treatment), channel controls subtitle PLACEMENT on the frame (where the platform's native UI lives). Both can combine freely.

### 7. QA review process (MANDATORY — never skip)

Render exit code 0 does NOT guarantee a correct video. Playwright recording timing drift, iframe-load white frames, cursor invisibility on bright backgrounds, misframing, and subtitle drift all PASS the render but FAIL visually. Always run the four-step QA review below before declaring done.

#### 7a. Metadata audit

```bash
FFMPEG=$(python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
"$FFMPEG" -i videos/<output>.mp4 2>&1 | grep -E "Duration|Stream"
```

Verify: duration matches (~28-30s), resolution matches format, h264/yuv420p/AAC ≥128kbps audio.

#### 7b. Frame extraction at critical timestamps

Critical timestamps for a 28s 2-page video (adapt per structure):

| t | What to verify |
|---|---|
| 0.3–0.5s | First subtitle visible, drone landing, no white iframe-load frame |
| 1.5s | Sub-1 fading out / sub-2 fading in (subtitle sync) |
| 4.5s | Mid-home scroll, sub matches voice phrase |
| Just-before-transition (e.g. 8.6s) | Fake cursor visible AND on/near a clickable element |
| Just-after-transition (e.g. 9.0s) | Next page rendered (no blank), subtitle matches voice |
| Page-2 climax (e.g. 13.0s) | Money shot — narrative pitch lands on most relevant content |
| Pre-CTA (e.g. 22.5s) | Last sub of voice off, last frame of demo |
| CTA (e.g. 24-25s) | Logo + tagline + phone visible, NO subtitle, NO cursor |

```bash
mkdir -p videos/qa-frames
for t in 0.3 1.5 4.5 8.6 9.0 13.0 18.5 22.5 24.0; do
  "$FFMPEG" -y -ss "$t" -i videos/<output>.mp4 -frames:v 1 -q:v 2 "videos/qa-frames/t${t}.png"
done
```

Then READ each PNG via the Read tool. Visual inspection is the ONLY way to catch real bugs.

#### 7c. Error patterns table — what to look for in each frame

| Error pattern | What it looks like | Root cause / fix |
|---|---|---|
| Pure white frame at start | Blank white, no content | Iframe still loading. Add `onload="window.iframe1Loaded=true"` to iframe + Python `wait_for_function("() => window.iframe1Loaded")` BEFORE `window.startSlideshow()`. Trim with `-ss <offset>` |
| Misframed page (sides cropped) | Right/left UI cut off | iframe `width` ≠ wrapper width, or `margin-left: -420px` on a responsive site. Match iframe width to wrapper (regla #6) |
| Sudden white page mid-video | Bright page after dark | A subpage has white bg → flash. REMOVE that page (regla #17). Keep only dark-themed pages |
| Cursor invisible | No cursor at expected click moment | White-on-white. Cursor SVG must have `stroke-width: 3` + `filter: drop-shadow(0 0 6px rgba(0,0,0,0.9)) drop-shadow(0 4px 10px rgba(0,0,0,0.7))` (regla #18) |
| Cursor on empty bg | Cursor in dead space, not a button | `left`/`top` estimate wrong. Adjust per cursor instance |
| Subtitle wrong text | Sub says X, voice says Y | Sub text doesn't match whisper transcript. Use whisper as truth |
| Subtitle wrong timing | Sub appears too early/late vs voice | Trim offset miscalculated. Adjust `slideshow_start_offset` or measure `recording_start` BEFORE `page.goto()` |
| Music abrupt cut at voice end | Audio stops at ~23s | Used `-shortest`. Switch to `amix=inputs=2:duration=longest` (regla #3) |
| White flash 0-0.3s | Brief white at very start | Iframe-load gating missing OR `-ss` trim too small |
| Subtitle visible during CTA | Demo sub bleeds into outro | Missing `body.cta-active .subtitles { opacity: 0 }` (regla #12) |

#### 7d. Cursor visibility zoom

Cursors are 28-32px on a 1080-canvas — invisible at preview downscale. ALWAYS zoom:

```bash
"$FFMPEG" -y -i <frame>.png -vf "crop=400:200:<cursor-x>:<cursor-y>,scale=800:400" <frame>-zoom.png
```

Read the zoomed PNG. Cursor must be clearly visible against the background — both fill AND stroke contrasting with whatever's behind.

#### 7e. Static checklist (after frame inspection passes)

- [ ] Subtitle text matches the voice EXACTLY (whisper-transcribed words)
- [ ] Each subtitle appears as the phrase starts, disappears as it ends
- [ ] No subtitle visible during the CTA slide
- [ ] No white flash at start (`-ss <offset>` working, iframe gating working)
- [ ] Music continues past voice end (no abrupt cut)
- [ ] Logo + phone fully visible during CTA
- [ ] Total duration ≈ slideshow + 1-2s buffer
- [ ] File sizes reasonable: square ~5-9 MB, vertical ~9-14 MB
- [ ] **Multi-page**: every iframe loaded fully, no blank frames after transition
- [ ] **Multi-page**: page transitions feel natural — crossfade default
- [ ] **Multi-page**: total page durations + CTA = voiceover + CTA duration
- [ ] **Fake cursor**: visible (zoom-checked) AND lands on/near clickable element
- [ ] **Auto-discovered pages**: user approved AND no light/white-bg pages in dark video

#### 7f. If anything fails

Do NOT declare done. Fix HTML or `record_video.py`, re-render, re-extract frames, re-inspect. Iterate until the video passes the visual inspection cleanly. The user pays you to catch errors, not to ship them and ask for forgiveness.

## Camera tour tuning (the hardest creative part)

Spend 10–15 minutes per client tuning `@keyframes scroll-tour`. The structure:

```css
@keyframes scroll-tour {
  /* DRONE LANDING — open zoomed-in, settle */
  0%   { transform: translateY(0)       scale(1.15); }
  9%   { transform: translateY(0)       scale(1.0);  }   /* land at hero */

  /* HOLD on hero */
  18%  { transform: translateY(0)       scale(1.0);  }

  /* SCROLL through key sections */
  30%  { transform: translateY(-900px)  scale(1.0);  }
  45%  { transform: translateY(-2200px) scale(1.06); }   /* slight zoom for emphasis */
  65%  { transform: translateY(-3600px) scale(1.0);  }

  /* LAND on brand-positive section (footer / contact / testimonials) */
  100% { transform: translateY(-4720px) scale(1.0);  }
}
```

Tuning rules:

- **0–9 % drone landing:** `scale(1.10–1.20)` → `scale(1.0)`. This is the hook.
- **Hold longer** on visually-important sections (hero, featured products, CTAs).
- **Slight zoom** (`scale(1.05–1.08)`) at 1–2 emphasis points — never on every section.
- **Total animation duration must equal voiceover.mp3 duration** so the CTA outro lands as the voice transitions to the brand close.
- **End on something brand-positive** — footer, contact section, testimonials, never mid-scroll.

## Multi-page tour pattern

When the marketing video should reveal more than just the homepage (which is most of the time — single-page tours feel thin), stack each page as its own `demo-slide` and let the existing scheduler swap between them.

### Structure

```html
<!-- Slide 1: homepage (8 s) -->
<div class="slide demo-slide active" data-duration="8000">
  <div class="demo-frame-wrapper">
    <iframe src="https://client.com/" class="page-1"
            sandbox="allow-same-origin allow-scripts" loading="eager"></iframe>
  </div>
</div>

<!-- Slide 2: products (6 s) -->
<div class="slide demo-slide" data-duration="6000">
  <div class="demo-frame-wrapper">
    <iframe src="https://client.com/products" class="page-2"
            sandbox="allow-same-origin allow-scripts" loading="eager"></iframe>
  </div>
</div>

<!-- Slide 3: contact (5 s) -->
<div class="slide demo-slide" data-duration="5000">
  <div class="demo-frame-wrapper">
    <iframe src="https://client.com/contact" class="page-3"
            sandbox="allow-same-origin allow-scripts" loading="eager"></iframe>
  </div>
</div>

<!-- CTA outro (5 s) -->
<div class="slide cta-slide" data-duration="5000">...</div>
```

Each iframe gets its own scroll-tour keyframes, sized to its content:

```css
.page-1 { animation: scroll-tour-1 8s linear forwards; }
.page-2 { animation: scroll-tour-2 6s linear forwards; }
.page-3 { animation: scroll-tour-3 5s linear forwards; }

@keyframes scroll-tour-1 {
  0%   { transform: translateY(0)       scale(1.15); }
  14%  { transform: translateY(0)       scale(1.0);  }
  100% { transform: translateY(-2400px) scale(1.0);  }
}
@keyframes scroll-tour-2 {
  0%   { transform: translateY(0)       scale(1.0);  }
  60%  { transform: translateY(-1200px) scale(1.06); }
  100% { transform: translateY(-1800px) scale(1.0);  }
}
/* etc. */
```

### Pacing

- **5–8 s per page** is the sweet spot for product/service marketing.
- **First page (homepage) gets the longest hold** — 7–8 s with the drone landing intro.
- **Last page should be action-oriented** (contact, signup) so the visual narrative ends at "what to do next."
- **Total page durations + CTA must equal voiceover duration** so the voice off lands the brand close exactly when the CTA slide appears. Off-by-1-second is fine; off-by-3 looks broken.

### Page selection — pick by narrative arc, not URL alphabet

| Slot | Content type | Why |
|---|---|---|
| 1 | Homepage / hero | First impression, brand vibe |
| 2 | Primary value (products, services, work) | What they actually sell |
| 3 | Trust (testimonials, case studies, about) | Why believe this brand |
| 4 | Action (contact, booking, signup) | What to do right now |

Skip subpages with login walls, half-built dashboards, "coming soon" placeholders, or noisy admin panels.

## Fake cursor click overlay (recommended for multi-page tours)

A fake mouse-cursor SVG that animates onto a visible CTA button on screen ~0.3 s BEFORE the slide transitions to the next page. The viewer's brain reads it as "clicked → navigated" even though no actual click happened. Pure visual storytelling.

### Structure

```html
<!-- Strong stroke + dual drop-shadow keeps the cursor visible on ANY background.
     White fill + 3px black stroke = high contrast on dark; black stroke + dark
     drop-shadow keeps it readable on white. -->
<svg class="fake-cursor" width="32" height="46" viewBox="0 0 24 36">
  <path d="M0,0 L0,28 L7,21 L11,30 L14,29 L10,20 L18,20 Z"
        fill="white" stroke="black" stroke-width="3" stroke-linejoin="round"/>
</svg>
```

```css
.fake-cursor {
  position: fixed;
  top: 0; left: 0;
  z-index: 200;
  opacity: 0;
  pointer-events: none;
  /* Dual drop-shadow: dark for contrast on light bg + cyan glow for brand pop */
  filter:
    drop-shadow(0 0 6px rgba(0, 0, 0, 0.9))
    drop-shadow(0 4px 10px rgba(0, 0, 0, 0.7));
  will-change: transform, opacity;
}

/* Animate cursor for handoff slide-1 → slide-2 (slide-1 is 8 s, transition fires at 8 s) */
.fake-cursor {
  animation: cursor-click-1 1s ease-in-out forwards 6.7s;
}

@keyframes cursor-click-1 {
  0%   { left: 50%;  top: 50%;  opacity: 0; transform: scale(1);    }
  20%  { left: 50%;  top: 50%;  opacity: 1; transform: scale(1);    }   /* fade in mid-screen */
  70%  { left: 760px; top: 820px; opacity: 1; transform: scale(1);   }   /* glide to button */
  85%  { left: 760px; top: 820px; opacity: 1; transform: scale(0.85);}   /* click pulse */
  100% { left: 760px; top: 820px; opacity: 0; transform: scale(1);   }   /* fade out */
}

body.cta-active .fake-cursor { opacity: 0; }
```

### Rules

- **Land on a real visible button** (Hero CTA, "Ver productos", "Contacto"). Estimate `(left, top)` based on the iframe's current scroll position at handoff time.
- **Time the click pulse 0.3 s BEFORE the slide transition fires**, not after. The transition feels "caused" only if the click happens first.
- **One cursor element for the whole video**, animated between scenes. Don't create one per slide.
- **Always hide during the CTA outro** (`body.cta-active .fake-cursor { opacity: 0 }`).
- **Skip the cursor on transitions where it would feel forced** — e.g., a long product gallery scroll already feels like browsing; don't fake-click between gallery items.

## Auto-discovery of subpages

If the user doesn't volunteer subpage URLs, run a Playwright pass to scrape the site's nav before recording, then ASK the user to approve the discovered list.

### Discovery script — drop in `videos/discover_pages.py`

```python
"""
Usage: python discover_pages.py https://client.com
Prints a JSON list of up to 4 same-origin URLs from the nav/header.
"""
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json, sys

base_url = sys.argv[1]
origin = urlparse(base_url).netloc

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(base_url, wait_until="networkidle")

    hrefs = page.eval_on_selector_all(
        "nav a[href], header a[href]",
        "els => els.map(e => e.href)"
    )
    browser.close()

unique = []
seen = set()
for h in hrefs:
    parsed = urlparse(h)
    if parsed.netloc != origin: continue
    if parsed.fragment: continue
    if parsed.path in ("", "/"): continue
    key = parsed.path.rstrip("/")
    if key in seen: continue
    seen.add(key)
    unique.append(h)

print(json.dumps(unique[:4], indent=2))
```

### Use it

```bash
python videos/discover_pages.py https://client.com > videos/subpages.json
```

Then SHOW the discovered list to the user. Examples of how to phrase it:

> "Encontré estas páginas en el menú: `/products`, `/about`, `/contact`. ¿Vamos con esas, o prefieres otras?"

### Rules

- **Always require user approval** before wiring auto-discovered URLs into the HTML. The most marketing-relevant page is sometimes buried in the footer and the nav-scrape misses it.
- **Trim to 3 max** for a 30-second video. More than that = each page gets too little screen time to register.
- **If discovery returns 0 results** (single-page sites, hash-based routing, JS-rendered nav that didn't load in time), fall back to homepage-only mode and tell the user.
- **Verify each discovered URL with `curl -I`** to filter out `X-Frame-Options: DENY` pages before showing the list.

## Output spec to validate

| Property | Square | Vertical | Horizontal (optional) |
|---|---|---|---|
| Resolution | 1080×1080 | 1080×1920 | 1920×1080 |
| Frame rate | 25 fps (Playwright default) | 25 fps | 25 fps |
| Codec | H.264 (libx264, CRF 20) | same | same |
| Audio | AAC, 192 kbps | same | same |
| Pixel format | yuv420p | yuv420p | yuv420p |
| Container | MP4 (`+faststart`) | MP4 | MP4 |
| Final size | ~5 MB | ~9 MB | ~15 MB |
| Native fit | LinkedIn, IG feed, FB, X | Reels, TikTok, Shorts, IG Stories | YouTube, web hero |

## Reference

- **`PIPELINE.md`** at the project root — full workflow, FFmpeg flag table per flag, voice presets table, ElevenLabs gotchas table, troubleshooting matrix
- **`videos/video-marketing-services.html`** — canonical square template (1080×1080)
- **`videos/video-marketing-services-vertical.html`** — canonical vertical template (1080×1920)
- **`videos/record_video.py`** — Playwright + FFmpeg orchestrator with Windows file-lock retry

When a step is ambiguous or the user asks for something the rules don't cover, read `PIPELINE.md` rather than improvising.
