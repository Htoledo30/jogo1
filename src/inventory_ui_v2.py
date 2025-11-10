"""
Inventory UI V2 — Modern Grid-Based Inventory with Screen Base, Dynamic Filters,
Selection Highlight, and Fade Transitions (Pygame)

Depends on:
  - .ui_components as ui  (Button, Panel, Grid, Tooltip, ProgressBar, UIColors)
  - .items (expects ItemType enum and item objects with attributes used below)

Features added vs v1:
  ✓ UIScreen base class (open/close/toggle, visibility, transitions)
  ✓ Fade-in / fade-out animation for the whole screen
  ✓ Dynamic filter system (easily add new categories)
  ✓ Visual highlight for selected grid cell
  ✓ Optional UIManager (to manage multiple UIScreens)

Author: Henry + ChatGPT
"""

from __future__ import annotations

import pygame
from typing import List, Optional, Callable, Dict, Tuple
from . import items
from . import ui_components as ui


# =============================================================================
# UIScreen base
# =============================================================================
class UIScreen:
    """Base class for any UI screen (e.g., Inventory, Shop, Crafting).

    Provides visibility state and simple fade transitions.
    """

    def __init__(self, name: str, fade_duration_ms: int = 180):
        self.name = name
        self.visible: bool = False
        self._state: str = "closed"  # "opening" | "open" | "closing" | "closed"
        self._fade_duration = max(1, fade_duration_ms)
        self._transition_start = 0
        self._alpha: int = 0  # 0..255

    # ---- Lifecycle ---------------------------------------------------------
    def open(self):
        if self._state in ("closed", "closing"):
            self.visible = True
            self._state = "opening"
            self._transition_start = pygame.time.get_ticks()

    def close(self):
        if self._state in ("open", "opening"):
            self._state = "closing"
            self._transition_start = pygame.time.get_ticks()

    def toggle(self):
        if self.visible:
            self.close()
        else:
            self.open()

    # ---- Transition update -------------------------------------------------
    def _update_fade(self):
        if self._state in ("opening", "closing"):
            now = pygame.time.get_ticks()
            t = (now - self._transition_start) / self._fade_duration
            t = max(0.0, min(1.0, t))

            if self._state == "opening":
                self._alpha = int(255 * t)
                if t >= 1.0:
                    self._state = "open"
                    self._alpha = 255
            else:  # closing
                self._alpha = int(255 * (1.0 - t))
                if t >= 1.0:
                    self._state = "closed"
                    self._alpha = 0
                    self.visible = False
        elif self._state == "open":
            self._alpha = 255
        elif self._state == "closed":
            self._alpha = 0

    @property
    def alpha(self) -> int:
        return self._alpha

    @property
    def is_open(self) -> bool:
        return self._state == "open"


# =============================================================================
# Optional UIManager (for multiple screens)
# =============================================================================
class UIManager:
    """Simple manager to orchestrate UIScreens.

    Example:
        ui_manager = UIManager()
        ui_manager.register(inventory_ui)
        ...
        ui_manager.update(events, mouse_pos, dt)
        ui_manager.render(screen)
    """

    def __init__(self):
        self.screens: Dict[str, UIScreen] = {}

    def register(self, screen: UIScreen):
        self.screens[screen.name] = screen

    def open(self, name: str):
        if name in self.screens:
            self.screens[name].open()

    def close(self, name: str):
        if name in self.screens:
            self.screens[name].close()

    def toggle(self, name: str):
        if name in self.screens:
            self.screens[name].toggle()

    def any_open(self) -> bool:
        return any(s.visible for s in self.screens.values())

    # Delegated loop hooks (optional)
    def update(self, events: List[pygame.event.Event], mouse_pos: Tuple[int, int], *args, **kwargs):
        for s in self.screens.values():
            if s.visible and hasattr(s, "update"):
                s.update(events, mouse_pos, *args, **kwargs)

    def render(self, screen: pygame.Surface, *args, **kwargs):
        for s in self.screens.values():
            if s.visible and hasattr(s, "render"):
                s.render(screen, *args, **kwargs)


