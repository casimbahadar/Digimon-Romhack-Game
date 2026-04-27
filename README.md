# Digimon Romhack Game

A Pokemon-style Digimon fan game built in Python/Pygame, plus a ROM hack patch generator for Pokemon FireRed. All Pokemon are replaced with Digimon across every system: battles, catching, evolution, items, and the world.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [The Fan Game](#the-fan-game)
4. [Digimon Database](#digimon-database)
5. [Move System](#move-system)
6. [World & Areas](#world--areas)
7. [Battle System](#battle-system)
8. [Items & Catching](#items--catching)
9. [Progression & Saving](#progression--saving)
10. [ROM Hack Patcher](#rom-hack-patcher)
11. [Data Tools](#data-tools)
12. [Wiki Coverage](#wiki-coverage)
13. [Requirements](#requirements)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the fan game
python game/main.py

# ROM hack patcher (needs your own FireRed ROM)
python romhack/patcher.py firered.gba

# Add more Digimon from the wiki automatically
python tools/pipeline.py --limit 500
```

---

## Project Structure

```
Digimon-Romhack-Game/
├── game/
│   ├── main.py               # Entry point — run this to play
│   ├── src/
│   │   ├── battle.py         # Turn-based battle engine
│   │   ├── constants.py      # Type chart, attributes, enums, colors
│   │   ├── digimon.py        # DigimonInstance class, stat formulas
│   │   ├── move.py           # Move class and move database loader
│   │   ├── save.py           # JSON save/load (slot-based)
│   │   ├── trainer.py        # Trainer class: party, items, catching
│   │   ├── ui.py             # All Pygame rendering (procedural, no sprites)
│   │   └── world.py          # Overworld: areas, encounters, navigation
│   └── data/
│       ├── digimon.json      # 1,009 Digimon species (756 KB)
│       ├── moves.json        # 172 moves across 14 types (49 KB)
│       └── areas.json        # 8 areas with encounters and trainers (18 KB)
├── romhack/
│   ├── patcher.py            # Main ROM patching CLI
│   ├── ips.py                # IPS patch encoder/decoder
│   ├── verify.py             # ROM SHA-1 verification
│   ├── offsets.py            # FireRed ROM memory map
│   ├── encoders.py           # FireRed text charset encoder
│   └── data/
│       ├── digimon_stats.json    # Stats in FireRed format (57 KB)
│       ├── digimon_names.json    # Names truncated to 10 chars
│       ├── slot_mapping.json     # Pokemon slot → Digimon ID
│       ├── type_mapping.json     # Digimon type → FireRed type ID
│       └── pokedex_text.json     # Pokedex descriptions (15 KB)
└── tools/
    ├── auto_assign.py        # Auto-generate moves/stats from type+stage
    ├── merge.py              # Merge new Digimon JSON into the database
    ├── wiki_scraper.py       # Scrape digimon.fandom.com
    └── pipeline.py           # One command: scrape → merge → update areas
```

**Total source size: ~1 MB** (756 KB of Digimon data + ~250 KB of Python code)

---

## The Fan Game

Run with `python game/main.py`. The game opens an **800×600 Pygame window** and drops you into a Pokemon-style adventure where every creature is a Digimon.

### Controls

| Key | Action |
|-----|--------|
| Arrow keys | Move between areas / navigate menus |
| `1` `2` `3` `4` | Select a move in battle |
| `Enter` | Confirm selection / start game |
| `I` | Use an item in battle |
| `R` | Attempt to run from a wild battle |
| `Escape` | Quit / back |

### Game States

The game runs a state machine with three screens:

**Title Screen** — Press Enter to start. Your party begins with a level-5 Koromon and a level-5 Tsunomon.

**Overworld** — Your current area is displayed with a list of connected areas. Every step has a 5% chance of triggering a wild encounter. Trainer battles fire automatically when you enter their area.

**Battle** — Full turn-based combat. Pick one of up to 4 moves, use an item, or run. After winning you gain EXP and money; losing heals your party but costs money.

### Rendering

The game uses **no external sprite assets** — everything is drawn procedurally with Pygame shapes and text. Digimon are represented as colored rectangles with their name and type displayed. HP bars shift from green → yellow → red. Each of the 14 types has a unique accent color used throughout the UI.

---

## Digimon Database

`game/data/digimon.json` contains **1,009 unique Digimon species** drawn from every major Digimon series and media.

### By Digivolution Stage

| Stage | Count | Level range encounters |
|-------|-------|----------------------|
| Baby (Fresh / In-Training) | 50 | File City (lv 3–10) |
| Rookie | 148 | Gear Savanna / Tropical Jungle (lv 8–22) |
| Champion | 225 | Ancient Dino Region / Factorial Town (lv 18–38) |
| Ultimate | 225 | Metal Factory / Dark Cave (lv 30–50) |
| Mega | 361 | Dark Cave / Infinity Mountain (lv 38–60) |

### By Attribute

Attributes are the Digimon-specific alignment system layered on top of types:

| Attribute | Count | Notes |
|-----------|-------|-------|
| Vaccine | 414 | Circular advantage over Virus |
| Virus | 339 | Circular advantage over Data |
| Data | 200 | Circular advantage over Vaccine |
| Free | 46 | No attribute advantage or penalty |
| Unknown | 10 | Special/corrupted Digimon (D-Reaper, Eater, etc.) |

### By Primary Type

| Type | Count | Type | Count |
|------|-------|------|-------|
| Dark | 237 | Water | 64 |
| Holy | 156 | Ice | 60 |
| Fire | 124 | Bug | 38 |
| Dragon | 97 | Plant | 31 |
| Normal | 75 | Electric | 31 |
| — | — | Steel | 31 |

### What Series Are Covered

Every major Digimon series and game contributes to the database:

- **Digimon Adventure** (original 8 partner lines + Dark Masters + villains)
- **Digimon Adventure 02** (02 partners, armor evolutions, DNA digivolutions)
- **Digimon Tamers** (full cast + Deva + D-Reaper)
- **Digimon Frontier** (all 10 warriors + unified/beast spirits)
- **Digimon Savers / Data Squad** (all partner lines)
- **Digimon Xros Wars / Fusion** (Shoutmon, Ballistamon, and fusion forms)
- **Digimon Xros Wars: Hunters** (Gumdramon, Arresterdramon)
- **Digimon Adventure tri.** (Meicoomon / Raguelmon / Ordinemon)
- **Digimon Adventure: Last Evolution Kizuna** (Eosmon)
- **Digimon Adventure: (2020 reboot)** (Negamon, GreatNegamon)
- **Digimon Ghost Game** (full cast: Gammamon, Jellymon, Angoramon lines)
- **Digimon Survive** (full game cast)
- **Digimon Universe: App Monsters** (AppMon cast)
- **Digimon Story: Cyber Sleuth** (Eater, Hackmon, Jesmon lines)
- **Digimon World series** (game-exclusive Digimon)
- **V-Pet / Digital Monster** (original V-Pet Digimon)
- **Digimon Chronicle X** (X-Antibody story Digimon)
- **Royal Knights** (all 13 members + X-Antibody variants)
- **Four Holy Beasts / Sovereigns** (all 5 + X-Antibody variants)
- **Olympos XII** (all 12 god Digimon)
- **Seven Deadly Sin Demon Lords** (all 7)
- **Ten Legendary Warriors** (all 10 + Ancient versions)
- **X-Antibody variants** (X-forms for most major Digimon lines)

### Data Schema

Each entry in `digimon.json`:

```json
{
  "id": 1,
  "name": "Agumon",
  "stage": "Rookie",
  "attribute": "Vaccine",
  "types": ["Fire", "Dragon"],
  "base_stats": {
    "hp": 57, "atk": 67, "def": 47,
    "sp_atk": 72, "sp_def": 47, "spd": 52
  },
  "moves": [
    { "learn_level": 1,  "move_id": "pepper_flame" },
    { "learn_level": 7,  "move_id": "nova_blast" },
    { "learn_level": 16, "move_id": "wildfire" }
  ],
  "digivolves_to": [{ "id": 9, "name": "Greymon", "min_level": 16 }],
  "digivolves_from": [],
  "catch_rate": 150,
  "description": "A small orange dinosaur Digimon..."
}
```

---

## Move System

`game/data/moves.json` contains **172 moves** with real Digimon attack names sourced from the franchise.

### Move Counts by Type

| Type | Moves | Type | Moves |
|------|-------|------|-------|
| Fire | 13 | Holy | 15 |
| Water | 11 | Dark | 13 |
| Ice | 11 | Fighting | 13 |
| Plant | 12 | Flying | 11 |
| Electric | 12 | Bug | 9 |
| Dragon | 10 | Poison | 9 |
| Steel | 12 | Normal | 9 |

**156 damaging moves** (power range 30–150) and **16 status moves**.

### Move Categories

- **Special** (100 moves): Uses SP.ATK vs SP.DEF — elemental beams, breath attacks
- **Physical** (56 moves): Uses ATK vs DEF — claws, punches, bites
- **Status** (16 moves): No damage — heals, stat boosts, debuffs

### Signature Moves (examples)

| Move | Type | Power | Effect |
|------|------|-------|--------|
| Terra Destroyer | Dragon | 140 | — |
| Heaven's Gate | Holy | 140 | — |
| Flame Inferno | Fire | 140 | 50% burn |
| Infinity Cannon | Steel | 130 | — |
| Draco Meteor | Dragon | 130 | Lowers own SP.ATK |
| Atomic Flame | Fire | 130 | 30% burn |
| Tundra Freeze | Ice | 130 | 40% freeze |
| Soul Crusher | Dark | 130 | 50% lowers SP.DEF |
| Diamond Storm | Ice | 95 | 20% freeze |
| Chaos Flare | Dark | 110 | 20% burn |
| Nightmare Syndrome | Dark | 90 | 30% sleep |
| Dramon Killer | Dragon | 100 | — |
| Cocytus Breath | Water | 90 | 20% freeze |
| Seven Heavens | Holy | 120 | — |

### Move Effects

Moves can apply: `burn`, `poison`, `paralysis`, `freeze`, `sleep`, `flinch`

Stat changes: raise/lower ATK, DEF, SP.ATK, SP.DEF, SPD, accuracy, evasion

Status moves include healing (25%/50% HP restore), evasion raise, barrier, and burst.

### Damage Formula

```
damage = floor((2*level/5 + 2) * power * atk/def / 50 + 2)
       * type_mult          # 0.0 / 0.5 / 1.0 / 2.0
       * attribute_mult     # 1.15 if attacker has advantage, else 1.0
       * random(0.85–1.0)
```

Type multiplier comes from a 14×14 chart. Attribute advantage is circular: Vaccine beats Virus beats Data beats Vaccine (+15% damage).

---

## World & Areas

The overworld has **8 areas** connected in a hub-and-spoke layout. File City is the central hub connecting to all other zones. Each area has wild encounters sampled from the full 1,009-Digimon pool by stage.

### Area Overview

| Area | Wild Levels | Stages | Wild Slots | Trainers |
|------|-------------|--------|-----------|----------|
| File City | 3–10 | Baby, Rookie | 6 | 2 |
| Gear Savanna | 8–18 | Rookie, Champion | 10 | 3 |
| Tropical Jungle | 12–22 | Rookie, Champion | 10 | 3 |
| Ancient Dino Region | 18–30 | Champion | 10 | 3 |
| Factorial Town | 25–38 | Champion, Ultimate | 10 | 3 |
| Metal Factory | 30–42 | Champion, Ultimate | 10 | 3 |
| Dark Cave | 38–50 | Ultimate, Mega | 10 | 3 |
| Infinity Mountain | 45–60 | Ultimate, Mega | 10 | 3 |

**Total: 76 wild encounter slots, 23 trainer battles**

### Wild Encounters

Each step in an area has a **5% chance** of triggering a wild battle. The Digimon species is drawn by weighted random from the area's encounter table. Level is randomized within the area's min–max range.

### Trainers

Each area has 2–3 trainer battles. Trainers use themed parties matching the area's level range. Defeating a trainer earns money and cannot be rematched in the same session.

### Navigation

Areas connect to each other. From the overworld screen you can see all connected areas and move to any one of them directly. The connections are:

- **File City** connects to all 7 other areas (hub)
- **Gear Savanna** → File City, Tropical Jungle, Ancient Dino Region
- **Tropical Jungle** → File City, Gear Savanna, Factorial Town, Dark Cave
- **Ancient Dino Region** → File City, Gear Savanna, Factorial Town, Metal Factory
- **Factorial Town** → File City, Tropical Jungle, Metal Factory
- **Metal Factory** → File City, Ancient Dino Region, Factorial Town, Dark Cave
- **Dark Cave** → File City, Tropical Jungle, Metal Factory, Infinity Mountain
- **Infinity Mountain** → File City, Dark Cave, Metal Factory

---

## Battle System

Battles are fully turn-based, implemented in `game/src/battle.py`.

### Turn Order

Both sides choose their action simultaneously. Moves with higher `priority` go first (Quick Attack-type moves have priority 1, everything else 0). Among equal priority, the faster Digimon (higher SPD stat, after stage modifiers) acts first.

### Accuracy

```
hit_chance = (move.accuracy / 100) * acc_stage_mult / eva_stage_mult
```

Stage multipliers follow the Pokemon formula: +1 stage = 1.5×, +6 = 4×, −1 = 0.667×, −6 = 0.25×.

### Status Conditions

| Status | Applied by | End-of-turn effect |
|--------|-----------|-------------------|
| Burn | Fire moves | −1/8 max HP per turn |
| Poison | Poison moves | −1/8 max HP per turn |
| Paralysis | Electric moves | Cannot move (chance) |
| Freeze | Ice moves | Cannot move (thaws after 1–4 turns) |
| Sleep | Spore/nightmare moves | Cannot move (wakes after 1–3 turns) |

### Stat Stage Modifiers

In-battle modifiers range from −6 to +6. Moves like Leaf Storm, Draco Meteor lower your own SP.ATK sharply (−2) after use. Status moves can raise DEF, SP.DEF, ATK+SP.ATK together, or raise evasion.

### Digivolution

When a Digimon reaches its minimum digivolution level mid-battle or after battle, a prompt appears asking if you want to digivolve. Digivolving raises all stats immediately.

### AI

The enemy AI currently chooses the highest-power available move. Future updates can plug in smarter AI per trainer.

---

## Items & Catching

### Items

| Item | Type | Effect |
|------|------|--------|
| DigiEgg | Ball | Catch wild Digimon (1.0× catch rate) |
| GreatEgg | Ball | Catch with 1.5× multiplier |
| UltraEgg | Ball | Catch with 2.0× multiplier |
| DigiPotion | Heal | Restore 20 HP |
| MaxPotion | Heal | Fully restore HP |
| Revive | Revive | Revive fainted Digimon to 50% HP |
| Antidote | Status cure | Cure poison |
| FullHeal | Status cure | Cure any status condition |
| Digital Meat | EXP boost | Grant 500 EXP to one Digimon |

The player starts with 5 DigiEggs and 3 DigiPotions.

### Catch Formula

```python
catch_value = (3 * max_hp - 2 * current_hp) * catch_rate * ball_mult / (3 * max_hp)
catch_value  = clamp(catch_value, 0, 255)
success      = random.randint(0, 255) < catch_value
```

Weaken the wild Digimon first — lower HP dramatically increases catch chance. Baby/Rookie Digimon have catch rates of 150–220; Mega Digimon have rates as low as 30.

### Party & PC Box

- Active party: up to **6 Digimon**
- Overflow goes to the **PC Box** (unlimited)
- Swap party members via the party screen

---

## Progression & Saving

### Experience

Digimon gain EXP after every battle. The leveling curve uses a medium-fast formula:

```
exp_needed_to_level_up = current_level³
```

On level-up, all stats recalculate and the HP difference is added to current HP. New moves are learned automatically when their `learn_level` is reached and the Digimon has fewer than 4 moves.

### Saving

The game saves to `~/.digimon_game/saves/`. Three save slots are available. Each save file stores the full trainer state: party, PC box, items, money, badges, seen/caught Digimon, current area, steps, and playtime.

```bash
# Save files location
~/.digimon_game/saves/save_0.json
~/.digimon_game/saves/save_1.json
~/.digimon_game/saves/save_2.json
```

### Digivolution

Digivolution is data-driven. Each Digimon's entry in `digimon.json` lists its `digivolves_to` targets with a `min_level`. When the level requirement is met after battle, the game prompts you to digivolve. Stats fully recalculate for the new species and moves are retained.

---

## ROM Hack Patcher

The `romhack/` folder is a standalone tool that patches **Pokemon FireRed (BPRE v1.0)** to replace Pokemon with Digimon at the binary level.

### Requirements

You must legally own a Pokemon FireRed ROM. The patcher verifies your ROM before touching it:

- **Target:** Pokemon FireRed (BPRE), US v1.0
- **SHA-1:** `DD5945DB9B930750CB39D00C84DA8571FEEBF417`

### Usage

```bash
# Patch your ROM directly
python romhack/patcher.py firered.gba

# Output to a specific file
python romhack/patcher.py firered.gba --output digimon_firered.gba

# Generate an IPS patch file instead of a full ROM
python romhack/patcher.py firered.gba --patch-only

# Verify your ROM without patching
python romhack/verify.py firered.gba
```

### What Gets Patched

The patcher modifies these ROM tables at hardcoded FireRed offsets:

| Table | Offset | Entry size | Entries |
|-------|--------|-----------|---------|
| Base stats | `0x254784` | 28 bytes | 386 |
| Species names | `0x245EE0` | 11 bytes | 386 |
| Type chart | `0x24F1A0` | — | — |

Each 28-byte base stat entry stores: HP, ATK, DEF, SPD, SP.ATK, SP.DEF, Type1, Type2, CatchRate, BaseExp, EVYield, abilities, growth rate, and more.

### Type Mapping

Digimon types are mapped to FireRed's 17-type system:

| Digimon Type | FireRed Type |
|-------------|-------------|
| Fire | Fire (9) |
| Water | Water (10) |
| Holy | Psychic (13) |
| Dark | Dark (16) |
| Dragon | Dragon (15) |
| Plant | Grass (11) |
| Electric | Electric (12) |
| Ice | Ice (14) |
| Steel | Steel (8) |
| Fighting | Fighting (1) |
| Flying | Flying (2) |
| Bug | Bug (6) |
| Poison | Poison (3) |
| Normal | Normal (0) |

### IPS Patch Format

When run with `--patch-only`, the patcher produces an `.ips` file encoding only the changed bytes. You can apply this to your ROM with any standard IPS patcher (Lunar IPS, Flips, etc.).

---

## Data Tools

### Auto-Assign (`tools/auto_assign.py`)

Every Digimon that enters the database gets moves and stats auto-generated from its `stage` and `types`. No manual editing required.

- **Moves**: Chosen from a type-appropriate pool ordered weakest→strongest. Champion+ Digimon get one status move (barrier, heal, taunt, etc.) for variety.
- **Base stats**: Drawn from a stage range (Baby: 35–55, Mega: 100–135) shaped by the primary type's stat profile (Fire Digimon get higher ATK/SP.ATK; Steel gets higher DEF; Flying gets higher SPD, etc.).
- **Catch rate**: Baby: 220, Rookie: 150, Champion: 100, Ultimate: 60, Mega: 30.

### Wiki Scraper (`tools/wiki_scraper.py`)

Scrapes `digimon.fandom.com` and builds JSON entries ready for merging.

```bash
# Scrape 500 Digimon and save to a file
python tools/wiki_scraper.py --limit 500 --output scraped.json

# Preview 3 samples without making network requests
python tools/wiki_scraper.py --dry-run
```

Rate-limited to 1 request/second to be polite to the wiki. Auto-assigns moves and stats via `auto_assign.py` for every scraped entry.

### Merge Tool (`tools/merge.py`)

Merges a JSON file of new Digimon into the main database, deduplicating by name and regenerating area encounter tables.

```bash
python tools/merge.py scraped.json
```

### Full Pipeline (`tools/pipeline.py`)

One command that runs scrape → merge → resolve evolutions → update areas:

```bash
# Scrape up to 2000 Digimon and add them all
python tools/pipeline.py --limit 2000

# Merge from an already-scraped file (skip network)
python tools/pipeline.py --scraped scraped.json
```

---

## Wiki Coverage

The [Digimon Wiki](https://digimon.fandom.com) lists approximately **1,400–1,500 unique named Digimon** (the exact count varies as new Digimon are released regularly and the wiki includes regional/alternate names).

### What This Game Has

**1,009 Digimon** are currently in the database. Coverage includes:

- All Digimon from the main animated series (Adventure through Ghost Game) ✓
- All Royal Knights (13/13) ✓
- All Seven Deadly Sin Demon Lords (7/7) ✓
- All Four Holy Beasts / Sovereigns (5/5) ✓
- All Ten Legendary Warriors + Ancient forms (20/20) ✓
- All Olympos XII (12/12) ✓
- All 12 Deva (12/12) ✓
- X-Antibody variants for all major partner lines ✓
- Baby/In-Training forms for all anime partner Digimon ✓
- Armor digivolutions from Adventure 02 ✓
- Spirit digivolutions from Frontier ✓
- DNA digivolutions ✓

### What May Be Missing

The ~400 gap between our 1,009 and the wiki's ~1,400+ is mostly:

- Obscure single-appearance Digimon from manga or V-Pet games
- Regional/Japanese-only V-Pet exclusive Digimon
- Digimon released after the database was compiled
- Some Digimon Card Game-only new releases

### Adding More Digimon

Run the pipeline to automatically scrape and add missing Digimon:

```bash
python tools/pipeline.py --limit 2000
```

Each new Digimon gets moves and stats auto-assigned — no manual work needed. The areas.json encounter tables rebuild automatically to include new entries.

---

## Requirements

```
pygame>=2.5.0       # Game window, rendering, input
requests>=2.31.0    # Wiki scraper HTTP
beautifulsoup4>=4.12.0  # Wiki scraper HTML parsing
lxml>=4.9.0         # HTML backend for BeautifulSoup
```

Install with: `pip install -r requirements.txt`

Python 3.10+ is required (uses `match` syntax and `X | Y` type hints in places).

---

## Size Summary

| Component | Count / Size |
|-----------|-------------|
| Digimon species | **1,009** |
| Moves | **172** |
| World areas | **8** |
| Wild encounter slots | **76** |
| Trainer battles | **23** |
| Digivolution stages | 5 (Baby → Rookie → Champion → Ultimate → Mega) |
| Type system | 14 types + 4 attributes |
| Items | 9 types |
| Save slots | 3 |
| Python source | ~2,800 lines |
| Total data size | ~1 MB |

---

*Fan-made project. Digimon is a registered trademark of Bandai / Toei Animation. This project is not affiliated with or endorsed by Bandai or Toei.*
