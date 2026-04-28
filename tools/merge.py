"""
Merge scraped/new Digimon entries into game/data/digimon.json.
Auto-assigns moves, stats, and resolves evolution chains by name.
Updates areas.json encounter tables automatically.

Usage:
    python merge.py scraped.json          # merge a file of new entries
    python merge.py --resolve-evos        # re-resolve all evo chains by name
    python merge.py --update-areas        # rebuild area encounter tables
"""
import json
import sys
import argparse
from pathlib import Path

ROOT      = Path(__file__).parent.parent
DIGI_PATH = ROOT / "game/data/digimon.json"
AREA_PATH = ROOT / "game/data/areas.json"

sys.path.insert(0, str(Path(__file__).parent))
from auto_assign import assign

# Stage → area IDs that should include this Digimon in wild encounters
STAGE_AREAS = {
    "Baby":     ["file_city", "gear_savanna"],
    "Rookie":   ["gear_savanna", "tropical_jungle"],
    "Champion": ["tropical_jungle", "ancient_dino_region", "factorial_town"],
    "Ultimate": ["factorial_town", "metal_factory", "dark_cave"],
    "Mega":     ["infinity_mountain", "dark_cave"],
}

LEVEL_RANGES = {
    "Baby":     (3,  10),
    "Rookie":   (8,  20),
    "Champion": (18, 35),
    "Ultimate": (33, 50),
    "Mega":     (48, 65),
}


def load_db():
    return json.loads(DIGI_PATH.read_text())


def save_db(data):
    DIGI_PATH.write_text(json.dumps(data, indent=2))


def name_to_id(db):
    return {d["name"].lower(): d["id"] for d in db}


def resolve_evos(db):
    """Replace string evo references with numeric IDs using name lookup."""
    n2id = name_to_id(db)
    for d in db:
        for evo in d.get("digivolves_to", []):
            if "id" not in evo and "name" in evo:
                evo["id"] = n2id.get(evo["name"].lower(), 0)
        for evo in d.get("digivolves_from", []):
            if "id" not in evo and "name" in evo:
                evo["id"] = n2id.get(evo["name"].lower(), 0)
    return db


def update_areas(db):
    areas = json.loads(AREA_PATH.read_text())
    area_map = {a["id"]: a for a in areas}

    # Remove existing auto-generated encounters (keep hand-crafted ones for ids 1-200)
    for area in areas:
        area["wild_encounters"] = [
            e for e in area.get("wild_encounters", [])
            if e.get("species_id", 0) <= 200
        ]

    # Add new Digimon (id > 200)
    for d in db:
        if d["id"] <= 200:
            continue
        stage = d.get("stage", "Rookie")
        lo, hi = LEVEL_RANGES.get(stage, (10, 30))
        weight = {"Baby":30,"Rookie":25,"Champion":20,"Ultimate":10,"Mega":3}.get(stage,15)
        for area_id in STAGE_AREAS.get(stage, ["gear_savanna"]):
            if area_id in area_map:
                area_map[area_id].setdefault("wild_encounters", []).append({
                    "species_id": d["id"],
                    "min_level": lo,
                    "max_level": hi,
                    "weight": weight,
                })

    AREA_PATH.write_text(json.dumps(areas, indent=2))
    print(f"Updated areas.json")


def merge_file(path: str):
    db = load_db()
    existing_ids = {d["id"] for d in db}
    existing_names = {d["name"].lower() for d in db}
    next_id = max(d["id"] for d in db) + 1

    new_entries = json.loads(Path(path).read_text())
    if isinstance(new_entries, dict):
        new_entries = list(new_entries.values())

    added = 0
    for entry in new_entries:
        name = entry.get("name","").strip()
        if not name:
            continue
        if name.lower() in existing_names:
            continue  # already present
        if "id" not in entry or entry["id"] in existing_ids:
            entry["id"] = next_id
            next_id += 1
        assign(entry)
        db.append(entry)
        existing_ids.add(entry["id"])
        existing_names.add(name.lower())
        added += 1

    db.sort(key=lambda d: d["id"])
    db = resolve_evos(db)
    save_db(db)
    print(f"Added {added} new Digimon. Total: {len(db)}")
    update_areas(db)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="JSON file of new Digimon entries to merge")
    ap.add_argument("--resolve-evos", action="store_true")
    ap.add_argument("--update-areas", action="store_true")
    args = ap.parse_args()

    if args.file:
        merge_file(args.file)
    elif args.resolve_evos:
        db = resolve_evos(load_db())
        save_db(db)
        print("Evolution chains resolved.")
    elif args.update_areas:
        update_areas(load_db())
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
