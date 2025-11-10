"""World/Overworld system constants.

All magic numbers from world.py, main.py overworld logic extracted here.
"""

import math

# =============================================================================
# WORLD DIMENSIONS
# =============================================================================
WORLD_WIDTH = 4000
WORLD_HEIGHT = 3000

# =============================================================================
# PLAYER MOVEMENT
# =============================================================================
PLAYER_MOVE_SPEED = 180.0  # pixels per second (overworld)
DIAGONAL_MOVEMENT_FACTOR = 1.0 / math.sqrt(2)  # 0.707 for 45° angles

# =============================================================================
# ARMY SPAWNING & BEHAVIOR
# =============================================================================

# Spawn Intervals
ARMY_SPAWN_INTERVAL = 30.0  # seconds between spawn attempts
CASTLE_SPAWN_INTERVAL = 60.0  # seconds before castle spawns army

# Army Sizes
ARMY_SIZE_MIN = 3  # minimum enemies in roaming army
ARMY_SIZE_MAX = 8  # maximum enemies in roaming army
CASTLE_ARMY_SIZE_MIN = 5  # minimum enemies from castle
CASTLE_ARMY_SIZE_MAX = 12  # maximum enemies from castle

# Army Movement
ARMY_MOVE_SPEED_MIN = 40.0  # slowest army
ARMY_MOVE_SPEED_MAX = 100.0  # fastest army
ARMY_WANDER_RADIUS = 200  # how far armies wander from spawn
ARMY_DIRECTION_CHANGE_CHANCE = 0.02  # per frame (60fps)

# Army Targeting
ARMY_PLAYER_DETECTION_RANGE = 300  # distance to detect player
ARMY_CHASE_SPEED_MULTIPLIER = 1.5  # speed boost when chasing
ARMY_LOSE_INTEREST_DISTANCE = 600  # stop chasing if player gets this far

# =============================================================================
# COLLISION & INTERACTION
# =============================================================================

# Detection Radii
LOCATION_INTERACTION_RADIUS = 80  # distance to interact with location
ARMY_COLLISION_RADIUS = 60  # distance to trigger battle with army
CASTLE_INTERACTION_RADIUS = 100  # distance to interact with castle/tavern

# Collision Processing
ARMY_COLLISION_CHECK_INTERVAL = 0.1  # seconds between collision checks

# =============================================================================
# DIPLOMACY & AUTO-RESOLVE
# =============================================================================

# Auto-Resolve Battle Thresholds
AUTO_RESOLVE_STRENGTH_RATIO_DECISIVE = 2.0  # 2x stronger = auto-win
AUTO_RESOLVE_STRENGTH_RATIO_ADVANTAGE = 1.5  # 1.5x stronger = likely win
AUTO_RESOLVE_BASE_CASUALTY_RATE = 0.3  # 30% losses in even fight
AUTO_RESOLVE_VICTORY_CASUALTY_MIN = 0.1  # 10% losses when winning
AUTO_RESOLVE_DEFEAT_CASUALTY_MAX = 0.8  # 80% losses when losing

# Faction Relations
RELATION_CHANGE_PER_BANDIT_KILL = 2  # relation gain with all factions
RELATION_CHANGE_ARMY_DEFEAT = -10  # relation loss when defeating faction army
RELATION_CHANGE_FRIENDLY_FIRE = -25  # attacking allied faction
RELATION_WAR_DECLARATION_THRESHOLD = -60  # auto-declare war below this

# =============================================================================
# FOOD & SURVIVAL
# =============================================================================

# Food Consumption
FOOD_CONSUMPTION_INTERVAL = 60.0  # seconds between consumption ticks
FOOD_PER_CONSUMPTION = 1  # food consumed per tick
FOOD_CONSUMPTION_PER_TROOP = 0.2  # additional food per troop

# Starvation
STARVATION_DAMAGE = 5  # HP lost when out of food
STARVATION_TROOP_DEATH_CHANCE = 0.1  # 10% chance troop dies from starvation

