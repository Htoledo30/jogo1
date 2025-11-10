"""Battle systems module - Formations, terrain, and veterancy.

Extracted from battle.py to improve code organization.
Contains tactical systems: formation calculations, target distribution, veterancy, terrain.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple
import math
from src.logger import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from src.battle import BattleController
    from src.entities import Entity


def calculate_formation_position(battle: 'BattleController', troop_index: int, troop: 'Entity') -> Tuple[float, float]:
    """Calculate target position for troop based on current formation mode.

    Args:
        battle: BattleController instance
        troop_index: Index of the troop in the troops list
        troop: The troop entity

    Returns:
        (target_x, target_y) position tuple
    """
    player_x, player_y = battle.player.pos
    total_troops = len(battle.troops)

    # Get troop type (cavalry, archer, infantry, tank)
    troop_type = getattr(troop, 'troop_type', 'infantry')

    if battle.formation_mode == 0:  # CIRCLE formation
        # All troops in circular formation around player
        angle = (troop_index / max(1, total_troops)) * math.tau
        radius = 80
        target_x = player_x + math.cos(angle) * radius
        target_y = player_y + math.sin(angle) * radius

    elif battle.formation_mode == 1:  # LINE formation
        # Infantry front, Archers back, Cavalry on flanks
        if troop_type == 'cavalry':
            # Cavalry on flanks (left or right)
            side = 1 if troop_index % 2 == 0 else -1
            target_x = player_x + side * 120
            target_y = player_y - 40
        elif troop_type == 'archer':
            # Archers in back line
            spacing = 50
            archer_index = troop_index // 2
            offset_x = (archer_index - total_troops / 4) * spacing
            target_x = player_x + offset_x
            target_y = player_y + 60  # Behind player
        else:  # infantry or tank
            # Infantry front line
            spacing = 60
            offset_x = (troop_index - total_troops / 2) * spacing
            target_x = player_x + offset_x
            target_y = player_y - 60  # In front of player

    elif battle.formation_mode == 2:  # WEDGE formation (V-shape)
        # Cavalry at point, Infantry on sides, Archers in center back
        if troop_type == 'cavalry':
            # Cavalry at the point (front)
            side = 1 if troop_index % 2 == 0 else -1
            target_x = player_x + side * 40
            target_y = player_y - 100
        elif troop_type == 'archer':
            # Archers in center back
            spacing = 40
            archer_index = troop_index // 3
            offset_x = (archer_index - total_troops / 6) * spacing
            target_x = player_x + offset_x
            target_y = player_y + 40
        else:  # infantry or tank
            # Infantry on the sides of the wedge
            side = 1 if troop_index % 2 == 0 else -1
            depth = (troop_index // 2) * 40
            target_x = player_x + side * (60 + depth)
            target_y = player_y - 60 + depth
    else:
        # Fallback: circle
        angle = (troop_index / max(1, total_troops)) * math.tau
        radius = 80
        target_x = player_x + math.cos(angle) * radius
        target_y = player_y + math.sin(angle) * radius

    return (target_x, target_y)


def redistribute_troop_targets(battle: 'BattleController') -> None:
    """Intelligently distribute troops across different enemies.

    Ensures troops don't all attack the same target, improving tactical combat.
    Should be called at battle start and when enemies die.

    Args:
        battle: BattleController instance
    """
    alive_troops = [t for t in battle.troops if t.alive()]
    alive_enemies = [e for e in battle.enemies if e.alive()]

    if not alive_troops or not alive_enemies:
        return

    # Clear old assignments
    battle.troop_target_assignments.clear()

    # Distribute troops evenly across enemies
    # Strategy: Round-robin assignment to spread troops out
    for i, troop in enumerate(alive_troops):
        enemy_index = i % len(alive_enemies)
        assigned_enemy = alive_enemies[enemy_index]
        battle.troop_target_assignments[troop.id] = assigned_enemy.id


def is_on_high_ground(battle: 'BattleController', entity: 'Entity') -> bool:
    """Check if entity is on high ground (hill zone).

    Args:
        battle: BattleController instance
        entity: Entity to check

    Returns:
        True if entity is in hill_zone
    """
    px = int(entity.pos[0])
    py = int(entity.pos[1])

    zones = getattr(battle, 'high_ground_rects', None)
    if zones:
        for rect in zones:
            if rect.collidepoint(px, py):
                return True

    hill = getattr(battle, 'hill_zone', None)
    if hill and hill.width > 0 and hill.height > 0:
        return hill.collidepoint(px, py)
    return False


def check_veterancy_promotions(battle: 'BattleController') -> List['Entity']:
    """Check and process troop promotions based on XP.

    Called when battle ends in victory. Promotes troops that have earned enough XP,
    heals them, and tracks promoted troops for rewards/notifications.

    Args:
        battle: BattleController instance

    Returns:
        List of troops that were promoted this check
    """
    promoted_troops = []

    for troop in battle.troops:
        if troop.stats.xp >= troop.stats.xp_to_next_level:
            troop.stats.level += 1
            troop.stats.xp = 0  # Reset XP for next level
            troop.stats.xp_to_next_level = troop.stats.level * 10

            # Heal on promotion
            troop.stats.hp = troop.stats.hp_max

            # Track promoted troop
            promoted_troops.append(troop)
            logger.info(f"Troop {troop.id} promoted to Tier {troop.stats.level} (XP threshold reached)")

    return promoted_troops


def apply_terrain_damage_modifier(battle: 'BattleController', attacker: 'Entity', defender: 'Entity', base_damage: float) -> float:
    """Apply terrain-based damage modifier (high ground advantage).

    Args:
        battle: BattleController instance
        attacker: Entity performing the attack
        defender: Entity being attacked
        base_damage: Base damage before terrain modifier

    Returns:
        Modified damage value
    """
    attacker_high_ground = is_on_high_ground(battle, attacker)
    defender_high_ground = is_on_high_ground(battle, defender)

    # Attacker on high ground, defender not: +20% damage
    if attacker_high_ground and not defender_high_ground:
        return base_damage * 1.2

    # Defender on high ground, attacker not: -10% damage (harder to hit uphill)
    if defender_high_ground and not attacker_high_ground:
        return base_damage * 0.9

    # Both on same level: no modifier
    return base_damage
