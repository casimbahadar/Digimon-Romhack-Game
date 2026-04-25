"""wiki_scraper.py — Scrape digimon.fandom.com to build Digimon data JSON.

Usage examples:
    python wiki_scraper.py --dry-run
    python wiki_scraper.py --limit 20 --output ../game/data/digimon_scraped.json
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://digimon.fandom.com/wiki/"
DIGIMON_LIST_URL = "https://digimon.fandom.com/wiki/List_of_Digimon"

_HEADERS = {
    "User-Agent": (
        "DigimonRomhackScraper/1.0 "
        "(https://github.com/example/digimon-romhack; educational use)"
    )
}

_LAST_REQUEST_TIME: float = 0.0
_RATE_LIMIT_SECONDS: float = 1.0

# ---------------------------------------------------------------------------
# Dry-run sample data (no network requests)
# ---------------------------------------------------------------------------

_DRY_RUN_SAMPLES = [
    {
        "id": 1,
        "species_id": 1,
        "name": "Agumon",
        "level": "Rookie",
        "attribute": "Vaccine",
        "type": "Reptile",
        "base_stats": {
            "hp": 120,
            "mp": 60,
            "attack": 55,
            "defense": 45,
            "speed": 50,
            "special": 40,
        },
        "moves": ["scratch", "tackle"],
        "evolution_from": None,
        "evolution_to": ["Greymon"],
        "description": "A Reptile Digimon with an aggressive personality.",
        "source": "wiki_scraper",
    },
    {
        "id": 2,
        "species_id": 2,
        "name": "Gabumon",
        "level": "Rookie",
        "attribute": "Data",
        "type": "Reptile",
        "base_stats": {
            "hp": 110,
            "mp": 70,
            "attack": 45,
            "defense": 55,
            "speed": 45,
            "special": 50,
        },
        "moves": ["scratch", "quick_attack"],
        "evolution_from": None,
        "evolution_to": ["Garurumon"],
        "description": "A Reptile Digimon that wears a Gabumon pelt.",
        "source": "wiki_scraper",
    },
    {
        "id": 3,
        "species_id": 3,
        "name": "Patamon",
        "level": "Rookie",
        "attribute": "Data",
        "type": "Mammal",
        "base_stats": {
            "hp": 100,
            "mp": 80,
            "attack": 40,
            "defense": 40,
            "speed": 55,
            "special": 55,
        },
        "moves": ["tackle", "quick_attack"],
        "evolution_from": None,
        "evolution_to": ["Angemon"],
        "description": "A small Mammal Digimon with large ears used for flying.",
        "source": "wiki_scraper",
    },
]

# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------


def fetch_page(url: str) -> "BeautifulSoup | None":
    """GET *url* with a rate limit, returning parsed BeautifulSoup or None."""
    global _LAST_REQUEST_TIME

    elapsed = time.monotonic() - _LAST_REQUEST_TIME
    if elapsed < _RATE_LIMIT_SECONDS:
        time.sleep(_RATE_LIMIT_SECONDS - elapsed)

    try:
        response = requests.get(url, headers=_HEADERS, timeout=15)
        _LAST_REQUEST_TIME = time.monotonic()
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"[warn] Failed to fetch {url}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _clean(text: str) -> str:
    """Strip whitespace and citation markers like [1] from a string."""
    text = re.sub(r"\[\d+\]", "", text)
    return text.strip()


def parse_digimon_page(name: str) -> "dict | None":
    """Fetch the wiki page for *name* and extract infobox fields.

    Returns a (possibly partial) dict with keys: level, attribute, type.
    Returns None if the page cannot be fetched.
    """
    url = BASE_URL + name.replace(" ", "_")
    soup = fetch_page(url)
    if soup is None:
        return None

    result: dict = {"name": name}

    # The infobox on fandom wikis is typically a <table class="infobox"> or
    # an aside element; fandom uses <aside class="portable-infobox">.
    infobox = soup.find("aside", class_=re.compile(r"portable-infobox", re.I))
    if infobox is None:
        # Fall back to any table that looks like an infobox
        infobox = soup.find("table", class_=re.compile(r"infobox|wikitable", re.I))

    if infobox:
        # Portable infobox: rows are <div data-source="...">
        for item in infobox.find_all("div", attrs={"data-source": True}):
            source = item.get("data-source", "").lower()
            value_tag = item.find("div", class_=re.compile(r"pi-data-value", re.I))
            if value_tag is None:
                continue
            value = _clean(value_tag.get_text(" ", strip=True))

            if source in ("level", "stage"):
                result["level"] = value
            elif source == "attribute":
                result["attribute"] = value
            elif source in ("type", "family", "families"):
                result["type"] = value

        # Also try plain <tr> rows if portable infobox rows were sparse
        for row in infobox.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            label = _clean(cells[0].get_text()).lower()
            value = _clean(cells[1].get_text())
            if not value:
                continue
            if "level" in label or "stage" in label:
                result.setdefault("level", value)
            elif "attribute" in label:
                result.setdefault("attribute", value)
            elif "type" in label or "family" in label:
                result.setdefault("type", value)

    return result if len(result) > 1 else None


# ---------------------------------------------------------------------------
# List scraping
# ---------------------------------------------------------------------------


def scrape_digimon_list(limit: int = 50) -> list:
    """Return up to *limit* Digimon names from the official list page."""
    soup = fetch_page(DIGIMON_LIST_URL)
    if soup is None:
        return []

    names: list = []
    seen: set = set()

    # The list page has wikitable(s); each row links to a Digimon article.
    for table in soup.find_all("table", class_=re.compile(r"wikitable", re.I)):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            # The Digimon name is usually in the first or second cell as a link.
            for cell in cells[:3]:
                link = cell.find("a", href=re.compile(r"^/wiki/"))
                if link is None:
                    continue
                name = _clean(link.get_text())
                # Skip empty names, category links, and disambiguation pages.
                if (
                    name
                    and name not in seen
                    and not name.startswith("Category:")
                    and "(" not in name
                ):
                    seen.add(name)
                    names.append(name)
                    break
            if len(names) >= limit:
                break
        if len(names) >= limit:
            break

    return names[:limit]


# ---------------------------------------------------------------------------
# Entry builder
# ---------------------------------------------------------------------------

# Rough stat defaults keyed by level/stage (all values are approximate).
_LEVEL_STAT_DEFAULTS: dict = {
    "Fresh":      {"hp": 60,  "mp": 30,  "attack": 20, "defense": 20, "speed": 30, "special": 20},
    "In-Training":{"hp": 80,  "mp": 40,  "attack": 30, "defense": 30, "speed": 35, "special": 30},
    "Rookie":     {"hp": 110, "mp": 60,  "attack": 50, "defense": 45, "speed": 50, "special": 45},
    "Champion":   {"hp": 160, "mp": 80,  "attack": 75, "defense": 65, "speed": 65, "special": 65},
    "Ultimate":   {"hp": 220, "mp": 110, "attack": 100,"defense": 90, "speed": 85, "special": 90},
    "Mega":       {"hp": 300, "mp": 150, "attack": 130,"defense": 120,"speed": 110,"special": 120},
}

_DEFAULT_STATS = _LEVEL_STAT_DEFAULTS["Rookie"]

_DEFAULT_MOVES_BY_LEVEL: dict = {
    "Fresh":       ["tackle"],
    "In-Training": ["tackle"],
    "Rookie":      ["scratch", "tackle"],
    "Champion":    ["scratch", "tackle", "quick_attack"],
    "Ultimate":    ["scratch", "tackle", "quick_attack"],
    "Mega":        ["scratch", "tackle", "quick_attack"],
}

_DEFAULT_MOVES = ["scratch", "tackle"]


def build_digimon_entry(name: str, species_id: int) -> dict:
    """Scrape *name* from the wiki and build a schema-compliant dict.

    Missing fields are filled with sensible defaults so the returned dict
    always matches the ``game/data/digimon.json`` schema.
    """
    page_data = parse_digimon_page(name) or {}

    level = page_data.get("level", "Rookie")
    # Normalise level strings like "Rookie Level" → "Rookie"
    for key in _LEVEL_STAT_DEFAULTS:
        if key.lower() in level.lower():
            level = key
            break
    else:
        level = "Rookie"

    attribute = page_data.get("attribute", "Unknown")
    digimon_type = page_data.get("type", "Unknown")
    # Some pages return multiple types separated by newlines/commas; keep first.
    digimon_type = re.split(r"[\n,/]", digimon_type)[0].strip() or "Unknown"

    base_stats = dict(_LEVEL_STAT_DEFAULTS.get(level, _DEFAULT_STATS))
    moves = list(_DEFAULT_MOVES_BY_LEVEL.get(level, _DEFAULT_MOVES))

    return {
        "id": species_id,
        "species_id": species_id,
        "name": name,
        "level": level,
        "attribute": attribute,
        "type": digimon_type,
        "base_stats": base_stats,
        "moves": moves,
        "evolution_from": None,
        "evolution_to": [],
        "description": f"A {digimon_type} Digimon at the {level} level.",
        "source": "wiki_scraper",
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scrape digimon.fandom.com and output Digimon data JSON."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of Digimon to scrape (default: 50).",
    )
    parser.add_argument(
        "--output",
        default="../game/data/digimon_scraped.json",
        help="Output JSON file path (default: ../game/data/digimon_scraped.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print 3 hardcoded sample entries without making any network requests.",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("[dry-run] No network requests will be made.\n")
        print(json.dumps(_DRY_RUN_SAMPLES, indent=2))
        return

    # --- Live scrape ---
    print(f"Fetching Digimon list (limit={args.limit}) …")
    names = scrape_digimon_list(limit=args.limit)
    if not names:
        print("[error] Could not retrieve Digimon list. Exiting.")
        return

    print(f"Found {len(names)} names. Scraping individual pages …")
    entries: list = []
    for species_id, name in enumerate(names, start=1):
        print(f"  [{species_id}/{len(names)}] {name}")
        entry = build_digimon_entry(name, species_id)
        entries.append(entry)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(entries)} entries to {output_path.resolve()}")


if __name__ == "__main__":
    main()
