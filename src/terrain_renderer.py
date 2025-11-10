"""
Procedural terrain patch renderer (no external assets).

Builds small surfaces with organic borders, soft gradients and simple
biome-specific patterns (dunes, canopies, reeds, rocks) to make the map
look more natural than solid rectangles.
"""

from __future__ import annotations

import math
import random
from typing import Tuple

import pygame


BiomeColors = {
    "mountain": ((85, 85, 92), (66, 66, 70), (110, 110, 118)),
    "forest": ((36, 110, 62), (22, 84, 46), (60, 140, 80)),
    "desert": ((216, 185, 92), (198, 165, 70), (235, 205, 120)),
    "swamp": ((32, 74, 54), (24, 56, 42), (50, 96, 72)),
}


def _organic_polygon(w: int, h: int, seed: int, points: int = 18, jitter: float = 0.18) -> list[Tuple[int, int]]:
    rng = random.Random(seed)
    cx, cy = w / 2.0, h / 2.0
    rx, ry = w * 0.5, h * 0.5
    poly: list[Tuple[int, int]] = []
    for i in range(points):
        ang = (i / points) * math.tau
        j = 1.0 - jitter * (0.5 + rng.random())
        x = int(cx + math.cos(ang) * rx * j)
        y = int(cy + math.sin(ang) * ry * j)
        poly.append((x, y))
    return poly


def _gradient_fill(surf: pygame.Surface, c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> None:
    w, h = surf.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        col = (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
        pygame.draw.line(surf, col, (0, y), (w, y))


def _pattern_desert(surf: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    w, h = surf.get_size()
    # Dune stripes
    base = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(8):
        y = int((i + 1) * h / 9)
        amp = 6 + rng.randint(0, 6)
        color = (240, 210, 120, 30)
        pts = []
        for x in range(0, w, 8):
            yy = int(y + math.sin((x * 0.05) + i) * amp)
            pts.append((x, yy))
        if len(pts) > 1:
            pygame.draw.aalines(base, color, False, pts)
    surf.blit(base, (0, 0))


def _pattern_forest(surf: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    w, h = surf.get_size()
    canopy = pygame.Surface((w, h), pygame.SRCALPHA)
    # Scatter simple tree canopies
    for _ in range(max(12, w * h // 5000)):
        x = rng.randint(6, w - 6)
        y = rng.randint(6, h - 6)
        r = rng.randint(4, 8)
        col = (44, 130, 72, 140)
        pygame.draw.circle(canopy, col, (x, y), r)
        # trunk hint
        pygame.draw.line(canopy, (60, 40, 30, 160), (x, y + r), (x, y + r + 3), 1)
    surf.blit(canopy, (0, 0))


def _pattern_swamp(surf: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    w, h = surf.get_size()
    blot = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(10):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        rw = rng.randint(18, 42)
        rh = rng.randint(10, 26)
        col = (24, 60, 44, 90)
        pygame.draw.ellipse(blot, col, (x, y, rw, rh))
    # reeds
    for _ in range(20):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        length = rng.randint(6, 12)
        pygame.draw.line(blot, (32, 100, 70, 130), (x, y), (x, y - length), 1)
    surf.blit(blot, (0, 0))


def _pattern_mountain(surf: pygame.Surface, seed: int) -> None:
    rng = random.Random(seed)
    w, h = surf.get_size()
    rocks = pygame.Surface((w, h), pygame.SRCALPHA)
    for _ in range(12):
        x = rng.randint(0, w - 20)
        y = rng.randint(0, h - 12)
        rw = rng.randint(12, 28)
        rh = rng.randint(8, 18)
        col = (120, 120, 128, 110)
        pygame.draw.ellipse(rocks, col, (x, y, rw, rh))
    surf.blit(rocks, (0, 0))


def build_patch_surface(size: Tuple[int, int], biome: str, seed: int) -> pygame.Surface:
    """Return a Surface with an organic-looking patch for the given biome."""
    w, h = max(24, int(size[0])), max(24, int(size[1]))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    colors = BiomeColors.get(biome, BiomeColors["forest"])
    base, mid, highlight = colors

    # Gradient base fill
    _gradient_fill(surf, base, mid)

    # Organic mask polygon
    poly = _organic_polygon(w, h, seed, points=20, jitter=0.22)
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), poly)

    # Apply biome pattern
    pattern = pygame.Surface((w, h), pygame.SRCALPHA)
    if biome == "desert":
        _pattern_desert(pattern, seed)
    elif biome in ("forest", "mountain_forest"):
        _pattern_forest(pattern, seed)
    elif biome == "swamp":
        _pattern_swamp(pattern, seed)
    elif biome in ("mountain", "rugged"):
        _pattern_mountain(pattern, seed)

    # Blend pattern and base
    surf.blit(pattern, (0, 0))

    # Dark outline
    pygame.draw.polygon(surf, (0, 0, 0, 60), poly, 2)

    # Apply mask (keep inside organic border)
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Soft highlight pass
    hl = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(hl, (0, 0, 0, 0), (highlight[0], highlight[1], highlight[2]))
    hl.set_alpha(40)
    surf.blit(hl, (0, 0))

    return surf

