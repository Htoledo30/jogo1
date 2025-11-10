"""Equipment system: weapons, armor, items."""

from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Optional
from . import items
from . import factions


@dataclass
class Weapon:
    """Weapon with stats and properties."""
    name: str
    weapon_type: str  # "sword", "axe", "spear", "bow", "shield"
    tier: int  # 1=Basic, 2=Advanced, 3=Master
    damage: float  # Base damage multiplier
    range: float  # Attack range in pixels
    cooldown: float  # Attack cooldown in seconds
    speed_mult: float  # Movement speed multiplier when equipped
    stamina_cost: float  # Stamina cost per attack
    value: int  # Gold cost
    damage_type: str = "slashing"  # "slashing", "piercing", "bludgeoning"

    def get_display_name(self) -> str:
        """Get display name with tier."""
        tier_names = {1: "Basic", 2: "Advanced", 3: "Master"}
        return f"{tier_names.get(self.tier, '')} {self.name}"


# WEAPON DATABASE (Balanced costs - T3 reduced ~40%)
WEAPONS = {
    # SWORDS - Balanced (SLASHING)
    "sword_1": Weapon("Sword", "sword", 1, 1.0, 30, 0.8, 1.0, 15, 50, "slashing"),
    "sword_2": Weapon("Longsword", "sword", 2, 1.4, 35, 0.75, 0.95, 18, 200, "slashing"),
    "sword_3": Weapon("Legendary Blade", "sword", 3, 2.0, 40, 0.7, 0.9, 20, 480, "slashing"),

    # AXES - High damage, slow, break block (SLASHING)
    "axe_1": Weapon("Axe", "axe", 1, 1.3, 25, 1.2, 0.9, 20, 60, "slashing"),
    "axe_2": Weapon("Battle Axe", "axe", 2, 1.8, 28, 1.1, 0.85, 25, 250, "slashing"),
    "axe_3": Weapon("Executioner's Axe", "axe", 3, 2.5, 30, 1.0, 0.8, 30, 600, "slashing"),

    # SPEARS - Long range (PIERCING)
    "spear_1": Weapon("Spear", "spear", 1, 0.9, 45, 1.0, 1.0, 12, 55, "piercing"),
    "spear_2": Weapon("Pike", "spear", 2, 1.3, 55, 0.95, 0.95, 15, 220, "piercing"),
    "spear_3": Weapon("Dragon Lance", "spear", 3, 1.8, 65, 0.9, 0.9, 18, 540, "piercing"),

    # BOWS - Ranged (PIERCING)
    "bow_1": Weapon("Bow", "bow", 1, 0.8, 200, 1.5, 1.0, 25, 70, "piercing"),
    "bow_2": Weapon("Longbow", "bow", 2, 1.2, 250, 1.3, 0.95, 30, 280, "piercing"),
    "bow_3": Weapon("Elven Bow", "bow", 3, 1.7, 300, 1.1, 0.9, 35, 660, "piercing"),

    # SHIELDS - Defensive (BLUDGEONING - bash attacks)
    "shield_1": Weapon("Shield", "shield", 1, 0.6, 20, 1.0, 0.85, 10, 45, "bludgeoning"),
    "shield_2": Weapon("Kite Shield", "shield", 2, 0.8, 22, 0.95, 0.8, 12, 180, "bludgeoning"),
    "shield_3": Weapon("Tower Shield", "shield", 3, 1.0, 25, 0.9, 0.75, 15, 450, "bludgeoning"),

    # --- 280 BC Additions ---
    # Macedon (PIERCING - long pikes)
    "sarissa_1": Weapon("Sarissa", "spear", 1, 1.4, 90, 1.1, 0.9, 18, 90, "piercing"),
    "sarissa_2": Weapon("Sarissa", "spear", 2, 1.7, 100, 1.2, 0.85, 22, 220, "piercing"),
    "sarissa_3": Weapon("Sarissa", "spear", 3, 2.0, 110, 1.3, 0.8, 26, 520, "piercing"),
    # Greek city-states
    "dory_1": Weapon("Dory Spear", "spear", 1, 1.3, 70, 1.0, 1.0, 15, 80, "piercing"),
    "dory_2": Weapon("Dory Spear", "spear", 2, 1.5, 75, 0.95, 0.95, 16, 200, "piercing"),
    "xiphos_1": Weapon("Xiphos", "sword", 1, 1.0, 35, 0.8, 1.05, 14, 60, "slashing"),
    "kopis_2": Weapon("Kopis", "sword", 2, 1.6, 38, 0.85, 0.95, 18, 210, "slashing"),
    "aspis_2": Weapon("Aspis Shield", "shield", 2, 0.8, 22, 1.0, 0.9, 10, 160, "bludgeoning"),
    # Ptolemaic Egypt
    "khopesh_2": Weapon("Khopesh", "sword", 2, 1.5, 36, 0.85, 0.95, 18, 210, "slashing"),
    "egypt_spear_1": Weapon("Egyptian Short Spear", "spear", 1, 1.1, 60, 1.0, 1.0, 12, 55, "piercing"),
    # Seleucid / Hellenistic Persia
    "akinakes_1": Weapon("Akinakes", "sword", 1, 1.0, 30, 0.75, 1.05, 12, 65, "slashing"),
    "sabre_3": Weapon("Curved Sabre", "sword", 3, 1.8, 40, 0.8, 0.95, 20, 500, "slashing"),
    "composite_bow_2": Weapon("Composite Bow", "bow", 2, 0.9, 260, 1.3, 1.0, 30, 260, "piercing"),
    # Rome (Republic)
    "gladius_2": Weapon("Gladius Hispaniensis", "sword", 2, 1.6, 35, 0.8, 1.0, 16, 230, "slashing"),
    "pilum_2": Weapon("Pilum", "spear", 2, 1.2, 80, 1.2, 0.95, 20, 150, "piercing"),
    "scutum_2": Weapon("Scutum (Oval)", "shield", 2, 0.85, 24, 1.0, 0.9, 12, 170, "bludgeoning"),
    # Carthage
    "carth_spear_2": Weapon("Carthaginian Long Spear", "spear", 2, 1.5, 85, 1.1, 0.95, 18, 210, "piercing"),
    "carth_shortsword_1": Weapon("Carthaginian Short Sword", "sword", 1, 1.1, 30, 0.75, 1.05, 12, 70, "slashing"),
    "carth_oval_1": Weapon("Carthaginian Oval Shield", "shield", 1, 0.75, 22, 1.0, 0.95, 10, 80, "bludgeoning"),
    # Nubia (Kush)
    "kush_longbow_2": Weapon("Nubian Longbow", "bow", 2, 1.0, 280, 1.35, 1.05, 28, 240, "piercing"),
    "kush_spear_1": Weapon("Kushite Short Spear", "spear", 1, 1.1, 65, 1.0, 1.0, 12, 60, "piercing"),
    # Maurya
    "maurya_spear_2": Weapon("Mauryan Long Spear", "spear", 2, 1.6, 90, 1.15, 0.95, 20, 220, "piercing"),
    "indian_composite_3": Weapon("Indian Composite Bow", "bow", 3, 1.1, 300, 1.4, 1.05, 32, 520, "piercing"),
    # Pontus
    "pontic_kopis_2": Weapon("Pontic Kopis", "sword", 2, 1.6, 36, 0.85, 0.95, 18, 220, "slashing"),
    "pontic_lance_1": Weapon("Pontic Light Lance", "spear", 1, 1.2, 70, 1.05, 1.0, 14, 75, "piercing"),
    # Thrace / Illyria
    "rhomphaia_3": Weapon("Rhomphaia", "sword", 3, 2.2, 55, 0.9, 0.9, 26, 560, "slashing"),
    "light_axe_1": Weapon("Light Tribal Axe", "axe", 1, 1.2, 28, 0.9, 1.0, 14, 65, "slashing"),

    # Mythic/Beast weapons
    "sabertooth_claws": Weapon("Sabertooth Claws", "sword", 3, 1.8, 34, 0.65, 1.06, 12, 600, "slashing"),
}


