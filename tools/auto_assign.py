"""
Auto-assigns moves, stats, catch_rate, and descriptions to Digimon entries
based purely on their stage and types. No manual work required.
"""
import random

# Moves available per type (ordered weakest→strongest)
TYPE_MOVES = {
    "Fire":     ["pepper_flame","blaze_blast","fire_bomb","pyro_sphere","nova_blast","terra_fire","heat_wave","magma_blast","wildfire","giga_blaster","atomic_flame","flame_inferno","crimson_flame"],
    "Water":    ["bubble_blow","marching_fishes","water_cannon","aqua_blaster","water_bomb","harpoon_torpedo","whirlpool","surf","tidal_wave","cocytus_breath","hydro_cannon"],
    "Ice":      ["blue_blaster","cold_breath","ice_blast","ice_arrow","arctic_blast","howling_blaster","sub_zero_ice","diamond_storm","blizzard_breath","metal_wolf_claw","tundra_freeze"],
    "Plant":    ["poison_ivy","vine_whip","thorn_whip","thorn_shot","nature_force","needle_spray","petal_blizzard","root_bind","spore_cloud","flower_cannon","solar_blast","leaf_storm"],
    "Electric": ["super_shocker","electro_bolts","thunder_bomb","static_force","bolt_drive","plasma_sphere","electro_shocker","lightning_blade","mega_shocker","horn_buster","thunder_strike","lightning_spear"],
    "Dragon":   ["dragon_breath","dragon_kick","dragon_claw","dragon_fire","dragon_roar","giga_slash","dragon_crusher","dramon_killer","draco_meteor","terra_destroyer"],
    "Steel":    ["metal_fang","metal_smash","laser_shot","iron_uppercut","iron_fist","beam_cannon","rivet_hammer","metal_cannon","giga_crusher","chrome_digizoid","atomic_blaster","infinity_cannon"],
    "Holy":     ["boom_bubble","sacred_arrow","holy_claw","angel_rod","shining_blast","holy_flame","holy_heal","celestial_arrow","divine_tornado","gate_of_destiny","god_typhoon","star_light_explosion","seven_heavens","excalibur","heavens_gate"],
    "Dark":     ["dark_spore","night_raid","death_claw","shadow_saber","death_slinger","shadow_wing","grisly_wing","crimson_lightning","dark_crush","nightmare_claw","chaos_flare","nightmare_syndrome","soul_crusher"],
    "Fighting": ["rapid_kick","power_punch","beat_knuckle","hurricane_kick","force_claw","bone_crusher","seismic_toss","tiger_wing_blades","justice_knuckle","fist_of_beast_king","crushing_blow","lion_king","volcanic_strike"],
    "Flying":   ["wing_gust","spiral_twister","feather_slash","sonic_boom","talon_strike","wing_blade","sky_slash","condor_wind","meteor_wing","hurricane_force","aerial_dive"],
    "Bug":      ["stinger","luring_net","cocoon_armor","wasp_sting","spiking_strike","larva_burst","mantis_blade","bug_blitz","bug_rush"],
    "Poison":   ["poison_needle","venom_spit","acid_spray","bio_slime","toxic_mist","venom_breath","corrosive_acid","miasma_breath","infection_breath"],
    "Normal":   ["tackle","scratch","quick_attack","digi_beam","data_burst","data_drain","body_slam","roar","hyper_beam"],
}

# Status/utility moves mixed in for variety
STATUS_MOVES = ["growl","barrier","heal","digivolve_burst","quick_heal","double_team","taunt","holy_heal","chrome_digizoid","cocoon_armor","root_bind","spore_cloud","roar","ultimate_charge","fire_wall"]

# Stage → (learn_levels, stat_ranges, catch_rate, move_count)
STAGE_CONFIG = {
    "Baby":     {"levels":[1,5],              "stats":(35,55),  "catch":220, "moves":2},
    "Rookie":   {"levels":[1,7,16],           "stats":(45,75),  "catch":150, "moves":3},
    "Champion": {"levels":[1,10,22,32],       "stats":(65,95),  "catch":100, "moves":4},
    "Ultimate": {"levels":[1,15,30,45],       "stats":(85,115), "catch":60,  "moves":4},
    "Mega":     {"levels":[1,20,40,55],       "stats":(100,135),"catch":30,  "moves":4},
}

