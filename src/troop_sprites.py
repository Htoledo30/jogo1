"""Troop sprites rendering (allied units - Blue Units).

Handles sprite loading and rendering for player's troops in battle.
"""

from __future__ import annotations
import os
import pygame

from .sprite_manager import load_spritesheet

# Sprite scaling
TROOP_SPRITE_HEIGHT_PER_RADIUS = 6.0
TROOP_SPRITE_FOOT_OFFSET_PCT = 0.40

_CACHE: dict[str, pygame.Surface] = {}
_TROOP_FACING_RIGHT: dict[int, bool] = {}
_TROOP_LAST_FLIP_MS: dict[int, int] = {}
_TROOP_SIGN_STREAK: dict[int, int] = {}


def _load_troop_sprite(troop_type: str) -> pygame.Surface | None:
    """Load first frame of troop sprite from Blue Units."""
    key = f"troop_{troop_type}"
    if key in _CACHE:
        return _CACHE[key]

    # Map troop types to sprite files
    sprite_map = {
        "warrior": "Warrior/Warrior_Idle.png",
        "archer": "Archer/Archer_Idle.png",
        "tank": "Lancer/Lancer_Idle.png",
        "cavalry": "Lancer/Lancer_Idle.png",
        "lancer": "Lancer/Lancer_Idle.png",
    }

    sprite_file = sprite_map.get(troop_type.lower(), "Warrior/Warrior_Idle.png")
    path = os.path.join("Tiny Swords (Free Pack)", "Units", "Blue Units", sprite_file)

    try:
        sheet = pygame.image.load(path).convert_alpha()
        sw, sh = sheet.get_width(), sheet.get_height()

        # Try square frames first
        frames = load_spritesheet(path, sh, sh)

        # Fallback: assume 8 frames horizontally
        if len(frames) <= 1 and sw > 0:
            fw = max(1, sw // 8)
            frames = load_spritesheet(path, fw, sh, num_frames=8)

        # Get first frame
        sprite = frames[0] if frames else None
        _CACHE[key] = sprite
        return sprite
    except Exception:
        _CACHE[key] = None
        return None


def update_troop_facing(troop, prev_pos: tuple[float, float] | None) -> None:
    """Update facing with hysteresis to avoid excessive flipping."""
    tid = troop.id
    if prev_pos is None:
        _TROOP_FACING_RIGHT[tid] = _TROOP_FACING_RIGHT.get(tid, True)
        _TROOP_SIGN_STREAK[tid] = 0
        _TROOP_LAST_FLIP_MS[tid] = _TROOP_LAST_FLIP_MS.get(tid, 0)
        return

    dx = float(troop.pos[0]) - float(prev_pos[0])
    if abs(dx) < 1.0:
        _TROOP_SIGN_STREAK[tid] = 0
        return

    want_right = dx > 0
    curr_right = _TROOP_FACING_RIGHT.get(tid, True)
    if want_right == curr_right:
        _TROOP_SIGN_STREAK[tid] = 0
        return

    _TROOP_SIGN_STREAK[tid] = _TROOP_SIGN_STREAK.get(tid, 0) + 1
    now = pygame.time.get_ticks()
    last = _TROOP_LAST_FLIP_MS.get(tid, 0)
    if _TROOP_SIGN_STREAK[tid] >= 3 and (now - last) >= 200:
        _TROOP_FACING_RIGHT[tid] = want_right
        _TROOP_SIGN_STREAK[tid] = 0
        _TROOP_LAST_FLIP_MS[tid] = now


def draw_troop_sprite(troop, screen: pygame.Surface, screen_pos: tuple[int, int]) -> bool:
    """Draw troop sprite with proper scaling and flip. Returns True if drawn."""
    # Determine troop type from archetype or unit_type
    troop_type = getattr(troop, 'unit_type', None) or getattr(troop, 'archetype', 'warrior')

    sprite = _load_troop_sprite(troop_type)
    if not sprite:
        return False

    # Scale to troop radius
    target_h = max(8, int(getattr(troop, 'radius', 10) * TROOP_SPRITE_HEIGHT_PER_RADIUS))
    scale = target_h / max(1, sprite.get_height())
    target_w = max(8, int(sprite.get_width() * scale))
    sprite_scaled = pygame.transform.smoothscale(sprite, (target_w, target_h))

    # Apply flip
    facing_right = _TROOP_FACING_RIGHT.get(troop.id, True)
    if not facing_right:
        sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

    # Draw with foot offset
    x, y = screen_pos
    offset_y = int(target_h * TROOP_SPRITE_FOOT_OFFSET_PCT)
    blit_pos = (int(x - target_w // 2), int(y - target_h + offset_y))
    screen.blit(sprite_scaled, blit_pos)
    return True
