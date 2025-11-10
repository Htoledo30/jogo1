"""
Menu screens and notification system for the game.

Contains main menu, pause menu, notifications, and tooltips.
"""

import time
import pygame
from ..constants import SCREEN_WIDTH, SCREEN_HEIGHT


# Global notification storage
active_notifications = []


def draw_main_menu(screen, selected_option, has_save=False):
    """Draw the main menu screen."""
    screen.fill((15, 15, 25))

    # Title
    font_title = pygame.font.Font(None, 80)
    font_menu = pygame.font.Font(None, 40)
    font_small = pygame.font.Font(None, 24)

    title_surf = font_title.render("MOUNT & BLADE 2D", True, (255, 215, 0))
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
    screen.blit(title_surf, title_rect)

    subtitle_surf = font_small.render("RPG Edition", True, (200, 200, 200))
    subtitle_rect = subtitle_surf.get_rect(center=(SCREEN_WIDTH // 2, 210))
    screen.blit(subtitle_surf, subtitle_rect)

    # Menu options
    menu_options = ["New Game", "Load Game", "Quit"]
    if not has_save:
        menu_options = ["New Game", "Quit"]

    menu_y_start = 300
    for i, option in enumerate(menu_options):
        color = (255, 255, 100) if i == selected_option else (200, 200, 200)
        if i == selected_option:
            # Draw selection indicator
            indicator = "> "
        else:
            indicator = "  "

        option_surf = font_menu.render(f"{indicator}{option}", True, color)
        option_rect = option_surf.get_rect(center=(SCREEN_WIDTH // 2, menu_y_start + i * 60))
        screen.blit(option_surf, option_rect)

    # Controls hint
    hint_surf = font_small.render("Use ARROW KEYS to navigate, ENTER to select", True, (150, 150, 150))
    hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
    screen.blit(hint_surf, hint_rect)


def draw_pause_menu(screen, selected_option):
    """Draw the pause menu overlay."""
    # Darken the background
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # Draw menu
    font_title = pygame.font.Font(None, 60)
    font_menu = pygame.font.Font(None, 36)

    title_surf = font_title.render("PAUSED", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))
    screen.blit(title_surf, title_rect)

    # Menu options
    menu_options = ["Resume", "Save Game", "Quit to Menu", "Quit Game"]
    menu_y_start = 300

    for i, option in enumerate(menu_options):
        color = (255, 255, 100) if i == selected_option else (200, 200, 200)
        if i == selected_option:
            indicator = "> "
        else:
            indicator = "  "

        option_surf = font_menu.render(f"{indicator}{option}", True, color)
        option_rect = option_surf.get_rect(center=(SCREEN_WIDTH // 2, menu_y_start + i * 50))
        screen.blit(option_surf, option_rect)


def show_notification(screen, text, duration=1.5, color=(220, 220, 180)):
    """Adds a notification to the list (non-blocking)."""
    # This function now just adds to the global list.
    # Rendering happens in the main loop.
    global active_notifications
    expiration_time = time.time() + duration
    active_notifications.append((text, color, expiration_time))


def render_notifications(screen):
    """Renderiza todas as notificações ativas (chamado no loop principal)."""
    global active_notifications

    # Remove expired notifications
    current_time = time.time()
    active_notifications = [(text, color, exp_time) for text, color, exp_time in active_notifications if exp_time > current_time]

    # Render active notifications
    font = pygame.font.Font(None, 32)
    y_offset = SCREEN_HEIGHT // 2

    for i, (text, color, exp_time) in enumerate(active_notifications):
        prompt_surf = font.render(text, True, color)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, y_offset + i * 40))
        bg_rect = prompt_rect.inflate(20, 10)

        pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect)
        screen.blit(prompt_surf, prompt_rect)


def render_tooltip(screen, text, pos):
    """Renders a tooltip box near the mouse."""
    if not text:
        return

    font = pygame.font.Font(None, 20)
    tooltip_surf = font.render(text, True, (220, 220, 220))

    padding = 10
    bg_rect = tooltip_surf.get_rect().inflate(padding, padding)
    bg_rect.topleft = (pos[0] + 15, pos[1] + 15) # Offset from cursor

    pygame.draw.rect(screen, (20, 20, 30, 230), bg_rect)
    screen.blit(tooltip_surf, (bg_rect.x + padding // 2, bg_rect.y + padding // 2))
