"""Battle system constants - All magic numbers extracted and named.

This module centralizes all hardcoded values used in the battle system,
making them easy to find, modify, and balance.
"""

import math

# =============================================================================
# ARENA DIMENSIONS
# =============================================================================
ARENA_WIDTH = 1280
ARENA_HEIGHT = 720
ARENA_BORDER = 40

# =============================================================================
# PLAYER COMBAT
# =============================================================================

# Attack System
PLAYER_BASE_ATTACK_COOLDOWN = 0.5  # seconds
PLAYER_MIN_ATTACK_COOLDOWN = 0.25  # minimum possible cooldown
PLAYER_ATTACK_DURATION = 0.2  # how long the attack hitbox is active
PLAYER_OVERHEAD_COOLDOWN_BONUS = 0.3  # added to overhead attacks
PLAYER_THRUST_COOLDOWN_REDUCTION = 0.1  # subtracted from thrust attacks

# Light/Heavy Attack System (Dark Souls style)
PLAYER_LIGHT_ATTACK_STAMINA = 10.0  # Stamina cost for light attack
PLAYER_HEAVY_ATTACK_STAMINA = 30.0  # Stamina cost for heavy attack
PLAYER_HEAVY_ATTACK_DAMAGE_MULT = 1.8  # 180% damage for heavy attacks
PLAYER_HEAVY_ATTACK_COOLDOWN_MULT = 1.8  # 180% cooldown for heavy attacks
PLAYER_HEAVY_ATTACK_CHARGE_TIME = 0.3  # Seconds to hold for heavy attack
PLAYER_HEAVY_ATTACK_DURATION = 0.25  # Hitbox duration for heavy attack
PLAYER_LIGHT_ATTACK_DURATION = 0.15  # Hitbox duration for light attack
PLAYER_HEAVY_ATTACK_MOVE_MULT = 0.65  # Movement multiplier while charging/executing heavy attack

# Poise/Stagger System
POISE_DAMAGE_LIGHT_ATTACK = 20.0  # Poise damage from light attack
POISE_DAMAGE_HEAVY_ATTACK = 100.0  # Poise damage from heavy attack
POISE_REGEN_RATE = 33.0  # Poise regeneration per second (100 poise in 3s)
POISE_REGEN_DELAY = 3.0  # Delay before poise starts regenerating
STAGGER_DURATION = 1.5  # Seconds enemy is stunned when staggered
STAGGER_DAMAGE_BONUS = 1.25  # +25% damage to staggered enemies

# Attack Range
PLAYER_BASE_ATTACK_RANGE = 30.0  # added to player radius
PLAYER_MIN_WEAPON_RANGE = 30.0  # minimum weapon range considered
PLAYER_MAX_WEAPON_RANGE = 110.0  # maximum weapon range considered

# Stamina
PLAYER_STAMINA_MAX = 100.0
PLAYER_BASE_STAMINA_COST = 15.0  # default cost per attack
PLAYER_MIN_STAMINA_COST = 8.0  # minimum stamina cost
PLAYER_STAMINA_REGEN_RATE = 20.0  # per second
PLAYER_STAMINA_REGEN_DELAY = 1.0  # delay after attacking before regen starts

# Combo System
PLAYER_COMBO_WINDOW = 1.0  # seconds to perform next attack
PLAYER_COMBO_MAX_COUNT = 3  # max combo chain
PLAYER_COMBO_DAMAGE_MULTIPLIER = 0.3  # per combo level (1.0 -> 1.3 -> 1.6)

# Blocking
PLAYER_PERFECT_PARRY_WINDOW = 0.2  # seconds for perfect parry
PLAYER_BLOCK_DAMAGE_REDUCTION = 0.7  # 70% damage reduction (takes 30%)
PLAYER_PARRY_STUN_DURATION = 1.5  # seconds enemy is stunned

# =============================================================================
# TROOP COMBAT
# =============================================================================

# Attack
TROOP_MELEE_ATTACK_RANGE = 20  # added to troop radius
TROOP_ATTACK_DURATION = 0.3  # how long attack is active

