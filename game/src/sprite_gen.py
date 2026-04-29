"""
Procedural Digimon sprite generator.
Draws a distinctive character shape for each type/stage combination.
Sprites are cached as PNG to game/assets/sprites/.
"""
import math
import pygame
from pathlib import Path

SPRITE_DIR = Path(__file__).parent.parent / "assets" / "sprites"
SPRITE_SIZE = 128

# Base colors per type
TYPE_COLORS = {
    "Fire":     (230, 80,  30),
    "Water":    (40,  130, 230),
    "Ice":      (160, 220, 240),
    "Plant":    (60,  180, 60),
    "Electric": (240, 220, 40),
    "Dragon":   (100, 50,  200),
    "Steel":    (160, 170, 185),
    "Holy":     (250, 240, 160),
    "Dark":     (90,  50,  120),
    "Fighting": (200, 80,  50),
    "Flying":   (140, 180, 240),
    "Bug":      (120, 180, 50),
    "Poison":   (150, 70,  190),
    "Normal":   (190, 180, 160),
}

# Highlight colors (lighter version)
def lighten(c, amt=60):
    return tuple(min(255, v + amt) for v in c)

def darken(c, amt=50):
    return tuple(max(0, v - amt) for v in c)

# Stage → body scale factor
STAGE_SCALE = {
    "Baby":     0.38,
    "Rookie":   0.52,
    "Champion": 0.65,
    "Ultimate": 0.78,
    "Mega":     0.92,
}