def get_weapon(weapon_id: str) -> Optional[Weapon]:
    """Get weapon by ID."""
    return WEAPONS.get(weapon_id)


def get_weapons_by_type(weapon_type: str) -> list[Weapon]:
    """Get all weapons of a type."""
    return [w for w in WEAPONS.values() if w.weapon_type == weapon_type]


def get_weapons_by_tier(tier: int) -> list[Weapon]:
    """Get all weapons of a tier."""
    return [w for w in WEAPONS.values() if w.tier == tier]


def get_starter_weapon() -> Weapon:
    """Get default starting weapon."""
    return WEAPONS["sword_1"]


@dataclass
class Armor:
    """Armor piece."""
    name: str
    armor_type: str  # "helmet", "chest", "legs", "boots"
    tier: int
    defense: float  # Damage reduction %
    speed_penalty: float  # Speed reduction
    value: int
    material: str = "leather"  # "leather", "bronze", "chainmail", "plate"

    def get_display_name(self) -> str:
        tier_names = {1: "Leather", 2: "Chainmail", 3: "Plate"}
        return f"{tier_names.get(self.tier, '')} {self.name}"


# ARMOR DATABASE (Balanced costs - T3 reduced ~40%)
ARMORS = {
    # HELMETS
    "helm_1": Armor("Helmet", "helmet", 1, 0.05, 0.0, 30, "leather"),
    "helm_2": Armor("Helmet", "helmet", 2, 0.10, 0.02, 120, "chainmail"),
    "helm_3": Armor("Helmet", "helmet", 3, 0.15, 0.05, 300, "plate"),

    # CHEST
    "chest_1": Armor("Armor", "chest", 1, 0.10, 0.05, 50, "leather"),
    "chest_2": Armor("Armor", "chest", 2, 0.20, 0.10, 200, "chainmail"),
    "chest_3": Armor("Armor", "chest", 3, 0.30, 0.15, 480, "plate"),

    # LEGS
    "legs_1": Armor("Leggings", "legs", 1, 0.05, 0.03, 35, "leather"),
    "legs_2": Armor("Leggings", "legs", 2, 0.10, 0.06, 150, "chainmail"),
    "legs_3": Armor("Leggings", "legs", 3, 0.15, 0.10, 360, "plate"),

    # BOOTS
    "boots_1": Armor("Boots", "boots", 1, 0.03, 0.02, 25, "leather"),
    "boots_2": Armor("Boots", "boots", 2, 0.06, 0.04, 100, "chainmail"),
    "boots_3": Armor("Boots", "boots", 3, 0.10, 0.06, 240, "plate"),

    # --- 280 BC Additions ---
    # Helmets
    "phrygian_helm_1": Armor("Phrygian Helmet", "helmet", 1, 0.06, 0.01, 35, "leather"),
    "corinthian_helm_2": Armor("Corinthian Helmet", "helmet", 2, 0.12, 0.03, 140, "bronze"),
    "illyrian_helm_1": Armor("Illyrian Helmet", "helmet", 1, 0.08, 0.02, 70, "bronze"),
    "montefortino_helm_2": Armor("Montefortino Helmet", "helmet", 2, 0.12, 0.03, 150, "bronze"),
    "balkan_simple_helm_1": Armor("Simple Crest Helm", "helmet", 1, 0.06, 0.01, 45, "leather"),

    # Chest
    "muscled_cuirass_2": Armor("Muscled Bronze Cuirass", "chest", 2, 0.20, 0.06, 220, "bronze"),
    "linothorax_2": Armor("Linothorax", "chest", 2, 0.18, 0.04, 180, "leather"),
    "lorica_hamata_3": Armor("Lorica Hamata", "chest", 3, 0.26, 0.08, 360, "chainmail"),
    "scale_armor_2": Armor("Scale Armor", "chest", 2, 0.22, 0.06, 230, "bronze"),
    "lamellar_armor_3": Armor("Lamellar Armor", "chest", 3, 0.30, 0.10, 420, "chainmail"),

    # Mythic/Beast armors
    "hydra_scale_mail": Armor("Hydra Scale Mail", "chest", 3, 0.28, 0.06, 900, "chainmail"),
    "nemean_lion_hide": Armor("Nemean Lion Hide", "chest", 3, 0.24, 0.02, 850, "leather"),
}


