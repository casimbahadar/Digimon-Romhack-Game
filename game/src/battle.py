import math
import random
from .constants import BattleState, TYPE_CHART, ATTRIBUTE_ADVANTAGE, ATTRIBUTE_MULT
from .digimon import DigimonInstance
from .move import Move
from .trainer import Trainer, ITEMS


def stat_stage_mult(mod: int) -> float:
    return (2 + max(0, mod)) / (2 + max(0, -mod))


class Battle:
    def __init__(
        self,
        player: Trainer,
        enemy_trainer: Trainer | None = None,
        wild_digimon: DigimonInstance | None = None,
    ):
        self.player = player
        self.enemy_trainer = enemy_trainer
        self.wild_digimon = wild_digimon
        self.is_wild = wild_digimon is not None

        self.player_digimon: DigimonInstance = player.active_digimon()
        self.enemy_digimon: DigimonInstance = (
            wild_digimon if self.is_wild else enemy_trainer.active_digimon()
        )

        self.state = BattleState.PLAYER_CHOOSE
        self.turn_log: list[str] = []
        self.battle_over: bool = False
        self.player_won: bool = False
        self.pending_player_action: str | None = None
        self.pending_player_move_idx: int = 0
        self.pending_item_id: str | None = None

    # ------------------------------------------------------------------
    # Damage calculation
    # ------------------------------------------------------------------

    def calculate_damage(
        self, attacker: DigimonInstance, move: Move, defender: DigimonInstance
    ) -> int:
        if move.category == "Status":
            return 0

        if move.category == "Physical":
            atk_stat = attacker.effective_atk
            def_stat = defender.effective_def
        else:
            atk_stat = attacker.effective_sp_atk
            def_stat = defender.effective_sp_def

        base = math.floor(
            (2 * attacker.level / 5 + 2) * move.power * atk_stat / def_stat / 50 + 2
        )

        type_mult = 1.0
        for def_type in defender.types:
            type_mult *= TYPE_CHART.get(move.type, {}).get(def_type, 1.0)

        attr_mult = (
            ATTRIBUTE_MULT
            if ATTRIBUTE_ADVANTAGE.get(attacker.attribute) == defender.attribute
            else 1.0
        )

        result = base * type_mult * attr_mult * random.uniform(0.85, 1.0)
        return max(1, int(result))

    # ------------------------------------------------------------------
    # Move effects
    # ------------------------------------------------------------------

    def apply_move_effect(self, move: Move, user: DigimonInstance, target: DigimonInstance):
        effect = move.effect
        if not effect:
            return

        chance = move.effect_chance / 100 if move.effect_chance else 1.0

        if effect == "burn":
            if random.random() < chance and target.apply_status("burn"):
                self.turn_log.append(f"{target.display_name} was burned!")
        elif effect == "poison":
            if random.random() < chance and target.apply_status("poison"):
                self.turn_log.append(f"{target.display_name} was poisoned!")
        elif effect == "paralysis":
            if random.random() < chance and target.apply_status("paralysis"):
                self.turn_log.append(f"{target.display_name} was paralyzed!")
        elif effect == "freeze":
            if random.random() < chance and target.apply_status("freeze"):
                self.turn_log.append(f"{target.display_name} was frozen!")
        elif effect == "sleep":
            if random.random() < chance and target.apply_status("sleep"):
                self.turn_log.append(f"{target.display_name} fell asleep!")
        elif effect == "heal_50pct":
            user.heal_fraction(0.5)
            self.turn_log.append(f"{user.display_name} restored HP!")
        elif effect == "heal_25pct":
            user.heal_fraction(0.25)
            self.turn_log.append(f"{user.display_name} restored a little HP!")
        elif effect == "raise_def_spdef":
            user.apply_stage_mod("def", 1)
            user.apply_stage_mod("sp_def", 1)
            self.turn_log.append(f"{user.display_name}'s DEF and SP.DEF rose!")
        elif effect == "raise_atk_spatk":
            user.apply_stage_mod("atk", 1)
            user.apply_stage_mod("sp_atk", 1)
            self.turn_log.append(f"{user.display_name}'s ATK and SP.ATK rose!")
        elif effect == "lower_opp_atk":
            target.apply_stage_mod("atk", -1)
            self.turn_log.append(f"{target.display_name}'s ATK fell!")
        elif effect == "raise_evasion":
            user.apply_stage_mod("evasion", 2)
            self.turn_log.append(f"{user.display_name}'s evasion rose sharply!")
        elif effect == "raise_def":
            user.apply_stage_mod("def", 2)
            self.turn_log.append(f"{user.display_name}'s DEF rose sharply!")
        elif effect == "raise_sp_def":
            user.apply_stage_mod("sp_def", 2)
            self.turn_log.append(f"{user.display_name}'s SP.DEF rose sharply!")
        elif effect == "raise_all_stats":
            for stat in ("atk", "def", "sp_atk", "sp_def", "spd"):
                user.apply_stage_mod(stat, 1)
            self.turn_log.append(f"{user.display_name}'s all stats rose!")
        elif effect == "lower_opp_spd":
            if random.random() < chance:
                target.apply_stage_mod("spd", -1)
                self.turn_log.append(f"{target.display_name}'s SPD fell!")
        elif effect == "lower_opp_def":
            if random.random() < chance:
                target.apply_stage_mod("def", -1)
                self.turn_log.append(f"{target.display_name}'s DEF fell!")
        elif effect == "lower_opp_sp_def":
            if random.random() < chance:
                target.apply_stage_mod("sp_def", -1)
                self.turn_log.append(f"{target.display_name}'s SP.DEF fell!")
        elif effect == "lower_opp_accuracy":
            if random.random() < chance:
                target.apply_stage_mod("accuracy", -1)
                self.turn_log.append(f"{target.display_name}'s accuracy fell!")
        elif effect == "lower_sp_atk":
            user.apply_stage_mod("sp_atk", -2)
            self.turn_log.append(f"{user.display_name}'s SP.ATK fell sharply!")
        elif effect == "flinch":
            pass  # flinch handled in turn order logic
        elif effect == "taunt":
            self.turn_log.append(f"{target.display_name} is taunted!")
        elif effect == "recharge":
            self.turn_log.append(f"{user.display_name} must recharge!")

    # ------------------------------------------------------------------
    # Enemy AI
    # ------------------------------------------------------------------

    def enemy_choose_move(self) -> int:
        best_idx = 0
        best_power = -1
        for i, move in enumerate(self.enemy_digimon.moves):
            if move.pp_current > 0 and move.power > best_power:
                best_power = move.power
                best_idx = i
        return best_idx

    # ------------------------------------------------------------------
    # Move execution
    # ------------------------------------------------------------------

    def execute_move(
        self, attacker: DigimonInstance, move: Move, defender: DigimonInstance
    ) -> int:
        if move.pp_current <= 0:
            self.turn_log.append(f"{attacker.display_name}'s {move.name} has no PP left!")
            return 0

        move.use()

        if not attacker.can_move():
            self.turn_log.append(f"{attacker.display_name} is immobilized and can't move!")
            return 0

        # Accuracy check
        if move.accuracy > 0:
            acc_mult = stat_stage_mult(attacker.stage_mods["accuracy"])
            eva_mult = stat_stage_mult(defender.stage_mods["evasion"])
            hit_chance = (move.accuracy / 100) * acc_mult / eva_mult
            if random.random() > hit_chance:
                self.turn_log.append(f"{attacker.display_name}'s {move.name} missed!")
                return 0

        self.turn_log.append(f"{attacker.display_name} used {move.name}!")

        if move.category == "Status":
            self.apply_move_effect(move, attacker, defender)
            return 0

        damage = self.calculate_damage(attacker, move, defender)
        defender.take_damage(damage)
        self.turn_log.append(f"{defender.display_name} took {damage} damage!")

        if move.effect_chance > 0:
            self.apply_move_effect(move, attacker, defender)

        return damage

    # ------------------------------------------------------------------
    # Player action entry point
    # ------------------------------------------------------------------

    def player_action(
        self,
        action: str,
        move_index: int = 0,
        item_id: str = None,
        switch_index: int = None,
    ):
        self.pending_player_action = action

        if action == "FIGHT":
            self.pending_player_move_idx = move_index
            self.execute_turn(player_move_idx=move_index)

        elif action == "ITEM":
            self.pending_item_id = item_id
            result = self.player.use_item(item_id, self.player_digimon)
            self.turn_log.append(result)
            self.execute_turn(player_move_idx=0)

        elif action == "SWITCH":
            if switch_index is not None and 0 <= switch_index < len(self.player.party):
                new_digi = self.player.party[switch_index]
                if not new_digi.is_fainted and new_digi is not self.player_digimon:
                    self.turn_log.append(
                        f"Come back, {self.player_digimon.display_name}! "
                        f"Go, {new_digi.display_name}!"
                    )
                    self.player_digimon = new_digi
            self.execute_turn(player_move_idx=0)

        elif action == "RUN":
            if self.is_wild:
                if random.random() < 0.5:
                    self.turn_log.append("Got away safely!")
                    self.battle_over = True
                    self.player_won = False
                else:
                    self.turn_log.append("Can't escape!")
            else:
                self.turn_log.append("Can't flee a trainer battle!")

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    def execute_turn(self, player_move_idx: int = 0):
        if self.battle_over:
            return

        enemy_move_idx = self.enemy_choose_move()
        player_move = (
            self.player_digimon.moves[player_move_idx]
            if self.player_digimon.moves
            else None
        )
        enemy_move = (
            self.enemy_digimon.moves[enemy_move_idx]
            if self.enemy_digimon.moves
            else None
        )

        # Determine order
        player_spd = self.player_digimon.effective_spd
        enemy_spd = self.enemy_digimon.effective_spd
        player_first = (
            player_spd > enemy_spd
            or (player_spd == enemy_spd and random.random() < 0.5)
        )

        def do_player_move():
            if player_move and self.pending_player_action == "FIGHT":
                self.execute_move(self.player_digimon, player_move, self.enemy_digimon)

        def do_enemy_move():
            if enemy_move:
                self.execute_move(self.enemy_digimon, enemy_move, self.player_digimon)

        if player_first:
            do_player_move()
            if not self.enemy_digimon.is_fainted:
                do_enemy_move()
        else:
            do_enemy_move()
            if not self.player_digimon.is_fainted:
                do_player_move()

        # End-of-turn status damage
        for digi in (self.player_digimon, self.enemy_digimon):
            dmg = digi.tick_status()
            if dmg > 0:
                self.turn_log.append(
                    f"{digi.display_name} was hurt by its {digi.status or 'status'}! ({dmg} dmg)"
                )

        # Handle faints
        if self.enemy_digimon.is_fainted:
            exp = self.get_exp_reward(self.enemy_digimon)
            messages = self.player_digimon.gain_exp(exp)
            self.turn_log.append(
                f"{self.enemy_digimon.display_name} fainted! "
                f"{self.player_digimon.display_name} gained {exp} EXP."
            )
            for msg in messages:
                self.turn_log.append(msg)
            if self.player_digimon.can_digivolve():
                self.state = BattleState.DIGIVOLVE_PROMPT

        if self.player_digimon.is_fainted:
            next_digi = self.player.active_digimon()
            if next_digi:
                self.turn_log.append(
                    f"{self.player_digimon.display_name} fainted! "
                    f"Go, {next_digi.display_name}!"
                )
                self.player_digimon = next_digi
            else:
                self.turn_log.append(f"{self.player_digimon.display_name} fainted!")

        self.check_battle_end()

    # ------------------------------------------------------------------
    # EXP reward
    # ------------------------------------------------------------------

    def get_exp_reward(self, fainted_digimon: DigimonInstance) -> int:
        return max(1, (fainted_digimon.level * fainted_digimon.level * 3) // 7)

    # ------------------------------------------------------------------
    # Catching
    # ------------------------------------------------------------------

    def try_catch(self, ball_id: str) -> bool:
        if not self.is_wild:
            self.turn_log.append("Can't catch a trainer's Digimon!")
            return False

        caught = self.player.catch_digimon(self.wild_digimon, ball_id)
        name = self.wild_digimon.display_name
        if caught:
            self.turn_log.append(f"Gotcha! {name} was caught!")
            self.battle_over = True
            self.player_won = True
        else:
            self.turn_log.append(f"Oh no! {name} broke free!")
        return caught

    # ------------------------------------------------------------------
    # Battle end check
    # ------------------------------------------------------------------

    def check_battle_end(self):
        if self.battle_over:
            return

        enemy_fainted = self.enemy_digimon.is_fainted
        if enemy_fainted:
            no_more_enemy = self.is_wild or (
                self.enemy_trainer is not None and self.enemy_trainer.all_fainted()
            )
            if no_more_enemy:
                self.battle_over = True
                self.player_won = True
                self.state = BattleState.BATTLE_END
                self.turn_log.append("You won!")
                if not self.is_wild and self.enemy_trainer is not None:
                    reward = self.enemy_trainer.money // 2
                    self.player.money += reward
                    self.turn_log.append(f"You received {reward} bits!")

        if self.player.all_fainted():
            self.battle_over = True
            self.player_won = False
            self.state = BattleState.BATTLE_END
            self.turn_log.append("You blacked out...")
