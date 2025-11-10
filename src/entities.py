"""Entities and stats for MVP B (implemented)."""

from __future__ import annotations
from . import items
from . import equipment

from dataclasses import dataclass
import math
import random
from typing import Tuple, TYPE_CHECKING


@dataclass
class Stats:
    hp_max: float
    hp: float
    atk: float
    spd: float
    level: int
    xp: int
    xp_to_next_level: int = 10
    food: int = 20
    gold: int = 0  # Gold for recruiting troops

    # Primary Attributes (new progression system)
    strength: int = 10      # Affects ATK, HP
    agility: int = 10       # Affects SPD, Attack Speed, Stamina Regen
    vitality: int = 10      # Affects HP Max, Stamina Max, Defense
    charisma: int = 10      # Affects Troop Bonus, Gold Find, Shop Discount
    skill: int = 10         # Affects Crit Chance, Crit Damage, Block Power
    attribute_points: int = 0  # Points available to spend

    # Derived Stats (calculated from attributes)
    stamina_max: float = 100.0
    crit_chance: float = 0.05      # 5% base
    crit_damage: float = 2.0       # 200% base
    block_power: float = 0.30      # 30% base reduction when blocking
    gold_bonus: float = 1.0        # 100% base (no bonus)
    troop_bonus: float = 0.0       # 0% base
    defense: float = 0.0           # 0% damage reduction
    parry_window: float = 0.2      # 0.2s base parry window
    attack_speed_bonus: float = 0.0  # 0% attack speed bonus
    stamina_regen_bonus: float = 0.0  # 0% stamina regen bonus
    shop_discount: float = 0.0     # 0% shop discount

    # Poise System (stagger/guard break)
    poise: float = 100.0           # Current poise (resistance to stagger)
    poise_max: float = 100.0       # Maximum poise
    is_staggered: bool = False     # Is entity currently stunned?
    stagger_timer: float = 0.0     # Time remaining stunned


class Entity:
    """Minimal entity with circular collision and basic damage."""

    def __init__(self, ent_id: int, kind: str, pos: Tuple[float, float], radius: float, stats: Stats):
        self.id = ent_id
        self.kind = kind
        self.pos = [float(pos[0]), float(pos[1])]
        self.vel = [0.0, 0.0]
        self.radius = float(radius)
        self.stats = stats
        self._invuln = 0.0
        self.equipment: equipment.Equipment | None = None
        self.inventory: list[items.Item] = []

    def update(self, dt: float) -> None:
        if self._invuln > 0:
            self._invuln = max(0.0, self._invuln - dt)

    def apply_damage(self, amount: float) -> None:
        if self._invuln > 0:
            return
        dmg = float(amount)

        # DEFENSE SYSTEM: Armor and VIT defense combine MULTIPLICATIVELY
        try:
            armor_def = 0.0
            vit_def = 0.0

            # 1. Armor defense from equipment
            if getattr(self, 'equipment', None):
                armor_def = self.equipment.get_total_defense()
                # Simple shield passive if weapon is a shield
                weapon = self.equipment.get_weapon()
                if getattr(weapon, 'weapon_type', '') == 'shield':
                    armor_def = min(0.9, armor_def + 0.05)  # small bonus

            # 2. VIT defense from attributes (player only)
            if hasattr(self.stats, 'defense'):
                vit_def = self.stats.defense

            # 3. MULTIPLICATIVE COMBINATION (not additive!)
            # Formula: final_damage = damage * (1 - armor) * (1 - vit)
            # Example: 20% armor + 30% vit = 1 - (0.8 * 0.7) = 44% total (not 50%)
            dmg = dmg * (1.0 - armor_def) * (1.0 - vit_def)

        except Exception:
            pass

        self.stats.hp = max(0.0, self.stats.hp - dmg)
        self._invuln = 0.3

    def alive(self) -> bool:
        return self.stats.hp > 0.0


def create_player(seed: int) -> Entity:
    """Create a new player with default stats.

    Starting attributes are all 10 (balanced).
    Derived stats are calculated from these base attributes.
    """
    from src.attributes import calculate_derived_stats

    rng = random.Random(seed)

    # Create base stats with default attributes (all 10)
    # Note: hp_max, atk, spd will be recalculated by calculate_derived_stats
    from src.rpg import xp_for_level

    s = Stats(
        hp_max=1, hp=1, atk=1, spd=1,  # Placeholder values
        level=1, xp=0, xp_to_next_level=xp_for_level(2),  # Proper XP formula
        food=20, gold=50
    )

    player = Entity(1, "player", (640.0 + rng.randint(-40, 40), 360.0 + rng.randint(-40, 40)), 16.0, s)

    # Calculate derived stats from base attributes (this sets proper hp_max, atk, spd)
    calculate_derived_stats(player)

    # Set HP to max after calculation
    player.stats.hp = player.stats.hp_max

    return player


