"""
Enemy AI helpers extracted from battle controller to reduce file size and
improve maintainability. Keeps behavior identical to inlined version.
"""

from __future__ import annotations

import math
from typing import Any, Optional, Iterable


def init_enemy_ai_state(ctrl: Any) -> None:
    """Initialize simple enemy AI state on the controller."""
    ctrl.enemy_stamina = {e.id: 100.0 for e in ctrl.enemies}
    ctrl.enemy_decision_lock = {e.id: 0.0 for e in ctrl.enemies}
    ctrl.enemy_targets = {}


def _ai_profile(enemy) -> dict:
    # Try troop_type first (if set), fallback to enemy_type
    troop_type = getattr(enemy, 'troop_type', None)
    if troop_type == 'archer':
        return {"style": "kite", "ideal_min": 100.0, "ideal_max": 140.0, "spd_mult": 1.0}
    elif troop_type == 'tank':
        return {"style": "press", "ideal_min": 30.0, "ideal_max": 60.0, "spd_mult": 0.95}

    # Fallback to enemy_type detection
    et = getattr(enemy, 'enemy_type', '') or ''
    et = et.lower()
    if 'archer' in et or 'bow' in et:
        return {"style": "kite", "ideal_min": 100.0, "ideal_max": 140.0, "spd_mult": 1.0}
    if et in ("phalangite", "hoplite", "maurya_spearman"):
        return {"style": "spear", "ideal_min": 80.0, "ideal_max": 110.0, "spd_mult": 0.95}
    if et == "cataphract":
        return {"style": "press", "ideal_min": 30.0, "ideal_max": 60.0, "spd_mult": 1.1}
    return {"style": "press", "ideal_min": 25.0, "ideal_max": 50.0, "spd_mult": 1.0}


def _score_target(ctrl: Any, enemy, tgt) -> float:
    # Lower is better (distance-weighted with isolation bonus)
    d = _dist(enemy, tgt)
    iso = 0.0
    if hasattr(tgt, 'pos'):
        nearby = sum(1 for ee in ctrl.enemies if ee is not enemy and _dist(ee, tgt) < 120)
        iso = max(0.0, 2 - 0.2 * nearby)
    # Penalize targets currently invulnerable (i-frames)
    invuln_pen = 0.0
    try:
        if getattr(tgt, '_invuln', 0.0) > 0.0:
            invuln_pen = 80.0
    except Exception:
        pass
    return d - 15 * iso + invuln_pen


def _dist(a, b) -> float:
    dx = a.pos[0] - b.pos[0]
    dy = a.pos[1] - b.pos[1]
    return math.hypot(dx, dy)


