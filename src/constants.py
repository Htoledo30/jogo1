"""Game constants and balance values.

All hardcoded values centralized here for easy balancing.
"""

# ============================================================================
# SCREEN & RENDERING
# ============================================================================
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# ============================================================================
# WORLD & MAP
# ============================================================================
WORLD_WIDTH = 4000
WORLD_HEIGHT = 3000

# ============================================================================
# ECONOMY
# ============================================================================
# Recruitment costs (scaled by tier)
RECRUIT_COST_BASE = 30
RECRUIT_COST_MULTIPLIER = 2.5  # T1=30, T2=75, T3=187

# Shop costs
REST_COST_TAVERN = 10
REST_COST_CASTLE = 0  # Free rest at castles
FOOD_COST = 15
FOOD_AMOUNT_PER_PURCHASE = 10
PEACE_PROPOSAL_COST = 100

# Starting resources
STARTING_GOLD = 50
STARTING_FOOD = 20

# Gold drops from enemies (per tier)
GOLD_DROP_MIN_PER_TIER = 10  # Increased from ~5
GOLD_DROP_MAX_PER_TIER = 20  # Increased from ~15

# Equipment costs (reduced T3 by ~40%)
# Will be applied in equipment.py

# ============================================================================
# PROGRESSION & XP
# ============================================================================
# XP formula: BASE + (level * MULTIPLIER)
# More linear progression instead of exponential
XP_FORMULA_BASE = 10
XP_FORMULA_MULTIPLIER = 10  # Level 1->2: 20 XP, Level 10->11: 110 XP

# XP rewards from enemies
XP_PER_ENEMY_TIER = 5  # Tier 1 = 5 XP, Tier 2 = 10 XP, etc.

# Levelup bonuses
LEVELUP_HP_BONUS = 8
LEVELUP_ATK_BONUS = 2

# Difficulty scaling
DIFFICULTY_TIME_FACTOR = 0.05  # minutes
DIFFICULTY_LEVEL_FACTOR = 0.1  # per level
DIFFICULTY_MAX = 2.0  # Cap at 2x

# ============================================================================
# COMBAT & BATTLE
# ============================================================================
# Player combat
PLAYER_STAMINA_MAX = 100
PLAYER_STAMINA_REGEN = 25  # Increased from 20
ATTACK_STAMINA_COST = 12  # Reduced from 15
BLOCK_STAMINA_COST = 5

# Parry timing
PERFECT_PARRY_WINDOW = 0.15  # Reduced from 0.2s for more skill

# Combo system
COMBO_TIMEOUT = 1.5
COMBO_DAMAGE_MULTIPLIERS = [1.0, 1.3, 1.6]  # Hit 1, 2, 3

# Terrain bonuses
HIGH_GROUND_DAMAGE_BONUS = 0.15  # Reduced from 0.20
HIGH_GROUND_DEFENSE_BONUS = 0.05  # Reduced from 0.10

# Attack cooldowns and durations
PLAYER_ATTACK_COOLDOWN = 0.5
PLAYER_ATTACK_DURATION = 0.2
ENEMY_ATTACK_COOLDOWN = 0.8
TROOP_ATTACK_COOLDOWN = 0.8

# ============================================================================
# SURVIVAL & RESOURCES
# ============================================================================
# Food consumption
FOOD_CONSUMPTION_INTERVAL = 120  # Increased from 60 (2 minutes instead of 1)
FOOD_PER_CONSUMPTION = 1

# Troop limits
BASE_TROOP_LIMIT = 1  # +1 per level (so level 1 = 2 troops, level 5 = 6 troops)

# ============================================================================
# DIPLOMACY
# ============================================================================
# Faction relation thresholds
RELATION_WAR_THRESHOLD = -30
RELATION_ALLY_THRESHOLD = 30
RELATION_MIN = -100
RELATION_MAX = 100

# Relation changes
RELATION_GAIN_PER_BANDIT_KILL = 2
RELATION_LOSS_CAPTURE = -50

# ============================================================================
# SLAVERY & CAPTURE
# ============================================================================
SLAVERY_CAPTURE_CHANCE = 0.5  # 50% on defeat by bandits
SLAVERY_GOLD_LOSS_PERCENT = 0.5  # Lose 50% of gold
SLAVERY_HP_AFTER_ESCAPE = 0.3  # 30% HP after escape
SLAVERY_ESCAPE_CHANCE = 0.05  # Reduced from 0.10 (5% per spacebar press)

# ============================================================================
# INVENTORY
# ============================================================================
INVENTORY_MAX_SIZE = 20
ITEM_DROP_CHANCE = 0.15  # 15% chance per enemy

# ============================================================================
# BATTLE ARENA
# ============================================================================
ARENA_WIDTH = 1920
ARENA_HEIGHT = 1080

# ============================================================================
# AI BEHAVIOR
# ============================================================================
# Enemy AI ranges
ENEMY_ATTACK_RANGE = 40
ENEMY_FLEE_HP_THRESHOLD = 0.25  # Flee when below 25% HP
ENEMY_BLOCK_CHANCE = 0.3  # 30% chance to block

# Troop AI
TROOP_ATTACK_RANGE = 45
TROOP_FOLLOW_DISTANCE = 80  # Start following player if further than this
TROOP_DEFEND_PLAYER_HP_THRESHOLD = 0.4  # Defend player when below 40% HP

# ============================================================================
# VISUAL EFFECTS
# ============================================================================
SCREEN_SHAKE_INTENSITY = 3
HIT_FLASH_DURATION = 0.15
DAMAGE_NUMBER_DURATION = 1.0
PARTICLE_LIFETIME = 2.0

# ============================================================================
# UI
# ============================================================================
NOTIFICATION_DURATION = 1.5
NOTIFICATION_DEFAULT_COLOR = (220, 220, 180)
NOTIFICATION_ERROR_COLOR = (255, 100, 100)
NOTIFICATION_SUCCESS_COLOR = (100, 255, 100)

# ============================================================================
# SAVE SYSTEM
# ============================================================================
SAVE_FILE_PATH = "savegame.json"
AUTO_SAVE_INTERVAL = 300  # Auto-save every 5 minutes (seconds)
