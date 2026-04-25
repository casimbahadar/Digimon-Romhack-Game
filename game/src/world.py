# World / overworld state manager

import json
import random
from pathlib import Path

from .digimon import DigimonInstance, create_digimon, load_digimon_db
from .trainer import Trainer
from .constants import GameState


# ---------------------------------------------------------------------------
# Module-level areas DB cache
# ---------------------------------------------------------------------------

_AREAS_DB: dict[str, dict] = {}


def load_areas_db(path=None) -> dict[str, dict]:
    """Load and cache areas.json, keyed by area id.

    Subsequent calls return the cached dict without re-reading the file.
    """
    global _AREAS_DB
    if _AREAS_DB:
        return _AREAS_DB
    if path is None:
        path = Path(__file__).parent.parent / "data" / "areas.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _AREAS_DB = {area["id"]: area for area in data}
    return _AREAS_DB


# ---------------------------------------------------------------------------
# World class
# ---------------------------------------------------------------------------

class World:
    """Manages the overworld state: areas, movement, and wild encounters."""

    def __init__(self, trainer: Trainer) -> None:
        self.trainer = trainer
        self.areas: dict[str, dict] = self.load_areas()

        # Start in the trainer's saved area if valid; otherwise fall back to
        # the first area in the data file.
        first_area_id = next(iter(self.areas))
        if trainer.current_area in self.areas:
            # trainer.current_area is a name string from old saves — look up
            # by name or id.
            self.current_area_id: str = trainer.current_area
        else:
            # Try matching by area name (trainer.current_area may store the
            # human-readable name rather than the id).
            matched = next(
                (aid for aid, a in self.areas.items()
                 if a["name"] == trainer.current_area),
                None,
            )
            self.current_area_id = matched if matched else first_area_id

        # Keep trainer in sync
        trainer.current_area = self.current_area_id

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_areas(self, path=None) -> dict[str, dict]:
        """Read game/data/areas.json and return a dict keyed by area id."""
        return load_areas_db(path)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def move_to(self, area_id: str) -> None:
        """Change the current area to *area_id* and update the trainer."""
        if area_id not in self.areas:
            raise ValueError(f"Unknown area id: {area_id!r}")
        self.current_area_id = area_id
        self.trainer.current_area = area_id

    def get_current_area(self) -> dict:
        """Return the dict for the current area."""
        return self.areas[self.current_area_id]

    def connected_areas(self) -> list[str]:
        """Return the list of area ids that connect to the current area."""
        return self.get_current_area().get("connections", [])

    # ------------------------------------------------------------------
    # Encounters
    # ------------------------------------------------------------------

    def check_wild_encounter(self, steps: int = 1) -> "DigimonInstance | None":
        """Roll for a wild encounter.

        Each step has a 1/20 (5 %) chance of triggering an encounter.  If
        triggered, a species is randomly selected from the current area's
        ``wild_encounters`` list using the ``weight`` field, then spawned at
        a random level within [min_level, max_level].

        Returns a wild :class:`DigimonInstance` when an encounter occurs, or
        ``None`` otherwise.
        """
        area = self.get_current_area()
        wild_table = area.get("wild_encounters", [])
        if not wild_table:
            return None

        for _ in range(steps):
            if random.randint(1, 20) != 1:
                continue

            # Encounter triggered — weighted random species selection
            weights = [entry["weight"] for entry in wild_table]
            entry = random.choices(wild_table, weights=weights, k=1)[0]

            level = random.randint(entry["min_level"], entry["max_level"])
            try:
                wild = create_digimon(entry["species_id"], level, is_wild=True)
            except (KeyError, Exception):
                # species_id not in digimon DB yet — skip silently
                return None
            return wild

        return None

    def get_trainer_encounters(self) -> list[dict]:
        """Return the list of trainer encounter dicts for the current area."""
        return self.get_current_area().get("trainers", [])

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        area = self.get_current_area()
        return (
            f"World(area={area['name']!r}, "
            f"connections={self.connected_areas()})"
        )
