import json
import random
from pathlib import Path

from .digimon import DigimonInstance, create_digimon, load_digimon_db
from .move import load_move_db

# ---------------------------------------------------------------------------
# Item definitions
# ---------------------------------------------------------------------------

ITEMS: dict[str, dict] = {
    "digi_egg": {
        "name": "DigiEgg",
        "type": "ball",
        "catch_mult": 1.0,
        "description": "A standard egg used to capture wild Digimon.",
    },
    "great_egg": {
        "name": "GreatEgg",
        "type": "ball",
        "catch_mult": 1.5,
        "description": "A higher quality DigiEgg.",
    },
    "ultra_egg": {
        "name": "UltraEgg",
        "type": "ball",
        "catch_mult": 2.0,
        "description": "An ultra-quality DigiEgg.",
    },
    "digi_potion": {
        "name": "DigiPotion",
        "type": "heal",
        "heal_amount": 20,
        "description": "Restores 20 HP.",
    },
    "max_potion": {
        "name": "MaxPotion",
        "type": "heal",
        "heal_amount": 999,
        "description": "Fully restores HP.",
    },
    "revive": {
        "name": "Revive",
        "type": "revive",
        "heal_fraction": 0.5,
        "description": "Revives a fainted Digimon to half HP.",
    },
    "antidote": {
        "name": "Antidote",
        "type": "status_cure",
        "cures": ["poison"],
        "description": "Cures poison.",
    },
    "full_heal": {
        "name": "FullHeal",
        "type": "status_cure",
        "cures": "all",
        "description": "Cures all status conditions.",
    },
    "digital_meat": {
        "name": "Digital Meat",
        "type": "exp_boost",
        "exp_amount": 500,
        "description": "Gives 500 EXP to a Digimon.",
    },
}


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------

