# Troubleshooting

The 10 most common bugs and their fixes. Copied from the SKILL's error patterns table — Claude Code reads the skill, but if you're running the pipeline manually, read this.

## 1. White/blank frame at start

**Symptom**: First 0.5-2 seconds of the output MP4 are pure white.

**Cause**: The iframe is still loading when recording starts.

**Fix**:
- Verify your iframe has `onload="window.iframe1Loaded=true"` attribute
- Verify `record_video.py` waits for `window.iframe1Loaded === true` before calling `window.startSlideshow()`
- The `-ss <offset>` trim in FFmpeg should match the slideshow start offset

## 2. Misframed page (sides cropped)

**Symptom**: Right or left edge of the website UI is cut off.

**Cause**: iframe `width` doesn't match the wrapper, or you're using `margin-left: -420px` for cropping when the site is responsive.

**Fix**:
- Set `iframe { width: 1080px; }` (matching the wrapper)
- Remove any `margin-left: -420px` unless the target site only renders correctly at 1920px
- Test in browser first by opening the HTML directly

## 3. Sudden white page mid-video

**Symptom**: A bright/light page flashes between two dark pages.

**Cause**: A subpage in the multi-page tour has a white/light background that breaks the dark cinematic flow.

**Fix**:
- Remove that subpage from the tour — keep only pages with consistent background
- OR apply CSS overlay: `iframe { filter: invert(1); }` (changes brand colors though — usually worse)
- OR use a screenshot with Ken Burns instead of an iframe for that page

## 4. Cursor invisible

**Symptom**: At the click moment, no cursor visible (especially on white/light pages).

**Cause**: White SVG fill blends with the background.

**Fix**: Cursor SVG must have:
```html
<svg class="fake-cursor" ...>
  <path fill="white" stroke="black" stroke-width="3" stroke-linejoin="round" .../>
</svg>
```

```css
.fake-cursor {
  filter:
    drop-shadow(0 0 6px rgba(0, 0, 0, 0.9))
    drop-shadow(0 4px 10px rgba(0, 0, 0, 0.7));
}
```

Stroke ≥ 2.5px and DUAL drop-shadow are non-negotiable.

## 5. Cursor in empty space

**Symptom**: Cursor lands on background, not on a clickable element.

**Cause**: `left`/`top` values are estimates without runtime introspection of the iframe.

**Fix**: Adjust per-cursor `left`/`top` after the first render. Approximate (540, 850) for square (bottom-center hero CTA area) or (320, 60) for top-nav.

## 6. Subtitle text wrong

**Symptom**: Subtitle says "Y hay webs" but voice says "hay webs".

**Cause**: HTML subtitle text doesn't match what whisper.cpp actually transcribed.

**Fix**: Whisper transcript is truth. Update HTML subtitles to match the words in `transcript.json`. ElevenLabs sometimes drops words or adds them subtly — always trust whisper, not your original script.

## 7. Subtitle wrong timing (early or late vs voice)

**Symptom**: Subtitle appears 1-2 seconds before/after the voice says the phrase.

**Cause**: Trim offset miscalculated. `-ss <X>` is shifting the video relative to the audio.

**Fix**:
- Verify `record_video.py` measures `recording_start = time.time()` BEFORE `page.goto()` (not after)
- Verify `slideshow_start_offset = time.time() - recording_start` is calculated AFTER the `time.sleep(2.0)` grace period
- If drift persists, add an empirical buffer: `trim_value = slideshow_start_offset + 0.5` (test values 0.0-1.5 to find the right one for your machine)

## 8. Music abrupt cut at voice end

**Symptom**: Background music stops at ~23s when voice ends, but the CTA continues.

**Cause**: FFmpeg used `-shortest` instead of `amix duration=longest`.

**Fix**: Replace the FFmpeg filter with:
```
[1:a]volume=1.0[voice];[2:a]volume=0.18[bgm];[voice][bgm]amix=inputs=2:duration=longest[mixed]
```

`-map "[mixed]"` for audio, no `-shortest` flag.

## 9. White flash 0-0.3s at start

**Symptom**: Brief white frame at the very beginning before content appears.

**Cause**: Recording captured the Chromium init flash, or iframe loading wasn't gated.

**Fix**:
- Ensure `-ss 0.3` minimum on FFmpeg video input
- Ensure iframe-load gating is working (`window.iframe1Loaded` checked before `startSlideshow()`)
- If using a slow network, increase the grace period: `time.sleep(3.0)` instead of `2.0`

## 10. Subtitle visible during CTA outro

**Symptom**: Last subtitle of voice off bleeds into the brand outro slide.

**Cause**: Missing `body.cta-active .subtitles { opacity: 0 }` rule, or the slideshow scheduler isn't adding the `cta-active` class.

**Fix**:
```css
body.cta-active .subtitles { opacity: 0; transition: opacity 0.6s ease; }
body.cta-active .fake-cursor { opacity: 0 !important; }
```

And in JS scheduler:
```js
if (slides[current].classList.contains('cta-slide')) {
  document.body.classList.add('cta-active');
}
```

## QA review process — catches all of the above

After every render, extract frames at critical timestamps and inspect them visually:

```bash
FFMPEG=$(python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())")
mkdir -p qa-frames
for t in 0.3 1.5 4.5 8.6 9.0 13.0 18.5 22.5 24.0; do
  "$FFMPEG" -y -ss "$t" -i output/marketing-square.mp4 -frames:v 1 -q:v 2 "qa-frames/t${t}.png"
done
```

Then open each PNG and check against the patterns above. Iterate until clean — never declare a render done without visual inspection.

(If you're using Claude Code with the skill installed, this QA process runs automatically per rule #19 of the skill.)
