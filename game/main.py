"""
Digimon Fan Game — entry point.

Run with:
    python -m game.main          (from the repo root)
  or
    python game/main.py          (from the repo root, sys.path adjusted below)
"""

import sys
import os

# Ensure 'game/' is on sys.path so 'from src.xxx import ...' works when the
# script is run directly (e.g. python game/main.py).
_GAME_DIR = os.path.dirname(os.path.abspath(__file__))
if _GAME_DIR not in sys.path:
    sys.path.insert(0, _GAME_DIR)

import pygame

from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    GameState, BattleState,
    WHITE, BLACK, DARK_GRAY, LIGHT_GRAY, YELLOW, RED,
)
from src.digimon import create_digimon, load_digimon_db
from src.trainer import Trainer
from src.world import World
from src import ui
from src import save as save_mod

# ---------------------------------------------------------------------------
# Optional battle import — battle.py may not exist yet.
# A lightweight stub is provided so the rest of the game loop still runs.
# ---------------------------------------------------------------------------

try:
    from src import battle as battle_mod
    _BATTLE_AVAILABLE = True
except ImportError:
    _BATTLE_AVAILABLE = False
    battle_mod = None


# ---------------------------------------------------------------------------
# Minimal Battle stub
# Used when src/battle.py is absent so the game loop can still demonstrate
# the BATTLE state without crashing.
# ---------------------------------------------------------------------------

