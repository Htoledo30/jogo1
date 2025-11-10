"""
Troop AI helpers extracted from battle controller.
Currently placeholder for future extraction; safe no-op to be called from controller.
"""

from __future__ import annotations

from typing import Any, Optional, Iterable
import math


def update_troops(ctrl: Any, dt: float) -> None:
    """Troop AI: follow/engage + ranged attacks for archers.

    - Formation follow when far from player
    - Engage nearest (or assigned) enemy
    - Archers maintain distance and shoot projectiles
    - Melee rush and hit when in range
    - Bodyguard when player low HP
    """

    def nearest_enemy_to(troop) -> Optional[Any]:
        best = None
        best_d = 1e9
        for e in ctrl.enemies:
            if e.alive():
                d = math.hypot(e.pos[0] - troop.pos[0], e.pos[1] - troop.pos[1])
                if d < best_d:
                    best_d = d
                    best = e
        return best

    for troop in ctrl.troops:
        if not troop.alive():
            continue

        # Follow player (stay within ~80 units) or engage
        dx_player = ctrl.player.pos[0] - troop.pos[0]
        dy_player = ctrl.player.pos[1] - troop.pos[1]
        dist_to_player = math.hypot(dx_player, dy_player)

        # Assigned target or nearest (respect FOCUS order)
        assigned_enemy_id = ctrl.troop_target_assignments.get(troop.id)
        nearest_enemy = None
        min_dist = float('inf')
        # If FOCUS, force all troops to target focus enemy if alive
        if getattr(ctrl, 'troop_order', 'FOLLOW') == 'FOCUS' and getattr(ctrl, 'focus_target_id', None):
            for enemy in ctrl.enemies:
                if enemy.alive() and enemy.id == ctrl.focus_target_id:
                    nearest_enemy = enemy
                    min_dist = math.hypot(enemy.pos[0] - troop.pos[0], enemy.pos[1] - troop.pos[1])
                    ctrl.troop_target_assignments[troop.id] = enemy.id
                    break
        if assigned_enemy_id:
            for enemy in ctrl.enemies:
                if enemy.alive() and enemy.id == assigned_enemy_id:
                    nearest_enemy = enemy
                    min_dist = math.hypot(enemy.pos[0] - troop.pos[0], enemy.pos[1] - troop.pos[1])
                    break
        if nearest_enemy is None or not nearest_enemy.alive():
            from src import battle_systems
            battle_systems.redistribute_troop_targets(ctrl)
            assigned_enemy_id = ctrl.troop_target_assignments.get(troop.id)
            if assigned_enemy_id:
                for enemy in ctrl.enemies:
                    if enemy.alive() and enemy.id == assigned_enemy_id:
                        nearest_enemy = enemy
                        min_dist = math.hypot(enemy.pos[0] - troop.pos[0], enemy.pos[1] - troop.pos[1])
                        break

        troop_type = getattr(troop, 'troop_type', 'warrior')
        is_archer = troop_type == 'archer'

        engaged = False
        if nearest_enemy and min_dist < 150:
            dx = nearest_enemy.pos[0] - troop.pos[0]
            dy = nearest_enemy.pos[1] - troop.pos[1]
            dist = math.hypot(dx, dy)

            if is_archer:
                # Maintain distance band and fire projectiles when aligned
                min_range, max_range = 90.0, 150.0
                # Modify behavior based on order
                order = getattr(ctrl, 'troop_order', 'FOLLOW')
                speed_boost = 1.0
                if order == 'CHARGE':
                    speed_boost = 1.2
                    min_range = max(70.0, min_range - 10)
                if order == 'HOLD':
                    min_range = min_range + 10
                if dist < min_range and dist > 0:
                    dx /= dist; dy /= dist
                    speed = troop.stats.spd * 1.1 * speed_boost
                    troop.pos[0] -= dx * speed * dt
                    troop.pos[1] -= dy * speed * dt
                elif dist > max_range and dist > 0:
                    dx /= dist; dy /= dist
                    speed = troop.stats.spd * 0.6 * speed_boost
                    troop.pos[0] += dx * speed * dt
                    troop.pos[1] += dy * speed * dt

                # Fire projectile if in band
                if hasattr(ctrl, 'projectiles') and ctrl.projectiles is not None and min_range <= dist <= 300.0:
                    cd = ctrl.troop_attack_cooldowns.get(troop.id, 0.0)
                    if cd <= 0.0 and dist > 0:
                        default_dirx = dx / dist; default_diry = dy / dist
                        proj_speed = 360.0
                        damage = max(5.0, float(getattr(troop.stats, 'atk', 8)))

                        dirx, diry = _compute_lead_direction(
                            ctrl,
                            (troop.pos[0], troop.pos[1]),
                            nearest_enemy,
                            proj_speed,
                            default_dir=(default_dirx, default_diry),
                        )

                        # Skip if friendlies (troops + player) block the shot
                        if _friendly_blocks_line(
                            (troop.pos[0], troop.pos[1]),
                            (nearest_enemy.pos[0], nearest_enemy.pos[1]),
                            allies=[ctrl.player, *[fr for fr in ctrl.troops if fr is not troop]],
                        ):
                            pass
                        else:
                            ctrl.projectiles.spawn(troop.pos[0], troop.pos[1], (dirx, diry), proj_speed, damage, team="ally")
                            ctrl.troop_attack_cooldowns[troop.id] = 1.0
                            ctrl.troop_attack_durations[troop.id] = 0.25
                engaged = True
            else:
                # Melee rush
                if dist > 0:
                    dx /= dist; dy /= dist
                    speed = troop.stats.spd * (1.2 if getattr(ctrl, 'troop_order', 'FOLLOW') == 'CHARGE' else 1.0)
                    troop.pos[0] += dx * speed * dt
                    troop.pos[1] += dy * speed * dt

                    # MELEE ATTACK: Initiate attack when in range
                    attack_range = troop.radius + nearest_enemy.radius + 20
                    if dist <= attack_range:
                        cd = ctrl.troop_attack_cooldowns.get(troop.id, 0.0)
                        if cd <= 0.0:
                            ctrl.troop_attack_cooldowns[troop.id] = 1.2
                            ctrl.troop_attack_durations[troop.id] = 0.3
                engaged = True

        # HOLD/DEFEND tighten formation around the player; FOLLOW default
        hold_radius = 80 if getattr(ctrl, 'troop_order', 'FOLLOW') != 'DEFEND' else 50
        if getattr(ctrl, 'troop_order', 'FOLLOW') == 'HOLD':
            # Stay near formation; engage only when very close
            if nearest_enemy and min_dist > 120:
                engaged = False
        if not engaged and dist_to_player > hold_radius:
            # Formation follow
            troop_index = ctrl.troops.index(troop)
            from src import battle_systems
            target_x, target_y = battle_systems.calculate_formation_position(ctrl, troop_index, troop)
            dx_form = target_x - troop.pos[0]
            dy_form = target_y - troop.pos[1]
            dist_form = math.hypot(dx_form, dy_form)
            if dist_form > 10:
                dx_form /= dist_form; dy_form /= dist_form
                speed = troop.stats.spd * (0.9 if getattr(ctrl, 'troop_order', 'FOLLOW') != 'CHARGE' else 1.05)
                troop.pos[0] += dx_form * speed * dt
                troop.pos[1] += dy_form * speed * dt

        # Clamp to arena
        troop.pos[0] = max(ctrl.ARENA_BORDER + troop.radius,
                           min(ctrl.ARENA_WIDTH - ctrl.ARENA_BORDER - troop.radius, troop.pos[0]))
        troop.pos[1] = max(ctrl.ARENA_BORDER + troop.radius,
                           min(ctrl.ARENA_HEIGHT - ctrl.ARENA_BORDER - troop.radius, troop.pos[1]))

        # Bodyguard: if player low HP and close, reprioritize threat
        if ctrl.player.stats.hp < ctrl.player.stats.hp_max * 0.35 and dist_to_player < 150:
            player_threat = nearest_enemy_to(ctrl.player)
            if player_threat and player_threat.alive():
                ctrl.troop_target_assignments[troop.id] = player_threat.id


