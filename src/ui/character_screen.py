"""Character Status screen (Elden Ring-inspired).

Displays primary attributes, combat stats, meta stats, and available
attribute points. Offers a prompt to open the Level Up screen if the
player has unspent points.
"""

from __future__ import annotations

import pygame
from typing import Any

from ..resource_manager import get_font
from ..ui_components import UIColors


class CharacterScreen:
    def __init__(self, screen: pygame.Surface, player: Any):
        self.screen = screen
        self.player = player
        self.should_close = False
        self.request_levelup = False

        # Fonts
        self.font_header = get_font(24, bold=True)
        self.font_body = get_font(18)
        self.font_small = get_font(16)

        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

    def _draw_frame(self) -> None:
        w, h = self.screen.get_size()

        # Dim background
        self.overlay.fill((0, 0, 0, 160))
        self.screen.blit(self.overlay, (0, 0))

        # Outer border panel
        margin = 40
        panel_rect = pygame.Rect(margin, margin, w - margin * 2, h - margin * 2)
        pygame.draw.rect(self.screen, (35, 35, 48), panel_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), panel_rect, 2)

        # Title
        title = f"CHARACTER STATUS (Level {self.player.stats.level})"
        title_surf = self.font_header.render(title, True, (235, 235, 235))
        title_rect = title_surf.get_rect(center=(w // 2, margin + 22))
        self.screen.blit(title_surf, title_rect)

        # Sections layout
        left_x = panel_rect.x + 30
        right_x = panel_rect.centerx + 20
        cursor_y = panel_rect.y + 70

        # Primary Attributes
        self._draw_section_header("PRIMARY ATTRIBUTES", left_x, cursor_y)
        cursor_y += 26
        self._draw_box(left_x, cursor_y, panel_rect.width // 2 - 50, 180)

        attr_lines = self._build_primary_attr_lines()
        self._draw_lines(attr_lines, left_x + 14, cursor_y + 12)
        cursor_y += 200

        # Meta Stats
        self._draw_section_header("META", left_x, cursor_y)
        cursor_y += 26
        self._draw_box(left_x, cursor_y, panel_rect.width // 2 - 50, 120)
        meta_lines = self._build_meta_lines()
        self._draw_lines(meta_lines, left_x + 14, cursor_y + 12)

        # Combat Stats (right column)
        r_y = panel_rect.y + 70
        self._draw_section_header("COMBAT STATS", right_x, r_y)
        r_y += 26
        self._draw_box(right_x, r_y, panel_rect.width // 2 - 50, 220)
        combat_lines = self._build_combat_lines()
        self._draw_lines(combat_lines, right_x + 14, r_y + 12)

        # Attribute Points footer
        footer_y = panel_rect.bottom - 70
        points = int(getattr(self.player.stats, "attribute_points", 0))
        points_text = f"ATTRIBUTE POINTS: {points}"
        pt_surf = self.font_body.render(points_text, True, (240, 230, 180))
        self.screen.blit(pt_surf, (left_x, footer_y))

        hint1 = "[Press ESC to Close]"
        if points > 0:
            hint2 = "[Press ENTER to Level Up]"
        else:
            hint2 = ""
        hint = (hint2 + "    " + hint1) if hint2 else hint1
        h_surf = self.font_small.render(hint, True, (220, 220, 220))
        h_rect = h_surf.get_rect(right=panel_rect.right - 20, bottom=panel_rect.bottom - 20)
        self.screen.blit(h_surf, h_rect)

    def _draw_section_header(self, text: str, x: int, y: int) -> None:
        lab = self.font_body.render(text, True, (200, 200, 220))
        self.screen.blit(lab, (x, y))

    def _draw_box(self, x: int, y: int, w: int, h: int) -> None:
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (28, 28, 38), rect)
        pygame.draw.rect(self.screen, (120, 120, 140), rect, 1)

    def _draw_lines(self, lines: list[str], x: int, y: int) -> None:
        for i, line in enumerate(lines):
            surf = self.font_small.render(line, True, (235, 235, 235))
            self.screen.blit(surf, (x, y + i * 22))

    def _build_primary_attr_lines(self) -> list[str]:
        s = self.player.stats
        return [
            f"Strength [ {int(s.strength)} ] → ATK +{int((s.strength-10)*2)} , HP +{int((s.strength-10)*2)}",
            f"Agility  [ {int(s.agility)} ] → SPD +{int((s.agility-10)*2)} , Atk Spd {int(-100*s.attack_speed_bonus)}%",
            f"Vitality [ {int(s.vitality)} ] → HP +{int((s.vitality-10)*8)} , Def +{int(100*s.defense)}%",
            f"Charisma [ {int(s.charisma)} ] → Gold +{int(100*(s.gold_bonus-1.0))}% , Troops +{int(100*s.troop_bonus)}%",
            f"Skill    [ {int(s.skill)} ] → Crit {int(100*s.crit_chance)}% , Block {int(100*s.block_power)}%",
        ]

    def _build_combat_lines(self) -> list[str]:
        s = self.player.stats
        return [
            f"HP           {int(s.hp)} / {int(s.hp_max)}",
            f"Attack       {int(s.atk)}",
            f"Speed        {int(s.spd)}",
            f"Stamina Max  {int(s.stamina_max)}",
            f"Crit Chance  {round(100*s.crit_chance, 1)}%",
            f"Crit Damage  {int(100*s.crit_damage)}%",
            f"Block Power  {int(100*s.block_power)}%",
            f"Defense      {int(100*s.defense)}%",
        ]

    def _build_meta_lines(self) -> list[str]:
        s = self.player.stats
        return [
            f"Gold Find    +{int(100*(s.gold_bonus-1.0))}%",
            f"Troop Bonus  +{int(100*s.troop_bonus)}% HP/ATK",
            f"Shop Discount {int(100*s.shop_discount)}%",
        ]

    def run(self) -> str:
        """Modal loop. Returns 'close' or 'levelup'."""
        clock = pygame.time.Clock()
        while not self.should_close:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.should_close = True
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.should_close = True
                        break
                    if event.key == pygame.K_RETURN:
                        if getattr(self.player.stats, 'attribute_points', 0) > 0:
                            self.request_levelup = True
                            self.should_close = True
                            break

            # Redraw behind (no world rerender – assume paused overlay)
            # Caller is responsible for drawing world if desired.
            self._draw_frame()
            pygame.display.flip()

        return 'levelup' if self.request_levelup else 'close'