def _draw_fire(surf, cx, cy, r, col):
    """Spiky flame-like creature."""
    hi = lighten(col)
    dk = darken(col)
    # Body
    pygame.draw.ellipse(surf, col, (cx-r, cy-int(r*0.8), r*2, int(r*1.6)))
    # Flame spikes on top
    for angle in (-35, 0, 35):
        rad = math.radians(angle - 90)
        tx = int(cx + math.cos(rad) * r * 1.3)
        ty = int(cy + math.sin(rad) * r * 1.3 - r * 0.3)
        pygame.draw.polygon(surf, hi, [
            (cx + int(math.cos(math.radians(angle-90-15))*r*0.5),
             cy + int(math.sin(math.radians(angle-90-15))*r*0.5) - r//3),
            (tx, ty),
            (cx + int(math.cos(math.radians(angle-90+15))*r*0.5),
             cy + int(math.sin(math.radians(angle-90+15))*r*0.5) - r//3),
        ])
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//3, cy-r//5), r//5)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3, cy-r//5), r//5)
    pygame.draw.circle(surf, (20,10,0),    (cx-r//3, cy-r//5), r//9)
    pygame.draw.circle(surf, (20,10,0),    (cx+r//3, cy-r//5), r//9)
    # Tiny arms
    pygame.draw.line(surf, dk, (cx-r, cy+r//4), (cx-r-r//2, cy), 3)
    pygame.draw.line(surf, dk, (cx+r, cy+r//4), (cx+r+r//2, cy), 3)


def _draw_water(surf, cx, cy, r, col):
    """Teardrop body with side fins."""
    hi = lighten(col)
    dk = darken(col)
    # Body teardrop
    pygame.draw.ellipse(surf, col, (cx-r, cy-r, r*2, int(r*2.1)))
    # Top bubble highlight
    pygame.draw.ellipse(surf, hi, (cx-r//2, cy-r, r, r))
    # Side fins
    pygame.draw.polygon(surf, dk, [
        (cx-r, cy+r//3), (cx-r-r//2, cy-r//4), (cx-r, cy-r//3)
    ])
    pygame.draw.polygon(surf, dk, [
        (cx+r, cy+r//3), (cx+r+r//2, cy-r//4), (cx+r, cy-r//3)
    ])
    # Tail
    pygame.draw.polygon(surf, dk, [
        (cx-r//3, cy+r), (cx+r//3, cy+r), (cx, cy+int(r*1.5))
    ])
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//3, cy-r//4), r//5)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3, cy-r//4), r//5)
    pygame.draw.circle(surf, (0,20,60),     (cx-r//3, cy-r//4), r//9)
    pygame.draw.circle(surf, (0,20,60),     (cx+r//3, cy-r//4), r//9)


def _draw_ice(surf, cx, cy, r, col):
    """Crystal/diamond angular body."""
    hi = lighten(col, 80)
    dk = darken(col)
    # Diamond body
    pts = [
        (cx,       cy-r),
        (cx+r,     cy),
        (cx+r//2,  cy+int(r*0.9)),
        (cx-r//2,  cy+int(r*0.9)),
        (cx-r,     cy),
    ]
    pygame.draw.polygon(surf, col, pts)
    # Inner highlight
    inner = [(cx, cy-r//2), (cx+r//2, cy), (cx, cy+r//2), (cx-r//2, cy)]
    pygame.draw.polygon(surf, hi, inner)
    # Face
    pygame.draw.circle(surf, (20,60,80),  (cx-r//4, cy-r//8), r//6)
    pygame.draw.circle(surf, (20,60,80),  (cx+r//4, cy-r//8), r//6)
    # Crystal shards on top
    for ox in (-r//2, 0, r//2):
        pygame.draw.polygon(surf, hi, [
            (cx+ox-r//8, cy-r+r//4),
            (cx+ox,      cy-int(r*1.3)),
            (cx+ox+r//8, cy-r+r//4),
        ])


def _draw_plant(surf, cx, cy, r, col):
    """Round body with leaf petals."""
    hi = lighten(col, 50)
    dk = darken(col)
    # Leaves behind body
    for angle in (0, 60, 120, 180, 240, 300):
        rad = math.radians(angle)
        lx = int(cx + math.cos(rad) * r * 1.1)
        ly = int(cy + math.sin(rad) * r * 1.1 - r//4)
        pygame.draw.ellipse(surf, dk, (lx-r//3, ly-r//2, r//2+2, r+2))
        pygame.draw.ellipse(surf, col, (lx-r//3+2, ly-r//2+2, r//2-2, r-2))
    # Round body
    pygame.draw.circle(surf, hi, (cx, cy), r)
    pygame.draw.circle(surf, col, (cx, cy), int(r*0.85))
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//3, cy-r//6), r//5)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3, cy-r//6), r//5)
    pygame.draw.circle(surf, (10,40,10),    (cx-r//3, cy-r//6), r//9)
    pygame.draw.circle(surf, (10,40,10),    (cx+r//3, cy-r//6), r//9)
    # Stem on top
    pygame.draw.line(surf, dk, (cx, cy-r), (cx, cy-r-r//2), 4)
    pygame.draw.circle(surf, hi, (cx, cy-r-r//2), r//4)


def _draw_electric(surf, cx, cy, r, col):
    """Zigzag/lightning bolt body."""
    hi = lighten(col, 60)
    dk = darken(col)
    # Body
    pygame.draw.ellipse(surf, col, (cx-r, cy-r, r*2, r*2))
    # Zigzag ears/horns
    pygame.draw.polygon(surf, hi, [
        (cx-r//2, cy-r),
        (cx-r//4, cy-int(r*1.5)),
        (cx,      cy-r),
    ])
    pygame.draw.polygon(surf, hi, [
        (cx+r//2, cy-r),
        (cx+r//4, cy-int(r*1.5)),
        (cx,      cy-r),
    ])
    # Lightning bolt on chest
    bolt = [
        (cx-r//6, cy-r//2),
        (cx+r//8, cy-r//8),
        (cx-r//8, cy-r//8),
        (cx+r//6, cy+r//2),
    ]
    pygame.draw.polygon(surf, hi, bolt)
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//3, cy-r//4), r//5)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3, cy-r//4), r//5)
    pygame.draw.circle(surf, (30,30,0),     (cx-r//3, cy-r//4), r//9)
    pygame.draw.circle(surf, (30,30,0),     (cx+r//3, cy-r//4), r//9)


def _draw_dragon(surf, cx, cy, r, col):
    """Lizard-like body with wings."""
    hi = lighten(col, 50)
    dk = darken(col)
    # Wings
    pygame.draw.polygon(surf, dk, [
        (cx-r//2, cy-r//4),
        (cx-int(r*1.8), cy-r),
        (cx-r, cy+r//2),
    ])
    pygame.draw.polygon(surf, dk, [
        (cx+r//2, cy-r//4),
        (cx+int(r*1.8), cy-r),
        (cx+r, cy+r//2),
    ])
    # Body
    pygame.draw.ellipse(surf, col, (cx-r, cy-r, r*2, int(r*2.2)))
    # Head
    pygame.draw.ellipse(surf, col, (cx-int(r*0.7), cy-r-int(r*0.5), int(r*1.4), int(r*0.9)))
    # Horns
    pygame.draw.polygon(surf, dk, [(cx-r//3, cy-r-r//3), (cx-r//4, cy-int(r*1.8)), (cx-r//8, cy-r-r//3)])
    pygame.draw.polygon(surf, dk, [(cx+r//3, cy-r-r//3), (cx+r//4, cy-int(r*1.8)), (cx+r//8, cy-r-r//3)])
    # Eyes
    pygame.draw.circle(surf, (255,220,0), (cx-r//4, cy-r-r//6), r//5)
    pygame.draw.circle(surf, (255,220,0), (cx+r//4, cy-r-r//6), r//5)
    pygame.draw.circle(surf, (0,0,0),     (cx-r//4, cy-r-r//6), r//10)
    pygame.draw.circle(surf, (0,0,0),     (cx+r//4, cy-r-r//6), r//10)
    # Tail
    pygame.draw.line(surf, dk, (cx, cy+r), (cx-r//2, cy+int(r*1.7)), 5)


def _draw_steel(surf, cx, cy, r, col):
    """Blocky armored robot shape."""
    hi = lighten(col, 60)
    dk = darken(col)
    # Torso block
    pygame.draw.rect(surf, col,  (cx-r, cy-int(r*0.5), r*2, int(r*1.5)))
    # Head block
    pygame.draw.rect(surf, col,  (cx-int(r*0.7), cy-r-int(r*0.6), int(r*1.4), int(r*0.8)))
    pygame.draw.rect(surf, hi,   (cx-int(r*0.6), cy-r-int(r*0.5), int(r*1.2), int(r*0.6)))
    # Arms
    pygame.draw.rect(surf, dk, (cx-r-r//2, cy-r//3, r//2, int(r*1.2)))
    pygame.draw.rect(surf, dk, (cx+r,      cy-r//3, r//2, int(r*1.2)))
    # Legs
    pygame.draw.rect(surf, dk, (cx-int(r*0.6), cy+r, int(r*0.5), r//2))
    pygame.draw.rect(surf, dk, (cx+int(r*0.1), cy+r, int(r*0.5), r//2))
    # Visor
    pygame.draw.rect(surf, (80,200,255), (cx-r//2, cy-r-r//4, r, r//4))
    # Rivets
    for ox in (-r//2, 0, r//2):
        pygame.draw.circle(surf, dk, (cx+ox, cy), r//10)


def _draw_holy(surf, cx, cy, r, col):
    """Angelic shape with halo and wings."""
    hi = lighten(col, 80)
    dk = (200, 160, 40)
    # Wings (feathered)
    for i, side in enumerate([-1, 1]):
        wx = cx + side * r//2
        for j in range(3):
            wy = cy - r//4 + j * r//3
            pygame.draw.ellipse(surf, hi, (wx + side*(j*r//5), wy-r//4, int(r*0.8), r//3))
    # Body (robe)
    pygame.draw.ellipse(surf, col, (cx-int(r*0.7), cy-r//2, int(r*1.4), int(r*1.5)))
    # Head
    pygame.draw.circle(surf, hi, (cx, cy-r//2-r//3), int(r*0.55))
    # Halo
    pygame.draw.circle(surf, dk, (cx, cy-r), int(r*0.55), 4)
    # Eyes
    pygame.draw.circle(surf, (100,80,20), (cx-r//5, cy-r//2-r//3), r//6)
    pygame.draw.circle(surf, (100,80,20), (cx+r//5, cy-r//2-r//3), r//6)


def _draw_dark(surf, cx, cy, r, col):
    """Bat/shadow shape with horns."""
    hi = lighten(col, 40)
    dk = darken(col, 30)
    # Cape/bat wings
    pygame.draw.polygon(surf, dk, [
        (cx, cy),
        (cx-int(r*1.8), cy-r),
        (cx-r, cy+r),
    ])
    pygame.draw.polygon(surf, dk, [
        (cx, cy),
        (cx+int(r*1.8), cy-r),
        (cx+r, cy+r),
    ])
    # Body
    pygame.draw.circle(surf, col, (cx, cy-r//4), int(r*0.8))
    # Horns
    pygame.draw.polygon(surf, hi, [(cx-r//3, cy-r), (cx-r//4, cy-int(r*1.6)), (cx-r//8, cy-r)])
    pygame.draw.polygon(surf, hi, [(cx+r//3, cy-r), (cx+r//4, cy-int(r*1.6)), (cx+r//8, cy-r)])
    # Glowing eyes
    pygame.draw.circle(surf, (255, 50, 50), (cx-r//3, cy-r//3), r//5)
    pygame.draw.circle(surf, (255, 50, 50), (cx+r//3, cy-r//3), r//5)
    pygame.draw.circle(surf, (255,200,200),(cx-r//3, cy-r//3), r//10)
    pygame.draw.circle(surf, (255,200,200),(cx+r//3, cy-r//3), r//10)


def _draw_fighting(surf, cx, cy, r, col):
    """Stocky muscular shape with big fists."""
    hi = lighten(col, 50)
    dk = darken(col)
    # Legs
    pygame.draw.ellipse(surf, dk, (cx-r, cy+r//2, int(r*0.9), int(r*0.9)))
    pygame.draw.ellipse(surf, dk, (cx+r//8, cy+r//2, int(r*0.9), int(r*0.9)))
    # Torso
    pygame.draw.ellipse(surf, col, (cx-r, cy-r//2, r*2, int(r*1.4)))
    # Head
    pygame.draw.circle(surf, hi, (cx, cy-r//2-r//3), int(r*0.55))
    # Big fists
    pygame.draw.circle(surf, dk, (cx-r-r//3, cy+r//6), int(r*0.45))
    pygame.draw.circle(surf, dk, (cx+r+r//3, cy+r//6), int(r*0.45))
    # Arms
    pygame.draw.line(surf, col, (cx-r, cy), (cx-r-r//3+r//5, cy+r//6), r//3)
    pygame.draw.line(surf, col, (cx+r, cy), (cx+r+r//3-r//5, cy+r//6), r//3)
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//5, cy-r//2-r//3), r//6)
    pygame.draw.circle(surf, (255,255,255), (cx+r//5, cy-r//2-r//3), r//6)
    pygame.draw.circle(surf, (60,10,10),    (cx-r//5, cy-r//2-r//3), r//10)
    pygame.draw.circle(surf, (60,10,10),    (cx+r//5, cy-r//2-r//3), r//10)


def _draw_flying(surf, cx, cy, r, col):
    """Bird shape with spread wings."""
    hi = lighten(col, 60)
    dk = darken(col)
    # Spread wings
    wing_pts_l = [
        (cx-r//3, cy),
        (cx-int(r*1.8), cy-r//2),
        (cx-int(r*1.6), cy+r//3),
        (cx-r//2, cy+r//4),
    ]
    wing_pts_r = [
        (cx+r//3, cy),
        (cx+int(r*1.8), cy-r//2),
        (cx+int(r*1.6), cy+r//3),
        (cx+r//2, cy+r//4),
    ]
    pygame.draw.polygon(surf, col, wing_pts_l)
    pygame.draw.polygon(surf, col, wing_pts_r)
    pygame.draw.polygon(surf, hi, [(cx-r//3,cy),(cx-r,cy-r//4),(cx-r//2,cy+r//6)])
    pygame.draw.polygon(surf, hi, [(cx+r//3,cy),(cx+r,cy-r//4),(cx+r//2,cy+r//6)])
    # Body
    pygame.draw.ellipse(surf, hi, (cx-r//2, cy-r//3, r, int(r*1.1)))
    # Head
    pygame.draw.circle(surf, hi, (cx, cy-r//2), int(r*0.4))
    # Beak
    pygame.draw.polygon(surf, (240,180,30), [(cx, cy-r//2), (cx+r//3, cy-r//2), (cx+r//6, cy-r//3)])
    # Eye
    pygame.draw.circle(surf, (0,0,0), (cx-r//8, cy-r//2), r//8)
    pygame.draw.circle(surf, (255,255,255), (cx-r//8-r//16, cy-r//2-r//16), r//16)
    # Tail feathers
    pygame.draw.polygon(surf, dk, [(cx-r//4, cy+r//2),(cx+r//4, cy+r//2),(cx, cy+r)])


def _draw_bug(surf, cx, cy, r, col):
    """Insect with segmented body and antennae."""
    hi = lighten(col, 50)
    dk = darken(col)
    # Abdomen
    pygame.draw.ellipse(surf, dk, (cx-int(r*0.6), cy+r//4, int(r*1.2), int(r*0.9)))
    # Thorax
    pygame.draw.ellipse(surf, col, (cx-int(r*0.7), cy-r//4, int(r*1.4), int(r*0.8)))
    # Head
    pygame.draw.circle(surf, hi, (cx, cy-r//2-r//4), int(r*0.5))
    # Antennae
    pygame.draw.line(surf, dk, (cx-r//4, cy-r//2-r//4), (cx-r, cy-int(r*1.3)), 2)
    pygame.draw.circle(surf, dk, (cx-r, cy-int(r*1.3)), r//8)
    pygame.draw.line(surf, dk, (cx+r//4, cy-r//2-r//4), (cx+r, cy-int(r*1.3)), 2)
    pygame.draw.circle(surf, dk, (cx+r, cy-int(r*1.3)), r//8)
    # 3 pairs of legs
    for i in range(3):
        yo = cy - r//8 + i * (r//3)
        pygame.draw.line(surf, dk, (cx-int(r*0.6), yo), (cx-r-r//3, yo+r//4), 2)
        pygame.draw.line(surf, dk, (cx+int(r*0.6), yo), (cx+r+r//3, yo+r//4), 2)
    # Compound eyes
    pygame.draw.circle(surf, (200,255,100), (cx-r//5, cy-r//2-r//4), r//5)
    pygame.draw.circle(surf, (200,255,100), (cx+r//5, cy-r//2-r//4), r//5)
    pygame.draw.circle(surf, (0,0,0),       (cx-r//5, cy-r//2-r//4), r//10)
    pygame.draw.circle(surf, (0,0,0),       (cx+r//5, cy-r//2-r//4), r//10)


def _draw_poison(surf, cx, cy, r, col):
    """Blob shape with tendrils."""
    hi = lighten(col, 50)
    dk = darken(col)
    # Tendrils
    for angle in (30, 90, 150, 210, 270, 330):
        rad = math.radians(angle)
        tx = int(cx + math.cos(rad) * r * 1.4)
        ty = int(cy + math.sin(rad) * r * 1.4)
        pygame.draw.line(surf, dk, (cx, cy), (tx, ty), r//5)
        pygame.draw.circle(surf, dk, (tx, ty), r//6)
    # Blob body
    pygame.draw.circle(surf, col, (cx, cy), r)
    pygame.draw.circle(surf, hi,  (cx-r//4, cy-r//4), r//2)
    # Fangs
    pygame.draw.polygon(surf, (220,220,220), [(cx-r//4, cy+r//4), (cx-r//6, cy+r//2), (cx, cy+r//4)])
    pygame.draw.polygon(surf, (220,220,220), [(cx+r//4, cy+r//4), (cx+r//6, cy+r//2), (cx, cy+r//4)])
    # Eyes
    pygame.draw.circle(surf, (255,50,255), (cx-r//3, cy-r//5), r//5)
    pygame.draw.circle(surf, (255,50,255), (cx+r//3, cy-r//5), r//5)
    pygame.draw.circle(surf, (0,0,0),      (cx-r//3, cy-r//5), r//10)
    pygame.draw.circle(surf, (0,0,0),      (cx+r//3, cy-r//5), r//10)


def _draw_normal(surf, cx, cy, r, col):
    """Friendly round creature."""
    hi = lighten(col, 60)
    dk = darken(col)
    # Body
    pygame.draw.circle(surf, col, (cx, cy), r)
    pygame.draw.circle(surf, hi,  (cx-r//3, cy-r//3), r//2)
    # Ears
    pygame.draw.ellipse(surf, col, (cx-r-r//4, cy-r-r//4, r//2, r//2+r//4))
    pygame.draw.ellipse(surf, col, (cx+r-r//4, cy-r-r//4, r//2, r//2+r//4))
    pygame.draw.ellipse(surf, (255,200,200), (cx-r-r//8, cy-r-r//8, r//4, r//3))
    pygame.draw.ellipse(surf, (255,200,200), (cx+r,       cy-r-r//8, r//4, r//3))
    # Legs
    pygame.draw.ellipse(surf, dk, (cx-r+r//4, cy+int(r*0.7), int(r*0.6), int(r*0.5)))
    pygame.draw.ellipse(surf, dk, (cx+r//8,   cy+int(r*0.7), int(r*0.6), int(r*0.5)))
    # Eyes
    pygame.draw.circle(surf, (255,255,255), (cx-r//3, cy-r//5), r//4)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3, cy-r//5), r//4)
    pygame.draw.circle(surf, (30,20,10),    (cx-r//3, cy-r//5), r//8)
    pygame.draw.circle(surf, (30,20,10),    (cx+r//3, cy-r//5), r//8)
    pygame.draw.circle(surf, (255,255,255), (cx-r//3+r//16, cy-r//5-r//16), r//16)
    pygame.draw.circle(surf, (255,255,255), (cx+r//3+r//16, cy-r//5-r//16), r//16)
    # Smile
    pygame.draw.arc(surf, dk, (cx-r//3, cy+r//8, r//1+r//3, r//3), math.pi, 0, 2)


DRAW_FUNCS = {
    "Fire":     _draw_fire,
    "Water":    _draw_water,
    "Ice":      _draw_ice,
    "Plant":    _draw_plant,
    "Electric": _draw_electric,
    "Dragon":   _draw_dragon,
    "Steel":    _draw_steel,
    "Holy":     _draw_holy,
    "Dark":     _draw_dark,
    "Fighting": _draw_fighting,
    "Flying":   _draw_flying,
    "Bug":      _draw_bug,
    "Poison":   _draw_poison,
    "Normal":   _draw_normal,
}


def _safe_filename(name: str) -> str:
    import re
    n = name.lower()
    n = re.sub(r"[^a-z0-9]", "_", n)
    n = re.sub(r"_+", "_", n).strip("_")
    return n + ".png"


def generate_sprite(name: str, types: list, stage: str) -> pygame.Surface:
    """Generate and return a 128x128 sprite surface."""
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    primary_type = types[0] if types else "Normal"
    col = TYPE_COLORS.get(primary_type, TYPE_COLORS["Normal"])
    scale = STAGE_SCALE.get(stage, 0.55)
    r = max(10, int(SPRITE_SIZE * scale * 0.45))
    cx = SPRITE_SIZE // 2
    cy = SPRITE_SIZE // 2

    draw_fn = DRAW_FUNCS.get(primary_type, _draw_normal)
    draw_fn(surf, cx, cy, r, col)

    # Outline pass — subtle dark border
    outline = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    outline.fill((0, 0, 0, 0))
    draw_fn(outline, cx, cy, r + 1, darken(col, 80))
    # Blit outline behind
    final = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    final.fill((0, 0, 0, 0))
    final.blit(outline, (0, 0))
    final.blit(surf, (0, 0))

    return final


def get_sprite(name: str, types: list, stage: str) -> pygame.Surface:
    """Return cached sprite if available, otherwise generate and cache it."""
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SPRITE_DIR / _safe_filename(name)
    if path.exists():
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except Exception:
            pass
    surf = generate_sprite(name, types, stage)
    try:
        pygame.image.save(surf, str(path))
    except Exception:
        pass
    return surf
