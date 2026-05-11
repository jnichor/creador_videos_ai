"""
Record both square (1080×1080) and vertical (1080×1920) marketing videos
for a given project folder.

Pipeline (per format):
  1. Playwright headless Chromium opens the HTML
  2. Wait for iframe load (gates the slideshow trigger)
  3. Capture ~30 seconds while the slideshow auto-plays
  4. FFmpeg muxes silent video + voiceover.mp3 (100%) + music.mp3 (18%)
     + optional SFX cues from sfx.json (whoosh, click, sub-bass, ...)

Project folder structure expected:
  <project>/
    voiceover.mp3
    music.mp3
    <client>-logo.png
    square.html               (or video-marketing-services.html)
    vertical.html             (or video-marketing-services-vertical.html)
    sfx.json                  (OPTIONAL — sound-design cues; see docs/sound-design.md)
    sfx/*.mp3                 (OPTIONAL — referenced by sfx.json)
    output/                   (created if missing)

Usage:
  python record_video.py <project-folder>                                  # both formats, defaults
  python record_video.py <project-folder> square                           # only square
  python record_video.py <project-folder> --style bold                     # bold pack
  python record_video.py <project-folder> --channel tiktok                 # TikTok placement
  python record_video.py <project-folder> --template multi-product         # multi-product template
  python record_video.py <project-folder> vertical --template multi-product --style bold --channel tiktok

Templates (--template <name>): tour-pages | multi-product
  - tour-pages (default): 3 slides (home → products → CTA). Web with pages.
  - multi-product:        5 product iframes + CTA. Ecommerce / catalogue / SaaS features.

Style packs (--style <name>): cinematic | bold | editorial | tech
  - cinematic (default): dark navy + cyan, restrained — SaaS / B2B / agencies
  - bold:                magenta + warm, punchy entrances — D2C / lifestyle / retail
  - editorial:           warm sepia + serif, letterbox, lower-third subs — content brands
  - tech:                matrix-green mono, scanlines, glitch reveals — AI / dev tools
"""

from playwright.sync_api import sync_playwright
import time
import subprocess
import shutil
import sys
import json
from pathlib import Path

# Total slideshow duration:
#   Home (9000) + Productos (14000) + CTA (5000) = 28000ms
# +2s buffer for final fade
TOTAL_DURATION_SEC = 28 + 2

# Recognised channel variants — applied as a body class via Playwright before
# the slideshow starts, so CSS rules like .channel-tiktok .subtitles can shift
# placement per social platform without duplicating the template.
SUPPORTED_CHANNELS = {"default", "tiktok", "linkedin", "youtube"}

# Visual style packs — applied as body.style-<name>. A "pack" is a coherent
# set of design decisions (transitions, typography, palette, callout entrance)
# served to a brand personality, not a buffet of toggles.
#   cinematic — default. Dark navy + cyan, drone landing, linear scroll,
#               restrained crossfades. For SaaS / B2B / agencies.
#   bold      — magenta + warm palette, punch transitions, pop subtitles,
#               elastic stat callouts. For ecommerce / D2C / lifestyle.
#   editorial — warm sepia + serif italic, letterbox bars, lower-third
#               subtitle band, slow cross-dissolves. For content brands /
#               podcasts / thought leadership.
#   tech      — matrix-green + monospace, scanline overlay, glitch-step
#               subtitle reveal, terminal-style CTA with `> ` prefix.
#               For AI / dev tools / cybersecurity.
SUPPORTED_STYLES = {"cinematic", "bold", "editorial", "tech"}

