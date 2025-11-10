"""Battle arena setup and themed variants.

This module contains the data-driven definitions for battle arenas
and the initializer that applies a randomly selected variant to the
current BattleController instance.
"""

from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING
import pygame

from .constants_battle import ARENA_WIDTH, ARENA_HEIGHT, ARENA_BORDER

if TYPE_CHECKING:
    from .battle import BattleController


def _rect_from_center(cx: float, cy: float, w: float, h: float) -> pygame.Rect:
    return pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))


def _rect_tuple_from_center(cx: float, cy: float, w: float, h: float) -> tuple[int, int, int, int]:
    return (int(cx - w / 2), int(cy - h / 2), int(w), int(h))


def _rect_to_tuple(rect: pygame.Rect) -> tuple[int, int, int, int]:
    return (rect.x, rect.y, rect.width, rect.height)


def build_arena_variants(ctrl: "BattleController") -> List[Dict[str, Any]]:
    w, h = ARENA_WIDTH, ARENA_HEIGHT
    variants: List[Dict[str, Any]] = []

    # Highland / default hill
    hill_rect = _rect_from_center(w / 2, h / 2 - 20, 420, 220)
    variants.append({
        "id": "highland",
        "name": "Highland Pass",
        "ambient_tint": None,
        "high_ground_rects": [hill_rect],
        "decor": [
            {
                "type": "hill_polygon",
                "fill": (139, 90, 43, 90),
                "outline": (180, 140, 80, 140)
            }
        ],
    })

    # Desert dunes
    dune_features: List[Dict[str, Any]] = []
    for center_x in (w * 0.32, w * 0.62):
        width = ctrl.rng.randint(380, 540)
        height = ctrl.rng.randint(150, 230)
        dune_features.append({
            "type": "ellipse",
            "rect": _rect_tuple_from_center(center_x, h * 0.6, width, height),
            "color": (214, 182, 123, 120),
            "border": (255, 220, 150, 140),
            "border_width": 3
        })
    if ctrl.rng.random() < 0.7:
        width = ctrl.rng.randint(260, 360)
        height = ctrl.rng.randint(120, 160)
        dune_features.append({
            "type": "ellipse",
            "rect": _rect_tuple_from_center(w * 0.5, h * 0.48, width, height),
            "color": (196, 162, 96, 100),
            "border": (240, 200, 140, 120),
            "border_width": 2
        })
    oasis_points = []
    for _ in range(18):
        radius = ctrl.rng.randint(8, 14)
        x = ctrl.rng.randint(int(w * 0.25), int(w * 0.75))
        y = ctrl.rng.randint(int(h * 0.45), int(h * 0.75))
        color = (
            ctrl.rng.randint(20, 70),
            ctrl.rng.randint(120, 190),
            ctrl.rng.randint(100, 160),
            ctrl.rng.randint(140, 200)
        )
        oasis_points.append((x, y, radius, color))
    dune_features.append({"type": "scatter", "points": oasis_points})
    variants.append({
        "id": "dunes",
        "name": "Dunas de Siwa",
        "ambient_tint": (40, 25, 5, 70),
        "high_ground_rects": [],
        "decor": dune_features,
    })

    # Forest clearing
    clearing_rect = _rect_tuple_from_center(w / 2, h / 2 - 10, 520, 240)
    forest_features: List[Dict[str, Any]] = [
        {
            "type": "rect",
            "rect": clearing_rect,
            "color": (30, 70, 30, 90),
            "border_color": (80, 130, 80, 130),
            "border_width": 2,
            "border_radius": 80
        }
    ]
    tree_points = []
    for _ in range(28):
        radius = ctrl.rng.randint(18, 28)
        x = ctrl.rng.randint(ARENA_BORDER + 30, w - ARENA_BORDER - 30)
        y = ctrl.rng.randint(ARENA_BORDER + 30, h - ARENA_BORDER - 80)
        color = (
            ctrl.rng.randint(20, 60),
            ctrl.rng.randint(110, 170),
            ctrl.rng.randint(30, 70),
            ctrl.rng.randint(160, 220)
        )
        tree_points.append((x, y, radius, color))
    forest_features.append({"type": "scatter", "points": tree_points})
    forest_features.append({
        "type": "rect",
        "rect": (ARENA_BORDER + 80, int(h * 0.72), w - (ARENA_BORDER + 160), 18),
        "color": (90, 60, 30, 160),
        "border_radius": 6
    })
    variants.append({
        "id": "forest",
        "name": "Clareira Ancestral",
        "ambient_tint": (5, 25, 5, 60),
        "high_ground_rects": [],
        "decor": forest_features,
    })

    # Ruined arena with raised platform
    plateau_rect = _rect_from_center(w / 2, h / 2 - 5, 360, 150)
    ruin_features: List[Dict[str, Any]] = [
        {
            "type": "rect",
            "rect": (ARENA_BORDER + 40, ARENA_BORDER + 40, w - (ARENA_BORDER + 80), h - (ARENA_BORDER + 100)),
            "color": (60, 60, 75, 90),
            "border_color": (90, 90, 110, 130),
            "border_width": 2
        },
        {
            "type": "plateau",
            "rect": _rect_to_tuple(plateau_rect),
            "color": (120, 120, 140, 160),
            "border_color": (200, 200, 220, 180)
        }
    ]
    pillar_points = []
    for offset_x in (-220, -130, 130, 220):
        for offset_y in (-70, 70):
            radius = ctrl.rng.randint(10, 14)
            color = (170, 160, 150, 180)
            pillar_points.append((int(w / 2 + offset_x), int(h / 2 + offset_y), radius, color))
    ruin_features.append({"type": "scatter", "points": pillar_points})
    variants.append({
        "id": "ruins",
        "name": "Arena em Ruínas",
        "ambient_tint": (15, 15, 25, 80),
        "high_ground_rects": [plateau_rect],
        "decor": ruin_features,
    })

    return variants


def init_arena_theme(ctrl: "BattleController") -> None:
    """Pick an arena variant and apply it to the controller."""
    variants = build_arena_variants(ctrl)
    ctrl.arena_variant = ctrl.rng.choice(variants)
    ctrl.arena_variant_id = ctrl.arena_variant.get("id", "highland")
    ctrl.arena_variant_name = ctrl.arena_variant.get("name", "Arena")
    ctrl.arena_ambient_tint = ctrl.arena_variant.get("ambient_tint")
    ctrl.arena_decor = ctrl.arena_variant.get("decor", [])

    rects = [r.copy() for r in ctrl.arena_variant.get("high_ground_rects", [])]
    ctrl.high_ground_rects = rects
    if rects:
        ctrl.hill_zone = rects[0].copy()
    else:
        ctrl.hill_zone = pygame.Rect(-999, -999, 0, 0)

