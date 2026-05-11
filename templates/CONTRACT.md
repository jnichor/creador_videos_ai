# Template Contract

Any HTML template under `templates/` must respect this contract so the **style packs** (`cinematic` / `bold` / `editorial` / `tech`) and the **channel variants** (`tiktok` / `linkedin` / `youtube`) apply correctly, and so `scripts/record_video.py` can record + trim it.

Break the contract and the recorder still runs, but: packs stop re-skinning the template, subtitles desync, or the marker scan fails and the trim falls back to wall-clock (lossy).

---

## 1. File naming

```
templates/<template-name>-<format>.html
```

- `<template-name>` matches an entry in `SUPPORTED_TEMPLATES` in [scripts/record_video.py](../scripts/record_video.py)
- `<format>` is `square` or `vertical`

Example: `multi-product-square.html`, `tour-pages-vertical.html`.

## 2. Required JavaScript

```js
window.startSlideshow = function() {
  if (window.__slideshowStarted) return;     // idempotent guard
  window.__slideshowStarted = true;

  // 6×6 magenta sync marker at top-right — recorder uses this to find t=0
  const m = document.createElement('div');
  m.id = '__sync-marker';
  m.style.cssText =
    'position:fixed;top:0;right:0;width:6px;height:6px;' +
    'background:#FF00FF;z-index:99999;pointer-events:none;';
  document.body.appendChild(m);
  requestAnimationFrame(() => requestAnimationFrame(() => m.remove()));

  // unpause animations + kick the slide scheduler
  document.documentElement.classList.remove('slideshow-paused');
  setTimeout(next, parseInt(slides[0].dataset.duration));
};
```

**Why every part matters:**

- `__slideshowStarted` guard → the HTML has a 5s dev-preview fallback that calls `startSlideshow()` from a `setTimeout`. Without the guard, the slideshow fires twice (once from Python, once from the fallback) and the trim offset is wrong.
- Magenta marker → `_find_sync_marker_offset()` in record_video.py scans the raw webm for the first magenta-ish frame and uses its timestamp as the trim offset. This is **ground truth** — without it, the recorder falls back to `time.time()` which is off by Playwright's recording-onset delay (sometimes 2-3 seconds).
- `requestAnimationFrame × 2` → keeps the marker on screen for 2 frames so the scan reliably picks it up despite VP8 chroma subsampling.

## 3. Required iframe-load signal

The **first** slide's iframe must have:

```html
<iframe class="page-1" ... onload="window.iframe1Loaded=true"></iframe>
```

`record_video.py` waits up to 10s for `window.iframe1Loaded === true` before calling `startSlideshow()` — that's how it avoids capturing white "loading" frames.

## 4. Required CSS classes

The packs target these selectors. If your template omits or renames any of them, the corresponding pack override stops working:

| Class | Where | Used by |
|---|---|---|
| `.slide` | every slide root | base scheduler + pack transitions |
| `.demo-slide` | iframe slides (everything except CTA) | base styles for the iframe wrapper |
| `.cta-slide` | final CTA slide | `body.cta-active` toggle that hides subtitles |
| `.demo-frame-wrapper` | div around each iframe | vignette / letterbox / scanline overlays via `::after` |
| `.cta-logo-card` | logo container inside `.cta-slide` | base styling, packs don't override |
| `.cta-eyebrow` | "CONTACTO" label above the tagline | packs override color + ::before/::after |
| `.cta-conversemos` | tagline in `.cta-slide` | packs override font + color |
| `.cta-pill` | phone/contact pill in `.cta-slide` | packs override background + border |
| `.sub` | each subtitle wrapper | packs override font + bg + entrance animation |
| `.sub-1` … `.sub-N` | per-line subtitle classes with timing | scheduler-independent CSS animations |
| `.subtitles` | container for `.sub` elements | base layout, `body.channel-tiktok` shifts position |
| `.fake-cursor` | optional pointer overlay | base styling, no pack override |
| `.callout` / `.callout--ring` / `.callout--box` / `.callout--stat` | optional motion overlays | packs override color + animation |

## 5. Slide scheduler

