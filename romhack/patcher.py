#!/usr/bin/env python3
"""Pokemon FireRed → Digimon ROM patcher.

Usage:
    python patcher.py firered.gba [--output out.gba] [--patch-only]
"""
import sys
import struct
import json
import argparse
from pathlib import Path

HERE = Path(__file__).parent

sys.path.insert(0, str(HERE))
from offsets import (
    BASE_STATS, POKEMON_NAMES, STAT_ENTRY_SIZE, NAME_ENTRY_SIZE,
    STAT_HP, STAT_ATK, STAT_DEF, STAT_SPD, STAT_SPATK, STAT_SPDEF,
    STAT_TYPE1, STAT_TYPE2, STAT_CATCH_RATE, STAT_BASE_EXP,
    STAT_GENDER, STAT_GROWTH_RATE, STAT_FRIENDSHIP,
)
from verify import verify_rom
from encoders import encode_name
from ips import IpsPatch


def load_data():
    stats   = json.loads((HERE / "data/digimon_stats.json").read_text())
    names   = json.loads((HERE / "data/digimon_names.json").read_text())
    mapping = json.loads((HERE / "data/slot_mapping.json").read_text())
    return stats, names, mapping


def patch_rom(rom: bytearray, stats: dict, names: dict, mapping: dict) -> None:
    for slot_str, digi_id in mapping.items():
        if digi_id is None:
            continue
        slot = int(slot_str)
        if slot < 1 or slot > 386:
            continue

        did = str(digi_id)
        if did not in stats or did not in names:
            continue

        s = stats[did]
        name = names[did]

        # --- base stats (28-byte entry) ---
        base = BASE_STATS + (slot - 1) * STAT_ENTRY_SIZE
        rom[base + STAT_HP]          = min(255, s.get("hp",   50))
        rom[base + STAT_ATK]         = min(255, s.get("atk",  50))
        rom[base + STAT_DEF]         = min(255, s.get("def",  50))
        rom[base + STAT_SPD]         = min(255, s.get("spd",  50))
        rom[base + STAT_SPATK]       = min(255, s.get("spatk",50))
        rom[base + STAT_SPDEF]       = min(255, s.get("spdef",50))
        rom[base + STAT_TYPE1]       = s.get("type1", 0) & 0xFF
        rom[base + STAT_TYPE2]       = s.get("type2", 0) & 0xFF
        rom[base + STAT_CATCH_RATE]  = min(255, s.get("catch_rate", 45))
        rom[base + STAT_BASE_EXP]    = min(255, s.get("base_exp", 64))
        rom[base + STAT_GENDER]      = s.get("gender", 127) & 0xFF
        rom[base + STAT_GROWTH_RATE] = s.get("growth_rate", 3) & 0xFF
        rom[base + STAT_FRIENDSHIP]  = s.get("base_friendship", 70) & 0xFF

        # --- name (11 bytes) ---
        name_base = POKEMON_NAMES + (slot - 1) * NAME_ENTRY_SIZE
        encoded = encode_name(name, max_len=10)
        rom[name_base: name_base + NAME_ENTRY_SIZE] = encoded


def main():
    ap = argparse.ArgumentParser(description="Digimon FireRed ROM Patcher")
    ap.add_argument("rom", nargs="?", help="Path to FireRed ROM (.gba)")
    ap.add_argument("--output", "-o", default="firered_digimon.gba",
                    help="Output file (default: firered_digimon.gba)")
    ap.add_argument("--patch-only", action="store_true",
                    help="Output IPS patch instead of full ROM")
    args = ap.parse_args()

    if not args.rom:
        ap.print_help()
        sys.exit(0)

    rom_path = Path(args.rom)
    if not rom_path.exists():
        print(f"Error: ROM not found: {rom_path}")
        sys.exit(1)

    print(f"Verifying {rom_path} …")
    if not verify_rom(str(rom_path)):
        print("SHA-1 mismatch. Ensure you have Pokemon FireRed (BPRE v1.0).")
        sys.exit(1)

    rom_original = bytearray(rom_path.read_bytes())
    rom = bytearray(rom_original)

    print("Loading Digimon data …")
    stats, names, mapping = load_data()

    print("Patching …")
    patch_rom(rom, stats, names, mapping)

    if args.patch_only:
        patch = IpsPatch()
        for i, (orig, new) in enumerate(zip(rom_original, rom)):
            if orig != new:
                patch.add_record(i, bytes([new]))
        out = Path(args.output).with_suffix(".ips")
        patch.save(str(out))
        print(f"IPS patch saved to {out}")
    else:
        out = Path(args.output)
        out.write_bytes(rom)
        print(f"Patched ROM saved to {out}")


if __name__ == "__main__":
    main()