def update_enemies(ctrl: Any, dt: float) -> None:
    """Update enemy movement/spacing/target selection with simple stamina gating."""
    # Update decision locks and stamina regen
    for e in ctrl.enemies:
        eid = e.id
        ctrl.enemy_decision_lock[eid] = max(0.0, ctrl.enemy_decision_lock.get(eid, 0.0) - dt)
        ctrl.enemy_stamina[eid] = min(100.0, ctrl.enemy_stamina.get(eid, 100.0) + 12.0 * dt)

    # Potential targets: player, player troops, and enemies from opposing team (for AI vs AI)
    potential_targets = [ctrl.player] + [t for t in ctrl.troops if t.alive()]

    for enemy in ctrl.enemies:
        if not enemy.alive():
            continue
        eid = enemy.id
        prof = _ai_profile(enemy)

        # Choose/remember target occasionally
        if ctrl.enemy_decision_lock[eid] <= 0.0 or ctrl.enemy_targets.get(eid) is None:
            best = None
            best_score = 1e9
            # Add cross-team enemies as valid targets (AI vs AI)
            enemy_team = getattr(enemy, 'team', 'A')
            cross_team = [ee for ee in ctrl.enemies if (ee is not enemy) and getattr(ee, 'team', 'A') != enemy_team and ee.alive()]
            for tgt in potential_targets + cross_team:
                s = _score_target(ctrl, enemy, tgt)
                if s < best_score:
                    best_score = s
                    best = tgt
            ctrl.enemy_targets[eid] = best
            ctrl.enemy_decision_lock[eid] = 0.35

        target = ctrl.enemy_targets.get(eid, ctrl.player)
        dx = target.pos[0] - enemy.pos[0]
        dy = target.pos[1] - enemy.pos[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist

        ideal_min = prof["ideal_min"]
        ideal_max = prof["ideal_max"]
        style = prof["style"]
        spd = enemy.stats.spd * prof["spd_mult"]

        move_ok = ctrl.enemy_stamina[eid] > 10.0

        if style in ("kite", "spear"):
            if dist < ideal_min and move_ok:
                enemy.pos[0] -= dx * spd * dt
                enemy.pos[1] -= dy * spd * dt
                ctrl.enemy_stamina[eid] = max(0.0, ctrl.enemy_stamina[eid] - 6.0 * dt)
            elif dist > ideal_max and move_ok:
                enemy.pos[0] += dx * spd * 0.6 * dt
                enemy.pos[1] += dy * spd * 0.6 * dt
                ctrl.enemy_stamina[eid] = max(0.0, ctrl.enemy_stamina[eid] - 4.0 * dt)
            # Ranged fire for archers (kite) when in band
            if style == "kite" and hasattr(ctrl, 'projectiles') and ctrl.projectiles is not None and ideal_min <= dist <= 280.0:
                cd = ctrl.enemy_attack_cooldowns.get(eid, 0.0)
                if cd <= 0.0 and dist > 0:
                    # Compute predictive aim and basic line-of-fire checks
                    proj_speed = 340.0
                    damage = max(5.0, float(getattr(enemy.stats, 'atk', 8)))

                    dirx, diry = _compute_lead_direction(
                        ctrl,
                        (enemy.pos[0], enemy.pos[1]),
                        target,
                        proj_speed,
                        default_dir=(dx, dy),
                    )

                    # Skip if friendly blocking line of fire
                    if _friendly_blocks_line(
                        (enemy.pos[0], enemy.pos[1]),
                        (target.pos[0], target.pos[1]),
                        allies=(ally for ally in ctrl.enemies if ally is not enemy),
                    ):
                        pass  # hold fire this frame
                    else:
                        ctrl.projectiles.spawn(enemy.pos[0], enemy.pos[1], (dirx, diry), proj_speed, damage, team="enemy")
                        ctrl.enemy_attack_cooldowns[eid] = 1.1
        else:  # press
            # Limit simultaneous engagers around player to reduce clumping
            engaging_player = (target is ctrl.player)
            too_crowded = False
            if engaging_player and dist < 120:
                try:
                    close = 0
                    for ee in ctrl.enemies:
                        if ee is enemy or not ee.alive():
                            continue
                        if _dist(ee, ctrl.player) < 100:
                            close += 1
                    too_crowded = close >= 2
                except Exception:
                    too_crowded = False

            if too_crowded and move_ok:
                # Strafe around the player instead of pushing in
                # Perpendicular to (dx,dy)
                sx, sy = -dy, dx
                enemy.pos[0] += sx * spd * 0.5 * dt
                enemy.pos[1] += sy * spd * 0.5 * dt
                ctrl.enemy_stamina[eid] = max(0.0, ctrl.enemy_stamina[eid] - 3.0 * dt)
            else:
                if dist > ideal_max and move_ok:
                    enemy.pos[0] += dx * spd * dt
                    enemy.pos[1] += dy * spd * dt
                    ctrl.enemy_stamina[eid] = max(0.0, ctrl.enemy_stamina[eid] - 5.0 * dt)
                elif dist < ideal_min and move_ok:
                    enemy.pos[0] -= dx * spd * 0.4 * dt
                    enemy.pos[1] -= dy * spd * 0.4 * dt
                    ctrl.enemy_stamina[eid] = max(0.0, ctrl.enemy_stamina[eid] - 3.0 * dt)

        # Clamp to arena
        enemy.pos[0] = max(ctrl.ARENA_BORDER + enemy.radius, min(ctrl.ARENA_WIDTH - ctrl.ARENA_BORDER - enemy.radius, enemy.pos[0]))
        enemy.pos[1] = max(ctrl.ARENA_BORDER + enemy.radius, min(ctrl.ARENA_HEIGHT - ctrl.ARENA_BORDER - enemy.radius, enemy.pos[1]))

        # Arena LOD: throttle far enemies' updates every other frame
        if _dist(ctrl.player, enemy) > 650 and getattr(ctrl, '_frame_toggle', False):
            continue


def _compute_lead_direction(ctrl: Any,
                            shooter_xy: tuple[float, float],
                            target: Any,
                            proj_speed: float,
                            default_dir: tuple[float, float]) -> tuple[float, float]:
    """Return a unit vector direction with simple target leading.

    Uses ctrl.prev_positions to estimate target velocity and solves a
    quadratic intercept. Falls back to default_dir on failure.
    """
    sx, sy = shooter_xy
    tx, ty = float(target.pos[0]), float(target.pos[1])
    r_x = tx - sx
    r_y = ty - sy

    # Estimate target velocity from previous frame
    prev = ctrl.prev_positions.get(target.id) if hasattr(ctrl, 'prev_positions') else None
    if prev is None:
        dx, dy = default_dir
        length = math.hypot(dx, dy) or 1.0
        return dx / length, dy / length

    # Use last frame dt if available; else approximate with current dt or 1/60
    dt_est = getattr(ctrl, '_last_dt', None)
    if not dt_est or dt_est <= 0:
        # Best effort: assume ~60 FPS if we don't have a stored dt
        dt_est = 1.0 / 60.0
    vx = (tx - prev[0]) / max(1e-3, dt_est)
    vy = (ty - prev[1]) / max(1e-3, dt_est)

    # Solve (v·v - s^2) t^2 + 2 (r·v) t + r·r = 0 for t >= 0
    rr = r_x * r_x + r_y * r_y
    rv = r_x * vx + r_y * vy
    vv = vx * vx + vy * vy
    s2 = proj_speed * proj_speed
    a = vv - s2
    b = 2.0 * rv
    c = rr

    t_impact: Optional[float] = None
    if abs(a) < 1e-6:
        # Linear: s ~= |v|, fallback t = -c/b if b < 0
        if abs(b) > 1e-6:
            t = -c / b
            if t > 0:
                t_impact = t
    else:
        disc = b * b - 4.0 * a * c
        if disc >= 0.0:
            sqrt_disc = math.sqrt(disc)
            t1 = (-b - sqrt_disc) / (2.0 * a)
            t2 = (-b + sqrt_disc) / (2.0 * a)
            # Choose smallest positive time
            candidates = [t for t in (t1, t2) if t > 0]
            if candidates:
                t_impact = min(candidates)

    if t_impact is None:
        dx, dy = default_dir
        length = math.hypot(dx, dy) or 1.0
        return dx / length, dy / length

    # Clamp prediction horizon to avoid extreme leads
    t_impact = max(0.05, min(1.2, t_impact))
    aim_x = r_x + vx * t_impact
    aim_y = r_y + vy * t_impact
    length = math.hypot(aim_x, aim_y) or 1.0
    return aim_x / length, aim_y / length


def _friendly_blocks_line(shooter_xy: tuple[float, float],
                          target_xy: tuple[float, float],
                          allies: Iterable[Any],
                          cone_cos: float = math.cos(math.radians(15)),
                          pad: float = 6.0) -> bool:
    """Basic line-of-fire occlusion by allies.

    Checks if any ally (excluding the intended target) sits close to the ray
    from shooter to target with smaller range than the target.
    """
    sx, sy = shooter_xy
    tx, ty = target_xy
    to_t_x = tx - sx
    to_t_y = ty - sy
    dist_t = math.hypot(to_t_x, to_t_y)
    if dist_t <= 1e-3:
        return False
    dirx = to_t_x / dist_t
    diry = to_t_y / dist_t

    for ally in allies:
        if not getattr(ally, 'alive', lambda: True)():
            continue
        ax = ally.pos[0] - sx
        ay = ally.pos[1] - sy
        proj = ax * dirx + ay * diry  # distance along the ray
        if proj <= 0 or proj >= dist_t:
            continue
        # Lateral distance from ray
        lx = ax - proj * dirx
        ly = ay - proj * diry
        lateral = math.hypot(lx, ly)
        if lateral <= getattr(ally, 'radius', 10.0) + pad:
            return True
    return False
