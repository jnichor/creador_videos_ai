"""
Discovers subpages from a website's nav/header for the multi-page video tour.
Usage: python discover_pages.py https://client.com
Prints up to 4 same-origin URLs as JSON.
"""
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python discover_pages.py <url>", file=sys.stderr)
    sys.exit(1)

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
    if parsed.netloc != origin:
        continue
    if parsed.fragment:
        continue
    if parsed.path in ("", "/"):
        continue
    key = parsed.path.rstrip("/")
    if key in seen:
        continue
    seen.add(key)
    unique.append(h)

print(json.dumps(unique[:4], indent=2))
