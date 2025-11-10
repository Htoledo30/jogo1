"""Battle combat module - All attack and damage logic.

Extracted from battle.py to improve code organization.
Contains player attacks, troop attacks, enemy attacks, and damage calculations.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import math
from src import entities, vfx, battle_effects
from src.logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.battle import BattleController


def process_player_attack(battle: 'BattleController', input_state: dict, dt: float) -> None:
    """Process player attack input and initiate attack.

    Handles attack type variation (slash/thrust/overhead), direction calculation,
    cooldowns, stamina consumption, and combo system.

    Args:
        battle: BattleController instance
        input_state: Input state dictionary with attack and mouse_pos
        dt: Delta time
    """
    if input_state.get("attack") and battle.player_attack_cooldown <= 0.0 and battle.player_stamina > 0:
        # Determine attack direction from player to mouse
        mouse_pos = input_state.get("mouse_pos", (battle.player.pos[0], battle.player.pos[1] + 50))
        dx_mouse = mouse_pos[0] - battle.player.pos[0]
        dy_mouse = mouse_pos[1] - battle.player.pos[1]

        # Normalize direction
        dist_mouse = math.hypot(dx_mouse, dy_mouse)
        if dist_mouse > 0:
            attack_vx = dx_mouse / dist_mouse
            attack_vy = dy_mouse / dist_mouse
        else:
            attack_vx = 0
            attack_vy = 1  # Default downward

        # ATTACK TYPE VARIATION based on combo count
        if battle.player_combo_count == 0:
            battle.player_attack_type = "slash"  # First hit: horizontal slash
        elif battle.player_combo_count == 1:
            battle.player_attack_type = "thrust"  # Second hit: thrust
        else:
            battle.player_attack_type = "overhead"  # Third hit: overhead smash

        battle.player_attack_direction = [attack_vx, attack_vy]

        # Use weapon stats to drive cooldown and stamina
        weapon = battle.player.equipment.get_weapon()
        base_cd = max(0.3, float(getattr(weapon, "cooldown", 0.5)))
        if battle.player_attack_type == "overhead":
            battle.player_attack_cooldown = base_cd + 0.3
        elif battle.player_attack_type == "thrust":
            battle.player_attack_cooldown = max(0.25, base_cd - 0.1)
        else:
            battle.player_attack_cooldown = base_cd
        # Apply AGI attack speed bonus
        try:
            speed_bonus = float(getattr(battle.player.stats, 'attack_speed_bonus', 0.0))
            battle.player_attack_cooldown = max(0.2, battle.player_attack_cooldown * (1.0 + speed_bonus))
        except Exception:
            pass

        battle.player_attack_duration = 0.2
        stam_cost = max(8.0, float(getattr(weapon, "stamina_cost", 15)))
        battle.player_stamina = max(0.0, battle.player_stamina - stam_cost)

        # Reset per-swing hit tracking
        battle.player_hit_enemies.clear()

        # Create attack visual effect
        attack_angle = math.atan2(attack_vy, attack_vx)
        if battle.player_attack_type == "slash":
            vfx.create_slash_effect(battle.player.pos, attack_angle, "horizontal")
        elif battle.player_attack_type == "thrust":
            vfx.create_slash_effect(battle.player.pos, attack_angle, "thrust")
        else:  # overhead
            vfx.create_slash_effect(battle.player.pos, attack_angle, "vertical")

        # Combo system
        battle.player_combo_count = min(3, battle.player_combo_count + 1)
        battle.player_combo_timer = 1.0  # 1 second window for next attack


def apply_player_attack_damage(battle: 'BattleController') -> None:
    """Apply damage from active player attack to enemies in range.

    Handles blocking, combo multipliers, terrain advantage, varied particle effects,
    and hit tracking to prevent multi-hits.

    Args:
        battle: BattleController instance
    """
    if battle.player_attack_duration <= 0.0:
        return

    # Reach depends on equipped weapon range
    weapon = battle.player.equipment.get_weapon()
    w_range = float(getattr(weapon, "range", 60.0))
    attack_range = battle.player.radius + max(30.0, min(w_range, 110.0))

    combo_mult = battle._combo_multiplier()

    for enemy in battle.enemies:
        if not enemy.alive():
            continue

        dist = entities.distance(battle.player, enemy)
        if dist > attack_range:
            continue

        # Skip if already hit this swing
        if enemy.id in battle.player_hit_enemies:
            continue

        # Check if enemy is blocking
        is_enemy_blocking = battle.enemy_blocking_states.get(enemy.id, False)

        if is_enemy_blocking:
            # BLOCKED ATTACK: Sparks, no damage, no hit pause
            attack_angle = math.atan2(battle.player_attack_direction[1], battle.player_attack_direction[0])
            vfx.create_block_spark(enemy.pos, 15, attack_angle + math.pi)  # Sparks fly back
            battle._add_damage_number(enemy.pos[0], enemy.pos[1], 0, (200, 200, 255))  # Shows "PARRY!"
            battle._add_hit_flash(enemy.pos[0], enemy.pos[1], (150, 200, 255))
            battle.screen_shake = 0.2
            battle.player_hit_enemies.add(enemy.id)
            continue

        # Calculate base damage
        damage = (battle.player.stats.atk * weapon.damage) * combo_mult

        # DAMAGE TYPE EFFECTIVENESS: Apply multiplier based on weapon type vs armor material
        from src.constants_battle import DAMAGE_TYPE_EFFECTIVENESS
        weapon_damage_type = getattr(weapon, 'damage_type', 'slashing')
        enemy_armor_material = enemy.equipment.get_primary_material() if enemy.equipment else "leather"
        effectiveness = DAMAGE_TYPE_EFFECTIVENESS.get(weapon_damage_type, {}).get(enemy_armor_material, 1.0)
        damage *= effectiveness

        # Track if damage was super effective or resisted (for visual feedback)
        is_effective = effectiveness >= 1.10
        is_resisted = effectiveness <= 0.90

        # STAGGER BONUS: +25% damage to staggered enemies
        from src.constants_battle import STAGGER_DAMAGE_BONUS
        is_enemy_staggered = getattr(enemy.stats, 'is_staggered', False)
        if is_enemy_staggered:
            damage *= STAGGER_DAMAGE_BONUS

        # Terrain advantage: +20% damage if player on high ground
        if battle._is_on_high_ground(battle.player):
            damage *= 1.2

        # CRITICAL HIT SYSTEM (based on SKL attribute)
        import random
        is_crit = random.random() < battle.player.stats.crit_chance
        if is_crit:
            damage *= battle.player.stats.crit_damage
            # Critical hit visual will be added below

        hp_before = enemy.stats.hp
        enemy.apply_damage(damage)

        # POISE SYSTEM: Apply poise damage based on attack type
        from src.constants_battle import (
            POISE_DAMAGE_LIGHT_ATTACK, POISE_DAMAGE_HEAVY_ATTACK,
            STAGGER_DURATION
        )
        is_heavy = battle.current_attack_type == "heavy"
        poise_damage = POISE_DAMAGE_HEAVY_ATTACK if is_heavy else POISE_DAMAGE_LIGHT_ATTACK

        # Apply poise damage
        if hasattr(enemy.stats, 'poise'):
            enemy.stats.poise = max(0, enemy.stats.poise - poise_damage)

            # Check for stagger
            if enemy.stats.poise <= 0 and not enemy.stats.is_staggered:
                enemy.stats.is_staggered = True
                enemy.stats.stagger_timer = STAGGER_DURATION
                # Visual feedback for stagger (will be added below)

        # Skip if no actual damage applied (i-frames)
        if enemy.stats.hp >= hp_before:
            continue

        battle._register_combo_hit()
        # Mark as hit
        battle.player_hit_enemies.add(enemy.id)

        # VARIED PARTICLES based on attack type
        attack_angle = math.atan2(battle.player_attack_direction[1], battle.player_attack_direction[0])
        is_heavy = battle.current_attack_type == "heavy"

        if is_heavy:
            # Heavy attack: More particles, bigger shake
            vfx.create_blood_splatter(enemy.pos, 25, attack_angle)
            vfx.create_impact_dust(enemy.pos, 15, attack_angle)
            battle.screen_shake = 0.8
        elif battle.player_attack_type == "slash":
            vfx.create_blood_splatter(enemy.pos, 12, attack_angle)
            vfx.create_impact_dust(enemy.pos, 5, attack_angle)
        elif battle.player_attack_type == "thrust":
            vfx.create_blood_splatter(enemy.pos, 15, attack_angle)
            battle.screen_shake = 0.3
        else:  # overhead
            vfx.create_blood_splatter(enemy.pos, 20, attack_angle)
            vfx.create_impact_dust(enemy.pos, 10, attack_angle)
            battle.screen_shake = 0.6

        # STAGGER VISUAL: Show "!" icon above enemy head
        if is_enemy_staggered:
            # Add visual indicator (could be implemented in battle_rendering)
            pass

        # Add damage number with color based on effectiveness and crits
        if is_crit:
            color = (255, 215, 0)  # Gold for critical hits
            vfx.create_levelup_glow(enemy.pos)  # Golden particles on crit
            battle.screen_shake = max(battle.screen_shake, 0.5)  # Extra shake
        elif is_effective:
            color = (100, 255, 100)  # Green for super effective
        elif is_resisted:
            color = (255, 150, 50)  # Orange for resisted
        else:
            color = (255, 255, 100) if battle.player_attack_type != "overhead" else (255, 180, 50)

        battle_effects.add_damage_number(battle, enemy.pos[0], enemy.pos[1], int(damage), color)

        if not enemy.alive():
            # Death effects
            battle_effects.add_hit_flash(battle, enemy.pos[0], enemy.pos[1], (255, 200, 0))
            battle_effects.shake(battle, 0.8)
            battle_effects.add_hit_pause(battle, 0.15)
            vfx.create_blood_splatter(enemy.pos, 30, attack_angle)
        else:
            battle_effects.add_hit_flash(battle, enemy.pos[0], enemy.pos[1], (255, 100, 100))
            battle_effects.add_hit_pause(battle, 0.05 if battle.player_attack_type != "overhead" else 0.1)


def process_troop_attacks(battle: 'BattleController') -> None:
    """Process troop melee attacks against enemies.

    Handles damage application, terrain advantage, XP gain on kills.
    Note: Archer troops use projectiles (handled elsewhere).

    Args:
        battle: BattleController instance
    """
    for troop in battle.troops:
        if not troop.alive():
            continue

        troop_type = getattr(troop, 'troop_type', 'warrior')
        if troop_type == 'archer':
            continue  # Archers handled by projectiles

        duration = battle.troop_attack_durations.get(troop.id, 0.0)
        if duration <= 0.0:
            continue

        # Melee range attack processing
        attack_range = troop.radius + 20

        for enemy in battle.enemies:
            if not enemy.alive():
                continue

            dist = entities.distance(troop, enemy)
            if dist > attack_range:
                continue

            damage = troop.stats.atk

            # Terrain advantage: +20% damage if troop on high ground
            if battle._is_on_high_ground(troop):
                damage *= 1.2

            enemy.apply_damage(damage)
            battle_effects.add_damage_number(battle, enemy.pos[0], enemy.pos[1], int(damage), (150, 200, 255))

            if not enemy.alive():
                battle_effects.add_hit_flash(battle, enemy.pos[0], enemy.pos[1], (255, 200, 0))
                # Veterancy: Grant XP to troop for kill
                xp_gained = enemy.stats.level * 2
                troop.stats.xp += xp_gained
                logger.debug(f"Troop {troop.id} gained {xp_gained} XP (enemy level {enemy.stats.level})")
            else:
                battle_effects.add_hit_flash(battle, enemy.pos[0], enemy.pos[1], (255, 150, 150))

            # Reset duration
            battle.troop_attack_durations[troop.id] = 0.0
            vfx.create_blood_splatter(enemy.pos, 5)
            break  # One enemy per attack


def process_enemy_attack_initiation(battle: 'BattleController', enemy, target, enemy_state: str,
                                    is_stunned: bool, min_dist: float) -> None:
    """Initiate enemy attack if conditions are met.

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        target: Target entity
        enemy_state: Current AI state
        is_stunned: Whether enemy is stunned
        min_dist: Distance to target
    """
    if is_stunned or not target or enemy_state == "BLOCKING":
        return

    is_archer = getattr(enemy, 'troop_type', '') == 'archer'
    kiting_distance = 180
    attack_range = kiting_distance if is_archer else enemy.radius + target.radius + 15

    if min_dist <= attack_range:
        if battle.enemy_attack_cooldowns.get(enemy.id, 0.0) <= 0.0:
            battle.enemy_attack_cooldowns[enemy.id] = battle.rng.uniform(1.0, 1.4)
            battle.enemy_attack_durations[enemy.id] = 0.3


def apply_enemy_attack_damage(battle: 'BattleController', enemy, target, min_dist: float,
                              attack_range: float) -> None:
    """Apply damage from enemy attack to target.

    Handles blocking mechanics (player parry, regular block), terrain disadvantage.

    Args:
        battle: BattleController instance
        enemy: Enemy entity
        target: Target entity
        min_dist: Distance to target
        attack_range: Attack range
    """
    duration = battle.enemy_attack_durations.get(enemy.id, 0.0)
    if duration <= 0.0 or min_dist > attack_range or not target:
        return

    damage = enemy.stats.atk

    # Terrain disadvantage: -10% damage if defender on high ground
    if battle._is_on_high_ground(target):
        damage *= 0.9

    # Check if target is player (for blocking mechanics)
    is_player_target = (target.id == battle.player.id)

    # Blocking mechanics (only for player)
    if is_player_target and battle.player_blocking:
        # Perfect Parry: Block pressed within parry window
        parry_window = float(getattr(battle.player.stats, 'parry_window', 0.2))
        if battle.player_block_time < parry_window:
            # Perfect parry! No damage, stun enemy
            damage = 0
            battle.enemy_stun_times[enemy.id] = 1.5
            battle._add_hit_flash(target.pos[0], target.pos[1], (100, 200, 255))
            battle._add_damage_number(target.pos[0], target.pos[1] - 30, 0, (100, 255, 255))
            battle.screen_shake = 0.1
        else:
            # Regular block: reduction based on player's block_power
            block_reduction = float(getattr(battle.player.stats, 'block_power', 0.3))
            damage *= (1.0 - block_reduction)
            battle._add_hit_flash(target.pos[0], target.pos[1], (150, 150, 200))
            vfx.create_block_spark(target.pos, 15)
            battle._add_damage_number(target.pos[0], target.pos[1] - 30, int(damage), (200, 200, 255))
            battle.screen_shake = 0.15
    elif not is_player_target and battle.enemy_blocking_states.get(target.id, False):
        # Troop blocking
        damage *= 0.3
        vfx.create_block_spark(target.pos, 10)
        battle._add_hit_flash(target.pos[0], target.pos[1], (150, 150, 150))
    else:
        # No block: full damage
        battle._add_damage_number(target.pos[0], target.pos[1] - 30, int(damage), (255, 100, 100))
        if is_player_target:
            if not battle.player.alive():
                battle._add_hit_flash(target.pos[0], target.pos[1], (200, 200, 255))
                battle.screen_shake = 0.8
            else:
                battle._add_hit_flash(target.pos[0], target.pos[1], (255, 150, 150))
                battle.screen_shake = 0.3
        else:
            battle._add_hit_flash(target.pos[0], target.pos[1], (255, 150, 150))

    vfx.create_blood_splatter(target.pos, 8)
    target.apply_damage(damage)
    if is_player_target and damage > 0:
        battle._reset_combo_chain()

    # Reset duration and block timer
    battle.enemy_attack_durations[enemy.id] = 0.0
    if is_player_target:
        battle.player_block_time = 0.0
