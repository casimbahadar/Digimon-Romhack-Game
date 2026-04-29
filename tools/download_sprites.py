"""
Download Digimon sprites from the Digimon wiki (digimon.fandom.com).
Saves 128x128 PNG thumbnails to game/assets/sprites/<name>.png.

Usage:
    python tools/download_sprites.py              # all Digimon
    python tools/download_sprites.py --limit 50   # first 50 only
    python tools/download_sprites.py --name Agumon  # one specific Digimon
"""

import argparse
import json
import os
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

SPRITE_DIR = Path(__file__).parent.parent / "game" / "assets" / "sprites"
DIGIMON_JSON = Path(__file__).parent.parent / "game" / "data" / "digimon.json"
WIKI_API = "https://digimon.fandom.com/api.php"
THUMB_SIZE = 128
DELAY = 1.1  # seconds between requests

def safe_filename(name: str) -> str:
    """Convert a Digimon name to a safe filename."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name + ".png"

def fetch_image_url(name: str) -> str | None:
    """Query the wiki API for the main image of a Digimon page."""
    params = urllib.parse.urlencode({
        "action": "query",
        "titles": name,
        "prop": "pageimages",
        "format": "json",
        "pithumbsize": THUMB_SIZE,
        "pilicense": "any",
    })
    url = f"{WIKI_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DigimonFanGame/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            thumb = page.get("thumbnail", {})
            if thumb.get("source"):
                return thumb["source"]
    except Exception as e:
        print(f"  API error for {name!r}: {e}")
    return None

def download_image(url: str, dest: Path) -> bool:
    """Download an image URL to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DigimonFanGame/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return True
    except Exception as e:
        print(f"  Download error: {e}")
        return False

def process(name: str, force: bool = False) -> bool:
    dest = SPRITE_DIR / safe_filename(name)
    if dest.exists() and not force:
        return True  # already have it

    img_url = fetch_image_url(name)
    if not img_url:
        print(f"  No image found for: {name}")
        return False

    ok = download_image(img_url, dest)
    if ok:
        print(f"  Saved {name} → {dest.name}")
    return ok

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--name", type=str, default=None)
    parser.add_argument("--force", action="store_true", help="Re-download existing sprites")
    args = parser.parse_args()

    SPRITE_DIR.mkdir(parents=True, exist_ok=True)

    if args.name:
        process(args.name, force=args.force)
        return

    digimon = json.loads(DIGIMON_JSON.read_text())
    if args.limit:
        digimon = digimon[:args.limit]

    already = sum(1 for d in digimon if (SPRITE_DIR / safe_filename(d["name"])).exists())
    print(f"Downloading sprites for {len(digimon)} Digimon ({already} already cached)...")

    ok = fail = 0
    for i, d in enumerate(digimon):
        dest = SPRITE_DIR / safe_filename(d["name"])
        if dest.exists() and not args.force:
            ok += 1
            continue
        print(f"[{i+1}/{len(digimon)}] {d['name']}")
        if process(d["name"], force=args.force):
            ok += 1
        else:
            fail += 1
        time.sleep(DELAY)

    print(f"\nDone. {ok} sprites saved, {fail} failed.")
    print(f"Sprites at: {SPRITE_DIR}")

if __name__ == "__main__":
    main()
