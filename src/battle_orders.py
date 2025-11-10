"""Troop order handling (FOLLOW/HOLD/CHARGE/DEFEND/FOCUS)."""

from __future__ import annotations
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .battle import BattleController


def handle_orders(ctrl: "BattleController") -> None:
    keys = pygame.key.get_pressed()
    new_order = None
    if keys[pygame.K_F1]:
        new_order = "FOLLOW"
    elif keys[pygame.K_F2]:
        new_order = "HOLD"
    elif keys[pygame.K_F3]:
        new_order = "CHARGE"
    elif keys[pygame.K_F4]:
        new_order = "DEFEND"
    elif keys[pygame.K_F5]:
        new_order = "FOCUS"

    if new_order and new_order != ctrl.troop_order:
        ctrl.troop_order = new_order
        ctrl.order_flash_timer = 1.2
        if ctrl.troop_order == "FOCUS":
            # Select nearest enemy to player as focus target
            best = None
            best_d2 = 1e12
            for e in ctrl.enemies:
                if e.alive():
                    dx = e.pos[0] - ctrl.player.pos[0]
                    dy = e.pos[1] - ctrl.player.pos[1]
                    d2 = dx * dx + dy * dy
                    if d2 < best_d2:
                        best_d2 = d2
                        best = e
            ctrl.focus_target_id = best.id if best else None
        else:
            ctrl.focus_target_id = None

