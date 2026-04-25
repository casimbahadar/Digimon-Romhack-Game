from enum import Enum, auto

# ---------------------------------------------------------------------------
# Type system
# ---------------------------------------------------------------------------

TYPES = [
    "Normal", "Fire", "Water", "Plant", "Electric", "Ice",
    "Dragon", "Steel", "Holy", "Dark", "Fighting", "Flying", "Bug", "Poison",
]

# ---------------------------------------------------------------------------
# Attribute system (Digimon-specific)
# ---------------------------------------------------------------------------

ATTRIBUTES = ["Vaccine", "Data", "Virus", "Free"]

# Vaccine > Virus > Data > Vaccine  (circular advantage)
ATTRIBUTE_ADVANTAGE = {
    "Vaccine": "Virus",
    "Virus":   "Data",
    "Data":    "Vaccine",
}

ATTRIBUTE_MULT = 1.15  # damage multiplier when attacker has advantage

# ---------------------------------------------------------------------------
# Type chart  –  TYPE_CHART[attacker][defender] = multiplier
# Unlisted defender pairs default to 1.0
# ---------------------------------------------------------------------------

def _build_type_chart():
    types = TYPES
    chart = {t: {d: 1.0 for d in types} for t in types}

    def set_mult(attacker, pairs):
        for defender, mult in pairs.items():
            chart[attacker][defender] = mult

    set_mult("Normal",   {"Steel": 0.5})
    set_mult("Fire",     {"Plant": 2.0, "Ice": 2.0, "Bug": 2.0, "Steel": 2.0,
                          "Fire": 0.5, "Water": 0.5, "Dragon": 0.5})
    set_mult("Water",    {"Fire": 2.0,
                          "Water": 0.5, "Plant": 0.5, "Dragon": 0.5})
    set_mult("Plant",    {"Water": 2.0,
                          "Fire": 0.5, "Plant": 0.5, "Flying": 0.5,
                          "Bug": 0.5, "Steel": 0.5, "Dragon": 0.5, "Poison": 0.5})
    set_mult("Electric", {"Water": 2.0, "Flying": 2.0,
                          "Plant": 0.5, "Electric": 0.5, "Dragon": 0.5})
    set_mult("Ice",      {"Plant": 2.0, "Dragon": 2.0, "Flying": 2.0,
                          "Water": 0.5, "Ice": 0.5, "Steel": 0.5})
    set_mult("Dragon",   {"Dragon": 2.0,
                          "Steel": 0.5, "Holy": 0.0})
    set_mult("Steel",    {"Ice": 2.0, "Plant": 2.0, "Holy": 2.0,
                          "Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Steel": 0.5})
    set_mult("Holy",     {"Dragon": 2.0, "Dark": 2.0, "Fighting": 2.0,
                          "Holy": 0.5, "Steel": 0.5, "Poison": 0.5})
    set_mult("Dark",     {"Holy": 2.0,
                          "Dark": 0.5, "Fighting": 0.5, "Steel": 0.5})
    set_mult("Fighting", {"Normal": 2.0, "Ice": 2.0, "Steel": 2.0, "Dark": 2.0,
                          "Plant": 0.5, "Flying": 0.5, "Bug": 0.5,
                          "Poison": 0.5, "Holy": 0.5})
    set_mult("Flying",   {"Plant": 2.0, "Fighting": 2.0, "Bug": 2.0,
                          "Electric": 0.5, "Steel": 0.5})
    set_mult("Bug",      {"Plant": 2.0, "Dark": 2.0,
                          "Fire": 0.5, "Fighting": 0.5, "Flying": 0.5,
                          "Steel": 0.5, "Poison": 0.5, "Holy": 0.5})
    set_mult("Poison",   {"Plant": 2.0,
                          "Steel": 0.0, "Holy": 0.5, "Poison": 0.5})

    return chart

TYPE_CHART = _build_type_chart()

# ---------------------------------------------------------------------------
# Digivolution stages
# ---------------------------------------------------------------------------

STAGES = ["Baby", "Rookie", "Champion", "Ultimate", "Mega"]

# Minimum level required to digivolve *from* a given stage
STAGE_DIGIVOLVE_LEVEL = {
    "Baby":     10,
    "Rookie":   20,
    "Champion": 35,
    "Ultimate": 50,
}

# ---------------------------------------------------------------------------
# Experience / levelling
# ---------------------------------------------------------------------------

def exp_to_next_level(level, growth_rate="medium"):
    """Return the total XP needed to reach (level + 1)."""
    rates = {
        "fast":        0.7,
        "medium_fast": 0.8,
        "medium":      0.9,
        "slow":        1.2,
    }
    m = rates.get(growth_rate, 0.9)
    return int(((level + 1) ** 3) * m)

# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------

STATUS_EFFECTS = ["burn", "freeze", "paralysis", "poison", "sleep", "none"]

# Fraction of max HP dealt as damage at the end of each turn
STATUS_DAMAGE = {
    "burn":   1 / 8,
    "poison": 1 / 8,
}

# ---------------------------------------------------------------------------
# Battle / party limits
# ---------------------------------------------------------------------------

MAX_PARTY_SIZE = 6
MAX_MOVES = 4
MAX_LEVEL = 100
DIGI_EGG_CATCH_MULTIPLIER = 1.0  # standard DigiEgg catch rate multiplier

# ---------------------------------------------------------------------------
# Game-state enums
# ---------------------------------------------------------------------------

class GameState(Enum):
    TITLE           = auto()
    OVERWORLD       = auto()
    BATTLE_WILD     = auto()
    BATTLE_TRAINER  = auto()
    MENU            = auto()
    PAUSED          = auto()


class BattleState(Enum):
    PLAYER_CHOOSE   = auto()
    ENEMY_CHOOSE    = auto()
    EXECUTE_PLAYER  = auto()
    EXECUTE_ENEMY   = auto()
    DIGIVOLVE_PROMPT = auto()
    CATCH_ATTEMPT   = auto()
    BATTLE_END      = auto()

# ---------------------------------------------------------------------------
# UI colors (RGB)
# ---------------------------------------------------------------------------

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
RED        = (220, 50,  50)
BLUE       = (50,  100, 220)
GREEN      = (50,  180, 50)
YELLOW     = (240, 220, 50)
ORANGE     = (240, 150, 50)
PURPLE     = (150, 50,  220)
DARK_GRAY  = (60,  60,  60)
LIGHT_GRAY = (200, 200, 200)
SCREEN_BG  = (30,  30,  50)
HP_GREEN   = (100, 220, 100)
HP_YELLOW  = (220, 220, 50)
HP_RED     = (220, 60,  60)

# ---------------------------------------------------------------------------
# Per-type accent colors
# ---------------------------------------------------------------------------

TYPE_COLORS = {
    "Normal":   LIGHT_GRAY,
    "Fire":     (240, 100,  50),
    "Water":    (50,  150, 240),
    "Plant":    (80,  200,  80),
    "Electric": (240, 220,  50),
    "Ice":      (150, 230, 240),
    "Dragon":   (100,  50, 200),
    "Steel":    (180, 190, 200),
    "Holy":     (250, 240, 180),
    "Dark":     (80,   50, 100),
    "Fighting": (180,  80,  50),
    "Flying":   (150, 180, 240),
    "Bug":      (140, 190,  60),
    "Poison":   (160,  80, 200),
}

# ---------------------------------------------------------------------------
# Display / pygame settings
# ---------------------------------------------------------------------------

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60
FONT_SMALL    = 16
FONT_MEDIUM   = 22
FONT_LARGE    = 32