def _compute_lead_direction(ctrl: Any,
                            shooter_xy: tuple[float, float],
                            target: Any,
                            proj_speed: float,
                            default_dir: tuple[float, float]) -> tuple[float, float]:
    sx, sy = shooter_xy
    tx, ty = float(target.pos[0]), float(target.pos[1])
    r_x = tx - sx
    r_y = ty - sy

    prev = ctrl.prev_positions.get(target.id) if hasattr(ctrl, 'prev_positions') else None
    if prev is None:
        dx, dy = default_dir
        length = math.hypot(dx, dy) or 1.0
        return dx / length, dy / length

    dt_est = getattr(ctrl, '_last_dt', None)
    if not dt_est or dt_est <= 0:
        dt_est = 1.0 / 60.0
    vx = (tx - prev[0]) / max(1e-3, dt_est)
    vy = (ty - prev[1]) / max(1e-3, dt_est)

    rr = r_x * r_x + r_y * r_y
    rv = r_x * vx + r_y * vy
    vv = vx * vx + vy * vy
    s2 = proj_speed * proj_speed
    a = vv - s2
    b = 2.0 * rv
    c = rr

    t_impact: Optional[float] = None
    if abs(a) < 1e-6:
        if abs(b) > 1e-6:
            t = -c / b
            if t > 0:
                t_impact = t
    else:
        disc = b * b - 4.0 * a * c
        if disc >= 0:
            sdisc = math.sqrt(disc)
            t1 = (-b - sdisc) / (2.0 * a)
            t2 = (-b + sdisc) / (2.0 * a)
            cand = [t for t in (t1, t2) if t > 0]
            if cand:
                t_impact = min(cand)

    if t_impact is None:
        dx, dy = default_dir
        L = math.hypot(dx, dy) or 1.0
        return dx / L, dy / L

    t_impact = max(0.05, min(1.2, t_impact))
    aim_x = r_x + vx * t_impact
    aim_y = r_y + vy * t_impact
    L = math.hypot(aim_x, aim_y) or 1.0
    return aim_x / L, aim_y / L


def _friendly_blocks_line(shooter_xy: tuple[float, float],
                          target_xy: tuple[float, float],
                          allies: Iterable[Any],
                          pad: float = 6.0) -> bool:
    sx, sy = shooter_xy
    tx, ty = target_xy
    vx = tx - sx
    vy = ty - sy
    dist_t = math.hypot(vx, vy)
    if dist_t <= 1e-3:
        return False
    dirx = vx / dist_t
    diry = vy / dist_t
    for ally in allies:
        if not getattr(ally, 'alive', lambda: True)():
            continue
        ax = ally.pos[0] - sx
        ay = ally.pos[1] - sy
        proj = ax * dirx + ay * diry
        if proj <= 0 or proj >= dist_t:
            continue
        lx = ax - proj * dirx
        ly = ay - proj * diry
        lateral = math.hypot(lx, ly)
        if lateral <= getattr(ally, 'radius', 10.0) + pad:
            return True
    return False