def create_troop(seed: int, troop_type: str, tier: int) -> Entity:
    """Create a troop (ally soldier).

    Types:
    - warrior: balanced melee
    - archer: ranged (future), high atk low hp
    - tank: high hp, low speed
    - lancer: alias of tank (uses lancer visuals)
    """
    rng = random.Random(seed)

    ttype = troop_type.lower()
    if ttype == "warrior":
        hp = 40 + 10 * tier
        atk = 8 + 2 * tier
        spd = 150 + 5 * tier
    elif ttype == "archer":
        hp = 30 + 8 * tier
        atk = 12 + 3 * tier
        spd = 140 + 5 * tier
    elif ttype == "tank" or ttype == "lancer":
        hp = 60 + 15 * tier
        atk = 6 + 2 * tier
        spd = 120 + 3 * tier
    else:
        hp, atk, spd = 40, 8, 150
        ttype = "warrior"

    s = Stats(hp_max=hp, hp=hp, atk=atk, spd=spd, level=tier, xp=0, xp_to_next_level=tier * 10)
    pos = (640.0 + rng.randint(-60, 60), 360.0 + rng.randint(-60, 60))
    troop = Entity(rng.randint(1000000, 9999999), f"troop_{ttype}", pos, 14.0, s)
    troop.troop_type = ("tank" if ttype == "lancer" else ttype)  # AI behavior
    # Visual hint for sprite modules (troop_sprites uses unit_type/archetype)
    if ttype == "lancer":
        troop.unit_type = "lancer"
    else:
        troop.unit_type = ttype
    return troop


