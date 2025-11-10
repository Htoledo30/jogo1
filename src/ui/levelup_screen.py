"""Level-up attribute distribution screen.

Simple modal UI that appears when player has attribute points to spend.
"""

import pygame
from typing import Optional
from src.ui_components import Panel, UIColors
from src.attributes import calculate_derived_stats


class LevelUpScreen:
    """Modal screen for distributing attribute points after level up."""

    def __init__(self, screen: pygame.Surface, player):
        self.screen = screen
        self.player = player
        self.font_title = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_main = pygame.font.SysFont("consolas", 20, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 16)

        # Temporary attribute values (can be reverted before confirm)
        self.temp_attrs = {
            'strength': player.stats.strength,
            'agility': player.stats.agility,
            'vitality': player.stats.vitality,
            'charisma': player.stats.charisma,
            'skill': player.stats.skill
        }

        self.points_to_spend = player.stats.attribute_points
        self.points_spent = 0

        # Button positions (will be calculated in render)
        self.buttons = {}

        # Attribute display info
        self.attr_info = {
            'strength': {
                'name': 'STRENGTH',
                'short': 'STR',
                'desc': 'ATK, HP',
                'color': (255, 100, 100)
            },
            'agility': {
                'name': 'AGILITY',
                'short': 'AGI',
                'desc': 'SPD, Attack Speed, Stamina Regen',
                'color': (100, 255, 100)
            },
            'vitality': {
                'name': 'VITALITY',
                'short': 'VIT',
                'desc': 'HP Max, Stamina Max, Defense',
                'color': (100, 200, 255)
            },
            'charisma': {
                'name': 'CHARISMA',
                'short': 'CHA',
                'desc': 'Troop Bonus, Gold Find, Shop Discount',
                'color': (255, 215, 0)
            },
            'skill': {
                'name': 'SKILL',
                'short': 'SKL',
                'desc': 'Crit Chance, Crit Damage, Block Power',
                'color': (200, 150, 255)
            }
        }

    def run(self) -> bool:
        """Run the level-up screen loop until player confirms or cancels.

        Returns:
            True if player confirmed, False if cancelled
        """
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False  # Cancel

                if event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.handle_click(event.pos)
                    if result == "confirm":
                        self.apply_attributes()
                        return True
                    elif result == "cancel":
                        return False

            self.render()
            pygame.display.flip()
            clock.tick(60)

        return False

    def handle_click(self, pos: tuple[int, int]) -> Optional[str]:
        """Handle mouse clicks on buttons.

        Args:
            pos: Mouse position (x, y)

        Returns:
            "confirm" if confirm clicked, "cancel" if cancel clicked, None otherwise
        """
        mouse_x, mouse_y = pos

        # Check attribute +/- buttons
        for attr_name, buttons in self.buttons.items():
            if attr_name in ('confirm', 'cancel'):
                # Special buttons
                if buttons.collidepoint(mouse_x, mouse_y):
                    return attr_name
            else:
                # Attribute buttons
                plus_btn, minus_btn = buttons

                if plus_btn.collidepoint(mouse_x, mouse_y):
                    # Add point to this attribute
                    if self.points_spent < self.points_to_spend:
                        self.temp_attrs[attr_name] += 1
                        self.points_spent += 1

                elif minus_btn.collidepoint(mouse_x, mouse_y):
                    # Remove point from this attribute
                    original_value = getattr(self.player.stats, attr_name)
                    if self.temp_attrs[attr_name] > original_value:
                        self.temp_attrs[attr_name] -= 1
                        self.points_spent -= 1

        return None

    def apply_attributes(self) -> None:
        """Apply temporary attributes to player and recalculate derived stats."""
        self.player.stats.strength = self.temp_attrs['strength']
        self.player.stats.agility = self.temp_attrs['agility']
        self.player.stats.vitality = self.temp_attrs['vitality']
        self.player.stats.charisma = self.temp_attrs['charisma']
        self.player.stats.skill = self.temp_attrs['skill']
        self.player.stats.attribute_points = 0

        # Recalculate all derived stats
        calculate_derived_stats(self.player)

    def render(self) -> None:
        """Render the level-up screen."""
        # Dark overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(220)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Main panel dimensions
        panel_width = 700
        panel_height = 550
        panel_x = (self.screen.get_width() - panel_width) // 2
        panel_y = (self.screen.get_height() - panel_height) // 2

        # Draw main panel
        panel = Panel(panel_x, panel_y, panel_width, panel_height,
                     title="", border_color=(255, 215, 0))
        panel.render(self.screen)

        # Title
        title_text = f"LEVEL UP! (Level {self.player.stats.level})"
        title_surf = self.font_title.render(title_text, True, (255, 215, 0))
        title_x = panel_x + (panel_width - title_surf.get_width()) // 2
        self.screen.blit(title_surf, (title_x, panel_y + 20))

        # Points remaining
        points_text = f"Points to spend: {self.points_to_spend - self.points_spent}/{self.points_to_spend}"
        points_color = (100, 255, 100) if self.points_spent == self.points_to_spend else (255, 200, 100)
        points_surf = self.font_main.render(points_text, True, points_color)
        points_x = panel_x + (panel_width - points_surf.get_width()) // 2
        self.screen.blit(points_surf, (points_x, panel_y + 60))

        # Draw attribute rows
        y_offset = panel_y + 110
        self.buttons.clear()

        attr_names = ['strength', 'agility', 'vitality', 'charisma', 'skill']
        for attr_name in attr_names:
            info = self.attr_info[attr_name]
            original_value = getattr(self.player.stats, attr_name)
            current_value = self.temp_attrs[attr_name]
            diff = current_value - original_value

            # Attribute name and value
            name_surf = self.font_main.render(info['name'], True, info['color'])
            self.screen.blit(name_surf, (panel_x + 30, y_offset))

            value_text = f"[{current_value}]"
            if diff > 0:
                value_text += f" (+{diff})"
                value_color = (100, 255, 100)
            else:
                value_color = UIColors.TEXT_PRIMARY

            value_surf = self.font_main.render(value_text, True, value_color)
            self.screen.blit(value_surf, (panel_x + 240, y_offset))

            # + and - buttons
            btn_size = 30
            btn_y = y_offset - 5

            # Minus button
            minus_btn = pygame.Rect(panel_x + 400, btn_y, btn_size, btn_size)
            minus_color = (100, 100, 100) if diff == 0 else (255, 100, 100)
            pygame.draw.rect(self.screen, minus_color, minus_btn, border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), minus_btn, 2, border_radius=5)
            minus_text = self.font_main.render("-", True, (255, 255, 255))
            self.screen.blit(minus_text, (minus_btn.centerx - 7, minus_btn.centery - 10))

            # Plus button
            plus_btn = pygame.Rect(panel_x + 450, btn_y, btn_size, btn_size)
            plus_color = (100, 100, 100) if self.points_spent >= self.points_to_spend else (100, 255, 100)
            pygame.draw.rect(self.screen, plus_color, plus_btn, border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), plus_btn, 2, border_radius=5)
            plus_text = self.font_main.render("+", True, (255, 255, 255))
            self.screen.blit(plus_text, (plus_btn.centerx - 7, plus_btn.centery - 10))

            # Store button rects
            self.buttons[attr_name] = (plus_btn, minus_btn)

            # Description
            desc_surf = self.font_small.render(f"→ {info['desc']}", True, UIColors.TEXT_SECONDARY)
            self.screen.blit(desc_surf, (panel_x + 500, y_offset + 5))

            y_offset += 70

        # Confirm and Cancel buttons
        btn_width = 150
        btn_height = 50
        btn_y = panel_y + panel_height - 80

        # Cancel button
        cancel_btn = pygame.Rect(panel_x + 150, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.screen, (100, 100, 100), cancel_btn, border_radius=8)
        pygame.draw.rect(self.screen, (200, 200, 200), cancel_btn, 3, border_radius=8)
        cancel_text = self.font_main.render("CANCEL", True, (255, 255, 255))
        self.screen.blit(cancel_text, (cancel_btn.centerx - 40, cancel_btn.centery - 10))
        self.buttons['cancel'] = cancel_btn

        # Confirm button (only active if all points spent)
        confirm_btn = pygame.Rect(panel_x + 400, btn_y, btn_width, btn_height)
        can_confirm = self.points_spent == self.points_to_spend
        confirm_color = (100, 255, 100) if can_confirm else (60, 60, 60)
        pygame.draw.rect(self.screen, confirm_color, confirm_btn, border_radius=8)
        pygame.draw.rect(self.screen, (200, 200, 200), confirm_btn, 3, border_radius=8)
        confirm_text = self.font_main.render("CONFIRM", True, (255, 255, 255) if can_confirm else (120, 120, 120))
        self.screen.blit(confirm_text, (confirm_btn.centerx - 45, confirm_btn.centery - 10))

        if can_confirm:
            self.buttons['confirm'] = confirm_btn

        # Instructions
        if not can_confirm:
            instr_text = "Spend all points to confirm"
            instr_surf = self.font_small.render(instr_text, True, (255, 200, 100))
            instr_x = panel_x + (panel_width - instr_surf.get_width()) // 2
            self.screen.blit(instr_surf, (instr_x, btn_y - 35))
