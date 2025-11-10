"""
Modern Shop UI with Buy/Sell functionality.

Features:
- Buy tab and Sell tab
- Grid layout for items
- Shop keeper gold limit
- Persistent shop inventory
"""

import pygame
from typing import List, Optional
from . import items
from . import ui_components as ui


class ShopUI:
    """Modern shop interface with buy/sell functionality."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Main panel
        self.panel = ui.Panel(50, 50, screen_width - 100, screen_height - 100,
                              "SHOP", ui.UIColors.PANEL_BORDER)

        # Tab buttons
        self.buy_tab = ui.Button(70, 90, 100, 35, "BUY", font_size=20)
        self.sell_tab = ui.Button(180, 90, 100, 35, "SELL", font_size=20)

        # Shop stock grid (left)
        self.shop_grid = ui.Grid(70, 150, cols=4, rows=3, cell_size=60, spacing=6)

        # Player inventory grid (right)
        self.player_grid = ui.Grid(screen_width - 370, 150, cols=4, rows=3, cell_size=60, spacing=6)

        # Item info panel (center)
        self.info_panel = ui.Panel(380, 150, 280, 250, "Item Info")

        # Gold displays
        self.gold_bar_shop = ui.ProgressBar(70, 420, 270, 25, 1000, 500, "Shop Gold")
        self.gold_bar_player = ui.ProgressBar(screen_width - 370, 420, 270, 25, 0, 0, "Your Gold")

        # Action buttons
        button_y = screen_height - 130
        self.buy_btn = ui.Button(380, button_y, 120, 35, "Buy Item", font_size=18)
        self.sell_btn = ui.Button(510, button_y, 120, 35, "Sell Item", font_size=18)
        self.close_btn = ui.Button(640, button_y, 100, 35, "Close", font_size=18)

        # State
        self.current_tab = "buy"  # "buy" or "sell"
        self.selected_shop_item: Optional[int] = None
        self.selected_player_item: Optional[int] = None
        self.should_close = False

    def update(self, events: List[pygame.event.Event], mouse_pos: tuple,
               shop_inventory: List, player_inventory: List,
               player_gold: int, shop_gold: int):
        """Update shop UI state."""
        self.should_close = False

        # Tab switching
        def switch_to_buy():
            self.current_tab = "buy"
            self.selected_shop_item = None
            self.selected_player_item = None

        def switch_to_sell():
            self.current_tab = "sell"
            self.selected_shop_item = None
            self.selected_player_item = None

        self.buy_tab.callback = switch_to_buy
        self.sell_tab.callback = switch_to_sell
        self.buy_tab.update(events, mouse_pos)
        self.sell_tab.update(events, mouse_pos)

        # Grid selection
        if self.current_tab == "buy":
            hovered_shop = self.shop_grid.get_hovered_index(mouse_pos)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hovered_shop is not None and hovered_shop < len(shop_inventory):
                        if shop_inventory[hovered_shop]:
                            self.selected_shop_item = hovered_shop
        else:  # sell
            hovered_player = self.player_grid.get_hovered_index(mouse_pos)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if hovered_player is not None and hovered_player < len(player_inventory):
                        if player_inventory[hovered_player]:
                            self.selected_player_item = hovered_player

        # Close button
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.should_close = True

        def on_close():
            self.should_close = True

        self.close_btn.callback = on_close
        self.close_btn.update(events, mouse_pos)

        # Buy/Sell buttons - handled externally
        self.buy_btn.enabled = (self.current_tab == "buy" and
                               self.selected_shop_item is not None and
                               self.selected_shop_item < len(shop_inventory) and
                               shop_inventory[self.selected_shop_item] is not None)

        self.sell_btn.enabled = (self.current_tab == "sell" and
                                self.selected_player_item is not None and
                                self.selected_player_item < len(player_inventory) and
                                player_inventory[self.selected_player_item] is not None)

        self.buy_btn.update(events, mouse_pos)
        self.sell_btn.update(events, mouse_pos)

    def render(self, screen: pygame.Surface, shop_inventory: List,
               player_inventory: List, player_gold: int, shop_gold: int,
               mouse_pos: tuple, player: Optional[object] = None):
        """Render shop UI."""
        # Main panel
        self.panel.render(screen)

        # Tabs
        self.buy_tab.render(screen)
        self.sell_tab.render(screen)

        # Highlight active tab
        if self.current_tab == "buy":
            pygame.draw.rect(screen, ui.UIColors.TEXT_HIGHLIGHT,
                           (70, 90, 100, 35), 3, border_radius=4)
        else:
            pygame.draw.rect(screen, ui.UIColors.TEXT_HIGHLIGHT,
                           (180, 90, 100, 35), 3, border_radius=4)

        # Shop GOLD highlight (top-left)
        font_gold = pygame.font.Font(None, 28)
        gold_text = font_gold.render(f"SHOP GOLD: {int(shop_gold)}g", True, ui.UIColors.TEXT_HIGHLIGHT)
        screen.blit(gold_text, (70, 60))

        # Shop stock grid
        self.shop_grid.render(screen, shop_inventory, mouse_pos)
        font = pygame.font.Font(None, 18)
        label = font.render("Shop Stock:", True, ui.UIColors.TEXT_SECONDARY)
        screen.blit(label, (70, 130))

        # Player inventory grid
        self.player_grid.render(screen, player_inventory, mouse_pos)
        label = font.render("Your Items:", True, ui.UIColors.TEXT_SECONDARY)
        screen.blit(label, (self.screen_width - 370, 130))

        # Item info panel
        self.info_panel.render(screen)
        if self.current_tab == "buy" and self.selected_shop_item is not None:
            if self.selected_shop_item < len(shop_inventory) and shop_inventory[self.selected_shop_item]:
                self._render_item_info(screen, shop_inventory[self.selected_shop_item], "buy", player)
        elif self.current_tab == "sell" and self.selected_player_item is not None:
            if self.selected_player_item < len(player_inventory) and player_inventory[self.selected_player_item]:
                self._render_item_info(screen, player_inventory[self.selected_player_item], "sell", player)

        # Gold bars
        self.gold_bar_shop.update(shop_gold, 1000)
        self.gold_bar_shop.render(screen)
        self.gold_bar_player.update(player_gold, player_gold * 2)  # Max is arbitrary for display
        self.gold_bar_player.render(screen)

        # Buttons
        self.buy_btn.render(screen)
        self.sell_btn.render(screen)
        self.close_btn.render(screen)

        # Tooltips
        if self.current_tab == "buy":
            hovered = self.shop_grid.get_hovered_index(mouse_pos)
            if hovered is not None and hovered < len(shop_inventory) and shop_inventory[hovered]:
                ui.Tooltip.render(screen, shop_inventory[hovered], mouse_pos)
        else:
            hovered = self.player_grid.get_hovered_index(mouse_pos)
            if hovered is not None and hovered < len(player_inventory) and player_inventory[hovered]:
                ui.Tooltip.render(screen, player_inventory[hovered], mouse_pos)

        # Instructions
        font_small = pygame.font.Font(None, 18)
        if self.current_tab == "buy":
            instr = "Click item to select • Buy with button below • ESC to close"
        else:
            instr = "Click item to select • Sell with button below • ESC to close"
        instr_surf = font_small.render(instr, True, ui.UIColors.TEXT_SECONDARY)
        screen.blit(instr_surf, (70, self.screen_height - 80))

    def _render_item_info(self, screen: pygame.Surface, item, mode: str, player: Optional[object] = None):
        """Render detailed item info in center panel."""
        font_title = pygame.font.Font(None, 20)
        font_text = pygame.font.Font(None, 18)

        x = self.info_panel.rect.x + 15
        y = self.info_panel.rect.y + 40

        # Item name
        name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
        tier_color = item.get_tier_color() if hasattr(item, 'get_tier_color') else ui.UIColors.TEXT_HIGHLIGHT
        name_surf = font_title.render(name, True, tier_color)
        screen.blit(name_surf, (x, y))
        y += 30

        # Stats summary (+ comparison vs equipped when available)
        equipped_name = None
        equipped_stats = None
        if player is not None:
            try:
                from . import equipment as equip_mod
                equipped_name, equipped_stats = equip_mod.get_equipped_item_for_comparison(player, item)
            except Exception:
                equipped_name, equipped_stats = None, None

        if hasattr(item, 'get_effective_stats'):
            stats = item.get_effective_stats()

            if stats.get('damage'):
                dmg_val = int(stats['damage'] * 12)
                cmp_str = ""
                color = ui.UIColors.TEXT_PRIMARY
                if equipped_stats and equipped_stats.get('damage') is not None:
                    eq_val = int(equipped_stats['damage'] * 12)
                    delta = dmg_val - eq_val
                    if delta != 0:
                        cmp_str = f" ({delta:+d})"
                        color = ui.UIColors.SUCCESS if delta > 0 else ui.UIColors.ERROR
                dmg_text = f"Damage: +{dmg_val}{cmp_str}"
                dmg_surf = font_text.render(dmg_text, True, color)
                screen.blit(dmg_surf, (x, y))
                y += 22

            if stats.get('defense'):
                def_val = int(stats['defense'])
                cmp_str = ""
                color = ui.UIColors.TEXT_PRIMARY
                if equipped_stats and equipped_stats.get('defense') is not None:
                    eq_val = int(equipped_stats['defense'])
                    delta = def_val - eq_val
                    if delta != 0:
                        cmp_str = f" ({delta:+d})"
                        color = ui.UIColors.SUCCESS if delta > 0 else ui.UIColors.ERROR
                def_text = f"Defense: +{def_val}{cmp_str}"
                def_surf = font_text.render(def_text, True, color)
                screen.blit(def_surf, (x, y))
                y += 22

        # Condition
        if hasattr(item, 'durability'):
            dur_color = ui.UIColors.SUCCESS if item.durability > 50 else ui.UIColors.WARNING
            if item.durability < 25:
                dur_color = ui.UIColors.ERROR
            dur_surf = font_text.render(f"Condition: {int(item.durability)}%", True, dur_color)
            screen.blit(dur_surf, (x, y))
            y += 22

        y += 10

        # Price
        if mode == "buy":
            price = item.get_value() if hasattr(item, 'get_value') else item.base_value
            price_text = f"Price: {price}g"
            price_color = ui.UIColors.TEXT_HIGHLIGHT
        else:  # sell
            price = item.get_sell_price() if hasattr(item, 'get_sell_price') else item.base_value // 2
            price_text = f"Sell for: {price}g"
            price_color = ui.UIColors.SUCCESS

        price_surf = font_title.render(price_text, True, price_color)
        screen.blit(price_surf, (x, y))

    def get_selected_item(self):
        """Get selected item index and type."""
        if self.current_tab == "buy":
            return ("buy", self.selected_shop_item)
        else:
            return ("sell", self.selected_player_item)

    def should_close_shop(self):
        """Check if shop should close."""
        return self.should_close

    def is_buy_clicked(self):
        """Check if buy button was clicked."""
        return self.buy_btn.pressed

    def is_sell_clicked(self):
        """Check if sell button was clicked."""
        return self.sell_btn.pressed
        # Currently equipped label (if any)
        if mode == "buy" and equipped_name:
            y += 6
            eq_label = font_text.render("Currently Equipped:", True, ui.UIColors.TEXT_SECONDARY)
            screen.blit(eq_label, (x, y))
            y += 20
            eq_name_surf = font_text.render(str(equipped_name), True, ui.UIColors.TEXT_PRIMARY)
            screen.blit(eq_name_surf, (x, y))
            y += 18
