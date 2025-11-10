"""
Reusable UI Components for Modern Game Menus.

Includes: Buttons, Grids, Tooltips, Panels, Progress Bars, etc.
"""

import pygame
import math
from typing import Optional, Callable, List, Tuple


# ============================================================================
# COLORS & CONSTANTS
# ============================================================================

class UIColors:
    """Standard UI color palette."""
    # Backgrounds
    PANEL_BG = (30, 30, 40, 220)  # Dark semi-transparent
    PANEL_BORDER = (100, 150, 200)
    BUTTON_BG = (50, 50, 70)
    BUTTON_HOVER = (70, 70, 100)
    BUTTON_ACTIVE = (90, 90, 130)

    # Text
    TEXT_PRIMARY = (240, 240, 240)
    TEXT_SECONDARY = (180, 180, 200)
    TEXT_DISABLED = (100, 100, 120)
    TEXT_HIGHLIGHT = (255, 215, 0)  # Gold

    # Status
    SUCCESS = (100, 255, 100)
    WARNING = (255, 200, 50)
    ERROR = (255, 100, 100)
    INFO = (100, 180, 255)

    # Tiers
    TIER_1 = (205, 127, 50)   # Bronze
    TIER_2 = (192, 192, 192)  # Silver
    TIER_3 = (255, 215, 0)    # Gold


# ============================================================================
# BUTTON COMPONENT
# ============================================================================

class Button:
    """Interactive button with hover and click states."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 text: str, callback: Optional[Callable] = None,
                 font_size: int = 20, enabled: bool = True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = pygame.font.Font(None, font_size)
        self.enabled = enabled

        self.hovered = False
        self.pressed = False

        # Animation state
        self.hover_progress = 0.0  # 0.0 to 1.0 for smooth hover transition
        self.press_offset = 0  # Y offset for press animation
        self.glow_intensity = 0.0  # 0.0 to 1.0 for glow effect

    def update(self, events: List[pygame.event.Event], mouse_pos: Tuple[int, int], dt: float = 0.016):
        """Update button state and animations."""
        self.hovered = self.rect.collidepoint(mouse_pos) and self.enabled

        # Smooth hover transition (0 to 1 over 0.15 seconds)
        hover_speed = 6.0  # Units per second
        if self.hovered:
            self.hover_progress = min(1.0, self.hover_progress + hover_speed * dt)
        else:
            self.hover_progress = max(0.0, self.hover_progress - hover_speed * dt)

        # Glow pulse when hovered
        if self.hovered:
            self.glow_intensity = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300.0)
        else:
            self.glow_intensity = 0.0

        # Press animation (button moves down slightly)
        if self.pressed:
            self.press_offset = 2  # Pixels down
        else:
            self.press_offset = 0

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.hovered:
                    self.pressed = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.pressed and self.hovered and self.callback:
                    self.callback()
                self.pressed = False

    def render(self, screen: pygame.Surface):
        """Draw button with animations."""
        # Apply press offset
        draw_rect = self.rect.copy()
        draw_rect.y += self.press_offset

        # Interpolate colors based on hover progress
        if not self.enabled:
            bg_color = (40, 40, 50)
            text_color = UIColors.TEXT_DISABLED
        else:
            # Lerp between normal and hover colors
            base_bg = UIColors.BUTTON_BG
            hover_bg = UIColors.BUTTON_HOVER
            bg_color = tuple(
                int(base_bg[i] + (hover_bg[i] - base_bg[i]) * self.hover_progress)
                for i in range(3)
            )

            base_text = UIColors.TEXT_PRIMARY
            hover_text = UIColors.TEXT_HIGHLIGHT
            text_color = tuple(
                int(base_text[i] + (hover_text[i] - base_text[i]) * self.hover_progress)
                for i in range(3)
            )

        # Draw glow effect when hovered
        if self.glow_intensity > 0.1 and self.enabled:
            glow_size = int(4 * self.glow_intensity)
            glow_rect = draw_rect.inflate(glow_size, glow_size)
            glow_alpha = int(80 * self.glow_intensity)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            glow_color = (*UIColors.TEXT_HIGHLIGHT, glow_alpha)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=6)
            screen.blit(glow_surf, glow_rect.topleft)

        # Draw background
        pygame.draw.rect(screen, bg_color, draw_rect, border_radius=4)
        pygame.draw.rect(screen, UIColors.PANEL_BORDER, draw_rect, 2, border_radius=4)

        # Draw text
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        screen.blit(text_surf, text_rect)


# ============================================================================
# PANEL COMPONENT
# ============================================================================

class Panel:
    """Bordered panel with optional title."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 title: str = "", border_color: tuple = UIColors.PANEL_BORDER):
        self.rect = pygame.Rect(x, y, width, height)
        self.title = title
        self.border_color = border_color
        self.title_font = pygame.font.Font(None, 24)

    def render(self, screen: pygame.Surface):
        """Draw panel with border and optional title."""
        # Create surface with alpha
        panel_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel_surf.fill(UIColors.PANEL_BG)

        # Draw to screen
        screen.blit(panel_surf, self.rect)

        # Border
        pygame.draw.rect(screen, self.border_color, self.rect, 3, border_radius=5)

        # Title bar if present
        if self.title:
            title_height = 30
            title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, title_height)
            pygame.draw.rect(screen, (40, 40, 60), title_rect, border_top_left_radius=5,
                           border_top_right_radius=5)
            pygame.draw.line(screen, self.border_color,
                           (self.rect.x, self.rect.y + title_height),
                           (self.rect.right, self.rect.y + title_height), 2)

            title_surf = self.title_font.render(self.title, True, UIColors.TEXT_HIGHLIGHT)
            title_text_rect = title_surf.get_rect(center=title_rect.center)
            screen.blit(title_surf, title_text_rect)


