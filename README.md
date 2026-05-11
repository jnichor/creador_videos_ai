# creador_videos_ai

> Turn any website URL into a polished 30-second marketing video — cinematic camera tour, professional voice off, word-level synced subtitles, multi-format output (square / vertical / horizontal). All deterministic, all from HTML + Python + FFmpeg.

A Claude Code skill + companion templates that automate marketing video production for any public website. Built and battle-tested for [Causal AI Digital](https://causalaidigital.com) — released as open source so any agency, freelancer, or marketing team can adapt the pipeline.

**No video editor required. No SaaS subscription. No paid AI tools beyond an ElevenLabs free account.**

---

## Preview

![Causal AI Digital marketing video — first 8 seconds](docs/preview/preview.gif)

> Drone landing → cinematic scroll through the live site → fake cursor click → transition to the products page. Word-level synced subtitles burned in. Full 30s render in [`examples/causal-ai-digital-demo/output/`](examples/causal-ai-digital-demo/output/).

---

## What it produces

| Format | Resolution | Use |
|---|---|---|
| Square | 1080×1080 | LinkedIn, Twitter, IG feed, Facebook |
| Vertical | 1080×1920 | Reels, TikTok, Shorts, IG Stories |
| Horizontal (optional) | 1920×1080 | YouTube, web hero |

Each video bundles:
- Cinematic camera tour through the live site (drone landing intro + scroll + zoom)
- Multi-page navigation simulated with a fake cursor click overlay
- Word-level synced burned-in subtitles (whisper.cpp transcription)
- Voice off + ducked background music
- Branded CTA outro (logo + phone/contact)

See [`examples/causal-ai-digital-demo/`](examples/causal-ai-digital-demo/) for fully rendered examples across all 6 templates.

---

## Templates, style packs, and channels

The pipeline is built around **three orthogonal axes** you combine freely:

### Templates (`--template <name>`) — the STRUCTURE

Six structural layouts, each suited to a different kind of site. Pick **one** per video.

| Template | Best for | Slides |
|---|---|---|
| `tour-pages` (default) | Multi-page sites: home → products → contact | 3 |
| `multi-product` | Ecommerce / catalogue with featured products | 5 (home → catalogue → 2 product details → CTA) |
| `single-page-tour` | SaaS landings / one-pagers where everything lives on `/` | 2 (one 23s scroll-tour + CTA) |
| `feature-spotlight` | Long landings with 3 key sections to highlight | 4 (3 zoom-and-hold spotlights + CTA) |
| `split-mobile-desktop` | Agencies showing responsive design | 2 (side-by-side mobile + desktop + CTA) |
| `before-after` | Redesigns / migrations / rebrands | 2 (split with `ANTES` / `AHORA` badges + CTA) |

Each template has its own placeholder set — see [`templates/README.md`](templates/README.md) for the full per-template specs and [`templates/CONTRACT.md`](templates/CONTRACT.md) for the rules every template respects.

### Style packs (`--style <name>`) — the VISUAL LANGUAGE

Four coherent design systems applied via `body.style-<name>`. Pick **one** per video. Works with all 6 templates.

| Pack | For | Look |
|---|---|---|
| `cinematic` (default) | SaaS / B2B / agencies | Dark navy + cyan, restrained crossfades, breathing CTA |
| `bold` | D2C / ecommerce / lifestyle | Magenta + coral, punch transitions, pop subtitles, elastic stat callouts |
| `editorial` | Podcasts / content brands / thought leadership | Warm sepia + serif italic, letterbox bars, lower-third subtitle band |
| `tech` | AI / dev tools / cybersecurity | Matrix-green + monospace, scanline overlay, glitch-step subtitle reveal |

### Channel variants (`--channel <name>`) — the PLATFORM TUNING (vertical only)

Each social platform's native UI eats different parts of the frame. The channel flag shifts subtitle placement so it never gets covered by likes/share rails or auto-hiding controls.

| Channel | What changes |
|---|---|
| `default` (LinkedIn / generic) | No change — placement is already correct |
| `tiktok` | Subtitles move up to clear the right-side likes/share/comments column |
| `youtube` | Subtitles drop slightly lower for a more cinematic frame (Shorts auto-hides bottom controls) |
| `linkedin` | Alias of default |

### Combinations

```
6 templates × 4 style packs × 4 channels = 96 distinct video configurations
```

…all from the **same** voiceover + logo + URLs. Build one render config per platform, no asset duplication.

---

## Why this exists

The marketing video space for small/mid agencies has three broken options:

1. **Adobe / CapCut**: hand-crafted, not reproducible, takes hours per client.
2. **AI video tools** (Synthesia, Pictory, etc.): subscription, generic, can't show *their actual website*.
3. **Remotion / pure code**: powerful but requires React + a build pipeline.

This repo's bet: an HTML page that auto-plays itself, screen-recorded by a headless browser, then muxed with audio. The site you sell shows up as a live `<iframe>` — pixel-perfect at 1920px, smoothly panned by CSS keyframes. Subtitles come from whisper.cpp word-level timestamps so they're never out of sync.

The whole pipeline runs in **~80 seconds** per client (square + vertical), zero recurring cost.

---

## How it integrates with Claude Code

This is primarily a **Claude Code skill** (`SKILL.md`). When installed at `~/.claude/skills/creador_videos_ai/`, Claude detects requests like *"make me a marketing video for [URL]"* and runs the entire pipeline interactively:

1. Asks you for the 6 required inputs (URL, logo, contact, script, voice MP3, music MP3).
2. Auto-discovers subpages from the site's nav (or accepts your list).
3. Customizes the HTML templates with your assets.
4. Generates word-level synced subtitle CSS from `transcript.json`.
5. Renders square + vertical formats.
6. Runs **automatic visual QA** — extracts frames at critical timestamps, inspects them for known error patterns (white iframe-load frames, cursor invisibility, subtitle drift, misframing), and iterates until clean.
7. Reports the deliverables.

You can also use the templates + scripts manually without Claude Code — see "Manual usage" below.

---

## Setup (one-time)

### 1. Python + Playwright

```bash
pip install playwright
python -m playwright install chromium
```

Optional fallback if no system FFmpeg:

```bash
pip install imageio-ffmpeg
```

### 2. FFmpeg

| OS | Install |
|---|---|
| Windows | https://www.gyan.dev/ffmpeg/builds/ → extract → add `bin/` to PATH |
| macOS | `brew install ffmpeg` |
| Linux | `apt install ffmpeg` |

### 3. whisper.cpp + multilingual model

For word-level subtitle timing.

**Windows pre-built binary**:
```powershell
curl -L -o whisper.zip "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.4/whisper-blas-bin-x64.zip"
# Extract to C:\whisper\, add to PATH
```

**macOS / Linux**:
```bash
git clone --depth 1 https://github.com/ggml-org/whisper.cpp
cd whisper.cpp && make
```

**Multilingual model** (~466 MB — for non-English voice off):
```bash
curl -L -o ggml-small.bin \
  "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
```

> ⚠ Always use `small` (multilingual), NOT `small.en`. The `.en` variants *translate* non-English audio into English instead of transcribing it.

### 4. Install the Claude Code skill

```bash
# Linux / macOS
mkdir -p ~/.claude/skills/creador_videos_ai
cp SKILL.md ~/.claude/skills/creador_videos_ai/

# Windows (PowerShell)
mkdir $HOME\.claude\skills\creador_videos_ai
copy SKILL.md $HOME\.claude\skills\creador_videos_ai\
```

Restart Claude Code. Verify with `/creador_videos_ai` autocomplete.

### 5. ElevenLabs free account

Register at https://elevenlabs.io. Free tier covers ~10k chars/month — a 30-second script is ~250 chars. No card required.

---

## Quickstart — your first marketing video

### What you produce manually (Claude can't generate audio)

1. **Voice off** — go to ElevenLabs, paste your script (45-55 words), select a voice (Mateo Aragon for Spanish LATAM, Adam for English US — see `docs/voice-presets.md`), download MP3 as `voiceover.mp3`.

2. **Background music** — YouTube Audio Library (free + cleared): https://studio.youtube.com/.../music. Filter Cinematic / Inspirational / 1+ min. Download as `music.mp3`.

3. **Brand logo** — PNG with transparent background, ~1500×500 or square. Save as `<client>-logo.png`.

### Then run the pipeline

If you have Claude Code installed with the skill:

```
You: Hazme un video de marketing para https://miclientepe.com
     Logo: client-logo.png, contacto +XX XXX XXX XXX
     Script: "Tu copy de marketing aquí..."
```

Claude will gather the rest, run the pipeline, and QA-review the output.

If you prefer manual:

```bash
# 1. Transcribe voice off → transcript.json
whisper-cli -m models/ggml-small.bin -l es -oj -of transcript voiceover.mp3
node scripts/transcript_convert.mjs    # flattens nested whisper JSON

# 2. Pick a template, copy its 2 format files into your project folder
#    (see "Templates" section above to pick one — default is tour-pages)
cp templates/tour-pages-square.html  my-project/
cp templates/tour-pages-vertical.html my-project/

# 3. Edit them with your inputs (placeholders documented in templates/README.md)

# 4. Render — both formats, default style + channel
python scripts/record_video.py my-project/

# Or pick a specific template + style + channel for a target platform:
python scripts/record_video.py my-project/ --template multi-product --style bold
python scripts/record_video.py my-project/ vertical --channel tiktok --style bold
python scripts/record_video.py my-project/ --template before-after --style editorial
```

Output filenames are auto-suffixed when you pick non-default values (e.g. `marketing-square-multi-product-bold.mp4`) so renders for different platforms don't overwrite each other.

---

## Folder structure

```
creador_videos_ai/
├── README.md                                  ← this file
├── LICENSE                                    ← MIT
├── SKILL.md                                   ← the Claude Code skill
├── .gitignore
│
├── templates/
│   ├── README.md                              ← per-template specs (placeholders + structure)
│   ├── CONTRACT.md                            ← rules every template respects (marker, classes, scheduler)
│   ├── tour-pages-{square,vertical}.html      ← 3 slides: home → products → CTA  (DEFAULT)
│   ├── multi-product-{square,vertical}.html   ← 5 slides: home → catalogue → 2 products → CTA
│   ├── single-page-tour-{square,vertical}.html ← 2 slides: 23s scroll-tour + CTA
│   ├── feature-spotlight-{square,vertical}.html ← 4 slides: 3 zoom-and-hold spotlights + CTA
│   ├── split-mobile-desktop-{square,vertical}.html ← 2 slides: side-by-side devices + CTA
│   └── before-after-{square,vertical}.html    ← 2 slides: ANTES / AHORA split + CTA
│
├── scripts/
│   ├── record_video.py                        ← Playwright + FFmpeg orchestrator
│   ├── discover_pages.py                      ← auto-discover subpages
│   └── transcript_convert.mjs                 ← whisper.cpp JSON → flat array
│
├── docs/
│   ├── voice-presets.md                       ← ElevenLabs voice + style table per language
│   ├── whisper-install.md                     ← detailed whisper.cpp setup
│   ├── sound-design.md                        ← optional sfx.json layer for whoosh / click / sub-bass
│   └── troubleshooting.md                     ← 10 most common bugs + fixes
│
└── examples/
    └── causal-ai-digital-demo/                ← fully working example, rendered in all 6 templates
        ├── README.md                          ← the inputs we used
        ├── voiceover.mp3                      ← Mateo Aragon, Spanish LATAM, ~24s
        ├── music.mp3                          ← cinematic ambient
        ├── causal-ai-digital-logo.png
        ├── transcript.json                    ← word-level whisper output
        ├── tour-pages-{square,vertical}.html  ← demo of each template (placeholders pre-filled)
        ├── multi-product-{square,vertical}.html
        ├── ... (one pair per template)
        └── output/
            ├── marketing-square.mp4            ← tour-pages, cinematic, default channel
            ├── marketing-square-multi-product.mp4
            ├── marketing-square-bold.mp4
            └── ... (one mp4 per template × style × channel combo rendered)
```

---

## The technique — how it works under the hood

### 1. Iframe-driven cinematic tour

The "camera" isn't a real camera — it's an `<iframe>` of the target site, rendered at desktop width (1080px), with `transform: translate3d()` and `scale()` driven by CSS keyframes. The wrapper crops it to the output viewport. Result: the actual rendered website is what the viewer sees, panned smoothly.

```css
.demo-frame-wrapper iframe {
  width: 1080px; height: 5800px;
  animation: scroll-tour-home 9s linear forwards;
}

@keyframes scroll-tour-home {
  0%   { transform: translate3d(0, 0, 0)        scale(1.15); }   /* drone landing */
  17%  { transform: translate3d(0, 0, 0)        scale(1.0);  }
  100% { transform: translate3d(0, -2400px, 0)  scale(1.0);  }   /* scrolled to footer */
}
```

### 2. Multi-page tour with stacked iframes

Multiple `<div class="slide demo-slide">` blocks, each with its own iframe pointing to a different URL. A small JS scheduler swaps `.active` between slides based on `data-duration`. The user sees a continuous "tour" through home → products → contact, even though no real navigation happens.

### 3. Fake cursor click overlay

An SVG cursor positioned `position: fixed`, animated with CSS to land on a CTA button ~0.3s before each scene transition. **Visual only — no real `.click()`** (cross-origin iframes block it anyway). The viewer's brain reads it as causality: "user clicked → next page loaded".

### 4. Word-level subtitle sync (the killer feature)

whisper.cpp transcribes the actual `voiceover.mp3` into JSON with per-word `start`/`end` timestamps:

```json
[
  { "text": "Hay",  "start": 0.13, "end": 0.27 },
  { "text": "webs", "start": 0.27, "end": 0.58 }
]
```

We group words into phrases, then generate CSS animations with **two animations per subtitle** — `subFadeIn` at phrase start, `subFadeOut` at phrase end:

```css
.sub-1 {
  animation:
    subFadeIn  0.18s ease-out forwards 0.13s,
    subFadeOut 0.22s ease-in  forwards 1.60s;
}
```

This eliminates the #1 caption complaint ("subtitles don't match the voice"). Tested across Spanish, English, Portuguese.

### 5. Audio mux

FFmpeg combines the silent recording with voice (100%) + music (18% ducked):

```bash
-filter_complex "[1:a]volume=1.0[voice];[2:a]volume=0.18[bgm];
                 [voice][bgm]amix=inputs=2:duration=longest[mixed]"
```

`duration=longest` keeps the music playing past the voice end into the CTA outro — never that abrupt cut you get with `-shortest`.

---

## What's hard / what doesn't work

Honest about limitations:

- **Sites with `X-Frame-Options: DENY`** can't be iframed. The pipeline auto-detects and warns. Workaround: full-page screenshots + Ken Burns.
- **Sites that detect iframe and block JS** (some banks, some retailers) render but break interactivity. Usually OK for video since we don't interact.
- **Page heights vary** — the per-page scroll keyframes are hand-tuned. Spend 10-15 min per client adjusting `translateY()` values to land on the right sections.
- **Cursor positions are estimates** — without runtime introspection of the iframe (CORS), we can't pixel-perfect-target buttons. Adjust `left`/`top` per cursor instance after first render.
- **Playwright recording timing drift** — can be 0.5-2s off from wall-clock. The skill's QA review process detects and corrects this.
- **No real audio recording** — Playwright headless silently drops audio. We mux post-recording. If you need sound effects timed to specific frames, this pipeline is too crude.

---

## Contributing

Issues welcome. PRs even more so. Common improvement areas:

- Cross-platform whisper.cpp install scripts
- Additional voice presets per language
- Tested templates for known-blocking sites (with screenshot fallback)
- Auto-tuning of camera tour keyframes from page height detection
- Cursor position auto-targeting via DOM inspection (where CORS allows)

This is unmaintained-by-default — assume the author won't reply within 7 days. Ship PRs that include both the change and a test render that passes the QA process.

---

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, sell services with it. Attribution appreciated, not required.

Built by [Causal AI Digital](https://causalaidigital.com) for our own marketing pipeline. Released so others don't have to rebuild it.
