"""
Regenerate areas.json with large encounter pools covering all 1009 Digimon.
Every Digimon appears in at least one area. Rarity = lower weight.
Run: python tools/_gen_areas.py
"""
import json, random
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
DIGIMON_JSON = ROOT / "game" / "data" / "digimon.json"
AREAS_JSON   = ROOT / "game" / "data" / "areas.json"

data = json.loads(DIGIMON_JSON.read_text())
# Build id->digimon map
by_id = {d["id"]: d for d in data}

# ---------------------------------------------------------------------------
# Area definitions
# ---------------------------------------------------------------------------
AREAS_META = [
    {
        "id": "file_city",
        "name": "File City",
        "description": "The bustling hub city of the Digital World. All roads begin and end here. Tamers from every corner of the Digital World pass through its gates.",
        "connections": ["gear_savanna", "tropical_jungle", "ancient_dino_region", "factorial_town", "metal_factory", "dark_cave", "infinity_mountain"],
        "stages": {"Baby", "In-Training"},
        "types": None,   # all types
        "lv": {"Baby": (3,10), "In-Training": (5,12)},
    },
    {
        "id": "gear_savanna",
        "name": "Gear Savanna",
        "description": "Vast golden plains humming with digital wind. Fire-breathing predators and swift dragon-types hunt among the tall data grasses.",
        "connections": ["file_city", "tropical_jungle", "ancient_dino_region"],
        "stages": {"Rookie", "Champion"},
        "types": {"Fire", "Dragon", "Normal", "Fighting", "Flying", "Holy"},
        "lv": {"Rookie": (8,20), "Champion": (15,24)},
    },
    {
        "id": "tropical_jungle",
        "name": "Tropical Jungle",
        "description": "A dense canopy of living data vines. Bug-type Digimon nest in the treetops while poisonous species lurk below.",
        "connections": ["file_city", "gear_savanna", "ancient_dino_region", "dark_cave"],
        "stages": {"Rookie", "Champion"},
        "types": {"Plant", "Bug", "Flying", "Poison", "Water"},
        "lv": {"Rookie": (10,22), "Champion": (15,26)},
    },
    {
        "id": "ancient_dino_region",
        "name": "Ancient Dino Region",
        "description": "Fossil data-plains where ancient Champion and Ultimate forms roam freely. Dragon-types and fire-wielders dominate the food chain.",
        "connections": ["file_city", "gear_savanna", "tropical_jungle", "factorial_town"],
        "stages": {"Champion", "Ultimate"},
        "types": {"Dragon", "Fire", "Fighting", "Normal", "Flying"},
        "lv": {"Champion": (18,32), "Ultimate": (25,34)},
    },
    {
        "id": "factorial_town",
        "name": "Factorial Town",
        "description": "A mechanized city district built from living Steel data. Electric currents flow through every street; machine Digimon patrol the grid.",
        "connections": ["file_city", "ancient_dino_region", "metal_factory"],
        "stages": {"Champion", "Ultimate"},
        "types": {"Steel", "Electric", "Normal", "Ice"},
        "lv": {"Champion": (25,36), "Ultimate": (28,40)},
    },
    {
        "id": "metal_factory",
        "name": "Metal Factory",
        "description": "A colossal processing plant deep underground. Powerful machine and dark-type Ultimate and Mega Digimon guard the forge cores.",
        "connections": ["file_city", "factorial_town", "dark_cave", "infinity_mountain"],
        "stages": {"Ultimate", "Mega"},
        "types": {"Steel", "Electric", "Dark", "Poison"},
        "lv": {"Ultimate": (30,45), "Mega": (42,50)},
    },
    {
        "id": "dark_cave",
        "name": "Dark Cave",
        "description": "A labyrinth of shadow-data tunnels. Virus-attribute Digimon thrive here. Mega-level dark types lurk at the deepest levels.",
        "connections": ["file_city", "tropical_jungle", "metal_factory", "infinity_mountain"],
        "stages": {"Ultimate", "Mega"},
        "types": {"Dark", "Ice", "Poison", "Water", "Dragon"},
        "lv": {"Ultimate": (35,50), "Mega": (45,55)},
    },
    {
        "id": "infinity_mountain",
        "name": "Infinity Mountain",
        "description": "The highest peak in the Digital World. Ancient Mega-level Digimon dwell here, including legendary Royal Knights and Demon Lords.",
        "connections": ["file_city", "metal_factory", "dark_cave"],
        "stages": {"Mega", "Ultimate"},
        "types": None,   # all — safety net
        "lv": {"Ultimate": (45,55), "Mega": (48,65)},
    },
]