def get_armor(armor_id: str) -> Optional[Armor]:
    """Get armor by ID."""
    return ARMORS.get(armor_id)


def get_starter_armor() -> dict[str, str]:
    """Get default starting armor set."""
    return {
        "helmet": "helm_1",
        "chest": "chest_1",
        "legs": "legs_1",
        "boots": "boots_1"
    }


@dataclass
class Equipment:
    """Player equipment loadout."""
    weapon: str = "sword_1"  # Weapon ID
    helmet: str = "helm_1"
    chest: str = "chest_1"
    legs: str = "legs_1"
    boots: str = "boots_1"

    def get_weapon(self) -> Weapon:
        """Get equipped weapon."""
        return get_weapon(self.weapon) or get_starter_weapon()

    def get_total_defense(self) -> float:
        """Calculate total defense from armor."""
        total = 0.0
        for armor_id in [self.helmet, self.chest, self.legs, self.boots]:
            armor = get_armor(armor_id)
            if armor:
                total += armor.defense
        return min(0.75, total)  # Cap at 75%

    def get_speed_penalty(self) -> float:
        """Calculate total speed penalty from armor."""
        total = 0.0
        for armor_id in [self.helmet, self.chest, self.legs, self.boots]:
            armor = get_armor(armor_id)
            if armor:
                total += armor.speed_penalty
        return total

    def get_total_value(self) -> int:
        """Get total gold value of equipment."""
        total = 0
        weapon = self.get_weapon()
        if weapon:
            total += weapon.value
        for armor_id in [self.helmet, self.chest, self.legs, self.boots]:
            armor = get_armor(armor_id)
            if armor:
                total += armor.value
        return total

    def get_primary_material(self) -> str:
        """Get the dominant armor material (for damage type effectiveness).

        Priority: chest > helmet > legs > boots (chest is most important).
        Returns: "leather", "bronze", "chainmail", or "plate"
        """
        # Check chest first (most important piece)
        chest_armor = get_armor(self.chest)
        if chest_armor and chest_armor.material:
            return chest_armor.material

        # Fallback to helmet
        helmet_armor = get_armor(self.helmet)
        if helmet_armor and helmet_armor.material:
            return helmet_armor.material

        # Fallback to legs
        legs_armor = get_armor(self.legs)
        if legs_armor and legs_armor.material:
            return legs_armor.material

        # Final fallback to boots or default
        boots_armor = get_armor(self.boots)
        if boots_armor and boots_armor.material:
            return boots_armor.material

        return "leather"  # Default


