"""
Shop screen UI for buying equipment.

Displays faction-themed shop with equipment items for purchase.
"""

import pygame
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT
from .. import equipment as equip_mod
from .. import factions as factions_mod


# Shop state storage (attached to function to persist between calls)
_shop_items = None


def draw_shop_screen(screen, player, events, current_faction_id, show_notification_callback):
    """
    Draw the shop screen with faction-themed items.

    Args:
        screen: Pygame screen surface
        player: Player entity
        events: List of pygame events
        current_faction_id: Current faction ID for themed shop
        show_notification_callback: Function to show notifications

    Returns:
        str: Next state ("OVERWORLD" if exiting, "SHOP_MENU" to stay)
    """
    global _shop_items

    screen.fill((28, 18, 18))
    font_title = pygame.font.Font(None, 48)
    font_faction = pygame.font.Font(None, 32)
    font_item = pygame.font.Font(None, 28)
    font_gold = pygame.font.Font(None, 24)

    # Get faction info for visual preview
    faction_data = factions_mod.FACTIONS.get(current_faction_id, {})
    faction_name = faction_data.get("name", "Unknown Faction")
    faction_icon = faction_data.get("icon", "🏛️")
    faction_palette = faction_data.get("palette", {})
    faction_primary = faction_palette.get("primary", (200, 180, 100))
    faction_accent = faction_palette.get("accent", (150, 130, 80))

    # Title with faction info
    title_surf = font_title.render("Equipment Shop", True, (255, 255, 255))
    screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40)))

    # Faction banner below title
    faction_banner = f"{faction_icon}  {faction_name}  {faction_icon}"
    faction_surf = font_faction.render(faction_banner, True, faction_primary)
    faction_rect = faction_surf.get_rect(center=(SCREEN_WIDTH // 2, 85))

    # Draw faction background panel
    panel_rect = pygame.Rect(faction_rect.x - 20, faction_rect.y - 10, faction_rect.width + 40, faction_rect.height + 20)
    pygame.draw.rect(screen, faction_accent, panel_rect, border_radius=10)
    pygame.draw.rect(screen, faction_primary, panel_rect, 3, border_radius=10)
    screen.blit(faction_surf, faction_rect)

    # Gold display
    gold_text = f"Your Gold: {player.stats.gold}"
    screen.blit(font_gold.render(gold_text, True, (255, 215, 0)), (SCREEN_WIDTH - 250, 30))

    # Shop items (generate a random list if not present)
    if _shop_items is None:
        # Use faction-themed inventory based on current_faction_id
        try:
            _shop_items = equip_mod.get_random_shop_inventory(12, faction_id=current_faction_id)
        except Exception:
            _shop_items = equip_mod.get_random_shop_inventory()

    shop_items = _shop_items
    item_y = 120
    for i, item in enumerate(shop_items):
        if not item:
            continue

        item_text = f"{i+1}. {item.get_display_name()} - {item.get_value()} Gold"
        screen.blit(font_item.render(item_text, True, (220, 220, 220)), (100, item_y + i * 40))

    # Instructions
    instr_text = "Press a number key to buy. Press 'ESC' to exit."
    screen.blit(font_gold.render(instr_text, True, (180, 180, 180)), (50, SCREEN_HEIGHT - 50))

    # Handle input
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Reset shop inventory for next visit
                _shop_items = None
                return "OVERWORLD"

            if pygame.K_1 <= event.key <= pygame.K_9:
                item_index = event.key - pygame.K_1
                if item_index < len(shop_items):
                    item_to_buy = shop_items[item_index]

                    if player.stats.gold >= item_to_buy.get_value():
                        if len(player.inventory) < 20:
                            player.stats.gold -= item_to_buy.get_value()
                            player.inventory.append(item_to_buy)
                            show_notification_callback(screen, f"Bought: {item_to_buy.get_display_name()}")
                            # Remove from shop
                            shop_items.pop(item_index)
                        else:
                            show_notification_callback(screen, "Inventory full!", color=(255, 100, 100))
                    else:
                        show_notification_callback(screen, "Not enough gold!", color=(255, 100, 100))

    return "SHOP_MENU"  # Stay in this state unless changed


def reset_shop():
    """Reset shop inventory (call when player leaves shop)."""
    global _shop_items
    _shop_items = None
