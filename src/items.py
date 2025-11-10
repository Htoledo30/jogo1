"""
Advanced Item System with Quality, Durability, Weight, and Modifiers.

Supports Mount & Blade / Kenshi style inventory management.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import random


class ItemQuality(Enum):
    """Item quality levels affecting stats."""
    POOR = "Poor"           # -20% stats, 60% price
    NORMAL = "Normal"       # Base stats, 100% price
    FINE = "Fine"          # +10% stats, 150% price
    MASTERWORK = "Masterwork"  # +20% stats, 200% price


class ItemType(Enum):
    """Categories of items."""
    WEAPON = "Weapon"
    ARMOR = "Armor"
    CONSUMABLE = "Consumable"
    MATERIAL = "Material"
    QUEST = "Quest"


@dataclass
class Item:
    """
    Enhanced item with quality, durability, weight, and description.
    """
    # Basic properties
    name: str
    item_type: ItemType
    base_value: int  # Gold value
    weight: float    # kg
    description: str = ""

    # Quality & Condition
    quality: ItemQuality = ItemQuality.NORMAL
    durability: float = 100.0  # 0-100%

    # Equipment stats (None if not equipment)
    damage: Optional[float] = None       # Weapon damage multiplier
    defense: Optional[float] = None      # Armor defense value
    speed_modifier: Optional[float] = None  # Speed penalty/bonus

    # Additional properties
    tier: int = 1  # 1-3
    is_equipped: bool = False
    is_quest_item: bool = False
    stack_size: int = 1  # For consumables/materials

    # Visual
    icon_color: tuple = (200, 200, 200)  # RGB color for icon

    def get_effective_stats(self) -> dict:
        """Calculate actual stats after quality and durability modifiers."""
        quality_mult = {
            ItemQuality.POOR: 0.8,
            ItemQuality.NORMAL: 1.0,
            ItemQuality.FINE: 1.1,
            ItemQuality.MASTERWORK: 1.2
        }[self.quality]

        durability_mult = max(0.5, self.durability / 100.0)  # Min 50% effectiveness

        final_mult = quality_mult * durability_mult

        return {
            "damage": self.damage * final_mult if self.damage else None,
            "defense": self.defense * final_mult if self.defense else None,
            "speed_modifier": self.speed_modifier,  # Speed not affected
        }

    def get_display_name(self) -> str:
        """Get full display name with quality prefix."""
        if self.quality == ItemQuality.NORMAL:
            return self.name
        return f"{self.quality.value} {self.name}"

    def get_value(self) -> int:
        """Get actual gold value based on quality and durability."""
        quality_mult = {
            ItemQuality.POOR: 0.6,
            ItemQuality.NORMAL: 1.0,
            ItemQuality.FINE: 1.5,
            ItemQuality.MASTERWORK: 2.0
        }[self.quality]

        durability_mult = max(0.3, self.durability / 100.0)  # Min 30% value

        return int(self.base_value * quality_mult * durability_mult)

    def get_sell_price(self) -> int:
        """Get sell price (50% of current value)."""
        return int(self.get_value() * 0.5)

    def get_tier_color(self) -> tuple:
        """Get color based on tier (Bronze, Silver, Gold)."""
        tier_colors = {
            1: (205, 127, 50),   # Bronze
            2: (192, 192, 192),  # Silver
            3: (255, 215, 0),    # Gold
        }
        return tier_colors.get(self.tier, (200, 200, 200))

    def degrade(self, amount: float = 1.0):
        """Reduce durability by amount."""
        if not self.is_quest_item:
            self.durability = max(0.0, self.durability - amount)

    def repair(self, amount: float = 50.0):
        """Restore durability by amount."""
        self.durability = min(100.0, self.durability + amount)

    def is_broken(self) -> bool:
        """Check if item is completely broken."""
        return self.durability <= 0.0

    # --- Serialization helpers ---
    def to_dict(self) -> dict:
        """Serialize item to a plain dict suitable for JSON save."""
        return {
            "name": self.name,
            "item_type": self.item_type.value,
            "base_value": self.base_value,
            "weight": self.weight,
            "description": self.description,
            "quality": self.quality.value,
            "durability": self.durability,
            "damage": self.damage,
            "defense": self.defense,
            "speed_modifier": self.speed_modifier,
            "tier": self.tier,
            "is_equipped": self.is_equipped,
            "is_quest_item": self.is_quest_item,
            "stack_size": self.stack_size,
            "icon_color": list(self.icon_color) if isinstance(self.icon_color, tuple) else self.icon_color,
        }

    @staticmethod
    def from_dict(data: dict) -> "Item":
        """Recreate an Item from a dict produced by to_dict."""
        # Map strings back to enums
        t = ItemType(data.get("item_type", ItemType.WEAPON.value))
        q = ItemQuality(data.get("quality", ItemQuality.NORMAL.value))
        it = Item(
            name=data.get("name", "Unknown"),
            item_type=t,
            base_value=int(data.get("base_value", 0)),
            weight=float(data.get("weight", 1.0)),
            description=data.get("description", ""),
            quality=q,
            durability=float(data.get("durability", 100.0)),
            damage=data.get("damage"),
            defense=data.get("defense"),
            speed_modifier=data.get("speed_modifier"),
            tier=int(data.get("tier", 1)),
            is_equipped=bool(data.get("is_equipped", False)),
            is_quest_item=bool(data.get("is_quest_item", False)),
            stack_size=int(data.get("stack_size", 1)),
            icon_color=tuple(data.get("icon_color", (200, 200, 200))),
        )
        return it


# ============================================================================
# ITEM CREATION FUNCTIONS
# ============================================================================

def create_weapon(name: str, tier: int, damage: float, speed_mod: float,
                  base_value: int, description: str = "",
                  quality: ItemQuality = ItemQuality.NORMAL) -> Item:
    """Create a weapon item."""
    weight = 2.0 + tier * 1.5  # Weapons: 3.5kg (T1) to 6.5kg (T3)

    return Item(
        name=name,
        item_type=ItemType.WEAPON,
        base_value=base_value,
        weight=weight,
        description=description,
        quality=quality,
        damage=damage,
        speed_modifier=speed_mod,
        tier=tier,
        icon_color=(220, 180, 140)  # Tan for weapons
    )


def create_armor(name: str, tier: int, defense: float, speed_penalty: float,
                 base_value: int, description: str = "",
                 quality: ItemQuality = ItemQuality.NORMAL) -> Item:
    """Create an armor piece."""
    weight = 3.0 + tier * 3.0  # Armor: 6kg (T1) to 12kg (T3)

    return Item(
        name=name,
        item_type=ItemType.ARMOR,
        base_value=base_value,
        weight=weight,
        description=description,
        quality=quality,
        defense=defense,
        speed_modifier=-speed_penalty,
        tier=tier,
        icon_color=(160, 160, 180)  # Steel blue for armor
    )


def create_consumable(name: str, base_value: int, stack_size: int = 1,
                      description: str = "") -> Item:
    """Create a consumable item (potion, food, etc)."""
    return Item(
        name=name,
        item_type=ItemType.CONSUMABLE,
        base_value=base_value,
        weight=0.2,  # Light
        description=description,
        stack_size=stack_size,
        icon_color=(100, 255, 100)  # Green for consumables
    )


def create_random_quality_weapon(name: str, tier: int, damage: float,
                                 speed_mod: float, base_value: int,
                                 description: str = "") -> Item:
    """Create a weapon with random quality."""
    # 50% Normal, 30% Fine, 15% Poor, 5% Masterwork
    roll = random.random()
    if roll < 0.15:
        quality = ItemQuality.POOR
    elif roll < 0.65:
        quality = ItemQuality.NORMAL
    elif roll < 0.95:
        quality = ItemQuality.FINE
    else:
        quality = ItemQuality.MASTERWORK

    return create_weapon(name, tier, damage, speed_mod, base_value, description, quality)


def create_random_quality_armor(name: str, tier: int, defense: float,
                                speed_penalty: float, base_value: int,
                                description: str = "") -> Item:
    """Create armor with random quality."""
    roll = random.random()
    if roll < 0.15:
        quality = ItemQuality.POOR
    elif roll < 0.65:
        quality = ItemQuality.NORMAL
    elif roll < 0.95:
        quality = ItemQuality.FINE
    else:
        quality = ItemQuality.MASTERWORK

    return create_armor(name, tier, defense, speed_penalty, base_value, description, quality)


# ============================================================================
# ITEM DATABASE
# ============================================================================

ITEM_DATABASE = {
    # WEAPONS - Swords
    "basic_sword": {
        "name": "Iron Sword",
        "tier": 1,
        "damage": 1.0,
        "speed_mod": 0.0,
        "value": 50,
        "desc": "A simple but reliable iron blade."
    },
    "longsword": {
        "name": "Steel Longsword",
        "tier": 2,
        "damage": 1.5,
        "speed_mod": -0.05,
        "value": 200,
        "desc": "A well-crafted longsword of tempered steel."
    },
    "legendary_blade": {
        "name": "Legendary Blade",
        "tier": 3,
        "damage": 2.0,
        "speed_mod": -0.10,
        "value": 480,
        "desc": "An ancient blade forged by master smiths. Its edge never dulls."
    },

    # ARMOR - Helmets
    "leather_helmet": {
        "name": "Leather Cap",
        "tier": 1,
        "defense": 2.0,
        "speed_penalty": 0.02,
        "value": 30,
        "desc": "Simple leather headgear. Better than nothing."
    },
    "chainmail_helmet": {
        "name": "Chainmail Coif",
        "tier": 2,
        "defense": 5.0,
        "speed_penalty": 0.05,
        "value": 120,
        "desc": "Interlocking metal rings protect your head."
    },
    "plate_helmet": {
        "name": "Plate Helmet",
        "tier": 3,
        "defense": 10.0,
        "speed_penalty": 0.10,
        "value": 300,
        "desc": "Full plate helm. Nearly impenetrable but heavy."
    },

    # ARMOR - Chest
    "leather_armor": {
        "name": "Leather Armor",
        "tier": 1,
        "defense": 4.0,
        "speed_penalty": 0.05,
        "value": 50,
        "desc": "Simple leather chest armor. Provides basic protection."
    },
    "chainmail_armor": {
        "name": "Chainmail Armor",
        "tier": 2,
        "defense": 8.0,
        "speed_penalty": 0.10,
        "value": 200,
        "desc": "Interlocking metal rings protect your torso."
    },
    "plate_armor": {
        "name": "Plate Armor",
        "tier": 3,
        "defense": 12.0,
        "speed_penalty": 0.15,
        "value": 480,
        "desc": "Heavy plate cuirass. Offers superior protection."
    },

    # ARMOR - Legs
    "leather_leggings": {
        "name": "Leather Leggings",
        "tier": 1,
        "defense": 2.0,
        "speed_penalty": 0.03,
        "value": 35,
        "desc": "Simple leather leg protection."
    },
    "chainmail_leggings": {
        "name": "Chainmail Leggings",
        "tier": 2,
        "defense": 4.0,
        "speed_penalty": 0.06,
        "value": 150,
        "desc": "Metal ring leggings for leg protection."
    },
    "plate_leggings": {
        "name": "Plate Leggings",
        "tier": 3,
        "defense": 6.0,
        "speed_penalty": 0.10,
        "value": 360,
        "desc": "Heavy plate leg armor."
    },

    # ARMOR - Boots
    "leather_boots": {
        "name": "Leather Boots",
        "tier": 1,
        "defense": 1.0,
        "speed_penalty": 0.02,
        "value": 25,
        "desc": "Simple leather boots."
    },
    "chainmail_boots": {
        "name": "Chainmail Boots",
        "tier": 2,
        "defense": 2.0,
        "speed_penalty": 0.04,
        "value": 100,
        "desc": "Metal-reinforced boots."
    },
    "plate_boots": {
        "name": "Plate Boots",
        "tier": 3,
        "defense": 4.0,
        "speed_penalty": 0.06,
        "value": 240,
        "desc": "Heavy plate boots with full protection."
    },

    # CONSUMABLES
    "bandage": {
        "name": "Bandage",
        "value": 10,
        "desc": "Restores 20 HP. Single use."
    },
    "health_potion": {
        "name": "Health Potion",
        "value": 50,
        "desc": "Restores 50 HP. Tastes terrible."
    },
    "bread": {
        "name": "Bread Loaf",
        "value": 5,
        "desc": "Simple food. Restores 5 food."
    },

    # --------------------------------------------------------------------
    # Legendary drops from Unique Monsters (hostile to all)
    # Each unique monster has a signature item. These are high-tier rewards.
    # --------------------------------------------------------------------
    "cyclops_club": {
        "name": "Cyclops War Club",
        "tier": 3,
        "damage": 2.2,
        "speed_mod": -0.15,
        "value": 700,
        "desc": "A massive club hewn from ancient oak. Devastating but slow."
    },
    "dire_wolf_pelt": {
        "name": "Dire Wolf Pelt",
        "tier": 3,
        "defense": 8.5,
        "speed_penalty": -0.02,
        "value": 520,
        "desc": "Thick fur cloak. Surprisingly light; grants agility and warmth."
    },
    "minotaur_labrys": {
        "name": "Minotaur Labrys",
        "tier": 3,
        "damage": 2.4,
        "speed_mod": -0.12,
        "value": 780,
        "desc": "Dual-headed axe that thirsts for battle."
    },
    "hydra_scale_mail": {
        "name": "Hydra Scale Mail",
        "tier": 3,
        "defense": 16.0,
        "speed_penalty": 0.06,
        "value": 900,
        "desc": "Armor woven from hydra scales; resistant and near-impervious."
    },
    "boar_tusk_spear": {
        "name": "Boar Tusk Spear",
        "tier": 3,
        "damage": 2.0,
        "speed_mod": -0.06,
        "value": 640,
        "desc": "Stout spear tipped with giant tusk. Excellent for thrusts."
    },
    "sabertooth_claws": {
        "name": "Sabertooth Claws",
        "tier": 3,
        "damage": 1.8,
        "speed_mod": 0.06,
        "value": 600,
        "desc": "Curved blades fashioned from fangs. Swift and lethal."
    },
    "nemean_lion_hide": {
        "name": "Nemean Lion Hide",
        "tier": 3,
        "defense": 14.0,
        "speed_penalty": 0.02,
        "value": 850,
        "desc": "Legend says no blade can pierce it. Offers superb protection."
    },
    "harpy_feather_cloak": {
        "name": "Harpy Feather Cloak",
        "tier": 3,
        "defense": 6.0,
        "speed_penalty": -0.04,
        "value": 560,
        "desc": "Cloak of sharp pinions; light as air, quickens the step."
    },
    "gorgon_visor": {
        "name": "Gorgon Visor",
        "tier": 3,
        "defense": 9.0,
        "speed_penalty": 0.03,
        "value": 720,
        "desc": "Helm with a fearsome visage; foes balk at your gaze."
    },
    "centaur_lance": {
        "name": "Centaur Lance",
        "tier": 3,
        "damage": 2.1,
        "speed_mod": -0.05,
        "value": 680,
        "desc": "Balanced lance favored by the swift. Excels at charges."
    },

    # ================================================================
    # 280 BC Content — Hellenistic and Mediterranean Arsenal
    # ================================================================

    # 1) Macedon — Sarissa, Xiphos, Kopis, Phrygian helmet, Muscled cuirass
    "macedon_sarissa_t1": {"name": "Sarissa", "tier": 1, "damage": 1.4, "speed_mod": -0.08, "value": 90,
        "desc": "Long pike of the Macedonian phalanx (~5m). Heavy but deadly in formation."},
    "macedon_sarissa_t2": {"name": "Sarissa", "tier": 2, "damage": 1.7, "speed_mod": -0.10, "value": 220,
        "desc": "Seasoned phalangite pike. Superior reach and weight."},
    "macedon_sarissa_t3": {"name": "Sarissa", "tier": 3, "damage": 2.0, "speed_mod": -0.12, "value": 520,
        "desc": "Elite sarissa. Imposing reach; unwieldy alone, devastating in ranks."},
    "greek_xiphos_t1": {"name": "Xiphos", "tier": 1, "damage": 1.0, "speed_mod": 0.02, "value": 60,
        "desc": "Greek short sword; quick sidearm for close quarters."},
    "greek_kopis_t2": {"name": "Kopis", "tier": 2, "damage": 1.6, "speed_mod": -0.04, "value": 210,
        "desc": "Forward-curved blade; chops with weighty strikes."},
    "phrygian_helmet_t1": {"name": "Phrygian Helmet", "tier": 1, "defense": 2.0, "speed_penalty": 0.01, "value": 35,
        "desc": "Helmet with forward-curving crest, common in Macedonia."},
    "muscled_cuirass_t2": {"name": "Muscled Bronze Cuirass", "tier": 2, "defense": 12.0, "speed_penalty": 0.06, "value": 220,
        "desc": "Bronze breastplate shaped to musculature; strong but heavy."},
    "pelte_shield_t1": {"name": "Pelte Shield", "tier": 1, "damage": 0.7, "speed_mod": 0.0, "value": 50,
        "desc": "Small round shield. Useful for bashing and defense."},

    # 2) Greek City-States — Dory, Xiphos, Aspis, Corinthian/Illyrian helmets, Linothorax
    "greek_dory_t1": {"name": "Dory Hoplite Spear", "tier": 1, "damage": 1.3, "speed_mod": -0.03, "value": 80,
        "desc": "Hoplite spear; balanced reach and control."},
    "greek_dory_t2": {"name": "Dory Hoplite Spear", "tier": 2, "damage": 1.5, "speed_mod": -0.04, "value": 200,
        "desc": "Well-crafted spear with hardened tip."},
    "aspis_shield_t2": {"name": "Aspis (Hoplite Shield)", "tier": 2, "damage": 0.8, "speed_mod": -0.01, "value": 160,
        "desc": "Large round shield; iconic defense of the phalanx."},
    "corinthian_helmet_t2": {"name": "Corinthian Helmet", "tier": 2, "defense": 5.0, "speed_penalty": 0.03, "value": 140,
        "desc": "Full-face helmet; excellent protection, reduced vision."},
    "illyrian_helmet_t1": {"name": "Illyrian Helmet", "tier": 1, "defense": 3.0, "speed_penalty": 0.02, "value": 70,
        "desc": "Open-faced bronze helmet used across the Balkans."},
    "linothorax_t2": {"name": "Linothorax", "tier": 2, "defense": 10.0, "speed_penalty": 0.04, "value": 180,
        "desc": "Layered linen armor; flexible and fairly protective."},

    # 3) Ptolemaic Egypt — Khopesh, short spear, linen+bronze, ornate shields
    "ptolemaic_khopesh_t2": {"name": "Khopesh", "tier": 2, "damage": 1.5, "speed_mod": -0.03, "value": 210,
        "desc": "Curved Egyptian blade with ritual origins; deadly in trained hands."},
    "ptolemaic_spear_t1": {"name": "Egyptian Short Spear", "tier": 1, "damage": 1.1, "speed_mod": 0.0, "value": 55,
        "desc": "Short spear, easy to wield in close formations."},
    "ptolemaic_linen_bronze_t2": {"name": "Linen-Bronze Armor", "tier": 2, "defense": 11.0, "speed_penalty": 0.05, "value": 190,
        "desc": "Composite linen with bronze plates; ornate and functional."},

    # 4) Seleucid / Hellenistic Persia — Akinakes, curved sabre, composite bow, scale armor
    "seleucid_akinakes_t1": {"name": "Akinakes", "tier": 1, "damage": 1.0, "speed_mod": 0.02, "value": 65,
        "desc": "Short Persian sword; compact and quick."},
    "hellenic_sabre_t3": {"name": "Curved Sabre", "tier": 3, "damage": 1.8, "speed_mod": -0.06, "value": 500,
        "desc": "Long, slightly curved sabre; excels at slashing from horseback."},
    "composite_bow_t2": {"name": "Composite Bow", "tier": 2, "damage": 0.9, "speed_mod": 0.05, "value": 260,
        "desc": "Laminated bow with strong draw; deadly in skilled hands."},
    "scale_armor_t2": {"name": "Scale Armor", "tier": 2, "defense": 13.0, "speed_penalty": 0.06, "value": 230,
        "desc": "Layered metal scales; excellent protection, some encumbrance."},

    # 5) Roman Republic — Gladius Hispaniensis, pilum, scutum oval, Montefortino, lorica hamata
    "roman_gladius_t2": {"name": "Gladius Hispaniensis", "tier": 2, "damage": 1.6, "speed_mod": 0.0, "value": 230,
        "desc": "Early gladius variant, longer blade; formidable thrusts and cuts."},
    "roman_pilum_t2": {"name": "Pilum", "tier": 2, "damage": 1.2, "speed_mod": -0.03, "value": 150,
        "desc": "Heavy throwing spear; bends on impact to hinder foes."},
    "roman_scutum_t2": {"name": "Scutum (Oval)", "tier": 2, "damage": 0.85, "speed_mod": -0.01, "value": 170,
        "desc": "Early oval scutum; large coverage and impactful shield bash."},
    "montefortino_helmet_t2": {"name": "Montefortino Helmet", "tier": 2, "defense": 5.0, "speed_penalty": 0.03, "value": 150,
        "desc": "Roman bronze helmet; simple and reliable."},
    "lorica_hamata_t3": {"name": "Lorica Hamata", "tier": 3, "defense": 16.0, "speed_penalty": 0.08, "value": 360,
        "desc": "Mail armor; durable, excellent all-around protection."},

    # 6) Carthage — spears, short swords, scale cuirasses, oval shields, war elephants
    "carthage_spear_t2": {"name": "Carthaginian Long Spear", "tier": 2, "damage": 1.5, "speed_mod": -0.04, "value": 210,
        "desc": "Long spear common among Carthaginian infantry and mercenaries."},
    "carthage_shortsword_t1": {"name": "Carthaginian Short Sword", "tier": 1, "damage": 1.1, "speed_mod": 0.02, "value": 70,
        "desc": "Short blade influenced by Iberian designs."},
    "carthage_scale_t2": {"name": "Scaled Cuirass", "tier": 2, "defense": 12.0, "speed_penalty": 0.06, "value": 220,
        "desc": "Armor of overlapping metal scales; good protection for officers."},
    "carthage_oval_shield_t1": {"name": "Carthaginian Oval Shield", "tier": 1, "damage": 0.75, "speed_mod": 0.0, "value": 80,
        "desc": "Oval shield used across Punic armies and mercenaries."},

    # 7) Nubia (Kush) — longbow, short spear, light armor, gold adornments
    "kush_longbow_t2": {"name": "Nubian Longbow", "tier": 2, "damage": 1.0, "speed_mod": 0.05, "value": 240,
        "desc": "Powerful longbow famed along the Nile."},
    "kush_spear_t1": {"name": "Kushite Short Spear", "tier": 1, "damage": 1.1, "speed_mod": 0.0, "value": 60,
        "desc": "Light spear favored by swift skirmishers."},
    "kush_leather_t1": {"name": "Kushite Leather Armor", "tier": 1, "defense": 6.0, "speed_penalty": 0.03, "value": 120,
        "desc": "Light leather, allows rapid movement and raids."},

    # 8) Maurya — long spear, Indian composite bow, lamellar, war elephants
    "maurya_spear_t2": {"name": "Mauryan Long Spear", "tier": 2, "damage": 1.6, "speed_mod": -0.05, "value": 220,
        "desc": "Long infantry spear used by disciplined formations."},
    "maurya_composite_bow_t3": {"name": "Indian Composite Bow", "tier": 3, "damage": 1.1, "speed_mod": 0.06, "value": 520,
        "desc": "Advanced composite bow; high draw strength."},
    "lamellar_armor_t3": {"name": "Lamellar Armor", "tier": 3, "defense": 18.0, "speed_penalty": 0.10, "value": 420,
        "desc": "Plates laced together; excellent protection, quite heavy."},

    # 9) Pontus — kopis wide, light lances, dark bronze tunics, medium shields
    "pontic_kopis_t2": {"name": "Pontic Kopis", "tier": 2, "damage": 1.6, "speed_mod": -0.04, "value": 220,
        "desc": "Wide kopis suited for rugged mountain warfare."},
    "pontic_light_lance_t1": {"name": "Pontic Light Lance", "tier": 1, "damage": 1.2, "speed_mod": -0.02, "value": 75,
        "desc": "Light lance favored by Pontic cavalry."},
    "pontic_tunic_bronze_t1": {"name": "Reinforced Dark Bronze Tunic", "tier": 1, "defense": 7.0, "speed_penalty": 0.03, "value": 110,
        "desc": "Tunic with bronze reinforcements; practical and common."},

    # 10) Thrace / Illyria — rhomphaia, light axes, simple helmets
    "thracian_rhomphaia_t3": {"name": "Rhomphaia", "tier": 3, "damage": 2.2, "speed_mod": -0.10, "value": 560,
        "desc": "Long, curved blade; terrifying two-handed cutter."},
    "balkan_light_axe_t1": {"name": "Light Tribal Axe", "tier": 1, "damage": 1.2, "speed_mod": -0.02, "value": 65,
        "desc": "Simple axe; cheap, quick to swing."},
    "balkan_simple_helm_t1": {"name": "Simple Crest Helm", "tier": 1, "defense": 2.0, "speed_penalty": 0.01, "value": 45,
        "desc": "Basic metal cap with side crest; common among tribes."},

    # BANDITS — Popular simple weapons/armor (T1)
    "bandit_club": {"name": "Wooden Club", "tier": 1, "damage": 0.9, "speed_mod": 0.0, "value": 15,
        "desc": "A simple hardwood club favored by brigands."},
    "bandit_hand_axe": {"name": "Hand Axe", "tier": 1, "damage": 1.2, "speed_mod": -0.02, "value": 40,
        "desc": "Compact axe for chopping and fighting."},
    "bandit_short_spear": {"name": "Short Spear", "tier": 1, "damage": 1.1, "speed_mod": -0.01, "value": 35,
        "desc": "Short thrusting spear, common among raiders."},
    "bandit_dagger": {"name": "Leaf Dagger", "tier": 1, "damage": 0.9, "speed_mod": 0.05, "value": 20,
        "desc": "Short blade with leaf-shaped profile."},
    "bandit_sling": {"name": "Sling", "tier": 1, "damage": 0.7, "speed_mod": 0.05, "value": 10,
        "desc": "A strip of leather to hurl stones; cheap and deadly with skill."},
    "bandit_self_bow": {"name": "Self Bow", "tier": 1, "damage": 0.8, "speed_mod": 0.03, "value": 60,
        "desc": "Simple wooden bow made from a single stave."},
    "bandit_round_shield": {"name": "Wooden Round Shield", "tier": 1, "damage": 0.7, "speed_mod": 0.0, "value": 25,
        "desc": "Light round shield; can bash foes when needed."},
    "bandit_padded_cap": {"name": "Padded Cap", "tier": 1, "defense": 1.5, "speed_penalty": 0.01, "value": 15,
        "desc": "Quilted cap offering minimal protection."},
    "bandit_leather_vest": {"name": "Leather Vest", "tier": 1, "defense": 4.0, "speed_penalty": 0.02, "value": 60,
        "desc": "Plain leather vest; better than nothing."},
}


def get_item_by_id(item_id: str, with_random_quality: bool = False) -> Optional[Item]:
    """Get an item from the database by ID."""
    if item_id not in ITEM_DATABASE:
        return None

    data = ITEM_DATABASE[item_id]

    # Weapons
    if "damage" in data:
        if with_random_quality:
            return create_random_quality_weapon(
                data["name"], data["tier"], data["damage"],
                data["speed_mod"], data["value"], data.get("desc", "")
            )
        return create_weapon(
            data["name"], data["tier"], data["damage"],
            data["speed_mod"], data["value"], data.get("desc", "")
        )

    # Armor
    elif "defense" in data:
        if with_random_quality:
            return create_random_quality_armor(
                data["name"], data["tier"], data["defense"],
                data["speed_penalty"], data["value"], data.get("desc", "")
            )
        return create_armor(
            data["name"], data["tier"], data["defense"],
            data["speed_penalty"], data["value"], data.get("desc", "")
        )

    # Consumables
    else:
        return create_consumable(
            data["name"], data["value"], 1, data.get("desc", "")
        )