def get_item(item_id: str) -> Optional[items.Item]:
    """Get any item (weapon or armor) by its ID."""
    return items.get_item_by_id(item_id)


def get_all_items() -> dict[str, items.Item]:
    """Get a dictionary of all items in the game."""
    return {**WEAPONS, **ARMORS}


# === Comparison helpers ===
def _infer_armor_slot_from_name(name: str) -> Optional[str]:
    n = (name or "").lower()
    if any(k in n for k in ("helm", "helmet")):
        return "helmet"
    if any(k in n for k in ("cuirass", "armor", "linothorax", "lorica", "scale", "lamellar", "chest")):
        return "chest"
    if any(k in n for k in ("leg", "greave")):
        return "legs"
    if any(k in n for k in ("boot", "sandal")):
        return "boots"
    return None


def get_equipped_item_for_comparison(player, candidate_item: items.Item) -> tuple[str, dict]:
    """Return (equipped_name, stats_dict) for the slot relevant to candidate_item.

    stats_dict keys: 'damage', 'defense', 'speed_modifier'. Values may be None when not applicable.
    """
    equipped_name = "None"
    stats = {"damage": None, "defense": None, "speed_modifier": None}
    eq = getattr(player, 'equipment', None)
    if not eq:
        return equipped_name, stats

    try:
        if candidate_item.item_type.name == 'WEAPON' or candidate_item.damage is not None:
            w = eq.get_weapon()
            if w:
                equipped_name = w.get_display_name() if hasattr(w, 'get_display_name') else getattr(w, 'name', 'Weapon')
                stats["damage"] = float(getattr(w, 'damage', 1.0))
                # Map weapon speed_mult (e.g., 0.9..1.1) to an item-like speed_modifier (delta from 1.0)
                stats["speed_modifier"] = float(getattr(w, 'speed_mult', 1.0)) - 1.0
            return equipped_name, stats

        # Armor path: infer slot from name
        slot = _infer_armor_slot_from_name(getattr(candidate_item, 'name', ''))
        armor_id = None
        if slot == 'helmet':
            armor_id = eq.helmet
        elif slot == 'chest':
            armor_id = eq.chest
        elif slot == 'legs':
            armor_id = eq.legs
        elif slot == 'boots':
            armor_id = eq.boots

        if armor_id:
            ar = get_armor(armor_id)
            if ar:
                equipped_name = ar.get_display_name() if hasattr(ar, 'get_display_name') else getattr(ar, 'name', 'Armor')
                stats["defense"] = float(getattr(ar, 'defense', 0.0))
                # Items store speed_modifier negative for penalty; map speed_penalty to -value
                stats["speed_modifier"] = -float(getattr(ar, 'speed_penalty', 0.0))
        return equipped_name, stats
    except Exception:
        return equipped_name, stats


