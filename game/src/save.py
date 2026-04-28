import json
import os
from datetime import datetime
from pathlib import Path

from .trainer import Trainer

# ---------------------------------------------------------------------------
# Save directory
# ---------------------------------------------------------------------------

SAVE_DIR: Path = Path.home() / ".digimon_game" / "saves"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_save_dir() -> None:
    """Create SAVE_DIR (and any missing parents) if it does not yet exist."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def _save_path(slot: int) -> Path:
    return SAVE_DIR / f"save_{slot}.json"


def _format_play_time(seconds: int) -> str:
    """Return a human-readable play-time string, e.g. '2h 34m 10s'."""
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h}h {m:02d}m {s:02d}s"


# ---------------------------------------------------------------------------
# Core save / load API
# ---------------------------------------------------------------------------

def save_game(trainer: Trainer, slot: int = 0) -> str:
    """Serialize *trainer* and write it to save slot *slot*.

    Metadata (timestamp, play_time) is embedded in the file alongside the
    trainer payload.

    Returns the absolute path of the written save file as a string.
    """
    ensure_save_dir()

    payload = {
        "metadata": {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "play_time": trainer.play_time_seconds,
            "play_time_formatted": _format_play_time(trainer.play_time_seconds),
            "trainer_name": trainer.name,
            "slot": slot,
            "version": 1,
        },
        "trainer": trainer.to_dict(),
    }

    path = _save_path(slot)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)

    return str(path)


def load_game(slot: int = 0) -> Trainer | None:
    """Load and deserialize the trainer from save slot *slot*.

    Returns a :class:`Trainer` on success, or ``None`` when the save file
    does not exist or cannot be parsed.
    """
    path = _save_path(slot)
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return Trainer.from_dict(payload["trainer"])
    except (json.JSONDecodeError, KeyError, Exception):
        return None


def list_saves() -> list[dict]:
    """Return a list of metadata dicts for every existing save slot.

    Each entry contains:
    - ``slot``         – integer slot number
    - ``timestamp``    – ISO-8601 string from when the file was written
    - ``trainer_name`` – name of the saved trainer
    - ``play_time``    – play time in seconds
    - ``play_time_formatted`` – human-readable play time string
    """
    ensure_save_dir()
    saves: list[dict] = []

    for save_file in sorted(SAVE_DIR.glob("save_*.json")):
        # Parse the slot number from the filename
        stem = save_file.stem          # e.g. "save_0"
        try:
            slot = int(stem.split("_", 1)[1])
        except (IndexError, ValueError):
            continue

        try:
            with save_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            meta = payload.get("metadata", {})
            saves.append(
                {
                    "slot": slot,
                    "timestamp": meta.get("timestamp", ""),
                    "trainer_name": meta.get("trainer_name", "Unknown"),
                    "play_time": meta.get("play_time", 0),
                    "play_time_formatted": meta.get(
                        "play_time_formatted",
                        _format_play_time(meta.get("play_time", 0)),
                    ),
                }
            )
        except (json.JSONDecodeError, KeyError):
            # Corrupted file — include a minimal entry so the UI can flag it
            saves.append(
                {
                    "slot": slot,
                    "timestamp": "",
                    "trainer_name": "??? (corrupted)",
                    "play_time": 0,
                    "play_time_formatted": "0h 00m 00s",
                }
            )

    return saves


def delete_save(slot: int) -> bool:
    """Delete the save file for *slot*.

    Returns True when the file was found and deleted, False otherwise.
    """
    path = _save_path(slot)
    if path.exists():
        path.unlink()
        return True
    return False