class _StubBattle:
    """Minimal stand-in for a real Battle object."""

    def __init__(self, player_digi, enemy_digi, is_wild: bool = True):
        self.player_active = player_digi
        self.enemy_active = enemy_digi
        self.is_wild = is_wild
        self.state = BattleState.PLAYER_CHOOSE
        self._messages: list[str] = [
            f"A wild {enemy_digi.display_name} appeared!",
        ]

    def execute_turn(self, player_move_idx: int) -> list[str]:
        """Very basic damage exchange, returns message lines."""
        msgs = []
        player = self.player_active
        enemy = self.enemy_active

        # Player attacks
        if player.moves and player_move_idx < len(player.moves):
            move = player.moves[player_move_idx]
            if move.use():
                dmg = max(1, (player.atk * move.power) // max(1, enemy.def_ * 5))
                enemy.take_damage(dmg)
                msgs.append(f"{player.display_name} used {move.name}!")
                msgs.append(f"Dealt {dmg} damage to {enemy.display_name}.")
            else:
                msgs.append(f"{move.name} has no PP left!")
        else:
            msgs.append(f"{player.display_name} did nothing.")

        if enemy.is_fainted:
            msgs.append(f"{enemy.display_name} fainted!")
            self.state = BattleState.BATTLE_END
            return msgs

        # Enemy attacks (random move)
        import random
        if enemy.moves:
            emove = random.choice(enemy.moves)
            emove.use()
            edmg = max(1, (enemy.atk * emove.power) // max(1, player.def_ * 5))
            player.take_damage(edmg)
            msgs.append(f"{enemy.display_name} used {emove.name}!")
            msgs.append(f"Dealt {edmg} damage to {player.display_name}.")

        if player.is_fainted:
            msgs.append(f"{player.display_name} fainted!")
            self.state = BattleState.BATTLE_END

        return msgs

    def attempt_run(self) -> tuple[bool, str]:
        """50 % chance to escape."""
        import random
        if random.random() < 0.5:
            return True, "Got away safely!"
        return False, "Can't escape!"


def _make_battle(player_digi, enemy_digi, is_wild: bool = True):
    """Return a real Battle or the stub, whichever is available."""
    if _BATTLE_AVAILABLE and hasattr(battle_mod, "Battle"):
        return battle_mod.Battle(player_digi, enemy_digi, is_wild=is_wild)
    return _StubBattle(player_digi, enemy_digi, is_wild=is_wild)


# ---------------------------------------------------------------------------
# Default trainer / starter setup
# ---------------------------------------------------------------------------

def _create_default_trainer() -> Trainer:
    """Return a fresh Trainer with Agumon (species_id=21) at level 5.

    Falls back gracefully when digimon.json is missing.
    """
    trainer = Trainer(name="Tamer")
    try:
        agumon = create_digimon(21, 5)
        trainer.add_to_party(agumon)
    except Exception:
        # digimon.json not present — party stays empty
        pass
    return trainer


# ---------------------------------------------------------------------------
# Game loop helpers
# ---------------------------------------------------------------------------

def _handle_title(event, game_state: GameState) -> GameState:
    """Process events on the TITLE screen."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        return GameState.OVERWORLD
    return game_state


def _handle_overworld(event, game_state: GameState, trainer: Trainer,
                      world: World, battle_ctx: dict) -> GameState:
    """Process events on the OVERWORLD screen.

    Returns the new GameState.  Sets up battle_ctx when an encounter starts.
    """
    if event.type != pygame.KEYDOWN:
        return game_state

    if event.key == pygame.K_SPACE:
        # Simulate one step
        trainer.steps += 1
        wild = world.check_wild_encounter(steps=1)
        if wild is not None:
            active = trainer.active_digimon()
            if active:
                battle_ctx["battle"] = _make_battle(active, wild, is_wild=True)
                battle_ctx["messages"] = [f"A wild {wild.display_name} appeared!"]
                battle_ctx["selected_move"] = 0
                return GameState.BATTLE_WILD
            # No usable Digimon — skip battle silently

    elif event.key in (pygame.K_UP, pygame.K_DOWN,
                       pygame.K_LEFT, pygame.K_RIGHT):
        # Arrow keys cycle through connected areas (just move message for now)
        connections = world.connected_areas()
        if connections:
            # Pick area based on direction key
            key_to_idx = {
                pygame.K_UP:    0,
                pygame.K_RIGHT: 1,
                pygame.K_DOWN:  2,
                pygame.K_LEFT:  3,
            }
            idx = key_to_idx[event.key] % len(connections)
            dest = connections[idx]
            dest_name = world.areas.get(dest, {}).get("name", dest)
            battle_ctx["messages"] = [f"Moved toward {dest_name}."]

    return game_state


def _handle_battle(event, game_state: GameState, trainer: Trainer,
                   world: World, battle_ctx: dict) -> GameState:
    """Process events during BATTLE_WILD (or BATTLE_TRAINER).

    Returns the new GameState after processing.
    """
    if event.type != pygame.KEYDOWN:
        return game_state

    battle = battle_ctx.get("battle")
    if battle is None:
        return GameState.OVERWORLD

    messages: list[str] = battle_ctx.setdefault("messages", [])
    selected_move: int = battle_ctx.get("selected_move", 0)

    # --- Move selection (1 / 2 / 3 / 4) ------------------------------------
    move_keys = {
        pygame.K_1: 0,
        pygame.K_2: 1,
        pygame.K_3: 2,
        pygame.K_4: 3,
    }
    if event.key in move_keys and battle.state == BattleState.PLAYER_CHOOSE:
        new_idx = move_keys[event.key]
        player = battle.player_active
        if new_idx < len(player.moves):
            battle_ctx["selected_move"] = new_idx
        return game_state

    # --- Execute turn (ENTER) -----------------------------------------------
    if event.key == pygame.K_RETURN and battle.state == BattleState.PLAYER_CHOOSE:
        turn_msgs = battle.execute_turn(battle_ctx.get("selected_move", 0))
        messages.extend(turn_msgs)
        battle_ctx["messages"] = messages

        if battle.state == BattleState.BATTLE_END:
            messages.append("Returning to overworld...")
            # Give XP if there's a real battle with the method
            if hasattr(battle, "calculate_exp_gain"):
                try:
                    xp = battle.calculate_exp_gain()
                    active = trainer.active_digimon()
                    if active and not active.is_fainted:
                        xp_msgs = active.gain_exp(xp)
                        messages.extend(xp_msgs)
                except Exception:
                    pass
            return GameState.OVERWORLD

        return game_state

    # --- Use DigiPotion (I) -------------------------------------------------
    if event.key == pygame.K_i:
        active = trainer.active_digimon()
        if active and trainer.has_item("digi_potion"):
            result = trainer.use_item("digi_potion", active)
            messages.append(result)
        elif not trainer.has_item("digi_potion"):
            messages.append("No DigiPotion left!")
        else:
            messages.append("No active Digimon to heal!")
        battle_ctx["messages"] = messages
        return game_state

    # --- Run (R) — wild battles only ----------------------------------------
    if event.key == pygame.K_r and game_state == GameState.BATTLE_WILD:
        if hasattr(battle, "attempt_run"):
            success, msg = battle.attempt_run()
        else:
            import random
            success = random.random() < 0.5
            msg = "Got away safely!" if success else "Can't escape!"
        messages.append(msg)
        battle_ctx["messages"] = messages
        if success:
            return GameState.OVERWORLD

    # --- Dismiss BATTLE_END state with any key once messages shown ----------
    if battle.state == BattleState.BATTLE_END:
        return GameState.OVERWORLD

    return game_state


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    pygame.init()
    pygame.display.set_caption("Digimon")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    fonts = ui.load_fonts()

    # ----------------------------------------------------------------
    # Game state
    # ----------------------------------------------------------------
    game_state: GameState = GameState.TITLE

    trainer: Trainer = _create_default_trainer()
    world: World | None = None

    # battle_ctx holds transient battle data between frames
    battle_ctx: dict = {
        "battle": None,
        "messages": [],
        "selected_move": 0,
    }

    # ----------------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------------
    running = True
    while running:
        # ---- Event processing ------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if game_state == GameState.TITLE:
                game_state = _handle_title(event, game_state)
                if game_state == GameState.OVERWORLD:
                    # Initialise world on first transition from title
                    if world is None:
                        world = World(trainer)

            elif game_state == GameState.OVERWORLD:
                game_state = _handle_overworld(
                    event, game_state, trainer, world, battle_ctx
                )

            elif game_state in (GameState.BATTLE_WILD,
                                GameState.BATTLE_TRAINER):
                game_state = _handle_battle(
                    event, game_state, trainer, world, battle_ctx
                )
                # Clean up battle_ctx on return to overworld
                if game_state == GameState.OVERWORLD:
                    battle_ctx = {
                        "battle": None,
                        "messages": [],
                        "selected_move": 0,
                    }

        # ---- Rendering -------------------------------------------------
        if game_state == GameState.TITLE:
            ui.draw_title_screen(screen, fonts)

        elif game_state == GameState.OVERWORLD:
            if world is not None:
                ui.draw_overworld(screen, world, trainer, fonts)
            else:
                screen.fill((0, 0, 0))

        elif game_state in (GameState.BATTLE_WILD,
                            GameState.BATTLE_TRAINER):
            battle = battle_ctx.get("battle")
            if battle is not None:
                ui.draw_battle_scene(
                    screen,
                    battle,
                    battle_ctx.get("selected_move", 0),
                    battle_ctx.get("messages", []),
                    fonts,
                )
            else:
                screen.fill((0, 0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
