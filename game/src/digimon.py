import json
import math
import random
from pathlib import Path
from .move import Move, get_move, load_move_db


class DigimonInstance:
    def __init__(self, species_data: dict, level: int, is_wild: bool = False):
        # Species identity
        self.species_id: int = species_data["id"]
        self.name: str = species_data["name"]
        self.stage: str = species_data["stage"]
        self.attribute: str = species_data["attribute"]
        self.types: list[str] = species_data["types"]
        self.base_stats: dict[str, int] = species_data["base_stats"]

        # Level & experience
        self.level: int = level
        self.exp: int = 0

        # Calculated stats (Pokemon formula)
        base_hp = self.base_stats["hp"]
        self.max_hp: int = math.floor(2 * base_hp * level / 100) + level + 10
        self.atk: int = math.floor(2 * self.base_stats["atk"] * level / 100) + 5
        self.def_: int = math.floor(2 * self.base_stats["def"] * level / 100) + 5
        self.sp_atk: int = math.floor(2 * self.base_stats["sp_atk"] * level / 100) + 5
        self.sp_def: int = math.floor(2 * self.base_stats["sp_def"] * level / 100) + 5
        self.spd: int = math.floor(2 * self.base_stats["spd"] * level / 100) + 5

        self.current_hp: int = self.max_hp

        # Moves — up to 4, highest-level moves learned at or below current level
        self.moves: list[Move] = self._pick_starting_moves(species_data["moves"], level)

        # Status
        self.status: str | None = None
        self.status_turns: int = 0

        # In-battle stage modifiers (-6 to +6)
        self.stage_mods: dict[str, int] = {
            "atk": 0,
            "def": 0,
            "sp_atk": 0,
            "sp_def": 0,
            "spd": 0,
            "accuracy": 0,
            "evasion": 0,
        }

        # Digivolution data
        self.digivolves_to: list[dict] = species_data.get("digivolves_to", [])

        # Misc
        self.is_wild: bool = is_wild
        self.nickname: str | None = None
        self.catch_rate: int = species_data.get("catch_rate", 100)

        # Keep species data for level-up move learning
        self._species_moves: list[dict] = species_data["moves"]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _pick_starting_moves(self, move_list: list[dict], level: int) -> list[Move]:
        """Return up to 4 Move objects: the highest-level ones learnable at or below level."""
        learnable = [m for m in move_list if m["learn_level"] <= level]
        # Sort descending by learn_level so we take the most recent ones
        learnable.sort(key=lambda m: m["learn_level"], reverse=True)
        selected = learnable[:4]
        move_db = load_move_db()
        return [Move(move_db[entry["move_id"]]) for entry in selected]

    def _recalc_stats(self):
        """Recalculate all stats for the current level (used after levelling up)."""
        base_hp = self.base_stats["hp"]
        self.max_hp = math.floor(2 * base_hp * self.level / 100) + self.level + 10
        self.atk = math.floor(2 * self.base_stats["atk"] * self.level / 100) + 5
        self.def_ = math.floor(2 * self.base_stats["def"] * self.level / 100) + 5
        self.sp_atk = math.floor(2 * self.base_stats["sp_atk"] * self.level / 100) + 5
        self.sp_def = math.floor(2 * self.base_stats["sp_def"] * self.level / 100) + 5
        self.spd = math.floor(2 * self.base_stats["spd"] * self.level / 100) + 5

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @staticmethod
    def stat_stage_mult(mod: int) -> float:
        """
        Pokemon-style stage multiplier.
        +1 = 1.5x, +2 = 2x, +3 = 2.5x ... +6 = 4x
        -1 = 0.667x, -2 = 0.5x ... -6 = 0.25x
        Formula: (2 + max(0, mod)) / (2 + max(0, -mod))
        """
        return (2 + max(0, mod)) / (2 + max(0, -mod))

    @property
    def effective_atk(self) -> float:
        return self.atk * self.stat_stage_mult(self.stage_mods["atk"])

    @property
    def effective_def(self) -> float:
        return self.def_ * self.stat_stage_mult(self.stage_mods["def"])

    @property
    def effective_sp_atk(self) -> float:
        return self.sp_atk * self.stat_stage_mult(self.stage_mods["sp_atk"])

    @property
    def effective_sp_def(self) -> float:
        return self.sp_def * self.stat_stage_mult(self.stage_mods["sp_def"])

    @property
    def effective_spd(self) -> float:
        return self.spd * self.stat_stage_mult(self.stage_mods["spd"])

    @property
    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    @property
    def display_name(self) -> str:
        return self.nickname if self.nickname else self.name

    # ------------------------------------------------------------------
    # HP / healing
    # ------------------------------------------------------------------

    def take_damage(self, amount: int):
        """Reduce current HP by amount, clamped to 0."""
        self.current_hp = max(0, self.current_hp - amount)

    def heal(self, amount: int):
        """Increase current HP by amount, clamped to max_hp."""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def heal_fraction(self, fraction: float):
        """Heal a fraction of max HP (e.g. 0.5 = half)."""
        self.heal(math.floor(self.max_hp * fraction))

    # ------------------------------------------------------------------
    # Status conditions
    # ------------------------------------------------------------------

    def apply_status(self, status: str) -> bool:
        """
        Apply a status condition if none is currently active.
        Returns True if the status was successfully applied.
        """
        if self.status is not None:
            return False
        self.status = status
        if status == "sleep":
            self.status_turns = random.randint(1, 3)
        elif status == "freeze":
            self.status_turns = random.randint(1, 4)
        else:
            self.status_turns = 0
        return True

    def tick_status(self) -> int:
        """
        Apply end-of-turn status effects.
        Returns the damage dealt (0 if none).
        Decrements remaining turns for sleep/freeze.
        """
        if self.status is None:
            return 0

        damage = 0

        if self.status == "burn":
            damage = math.floor(self.max_hp / 8)
            self.take_damage(damage)

        elif self.status == "poison":
            damage = math.floor(self.max_hp / 8)
            self.take_damage(damage)

        elif self.status in ("sleep", "freeze"):
            if self.status_turns > 0:
                self.status_turns -= 1
            if self.status_turns <= 0:
                self.status = None

        return damage

    # ------------------------------------------------------------------
    # Stage modifiers
    # ------------------------------------------------------------------

    def apply_stage_mod(self, stat: str, stages: int):
        """Apply a stat stage change, clamped to the range [-6, +6]."""
        current = self.stage_mods.get(stat, 0)
        self.stage_mods[stat] = max(-6, min(6, current + stages))

    # ------------------------------------------------------------------
    # Move availability
    # ------------------------------------------------------------------

    def can_move(self) -> bool:
        """Return False if the Digimon is frozen or asleep."""
        if self.status == "freeze" and self.status_turns > 0:
            return False
        if self.status == "sleep" and self.status_turns > 0:
            return False
        return True

    # ------------------------------------------------------------------
    # Experience & levelling
    # ------------------------------------------------------------------

    def gain_exp(self, amount: int) -> list[str]:
        """
        Add exp, level up as needed.
        Returns a list of human-readable messages (level-up notices, new moves, etc.).
        """
        messages: list[str] = []
        self.exp += amount

        # Experience threshold: simple medium-fast curve — level^3
        while self.level < 100:
            exp_needed = self.level ** 3
            if self.exp < exp_needed:
                break

            self.exp -= exp_needed
            self.level += 1

            # Recalculate stats and note HP increase
            old_max_hp = self.max_hp
            self._recalc_stats()
            hp_gain = self.max_hp - old_max_hp
            self.current_hp += hp_gain  # bonus HP on level-up

            messages.append(f"{self.display_name} grew to level {self.level}!")

            # Check for new moves at this level
            move_db = load_move_db()
            for entry in self._species_moves:
                if entry["learn_level"] == self.level and len(self.moves) < 4:
                    new_move = Move(move_db[entry["move_id"]])
                    self.moves.append(new_move)
                    messages.append(
                        f"{self.display_name} learned {new_move.name}!"
                    )

        return messages

    # ------------------------------------------------------------------
    # Digivolution
    # ------------------------------------------------------------------

    def can_digivolve(self) -> bool:
        """Return True if any digivolution target's level requirement is met."""
        if not self.digivolves_to:
            return False
        return any(self.level >= entry["min_level"] for entry in self.digivolves_to)

    def get_digivolve_target(self) -> dict | None:
        """Return the first digivolves_to entry whose min_level requirement is met."""
        for entry in self.digivolves_to:
            if self.level >= entry["min_level"]:
                return entry
        return None

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "species_id": self.species_id,
            "level": self.level,
            "exp": self.exp,
            "current_hp": self.current_hp,
            "nickname": self.nickname,
            "status": self.status,
            "status_turns": self.status_turns,
            "stage_mods": self.stage_mods.copy(),
            "is_wild": self.is_wild,
            "moves": [m.to_dict() for m in self.moves],
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
        digimon_db: dict,
        move_db: dict,
    ) -> "DigimonInstance":
        species_data = digimon_db[data["species_id"]]
        instance = cls(species_data, data["level"], is_wild=data.get("is_wild", False))

        instance.exp = data.get("exp", 0)
        instance.current_hp = data["current_hp"]
        instance.nickname = data.get("nickname")
        instance.status = data.get("status")
        instance.status_turns = data.get("status_turns", 0)
        instance.stage_mods = data.get("stage_mods", instance.stage_mods)

        # Restore moves from save data (preserves current PP)
        if "moves" in data:
            instance.moves = [Move.from_save(m, move_db) for m in data["moves"]]

        return instance

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self):
        return (
            f"DigimonInstance({self.display_name}, Lv{self.level}, "
            f"HP {self.current_hp}/{self.max_hp}, {self.status or 'OK'})"
        )


# ---------------------------------------------------------------------------
# Module-level DB helpers
# ---------------------------------------------------------------------------

_DIGIMON_DB: dict[int, dict] = {}


def load_digimon_db(path=None) -> dict[int, dict]:
    global _DIGIMON_DB
    if _DIGIMON_DB:
        return _DIGIMON_DB
    if path is None:
        path = Path(__file__).parent.parent / "data" / "digimon.json"
    with open(path) as f:
        data = json.load(f)
    _DIGIMON_DB = {d["id"]: d for d in data}
    return _DIGIMON_DB


def create_digimon(species_id: int, level: int, is_wild: bool = False) -> DigimonInstance:
    db = load_digimon_db()
    return DigimonInstance(db[species_id], level, is_wild)
