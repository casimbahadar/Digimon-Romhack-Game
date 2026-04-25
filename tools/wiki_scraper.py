#!/usr/bin/env python3
"""
Digimon wiki scraper — outputs JSON ready to merge via tools/merge.py.

Usage:
    python wiki_scraper.py --limit 500 --output scraped.json
    python wiki_scraper.py --dry-run          # prints 3 samples, no requests
    python wiki_scraper.py --limit 2000       # scrape everything
"""
import re
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Install deps: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from auto_assign import assign

BASE        = "https://digimon.fandom.com"
LIST_URL    = f"{BASE}/wiki/List_of_Digimon"
HEADERS     = {"User-Agent": "DigimonGameScraper/1.0 (educational fan project)"}
MIN_DELAY   = 1.0  # seconds between requests

_last_req   = 0.0

STAGE_MAP = {
    "fresh":"Baby","in-training":"Baby","baby":"Baby","baby i":"Baby","baby ii":"Baby",
    "rookie":"Rookie","child":"Rookie",
    "champion":"Champion","adult":"Champion",
    "ultimate":"Ultimate","perfect":"Ultimate",
    "mega":"Mega","ultra":"Mega","armor":"Champion","hybrid":"Rookie",
}

ATTR_MAP = {
    "vaccine":"Vaccine","data":"Data","virus":"Virus","free":"Free","variable":"Free",
    "unknown":"Free","neutral":"Free",
}

TYPE_KEYWORDS = {
    "fire":["fire","flame","heat","burn","blaze"],
    "water":["water","sea","ocean","aqua","marine","liquid"],
    "ice":["ice","freeze","frozen","snow","blizzard","frost","tundra"],
    "plant":["plant","grass","nature","leaf","wood","forest","flower","vine"],
    "electric":["electric","thunder","lightning","volt","spark"],
    "dragon":["dragon","drago","dino","reptile","saurian"],
    "steel":["metal","steel","iron","machine","mech","cyber","android"],
    "holy":["angel","holy","seraph","divine","sacred","light"],
    "dark":["dark","devil","demon","evil","shadow","night","undead","ghost"],
    "fighting":["warrior","knight","fighter","brawl","martial","beast","lion","tiger","wolf"],
    "flying":["bird","fly","wing","avian","hawk","eagle","falcon","raven"],
    "bug":["bug","insect","beetle","ant","moth","worm","spider","bee","wasp"],
    "poison":["poison","toxic","venom","slime","slug"],
}

NORMAL_TYPES = ["Normal"]

def _rate_limit():
    global _last_req
    elapsed = time.time() - _last_req
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)
    _last_req = time.time()


def fetch(url: str) -> Optional[BeautifulSoup]:
    _rate_limit()
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"  WARN: {e}", file=sys.stderr)
        return None


def _infer_types(name: str, description: str = "") -> list[str]:
    text = (name + " " + description).lower()
    found = []
    for type_name, keywords in TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            found.append(type_name.capitalize())
    return found[:2] if found else ["Normal"]


