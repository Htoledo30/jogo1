"""
HUD helpers for drawing diplomacy in a compact way.
"""

from __future__ import annotations

from typing import Any
import pygame


def draw_diplomacy_hud(screen: pygame.Surface, relations_obj: Any, x: int, y: int, width: int = 230, height: int = 100) -> None:
    from src.ui_components import Panel, UIColors

    panel = Panel(screen.get_width() - width - 10, 10, width, height, title="", border_color=UIColors.INFO)
    panel.render(screen)

    font = pygame.font.Font(None, 16)
    rel_items = list(getattr(relations_obj, 'relations', {}).items())

    def status_key(item):
        fid, val = item
        return abs(val)

    # Non-neutral first
    non_neutral = [(fid, val) for fid, val in rel_items if relations_obj.get_status(fid) != "NEUTRO"]
    neutral = [(fid, val) for fid, val in rel_items if relations_obj.get_status(fid) == "NEUTRO"]
    neutral_sorted = sorted(neutral, key=status_key)[:max(0, 5 - len(non_neutral))]
    display_list = non_neutral[:5] + neutral_sorted

    for i, (faction, _) in enumerate(display_list[:5]):
        status = relations_obj.get_status(faction)
        color = {"GUERRA": UIColors.ERROR, "ALIADO": UIColors.SUCCESS}.get(status, UIColors.TEXT_SECONDARY)
        label = faction.capitalize()
        text = f"{label}: {status}"
        surf = font.render(text, True, color)
        screen.blit(surf, (screen.get_width() - width + 5, 25 + i * 18))


