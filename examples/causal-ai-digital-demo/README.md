# Example: Causal AI Digital marketing video

A fully-rendered example using the pipeline. This is the actual marketing video we built for our own brand — released here so you can see what the pipeline produces end-to-end and use it as a reference when building your first one.

## Preview

![First 8 seconds of the square render](../../docs/preview/preview.gif)

| Money shot (frame at 12.5s — `/productos` tour) |
|:-:|
| ![Money shot thumbnail](../../docs/preview/thumbnail.jpg) |

Want the full 30 seconds? → [`output/marketing-square.mp4`](output/marketing-square.mp4) · [`output/marketing-vertical.mp4`](output/marketing-vertical.mp4)

## What's in this folder

```
causal-ai-digital-demo/
├── README.md                              ← this file
├── voiceover.mp3                          ← Mateo Aragon (Spanish LATAM), ~24s
├── music.mp3                              ← cinematic ambient
├── causal-ai-digital-logo.png             ← brand logo, transparent PNG
├── transcript.json                        ← word-level whisper.cpp output (52 words)
├── video-marketing-services.html          ← square 1080×1080 HTML
├── video-marketing-services-vertical.html ← vertical 1080×1920 HTML
└── output/
    ├── marketing-square.mp4               ← rendered output (~9 MB)
    └── marketing-vertical.mp4             ← rendered output (~14 MB)
```

## Inputs we used

| Input | Value |
|---|---|
| **Website URL** | `https://website-pi-seven-28.vercel.app/` (NovaTech Hardware demo store) |
| **Subpage** | `/productos` (multi-page tour) |
| **Logo** | `causal-ai-digital-logo.png` |
| **Contact** | `+51 972 571 826` |
| **Voice** | ElevenLabs Mateo Aragon, Style 30, Speed 0.9, Stability 50 |
| **Music** | YouTube Audio Library, "cinematic inspirational" filter |

## The script (Spanish)

```
Hay webs que se ven.
Hay webs que se sienten.
Y hay webs que venden por ti.

Aprenden de cada visita.
De cada clic.

Cada web que diseñamos viene con un chatbot
que conoce todos tus productos
y atiende a tu cliente
siempre.

Diseño que enamora.
Inteligencia que vende.

Causal AI Digital.
```

50 words, ~24 seconds when read at speed 0.9.

## How it was rendered

```bash
cd examples/causal-ai-digital-demo
python ../../scripts/record_video.py .
```

That produced `output/marketing-square.mp4` and `output/marketing-vertical.mp4`.

Total render time: ~80 seconds (both formats together).

## Reproducing it

If you cloned this repo and have the prerequisites (Python + Playwright + FFmpeg + whisper.cpp — see [main README](../../README.md)), you can re-render this exact video:

```bash
# From the repo root
cd examples/causal-ai-digital-demo

# (Optional) re-transcribe the voiceover to regenerate transcript.json
whisper-cli -m /path/to/ggml-small.bin -l es -oj -of transcript -ml 1 -sow voiceover.mp3
node ../../scripts/transcript_convert.mjs transcript.json

# Render
python ../../scripts/record_video.py .
```

The HTMLs in this example are NOT placeholder-templated — they're fully populated with the inputs above. Use them as a reference when filling in `templates/square.html` and `templates/vertical.html` for your own client.

## What this demonstrates

- **Multi-page tour**: home page (9s) → `/productos` page (14s) → CTA outro (5s)
- **Drone landing**: the first 1.5s of the home slide opens at `scale(1.15)` and settles to `1.0`
- **Cinematic camera tour**: `linear` easing on the `translateY()` keyframes — feels like a real drone passing over the page
- **Fake cursor click**: at ~5.7s a fake mouse cursor lands on the home page just before the transition to `/productos`, suggesting the user clicked
- **Word-level subtitle sync**: 12 phrase groups, each with `subFadeIn`/`subFadeOut` CSS animations matching whisper.cpp word boundaries
- **Voice + music duck**: voiceover at 100%, music at 18%, mixed with `amix=duration=longest` so music continues into the CTA
- **CTA outro**: Causal AI Digital logo + "Conversemos." in cyan + green WhatsApp pill with phone

## Watching the output

The MP4s are in `output/`. Open them in any video player (VLC, QuickTime, Windows Media Player) or drop into a browser via `file://`.

Specs:
- Square: 1080×1080, 30s, H.264 + AAC, ~9 MB
- Vertical: 1080×1920, 30s, H.264 + AAC, ~14 MB

Both pass the QA review process (Section 7 of the SKILL).

## Forking this for your own brand

This example deliberately ships with the real Causal AI Digital brand assets — voice off, phone number, logo, marketing pitch. It's the actual production video, kept intact as a quality reference.

If you want to use this as a starting template for your own brand:

1. **Replace assets**:
   - Record your own voice off in ElevenLabs → `voiceover.mp3`
   - Pick your own music → `music.mp3`
   - Add your logo → `<your-brand>-logo.png`
2. **Re-transcribe**:
   ```bash
   whisper-cli -m models/ggml-small.bin -l <lang> -oj -of transcript -ml 1 -sow voiceover.mp3
   node ../../scripts/transcript_convert.mjs transcript.json
   ```
3. **Edit the HTML files**:
   - `<iframe src="...">` → your client's URL (and subpage URL)
   - `.cta-conversemos` text → your tagline (e.g., "Let's talk", "Get in touch")
   - `.cta-pill` content → your phone/WhatsApp/email
   - `<img class="cta-logo" src="...">` → your logo filename
   - `.sub` divs → match your `transcript.json` words
   - `.sub-N` CSS rules → use whisper word timestamps (see SKILL.md § 5)
4. **Tune the camera tour**:
   - Adjust `@keyframes scroll-tour-home` and `scroll-tour-productos` translateY values for your client's page heights
   - Possibly adjust the cursor `left`/`top` positions if the click target moves
5. **Re-render**:
   ```bash
   rm -rf output && python ../../scripts/record_video.py .
   ```

The cleaner path for production work is to start from `templates/square.html` and `templates/vertical.html` (which use `{{PLACEHOLDERS}}`) instead of editing this example. This folder is meant as a *reference* of what a finished setup looks like.