# Archer
ARCHER_KITING_DISTANCE = 180  # minimum distance archer maintains
ARCHER_PROJECTILE_SPEED = 400.0  # pixels per second
ARCHER_PROJECTILE_RANGE = 500.0  # maximum projectile travel distance
ARCHER_FIRE_COOLDOWN_MIN = 1.0  # minimum seconds between shots
ARCHER_FIRE_COOLDOWN_MAX = 1.4  # maximum seconds between shots

# Veterancy
TROOP_XP_PER_KILL_MULTIPLIER = 2  # XP = enemy_level * this
TROOP_XP_TO_LEVEL_FORMULA = 10  # XP needed = level * this

# =============================================================================
# ENEMY AI
# =============================================================================

# Attack
ENEMY_ATTACK_COOLDOWN_MIN = 1.0  # seconds
ENEMY_ATTACK_COOLDOWN_MAX = 1.4  # seconds
ENEMY_ATTACK_DURATION = 0.3  # seconds
ENEMY_ATTACK_RANGE_BONUS = 15  # added to combined radii

# Movement
ENEMY_MOVE_SPEED_MULTIPLIER = 0.9  # multiplied by stats.spd
ENEMY_RETREAT_SPEED_MULTIPLIER = 1.2  # when fleeing for life
ENEMY_FLEE_SPEED_MULTIPLIER = 0.8  # when kiting (archer)
ENEMY_CIRCLE_SPEED_MULTIPLIER = 0.85  # when flanking
ENEMY_BLOCK_SPEED_MULTIPLIER = 0.2  # when blocking

# AI Behavior
ENEMY_RETREAT_HP_THRESHOLD = 0.3  # retreat when HP < 30%
ENEMY_CIRCLE_CHANCE = 0.4  # 40% chance to circle instead of rush
ENEMY_SPACING_DISTANCE = 50  # minimum distance between enemies
ENEMY_SPACING_PUSH_FORCE = 100  # push force when too close

# Blocking AI
ENEMY_BLOCK_DECISION_LOCK_MIN = 1.0  # seconds decision is locked
ENEMY_BLOCK_DECISION_LOCK_MAX = 2.0  # seconds decision is locked
ENEMY_BLOCK_CHANCE_HIGH_HP = 0.5  # 50% chance when HP > 50%
ENEMY_BLOCK_CHANCE_LOW_HP = 0.75  # 75% chance when HP < 50%
ENEMY_BLOCK_DETECTION_RANGE = 120  # distance to detect player attack
ENEMY_BLOCK_ATTACK_CONE_ANGLE = 0.5  # dot product threshold (60 degrees)

# Target Priority Weights (sum to 100)
ENEMY_PRIORITY_HP_WEIGHT = 40  # prioritize low HP targets
ENEMY_PRIORITY_THREAT_WEIGHT = 30  # prioritize high ATK targets
ENEMY_PRIORITY_DISTANCE_WEIGHT = 20  # slightly prefer closer
ENEMY_PRIORITY_PLAYER_WEIGHT = 10  # slight player preference
ENEMY_PRIORITY_MAX_DISTANCE = 400  # normalization distance

# =============================================================================
# DAMAGE TYPE EFFECTIVENESS SYSTEM
# =============================================================================

# Damage type vs armor material effectiveness multipliers
# Format: damage_type -> {armor_material -> multiplier}
DAMAGE_TYPE_EFFECTIVENESS = {
    "slashing": {
        "leather": 1.15,    # +25% vs leather (cuts through easily)
        "bronze": 0.97,     # -5% vs bronze (hard to cut)
        "chainmail": 0.95,  # -20% vs chainmail (links deflect slashes)
        "plate": 0.90,      # -30% vs plate (can't cut through solid metal)
    },
    "piercing": {
        "leather": 1.0,    # Normal vs leather
        "bronze": 1.05,     # +10% vs bronze (can pierce gaps)
        "chainmail": 1.10,  # +5% vs chainmail (can slip through links)
        "plate": 0.95,      # +30% vs plate (exploits joints and gaps)
    },
    "bludgeoning": {
        "leather": 0.90,    # -30,    # -10% vs leather (absorbs impact)
        "bronze": 1.08,     # +5% vs bronze (dents and crushes)
        "chainmail": 1.05,  # +25% vs chainmail (breaks bones through mail)
        "plate": 1.12,      # +50,      # Normal vs plate (blunt force trauma)
    },
}

