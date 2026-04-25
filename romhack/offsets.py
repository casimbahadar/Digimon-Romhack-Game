"""FireRed (BPRE v1.0) ROM data table offsets."""

# SHA-1 of target ROM
TARGET_SHA1 = "DD5945DB9B930750CB39D00C84DA8571FEEBF417"
ROM_NAME = "Pokemon FireRed (BPRE v1.0)"

# Table offsets
BASE_STATS    = 0x254784   # 28 bytes per entry × 386 entries
POKEMON_NAMES = 0x245EE0   # 11 bytes per name (10 chars + 0xFF terminator)
POKEDEX_PTR   = 0x44E8A4   # pointers to dex description strings
MOVE_DATA     = 0x250C04   # 12 bytes per move × 354 moves
TYPE_CHART    = 0x24F1A0   # type effectiveness table
LEVELUP_MOVES = 0x25D7B4   # level-up move pointer table

# Per-entry sizes
STAT_ENTRY_SIZE = 28
NAME_ENTRY_SIZE = 11
MOVE_ENTRY_SIZE = 12

# Stat entry byte offsets within a 28-byte entry
STAT_HP          = 0x00
STAT_ATK         = 0x01
STAT_DEF         = 0x02
STAT_SPD         = 0x03
STAT_SPATK       = 0x04
STAT_SPDEF       = 0x05
STAT_TYPE1       = 0x06
STAT_TYPE2       = 0x07
STAT_CATCH_RATE  = 0x08
STAT_BASE_EXP    = 0x09
STAT_EV_YIELD    = 0x0A   # 2 bytes
STAT_ITEM1       = 0x0C   # 2 bytes
STAT_ITEM2       = 0x0E   # 2 bytes
STAT_GENDER      = 0x10
STAT_EGG_CYCLES  = 0x11
STAT_FRIENDSHIP  = 0x12
STAT_GROWTH_RATE = 0x13
STAT_EGG_GROUP1  = 0x14   # 2 bytes
STAT_EGG_GROUP2  = 0x16   # 2 bytes
STAT_ABILITY1    = 0x18
STAT_ABILITY2    = 0x19
STAT_SAFARI_RATE = 0x1A
STAT_COLOR_FLIP  = 0x1B

# FireRed type IDs
TYPE_IDS = {
    "Normal":   0,
    "Fighting": 1,
    "Flying":   2,
    "Poison":   3,
    "Ground":   4,
    "Rock":     5,
    "Bug":      6,
    "Ghost":    7,
    "Steel":    8,
    "Fire":     9,
    "Water":    10,
    "Grass":    11,
    "Electric": 12,
    "Psychic":  13,
    "Ice":      14,
    "Dragon":   15,
    "Dark":     16,
}
