"""RPG progression and difficulty scaling (MVP implementation)."""

from __future__ import annotations

from typing import Dict
from .constants import (
    XP_FORMULA_BASE,
    XP_FORMULA_MULTIPLIER,
    LEVELUP_HP_BONUS,
    LEVELUP_ATK_BONUS,
    DIFFICULTY_TIME_FACTOR,
    DIFFICULTY_LEVEL_FACTOR,
    DIFFICULTY_MAX,
)


def xp_for_level(level: int) -> int:
    """Calculate XP needed for next level (exponential smooth progression).

    Formula: 15 * (level ^ 1.5)
    Progression examples:
    - Level 1->2: 30 XP
    - Level 2->3: 45 XP
    - Level 5->6: 135 XP
    - Level 10->11: 200 XP
    - Level 20->21: 535 XP
    """
    return int(15 * (level ** 1.5))


def grant_xp(player, amount: int) -> Dict[str, bool]:
    """Grant XP to player and handle level-ups.

    NEW SYSTEM: Instead of fixed stat bonuses, player receives attribute points
    to distribute freely. This enables build diversity and meaningful choices.
    """
    from src.attributes import calculate_derived_stats

    leveled = False
    points_earned = 0

    player.stats.xp += int(max(0, amount))

    # Level-up loop in case multiple levels are earned at once
    while player.stats.xp >= xp_for_level(player.stats.level + 1):
        player.stats.level += 1

        # NEW: Grant 1 attribute point per level
        player.stats.attribute_points += 1
        points_earned += 1

        # Recalculate derived stats (HP max, ATK, etc from attributes)
        calculate_derived_stats(player)

        # Restore HP to new max (level up = full heal)
        player.stats.hp = player.stats.hp_max

        # Update xp_to_next_level
        player.stats.xp_to_next_level = xp_for_level(player.stats.level + 1)
        leveled = True

    return {
        "leveled_up": leveled,
        "points_earned": points_earned
    }


def current_difficulty(time_minutes: float, player_level: int) -> float:
    """Calculate current difficulty multiplier (capped)."""
    time_component = DIFFICULTY_TIME_FACTOR * max(0.0, time_minutes)
    level_component = DIFFICULTY_LEVEL_FACTOR * max(0, player_level - 1)
    return min(DIFFICULTY_MAX, 1.0 + time_component + level_component)


def scale_enemy(enemy, difficulty: float) -> None:
    # Scale HP and ATK modestly; speed small bump
    enemy.stats.hp_max *= difficulty
    enemy.stats.hp *= difficulty
    enemy.stats.atk *= (0.9 + 0.2 * difficulty)
    enemy.stats.spd *= (0.95 + 0.1 * min(difficulty, 2.0))
