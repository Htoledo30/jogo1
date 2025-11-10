"""Attribute system - Calculate derived stats from primary attributes.

This module handles the progression system where primary attributes (STR, AGI, VIT, CHA, SKL)
determine derived combat stats (damage, crit, defense, etc).

Formulas are balanced based on feedback to prevent exploits and maintain gameplay balance.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.entities import Entity
    from src.equipment import Weapon


def calculate_derived_stats(player: Entity) -> None:
    """Recalculate all derived stats from primary attributes.

    This function should be called:
    - After leveling up
    - After allocating attribute points
    - When loading a save
    - When equipping items that modify attributes

    All formulas include caps to prevent exploits.
    """
    stats = player.stats

    STR = stats.strength
    AGI = stats.agility
    VIT = stats.vitality
    CHA = stats.charisma
    SKL = stats.skill

    # === CORE STATS ===

    # HP Max = 100 base + (VIT * 8) + (STR * 2)
    # VIT is primary, STR gives small bonus
    stats.hp_max = 100 + (VIT * 8) + (STR * 2)

    # ATK = 10 base + (STR * 2) + (SKL * 0.5)
    # STR is primary damage stat, SKL adds precision
    stats.atk = 10 + (STR * 2) + (SKL * 0.5)

    # SPD = 180 base + (AGI * 2)
    # BALANCED: Reduced from +3 to +2 to prevent excessive speed
    stats.spd = 180 + (AGI * 2)

    # Stamina Max = 100 + (VIT * 2) + (AGI * 1)
    stats.stamina_max = 100 + (VIT * 2) + (AGI * 1)

    # === COMBAT MODIFIERS (with caps) ===

    # Crit Chance = 5% base + (SKL * 0.5%)  [NERFED from 1%]
    # CAP: 45% to prevent crit fishing builds from being OP
    stats.crit_chance = min(0.45, 0.05 + (SKL * 0.005))

    # Crit Damage = 200% base + (SKL * 3%)  [NERFED from 5%]
    # CAP: 300% to prevent one-shot exploits
    stats.crit_damage = min(3.0, 2.0 + (SKL * 0.03))

    # Block Power = 30% base + (SKL * 2%)
    # CAP: 70% reduction when blocking (strong but not immune)
    stats.block_power = min(0.70, 0.30 + (SKL * 0.02))

    # Parry Window = 0.2s base + (SKL * 0.01s)
    # CAP: 0.5s to keep parrying skill-based
    stats.parry_window = min(0.5, 0.2 + (SKL * 0.01))

    # === SPEED MODIFIERS ===

    # Attack Speed = -0.5% cooldown per AGI  [NERFED from 1%]
    # CAP: -20% to prevent animation bugs
    stats.attack_speed_bonus = max(-0.20, -(AGI * 0.005))

    # Stamina Regen = +0.5% per AGI  [NERFED from 1%]
    # No hard cap, but soft diminishing returns
    stats.stamina_regen_bonus = AGI * 0.005

    # === ECONOMIC/META BONUSES ===

    # Gold Bonus = 100% base + (CHA * 2%)  [NERFED from 5%]
    # CAP: +60% (160% total) to prevent economy break
    stats.gold_bonus = min(1.6, 1.0 + (CHA * 0.02))

    # Troop Bonus = CHA * 1%  [NERFED from 2%]
    # CAP: +40% to prevent troop steamroll
    # Note: This bonus applies to HP AND ATK of recruited troops
    stats.troop_bonus = min(0.40, CHA * 0.01)

    # Shop Discount = CHA * 0.5%  [NERFED from 1%]
    # CAP: -20% to keep shops profitable
    stats.shop_discount = min(0.20, CHA * 0.005)

    # === DEFENSE ===

    # Defense = VIT * 1%
    # CAP: 30% to prevent tank immortality
    # NOTE: This combines MULTIPLICATIVELY with armor (not additive)
    # Formula: damage_taken = damage * (1 - armor_def) * (1 - vit_def)
    stats.defense = min(0.30, VIT * 0.01)

    # Ensure HP doesn't exceed max after recalculation
    if stats.hp > stats.hp_max:
        stats.hp = stats.hp_max


def calculate_weapon_scaling(player: Entity, weapon: Weapon) -> float:
    """Calculate damage multiplier from weapon attribute scaling.

    Each weapon has scaling grades (S/A/B/C/D/E) for STR and AGI.
    Higher grades give more bonus damage from your attributes.

    BALANCED: Scaling gives moderate bonuses, not multiplicative explosions.

    Args:
        player: Player entity with stats
        weapon: Equipped weapon with scaling grades

    Returns:
        Multiplier to apply to weapon base damage (e.g., 1.6 = +60% damage)
    """
    # Scaling grade values (BALANCED - moderate bonuses)
    # S = +20% per 10 points, A = +15%, etc.
    scaling_values = {
        'S': 0.020,  # 2% per point
        'A': 0.015,  # 1.5% per point
        'B': 0.010,  # 1% per point
        'C': 0.005,  # 0.5% per point
        'D': 0.002,  # 0.2% per point
        'E': 0.000   # No scaling
    }

    # Get weapon scaling grades (default to E if not set)
    str_grade = getattr(weapon, 'scaling_str', 'E')
    agi_grade = getattr(weapon, 'scaling_agi', 'E')

    str_scaling = scaling_values.get(str_grade, 0.0)
    agi_scaling = scaling_values.get(agi_grade, 0.0)

    # Calculate bonus from each attribute
    str_bonus = player.stats.strength * str_scaling
    agi_bonus = player.stats.agility * agi_scaling

    # Total multiplier = 1.0 (base) + bonuses
    multiplier = 1.0 + str_bonus + agi_bonus

    return multiplier


def can_equip_weapon(player: Entity, weapon: Weapon) -> tuple[bool, float]:
    """Check if player can equip weapon and return penalty if requirements not met.

    SOFT LOCK: Player can use any weapon, but suffers penalty if stats too low.
    This prevents frustration while encouraging proper stat allocation.

    Args:
        player: Player entity
        weapon: Weapon to check

    Returns:
        Tuple of (can_use, penalty_multiplier)
        - can_use: Always True (soft lock)
        - penalty_multiplier: 1.0 if meets requirements, else 0.5-0.95 based on deficit
    """
    str_req = getattr(weapon, 'str_req', 0)
    agi_req = getattr(weapon, 'agi_req', 0)

    str_deficit = max(0, str_req - player.stats.strength)
    agi_deficit = max(0, agi_req - player.stats.agility)

    total_deficit = str_deficit + agi_deficit

    if total_deficit == 0:
        return (True, 1.0)  # No penalty

    # Penalty: -5% per point missing, minimum 50% effectiveness
    # Examples:
    #   1 point missing: 95% damage
    #   5 points missing: 75% damage
    #   10 points missing: 50% damage (cap)
    penalty = max(0.5, 1.0 - (total_deficit * 0.05))

    return (True, penalty)


def get_requirement_text(player: Entity, weapon: Weapon) -> str:
    """Get human-readable text for weapon requirements.

    Returns string like:
    - "Requires: 15 STR, 10 AGI" (if not met, shown in red)
    - "Requirements met" (if met, shown in green)
    - "Penalty: -25% damage (need 5 more STR)" (if using with penalty)
    """
    str_req = getattr(weapon, 'str_req', 0)
    agi_req = getattr(weapon, 'agi_req', 0)

    if str_req == 0 and agi_req == 0:
        return "No requirements"

    str_deficit = max(0, str_req - player.stats.strength)
    agi_deficit = max(0, agi_req - player.stats.agility)

    if str_deficit == 0 and agi_deficit == 0:
        return "Requirements met"

    # Build requirement text
    parts = []
    if str_req > 0:
        if str_deficit > 0:
            parts.append(f"{str_req} STR (need {str_deficit} more)")
        else:
            parts.append(f"{str_req} STR")

    if agi_req > 0:
        if agi_deficit > 0:
            parts.append(f"{agi_req} AGI (need {agi_deficit} more)")
        else:
            parts.append(f"{agi_req} AGI")

    req_text = "Requires: " + ", ".join(parts)

    # Add penalty text if not meeting requirements
    if str_deficit + agi_deficit > 0:
        _, penalty = can_equip_weapon(player, weapon)
        penalty_pct = int((1.0 - penalty) * 100)
        req_text += f"\nPenalty: -{penalty_pct}% damage"

    return req_text


def apply_equipment_requirements(player: Entity) -> None:
    """Apply penalties for using equipment without meeting requirements.

    This should be called when:
    - Equipping a weapon
    - Allocating attribute points (to update penalties)
    - Loading a save

    The penalty is applied as a damage multiplier in combat calculations.
    """
    if not hasattr(player, 'equipment') or player.equipment is None:
        return

    weapon = player.equipment.get_weapon()
    if weapon is None:
        return

    _, penalty = can_equip_weapon(player, weapon)

    # Store penalty on player for combat calculations
    # (Will be used in battle_combat.py when calculating damage)
    player.equipment_penalty = penalty