# ---------------------------------------------------------------------------
# Rarity weights by stage
# ---------------------------------------------------------------------------
STAGE_WEIGHT = {
    "Baby": 10,
    "In-Training": 10,
    "Rookie": 8,
    "Champion": 5,
    "Ultimate": 3,
    "Mega": 2,
}

# Very rare legendaries get weight=1
LEGENDARY_NAMES = {
    "Omnimon","Gallantmon","MegaGargomon","Sakuyamon","Beelzemon","Imperialdramon",
    "Imperialdramon Dragon Mode","Imperialdramon Fighter Mode","Imperialdramon Paladin Mode",
    "Omnimon Zwart","Omnimon Merciful Mode","Omnimon X","Gallantmon Crimson Mode",
    "ShineGreymon","MirageGaogamon","Rosemon Burst Mode","Ravemon Burst Mode",
    "Susanoomon","Alphamon","Dukemon","Magnamon","Dynasmon","Kentaurosmon",
    "Craniummon","Sleipmon","Gankoomon","Jesmon","Examon","Duftmon","UlforceVeedramon",
    "Baihumon","Zhuqiaomon","Ebonwumon","Azulongmon","Fanglongmon",
    "Lucemon Falldown Mode","Lucemon Satan Mode","Daemon","VenomMyotismon",
    "Apocalymon","Armageddemon","Diaboromon","Belphemon","Leviamon","Barbamon",
    "Beelzemon Blast Mode","Lilithmon","Lucemon","MaloMyotismon",
    "Ophanimon","Cherubimon (Good)","Seraphimon",
}

# ---------------------------------------------------------------------------
# Assign each Digimon to areas
# ---------------------------------------------------------------------------
# area_id -> list of (species_id, weight, min_lv, max_lv)
pools = defaultdict(list)
assigned = set()  # track which Digimon IDs have been placed

def assign(digi, area_id):
    meta = next(m for m in AREAS_META if m["id"] == area_id)
    stage = digi.get("stage", "Rookie")
    lv_range = meta["lv"].get(stage)
    if lv_range is None:
        # find closest stage key
        all_lvs = list(meta["lv"].values())
        lv_range = all_lvs[-1]  # use highest
    w = 1 if digi["name"] in LEGENDARY_NAMES else STAGE_WEIGHT.get(stage, 3)
    pools[area_id].append({
        "species_id": digi["id"],
        "min_level": lv_range[0],
        "max_level": lv_range[1],
        "weight": w,
    })
    assigned.add(digi["id"])

for digi in data:
    stage = digi.get("stage", "Rookie")
    types = set(digi.get("types", ["Normal"]))

    if stage in ("Baby", "In-Training"):
        assign(digi, "file_city")
        continue

    placed = False
    for meta in AREAS_META:
        if meta["id"] == "infinity_mountain":
            continue  # handled as fallback
        if stage not in meta["stages"]:
            continue
        if meta["types"] is None or types & meta["types"]:
            assign(digi, meta["id"])
            placed = True
            # Also place in 1 extra area for cross-area discovery
            # Find another matching area that also accepts this stage+type
            for meta2 in AREAS_META:
                if meta2["id"] in ("infinity_mountain", meta["id"]):
                    continue
                if stage not in meta2["stages"]:
                    continue
                if meta2["types"] is None or types & meta2["types"]:
                    assign(digi, meta2["id"])
                    break
            break

    if not placed:
        # Fallback: place in infinity_mountain
        assign(digi, "infinity_mountain")

# Ensure everything is in infinity_mountain too (for legendary Mega hunting)
for digi in data:
    stage = digi.get("stage", "Rookie")
    if stage in ("Mega", "Ultimate") and digi["id"] not in {
        e["species_id"] for e in pools["infinity_mountain"]
    }:
        assign(digi, "infinity_mountain")

# Safety net: any still-unassigned Digimon goes to infinity_mountain
for digi in data:
    if digi["id"] not in assigned:
        assign(digi, "infinity_mountain")

