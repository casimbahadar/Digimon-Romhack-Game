#!/usr/bin/env python3
"""
One-command pipeline: scrape all Digimon → merge → resolve evos → update areas.

Usage:
    python pipeline.py                   # scrape 500 Digimon
    python pipeline.py --limit 2000      # scrape everything
    python pipeline.py --dry-run         # test with 3 samples
"""
import sys
import json
import argparse
import subprocess
from pathlib import Path

HERE = Path(__file__).parent


def run(cmd: list, **kw):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run([sys.executable] + cmd, **kw, capture_output=False)
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    ap = argparse.ArgumentParser(description="Full Digimon scrape + merge pipeline")
    ap.add_argument("--limit",   type=int, default=500, help="Max Digimon to scrape (default 500)")
    ap.add_argument("--dry-run", action="store_true",   help="Use 3 sample entries only")
    ap.add_argument("--scraped", default=None,          help="Skip scraping, merge this file directly")
    args = ap.parse_args()

    scraped_path = HERE / "scraped.json"

    if args.scraped:
        scraped_path = Path(args.scraped)
        print(f"Skipping scrape, using {scraped_path}")
    elif args.dry_run:
        run([str(HERE / "wiki_scraper.py"), "--dry-run",
             "--output", str(scraped_path)])
    else:
        run([str(HERE / "wiki_scraper.py"),
             "--limit", str(args.limit),
             "--output", str(scraped_path)])

    print("\nMerging into game/data/digimon.json …")
    run([str(HERE / "merge.py"), str(scraped_path)])

    print("\nDone! Run the game with: python game/main.py")


if __name__ == "__main__":
    main()
