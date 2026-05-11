# Sound design — optional SFX layer

A 30-second marketing video lives or dies on the first second of audio. Voice + music ducked is already strong — but **whooshes on transitions, a sub-bass impact on the drone landing, and a click sync'd to the fake cursor** push the perceived production value from "well-made" to "looks like an agency made this." The pipeline supports this through an optional `sfx.json` file.

## How it works

If `sfx.json` exists in the project folder, `scripts/record_video.py` adds those SFX as extra inputs to FFmpeg and mixes them into the final audio with `adelay` (per-cue offset) + `amix` (sum of voice + music + every SFX).

If `sfx.json` is missing, the pipeline behaves exactly as before — voice + music only. **Fully backward-compatible.**

## File layout

```
my-client/
  voiceover.mp3
  music.mp3
  sfx.json                      ← cue list (this file)
  sfx/
    whoosh-soft.mp3             ← referenced by sfx.json
    sub-bass-impact.mp3
    ui-click-tap.mp3
```

You can put SFX anywhere relative to the project folder; the `file` field in `sfx.json` is resolved against that folder.

## Schema

`sfx.json` is a JSON array. Each entry:

| Field    | Type   | Required | Default | What it means |
|----------|--------|----------|---------|---------------|
| `file`   | string | yes      | —       | Path to an MP3/WAV/OGG, relative to the project folder |
| `time`   | number | yes      | —       | Seconds **in slideshow-time** (t=0 = first frame the viewer sees) |
| `volume` | number | no       | `0.4`   | 0.0–1.0 linear multiplier (0.4 ≈ subtle, 0.8 ≈ prominent) |

`time` is in slideshow-time, not wall-clock. If your slideshow is 28 s long, valid `time` values are 0–28.

## Recommended cue palette for a 28 s multi-page tour

Start with these — they're the high-impact, low-effort layer. Adjust timings to your slideshow.

```json
[
  { "file": "sfx/sub-bass-impact.mp3", "time": 0.4, "volume": 0.5 },
  { "file": "sfx/whoosh-soft.mp3",     "time": 8.6, "volume": 0.45 },
  { "file": "sfx/ui-click-tap.mp3",    "time": 8.7, "volume": 0.55 },
  { "file": "sfx/whoosh-soft.mp3",     "time": 22.8, "volume": 0.45 },
  { "file": "sfx/riser-short.mp3",     "time": 22.4, "volume": 0.35 }
]
```

What each one does:

- **Sub-bass impact at 0.4 s**: lands the drone settle (`scale(1.15) → scale(1.0)`). Visceral. This is the cue that decides whether someone keeps watching at second 1.
- **Whoosh + click at ~8.7 s**: timed exactly to the fake cursor's click pulse (regla #15). Sells the causality "user clicked → next page loaded" — the click sound is what makes the brain believe the transition.
- **Whoosh at 22.8 s**: marks the handoff from the demo to the CTA outro.
- **Short riser at 22.4 s**: 0.4 s pre-CTA build-up. Subtle but creates the feeling of arriving somewhere.

## Where to source SFX (free / royalty-free)

| Source | URL | Notes |
|---|---|---|
| **freesound.org** | https://freesound.org | Largest library. Filter by CC0 license. Search: "whoosh transition", "sub bass impact", "ui click subtle" |
| **Pixabay SFX** | https://pixabay.com/sound-effects/ | All free, no attribution required |
| **Mixkit** | https://mixkit.co/free-sound-effects/ | Curated, high quality, free with no signup |
| **Zapsplat** | https://www.zapsplat.com | Free with free signup; massive catalog |
| **YouTube Audio Library** | https://studio.youtube.com/.../music | "Sound effects" tab; same source as music.mp3 |

Search terms that actually return useful results:

- **Whoosh**: "whoosh transition short", "swoosh ui", "sweep effect", "air whoosh"
- **Sub-bass impact**: "cinematic boom", "sub bass drop", "impact deep", "trailer hit"
- **Click**: "ui click tap", "soft click button", "interface tap minimal"
- **Riser**: "short riser", "build up tension", "uplifter 2 sec"

## Mixing rules

These are conventions, not hard rules — but breaking them costs realism.

1. **Volume ≤ 0.6 for everything except the sub-bass impact.** Voice is the king (1.0). Music sits at 0.18. SFX should be felt, not heard. If a viewer notices the whoosh, it's too loud.

2. **Click sounds: time the SFX 0.05–0.10 s AFTER the cursor pulse start, not before.** The brain registers the visual a few ms before the audio "syncs"; perfect alignment feels slightly off.

3. **Never stack 3+ SFX in the same 0.5 s window.** It becomes noise. Pick the strongest cue and drop the rest.

4. **Keep SFX files under 1 second each** (sub-bass impacts excepted, those can be 2–3 s). Long SFX bleed into the next phrase and muddy the voice.

5. **Sub-bass cues are 60–80 Hz** — they "feel" on phone speakers as a thump, not as audible sound. Don't substitute a mid-range "boom" sample; it competes with the voice.

## Tuning workflow

1. **Drop SFX files into `sfx/`** in your project folder.
2. **Write `sfx.json`** with rough timings (copy the palette above).
3. **Render** — `python scripts/record_video.py <project>`.
4. **Listen on phone speakers AND headphones.** Phone is the dominant viewing surface for vertical; headphones reveal layering issues.
5. **Adjust `time` and `volume`** and re-render. Each iteration is ~30 s per format.

## Common mistakes

| Symptom | Cause | Fix |
|---|---|---|
| Whoosh feels "before" the transition | `time` set to when the next slide *starts* | Whooshes should fire 0.1–0.3 s **before** the slide transition, not at it |
| Click sounds disconnected from cursor | Cursor pulse is at `8.7s` but `time: 8.7` is exactly the pulse peak | Try `time: 8.78` (the click "lands" after the pulse) |
| Sub-bass clips the voice | Voice and bass overlap at the same instant | Move sub-bass to a beat with no voice, or drop its `volume` to 0.35 |
| FFmpeg warns about input duration | SFX file longer than expected | Trim the SFX file itself, or shorten its tail with a fade — the pipeline doesn't trim SFX inputs |
| One cue silently missing in the render | `file` path typo → script printed warning and skipped | Re-read the render log for `WARNING: sfx file not found` lines |

## Quick smoke test

A 3-cue minimal `sfx.json` to verify the pipeline picks it up at all:

```json
[
  { "file": "sfx/test-beep.mp3", "time": 1.0, "volume": 0.5 }
]
```

If the resulting MP4 has the beep at 1 s past the first visible frame, the SFX layer is wired correctly. From there, swap in real cues.
