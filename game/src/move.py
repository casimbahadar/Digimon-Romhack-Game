import json
from pathlib import Path


class Move:
    def __init__(self, move_data: dict):
        self.id = move_data["id"]
        self.name = move_data["name"]
        self.type = move_data["type"]
        self.category = move_data["category"]  # "Physical", "Special", "Status"
        self.power = move_data["power"]
        self.accuracy = move_data["accuracy"]
        self.pp_max = move_data["pp"]
        self.pp_current = move_data["pp"]
        self.effect = move_data.get("effect")
        self.effect_chance = move_data.get("effect_chance", 0)
        self.priority = move_data.get("priority", 0)
        self.description = move_data.get("description", "")

    def use(self) -> bool:
        if self.pp_current > 0:
            self.pp_current -= 1
            return True
        return False

    def restore_pp(self, amount: int = None):
        if amount is None:
            self.pp_current = self.pp_max
        else:
            self.pp_current = min(self.pp_max, self.pp_current + amount)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pp_current": self.pp_current,
            "pp_max": self.pp_max,
        }

    @classmethod
    def from_save(cls, save_data: dict, move_db: dict) -> "Move":
        m = cls(move_db[save_data["id"]])
        m.pp_current = save_data["pp_current"]
        return m

    def __repr__(self):
        return f"Move({self.name}, {self.type}, {self.power}pw, {self.pp_current}/{self.pp_max}pp)"


_MOVE_DB: dict[str, dict] = {}


def load_move_db(path: str = None) -> dict[str, dict]:
    global _MOVE_DB
    if _MOVE_DB:
        return _MOVE_DB
    if path is None:
        path = Path(__file__).parent.parent / "data" / "moves.json"
    with open(path) as f:
        moves = json.load(f)
    _MOVE_DB = {m["id"]: m for m in moves}
    return _MOVE_DB


def get_move(move_id: str) -> Move:
    db = load_move_db()
    return Move(db[move_id])