# =============================================================================
# Inventory UI V2
# =============================================================================
class InventoryUI(UIScreen):
    """Modern inventory screen with grid layout, dynamic filters and transitions."""

    def __init__(self, screen_width: int, screen_height: int, fade_duration_ms: int = 180):
        super().__init__(name="inventory", fade_duration_ms=fade_duration_ms)

        self.screen_width = screen_width
        self.screen_height = screen_height

        # Layout
        self.panel = ui.Panel(50, 50, screen_width - 100, screen_height - 100,
                              "INVENTORY", ui.UIColors.PANEL_BORDER)

        # Equipment panel (left)
        self.equip_panel = ui.Panel(70, 100, 250, 400, "Equipped")

        # Inventory grid (center)
        self.inv_grid = ui.Grid(340, 100, cols=5, rows=4, cell_size=60, spacing=6)

        # Stats panel (right)
        self.stats_panel = ui.Panel(screen_width - 330, 100, 260, 300, "Item Info")

        # Weight bar
        self.weight_bar = ui.ProgressBar(340, 520, 320, 25, 100, 0, "Weight")

        # Action buttons
        button_y = screen_height - 130
        self.equip_btn = ui.Button(340, button_y, 100, 35, "Equip", font_size=18)
        self.drop_btn = ui.Button(450, button_y, 100, 35, "Drop", font_size=18)
        self.close_btn = ui.Button(560, button_y, 100, 35, "Close", font_size=18)

        # Dynamic filters (name -> predicate)
        # Predicates receive an `item` and return True/False.
        self.filters: Dict[str, Callable] = {
            "all": lambda it: True,
            "weapons": lambda it: hasattr(it, "item_type") and it.item_type == items.ItemType.WEAPON,
            "armor": lambda it: hasattr(it, "item_type") and it.item_type == items.ItemType.ARMOR,
        }

        # Create buttons from filters dynamically
        self.filter_buttons: Dict[str, ui.Button] = {}
        self.current_filter: str = "all"
        self._create_filter_buttons(base_x=340, y=550, spacing=8)

        # State
        self.selected_index: Optional[int] = None
        self.should_close_flag: bool = False

        # Pre-allocated surface for whole-screen composition + fade
        self._composite = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

    # ---- Helpers -----------------------------------------------------------
    def _create_filter_buttons(self, base_x: int, y: int, spacing: int = 8):
        self.filter_buttons.clear()
        x = base_x
        for name in self.filters.keys():
            label = name.capitalize() if name != "weapons" else "Weapons"
            w = max(70, 14 * len(label))
            btn = ui.Button(x, y, w, 30, label, font_size=16)
            # Capture closure variable `name` safely using default arg
            btn.callback = (lambda n=name: self._set_filter(n))
            self.filter_buttons[name] = btn
            x += w + spacing

    def _set_filter(self, name: str):
        if name in self.filters:
            self.current_filter = name
            self.selected_index = None

    # ---- Public API --------------------------------------------------------
    def should_close_inventory(self) -> bool:
        return self.should_close_flag

    def get_selected_item_index(self) -> Optional[int]:
        return self.selected_index

    def _get_filtered_items(self, player):
        """Get filtered inventory items based on current filter."""
        inventory = [it for it in player.inventory if it]
        predicate = self.filters.get(self.current_filter, lambda it: True)
        return [it for it in inventory if predicate(it)]

    # ---- Update ------------------------------------------------------------
    def update(self,
               events: List[pygame.event.Event],
               mouse_pos: Tuple[int, int],
               player,
               on_equip_callback: Callable,
               on_drop_callback: Callable):
        """Update UI state and controls.

        Returns the filtered list (`display_items`) for external use if needed.
        """
        # Update fade/visibility
        self._update_fade()
        if not self.visible:
            return []

        self.should_close_flag = False

        # Filter inventory based on current filter
        display_items = self._get_filtered_items(player)

        # Update grid selection (left click to select)
        hovered = self.inv_grid.get_hovered_index(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hovered is not None and hovered < len(display_items):
                    self.selected_index = hovered

            if event.type == pygame.KEYDOWN:
                # Only ESC closes inventory now - I key is handled in main.py to prevent double-trigger
                if event.key == pygame.K_ESCAPE:
                    self.close()  # trigger fade-out
                    self.should_close_flag = True

        # Button callbacks ---------------------------------------------------
        def on_equip():
            if self.selected_index is not None and self.selected_index < len(display_items):
                item_to_equip = display_items[self.selected_index]
                on_equip_callback(item_to_equip)
                self.selected_index = None

        def on_drop():
            if self.selected_index is not None and self.selected_index < len(display_items):
                item_to_drop = display_items[self.selected_index]
                on_drop_callback(item_to_drop)
                self.selected_index = None

        def on_close():
            self.close()
            self.should_close_flag = True

        # Wire actions
        self.equip_btn.callback = on_equip
        self.drop_btn.callback = on_drop
        self.close_btn.callback = on_close

        # Enable/disable based on selection
        has_selection = self.selected_index is not None and self.selected_index < len(display_items)
        self.equip_btn.enabled = has_selection
        self.drop_btn.enabled = has_selection

        # Update buttons
        self.equip_btn.update(events, mouse_pos)
        self.drop_btn.update(events, mouse_pos)
        self.close_btn.update(events, mouse_pos)
        for btn in self.filter_buttons.values():
            btn.update(events, mouse_pos)

        return display_items

    # ---- Render ------------------------------------------------------------
    def render(self, screen: pygame.Surface, player, equipped_items: Dict[str, str], mouse_pos: Tuple[int, int]):
        # Update fade/visibility and early out if fully hidden
        self._update_fade()
        if self.alpha <= 0:
            return

        # Compose to an off-screen surface to apply a global alpha
        self._composite.fill((0, 0, 0, 0))
        cs = self._composite

        # Filtered view to keep render consistent with update
        display_items = self._get_filtered_items(player)

        # Panels
        self.panel.render(cs)
        self.equip_panel.render(cs)
        self.stats_panel.render(cs)

        # Render equipped items (always show)
        self._render_equipped(cs, equipped_items)

        # Grid & tooltip
        self.inv_grid.render(cs, display_items, mouse_pos)

        # Selection highlight overlay (if any)
        if self.selected_index is not None and self.selected_index < len(display_items):
            # Safe-guard: grid may have fewer cells than index when layout changes
            if self.selected_index < len(self.inv_grid.cells):
                cell = self.inv_grid.cells[self.selected_index]
                pygame.draw.rect(cs, ui.UIColors.TEXT_HIGHLIGHT, cell, 3, border_radius=4)

            # Stats for selected item
            selected_item = display_items[self.selected_index]
            if selected_item:
                self._render_item_stats(cs, selected_item)

        # Tooltip for hovered item
        hovered = self.inv_grid.get_hovered_index(mouse_pos)
        if hovered is not None and hovered < len(display_items) and display_items[hovered]:
            ui.Tooltip.render(cs, display_items[hovered], mouse_pos)

        # Weight bar (with dynamic color hints)
        total_weight = sum(getattr(item, "weight", 0.0) for item in player.inventory if item)
        max_weight = 100.0
        self.weight_bar.update(total_weight, max_weight)
        self.weight_bar.render(cs)

        # Action buttons
        self.equip_btn.render(cs)
        self.drop_btn.render(cs)
        self.close_btn.render(cs)

        # Filter buttons
        for name, btn in self.filter_buttons.items():
            btn.render(cs)

        # Highlight current filter with outline
        for name, btn in self.filter_buttons.items():
            if name == self.current_filter:
                pygame.draw.rect(cs, ui.UIColors.TEXT_HIGHLIGHT, btn.rect, 2, border_radius=4)

        # Instructions footer
        font = pygame.font.Font(None, 18)
        instr = "Click item to select • ESC or I to close • Use filters to sort"
        instr_surf = font.render(instr, True, ui.UIColors.TEXT_SECONDARY)
        cs.blit(instr_surf, (70, self.screen_height - 80))

        # Apply global fade alpha to the composed surface
        faded = cs.copy()
        faded.set_alpha(self.alpha)
        screen.blit(faded, (0, 0))

    # ---- Private renderers -------------------------------------------------
    def _render_equipped(self, screen: pygame.Surface, equipped: Dict[str, Optional[str]]):
        font = pygame.font.Font(None, 18)
        y = 130

        slots = [
            ("Weapon", equipped.get("weapon")),
            ("Helmet", equipped.get("helmet")),
            ("Chest", equipped.get("chest")),
            ("Legs", equipped.get("legs")),
            ("Boots", equipped.get("boots")),
        ]

        for slot_name, item_name in slots:
            # Slot label
            label_surf = font.render(f"{slot_name}:", True, ui.UIColors.TEXT_SECONDARY)
            screen.blit(label_surf, (85, y))

            # Item name or Empty
            if item_name and item_name != "None":
                item_surf = font.render(str(item_name), True, ui.UIColors.TEXT_PRIMARY)
                screen.blit(item_surf, (160, y))
            else:
                empty_surf = font.render("Empty", True, ui.UIColors.TEXT_DISABLED)
                screen.blit(empty_surf, (160, y))

            y += 25

    def _render_item_stats(self, screen: pygame.Surface, item):
        font_title = pygame.font.Font(None, 20)
        font_text = pygame.font.Font(None, 18)

        x = self.stats_panel.rect.x + 15
        y = self.stats_panel.rect.y + 40

        # Item name with quality color
        name = item.get_display_name() if hasattr(item, 'get_display_name') else getattr(item, 'name', 'Unknown')
        tier_color = item.get_tier_color() if hasattr(item, 'get_tier_color') else ui.UIColors.TEXT_HIGHLIGHT
        name_surf = font_title.render(name, True, tier_color)
        screen.blit(name_surf, (x, y))
        y += 30

        # Stats (damage/defense/speed)
        if hasattr(item, 'get_effective_stats'):
            stats = item.get_effective_stats()

            if stats.get('damage'):
                dmg_text = f"Damage: +{int(stats['damage'] * 12)}"
                dmg_surf = font_text.render(dmg_text, True, ui.UIColors.SUCCESS)
                screen.blit(dmg_surf, (x, y))
                y += 22

            if stats.get('defense'):
                def_text = f"Defense: +{int(stats['defense'])}"
                def_surf = font_text.render(def_text, True, ui.UIColors.INFO)
                screen.blit(def_surf, (x, y))
                y += 22

            if stats.get('speed_modifier'):
                spd_val = stats['speed_modifier'] * 100
                spd_text = f"Speed: {spd_val:+.0f}%"
                spd_color = ui.UIColors.ERROR if spd_val < 0 else ui.UIColors.SUCCESS
                spd_surf = font_text.render(spd_text, True, spd_color)
                screen.blit(spd_surf, (x, y))
                y += 22

        # Weight & Durability
        y += 10
        if hasattr(item, 'weight'):
            weight_surf = font_text.render(f"Weight: {getattr(item, 'weight', 0.0):.1f}kg",
                                           True, ui.UIColors.TEXT_SECONDARY)
            screen.blit(weight_surf, (x, y))
            y += 22

        if hasattr(item, 'durability'):
            dur_val = getattr(item, 'durability', 100)
            dur_color = ui.UIColors.SUCCESS if dur_val > 50 else ui.UIColors.WARNING
            if dur_val < 25:
                dur_color = ui.UIColors.ERROR
            dur_surf = font_text.render(f"Condition: {int(dur_val)}%", True, dur_color)
            screen.blit(dur_surf, (x, y))
            y += 22

        # Value
        y += 10
        value = item.get_value() if hasattr(item, 'get_value') else getattr(item, 'base_value', 0)
        val_surf = font_text.render(f"Value: {value}g", True, ui.UIColors.TEXT_HIGHLIGHT)
        screen.blit(val_surf, (x, y))