# ============================================================================
# GRID COMPONENT
# ============================================================================

class Grid:
    """Item grid for inventory/shop display."""

    def __init__(self, x: int, y: int, cols: int, rows: int,
                 cell_size: int = 60, spacing: int = 4):
        self.x = x
        self.y = y
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.spacing = spacing

        self.cells = []
        self._create_cells()

        self.hovered_cell = None

    def _create_cells(self):
        """Generate cell rectangles."""
        self.cells = []
        for row in range(self.rows):
            for col in range(self.cols):
                cell_x = self.x + col * (self.cell_size + self.spacing)
                cell_y = self.y + row * (self.cell_size + self.spacing)
                self.cells.append(pygame.Rect(cell_x, cell_y, self.cell_size, self.cell_size))

    def get_hovered_index(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Get index of hovered cell."""
        for i, cell in enumerate(self.cells):
            if cell.collidepoint(mouse_pos):
                return i
        return None

    def render(self, screen: pygame.Surface, items: List, mouse_pos: Tuple[int, int]):
        """
        Render grid with items.

        items: List of items to display (must have get_tier_color() method)
        """
        self.hovered_cell = self.get_hovered_index(mouse_pos)

        for i, cell in enumerate(self.cells):
            # Cell background
            bg_color = (50, 50, 60) if i < len(items) and items[i] else (40, 40, 50)
            pygame.draw.rect(screen, bg_color, cell, border_radius=3)

            # Border - highlight if hovered
            border_color = UIColors.TEXT_HIGHLIGHT if i == self.hovered_cell else (70, 70, 80)
            border_width = 3 if i == self.hovered_cell else 2
            pygame.draw.rect(screen, border_color, cell, border_width, border_radius=3)

            # Item icon if present
            if i < len(items) and items[i]:
                item = items[i]

                # Tier border
                tier_color = item.get_tier_color() if hasattr(item, 'get_tier_color') else UIColors.TIER_1
                pygame.draw.rect(screen, tier_color, cell, 2, border_radius=3)

                # Simple icon (colored circle for now)
                icon_color = item.icon_color if hasattr(item, 'icon_color') else (200, 200, 200)
                center = cell.center
                radius = self.cell_size // 3
                pygame.draw.circle(screen, icon_color, center, radius)

                # Durability bar if applicable
                if hasattr(item, 'durability') and item.durability < 100:
                    bar_width = self.cell_size - 10
                    bar_height = 4
                    bar_x = cell.x + 5
                    bar_y = cell.bottom - 8

                    # Background
                    pygame.draw.rect(screen, (60, 60, 60),
                                   (bar_x, bar_y, bar_width, bar_height))

                    # Durability fill
                    fill_width = int(bar_width * (item.durability / 100.0))
                    dur_color = UIColors.SUCCESS if item.durability > 50 else UIColors.WARNING
                    if item.durability < 25:
                        dur_color = UIColors.ERROR
                    pygame.draw.rect(screen, dur_color,
                                   (bar_x, bar_y, fill_width, bar_height))

                # Stack size for consumables
                if hasattr(item, 'stack_size') and item.stack_size > 1:
                    font = pygame.font.Font(None, 16)
                    stack_text = font.render(f"x{item.stack_size}", True, UIColors.TEXT_PRIMARY)
                    screen.blit(stack_text, (cell.right - 20, cell.bottom - 18))


# ============================================================================
# TOOLTIP COMPONENT
# ============================================================================

class Tooltip:
    """Detailed item tooltip."""

    @staticmethod
    def render(screen: pygame.Surface, item, pos: Tuple[int, int],
               compare_item=None):
        """
        Render tooltip for an item.

        item: Item to show tooltip for
        pos: (x, y) position for tooltip
        compare_item: Optional item to compare against
        """
        if not item:
            return

        font_title = pygame.font.Font(None, 22)
        font_text = pygame.font.Font(None, 18)

        lines = []

        # Title with quality
        display_name = item.get_display_name() if hasattr(item, 'get_display_name') else item.name
        title_color = item.get_tier_color() if hasattr(item, 'get_tier_color') else UIColors.TEXT_HIGHLIGHT
        lines.append((display_name, font_title, title_color))

        # Type and tier
        type_text = f"{item.item_type.value} (Tier {item.tier})" if hasattr(item, 'tier') else item.item_type.value
        lines.append((type_text, font_text, UIColors.TEXT_SECONDARY))

        lines.append(("", font_text, UIColors.TEXT_PRIMARY))  # Spacer

        # Stats
        if hasattr(item, 'get_effective_stats'):
            stats = item.get_effective_stats()

            if stats['damage']:
                dmg_text = f"Damage: +{int(stats['damage'] * 12)}"  # Base ATK 12
                lines.append((dmg_text, font_text, UIColors.TEXT_PRIMARY))

            if stats['defense']:
                def_text = f"Defense: +{int(stats['defense'])}"
                lines.append((def_text, font_text, UIColors.TEXT_PRIMARY))

            if stats['speed_modifier']:
                spd_val = stats['speed_modifier'] * 100
                spd_text = f"Speed: {spd_val:+.0f}%"
                spd_color = UIColors.ERROR if spd_val < 0 else UIColors.SUCCESS
                lines.append((spd_text, font_text, spd_color))

        # Weight
        if hasattr(item, 'weight'):
            lines.append((f"Weight: {item.weight:.1f} kg", font_text, UIColors.TEXT_SECONDARY))

        # Durability
        if hasattr(item, 'durability'):
            dur_color = UIColors.SUCCESS if item.durability > 50 else UIColors.WARNING
            if item.durability < 25:
                dur_color = UIColors.ERROR
            lines.append((f"Condition: {int(item.durability)}%", font_text, dur_color))

        lines.append(("", font_text, UIColors.TEXT_PRIMARY))  # Spacer

        # Value
        value = item.get_value() if hasattr(item, 'get_value') else item.base_value
        lines.append((f"Value: {value}g", font_text, UIColors.TEXT_HIGHLIGHT))

        sell_price = item.get_sell_price() if hasattr(item, 'get_sell_price') else value // 2
        lines.append((f"Sell: {sell_price}g", font_text, UIColors.TEXT_SECONDARY))

        # Description
        if item.description:
            lines.append(("", font_text, UIColors.TEXT_PRIMARY))  # Spacer
            # Word wrap description
            words = item.description.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if font_text.size(test_line)[0] > 220:
                    lines.append((line, font_text, UIColors.INFO))
                    line = word + " "
                else:
                    line = test_line
            if line:
                lines.append((line, font_text, UIColors.INFO))

        # Calculate tooltip size
        # Use distinct local names to avoid scoping issues
        max_width = max(f.size(t)[0] for t, f, _ in lines) + 20
        total_height = sum(f.size(t)[1] + 2 for t, f, _ in lines) + 20

        # Position tooltip (avoid going off screen)
        tooltip_x = min(pos[0] + 15, screen.get_width() - max_width - 10)
        tooltip_y = min(pos[1] + 15, screen.get_height() - total_height - 10)

        # Draw background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, max_width, total_height)
        tooltip_surf = pygame.Surface((max_width, total_height), pygame.SRCALPHA)
        tooltip_surf.fill((20, 20, 30, 240))
        screen.blit(tooltip_surf, tooltip_rect)

        # Border
        pygame.draw.rect(screen, UIColors.PANEL_BORDER, tooltip_rect, 2, border_radius=5)

        # Render text lines
        y_offset = tooltip_y + 10
        for text, font, color in lines:
            if text:  # Skip empty lines for spacing
                text_surf = font.render(text, True, color)
                screen.blit(text_surf, (tooltip_x + 10, y_offset))
            y_offset += font.size(text)[1] + 2


# ============================================================================
# PROGRESS BAR COMPONENT
# ============================================================================

class ProgressBar:
    """Visual progress bar (for weight, HP, XP, etc) with smooth animations."""

    def __init__(self, x: int, y: int, width: int, height: int,
                 max_value: float, current_value: float,
                 label: str = "", color: tuple = UIColors.SUCCESS):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_value = max_value
        self.current_value = current_value
        self.label = label
        self.color = color

        # Animation state
        self.displayed_value = current_value  # Smoothly lerps to current_value
        self.damage_flash = 0.0  # Flash red when taking damage
        self.heal_flash = 0.0  # Flash green when healing

    def update(self, current: float, max_val: float = None, dt: float = 0.016):
        """Update bar values with smooth animation."""
        # Detect damage or healing
        if current < self.current_value:
            self.damage_flash = 1.0  # Full flash
        elif current > self.current_value:
            self.heal_flash = 1.0

        self.current_value = current
        if max_val:
            self.max_value = max_val

        # Smooth lerp toward actual value (reaches target in ~0.3 seconds)
        lerp_speed = 8.0  # Units per second
        diff = self.current_value - self.displayed_value
        if abs(diff) > 0.1:
            self.displayed_value += diff * lerp_speed * dt
        else:
            self.displayed_value = self.current_value

        # Decay flashes
        self.damage_flash = max(0.0, self.damage_flash - 4.0 * dt)
        self.heal_flash = max(0.0, self.heal_flash - 4.0 * dt)

    def render(self, screen: pygame.Surface):
        """Draw progress bar with smooth animation."""
        # Background
        pygame.draw.rect(screen, (40, 40, 50), self.rect, border_radius=3)
        pygame.draw.rect(screen, (70, 70, 80), self.rect, 2, border_radius=3)

        # Fill (using displayed_value for smooth animation)
        if self.max_value > 0:
            fill_width = int(self.rect.width * (self.displayed_value / self.max_value))
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)

            # Color based on percentage
            percent = self.displayed_value / self.max_value
            if percent > 0.7:
                color = UIColors.SUCCESS
            elif percent > 0.4:
                color = UIColors.WARNING
            else:
                color = UIColors.ERROR

            # Apply flash effects
            if self.damage_flash > 0.1:
                flash_amount = int(100 * self.damage_flash)
                color = tuple(min(255, c + flash_amount) if i == 0 else max(0, c - flash_amount // 2)
                             for i, c in enumerate(color))
            elif self.heal_flash > 0.1:
                flash_amount = int(100 * self.heal_flash)
                color = tuple(min(255, c + flash_amount) if i == 1 else max(0, c - flash_amount // 2)
                             for i, c in enumerate(color))

            pygame.draw.rect(screen, color, fill_rect, border_radius=3)

        # Text
        if self.label:
            font = pygame.font.Font(None, 18)
            text = f"{self.label}: {int(self.current_value)}/{int(self.max_value)}"
            text_surf = font.render(text, True, UIColors.TEXT_PRIMARY)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)


# ============================================================================
# ANIMATED GOLD DISPLAY
# ============================================================================

class AnimatedGoldDisplay:
    """Shows gold with smooth counting animation and gain/loss indicators."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.displayed_gold = 0
        self.actual_gold = 0

        # Floating text for gains/losses
        self.floating_texts = []  # List of (text, x, y, alpha, lifetime)

    def update(self, current_gold: int, dt: float = 0.016):
        """Update gold display with smooth counting."""
        # Detect gold gain/loss
        if current_gold > self.actual_gold:
            gain = current_gold - self.actual_gold
            # Add floating +gold text
            self.floating_texts.append({
                "text": f"+{gain}g",
                "x": self.x + 50,
                "y": self.y - 10,
                "alpha": 255,
                "lifetime": 2.0,
                "color": UIColors.TEXT_HIGHLIGHT
            })
        elif current_gold < self.actual_gold:
            loss = self.actual_gold - current_gold
            self.floating_texts.append({
                "text": f"-{loss}g",
                "x": self.x + 50,
                "y": self.y - 10,
                "alpha": 255,
                "lifetime": 2.0,
                "color": UIColors.ERROR
            })

        self.actual_gold = current_gold

        # Smooth counting animation
        diff = self.actual_gold - self.displayed_gold
        if abs(diff) > 0.5:
            # Count faster for large differences
            count_speed = max(abs(diff) * 2, 50)  # Min 50 gold per second
            step = count_speed * dt
            if diff > 0:
                self.displayed_gold = min(self.actual_gold, self.displayed_gold + step)
            else:
                self.displayed_gold = max(self.actual_gold, self.displayed_gold - step)
        else:
            self.displayed_gold = self.actual_gold

        # Update floating texts
        for ft in list(self.floating_texts):
            ft["lifetime"] -= dt
            ft["y"] -= 30 * dt  # Float upward
            ft["alpha"] = int(255 * (ft["lifetime"] / 2.0))  # Fade out

            if ft["lifetime"] <= 0:
                self.floating_texts.remove(ft)

    def render(self, screen: pygame.Surface):
        """Draw gold display and floating texts."""
        # Main gold text
        font = pygame.font.Font(None, 20)
        gold_text = f"{int(self.displayed_gold)}g"
        gold_surf = font.render(gold_text, True, UIColors.TEXT_HIGHLIGHT)
        screen.blit(gold_surf, (self.x, self.y))

        # Floating gain/loss texts
        font_small = pygame.font.Font(None, 18)
        for ft in self.floating_texts:
            text_surf = font_small.render(ft["text"], True, ft["color"])
            text_surf.set_alpha(ft["alpha"])
            screen.blit(text_surf, (int(ft["x"]), int(ft["y"])))