The default scheduler (copy-paste into your template):

```js
const slides = document.querySelectorAll('.slide');
let current = 0;
function next() {
  current++;
  if (current < slides.length) {
    slides.forEach(s => s.classList.remove('active'));
    slides[current].classList.add('active');
    if (slides[current].classList.contains('cta-slide')) {
      document.body.classList.add('cta-active');
    }
    setTimeout(next, parseInt(slides[current].dataset.duration));
  }
}
```

Each `.slide` must declare `data-duration="<ms>"`. The **sum of all `data-duration` values must equal 28000ms** (28s) — that matches `TOTAL_DURATION_SEC = 28 + 2` in [record_video.py:49](../scripts/record_video.py#L49). The remaining 2s is buffer for the final fade.

If your template needs a different total, change `TOTAL_DURATION_SEC` in the recorder too. Don't quietly desync them — the recorder cuts the audio at 28s and the final frames will be muted.

## 6. Subtitle timing

Subtitles animate via CSS keyframes, not the JS scheduler. Each `.sub-N` declares its own `forwards <delay>s` for entrance + exit:

```css
.sub-1 { animation: subFadeIn 0.18s ease-out forwards 0.10s,
                    subFadeOut 0.22s ease-in  forwards 2.00s; }
```

- Delays are relative to **slideshow start (t=0)**, not to the previous slide.
- Keep at least a 0.1s gap between consecutive subs to avoid stacking.
- The total time spanned by `.sub-1` … `.sub-N` should end **before the CTA slide starts**, otherwise the CTA hides the subs mid-animation (the `body.cta-active` rule fades them out).

## 7. Style-pack pause gate

Add this at the head of your `<script>` block so the pause class is set before any animations kick in:

```js
document.documentElement.classList.add('slideshow-paused');
const styleEl = document.createElement('style');
styleEl.textContent =
  ".slideshow-paused .demo-slide.active .page-1," +
  ".slideshow-paused .demo-slide.active .page-2," +
  ".slideshow-paused .fake-cursor," +
  ".slideshow-paused .sub { animation-play-state: paused !important; }";
document.head.appendChild(styleEl);
```

`startSlideshow()` removes the `slideshow-paused` class. Without this gate, iframe-internal animations (scroll-tour, cursor moves) start during the iframe-loading wait and the user sees a partial animation already in progress on the first frame.

## 8. Placeholder convention

Templates use `{{PLACEHOLDER}}` markers that Claude replaces when scaffolding a client project. Per-template placeholders:

- **`tour-pages`** → `{{HOME_URL}}`, `{{PRODUCTS_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`
- **`multi-product`** → `{{HOME_URL}}`, `{{CATALOG_URL}}`, `{{URL_1}}`, `{{URL_2}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`
- **`single-page-tour`** → `{{PAGE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`
- **`feature-spotlight`** → `{{PAGE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`
- **`split-mobile-desktop`** → `{{DESKTOP_URL}}`, `{{MOBILE_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`
- **`before-after`** → `{{BEFORE_URL}}`, `{{AFTER_URL}}`, `{{LOGO_FILENAME}}`, `{{CLIENT_NAME}}`, `{{CTA_TAGLINE}}`, `{{CTA_PHONE}}`

When you add a template, document its placeholder set in the template's top comment and in [README.md](README.md).

---

## Adding a new template — checklist

1. Pick a name. Add it to `SUPPORTED_TEMPLATES` in [scripts/record_video.py](../scripts/record_video.py).
2. Create `templates/<name>-square.html` and `templates/<name>-vertical.html` (copy `tour-pages-*` as a starting point — every contract requirement is already satisfied there).
3. Edit only what changes structurally (number of slides, durations, placeholders, subtitle count + timings).
4. Don't touch the 4 style-pack CSS blocks (`body.style-bold`, `body.style-editorial`, `body.style-tech`, base) unless you're explicitly changing how that pack reads on this template.
5. Render once with each pack to confirm the visuals carry over: `python scripts/record_video.py <test-project> --template <name> --style bold` (and repeat for editorial / tech).
6. Document the placeholder set in [README.md](README.md).