def create_enemy(seed: int, tier: int, enemy_type: str = None) -> Entity:
    """Create an enemy with varied types and stats.

    Types:
    - bandit: Fast, low HP, medium damage (raiders and thieves)
    - soldier: Balanced stats, can block (kingdom deserters)
    - brute: Slow, high HP, high damage (berserkers)
    - beast: Very fast, low HP, erratic movement (wolves, monsters)
    """
    rng = random.Random((seed << 1) ^ (tier * 7919))

    # Auto-select enemy type if not specified
    if enemy_type is None:
        enemy_type = rng.choice([
            "bandit", "soldier", "brute", "beast",
            # 280 BC themed archetypes
            "phalangite", "hoplite", "legionary", "cataphract",
            "ptolemaic_guard", "carthaginian", "pontic_raider",
            "thracian", "kush_archer", "maurya_spearman"
        ])

    # Base stats vary by type
    if enemy_type == "bandit":
        base_hp = 25 + 10 * tier
        base_atk = 7 + 3 * tier
        base_spd = 160 + 12 * tier  # Fast
    elif enemy_type == "soldier":
        base_hp = 35 + 12 * tier
        base_atk = 6 + 3 * tier
        base_spd = 130 + 8 * tier   # Balanced
    elif enemy_type == "brute":
        base_hp = 50 + 15 * tier
        base_atk = 10 + 4 * tier
        base_spd = 100 + 5 * tier   # Slow but hits hard
    elif enemy_type == "beast":
        base_hp = 20 + 8 * tier
        base_atk = 8 + 2 * tier
        base_spd = 180 + 15 * tier  # Very fast
    elif enemy_type == "phalangite":
        base_hp = 55 + 15 * tier
        base_atk = 9 + 4 * tier
        base_spd = 95 + 4 * tier   # Heavy formation infantry
    elif enemy_type == "hoplite":
        base_hp = 45 + 12 * tier
        base_atk = 8 + 3 * tier
        base_spd = 110 + 6 * tier  # Shielded, disciplined
    elif enemy_type == "legionary":
        base_hp = 50 + 14 * tier
        base_atk = 9 + 4 * tier
        base_spd = 115 + 6 * tier  # Well-balanced professional
    elif enemy_type == "cataphract":
        base_hp = 70 + 20 * tier
        base_atk = 11 + 4 * tier
        base_spd = 105 + 5 * tier  # Heavy cavalry prototype
    elif enemy_type == "ptolemaic_guard":
        base_hp = 50 + 14 * tier
        base_atk = 8 + 3 * tier
        base_spd = 110 + 6 * tier
    elif enemy_type == "carthaginian":
        base_hp = 45 + 12 * tier
        base_atk = 8 + 3 * tier
        base_spd = 120 + 7 * tier
    elif enemy_type == "pontic_raider":
        base_hp = 35 + 10 * tier
        base_atk = 8 + 3 * tier
        base_spd = 140 + 10 * tier
    elif enemy_type == "thracian":
        base_hp = 40 + 12 * tier
        base_atk = 10 + 4 * tier
        base_spd = 130 + 9 * tier   # Aggressive
    elif enemy_type == "kush_archer":
        base_hp = 30 + 10 * tier
        base_atk = 9 + 3 * tier
        base_spd = 145 + 10 * tier  # Mobile archer
    elif enemy_type == "maurya_spearman":
        base_hp = 45 + 12 * tier
        base_atk = 9 + 3 * tier
        base_spd = 120 + 7 * tier
    # New archer types
    elif enemy_type == "macedon_archer":
        base_hp = 32 + 10 * tier
        base_atk = 8 + 3 * tier
        base_spd = 140 + 9 * tier  # Macedonian archer
    elif enemy_type == "greek_archer":
        base_hp = 30 + 10 * tier
        base_atk = 8 + 3 * tier
        base_spd = 135 + 8 * tier  # Greek archer
    elif enemy_type == "egyptian_archer":
        base_hp = 30 + 10 * tier
        base_atk = 9 + 3 * tier
        base_spd = 140 + 9 * tier  # Egyptian archer
    elif enemy_type == "seleucid_archer":
        base_hp = 32 + 10 * tier
        base_atk = 9 + 3 * tier
        base_spd = 145 + 10 * tier  # Seleucid composite bow archer
    elif enemy_type == "roman_archer":
        base_hp = 35 + 11 * tier
        base_atk = 8 + 3 * tier
        base_spd = 130 + 8 * tier  # Roman auxiliary archer
    elif enemy_type == "carthage_archer":
        base_hp = 32 + 10 * tier
        base_atk = 9 + 3 * tier
        base_spd = 140 + 9 * tier  # Carthaginian archer
    else:
        # Fallback to generic
        base_hp = 30 + 12 * tier
        base_atk = 6 + 3 * tier
        base_spd = 140 + 10 * tier
        enemy_type = "bandit"

    s = Stats(hp_max=base_hp, hp=base_hp, atk=base_atk, spd=base_spd, level=max(1, tier), xp=0, xp_to_next_level=max(1, tier) * 10)
    ex = 200 + rng.randint(0, 800)
    ey = 120 + rng.randint(0, 480)

    enemy = Entity(rng.randint(2, 1_000_000), f"enemy_{enemy_type}", (ex, ey), 14.0, s)
    enemy.enemy_type = enemy_type  # Store for AI behavior

    # Determine troop_type based on enemy_type for proper AI behavior
    enemy_type_lower = enemy_type.lower()
    if 'archer' in enemy_type_lower or 'bow' in enemy_type_lower:
        enemy.troop_type = 'archer'
    elif enemy_type in ('cataphract', 'phalangite', 'ptolemaic_guard'):
        enemy.troop_type = 'tank'
    else:
        enemy.troop_type = 'warrior'

    return enemy


def distance(a: Entity, b: Entity) -> float:
    dx = a.pos[0] - b.pos[0]
    dy = a.pos[1] - b.pos[1]
    return math.hypot(dx, dy)


@dataclass
class Location:
    """Represents a location on the world map."""
    name: str
    pos: tuple[int, int]
    location_type: str  # "town", "castle", "bandit_camp"
    radius: int
    faction: str

    def distance_to(self, entity: Entity) -> float:
        """Calculate distance from location center to an entity."""
        dx = self.pos[0] - entity.pos[0]
        dy = self.pos[1] - entity.pos[1]
        return math.hypot(dx, dy)


@dataclass
class FactionRelations:
    """Manages player's relations with factions."""
    relations: dict[str, int] = None

    def __post_init__(self):
        if self.relations is None:
            # Initialize relations with all 11 factions (280 BC era)
            # Bandits are enemies, all others start neutral
            self.relations = {
                "macedon": 0,
                "greeks": 0,
                "ptolemaic": 0,
                "seleucid": 0,
                "rome": 0,
                "carthage": 0,
                "kush": 0,
                "maurya": 0,
                "pontus": 0,
                "thrace": 0,
                "bandits": -50,  # Only enemies
            }

    def update_relation(self, faction: str, amount: int):
        if faction in self.relations:
            self.relations[faction] = max(-100, min(100, self.relations[faction] + amount))

    def get_status(self, faction: str) -> str:
        relation = self.relations.get(faction, 0)
        if relation < -30: return "GUERRA"
        if relation > 30: return "ALIADO"
        return "NEUTRO"