def get_item_name(item_id: str) -> str:
    """Get the display name of any item."""
    item = get_item(item_id)
    return item.get_display_name() if item else "Unknown Item"


def equip_item(player, item_to_equip: items.Item):
    """Equip an Item from the player's inventory, bridging to Equipment IDs.

    Detects historical items by name and maps them to matching weapon/armor IDs
    added in this module. Falls back to generic sword/helm mappings by tier.
    """
    if not item_to_equip or not player or not getattr(player, "equipment", None):
        return

    # Legacy->Item mappings for unequip returns
    item_id_from_weapon = {
        "sword_1": "basic_sword", "sword_2": "longsword", "sword_3": "legendary_blade",
        "sarissa_1": "macedon_sarissa_t1", "sarissa_2": "macedon_sarissa_t2", "sarissa_3": "macedon_sarissa_t3",
        "dory_1": "greek_dory_t1", "dory_2": "greek_dory_t2",
        "xiphos_1": "greek_xiphos_t1", "kopis_2": "greek_kopis_t2",
        "aspis_2": "aspis_shield_t2", "pelte_shield_1": "pelte_shield_t1",
        "khopesh_2": "ptolemaic_khopesh_t2", "egypt_spear_1": "ptolemaic_spear_t1",
        "akinakes_1": "seleucid_akinakes_t1", "sabre_3": "hellenic_sabre_t3", "composite_bow_2": "composite_bow_t2",
        "gladius_2": "roman_gladius_t2", "pilum_2": "roman_pilum_t2", "scutum_2": "roman_scutum_t2",
        "carth_spear_2": "carthage_spear_t2", "carth_shortsword_1": "carthage_shortsword_t1",
        "carth_oval_1": "carthage_oval_shield_t1", "carth_scale_2": "carthage_scale_t2",
        "kush_longbow_2": "kush_longbow_t2", "kush_spear_1": "kush_spear_t1",
        "maurya_spear_2": "maurya_spear_t2", "indian_composite_3": "maurya_composite_bow_t3",
        "pontic_kopis_2": "pontic_kopis_t2", "pontic_lance_1": "pontic_light_lance_t1",
        "rhomphaia_3": "thracian_rhomphaia_t3", "light_axe_1": "balkan_light_axe_t1",
        # Legendary monster weapons
        "cyclops_club": "cyclops_club",
        "minotaur_labrys": "minotaur_labrys",
        "boar_tusk_spear": "boar_tusk_spear",
        "sabertooth_claws": "sabertooth_claws",
        "centaur_lance": "centaur_lance",
    }

    item_id_from_armor = {
        # Basic helmets
        "helm_1": "leather_helmet", "helm_2": "chainmail_helmet", "helm_3": "plate_helmet",
        # Basic chest pieces
        "chest_1": "leather_armor", "chest_2": "chainmail_armor", "chest_3": "plate_armor",
        # Basic legs
        "legs_1": "leather_leggings", "legs_2": "chainmail_leggings", "legs_3": "plate_leggings",
        # Basic boots
        "boots_1": "leather_boots", "boots_2": "chainmail_boots", "boots_3": "plate_boots",
        # Faction helmets
        "phrygian_helm_1": "phrygian_helmet_t1",
        "corinthian_helm_2": "corinthian_helmet_t2",
        "illyrian_helm_1": "illyrian_helmet_t1",
        "montefortino_helm_2": "montefortino_helmet_t2",
        "balkan_simple_helm_1": "balkan_simple_helm_t1",
        # Faction chest pieces
        "muscled_cuirass_2": "muscled_cuirass_t2",
        "linothorax_2": "linothorax_t2",
        "lorica_hamata_3": "lorica_hamata_t3",
        "scale_armor_2": "scale_armor_t2",
        "lamellar_armor_3": "lamellar_armor_t3",
        "ptolemaic_linen_bronze_2": "ptolemaic_linen_bronze_t2",
        "kush_leather_1": "kush_leather_t1",
        "pontic_tunic_bronze_1": "pontic_tunic_bronze_t1",
        # Legendary monster armors
        "dire_wolf_pelt": "dire_wolf_pelt",
        "hydra_scale_mail": "hydra_scale_mail",
        "nemean_lion_hide": "nemean_lion_hide",
        "harpy_feather_cloak": "harpy_feather_cloak",
        "gorgon_visor": "gorgon_visor",
    }

    def _infer_weapon_id_from_item(it: items.Item) -> str:
        name = getattr(it, "name", "").lower()
        tier = max(1, min(3, getattr(it, "tier", 1)))
        # Bandit/simple weapons mapping
        if "wooden round shield" in name or ("round" in name and "shield" in name):
            return "shield_1"
        if "wooden club" in name or "club" in name:
            return "axe_1"  # club approximated by axe profile
        if "hand axe" in name:
            return "axe_1"
        if "leaf dagger" in name or "dagger" in name:
            return "sword_1"
        if "short spear" in name:
            return "spear_1"
        if "self bow" in name or ("bow" in name and tier == 1):
            return "bow_1"
        if "sling" in name:
            return "bow_1"  # sling approximated by primitive ranged
        if "sarissa" in name: return f"sarissa_{tier}"
        if "dory" in name: return f"dory_{min(2, tier)}"
        if "xiphos" in name: return "xiphos_1"
        if "kopis" in name: return "kopis_2"
        if "aspis" in name: return "aspis_2"
        if "khopesh" in name: return "khopesh_2"
        if "akinakes" in name: return "akinakes_1"
        if "sabre" in name: return "sabre_3"
        if "composite bow" in name or "bow" in name: return "composite_bow_2" if tier <= 2 else "indian_composite_3"
        if "gladius" in name: return "gladius_2"
        if "pilum" in name: return "pilum_2"
        if "scutum" in name: return "scutum_2"
        if "carthaginian long spear" in name: return "carth_spear_2"
        if "oval shield" in name and "carthaginian" in name: return "carth_oval_1"
        if "nubian longbow" in name: return "kush_longbow_2"
        if "kushite short spear" in name: return "kush_spear_1"
        if "mauryan long spear" in name: return "maurya_spear_2"
        if "indian composite" in name: return "indian_composite_3"
        if "pontic kopis" in name: return "pontic_kopis_2"
        if "pontic light lance" in name: return "pontic_lance_1"
        if "rhomphaia" in name: return "rhomphaia_3"
        if "axe" in name: return "light_axe_1"
        # Legendary monster weapons
        if "cyclops" in name and "club" in name: return "cyclops_club"
        if "minotaur" in name and "labrys" in name: return "minotaur_labrys"
        if "boar" in name and "tusk" in name: return "boar_tusk_spear"
        if "sabertooth" in name and "claw" in name: return "sabertooth_claws"
        if "centaur" in name and "lance" in name: return "centaur_lance"
        # Fallback generic
        return {1: "sword_1", 2: "sword_2", 3: "sword_3"}[tier]

    def _infer_armor_slot_and_id_from_item(it: items.Item) -> tuple[str, str]:
        name = getattr(it, "name", "").lower()
        tier = max(1, min(3, getattr(it, "tier", 1)))
        # Legendary monster armors
        if "dire wolf" in name and "pelt" in name: return ("chest", "dire_wolf_pelt")
        if "hydra" in name and "scale" in name: return ("chest", "hydra_scale_mail")
        if "nemean" in name and "lion" in name: return ("chest", "nemean_lion_hide")
        if "harpy" in name and "feather" in name: return ("chest", "harpy_feather_cloak")
        if "gorgon" in name and "visor" in name: return ("helmet", "gorgon_visor")
        # Regular armors
        if any(k in name for k in ["helmet", "helm", "corinth", "phryg", "illyr", "montefortino", "crest"]):
            if "corinth" in name: return ("helmet", "corinthian_helm_2")
            if "phryg" in name: return ("helmet", "phrygian_helm_1")
            if "illyr" in name: return ("helmet", "illyrian_helm_1")
            if "montefortino" in name: return ("helmet", "montefortino_helm_2")
            return ("helmet", "balkan_simple_helm_1")
        if any(k in name for k in ["lorica", "hamata", "linothorax", "cuirass", "scale armor", "lamellar", "armor"]):
            if "lorica" in name or "hamata" in name: return ("chest", "lorica_hamata_3")
            if "linothorax" in name: return ("chest", "linothorax_2")
            if "muscled" in name or "cuirass" in name: return ("chest", "muscled_cuirass_2")
            if "lamellar" in name: return ("chest", "lamellar_armor_3")
            if "scale" in name: return ("chest", "scale_armor_2")
            return ("chest", "chest_2")
        return ("chest", {1: "chest_1", 2: "chest_2", 3: "chest_3"}[tier])

    try:
        if item_to_equip.item_type == items.ItemType.WEAPON:
            new_weapon_id = _infer_weapon_id_from_item(item_to_equip)

            # Validate that weapon ID exists
            if get_weapon(new_weapon_id) is None:
                from . import logger
                logger.warning(f"Invalid weapon ID: {new_weapon_id}")
                return  # Don't equip invalid weapon

            prev_weapon_id = getattr(player.equipment, "weapon", None)
            if prev_weapon_id and prev_weapon_id in item_id_from_weapon:
                prev_item = items.get_item_by_id(item_id_from_weapon[prev_weapon_id])
                if prev_item:
                    player.inventory.append(prev_item)

            setattr(player.equipment, "weapon", new_weapon_id)
            if item_to_equip in player.inventory:
                player.inventory.remove(item_to_equip)

        elif item_to_equip.item_type == items.ItemType.ARMOR:
            slot, target_armor_id = _infer_armor_slot_and_id_from_item(item_to_equip)

            # Validate that armor ID exists
            if get_armor(target_armor_id) is None:
                from . import logger
                logger.warning(f"Invalid armor ID: {target_armor_id}")
                return  # Don't equip invalid armor

            prev_armor_id = getattr(player.equipment, slot, None)
            if prev_armor_id:
                prev_item_id = item_id_from_armor.get(prev_armor_id)
                if prev_item_id:
                    prev_item = items.get_item_by_id(prev_item_id)
                    if prev_item:
                        player.inventory.append(prev_item)

            setattr(player.equipment, slot, target_armor_id)
            if item_to_equip in player.inventory:
                player.inventory.remove(item_to_equip)
    except Exception:
        # Fail silently to avoid crashing the game; caller may surface a notification
        pass


def get_random_shop_inventory(num_items=5, faction_id: str | None = None) -> list[items.Item]:
    """Generate a random list of items for the shop.

    If faction_id is provided, uses `factions.roll_shop_items`.
    """
    if faction_id:
        rolled = factions.roll_shop_items(faction_id, n=num_items)
        # Pad to grid size if needed by UI caller
        return rolled

    # Fallback: generic pool (previous behavior)
    shop_inventory: list[items.Item] = []

    possible_weapons = [k for k, v in items.ITEM_DATABASE.items() if "damage" in v and v.get("tier", 1) <= 2]
    possible_armors = [k for k, v in items.ITEM_DATABASE.items() if "defense" in v and v.get("tier", 1) <= 2]

    num_weapons = random.randint(2, 3)
    num_armors = max(0, num_items - num_weapons)

    if possible_weapons:
        for item_id in random.sample(possible_weapons, min(num_weapons, len(possible_weapons))):
            shop_inventory.append(items.get_item_by_id(item_id, with_random_quality=True))
    if possible_armors:
        for item_id in random.sample(possible_armors, min(num_armors, len(possible_armors))):
            shop_inventory.append(items.get_item_by_id(item_id, with_random_quality=True))

    return shop_inventory
