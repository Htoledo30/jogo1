"""Battle AI Enhanced - Advanced enemy AI behaviors and decision-making.

Extracted from battle.py to improve code organization.
Contains target prioritization, behavioral AI state machine, blocking intelligence, and movement.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
import math
from src import entities, vfx

if TYPE_CHECKING:
    from src.battle import BattleController
    from src.entities import Entity

# Constants
ARENA_WIDTH = 1280
ARENA_HEIGHT = 720
ARENA_BORDER = 40


def calculate_target_priority(battle: 'BattleController', enemy: 'Entity') -> Optional['Entity']:
    """Calculate best target for enemy using priority scoring system.

    Scoring factors:
    - HP Factor (40%): Prioritize low HP targets for kills
    - Threat Factor (30%): Prioritize high ATK targets
    - Distance Factor (20%): Slightly prefer closer targets
    - Type Factor (10%): Prioritize player over troops

    Args:
        battle: BattleController instance
        enemy: Enemy entity calculating target

    Returns:
        Best target entity, or None if no valid targets
    """
    targets = [battle.player] + [t for t in battle.troops if t.alive()]
    best_target = None
    best_score = -1

    for target in targets:
        if not target.alive():
            continue

        dist = entities.distance(enemy, target)

        # Calculate priority score (0-100)
        score = 0

        # HP Factor (40%): Prioritize low HP targets for kills
        hp_percent = target.stats.hp / target.stats.hp_max
        score += (1.0 - hp_percent) * 40  # Lower HP = higher score

        # Threat Factor (30%): Prioritize high ATK targets
        threat = target.stats.atk / 20.0  # Normalize (typical ATK 10-40)
        score += min(threat, 1.0) * 30

        # Distance Factor (20%): Slightly prefer closer targets
        max_dist = 400  # Normalize distance
        distance_score = max(0, 1.0 - (dist / max_dist))
        score += distance_score * 20

        # Type Factor (10%): Prioritize player over troops
        if target == battle.player:
            score += 10

        # Select best target
        if score > best_score:
            best_score = score
            best_target = target

    return best_target


def update_blocking_decision(battle: 'BattleController', enemy: 'Entity', dt: float, is_stunned: bool) -> bool:
    """Update enemy blocking decision using intelligent timing system.

    Locks blocking decisions for 1-2 seconds to prevent spammy behavior.
    Considers player attack direction and enemy HP for decision-making.

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        dt: Delta time
        is_stunned: Whether enemy is currently stunned

    Returns:
        True if enemy should block, False otherwise
    """
    if is_stunned:
        return False

    # Update decision timer
    block_timer = battle.enemy_block_decision_timers.get(enemy.id, 0.0)
    block_timer -= dt

    # If timer expired, make a new blocking decision
    if block_timer <= 0.0:
        # Check if player is attacking toward this enemy
        player_attacking = battle.player_attack_duration > 0.0
        close_to_player = entities.distance(enemy, battle.player) < 120

        if player_attacking and close_to_player:
            # Check attack direction (is player attacking toward this enemy?)
            attack_toward_enemy = False
            if battle.player_attack_direction[0] != 0 or battle.player_attack_direction[1] != 0:
                # Calculate direction from player to enemy
                dx_to_enemy = enemy.pos[0] - battle.player.pos[0]
                dy_to_enemy = enemy.pos[1] - battle.player.pos[1]
                dist = math.hypot(dx_to_enemy, dy_to_enemy)
                if dist > 0:
                    dx_to_enemy /= dist
                    dy_to_enemy /= dist
                    # Dot product: check if attack direction aligns with enemy direction
                    dot = (battle.player_attack_direction[0] * dx_to_enemy +
                           battle.player_attack_direction[1] * dy_to_enemy)
                    attack_toward_enemy = dot > 0.5  # 60-degree cone

            # Make blocking decision
            if attack_toward_enemy:
                # Higher chance to block when HP is low
                block_chance = 0.5 if enemy.stats.hp > enemy.stats.hp_max * 0.5 else 0.75
                battle.enemy_block_decisions[enemy.id] = battle.rng.random() < block_chance
            else:
                battle.enemy_block_decisions[enemy.id] = False

            # Lock decision for 1.0-2.0 seconds
            battle.enemy_block_decision_timers[enemy.id] = battle.rng.uniform(1.0, 2.0)
        else:
            battle.enemy_block_decisions[enemy.id] = False
            battle.enemy_block_decision_timers[enemy.id] = battle.rng.uniform(0.3, 0.6)
    else:
        # Update timer
        battle.enemy_block_decision_timers[enemy.id] = block_timer

    # Return locked decision
    return battle.enemy_block_decisions.get(enemy.id, False)


def determine_enemy_state(battle: 'BattleController', enemy: 'Entity', target: Optional['Entity'],
                          should_block: bool) -> str:
    """Determine enemy AI state based on conditions.

    States:
    - BLOCKING: Enemy is blocking player attack
    - CHASING: Default aggressive state (archers strafe to maintain distance)

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        target: Current target entity (can be None)
        should_block: Whether enemy decided to block

    Returns:
        AI state string
    """
    if should_block:
        return "BLOCKING"

    return "CHASING"


def calculate_enemy_movement(battle: 'BattleController', enemy: 'Entity', target: Optional['Entity'],
                             state: str, dt: float) -> Tuple[float, float, float]:
    """Calculate enemy movement direction and speed based on AI state.

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        target: Current target entity (can be None)
        state: Current AI state
        dt: Delta time

    Returns:
        Tuple of (dx, dy, move_speed)
    """
    if not target:
        return (0.0, 0.0, 0.0)

    move_speed = enemy.stats.spd * 0.9
    dx = 0.0
    dy = 0.0

    is_archer = getattr(enemy, 'troop_type', '') == 'archer'

    if state == "CHASING":
        # IMPROVED: Add circling/flanking behavior (40% chance)
        if battle.rng.random() < 0.4:
            # Circle around target instead of direct rush
            dx_base = target.pos[0] - enemy.pos[0]
            dy_base = target.pos[1] - enemy.pos[1]
            # Rotate 90 degrees (perpendicular movement)
            dx = -dy_base
            dy = dx_base
            move_speed *= 0.85  # Slightly slower when circling
        else:
            # Direct chase
            dx = target.pos[0] - enemy.pos[0]
            dy = target.pos[1] - enemy.pos[1]

        # Archers maintain distance without hard fleeing
        if is_archer:
            dist_to_target = entities.distance(enemy, target)
            if dist_to_target < 150:
                dx = enemy.pos[0] - target.pos[0]
                dy = enemy.pos[1] - target.pos[1]
                move_speed *= 0.95
            elif dist_to_target > 220:
                dx = target.pos[0] - enemy.pos[0]
                dy = target.pos[1] - enemy.pos[1]

        # SPACING: Avoid stacking on top of each other (check only nearby enemies for performance)
        nearby_enemies = [e for e in battle.enemies if e.id != enemy.id and e.alive() and entities.distance(enemy, e) < 100]
        # Limit to 5 nearest to avoid O(n²) performance
        nearby_enemies.sort(key=lambda e: entities.distance(enemy, e))
        for other_enemy in nearby_enemies[:5]:
            dist_to_other = entities.distance(enemy, other_enemy)
            if dist_to_other < 50:  # Too close to another enemy
                # Push away from other enemy
                push_dx = enemy.pos[0] - other_enemy.pos[0]
                push_dy = enemy.pos[1] - other_enemy.pos[1]
                push_dist = math.hypot(push_dx, push_dy)
                if push_dist > 0:
                    dx += (push_dx / push_dist) * 100
                    dy += (push_dy / push_dist) * 100

    elif state == "BLOCKING":
        # Stand still or move slowly backwards
        dx = enemy.pos[0] - target.pos[0]
        dy = enemy.pos[1] - target.pos[1]
        move_speed *= 0.2  # Very slow when blocking

    return (dx, dy, move_speed)


def execute_enemy_movement(battle: 'BattleController', enemy: 'Entity', dx: float, dy: float,
                          move_speed: float, dt: float) -> None:
    """Execute enemy movement and clamp to arena boundaries.

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        dx: Movement direction X
        dy: Movement direction Y
        move_speed: Movement speed
        dt: Delta time
    """
    if dx == 0 and dy == 0:
        return

    # Normalize direction
    dist = math.hypot(dx, dy)
    if dist == 0:
        return

    # Dust particles for enemy movement
    battle.dust_timer += dt
    if battle.dust_timer > 0.05:
        vfx.create_dust_cloud(enemy.pos, 1)
        battle.dust_timer = 0.0

    dx /= dist
    dy /= dist
    enemy.pos[0] += dx * move_speed * dt
    enemy.pos[1] += dy * move_speed * dt

    # Clamp to arena
    enemy.pos[0] = max(ARENA_BORDER + enemy.radius,
                      min(ARENA_WIDTH - ARENA_BORDER - enemy.radius, enemy.pos[0]))
    enemy.pos[1] = max(ARENA_BORDER + enemy.radius,
                      min(ARENA_HEIGHT - ARENA_BORDER - enemy.radius, enemy.pos[1]))


def update_enemy_ai(battle: 'BattleController', enemy: 'Entity', dt: float) -> None:
    """Update single enemy AI - complete AI pipeline.

    Handles:
    - Target prioritization
    - Blocking decision intelligence
    - State determination (CHASING, BLOCKING)
    - Movement calculation and execution

    Args:
        battle: BattleController instance
        enemy: Enemy entity to update
        dt: Delta time
    """
    # Check if stunned (from parry)
    is_stunned = battle.enemy_stun_times.get(enemy.id, 0.0) > 0.0

    # Reset blocking state at the start of each frame
    battle.enemy_blocking_states[enemy.id] = False

    # Target prioritization
    target = calculate_target_priority(battle, enemy)

    # Blocking decision intelligence
    should_block = update_blocking_decision(battle, enemy, dt, is_stunned)

    # Determine AI state
    state = determine_enemy_state(battle, enemy, target, should_block)

    # Update blocking state
    battle.enemy_blocking_states[enemy.id] = (state == "BLOCKING")

    # Movement (only if not stunned)
    if not is_stunned and target:
        dx, dy, move_speed = calculate_enemy_movement(battle, enemy, target, state, dt)
        execute_enemy_movement(battle, enemy, dx, dy, move_speed, dt)