# =============================================================================
# CAMERA & VIEWPORT
# =============================================================================

# Camera Smoothing
CAMERA_LERP_FACTOR = 0.1  # lower = smoother, higher = more responsive
CAMERA_DEAD_ZONE = 50  # pixels before camera starts moving

# Viewport Bounds
VIEWPORT_MARGIN = 100  # keep player this far from screen edge

# =============================================================================
# TERRAIN & BIOMES
# =============================================================================

# Terrain Effects
TERRAIN_FOREST_SPEED_PENALTY = 0.7  # 30% slower in forests
TERRAIN_DESERT_SPEED_PENALTY = 0.8  # 20% slower in deserts
TERRAIN_MOUNTAIN_SPEED_PENALTY = 0.5  # 50% slower in mountains

# Terrain Sizes
FOREST_MIN_SIZE = 100
FOREST_MAX_SIZE = 300
DESERT_MIN_SIZE = 150
DESERT_MAX_SIZE = 400

# =============================================================================
# LOCATION GENERATION
# =============================================================================

# Castles
CASTLE_COUNT = 6  # number of faction castles
CASTLE_MIN_DISTANCE = 400  # minimum distance between castles

# Taverns
TAVERN_COUNT = 4  # number of taverns
TAVERN_MIN_DISTANCE_FROM_CASTLE = 200

# Villages
VILLAGE_COUNT = 8  # number of villages
VILLAGE_MIN_DISTANCE = 150  # minimum distance between villages

# =============================================================================
# ECONOMY (WORLD-SPECIFIC)
# =============================================================================

# Shop Inventory
SHOP_INITIAL_GOLD = 800  # starting gold for shops
SHOP_RESTOCK_INTERVAL = 300.0  # seconds between restocks
SHOP_RESTOCK_GOLD_AMOUNT = 200  # gold added per restock

# Loot Drops
LOOT_DROP_CHANCE_TIER1 = 0.15  # 15% drop chance
LOOT_DROP_CHANCE_TIER2 = 0.25  # 25% drop chance
LOOT_DROP_CHANCE_TIER3 = 0.40  # 40% drop chance
LOOT_QUALITY_BONUS_PER_TIER = 0.2  # quality improvement per tier

# Troop Recruitment
RECRUIT_AVAILABLE_MIN = 2  # minimum recruits available
RECRUIT_AVAILABLE_MAX = 6  # maximum recruits available

# =============================================================================
# QUEST SYSTEM (PLACEHOLDER)
# =============================================================================

# Quest Timers
QUEST_EXPIRATION_TIME = 600.0  # seconds before quest expires
QUEST_SPAWN_INTERVAL = 180.0  # seconds between new quests

# Quest Rewards
QUEST_REWARD_GOLD_MULTIPLIER = 50  # gold = difficulty * this
QUEST_REWARD_XP_MULTIPLIER = 25  # xp = difficulty * this
QUEST_REWARD_RELATION_BONUS = 10  # relation gain on completion

# =============================================================================
# TIME & DAY/NIGHT CYCLE
# =============================================================================

# Time Progression
GAME_TIME_SCALE = 60.0  # 1 real second = 60 game seconds
DAY_LENGTH = 1200.0  # game seconds (20 real minutes)
NIGHT_LENGTH = 600.0  # game seconds (10 real minutes)

# Time Effects
NIGHT_SPEED_PENALTY = 0.8  # 20% slower at night
NIGHT_SPAWN_MULTIPLIER = 1.5  # 50% more enemies at night

# =============================================================================
# NOTIFICATION SYSTEM
# =============================================================================

# Notification Display
NOTIFICATION_FADE_DURATION = 0.5  # seconds to fade in/out
NOTIFICATION_DISPLAY_TIME = 3.0  # seconds on screen
NOTIFICATION_MAX_QUEUE = 5  # maximum queued notifications

# Notification Types
NOTIFICATION_TYPE_INFO = "info"
NOTIFICATION_TYPE_WARNING = "warning"
NOTIFICATION_TYPE_ERROR = "error"
NOTIFICATION_TYPE_SUCCESS = "success"

