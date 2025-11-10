"""World map building sprites rendering.

Selects Tiny Swords Buildings sprites based on location type and the player's
relation to that location's faction, and draws them on the overworld map.
"""

from __future__ import annotations
import os
import pygame

from typing import Optional

# Cache surfaces per (path, target_h)
_CACHE: dict[tuple[str, int], pygame.Surface] = {}


def _clamp(val: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, val))


def _load_and_scale(path: str, target_h: int) -> Optional[pygame.Surface]:
    key = (path, target_h)
    surf = _CACHE.get(key)
    if surf is not None:
        return surf
    try:
        img = pygame.image.load(path).convert_alpha()
        if target_h > 0 and img.get_height() != target_h:
            scale = target_h / img.get_height()
            w = max(1, int(img.get_width() * scale))
            img = pygame.transform.smoothscale(img, (w, target_h))
        _CACHE[key] = img
        return img
    except Exception:
        return None


def _relation_bucket(faction: str, relations) -> str:
    """Return one of 'blue','black','red','yellow' according to relation.

    - 'yellow' for bandits (bandit camps and any bandit-labeled loc)
    - 'blue' if > +30 (ally)
    - 'red' if < -30 (enemy)
    - 'black' otherwise (neutral)
    """
    if faction == 'bandits':
        return 'yellow'
    rel = 0
    try:
        if relations and hasattr(relations, 'relations'):
            rel = int(relations.relations.get(faction, 0))
    except Exception:
        rel = 0
    if rel > 30:
        return 'blue'
    if rel < -30:
        return 'red'
    return 'black'


def _folder_for_bucket(bucket: str) -> str:
    return {
        'blue': 'Blue Buildings',
        'black': 'Black Buildings',
        'red': 'Red Buildings',
        'yellow': 'Yellow Buildings',
    }.get(bucket, 'Black Buildings')


def draw_location_sprite(screen: pygame.Surface, loc, pos: tuple[int, int], relations) -> bool:
    """Draw a building sprite for a world location.

    Returns True if a sprite was drawn (caller can fallback otherwise).
    """
    try:
        loc_type = getattr(loc, 'location_type', '')
        fac = getattr(loc, 'faction', '') or ''
        bucket = _relation_bucket(fac, relations)
        folder = _folder_for_bucket(bucket)

        base = os.path.join('Tiny Swords (Free Pack)', 'Buildings', folder)

        # Pick file and dynamic size by type (scaled from loc.radius)
        lr = int(getattr(loc, 'radius', 60) or 60)
        if loc_type == 'castle':
            fname = 'Castle.png'
            target_h = _clamp(int(lr * 0.90), 44, 80)
            offset_up = 0
        elif loc_type == 'bandit_camp':
            # Always use the Tower sprite for bandit camps, regardless of relation
            base = os.path.join('Tiny Swords (Free Pack)', 'Buildings', _folder_for_bucket('yellow'))
            fname = 'Tower.png'
            # Double the visual size of bandit camps
            target_h = _clamp(int(lr * 0.70) * 2, 68, 136)
            offset_up = 0
        else:  # 'town' and any other -> House1
            fname = 'House1.png'
            target_h = _clamp(int(lr * 0.60), 30, 60)
            offset_up = 0

        path = os.path.join(base, fname)
        surf = _load_and_scale(path, target_h)
        if not surf:
            return False

        # Anchor center on pos so the sprite aligns with the interaction circle center
        x, y = pos
        rect = surf.get_rect()
        blit_pos = (int(x - rect.width // 2), int(y - rect.height // 2))
        screen.blit(surf, blit_pos)
        return True
    except Exception:
        return False