# ---------------------------------------------------------------------------
# Trainer data (preserved from original)
# ---------------------------------------------------------------------------
TRAINERS = {
    "file_city": [
        {"name": "Tamer Marcus", "party": [{"species_id": 21, "level": 5}, {"species_id": 22, "level": 5}], "reward_money": 150},
        {"name": "Rookie Sora",  "party": [{"species_id": 23, "level": 6}, {"species_id": 24, "level": 6}], "reward_money": 180},
    ],
    "gear_savanna": [
        {"name": "Tamer Joe",       "party": [{"species_id": 21, "level": 8}, {"species_id": 22, "level": 7}], "reward_money": 200},
        {"name": "Scout Pita",      "party": [{"species_id": 23, "level": 10}, {"species_id": 24, "level": 9}, {"species_id": 25, "level": 10}], "reward_money": 280},
        {"name": "Wanderer Gus",    "party": [{"species_id": 26, "level": 12}, {"species_id": 27, "level": 11}], "reward_money": 320},
    ],
    "tropical_jungle": [
        {"name": "Jungle Tamer Yuki", "party": [{"species_id": 24, "level": 15}, {"species_id": 26, "level": 14}], "reward_money": 380},
        {"name": "Botanist Rena",     "party": [{"species_id": 64, "level": 18}, {"species_id": 27, "level": 17}, {"species_id": 67, "level": 18}], "reward_money": 480},
        {"name": "Swamp Lord Kael",   "party": [{"species_id": 67, "level": 21}, {"species_id": 64, "level": 20}], "reward_money": 560},
    ],
    "ancient_dino_region": [
        {"name": "Dino Tamer Rex",    "party": [{"species_id": 21, "level": 20}, {"species_id": 61, "level": 21}], "reward_money": 520},
        {"name": "Flame Rider Kira",  "party": [{"species_id": 84, "level": 24}, {"species_id": 85, "level": 23}, {"species_id": 61, "level": 24}], "reward_money": 680},
        {"name": "Dragon King Voltan","party": [{"species_id": 85, "level": 27}, {"species_id": 84, "level": 26}], "reward_money": 780},
    ],
    "factorial_town": [
        {"name": "Engineer Theo",       "party": [{"species_id": 25, "level": 25}, {"species_id": 65, "level": 24}], "reward_money": 680},
        {"name": "Factory Boss Nira",   "party": [{"species_id": 105, "level": 30}, {"species_id": 108, "level": 29}, {"species_id": 106, "level": 30}], "reward_money": 880},
        {"name": "Circuit Master Dov",  "party": [{"species_id": 108, "level": 34}, {"species_id": 105, "level": 33}], "reward_money": 980},
    ],
    "metal_factory": [
        {"name": "Foreman Ike",           "party": [{"species_id": 105, "level": 33}, {"species_id": 108, "level": 32}], "reward_money": 960},
        {"name": "Steel Warden Lysa",     "party": [{"species_id": 121, "level": 38}, {"species_id": 111, "level": 37}, {"species_id": 108, "level": 38}], "reward_money": 1120},
        {"name": "Iron Overlord Gareth",  "party": [{"species_id": 111, "level": 41}, {"species_id": 121, "level": 40}], "reward_money": 1280},
    ],
    "dark_cave": [
        {"name": "Shadow Tamer Orla",   "party": [{"species_id": 44, "level": 37}, {"species_id": 71, "level": 36}], "reward_money": 1080},
        {"name": "Virus Cultist Draven","party": [{"species_id": 56, "level": 42}, {"species_id": 96, "level": 41}, {"species_id": 120, "level": 42}], "reward_money": 1280},
        {"name": "Cave Lord Mortis",    "party": [{"species_id": 120, "level": 47}, {"species_id": 96, "level": 46}], "reward_money": 1460},
    ],
    "infinity_mountain": [
        {"name": "Mountain Sage Elara",    "party": [{"species_id": 111, "level": 48}, {"species_id": 112, "level": 47}], "reward_money": 1560},
        {"name": "Peak Guardian Voss",     "party": [{"species_id": 113, "level": 54}, {"species_id": 118, "level": 53}, {"species_id": 119, "level": 54}], "reward_money": 1860},
        {"name": "Summit Champion Aiden",  "party": [{"species_id": 129, "level": 59}, {"species_id": 119, "level": 58}], "reward_money": 2200},
    ],
}

# ---------------------------------------------------------------------------
# Build final areas.json
# ---------------------------------------------------------------------------
areas_out = []
for meta in AREAS_META:
    aid = meta["id"]
    area = {
        "id": aid,
        "name": meta["name"],
        "description": meta["description"],
        "wild_encounters": pools[aid],
        "trainers": TRAINERS.get(aid, []),
        "connections": meta["connections"],
    }
    areas_out.append(area)

AREAS_JSON.write_text(json.dumps(areas_out, indent=2, ensure_ascii=False))

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
total_digi = len(data)
in_wild = set()
for area in areas_out:
    for e in area["wild_encounters"]:
        in_wild.add(e["species_id"])

print(f"Total Digimon: {total_digi}")
print(f"In wild encounters: {len(in_wild)}")
print(f"Missing from wild: {total_digi - len(in_wild)}")
for area in areas_out:
    print(f"  {area['name']:25s}: {len(area['wild_encounters']):4d} wild encounter entries")
