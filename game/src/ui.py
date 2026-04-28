# Pygame UI module — no sprite assets; everything is colored rectangles + text.

import pygame

from .constants import (
    WHITE, BLACK, RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE,
    DARK_GRAY, LIGHT_GRAY, SCREEN_BG, HP_GREEN, HP_YELLOW, HP_RED,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    FONT_SMALL, FONT_MEDIUM, FONT_LARGE,
    TYPE_COLORS,
    GameState, BattleState,
)


# ---------------------------------------------------------------------------
# Font loader
# ---------------------------------------------------------------------------

def load_fonts() -> dict:
    """Return a dict of pygame Font objects keyed by size name."""
    return {
        "small":  pygame.font.Font(None, FONT_SMALL),
        "medium": pygame.font.Font(None, FONT_MEDIUM),
        "large":  pygame.font.Font(None, FONT_LARGE),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_text(surface, text: str, font, color, x: int, y: int,
                 center: bool = False) -> pygame.Rect:
    """Render *text* onto *surface* at (*x*, *y*).

    If *center* is True, (x, y) is the center point rather than top-left.
    Returns the bounding Rect.
    """
    img = font.render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    surface.blit(img, rect)
    return rect


def _draw_panel(surface, x: int, y: int, w: int, h: int,
                bg_color=DARK_GRAY, border_color=LIGHT_GRAY,
                border_width: int = 2) -> None:
    """Draw a filled rectangle with an optional border."""
    pygame.draw.rect(surface, bg_color, (x, y, w, h))
    if border_width > 0:
        pygame.draw.rect(surface, border_color, (x, y, w, h), border_width)


# ---------------------------------------------------------------------------
# Battle UI
# ---------------------------------------------------------------------------

def draw_battle_background(screen) -> None:
    """Fill background and draw two simple platform shapes."""
    screen.fill(SCREEN_BG)

    # Enemy platform (top-right area)
    enemy_platform = pygame.Rect(SCREEN_WIDTH // 2 + 40, 180, 220, 24)
    pygame.draw.ellipse(screen, (70, 100, 70), enemy_platform)

    # Player platform (bottom-left area)
    player_platform = pygame.Rect(60, 330, 220, 24)
    pygame.draw.ellipse(screen, (80, 110, 80), player_platform)

    # Thin horizon line
    pygame.draw.line(screen, (60, 80, 60),
                     (0, SCREEN_HEIGHT // 2 - 20),
                     (SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 20), 2)


def draw_digimon_placeholder(screen, name: str, x: int, y: int,
                              is_player: bool, type_color) -> None:
    """Draw a colored rectangle as a placeholder sprite with a name label."""
    # Size: player sprite is slightly larger and in the foreground
    w, h = (90, 90) if is_player else (76, 76)
    rect = pygame.Rect(x - w // 2, y - h // 2, w, h)

    # Body rectangle with type-colored fill
    pygame.draw.rect(screen, type_color, rect, border_radius=8)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)

    # Simple face dots
    eye_y = rect.top + h // 3
    left_eye_x = rect.left + w // 3
    right_eye_x = rect.right - w // 3
    pygame.draw.circle(screen, BLACK, (left_eye_x, eye_y), 5)
    pygame.draw.circle(screen, BLACK, (right_eye_x, eye_y), 5)

    # Name below the sprite
    font = pygame.font.Font(None, FONT_SMALL)
    img = font.render(name, True, WHITE)
    nr = img.get_rect(centerx=x, top=rect.bottom + 4)
    screen.blit(img, nr)


def draw_hp_bar(screen, x: int, y: int, w: int,
                current_hp: int, max_hp: int, label: str = "") -> None:
    """Draw an HP bar with green/yellow/red coloring based on fraction."""
    h = 12
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, DARK_GRAY, bg_rect)

    fraction = current_hp / max_hp if max_hp > 0 else 0.0
    fraction = max(0.0, min(1.0, fraction))

    if fraction > 0.5:
        bar_color = HP_GREEN
    elif fraction > 0.2:
        bar_color = HP_YELLOW
    else:
        bar_color = HP_RED

    fill_w = int(w * fraction)
    if fill_w > 0:
        pygame.draw.rect(screen, bar_color, (x, y, fill_w, h))

    pygame.draw.rect(screen, LIGHT_GRAY, bg_rect, 1)

    if label:
        font = pygame.font.Font(None, FONT_SMALL)
        img = font.render(label, True, WHITE)
        screen.blit(img, (x, y - 16))


def draw_battle_hud(screen, player_digi, enemy_digi, fonts: dict) -> None:
    """Draw HP bars and stat panels for both Digimon."""
    font_sm = fonts["small"]
    font_md = fonts["medium"]

    # ------------------------------------------------------------------
    # Enemy HUD (top-left)
    # ------------------------------------------------------------------
    _draw_panel(screen, 10, 10, 280, 80)

    # Name + level
    _render_text(screen,
                 f"{enemy_digi.display_name}  Lv{enemy_digi.level}",
                 font_md, WHITE, 18, 14)

    # Type badge
    type_col = TYPE_COLORS.get(
        enemy_digi.types[0] if enemy_digi.types else "Normal", LIGHT_GRAY
    )
    pygame.draw.rect(screen, type_col, (18, 36, 60, 14), border_radius=4)
    _render_text(screen,
                 enemy_digi.types[0] if enemy_digi.types else "?",
                 font_sm, BLACK, 20, 37)

    # Status badge
    if enemy_digi.status and enemy_digi.status != "none":
        pygame.draw.rect(screen, RED, (86, 36, 60, 14), border_radius=4)
        _render_text(screen, enemy_digi.status.upper(), font_sm, WHITE, 88, 37)

    # HP label + bar
    draw_hp_bar(screen, 18, 60, 240,
                enemy_digi.current_hp, enemy_digi.max_hp)
    _render_text(screen,
                 f"HP {enemy_digi.current_hp}/{enemy_digi.max_hp}",
                 font_sm, LIGHT_GRAY, 18, 74)

    # ------------------------------------------------------------------
    # Player HUD (bottom-right)
    # ------------------------------------------------------------------
    hud_x = SCREEN_WIDTH - 300
    hud_y = SCREEN_HEIGHT - 160
    _draw_panel(screen, hud_x, hud_y, 290, 80)

    _render_text(screen,
                 f"{player_digi.display_name}  Lv{player_digi.level}",
                 font_md, WHITE, hud_x + 8, hud_y + 4)

    p_type_col = TYPE_COLORS.get(
        player_digi.types[0] if player_digi.types else "Normal", LIGHT_GRAY
    )
    pygame.draw.rect(screen, p_type_col,
                     (hud_x + 8, hud_y + 26, 60, 14), border_radius=4)
    _render_text(screen,
                 player_digi.types[0] if player_digi.types else "?",
                 font_sm, BLACK, hud_x + 10, hud_y + 27)

    if player_digi.status and player_digi.status != "none":
        pygame.draw.rect(screen, RED,
                         (hud_x + 76, hud_y + 26, 60, 14), border_radius=4)
        _render_text(screen, player_digi.status.upper(),
                     font_sm, WHITE, hud_x + 78, hud_y + 27)

    draw_hp_bar(screen, hud_x + 8, hud_y + 50, 250,
                player_digi.current_hp, player_digi.max_hp)
    _render_text(screen,
                 f"HP {player_digi.current_hp}/{player_digi.max_hp}",
                 font_sm, LIGHT_GRAY, hud_x + 8, hud_y + 64)


def draw_move_menu(screen, moves: list, selected_idx: int,
                   fonts: dict) -> None:
    """Draw a 2x2 move button grid at the bottom of the screen."""
    font_sm = fonts["small"]
    font_md = fonts["medium"]

    panel_x = 0
    panel_y = SCREEN_HEIGHT - 150
    panel_w = SCREEN_WIDTH // 2
    panel_h = 150

    _draw_panel(screen, panel_x, panel_y, panel_w, panel_h,
                bg_color=(20, 20, 40))

    btn_w = panel_w // 2 - 8
    btn_h = panel_h // 2 - 10

    for i, move in enumerate(moves[:4]):
        col = i % 2
        row = i // 2
        bx = panel_x + 4 + col * (btn_w + 8)
        by = panel_y + 6 + row * (btn_h + 8)

        type_col = TYPE_COLORS.get(move.type, LIGHT_GRAY)
        border_col = WHITE if i == selected_idx else DARK_GRAY
        border_w = 3 if i == selected_idx else 1

        # Button background — darker shade of the type color
        bg = tuple(max(0, c - 80) for c in type_col)
        pygame.draw.rect(screen, bg, (bx, by, btn_w, btn_h), border_radius=4)
        pygame.draw.rect(screen, type_col, (bx, by, btn_w, btn_h), 1,
                         border_radius=4)
        pygame.draw.rect(screen, border_col, (bx, by, btn_w, btn_h), border_w,
                         border_radius=4)

        # Move name
        _render_text(screen, move.name, font_md, WHITE, bx + 6, by + 4)

        # Type + PP
        _render_text(screen, move.type, font_sm, type_col, bx + 6, by + btn_h - 18)
        pp_text = f"PP {move.pp_current}/{move.pp_max}"
        pp_img = font_sm.render(pp_text, True, LIGHT_GRAY)
        screen.blit(pp_img,
                    (bx + btn_w - pp_img.get_width() - 4, by + btn_h - 18))

    # Slot numbers hint
    for i in range(min(4, len(moves))):
        col = i % 2
        row = i // 2
        bx = panel_x + 4 + col * (btn_w + 8)
        by = panel_y + 6 + row * (btn_h + 8)
        _render_text(screen, str(i + 1), font_sm, YELLOW, bx + btn_w - 16, by + 4)


def draw_battle_message(screen, message_lines: list[str], fonts: dict) -> None:
    """Draw the bottom message text box."""
    box_x = SCREEN_WIDTH // 2
    box_y = SCREEN_HEIGHT - 150
    box_w = SCREEN_WIDTH // 2
    box_h = 150

    _draw_panel(screen, box_x, box_y, box_w, box_h, bg_color=(20, 20, 40))

    font = fonts["medium"]
    line_h = font.get_linesize() + 2
    y = box_y + 10

    # Show the most recent lines that fit in the box
    visible_lines = message_lines[-(box_h // line_h):]
    for line in visible_lines:
        _render_text(screen, line, font, WHITE, box_x + 10, y)
        y += line_h


def draw_battle_scene(screen, battle, selected_move: int,
                      message_lines: list[str], fonts: dict) -> None:
    """Compose the full battle screen by calling all battle drawing helpers."""
    draw_battle_background(screen)

    player_digi = battle.player_active
    enemy_digi = battle.enemy_active

    # Determine primary type color for placeholder sprites
    p_type = player_digi.types[0] if player_digi.types else "Normal"
    e_type = enemy_digi.types[0] if enemy_digi.types else "Normal"
    p_color = TYPE_COLORS.get(p_type, LIGHT_GRAY)
    e_color = TYPE_COLORS.get(e_type, LIGHT_GRAY)

    # Player sprite (bottom-left foreground)
    draw_digimon_placeholder(screen, player_digi.display_name,
                             150, 300, True, p_color)

    # Enemy sprite (top-right background)
    draw_digimon_placeholder(screen, enemy_digi.display_name,
                             SCREEN_WIDTH - 180, 150, False, e_color)

    draw_battle_hud(screen, player_digi, enemy_digi, fonts)

    # Only show move menu when player is choosing
    if battle.state == BattleState.PLAYER_CHOOSE:
        draw_move_menu(screen, player_digi.moves, selected_move, fonts)
        draw_battle_message(screen, message_lines or ["What will you do?"], fonts)
    else:
        # Fill the bottom half with message box only
        _draw_panel(screen, 0, SCREEN_HEIGHT - 150,
                    SCREEN_WIDTH, 150, bg_color=(20, 20, 40))
        draw_battle_message(screen, message_lines, fonts)


# ---------------------------------------------------------------------------
# Overworld UI
# ---------------------------------------------------------------------------

def draw_overworld(screen, world, trainer, fonts: dict) -> None:
    """Draw a simple overworld: area name, a tiny grid map, and a player dot."""
    screen.fill(SCREEN_BG)

    font_lg = fonts["large"]
    font_md = fonts["medium"]
    font_sm = fonts["small"]

    area = world.get_current_area()

    # Area title
    _render_text(screen, area["name"], font_lg, WHITE,
                 SCREEN_WIDTH // 2, 30, center=True)

    # Description
    desc = area.get("description", "")
    # Word-wrap: split into ~60-char lines
    words = desc.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) > 60:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    y = 70
    for line in lines:
        _render_text(screen, line, font_sm, LIGHT_GRAY,
                     SCREEN_WIDTH // 2, y, center=True)
        y += font_sm.get_linesize() + 2

    # ------------------------------------------------------------------
    # Simple grid map showing connected areas
    # ------------------------------------------------------------------
    map_x, map_y = SCREEN_WIDTH // 2 - 200, 160
    map_w, map_h = 400, 260
    _draw_panel(screen, map_x, map_y, map_w, map_h, bg_color=(20, 30, 20))

    connections = world.connected_areas()
    # Place current area in center; surround with connections
    cx, cy = map_x + map_w // 2, map_y + map_h // 2

    # Draw current area node
    pygame.draw.circle(screen, GREEN, (cx, cy), 14)
    _render_text(screen, area["name"][:10], font_sm, BLACK, cx, cy, center=True)

    # Draw connected area nodes in a ring
    import math
    n = len(connections)
    ring_r = 90
    for idx, conn_id in enumerate(connections[:8]):
        angle = (2 * math.pi * idx / max(n, 1)) - math.pi / 2
        nx_ = int(cx + ring_r * math.cos(angle))
        ny_ = int(cy + ring_r * math.sin(angle))

        # Connection line
        pygame.draw.line(screen, DARK_GRAY, (cx, cy), (nx_, ny_), 2)

        conn_area = world.areas.get(conn_id, {})
        conn_name = conn_area.get("name", conn_id)

        pygame.draw.circle(screen, BLUE, (nx_, ny_), 10)
        _render_text(screen, conn_name[:8], font_sm, WHITE,
                     nx_, ny_ + 14, center=True)

    # Player dot overlay on current area
    pygame.draw.circle(screen, YELLOW, (cx, cy - 16), 5)

    # ------------------------------------------------------------------
    # Trainer info strip at the bottom
    # ------------------------------------------------------------------
    info_y = SCREEN_HEIGHT - 80
    _draw_panel(screen, 0, info_y, SCREEN_WIDTH, 80, bg_color=(15, 15, 35))

    active = trainer.active_digimon()
    if active:
        party_str = (
            f"{active.display_name} Lv{active.level}  "
            f"HP {active.current_hp}/{active.max_hp}"
        )
    else:
        party_str = "No active Digimon!"

    _render_text(screen,
                 f"Trainer: {trainer.name}   {party_str}",
                 font_md, WHITE, 12, info_y + 8)
    _render_text(screen,
                 f"Area: {area['name']}   Steps: {trainer.steps}   "
                 f"Money: {trainer.money}",
                 font_sm, LIGHT_GRAY, 12, info_y + 34)
    _render_text(screen,
                 "SPACE: step/encounter   ARROW KEYS: move   ESC: quit",
                 font_sm, DARK_GRAY, 12, info_y + 54)


# ---------------------------------------------------------------------------
# Menu UI
# ---------------------------------------------------------------------------

def draw_main_menu(screen, options: list[str], selected_idx: int,
                   fonts: dict) -> None:
    """Draw a vertical menu list with the selected item highlighted."""
    font = fonts["medium"]
    screen.fill(SCREEN_BG)

    start_y = SCREEN_HEIGHT // 2 - (len(options) * 36) // 2
    for i, option in enumerate(options):
        y = start_y + i * 36
        if i == selected_idx:
            # Highlight bar
            pygame.draw.rect(screen, DARK_GRAY,
                             (SCREEN_WIDTH // 2 - 120, y - 4, 240, 30),
                             border_radius=4)
            pygame.draw.rect(screen, YELLOW,
                             (SCREEN_WIDTH // 2 - 120, y - 4, 240, 30), 2,
                             border_radius=4)
            color = YELLOW
        else:
            color = WHITE

        _render_text(screen, option, font, color,
                     SCREEN_WIDTH // 2, y, center=True)


def draw_title_screen(screen, fonts: dict) -> None:
    """Draw the game title and a 'Press ENTER to start' prompt."""
    screen.fill(SCREEN_BG)

    font_xl = pygame.font.Font(None, 72)
    font_lg = fonts["large"]
    font_sm = fonts["small"]

    # Shadow effect for title
    _render_text(screen, "DIGIMON", font_xl, DARK_GRAY,
                 SCREEN_WIDTH // 2 + 3, SCREEN_HEIGHT // 3 + 3, center=True)
    _render_text(screen, "DIGIMON", font_xl, (80, 160, 240),
                 SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3, center=True)

    # Subtitle
    _render_text(screen, "Digital World Adventure", font_lg, LIGHT_GRAY,
                 SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3 + 60, center=True)

    # Decorative type-colored dots
    colors = list(TYPE_COLORS.values())
    for i, col in enumerate(colors):
        x = SCREEN_WIDTH // 2 - (len(colors) * 14) // 2 + i * 14 + 7
        pygame.draw.circle(screen, col, (x, SCREEN_HEIGHT // 3 + 100), 5)

    # Blinking prompt (always visible — caller handles blink if desired)
    _render_text(screen, "Press ENTER to start", font_lg, WHITE,
                 SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3, center=True)

    # Version hint
    _render_text(screen, "v0.1  –  Fan Game", font_sm, DARK_GRAY,
                 SCREEN_WIDTH - 10, SCREEN_HEIGHT - 20)


def draw_party_screen(screen, party: list, selected_idx: int,
                      fonts: dict) -> None:
    """Draw all 6 party slots with HP bars and basic info."""
    screen.fill(SCREEN_BG)

    font_lg = fonts["large"]
    font_md = fonts["medium"]
    font_sm = fonts["small"]

    _render_text(screen, "PARTY", font_lg, WHITE,
                 SCREEN_WIDTH // 2, 16, center=True)

    slot_h = 72
    slot_w = SCREEN_WIDTH - 40
    start_y = 60

    for i in range(6):
        x = 20
        y = start_y + i * (slot_h + 6)
        border_col = YELLOW if i == selected_idx else DARK_GRAY

        if i < len(party):
            digi = party[i]
            bg_col = (40, 40, 60)
            _draw_panel(screen, x, y, slot_w, slot_h,
                        bg_color=bg_col, border_color=border_col)

            # Type color stripe
            type_col = TYPE_COLORS.get(
                digi.types[0] if digi.types else "Normal", LIGHT_GRAY
            )
            pygame.draw.rect(screen, type_col, (x, y, 6, slot_h))

            # Name + level
            _render_text(screen,
                         f"{digi.display_name}  Lv{digi.level}",
                         font_md, WHITE, x + 14, y + 6)

            # Status
            if digi.status and digi.status != "none":
                pygame.draw.rect(screen, RED,
                                 (x + 14, y + 28, 60, 14), border_radius=3)
                _render_text(screen, digi.status.upper(),
                             font_sm, WHITE, x + 16, y + 29)

            # HP bar
            draw_hp_bar(screen, x + 14, y + 46, slot_w - 100,
                        digi.current_hp, digi.max_hp)
            _render_text(screen,
                         f"{digi.current_hp}/{digi.max_hp} HP",
                         font_sm, LIGHT_GRAY,
                         x + slot_w - 90, y + 42)

        else:
            # Empty slot
            _draw_panel(screen, x, y, slot_w, slot_h,
                        bg_color=(25, 25, 35), border_color=(50, 50, 60))
            _render_text(screen, "---", font_md, DARK_GRAY,
                         x + 14, y + slot_h // 2 - 8)

    _render_text(screen, "ESC: back", font_sm, DARK_GRAY,
                 SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20, center=True)