# =============================================================================
# TERRAIN SYSTEM
# =============================================================================

# High Ground
TERRAIN_HIGH_GROUND_ATK_BONUS = 1.2  # +20% damage
TERRAIN_HIGH_GROUND_DEF_BONUS = 0.9  # -10% damage taken (attacker penalty)

# Hill Zone (from battle.py)
HILL_ZONE_X = 900  # top-left x
HILL_ZONE_Y = 100  # top-left y
HILL_ZONE_WIDTH = 300  # width
HILL_ZONE_HEIGHT = 200  # height

# =============================================================================
# FORMATIONS
# =============================================================================

# Circle Formation
FORMATION_CIRCLE_RADIUS = 80  # pixels from player center

# Line Formation
FORMATION_LINE_INFANTRY_FRONT_OFFSET_Y = -60  # in front of player
FORMATION_LINE_INFANTRY_SPACING = 60  # horizontal spacing
FORMATION_LINE_ARCHER_BACK_OFFSET_Y = 60  # behind player
FORMATION_LINE_ARCHER_SPACING = 50  # horizontal spacing
FORMATION_LINE_CAVALRY_SIDE_OFFSET_X = 120  # left/right of player
FORMATION_LINE_CAVALRY_OFFSET_Y = -40  # slightly forward

# Wedge Formation
FORMATION_WEDGE_CAVALRY_POINT_OFFSET_Y = -100  # at the point
FORMATION_WEDGE_CAVALRY_SIDE_OFFSET_X = 40  # left/right spacing
FORMATION_WEDGE_INFANTRY_SIDE_BASE = 60  # base offset
FORMATION_WEDGE_INFANTRY_DEPTH_INCREMENT = 40  # per row
FORMATION_WEDGE_ARCHER_CENTER_OFFSET_Y = 40  # back center
FORMATION_WEDGE_ARCHER_SPACING = 40  # horizontal spacing

# =============================================================================
# VISUAL EFFECTS
# =============================================================================

# Screen Shake
SCREEN_SHAKE_DECAY_RATE = 10.0  # per second
SCREEN_SHAKE_INTENSITY_MULTIPLIER = 20  # screen shake * this = pixel offset
SCREEN_SHAKE_BLOCK = 0.15  # when blocking
SCREEN_SHAKE_PARRY = 0.1  # when perfect parry
SCREEN_SHAKE_HIT = 0.3  # when hitting enemy
SCREEN_SHAKE_DEATH = 0.8  # when killing enemy
SCREEN_SHAKE_SLASH = 0.2  # slash attack
SCREEN_SHAKE_THRUST = 0.3  # thrust attack
SCREEN_SHAKE_OVERHEAD = 0.6  # overhead attack
SCREEN_SHAKE_PLAYER_DEATH = 0.8  # player dies

# Hit Pause
HIT_PAUSE_NORMAL = 0.05  # normal hit
HIT_PAUSE_OVERHEAD = 0.1  # overhead smash
HIT_PAUSE_DEATH = 0.15  # killing blow
HIT_PAUSE_MULTIPLIER = 0.3  # time scale during pause

# Particles
BLOOD_SPLATTER_COUNT_SLASH = 12  # slash attack
BLOOD_SPLATTER_COUNT_THRUST = 15  # thrust attack
BLOOD_SPLATTER_COUNT_OVERHEAD = 20  # overhead attack
BLOOD_SPLATTER_COUNT_DEATH = 30  # death blow
BLOOD_SPLATTER_COUNT_NORMAL = 8  # normal hit
BLOOD_SPLATTER_COUNT_TROOP = 5  # troop hit

IMPACT_DUST_COUNT_SLASH = 5  # slash attack
IMPACT_DUST_COUNT_OVERHEAD = 10  # overhead attack

BLOCK_SPARK_COUNT = 15  # blocking sparks