class Trainer:
    def __init__(self, name: str = "Tamer") -> None:
        self.name: str = name
        self.party: list[DigimonInstance] = []          # max 6
        self.pc_box: list[DigimonInstance] = []         # unlimited
        self.items: dict[str, int] = {                  # item_id -> count
            "digi_egg": 5,
            "digi_potion": 3,
        }
        self.money: int = 3000
        self.badges: list[str] = []
        self.seen_digimon: set[int] = set()
        self.caught_digimon: set[int] = set()
        self.current_area: str = "File City"
        self.steps: int = 0
        self.play_time_seconds: int = 0

    # ------------------------------------------------------------------
    # Party management
    # ------------------------------------------------------------------

    def add_to_party(self, digi: DigimonInstance) -> bool:
        """Add *digi* to the party if there is room, otherwise send to PC box.

        Returns True when the Digimon was added to the active party, False
        when it was sent to the PC box instead.
        """
        if len(self.party) < 6:
            self.party.append(digi)
            return True
        self.pc_box.append(digi)
        return False

    def remove_from_party(self, index: int) -> DigimonInstance | None:
        """Remove and return the Digimon at *index*, or None if out of range."""
        if 0 <= index < len(self.party):
            return self.party.pop(index)
        return None

    def swap_party(self, i: int, j: int) -> None:
        """Swap the party positions of the Digimon at indices *i* and *j*."""
        if 0 <= i < len(self.party) and 0 <= j < len(self.party):
            self.party[i], self.party[j] = self.party[j], self.party[i]

    # ------------------------------------------------------------------
    # Active Digimon helpers
    # ------------------------------------------------------------------

    def active_digimon(self) -> DigimonInstance | None:
        """Return the first non-fainted Digimon in the party, or None."""
        for digi in self.party:
            if digi.current_hp > 0:
                return digi
        return None

    def all_fainted(self) -> bool:
        """Return True when every Digimon in the party has fainted."""
        return all(digi.current_hp <= 0 for digi in self.party)

    # ------------------------------------------------------------------
    # Item management
    # ------------------------------------------------------------------

    def has_item(self, item_id: str) -> bool:
        """Return True when the trainer owns at least one of *item_id*."""
        return self.items.get(item_id, 0) > 0

    def add_item(self, item_id: str, count: int = 1) -> None:
        """Add *count* copies of *item_id* to the trainer's bag."""
        if item_id not in ITEMS:
            raise ValueError(f"Unknown item: {item_id!r}")
        self.items[item_id] = self.items.get(item_id, 0) + count

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        """Remove *count* copies of *item_id*.

        Returns True on success, False if the trainer does not have enough.
        """
        current = self.items.get(item_id, 0)
        if current < count:
            return False
        self.items[item_id] = current - count
        if self.items[item_id] == 0:
            del self.items[item_id]
        return True

    def use_item(self, item_id: str, target: DigimonInstance) -> str:
        """Consume one of *item_id* from the bag and apply its effect to *target*.

        Returns a human-readable result string describing what happened.
        Raises ValueError for unknown items or when the trainer has none left.
        """
        if item_id not in ITEMS:
            raise ValueError(f"Unknown item: {item_id!r}")
        if not self.has_item(item_id):
            raise ValueError(f"No {ITEMS[item_id]['name']} remaining.")

        item = ITEMS[item_id]
        item_type = item["type"]

        # ---- heal --------------------------------------------------------
        if item_type == "heal":
            if target.current_hp <= 0:
                return f"{target.nickname} has fainted and cannot be healed."
            if target.current_hp >= target.max_hp:
                return f"{target.nickname}'s HP is already full."
            amount = item["heal_amount"]
            before = target.current_hp
            target.current_hp = min(target.max_hp, target.current_hp + amount)
            healed = target.current_hp - before
            self.remove_item(item_id)
            return f"{target.nickname} restored {healed} HP."

        # ---- revive ------------------------------------------------------
        elif item_type == "revive":
            if target.current_hp > 0:
                return f"{target.nickname} has not fainted."
            restore_hp = max(1, int(target.max_hp * item["heal_fraction"]))
            target.current_hp = restore_hp
            self.remove_item(item_id)
            return f"{target.nickname} was revived with {restore_hp} HP."

        # ---- status cure -------------------------------------------------
        elif item_type == "status_cure":
            if target.current_hp <= 0:
                return f"{target.nickname} has fainted and cannot use items."
            status = getattr(target, "status", "none")
            cures = item["cures"]
            if status == "none":
                return f"{target.nickname} has no status condition to cure."
            if cures == "all" or status in cures:
                target.status = "none"
                self.remove_item(item_id)
                return f"{target.nickname}'s {status} was cured."
            return f"{item['name']} cannot cure {status}."

        # ---- exp boost ---------------------------------------------------
        elif item_type == "exp_boost":
            if target.current_hp <= 0:
                return f"{target.nickname} has fainted and cannot gain EXP."
            exp_gain = item["exp_amount"]
            target.gain_exp(exp_gain)
            self.remove_item(item_id)
            return f"{target.nickname} gained {exp_gain} EXP."

        # ---- ball (not usable outside battle via bag) --------------------
        elif item_type == "ball":
            return f"{item['name']} must be used during a wild Digimon encounter."

        return f"{item['name']} had no effect."

    # ------------------------------------------------------------------
    # Catching
    # ------------------------------------------------------------------

    def catch_digimon(
        self,
        digi: DigimonInstance,
        ball_id: str = "digi_egg",
    ) -> bool:
        """Attempt to catch *digi* using the ball identified by *ball_id*.

        Uses the Pokemon-style catch formula:
            catch_value = (3*max_hp - 2*current_hp) * catch_rate * ball_mult
                          / (3 * max_hp)

        catch_value is clamped to [0, 255].  The attempt succeeds when
        random.randint(0, 255) < catch_value.

        If the capture is successful the Digimon is recorded in the Pokédex
        and added to the party (or PC box when the party is full).

        Returns True when the Digimon was caught.
        """
        if ball_id not in ITEMS or ITEMS[ball_id]["type"] != "ball":
            raise ValueError(f"Unknown ball item: {ball_id!r}")
        if not self.has_item(ball_id):
            raise ValueError(f"No {ITEMS[ball_id]['name']} remaining.")

        ball_mult: float = ITEMS[ball_id]["catch_mult"]
        catch_rate: int = getattr(digi, "catch_rate", 45)
        max_hp: int = digi.max_hp
        current_hp: int = max(1, digi.current_hp)  # avoid division edge cases

        catch_value = (
            (3 * max_hp - 2 * current_hp) * catch_rate * ball_mult
            / (3 * max_hp)
        )
        catch_value = max(0.0, min(255.0, catch_value))

        self.remove_item(ball_id)

        caught = random.randint(0, 255) < catch_value
        if caught:
            digi_id: int = getattr(digi, "digi_id", 0)
            self.seen_digimon.add(digi_id)
            self.caught_digimon.add(digi_id)
            self.add_to_party(digi)

        return caught

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the trainer to a JSON-compatible dict."""
        return {
            "name": self.name,
            "party": [d.to_dict() for d in self.party],
            "pc_box": [d.to_dict() for d in self.pc_box],
            "items": self.items,
            "money": self.money,
            "badges": self.badges,
            "seen_digimon": sorted(self.seen_digimon),
            "caught_digimon": sorted(self.caught_digimon),
            "current_area": self.current_area,
            "steps": self.steps,
            "play_time_seconds": self.play_time_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trainer":
        """Deserialize a Trainer from a previously saved dict."""
        move_db = load_move_db()
        digimon_db = load_digimon_db()

        trainer = cls(name=data.get("name", "Tamer"))
        trainer.party = [
            DigimonInstance.from_dict(d, digimon_db, move_db)
            for d in data.get("party", [])
        ]
        trainer.pc_box = [
            DigimonInstance.from_dict(d, digimon_db, move_db)
            for d in data.get("pc_box", [])
        ]
        trainer.items = data.get("items", {})
        trainer.money = data.get("money", 3000)
        trainer.badges = data.get("badges", [])
        trainer.seen_digimon = set(data.get("seen_digimon", []))
        trainer.caught_digimon = set(data.get("caught_digimon", []))
        trainer.current_area = data.get("current_area", "File City")
        trainer.steps = data.get("steps", 0)
        trainer.play_time_seconds = data.get("play_time_seconds", 0)
        return trainer

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Trainer({self.name!r}, party={len(self.party)}, "
            f"money={self.money}, badges={self.badges})"
        )