# Structural templates — applied via --template <name>. A template defines
# the HTML structure (number of slides, layout, scheduler behavior). It is
# orthogonal to style packs: any template × any pack combination works as
# long as the template respects the base contract (see templates/CONTRACT.md):
#   - .slide / .cta-slide / .demo-slide classes
#   - .sub / .sub-N subtitle elements
#   - .cta-eyebrow / .cta-conversemos / .cta-pill in the final slide
#   - window.startSlideshow() with magenta sync marker injection
#   - data-duration attribute on each .slide
#
# tour-pages       (default) — 3 slides: home + products + CTA. Web with pages.
# multi-product    — 5 slides: home + catalogue + product 1 + product 2 + CTA.
#                    Ecommerce / catalogue / brands featuring specific products.
# single-page-tour — 2 slides: ONE long-form page (23s scroll-tour) + CTA.
#                    SaaS landings / one-pagers where everything lives in /.
# feature-spotlight — 4 slides: 3 zoom-and-hold spotlights on the same URL + CTA.
#                     Landings with 3 key features/sections to highlight.
# split-mobile-desktop — 2 slides: side-by-side mobile + desktop iframes + CTA.
#                       Agencies showing responsive design / multi-device support.
# before-after     — 2 slides: side-by-side BEFORE / AFTER iframes with animated
#                    vertical divider + CTA. Redesigns / migrations / rebrands.
SUPPORTED_TEMPLATES = {
    "tour-pages", "multi-product", "single-page-tour",
    "feature-spotlight", "split-mobile-desktop", "before-after",
}


def _load_sfx(project: Path):
    """Read optional sfx.json. Schema:
        [
          {"file": "whoosh.mp3", "time": 8.7, "volume": 0.4},
          ...
        ]
    Returns a list of dicts (possibly empty) with absolute file paths resolved
    against the project folder. Entries with a missing audio file are dropped
    with a warning so a broken SFX never aborts the whole render.
    """
    sfx_path = project / "sfx.json"
    if not sfx_path.exists():
        return []
    try:
        raw = json.loads(sfx_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"  WARNING: sfx.json is not valid JSON ({e}). Skipping SFX layer.")
        return []
    if not isinstance(raw, list):
        print("  WARNING: sfx.json must be a JSON array. Skipping SFX layer.")
        return []
    cleaned = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        fname = entry.get("file")
        t = entry.get("time")
        vol = entry.get("volume", 0.4)
        if not fname or t is None:
            print(f"  WARNING: sfx[{i}] missing 'file' or 'time'. Skipping.")
            continue
        fpath = (project / fname).resolve()
        if not fpath.exists():
            print(f"  WARNING: sfx file not found: {fpath.name}. Skipping.")
            continue
        cleaned.append({"file": fpath, "time": float(t), "volume": float(vol)})
    return cleaned


def _build_filter_complex(has_music: bool, sfx_entries: list):
    """Compose the FFmpeg -filter_complex string for audio mixing.

    Inputs in order:
      [0]  raw webm video       (trimmed by -ss)
      [1]  voiceover.mp3
      [2]  music.mp3            (optional)
      [3+] sfx files            (optional, any number)

    Output label is always [mixed]. SFX timing is in slideshow-time (t=0 at the
    slideshow's first frame, which is what the user sees in the final MP4 after
    the -ss trim) — we feed audio inputs without trim, so we just delay each
    SFX by sfx.time * 1000 ms.
    """
    parts = ["[1:a]volume=1.0[voice]"]
    mix_inputs = ["[voice]"]
    if has_music:
        parts.append("[2:a]volume=0.18[bgm]")
        mix_inputs.append("[bgm]")
    base_idx = 3 if has_music else 2
    for i, sfx in enumerate(sfx_entries):
        delay_ms = max(0, int(sfx["time"] * 1000))
        label = f"sfx{i}"
        parts.append(
            f"[{base_idx + i}:a]adelay={delay_ms}|{delay_ms},"
            f"volume={sfx['volume']:.3f}[{label}]"
        )
        mix_inputs.append(f"[{label}]")
    n = len(mix_inputs)
    parts.append(
        "".join(mix_inputs)
        + f"amix=inputs={n}:duration=longest:dropout_transition=2:normalize=0[mixed]"
    )
    return ";".join(parts)