# Stat profiles by primary type
STAT_PROFILES = {
    "Fire":     {"hp":0,"atk":2,"def":-1,"sp_atk":2,"sp_def":-1,"spd":1},
    "Water":    {"hp":1,"atk":0,"def":1,"sp_atk":1,"sp_def":1,"spd":0},
    "Ice":      {"hp":0,"atk":0,"def":1,"sp_atk":2,"sp_def":1,"spd":-1},
    "Plant":    {"hp":1,"atk":-1,"def":1,"sp_atk":2,"sp_def":1,"spd":-1},
    "Electric": {"hp":-1,"atk":0,"def":-1,"sp_atk":2,"sp_def":0,"spd":2},
    "Dragon":   {"hp":0,"atk":2,"def":1,"sp_atk":1,"sp_def":0,"spd":1},
    "Steel":    {"hp":1,"atk":1,"def":3,"sp_atk":-1,"sp_def":2,"spd":-2},
    "Holy":     {"hp":0,"atk":-1,"def":0,"sp_atk":2,"sp_def":2,"spd":0},
    "Dark":     {"hp":0,"atk":1,"def":-1,"sp_atk":2,"sp_def":-1,"spd":2},
    "Fighting": {"hp":1,"atk":3,"def":0,"sp_atk":-1,"sp_def":0,"spd":2},
    "Flying":   {"hp":-1,"atk":1,"def":-1,"sp_atk":1,"sp_def":0,"spd":3},
    "Bug":      {"hp":-1,"atk":2,"def":0,"sp_atk":0,"sp_def":-1,"spd":3},
    "Poison":   {"hp":0,"atk":0,"def":1,"sp_atk":1,"sp_def":1,"spd":0},
    "Normal":   {"hp":1,"atk":1,"def":0,"sp_atk":0,"sp_def":1,"spd":0},
}

def _pick_moves(types: list[str], stage: str, seed: int = 0) -> list[dict]:
    cfg = STAGE_CONFIG.get(stage, STAGE_CONFIG["Rookie"])
    levels = cfg["levels"]
    count  = cfg["moves"]
    rng = random.Random(seed)

    # Gather candidate moves from primary then secondary type
    candidates = []
    for t in types:
        candidates += TYPE_MOVES.get(t, TYPE_MOVES["Normal"])
    # deduplicate preserving order
    seen = set()
    unique = [m for m in candidates if not (m in seen or seen.add(m))]

    # Start with weak type move, scale up to strong moves
    result = []
    # Insert one status move at second slot for Champion+
    include_status = stage in ("Champion", "Ultimate", "Mega") and len(levels) >= 3
    status_move = STATUS_MOVES[seed % len(STATUS_MOVES)] if include_status else None

    for i, lvl in enumerate(levels[:count]):
        if i == 0:
            move_id = unique[0] if unique else "tackle"
        elif include_status and i == 1:
            move_id = status_move
        elif i == len(levels) - 1 and stage in ("Champion","Ultimate","Mega"):
            move_id = unique[-1] if len(unique) > 1 else unique[0]
        else:
            idx = min(i * max(1, len(unique) // count), len(unique) - 1)
            move_id = unique[idx]
        result.append({"learn_level": lvl, "move_id": move_id})

    return result


def _make_stats(types: list[str], stage: str, seed: int = 0) -> dict:
    cfg = STAGE_CONFIG.get(stage, STAGE_CONFIG["Rookie"])
    lo, hi = cfg["stats"]
    rng = random.Random(seed)
    base = rng.randint(lo, hi)
    profile = STAT_PROFILES.get(types[0] if types else "Normal", STAT_PROFILES["Normal"])

    def s(key, delta=0):
        v = base + delta + profile.get(key, 0) * 5
        return max(10, min(255, v))

    return {
        "hp":     s("hp",     rng.randint(-5, 5)),
        "atk":    s("atk",    rng.randint(-5, 5)),
        "def":    s("def",    rng.randint(-5, 5)),
        "sp_atk": s("sp_atk", rng.randint(-5, 5)),
        "sp_def": s("sp_def", rng.randint(-5, 5)),
        "spd":    s("spd",    rng.randint(-5, 5)),
    }


def assign(entry: dict) -> dict:
    """Fill in moves, base_stats, catch_rate on an incomplete entry. Returns entry."""
    stage  = entry.get("stage", "Rookie")
    types  = entry.get("types", ["Normal"])
    seed   = entry.get("id", 0)

    if not entry.get("moves"):
        entry["moves"] = _pick_moves(types, stage, seed)

    if not entry.get("base_stats"):
        entry["base_stats"] = _make_stats(types, stage, seed)

    if not entry.get("catch_rate"):
        entry["catch_rate"] = STAGE_CONFIG.get(stage, {}).get("catch", 100)

    if not entry.get("description"):
        entry["description"] = f"A {stage}-level {types[0]}-type Digimon."

    entry.setdefault("digivolves_to", [])
    entry.setdefault("digivolves_from", [])

    return entry