# Dust Timer
DUST_SPAWN_INTERVAL = 0.05  # seconds between dust particles

# =============================================================================
# DAMAGE NUMBERS & FLASHES
# =============================================================================

# Colors (RGB tuples)
DAMAGE_NUMBER_COLOR_NORMAL = (255, 255, 100)  # Yellow
DAMAGE_NUMBER_COLOR_OVERHEAD = (255, 180, 50)  # Orange
DAMAGE_NUMBER_COLOR_PLAYER_HIT = (255, 100, 100)  # Red
DAMAGE_NUMBER_COLOR_TROOP_HIT = (150, 200, 255)  # Blue
DAMAGE_NUMBER_COLOR_BLOCK = (200, 200, 255)  # Light blue
DAMAGE_NUMBER_COLOR_PARRY = (100, 255, 255)  # Cyan

HIT_FLASH_COLOR_HIT = (255, 100, 100)  # Red
HIT_FLASH_COLOR_DEATH = (255, 200, 0)  # Gold
HIT_FLASH_COLOR_PARRY = (100, 200, 255)  # Cyan
HIT_FLASH_COLOR_BLOCK = (150, 150, 200)  # Gray-blue
HIT_FLASH_COLOR_PLAYER_ALIVE = (255, 150, 150)  # Light red
HIT_FLASH_COLOR_PLAYER_DEATH = (200, 200, 255)  # White-blue

# =============================================================================
# MOVEMENT & PHYSICS
# =============================================================================

# Diagonal Movement Normalization
DIAGONAL_MOVEMENT_FACTOR = 1.0 / math.sqrt(2)  # 0.707... for 45° angles

# Entity Radius
DEFAULT_ENTITY_RADIUS = 15  # default if not specified

# =============================================================================
# BATTLE FLOW
# =============================================================================

# Victory/Defeat Delays
BATTLE_VICTORY_DELAY = 2.0  # seconds before processing victory
BATTLE_DEFEAT_DELAY = 2.0  # seconds before returning to world

# Reward Multipliers
REWARD_MONEY_MIN = 5  # minimum gold per enemy
REWARD_MONEY_MAX = 20  # maximum gold per enemy
REWARD_XP_MULTIPLIER = 10  # XP = enemy_level * this

# =============================================================================
# UI/HUD
# =============================================================================

# Battle HUD
HUD_COMBO_DISPLAY_DURATION = 1.0  # seconds to show combo counter
HUD_ORDER_FLASH_DURATION = 0.5  # seconds to flash order changes

# Focus Reticle
FOCUS_RETICLE_INNER_RADIUS_BONUS = 6  # added to enemy radius
FOCUS_RETICLE_OUTER_RADIUS_BONUS = 10  # added to enemy radius
FOCUS_RETICLE_MIN_INNER_RADIUS = 16  # minimum inner ring
FOCUS_RETICLE_MIN_OUTER_RADIUS = 20  # minimum outer ring

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_combo_multiplier(combo_count: int) -> float:
    """Calculate combo damage multiplier.

    Args:
        combo_count: Current combo count (1-3)

    Returns:
        Damage multiplier (1.0, 1.3, or 1.6)
    """
    return 1.0 + (combo_count - 1) * PLAYER_COMBO_DAMAGE_MULTIPLIER


def get_attack_range(player_radius: float, weapon_range: float) -> float:
    """Calculate effective attack range.

    Args:
        player_radius: Player entity radius
        weapon_range: Weapon range stat

    Returns:
        Total attack range in pixels
    """
    clamped_range = max(
        PLAYER_MIN_WEAPON_RANGE,
        min(weapon_range, PLAYER_MAX_WEAPON_RANGE)
    )
    return player_radius + PLAYER_BASE_ATTACK_RANGE + clamped_range


def should_enemy_retreat(hp_ratio: float, is_archer: bool) -> bool:
    """Determine if enemy should retreat based on HP.

    Args:
        hp_ratio: Current HP / Max HP
        is_archer: Whether enemy is an archer

    Returns:
        True if should retreat
    """
    return hp_ratio < ENEMY_RETREAT_HP_THRESHOLD and not is_archer