def draw_hud(screen: pygame.Surface, player: Any, troops_count: int = 0,
             relations: Any = None, food_status: str = "",
             battle_instance: Any = None, troops_list: list = None, **kwargs) -> None:
    """Basic HUD renderer (compact), compatible with previous signature.

    Shows: Level, HP bar (and stamina in battle), and calls diplomacy HUD when provided.
    """
    from src.ui_components import Panel, UIColors

    # Left vitals panel
    vitals_panel = Panel(10, 10, 310, 100, title="", border_color=(200, 80, 80))
    vitals_panel.render(screen)

    # Use provided fonts when available (back-compat with main.py callers)
    font_main = kwargs.get('font_main') or pygame.font.Font(None, 18)
    font_large = kwargs.get('font_large') or pygame.font.Font(None, 24)

    # Level
    level_text = f"LEVEL {getattr(player.stats, 'level', 1)}"
    level_surf = font_large.render(level_text, True, UIColors.TEXT_HIGHLIGHT)
    screen.blit(level_surf, (25, 20))

    # Attribute points indicator (if available)
    attr_points = getattr(player.stats, 'attribute_points', 0)
    if attr_points > 0:
        import math
        pulse = 1.0 + 0.3 * math.sin(pygame.time.get_ticks() * 0.005)
        points_font_size = int(18 * pulse)
        points_font = pygame.font.Font(None, points_font_size)
        points_text = f"+{attr_points} POINTS!"
        points_surf = points_font.render(points_text, True, (255, 215, 0))
        screen.blit(points_surf, (180, 23))

        # Show "Press C" hint below
        hint_font = pygame.font.Font(None, 14)
        hint_text = "[Press C]"
        hint_surf = hint_font.render(hint_text, True, (200, 180, 100))
        screen.blit(hint_surf, (185, 42))

    # HP bar
    hp = float(getattr(player.stats, 'hp', 0))
    hp_max = float(getattr(player.stats, 'hp_max', 1)) or 1.0
    hp_ratio = max(0.0, min(1.0, hp / hp_max))
    hp_bg = pygame.Rect(25, 52, 275, 20)
    pygame.draw.rect(screen, (40, 40, 50), hp_bg, border_radius=4)
    pygame.draw.rect(screen, (70, 70, 80), hp_bg, 2, border_radius=4)
    hp_fill = pygame.Rect(25, 52, int(275 * hp_ratio), 20)
    hp_color = UIColors.SUCCESS if hp_ratio > 0.6 else (UIColors.WARNING if hp_ratio > 0.3 else UIColors.ERROR)
    pygame.draw.rect(screen, hp_color, hp_fill, border_radius=4)
    hp_text = f"HP {hp:.0f}/{hp_max:.0f}"
    screen.blit(font_main.render(hp_text, True, UIColors.TEXT_PRIMARY), (30, 54))

    # Stamina in battle
    if battle_instance is not None:
        try:
            stamina = float(getattr(battle_instance, 'player_stamina', 0.0))
            stamina_max = float(getattr(battle_instance, 'player_stamina_max', 100.0)) or 100.0
            ratio = max(0.0, min(1.0, stamina / stamina_max))
            bar = pygame.Rect(25, 78, 275, 14)
            pygame.draw.rect(screen, (30, 30, 40), bar, border_radius=3)
            fill = pygame.Rect(25, 78, int(275 * ratio), 14)
            color = (60, 180, 220) if ratio > 0.3 else (220, 60, 60)
            pygame.draw.rect(screen, color, fill, border_radius=3)
        except (AttributeError, ValueError, ZeroDivisionError):
            # Skip stamina bar if battle instance doesn't have stamina attributes
            pass

    # Troop details panel (only on overworld, not in battle)
    if battle_instance is None and troops_list and len(troops_list) > 0:
        try:
            troop_panel_y = 120
            troop_panel = Panel(10, troop_panel_y, 310, 90, title="", border_color=(100, 150, 255))
            troop_panel.render(screen)

            font_small = kwargs.get('font_small') or pygame.font.Font(None, 16)

            # Count alive troops by type
            alive_troops = [t for t in troops_list if t.alive()]
            warriors = sum(1 for t in alive_troops if getattr(t, 'troop_type', 'warrior') == 'warrior')
            archers = sum(1 for t in alive_troops if getattr(t, 'troop_type', 'warrior') == 'archer')
            tanks = sum(1 for t in alive_troops if getattr(t, 'troop_type', 'warrior') == 'tank')

            # Calculate average HP
            if alive_troops:
                total_hp = sum(getattr(t.stats, 'hp', 0) for t in alive_troops)
                total_hp_max = sum(getattr(t.stats, 'hp_max', 1) for t in alive_troops)
                avg_hp_ratio = total_hp / total_hp_max if total_hp_max > 0 else 0
            else:
                avg_hp_ratio = 0

            # Display
            y_offset = troop_panel_y + 15
            title_surf = font_main.render(f"TROOPS: {len(alive_troops)}", True, UIColors.TEXT_HIGHLIGHT)
            screen.blit(title_surf, (25, y_offset))
            y_offset += 22

            # HP bar for troops
            if alive_troops:
                troops_hp_bar = pygame.Rect(25, y_offset, 275, 12)
                pygame.draw.rect(screen, (40, 40, 50), troops_hp_bar, border_radius=3)
                troops_hp_fill = pygame.Rect(25, y_offset, int(275 * avg_hp_ratio), 12)
                hp_color = UIColors.SUCCESS if avg_hp_ratio > 0.6 else (UIColors.WARNING if avg_hp_ratio > 0.3 else UIColors.ERROR)
                pygame.draw.rect(screen, hp_color, troops_hp_fill, border_radius=3)
                y_offset += 16

            # Troop breakdown by type
            if warriors > 0:
                warrior_surf = font_small.render(f"Warriors: {warriors}", True, (200, 200, 220))
                screen.blit(warrior_surf, (30, y_offset))
                y_offset += 16
            if archers > 0:
                archer_surf = font_small.render(f"Archers: {archers}", True, (200, 220, 200))
                screen.blit(archer_surf, (30, y_offset))
                y_offset += 16
            if tanks > 0:
                tank_surf = font_small.render(f"Tanks: {tanks}", True, (220, 200, 180))
                screen.blit(tank_surf, (30, y_offset))
        except (AttributeError, ValueError, ZeroDivisionError):
            # Skip troop panel if data is invalid
            pass

    # Resources panel (Gold, Food, XP) - Only on overworld
    if battle_instance is None:
        try:
            font_small = kwargs.get('font_small') or pygame.font.Font(None, 16)
            resources_panel_y = 220 if troops_list and len(troops_list) > 0 else 120
            resources_panel = Panel(10, resources_panel_y, 310, 120, title="", border_color=(255, 215, 0))
            resources_panel.render(screen)

            y_offset = resources_panel_y + 15

            # Gold display
            gold = getattr(player.stats, 'gold', 0)
            gold_text = f"GOLD: {gold}"
            gold_surf = font_main.render(gold_text, True, (255, 215, 0))
            screen.blit(gold_surf, (25, y_offset))
            y_offset += 25

            # Food status
            food = getattr(player.stats, 'food', 0)
            food_text = f"Food: {food}"
            food_color = (255, 100, 100) if food <= 0 else (200, 220, 200)
            food_surf = font_small.render(food_text, True, food_color)
            screen.blit(food_surf, (25, y_offset))
            y_offset += 20

            # XP Progress Bar
            xp = getattr(player.stats, 'xp', 0)
            xp_needed = getattr(player.stats, 'xp_to_next_level', 100)
            xp_ratio = xp / xp_needed if xp_needed > 0 else 0

            xp_label = font_small.render(f"XP: {xp}/{xp_needed}", True, UIColors.TEXT_PRIMARY)
            screen.blit(xp_label, (25, y_offset))
            y_offset += 18

            xp_bar_bg = pygame.Rect(25, y_offset, 275, 14)
            pygame.draw.rect(screen, (40, 40, 50), xp_bar_bg, border_radius=3)
            xp_bar_fill = pygame.Rect(25, y_offset, int(275 * xp_ratio), 14)
            pygame.draw.rect(screen, (100, 200, 255), xp_bar_fill, border_radius=3)
            y_offset += 20

            # Inventory count (if player has inventory)
            if hasattr(player, 'inventory'):
                inv_count = len([item for item in player.inventory if item])
                inv_text = f"Inventory: {inv_count} items"
                inv_surf = font_small.render(inv_text, True, UIColors.TEXT_SECONDARY)
                screen.blit(inv_surf, (25, y_offset))
        except (AttributeError, ValueError, ZeroDivisionError):
            # Skip resources panel if data is invalid
            pass

    # Diplomacy HUD (right) - hide during battle
    if relations is not None and battle_instance is None:
        try:
            draw_diplomacy_hud(screen, relations, screen.get_width() - 240, 10)
        except (AttributeError, KeyError, TypeError):
            # Skip diplomacy HUD if relations data is invalid
            pass
