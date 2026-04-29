"""
Extract individual Digimon sprites from downloaded sprite sheets.

HOW TO USE:
1. Visit Spriters Resource and download sprite sheets manually (Cloudflare blocks bots).
   Best sources for Digimon sprites:
     - https://www.spriters-resource.com/playstation/digimonrumblearena/
       (individual character sheets with idle/attack poses — best quality)
     - https://www.spriters-resource.com/playstation/digimonworld/
       (battle sprites for 100+ original Digimon)
     - https://www.spriters-resource.com/game_boy_advance/digimonbattlespirit/
       (GBA sprites, many Digimon)
     - https://www.spriters-resource.com/game_boy_advance/digimonbattlespirit2/
     - https://www.spriters-resource.com/playstation2/digimonrumblearena2/

2. Save the PNG sheet files to:  tools/sheets/<DigimonName>.png
   Example:  tools/sheets/Agumon.png
             tools/sheets/Gabumon.png

3. Run this tool:
     python tools/extract_sprites.py                     # process all sheets
     python tools/extract_sprites.py --sheet Agumon.png  # one sheet
     python tools/extract_sprites.py --sheet Agumon.png --index 0  # pick frame by index
     python tools/extract_sprites.py --show Agumon.png   # show detected sprites (debug)

4. Sprites are saved to: game/assets/sprites/<name>.png (128x128, RGBA)

Options:
  --sheet FILE    Process a specific sheet file in tools/sheets/
  --index N       Which sprite frame to use (default: 0 = first/largest)
  --size N        Output size in pixels (default: 128)
  --show          Preview detected sprite bounding boxes (requires display)
  --min-px N      Minimum non-transparent pixels to count as a sprite (default: 100)
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow is required: pip install Pillow")
    sys.exit(1)

SHEETS_DIR = Path(__file__).parent / "sheets"
SPRITES_DIR = Path(__file__).parent.parent / "game" / "assets" / "sprites"
DEFAULT_SIZE = 128
MIN_PIXELS = 100


def find_sprites(img: Image.Image, min_pixels: int = MIN_PIXELS) -> list[tuple[int,int,int,int]]:
    """
    Return list of (x1, y1, x2, y2) bounding boxes for non-transparent regions.
    Uses connected-component flood fill on the alpha channel.
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    alpha = img.split()[3]
    width, height = img.size
    pixels = alpha.load()

    visited = [[False] * height for _ in range(width)]
    boxes = []

    def flood(sx, sy):
        stack = [(sx, sy)]
        min_x, min_y, max_x, max_y = sx, sy, sx, sy
        count = 0
        while stack:
            x, y = stack.pop()
            if x < 0 or x >= width or y < 0 or y >= height:
                continue
            if visited[x][y]:
                continue
            if pixels[x, y] < 10:  # mostly transparent
                continue
            visited[x][y] = True
            count += 1
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            stack.extend([(x+1,y),(x-1,y),(x,y+1),(x,y-1)])
        return (min_x, min_y, max_x, max_y, count)

    for x in range(width):
        for y in range(height):
            if not visited[x][y] and pixels[x, y] >= 10:
                x1, y1, x2, y2, count = flood(x, y)
                if count >= min_pixels:
                    boxes.append((x1, y1, x2, y2))

    # Sort by area descending so index 0 = largest sprite
    boxes.sort(key=lambda b: (b[2]-b[0]) * (b[3]-b[1]), reverse=True)
    return boxes


def crop_sprite(img: Image.Image, box: tuple, out_size: int, padding: int = 4) -> Image.Image:
    """Crop a sprite from a box, center it on a square canvas, resize to out_size."""
    x1, y1, x2, y2 = box
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(img.width, x2 + padding)
    y2 = min(img.height, y2 + padding)

    cropped = img.crop((x1, y1, x2, y2))
    w, h = cropped.size
    side = max(w, h)

    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    paste_x = (side - w) // 2
    paste_y = (side - h) // 2
    canvas.paste(cropped, (paste_x, paste_y))

    return canvas.resize((out_size, out_size), Image.LANCZOS)


def sheet_name_to_digi_name(sheet_path: Path) -> str:
    """Convert sheet filename to a safe sprite filename."""
    stem = sheet_path.stem
    # Normalize: lowercase, spaces/dashes to underscore
    safe = stem.lower().replace(" ", "_").replace("-", "_")
    import re
    safe = re.sub(r"[^a-z0-9_]", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe


def process_sheet(sheet_path: Path, index: int, out_size: int, min_pixels: int) -> bool:
    img = Image.open(sheet_path).convert("RGBA")
    sprites = find_sprites(img, min_pixels)

    if not sprites:
        print(f"  No sprites detected in {sheet_path.name}")
        return False

    if index >= len(sprites):
        print(f"  Sheet has {len(sprites)} sprites, index {index} out of range — using 0")
        index = 0

    box = sprites[index]
    sprite_img = crop_sprite(img, box, out_size)

    safe_name = sheet_name_to_digi_name(sheet_path)
    out_path = SPRITES_DIR / f"{safe_name}.png"
    sprite_img.save(out_path)
    print(f"  {sheet_path.name} -> {out_path.name}  ({len(sprites)} sprites found, used #{index})")
    return True


def show_sheet(sheet_path: Path, min_pixels: int):
    """Draw bounding boxes on the sheet and display it."""
    img = Image.open(sheet_path).convert("RGBA")
    sprites = find_sprites(img, min_pixels)

    overlay = img.copy().convert("RGBA")
    draw = ImageDraw.Draw(overlay)
    for i, (x1, y1, x2, y2) in enumerate(sprites):
        draw.rectangle([x1, y1, x2, y2], outline=(255, 0, 0, 255), width=2)
        draw.text((x1 + 2, y1 + 2), str(i), fill=(255, 255, 0, 255))

    print(f"  {len(sprites)} sprites detected in {sheet_path.name}")
    overlay.show()


def main():
    parser = argparse.ArgumentParser(description="Extract Digimon sprites from sprite sheets.")
    parser.add_argument("--sheet", type=str, default=None, help="Sheet filename in tools/sheets/")
    parser.add_argument("--index", type=int, default=0, help="Which sprite frame to use (default 0)")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="Output size in px (default 128)")
    parser.add_argument("--show", action="store_true", help="Show detected bounding boxes")
    parser.add_argument("--min-px", type=int, default=MIN_PIXELS, dest="min_px",
                        help="Min pixels for a region to count as sprite (default 100)")
    args = parser.parse_args()

    SHEETS_DIR.mkdir(exist_ok=True)
    SPRITES_DIR.mkdir(parents=True, exist_ok=True)

    if args.sheet:
        sheet_path = SHEETS_DIR / args.sheet
        if not sheet_path.exists():
            print(f"Sheet not found: {sheet_path}")
            sys.exit(1)
        if args.show:
            show_sheet(sheet_path, args.min_px)
        else:
            process_sheet(sheet_path, args.index, args.size, args.min_px)
        return

    sheets = sorted(SHEETS_DIR.glob("*.png"))
    if not sheets:
        print(f"No PNG sheets found in {SHEETS_DIR}")
        print("Download sprite sheets from Spriters Resource and save them to tools/sheets/")
        print("See the docstring at the top of this file for URLs and instructions.")
        return

    ok = fail = 0
    for sheet in sheets:
        if process_sheet(sheet, args.index, args.size, args.min_px):
            ok += 1
        else:
            fail += 1

    print(f"\nDone. {ok} sprites extracted, {fail} failed.")
    print(f"Sprites saved to: {SPRITES_DIR}")


if __name__ == "__main__":
    main()
