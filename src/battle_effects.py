"""
Battle visual effects helpers (hit flashes, damage numbers, hit pause).
Keeps state on the existing battle controller instance ("ctrl").
"""

from __future__ import annotations

from typing import Any, Tuple


def add_hit_flash(ctrl: Any, x: float, y: float, color: Tuple[int, int, int], duration: float = 0.15) -> None:
    if not hasattr(ctrl, 'hit_flashes'):
        ctrl.hit_flashes = []
    ctrl.hit_flashes.append((x, y, duration, color))


def add_damage_number(ctrl: Any, x: float, y: float, dmg: int, color: Tuple[int, int, int]) -> None:
    if not hasattr(ctrl, 'damage_numbers'):
        ctrl.damage_numbers = []
    # time_left, allow small float lifetime
    ctrl.damage_numbers.append((x, y, 0.9, int(dmg), color))


def add_hit_pause(ctrl: Any, amount: float) -> None:
    ctrl.hit_pause = max(getattr(ctrl, 'hit_pause', 0.0), float(amount))


def shake(ctrl: Any, amount: float) -> None:
    ctrl.screen_shake = max(getattr(ctrl, 'screen_shake', 0.0), float(amount))


def update_effects(ctrl: Any, dt: float) -> None:
    # Screen shake decay
    if hasattr(ctrl, 'screen_shake'):
        ctrl.screen_shake = max(0.0, ctrl.screen_shake - dt * 10.0)

    # Hit flashes
    if hasattr(ctrl, 'hit_flashes'):
        ctrl.hit_flashes = [(x, y, t - dt, c) for x, y, t, c in ctrl.hit_flashes if t > dt]

    # Damage numbers
    if hasattr(ctrl, 'damage_numbers'):
        ctrl.damage_numbers = [(x, y - 20.0 * dt, t - dt, d, c) for x, y, t, d, c in ctrl.damage_numbers if t > dt]