def _find_sync_marker_offset(raw_webm: Path, width: int, ffmpeg: str):
    """Scan the raw webm for the magenta sync marker (6x6 pixel block in the
    top-right corner) that the HTML's startSlideshow() injects at slideshow
    t=0. Returns the webm-time (in seconds) of the first magenta frame, or
    None if not detected.

    Why this exists: relying on `time.time()` to measure the slideshow start
    offset doesn't work when (a) Playwright's recording onset lags wall-clock,
    or (b) the HTML's 5s dev-preview fallback fires before Python's trigger
    (happens when the iframe loads slowly). The marker is the ground truth —
    detecting it in the webm pixel stream sidesteps both issues.

    Detection: crop a 10x10 region from the top-right corner (slightly larger
    than the 6x6 marker for tolerance to VP8 chroma subsampling and edge
    compression), read raw RGB, find the first frame whose AVERAGE pixel is
    magenta-ish (R high, G low, B high). 10x10 chosen so chroma subsampling
    (YUV 4:2:0 -> 2x2 sample blocks) doesn't blur the marker entirely.
    """
    crop_w, crop_h = 10, 10
    crop_x = max(0, width - crop_w)
    try:
        result = subprocess.run(
            [
                ffmpeg, "-i", str(raw_webm),
                "-vf", f"crop={crop_w}:{crop_h}:{crop_x}:0",
                "-pix_fmt", "rgb24",
                "-f", "rawvideo",
                "-loglevel", "error",
                "-",
            ],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    data = result.stdout
    if not data:
        return None

    # We need the fps to convert frame index -> seconds. Webms from Playwright
    # Chromium are 25 fps by default; verify rather than assume.
    fps = 25
    try:
        probe = subprocess.run(
            [ffmpeg, "-i", str(raw_webm)],
            capture_output=True, text=True, check=False,
        )
        for line in probe.stderr.splitlines():
            if "fps" in line and "Stream" in line:
                # e.g. "... 25 fps, 25 tbr, ..."
                tokens = line.split(",")
                for tok in tokens:
                    tok = tok.strip()
                    if tok.endswith(" fps"):
                        try:
                            fps = float(tok.split()[0])
                        except ValueError:
                            pass
                break
    except Exception:
        pass

    bytes_per_frame = crop_w * crop_h * 3
    nframes = len(data) // bytes_per_frame
    for f in range(nframes):
        start = f * bytes_per_frame
        frame = data[start:start + bytes_per_frame]
        # Average channel values across the crop
        r_sum = sum(frame[0::3])
        g_sum = sum(frame[1::3])
        b_sum = sum(frame[2::3])
        n = crop_w * crop_h
        r, g, b = r_sum / n, g_sum / n, b_sum / n
        # Magenta-ish: R and B clearly elevated, G clearly suppressed.
        # Threshold tuned for VP8/H264 compressed corner of a 6x6 patch
        # inside a 10x10 sampling window (so ~36% of pixels are pure magenta,
        # the rest are dark vignette).
        if r > 90 and b > 90 and g < 70 and (r - g) > 40 and (b - g) > 40:
            return f / fps
    return None


def _find_ffmpeg() -> str:
    """Auto-detect ffmpeg in this priority:
    1. system PATH (winget/brew/apt install)
    2. imageio-ffmpeg bundled binary (pip install imageio-ffmpeg)
    3. fallback to "ffmpeg" string (will fail with clear error)
    """
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    return "ffmpeg"


FFMPEG_PATH = _find_ffmpeg()


def _resolve_html(project: Path, fmt_name: str, template: str = "tour-pages"):
    """Find the HTML file for a given format + template.

    Resolution order, first match wins:
      1. <template>-<fmt>.html             (e.g. multi-product-square.html)
      2. <fmt>.html                        (legacy — single template per project)
      3. video-marketing-services[-vertical].html  (legacy demo name)

    The legacy fallbacks (#2, #3) are kept ONLY for `template == "tour-pages"`
    so a user opting into a non-default template can't accidentally render a
    tour-pages HTML when their multi-product HTML is missing.
    """
    candidates = [f"{template}-{fmt_name}.html"]
    if template == "tour-pages":
        candidates += [
            f"{fmt_name}.html",
            f"video-marketing-services{'-vertical' if fmt_name == 'vertical' else ''}.html",
        ]
    for c in candidates:
        p = project / c
        if p.exists():
            return p
    return None


def record_format(project: Path, fmt_name: str, fmt: dict,
                  channel: str = "default", style: str = "cinematic",
                  template: str = "tour-pages") -> bool:
    """Record one format end-to-end (Playwright capture + FFmpeg mux)."""
    html_path = _resolve_html(project, fmt_name, template)
    if not html_path:
        print(f"  ERROR: no HTML found for {fmt_name} (template={template}) in {project}")
        return False

    voiceover = project / "voiceover.mp3"
    music = project / "music.mp3"
    output_dir = project / "output"
    output_dir.mkdir(exist_ok=True)
    parts = []
    if template != "tour-pages":
        parts.append(template)
    if style != "cinematic":
        parts.append(style)
    if channel != "default":
        parts.append(channel)
    suffix = ("-" + "-".join(parts)) if parts else ""
    raw_webm = project / f"marketing-raw-{fmt_name}{suffix}.webm"
    final_mp4 = output_dir / f"marketing-{fmt_name}{suffix}.mp4"

    if not voiceover.exists():
        print(f"  ERROR: {voiceover} not found.")
        return False

    width = fmt["width"]
    height = fmt["height"]
    sfx_entries = _load_sfx(project)

    print(f"\n=== {fmt_name.upper()} ({width}x{height}) "
          f"[template={template}, style={style}, channel={channel}] ===")
    if sfx_entries:
        print(f"  SFX layer: {len(sfx_entries)} cue(s) from sfx.json")
    print(f"Recording for {TOTAL_DURATION_SEC} seconds...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": width, "height": height},
            record_video_dir=str(project),
            record_video_size={"width": width, "height": height},
            device_scale_factor=1,
        )
        page = context.new_page()
        # Playwright starts recording when the context is created (above), not at goto.
        # Mark recording_start BEFORE goto for accurate trim alignment.
        recording_start = time.time()
        page.goto(f"file:///{html_path.as_posix()}")

        # Wait for the demo iframe (page-1) to fully load before triggering the slideshow.
        # The HTML's iframe has onload="window.iframe1Loaded=true" — this is reliable
        # because the attribute registers when the HTML parses, before the iframe's
        # network request begins (avoiding addEventListener race conditions).
        try:
            page.wait_for_function(
                "() => window.iframe1Loaded === true",
                timeout=10000,
            )
        except Exception as e:
            print(f"  WARNING: iframe load wait timed out: {e}. Continuing anyway.")

        # Extra grace period for fonts, images, lazy-loaded images, deferred scripts
        time.sleep(2.0)

        # Apply style + channel variant classes to <body>. CSS rules like
        # `.style-bold .sub { ... }` and `.channel-tiktok .subtitles { ... }`
        # then re-skin the template per pack / per platform without duplicating
        # the HTML. cinematic is the default and is always added explicitly so
        # selectors can target `body.style-cinematic` if needed.
        page.evaluate(
            f"document.body.classList.add('style-{style}')"
        )
        if channel != "default":
            page.evaluate(
                f"document.body.classList.add('channel-{channel}')"
            )

        wallclock_start_offset = time.time() - recording_start
        page.evaluate("window.startSlideshow && window.startSlideshow()")
        print(f"  Slideshow trigger sent at wall-clock offset = {wallclock_start_offset:.2f}s")

        time.sleep(TOTAL_DURATION_SEC)

        page.close()
        context.close()
        browser.close()

        # Find the most recent webm and rename it.
        # Windows holds the .webm file briefly after browser.close() — retry on PermissionError.
        webm_files = list(project.glob("*.webm"))
        latest = max(webm_files, key=lambda f: f.stat().st_mtime)
        if latest != raw_webm:
            if raw_webm.exists():
                raw_webm.unlink()
            for attempt in range(10):
                try:
                    latest.rename(raw_webm)
                    break
                except PermissionError:
                    time.sleep(0.5)
            else:
                raise PermissionError(f"Could not rename {latest} after 10 attempts")
        print(f"  Raw video: {raw_webm.name}")

    # Resolve the true slideshow-start offset. Prefer the magenta sync marker
    # baked into the recording (ground truth); fall back to wall-clock only
    # if the scan fails (e.g. ffmpeg can't crop, marker not visible).
    marker_offset = _find_sync_marker_offset(raw_webm, width, FFMPEG_PATH)
    if marker_offset is not None:
        slideshow_start_offset = marker_offset
        delta = marker_offset - wallclock_start_offset
        print(f"  Sync marker detected at {marker_offset:.3f}s "
              f"(wall-clock said {wallclock_start_offset:.3f}s, delta {delta:+.3f}s)")
    else:
        slideshow_start_offset = wallclock_start_offset
        print(f"  WARNING: sync marker not detected. Falling back to wall-clock "
              f"offset {wallclock_start_offset:.3f}s — trim may be off by ~0.1-0.5s.")

    # Mux audio
    has_music = music.exists()
    sfx_blurb = f" + {len(sfx_entries)} sfx" if sfx_entries else ""
    music_blurb = " + music 18%" if has_music else " (no music)"
    print(f"  Muxing audio (voice 100%{music_blurb}{sfx_blurb})...")
    if not has_music:
        print(f"  WARNING: {music.name} not found. Output will have voice only.")

    # -ss <offset> trims the iframe-loading warm-up frames from the recording.
    # Applied ONLY to the video input — audio inputs still start at 0, so the
    # voice off aligns with the slideshow's internal t=0. SFX timings in
    # sfx.json are likewise in slideshow-time and delayed via adelay.
    trim_value = f"{slideshow_start_offset:.3f}"
    print(f"  Trimming first {trim_value}s of video (load warm-up)")

    cmd = [FFMPEG_PATH, "-y", "-ss", trim_value, "-i", str(raw_webm),
           "-i", str(voiceover)]
    if has_music:
        cmd += ["-i", str(music)]
    for sfx in sfx_entries:
        cmd += ["-i", str(sfx["file"])]

    cmd += [
        "-filter_complex", _build_filter_complex(has_music, sfx_entries),
        "-map", "0:v", "-map", "[mixed]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-shortest",                    # video is the canonical length
        str(final_mp4),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  FFmpeg error: {e.stderr[-500:] if e.stderr else e}")
        return False

    print(f"  [OK] {final_mp4.relative_to(project)}")
    return True


# Format definitions
FORMATS = {
    "square": {"width": 1080, "height": 1080},
    "vertical": {"width": 1080, "height": 1920},
}


def _parse_args(argv):
    """Parse positional formats + optional --channel/--style/--template flags.
    Keeps the original flexible CLI: bare folder, folder + formats, folder +
    formats + flags in any order.
    """
    project_arg = None
    channel = "default"
    style = "cinematic"
    template = "tour-pages"
    fmts = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--channel":
            if i + 1 >= len(argv):
                print("ERROR: --channel requires a value")
                sys.exit(1)
            channel = argv[i + 1]
            i += 2
            continue
        if a == "--style":
            if i + 1 >= len(argv):
                print("ERROR: --style requires a value")
                sys.exit(1)
            style = argv[i + 1]
            i += 2
            continue
        if a == "--template":
            if i + 1 >= len(argv):
                print("ERROR: --template requires a value")
                sys.exit(1)
            template = argv[i + 1]
            i += 2
            continue
        if project_arg is None:
            project_arg = a
        else:
            fmts.append(a)
        i += 1
    return project_arg, fmts, channel, style, template


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    project_arg, requested, channel, style, template = _parse_args(args)
    if project_arg is None:
        print(__doc__)
        sys.exit(1)

    project = Path(project_arg).resolve()
    if not project.is_dir():
        print(f"ERROR: project folder not found: {project}")
        sys.exit(1)

    if channel not in SUPPORTED_CHANNELS:
        print(f"ERROR: unknown --channel '{channel}'. Supported: "
              f"{sorted(SUPPORTED_CHANNELS)}")
        sys.exit(1)

    if style not in SUPPORTED_STYLES:
        print(f"ERROR: unknown --style '{style}'. Supported: "
              f"{sorted(SUPPORTED_STYLES)}")
        sys.exit(1)

    if template not in SUPPORTED_TEMPLATES:
        print(f"ERROR: unknown --template '{template}'. Supported: "
              f"{sorted(SUPPORTED_TEMPLATES)}")
        sys.exit(1)

    if not requested:
        requested = list(FORMATS.keys())

    results = {}
    for fmt_name in requested:
        if fmt_name not in FORMATS:
            print(f"  WARNING: unknown format '{fmt_name}', skipping")
            continue
        results[fmt_name] = record_format(
            project, fmt_name, FORMATS[fmt_name], channel, style, template
        )

    print("\n" + "=" * 50)
    print(f"SUMMARY  [template={template}, style={style}, channel={channel}]")
    print("=" * 50)
    for fmt_name, ok in results.items():
        status = "[OK]   " if ok else "[FAIL] "
        print(f"  {status}{fmt_name}")


if __name__ == "__main__":
    main()
