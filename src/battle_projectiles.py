"""
Simple projectile manager for ranged attacks (bows/slings) with teams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple
import math


@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    lifetime: float = 2.0
    radius: float = 4.0
    team: str = "ally"  # "ally" projectiles hit enemies; "enemy" hit player/troops


class ProjectileManager:
    def __init__(self, max_count: int = 60) -> None:
        self.projectiles: List[Projectile] = []
        self.max_count = int(max_count)

    def spawn(self, x: float, y: float, dir_xy: Tuple[float, float], speed: float, damage: float, team: str = "ally") -> None:
        dx, dy = dir_xy
        # Budget: cap total projectiles to avoid saturation
        if len(self.projectiles) >= self.max_count:
            # Drop oldest
            self.projectiles.pop(0)
        self.projectiles.append(Projectile(x, y, dx * speed, dy * speed, damage, team=team))

    def update(self, ctrl: Any, dt: float) -> None:
        # Update positions and handle collisions
        alive: List[Projectile] = []
        for p in self.projectiles:
            p.lifetime -= dt
            if p.lifetime <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt

            # Clamp inside arena
            if p.x < ctrl.ARENA_BORDER or p.x > (ctrl.ARENA_WIDTH - ctrl.ARENA_BORDER):
                continue
            if p.y < ctrl.ARENA_BORDER or p.y > (ctrl.ARENA_HEIGHT - ctrl.ARENA_BORDER):
                continue

            hit_any = False
            if p.team == "ally":
                # Hit enemies
                for e in ctrl.enemies:
                    if not getattr(e, 'alive', lambda: True)():
                        continue
                    dx = e.pos[0] - p.x
                    dy = e.pos[1] - p.y
                    if math.hypot(dx, dy) <= (getattr(e, 'radius', 10.0) + p.radius):
                        e.apply_damage(p.damage)
                        hit_any = True
                        break
            else:
                # Hit player or troops
                if getattr(ctrl.player, 'alive', lambda: True)():
                    dxp = ctrl.player.pos[0] - p.x
                    dyp = ctrl.player.pos[1] - p.y
                    if math.hypot(dxp, dyp) <= (getattr(ctrl.player, 'radius', 12.0) + p.radius):
                        ctrl.player.apply_damage(p.damage)
                        hit_any = True
                if not hit_any:
                    for t in ctrl.troops:
                        if not getattr(t, 'alive', lambda: True)():
                            continue
                        dxt = t.pos[0] - p.x
                        dyt = t.pos[1] - p.y
                        if math.hypot(dxt, dyt) <= (getattr(t, 'radius', 10.0) + p.radius):
                            t.apply_damage(p.damage)
                            hit_any = True
                            break

            if not hit_any:
                alive.append(p)

        self.projectiles = alive

