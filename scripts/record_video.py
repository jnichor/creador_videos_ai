"""
Record both square (1080×1080) and vertical (1080×1920) marketing videos
for a given project folder.

Pipeline (per format):
  1. Playwright headless Chromium opens the HTML
  2. Wait for iframe load (gates the slideshow trigger)
  3. Capture ~30 seconds while the slideshow auto-plays
  4. FFmpeg muxes silent video + voiceover.mp3 (100%) + music.mp3 (18%)

Project folder structure expected:
  <project>/
    voiceover.mp3
    music.mp3
    <client>-logo.png
    square.html               (or video-marketing-services.html)
    vertical.html             (or video-marketing-services-vertical.html)
    output/                   (created if missing)

Usage:
  python record_video.py <project-folder>             # both formats
  python record_video.py <project-folder> square      # only square
  python record_video.py <project-folder> vertical    # only vertical
"""

from playwright.sync_api import sync_playwright
import time
import subprocess
import shutil
import sys
from pathlib import Path

# Total slideshow duration:
#   Home (9000) + Productos (14000) + CTA (5000) = 28000ms
# +2s buffer for final fade
TOTAL_DURATION_SEC = 28 + 2


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


def _resolve_html(project: Path, fmt_name: str):
    """Find the HTML file for a given format, supporting common naming conventions."""
    candidates = [
        f"{fmt_name}.html",
        f"video-marketing-services{'-vertical' if fmt_name == 'vertical' else ''}.html",
    ]
    for c in candidates:
        p = project / c
        if p.exists():
            return p
    return None


def record_format(project: Path, fmt_name: str, fmt: dict) -> bool:
    """Record one format end-to-end (Playwright capture + FFmpeg mux)."""
    html_path = _resolve_html(project, fmt_name)
    if not html_path:
        print(f"  ERROR: no HTML found for {fmt_name} in {project}")
        return False

    voiceover = project / "voiceover.mp3"
    music = project / "music.mp3"
    output_dir = project / "output"
    output_dir.mkdir(exist_ok=True)
    raw_webm = project / f"marketing-raw-{fmt_name}.webm"
    final_mp4 = output_dir / f"marketing-{fmt_name}.mp4"

    if not voiceover.exists():
        print(f"  ERROR: {voiceover} not found.")
        return False

    width = fmt["width"]
    height = fmt["height"]

    print(f"\n=== {fmt_name.upper()} ({width}x{height}) ===")
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

        slideshow_start_offset = time.time() - recording_start
        page.evaluate("window.startSlideshow && window.startSlideshow()")
        print(f"  Slideshow started at recording offset = {slideshow_start_offset:.2f}s")

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

    # Mux audio
    print("  Muxing audio (voice 100% + music 18%)...")

    # -ss <offset> trims the iframe-loading warm-up frames from the recording.
    # Applied ONLY to the video input — voice and music still start at 0, so the
    # voice off aligns with the slideshow's internal t=0.
    trim_value = f"{slideshow_start_offset:.3f}"
    print(f"  Trimming first {trim_value}s of video (load warm-up)")

    if not music.exists():
        print(f"  WARNING: {music.name} not found. Output will have voice only.")
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", trim_value, "-i", str(raw_webm),
            "-i", str(voiceover),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-shortest",
            str(final_mp4),
        ]
    else:
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", trim_value, "-i", str(raw_webm),
            "-i", str(voiceover),
            "-i", str(music),
            "-filter_complex",
            "[1:a]volume=1.0[voice];"
            "[2:a]volume=0.18[bgm];"
            "[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=2[mixed]",
            "-map", "0:v", "-map", "[mixed]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-shortest",                # video is the canonical length, not the music
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


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    project = Path(args[0]).resolve()
    if not project.is_dir():
        print(f"ERROR: project folder not found: {project}")
        sys.exit(1)

    requested = args[1:] if len(args) > 1 else list(FORMATS.keys())

    results = {}
    for fmt_name in requested:
        if fmt_name not in FORMATS:
            print(f"  WARNING: unknown format '{fmt_name}', skipping")
            continue
        results[fmt_name] = record_format(project, fmt_name, FORMATS[fmt_name])

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for fmt_name, ok in results.items():
        status = "[OK]   " if ok else "[FAIL] "
        print(f"  {status}{fmt_name}")


if __name__ == "__main__":
    main()