# =============================================================================
# MINIMAP
# =============================================================================

# Minimap Dimensions
MINIMAP_WIDTH = 200
MINIMAP_HEIGHT = 150
MINIMAP_SCALE = 0.05  # world_size * scale = minimap_size
MINIMAP_OPACITY = 180  # 0-255

# Minimap Icons
MINIMAP_PLAYER_SIZE = 4  # radius in pixels
MINIMAP_ARMY_SIZE = 3
MINIMAP_LOCATION_SIZE = 5

# =============================================================================
# PERFORMANCE & CULLING
# =============================================================================

# Entity Culling
ENTITY_CULLING_MARGIN = 200  # pixels outside screen before culling
MAX_VISIBLE_ARMIES = 20  # maximum armies rendered at once

# Update Intervals
ARMY_UPDATE_INTERVAL = 0.016  # ~60fps
DIPLOMACY_UPDATE_INTERVAL = 1.0  # once per second
UI_UPDATE_INTERVAL = 0.033  # ~30fps

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_army_strength(army_size: int, avg_level: float) -> float:
    """Calculate army strength for auto-resolve.

    Args:
        army_size: Number of units in army
        avg_level: Average level of units

    Returns:
        Strength value (higher = stronger)
    """
    return army_size * avg_level


def get_terrain_speed_multiplier(terrain_type: str) -> float:
    """Get movement speed multiplier for terrain type.

    Args:
        terrain_type: Type of terrain ('forest', 'desert', 'mountain', etc.)

    Returns:
        Speed multiplier (0.0-1.0)
    """
    terrain_penalties = {
        'forest': TERRAIN_FOREST_SPEED_PENALTY,
        'desert': TERRAIN_DESERT_SPEED_PENALTY,
        'mountain': TERRAIN_MOUNTAIN_SPEED_PENALTY,
    }
    return terrain_penalties.get(terrain_type.lower(), 1.0)


def should_spawn_army(elapsed_time: float) -> bool:
    """Determine if enough time has passed to spawn new army.

    Args:
        elapsed_time: Seconds since last spawn

    Returns:
        True if should spawn
    """
    return elapsed_time >= ARMY_SPAWN_INTERVAL


def calculate_auto_resolve_casualties(strength_ratio: float, is_victor: bool) -> float:
    """Calculate casualty rate for auto-resolved battle.

    Args:
        strength_ratio: Attacker strength / Defender strength
        is_victor: True if this side won

    Returns:
        Casualty rate (0.0-1.0)
    """
    if is_victor:
        # Winners lose fewer troops based on strength advantage
        base_rate = AUTO_RESOLVE_VICTORY_CASUALTY_MIN
        if strength_ratio < AUTO_RESOLVE_STRENGTH_RATIO_ADVANTAGE:
            # Close fight = more casualties
            base_rate += (AUTO_RESOLVE_BASE_CASUALTY_RATE - AUTO_RESOLVE_VICTORY_CASUALTY_MIN) * \
                        (1.0 - (strength_ratio - 1.0) / (AUTO_RESOLVE_STRENGTH_RATIO_ADVANTAGE - 1.0))
        return min(base_rate, AUTO_RESOLVE_BASE_CASUALTY_RATE)
    else:
        # Losers lose more troops based on strength disadvantage
        base_rate = AUTO_RESOLVE_BASE_CASUALTY_RATE
        if strength_ratio > AUTO_RESOLVE_STRENGTH_RATIO_ADVANTAGE:
            # Getting crushed = catastrophic losses
            excess_ratio = min(strength_ratio - AUTO_RESOLVE_STRENGTH_RATIO_ADVANTAGE, 1.0)
            base_rate += (AUTO_RESOLVE_DEFEAT_CASUALTY_MAX - AUTO_RESOLVE_BASE_CASUALTY_RATE) * excess_ratio
        return min(base_rate, AUTO_RESOLVE_DEFEAT_CASUALTY_MAX)