def parse_digimon_page(name: str, url: str) -> dict:
    soup = fetch(url)
    entry = {
        "name": name,
        "stage": "Rookie",
        "attribute": "Free",
        "types": ["Normal"],
        "digivolves_to": [],
        "digivolves_from": [],
        "description": "",
    }
    if not soup:
        return entry

    # --- infobox (portable-infobox or wikitable) ---
    aside = soup.find("aside", class_="portable-infobox")
    if aside:
        for item in aside.find_all("div", class_="pi-item"):
            label_el = item.find("h3", class_="pi-data-label")
            value_el = item.find("div", class_="pi-data-value")
            if not label_el or not value_el:
                continue
            label = label_el.get_text(strip=True).lower()
            value = value_el.get_text(strip=True)
            if "level" in label or "stage" in label:
                entry["stage"] = STAGE_MAP.get(value.lower().strip(), "Rookie")
            elif "attribute" in label:
                entry["attribute"] = ATTR_MAP.get(value.lower().strip(), "Free")
            elif "type" in label and "digimon" not in label:
                raw_types = re.split(r"[,/\n]", value)
                types = _infer_types(name, " ".join(raw_types))
                if types:
                    entry["types"] = types

    # Fallback: look for a wikitable
    if entry["types"] == ["Normal"] and entry["stage"] == "Rookie":
        for row in soup.find_all("tr"):
            cells = row.find_all(["th","td"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True).lower()
                val = cells[1].get_text(strip=True)
                if "level" in key or "stage" in key:
                    entry["stage"] = STAGE_MAP.get(val.lower(), entry["stage"])
                elif "attribute" in key:
                    entry["attribute"] = ATTR_MAP.get(val.lower(), entry["attribute"])

    # --- description from first paragraph ---
    content = soup.find("div", class_="mw-parser-output")
    if content:
        for p in content.find_all("p", recursive=False):
            text = p.get_text(strip=True)
            if len(text) > 40:
                entry["description"] = text[:200]
                break

    # Infer types from name/description if still Normal
    if entry["types"] == ["Normal"]:
        entry["types"] = _infer_types(name, entry.get("description",""))

    # --- evolution links ---
    for section_name in ("Digivolution", "Evolution"):
        h2 = soup.find(lambda t: t.name in ("h2","h3") and section_name in t.get_text())
        if h2:
            for a in h2.find_next_siblings(limit=3):
                for link in a.find_all("a", href=True):
                    linked_name = link.get_text(strip=True)
                    if linked_name and linked_name != name:
                        entry["digivolves_to"].append({"name": linked_name})
            break

    return entry


def scrape_list(limit: int) -> list[str]:
    """Return list of (name, url) pairs from the Digimon index."""
    soup = fetch(LIST_URL)
    if not soup:
        return []
    pairs = []
    seen = set()
    for a in soup.select("table.wikitable a[href]"):
        name = a.get_text(strip=True)
        href = a["href"]
        if not name or name in seen or not href.startswith("/wiki/"):
            continue
        # skip non-Digimon pages
        if any(x in href for x in ["List_of","Category","Template","User","Help","File"]):
            continue
        seen.add(name)
        pairs.append((name, BASE + href))
        if len(pairs) >= limit:
            break
    return pairs


DRY_RUN_SAMPLES = [
    {"id":201,"name":"Agumon (X)","stage":"Rookie","attribute":"Vaccine","types":["Fire","Dragon"],
     "description":"An Agumon who has been affected by the X-Antibody."},
    {"id":202,"name":"Gabumon (X)","stage":"Rookie","attribute":"Data","types":["Ice","Dragon"],
     "description":"A Gabumon affected by the X-Antibody with enhanced wolf powers."},
    {"id":203,"name":"Omnimon (X)","stage":"Mega","attribute":"Vaccine","types":["Holy","Ice"],
     "description":"An Omnimon enhanced by the X-Antibody to even greater heights."},
]


def main():
    ap = argparse.ArgumentParser(description="Digimon wiki scraper")
    ap.add_argument("--limit",   type=int, default=100,           help="Max Digimon to scrape")
    ap.add_argument("--output",  default="scraped.json",           help="Output JSON file")
    ap.add_argument("--dry-run", action="store_true",              help="Print samples only")
    args = ap.parse_args()

    if args.dry_run:
        samples = [assign(dict(e)) for e in DRY_RUN_SAMPLES]
        print(json.dumps(samples, indent=2))
        return

    print(f"Fetching Digimon list (limit={args.limit}) …")
    pairs = scrape_list(args.limit)
    print(f"Found {len(pairs)} candidates")

    results = []
    for i, (name, url) in enumerate(pairs, 1):
        print(f"  [{i}/{len(pairs)}] {name}")
        entry = parse_digimon_page(name, url)
        assign(entry)      # fill moves, stats, catch_rate
        results.append(entry)

    out = Path(args.output)
    out.write_text(json.dumps(results, indent=2))
    print(f"\nSaved {len(results)} entries → {out}")
    print(f"Next: python merge.py {out}")


if __name__ == "__main__":
    main()
