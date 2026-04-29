"""
Map extracted sprite PNGs to Digimon names in the database.

After running extract_sprites.py you may have files like:
  game/assets/sprites/agumon_idle.png
  game/assets/sprites/wargreymon_sheet1.png

But the game expects:
  game/assets/sprites/agumon.png
  game/assets/sprites/wargreymon.png

This tool helps you:
  1. List which Digimon in the database are still missing sprites
  2. Rename / copy an extracted file to the correct sprite name
  3. Auto-match sheet names to database names by fuzzy string similarity

Usage:
  python tools/map_sprites.py --missing              # list Digimon without sprites
  python tools/map_sprites.py --match                # auto-match extracted PNGs to DB names
  python tools/map_sprites.py --rename SRC DST       # rename game/assets/sprites/SRC to DST
  python tools/map_sprites.py --copy  SRC DST        # copy SRC to DST (both in sprites dir)
  python tools/map_sprites.py --status               # show coverage count

SRC / DST are bare filenames (no path), e.g.  agumon_idle.png  agumon.png
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

SPRITES_DIR = Path(__file__).parent.parent / "game" / "assets" / "sprites"
DIGIMON_JSON = Path(__file__).parent.parent / "game" / "data" / "digimon.json"


def safe_sprite_name(name: str) -> str:
    import re
    n = name.lower()
    n = re.sub(r"[^a-z0-9_]", "_", n)
    n = re.sub(r"_+", "_", n).strip("_")
    return n + ".png"


def load_digimon_names() -> list[str]:
    data = json.loads(DIGIMON_JSON.read_text())
    return [d["name"] for d in data]


def list_missing(names: list[str]):
    missing = [n for n in names if not (SPRITES_DIR / safe_sprite_name(n)).exists()]
    print(f"{len(missing)} Digimon missing sprites (out of {len(names)}):")
    for n in missing:
        print(f"  {n:30s}  -> expected: {safe_sprite_name(n)}")


def show_status(names: list[str]):
    total = len(names)
    have = sum(1 for n in names if (SPRITES_DIR / safe_sprite_name(n)).exists())
    pct = have / total * 100
    print(f"Sprite coverage: {have}/{total} ({pct:.1f}%)")
    all_pngs = list(SPRITES_DIR.glob("*.png"))
    print(f"Total PNGs in sprites dir: {len(all_pngs)}")


def fuzzy_score(a: str, b: str) -> float:
    """Simple longest-common-subsequence ratio."""
    a, b = a.lower(), b.lower()
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0.0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    lcs = dp[m][n]
    return 2 * lcs / (m + n)


def auto_match(names: list[str], threshold: float = 0.6):
    """Try to auto-match PNGs in sprites dir to canonical Digimon names."""
    all_pngs = [p for p in SPRITES_DIR.glob("*.png")]
    canonical = {safe_sprite_name(n): n for n in names}

    unmatched = [p for p in all_pngs if p.name not in canonical]
    if not unmatched:
        print("All PNGs already match canonical names.")
        return

    print(f"Attempting to match {len(unmatched)} unmatched PNGs...\n")
    for png in unmatched:
        stem = png.stem  # e.g. "agumon_idle"
        best_name = None
        best_score = 0.0
        for digi_name in names:
            score = fuzzy_score(stem, digi_name)
            if score > best_score:
                best_score = score
                best_name = digi_name
        if best_score >= threshold and best_name:
            target = SPRITES_DIR / safe_sprite_name(best_name)
            if not target.exists():
                shutil.copy2(png, target)
                print(f"  {png.name:40s} -> {target.name}  (score {best_score:.2f})")
            else:
                print(f"  {png.name:40s} -> SKIP (target exists: {target.name})")
        else:
            print(f"  {png.name:40s} -> no match (best '{best_name}' score {best_score:.2f})")


def rename_sprite(src: str, dst: str):
    src_path = SPRITES_DIR / src
    dst_path = SPRITES_DIR / dst
    if not src_path.exists():
        print(f"Not found: {src_path}")
        sys.exit(1)
    src_path.rename(dst_path)
    print(f"Renamed: {src} -> {dst}")


def copy_sprite(src: str, dst: str):
    src_path = SPRITES_DIR / src
    dst_path = SPRITES_DIR / dst
    if not src_path.exists():
        print(f"Not found: {src_path}")
        sys.exit(1)
    shutil.copy2(src_path, dst_path)
    print(f"Copied: {src} -> {dst}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--missing", action="store_true", help="List Digimon without sprites")
    parser.add_argument("--match", action="store_true", help="Auto-match PNGs to Digimon names")
    parser.add_argument("--rename", nargs=2, metavar=("SRC", "DST"), help="Rename sprite file")
    parser.add_argument("--copy", nargs=2, metavar=("SRC", "DST"), help="Copy sprite file")
    parser.add_argument("--status", action="store_true", help="Show coverage stats")
    parser.add_argument("--threshold", type=float, default=0.6,
                        help="Fuzzy match threshold for --match (default 0.6)")
    args = parser.parse_args()

    SPRITES_DIR.mkdir(parents=True, exist_ok=True)
    names = load_digimon_names()

    if args.missing:
        list_missing(names)
    elif args.match:
        auto_match(names, threshold=args.threshold)
    elif args.rename:
        rename_sprite(args.rename[0], args.rename[1])
    elif args.copy:
        copy_sprite(args.copy[0], args.copy[1])
    elif args.status:
        show_status(names)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
