"""
Bridge between old equipment system and new item system.

Converts between equipment.py objects and items.py objects for compatibility.
"""

from . import equipment as equip_mod
from . import items
from typing import List


def convert_equipment_to_item(equipment_obj) -> items.Item:
    """Convert old Equipment/Weapon/Armor to new Item."""
    if isinstance(equipment_obj, equip_mod.Weapon):
        # Map equipment.Weapon fields to Items weapon fields
        return items.create_weapon(
            name=equipment_obj.name,
            tier=equipment_obj.tier,
            damage=equipment_obj.damage,
            speed_mod=equipment_obj.speed_mult,
            base_value=equipment_obj.value,
            description=f"A tier {equipment_obj.tier} weapon.",
            quality=items.ItemQuality.NORMAL
        )
    elif isinstance(equipment_obj, equip_mod.Armor):
        return items.create_armor(
            name=equipment_obj.name,
            tier=equipment_obj.tier,
            defense=equipment_obj.defense,
            speed_penalty=equipment_obj.speed_penalty,
            base_value=equipment_obj.value,
            description=f"A tier {equipment_obj.tier} armor piece.",
            quality=items.ItemQuality.NORMAL
        )
    else:
        # Fallback
        return items.Item(
            name=str(equipment_obj),
            item_type=items.ItemType.WEAPON,
            base_value=10,
            weight=1.0
        )


def convert_inventory_to_items(old_inventory: List) -> List[items.Item]:
    """Convert old inventory list to new Item objects."""
    new_inventory = []
    for item in old_inventory:
        if item:
            new_inventory.append(convert_equipment_to_item(item))
        else:
            new_inventory.append(None)

    # Pad to 20 slots
    while len(new_inventory) < 20:
        new_inventory.append(None)

    return new_inventory


def create_shop_inventory(tier: int = 2) -> List[items.Item]:
    """Create a shop inventory with items."""
    shop_items = []

    # Add some weapons
    shop_items.append(items.get_item_by_id("basic_sword", with_random_quality=True))
    shop_items.append(items.get_item_by_id("longsword", with_random_quality=True))

    # Add some armor
    shop_items.append(items.get_item_by_id("leather_helmet", with_random_quality=True))
    shop_items.append(items.get_item_by_id("chainmail_helmet", with_random_quality=True))

    # Add consumables
    shop_items.append(items.get_item_by_id("bandage"))
    shop_items.append(items.get_item_by_id("health_potion"))

    # Pad to 12 slots
    while len(shop_items) < 12:
        shop_items.append(None)

    return shop_items


def get_equipped_summary(equipment_obj) -> dict:
    """Get summary of equipped items for display."""
    from . import equipment as equip_mod

    weapon = equipment_obj.get_weapon()
    helmet = equip_mod.get_armor(equipment_obj.helmet)
    chest = equip_mod.get_armor(equipment_obj.chest)
    legs = equip_mod.get_armor(equipment_obj.legs)
    boots = equip_mod.get_armor(equipment_obj.boots)

    return {
        "weapon": weapon.name if weapon else "None",
        "helmet": helmet.name if helmet else "None",
        "chest": chest.name if chest else "None",
        "legs": legs.name if legs else "None",
        "boots": boots.name if boots else "None",
    }
