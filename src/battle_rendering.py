"""Battle rendering module - All visual rendering functions.

Extracted from battle.py to improve code organization and maintainability.
Contains all rendering methods for entities, UI, attacks, and effects.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
import math
import os
import pygame
from src import vfx
from src import battle_sprites
from src import troop_sprites
from src import enemy_sprites
from src.constants import ARENA_WIDTH as GLOBAL_ARENA_WIDTH, ARENA_HEIGHT as GLOBAL_ARENA_HEIGHT

if TYPE_CHECKING:
    from src.battle import BattleController

# Constants (sync with global constants)
ARENA_WIDTH = GLOBAL_ARENA_WIDTH
ARENA_HEIGHT = GLOBAL_ARENA_HEIGHT
ARENA_BORDER = 40

# Arrow sprite cache
_ARROW_SPRITES: dict[str, pygame.Surface] = {}


def _load_arrow_sprite(team: str) -> pygame.Surface | None:
    """Load arrow sprite based on team (ally=blue, enemy=red)."""
    if team in _ARROW_SPRITES:
        return _ARROW_SPRITES[team]

    # Map teams to arrow colors
    color_map = {
        "ally": "Blue Units",
        "enemy": "Red Units",  # Default for enemies
    }

    color_folder = color_map.get(team, "Red Units")
    path = os.path.join("Tiny Swords (Free Pack)", "Units", color_folder, "Archer", "Arrow.png")

    try:
        sprite = pygame.image.load(path).convert_alpha()
        _ARROW_SPRITES[team] = sprite
        return sprite
    except Exception:
        _ARROW_SPRITES[team] = None
        return None


# -----------------------------------------------------------------------------
def render_battle(battle: 'BattleController', screen: pygame.Surface) -> None:
    """Render complete battle scene.

    Args:
        battle: BattleController instance with all battle state
        screen: Pygame surface to draw on
    """
    # Apply screen shake
    shake_x = 0
    shake_y = 0
    if battle.screen_shake > 0:
        shake_x = battle.rng.randint(-int(battle.screen_shake * 10), int(battle.screen_shake * 10))
        shake_y = battle.rng.randint(-int(battle.screen_shake * 10), int(battle.screen_shake * 10))

    # Background
    screen.blit(vfx.BATTLE_GROUND_TEXTURE, (0, 0))

    # Arena border
    pygame.draw.rect(screen, (40, 50, 80), pygame.Rect(ARENA_BORDER, ARENA_BORDER,
                                                       ARENA_WIDTH - 2 * ARENA_BORDER,
                                                       ARENA_HEIGHT - 2 * ARENA_BORDER), 2)

    render_arena_features(battle, screen)

    # Update player animation state (idle/run) using last dt stored in battle
    try:
        dt = float(getattr(battle, "_last_dt", 1.0/60.0))
        from src import battle_sprites as _bs
        _bs.update_player_animation(battle, dt)
    except Exception:
        pass

    # Render entities (troops, player, enemies)
    render_entities(battle, screen, shake_x, shake_y)
    render_troops(battle, screen, shake_x, shake_y)

    # Render attack indicators
    render_attacks(battle, screen, shake_x, shake_y)

    # Render projectiles (arrows, sling stones, etc)
    render_projectiles(battle, screen, shake_x, shake_y)

    # Render particles
    vfx.render_particles(screen)

    # Render hit flashes
    for x, y, time_left, color in battle.hit_flashes:
        alpha = int(255 * (time_left / 0.3))
        size = int(20 * (1 - time_left / 0.3))
        pygame.draw.circle(screen, color, (int(x + shake_x), int(y + shake_y)), 10 + size, 3)

    # Render damage numbers
    font_dmg = pygame.font.SysFont("consolas", 24, bold=True)
    for x, y, time_left, damage, color in battle.damage_numbers:
        progress = 1 - (time_left / 1.0)
        offset_y = int(progress * 40)  # Float upward
        alpha = int(255 * (time_left / 1.0))

        if damage == 0:
            text = "PARRY!"
        else:
            text = str(damage)

        surf = font_dmg.render(text, True, color)
        screen.blit(surf, (int(x + shake_x - 15), int(y + shake_y - offset_y)))

    # Render AIM LINE from player to mouse (shows attack direction!)
    mouse_pos = pygame.mouse.get_pos()
    player_screen = (int(battle.player.pos[0] + shake_x), int(battle.player.pos[1] + shake_y))

    # Draw dashed line from player to mouse
    dx = mouse_pos[0] - player_screen[0]
    dy = mouse_pos[1] - player_screen[1]
    distance = math.hypot(dx, dy)

    if distance > 5:  # Only draw if mouse is not on player
        # Draw dashed line (10 pixel dash, 5 pixel gap)
        dash_length = 10
        gap_length = 5
        total_length = dash_length + gap_length
        num_dashes = int(distance / total_length)

        for i in range(num_dashes):
            start_dist = i * total_length
            end_dist = start_dist + dash_length
            if end_dist > distance:
                end_dist = distance

            start_x = player_screen[0] + (dx / distance) * start_dist
            start_y = player_screen[1] + (dy / distance) * start_dist
            end_x = player_screen[0] + (dx / distance) * end_dist
            end_y = player_screen[1] + (dy / distance) * end_dist

            pygame.draw.line(screen, (255, 255, 100, 150), (int(start_x), int(start_y)), (int(end_x), int(end_y)), 2)

    # Render crosshair (mouse cursor)
    pygame.draw.circle(screen, (255, 255, 255), mouse_pos, 3, 1)
    pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0] - 8, mouse_pos[1]), (mouse_pos[0] - 3, mouse_pos[1]))
    pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0] + 3, mouse_pos[1]), (mouse_pos[0] + 8, mouse_pos[1]))
    pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0], mouse_pos[1] - 8), (mouse_pos[0], mouse_pos[1] - 3))
    pygame.draw.line(screen, (255, 255, 255), (mouse_pos[0], mouse_pos[1] + 3), (mouse_pos[0], mouse_pos[1] + 8))

    # Battle UI
    render_battle_ui(battle, screen)


def render_projectiles(battle: 'BattleController', screen: pygame.Surface, shake_x: int, shake_y: int) -> None:
    """Render all active projectiles (arrows with sprites).

    Args:
        battle: BattleController instance
        screen: Pygame surface
        shake_x: Screen shake offset X
        shake_y: Screen shake offset Y
    """
    if not hasattr(battle, 'projectiles') or not battle.projectiles:
        return

    for proj in battle.projectiles.projectiles:
        # Calculate screen position with shake
        proj_x = int(proj.x + shake_x)
        proj_y = int(proj.y + shake_y)

        # Try to load arrow sprite
        arrow_sprite = _load_arrow_sprite(proj.team)

        if arrow_sprite:
            # Use arrow sprite with rotation
            # Calculate angle based on velocity
            angle = math.degrees(math.atan2(-proj.vy, proj.vx))  # Negative vy because Y is down

            # Scale arrow to appropriate size (larger for visibility)
            target_size = (48, 12)  # Width x Height for arrow
            arrow_scaled = pygame.transform.smoothscale(arrow_sprite, target_size)

            # Rotate arrow to face direction of movement
            arrow_rotated = pygame.transform.rotate(arrow_scaled, angle)

            # Get rect and center it on projectile position
            arrow_rect = arrow_rotated.get_rect(center=(proj_x, proj_y))

            # Draw arrow sprite
            screen.blit(arrow_rotated, arrow_rect)

        else:
            # Fallback: draw as circle if sprite fails to load
            if proj.team == "ally":
                color = (100, 255, 150)  # Green for friendly
            else:
                color = (255, 100, 100)  # Red for enemy

            pygame.draw.circle(screen, color, (proj_x, proj_y), int(proj.radius))


def render_arena_features(battle: 'BattleController', screen: pygame.Surface) -> None:
    variant = getattr(battle, "arena_variant", None)
    if variant is None:
        return

    ambient = variant.get("ambient_tint")
    if ambient:
        overlay = pygame.Surface((ARENA_WIDTH, ARENA_HEIGHT), pygame.SRCALPHA)
        overlay.fill(ambient)
        screen.blit(overlay, (0, 0))

    for feature in variant.get("decor", []):
        ftype = feature.get("type")
        if ftype == "hill_polygon":
            rect = getattr(battle, "hill_zone", None)
            if not rect or rect.width <= 0 or rect.height <= 0:
                continue
            shape = [
                (rect.left, rect.centery),
                (rect.left + 50, rect.top),
                (rect.right - 50, rect.top),
                (rect.right, rect.centery),
                (rect.right - 50, rect.bottom),
                (rect.left + 50, rect.bottom)
            ]
            hill_overlay = pygame.Surface((ARENA_WIDTH, ARENA_HEIGHT), pygame.SRCALPHA)
            fill_color = feature.get("fill", (139, 90, 43, 70))
            pygame.draw.polygon(hill_overlay, fill_color, shape)
            outline_color = feature.get("outline")
            if outline_color:
                pygame.draw.aalines(hill_overlay, outline_color[:3], True, shape)
            screen.blit(hill_overlay, (0, 0))

        elif ftype in ("ellipse", "rect", "plateau"):
            rect_tuple = feature.get("rect")
            if not rect_tuple:
                continue
            rect = pygame.Rect(rect_tuple)
            surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            color = feature.get("color", (120, 120, 120, 110))
            border_color = feature.get("border_color")
            border_width = feature.get("border_width", 2)
            border_radius = feature.get("border_radius", 0)
            if ftype == "ellipse":
                pygame.draw.ellipse(surface, color, surface.get_rect())
                if border_color:
                    pygame.draw.ellipse(surface, border_color, surface.get_rect(), border_width)
            else:  # rect / plateau
                pygame.draw.rect(surface, color, surface.get_rect(), border_radius=border_radius)
                if border_color:
                    pygame.draw.rect(surface, border_color, surface.get_rect(), border_width, border_radius=border_radius)
                if ftype == "plateau":
                    diag_color = feature.get("detail_color", (230, 230, 240, 80))
                    pygame.draw.line(surface, diag_color, (0, surface.get_height() // 2), (surface.get_width(), surface.get_height() // 2), 2)
                    pygame.draw.line(surface, diag_color, (surface.get_width() // 2, 0), (surface.get_width() // 2, surface.get_height()), 2)
            screen.blit(surface, rect.topleft)

        elif ftype == "scatter":
            for point in feature.get("points", []):
                if len(point) < 4:
                    continue
                x, y, radius, color = point[:4]
                scatter_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(scatter_surface, color, (radius, radius), radius)
                if len(point) >= 5 and point[4]:
                    pygame.draw.circle(scatter_surface, point[4], (radius, radius), radius, 1)
                screen.blit(scatter_surface, (int(x - radius), int(y - radius)))


def render_battle_ui(battle: 'BattleController', screen: pygame.Surface) -> None:
    """Render battle-specific UI elements.

    Args:
        battle: BattleController instance
        screen: Pygame surface
    """
    font_ui = pygame.font.SysFont("consolas", 20, bold=True)

    arena_variant = getattr(battle, "arena_variant", None)
    arena_name = arena_variant.get("name") if arena_variant else None
    if arena_name:
        name_font = pygame.font.SysFont("consolas", 22, bold=True)
        name_surf = name_font.render(arena_name, True, (200, 200, 230))
        screen.blit(name_surf, (ARENA_WIDTH // 2 - name_surf.get_width() // 2, 12))

    # Combo counter - ENHANCED VISUAL FEEDBACK
    if battle.combo_chain_hits > 0:
        tier = battle.combo_levels[battle.combo_chain_level]
        color = tier.get("color", (255, 200, 120))
        combo_text = f"{tier['label']}  x{battle.combo_chain_hits}"
        bonus_text = f"{tier['mult']:.2f}x"

        pulse = 1.0 + 0.2 * math.sin(pygame.time.get_ticks() * 0.01)
        pulse += battle.combo_chain_feedback * 1.2
        font_size = max(24, int(26 * pulse))
        combo_font = pygame.font.SysFont("consolas", font_size, bold=True)
        combo_surf = combo_font.render(combo_text, True, color)

        bonus_font = pygame.font.SysFont("consolas", 18, bold=True)
        bonus_surf = bonus_font.render(bonus_text, True, (240, 240, 240))

        combo_x = 20
        combo_y = ARENA_HEIGHT - 100

        glow_width = combo_surf.get_width() + 30
        glow_height = combo_surf.get_height() + bonus_surf.get_height() + 26
        glow_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
        glow_alpha = int(70 + 110 * min(1.0, battle.combo_chain_feedback + 0.2))
        pygame.draw.rect(glow_surf, (*color, glow_alpha),
                         pygame.Rect(0, 0, glow_width, glow_height), border_radius=10)
        screen.blit(glow_surf, (combo_x - 10, combo_y - 16))

        screen.blit(combo_surf, (combo_x, combo_y))
        screen.blit(bonus_surf, (combo_x, combo_y + combo_surf.get_height() - 4))

    # Formation indicator
    formation_names = {0: "CIRCLE", 1: "LINE", 2: "WEDGE"}
    formation_text = f"Formation: {formation_names.get(battle.formation_mode, 'UNKNOWN')}"
    formation_surf = font_ui.render(formation_text, True, (180, 180, 220))
    screen.blit(formation_surf, (20, ARENA_HEIGHT - 50))

    # High ground indicator
    from src import battle_systems
    if battle_systems.is_on_high_ground(battle, battle.player):
        terrain_text = "HIGH GROUND (+20% DMG, +10% DEF)"
        terrain_surf = font_ui.render(terrain_text, True, (255, 215, 0))
        screen.blit(terrain_surf, (ARENA_WIDTH // 2 - terrain_surf.get_width() // 2, 50))

    # Team labels and alive counters (AI vs AI)
    try:
        alive_a = sum(1 for e in battle.enemies if getattr(e, 'alive', lambda: True)() and getattr(e, 'team', 'A') == 'A')
        alive_b = sum(1 for e in battle.enemies if getattr(e, 'alive', lambda: True)() and getattr(e, 'team', 'A') == 'B')
        if alive_b > 0:
            a_s = font_ui.render(f"Side A: {alive_a}", True, (180, 220, 255))
            b_s = font_ui.render(f"Side B: {alive_b}", True, (255, 180, 180))
            screen.blit(a_s, (20, 20))
            screen.blit(b_s, (ARENA_WIDTH - b_s.get_width() - 20, 20))
    except (AttributeError, TypeError) as e:
        # Silently skip if team attributes not available (normal for non-AI battles)
        pass

    # Troop Order display (top center)
    try:
        order_name = getattr(battle, 'troop_order', 'FOLLOW')
        order_text = f"ORDER: {order_name}"
        color = (255, 200, 80) if battle.order_flash_timer > 0 else (200, 220, 255)
        order_surf = font_ui.render(order_text, True, color)
        screen.blit(order_surf, (ARENA_WIDTH // 2 - order_surf.get_width() // 2, 20))
    except (AttributeError, TypeError):
        # Silently skip if order attributes not available
        pass

    # Focus reticle on target (FOCUS)
    if getattr(battle, 'troop_order', 'FOLLOW') == 'FOCUS' and getattr(battle, 'focus_target_id', None):
        for e in battle.enemies:
            if e.alive() and e.id == battle.focus_target_id:
                x, y = int(e.pos[0]), int(e.pos[1])
                pygame.draw.circle(screen, (255, 230, 100), (x, y), max(16, int(e.radius) + 6), 2)
                pygame.draw.circle(screen, (255, 230, 100), (x, y), max(20, int(e.radius) + 10), 1)
                break


def render_entities(battle: 'BattleController', screen: pygame.Surface, shake_x: int, shake_y: int) -> None:
    """Render player and enemies.

    Args:
        battle: BattleController instance
        screen: Pygame surface
        shake_x: Screen shake offset X
        shake_y: Screen shake offset Y
    """
    # Player
    player_pos_screen = (int(battle.player.pos[0] + shake_x), int(battle.player.pos[1] + shake_y))
    vfx.draw_entity_shadow(screen, player_pos_screen, battle.player.radius)

    if battle.player.alive():
        # Try to render sprite; fallback to circle if not available
        drawn = battle_sprites.draw_player_sprite(battle, screen, player_pos_screen)
        if not drawn:
            color = (80, 220, 140)
            if battle.player._invuln > 0:
                flash = int((battle.player._invuln / 0.3) * 200)
                color = (min(255, 80 + flash), min(255, 220 + flash // 2), min(255, 140 + flash))
            if battle.player_blocking:
                color = (60, 180, 220)
            pygame.draw.circle(screen, color, player_pos_screen, int(battle.player.radius))
        # Shield ring when blocking (works for sprite or fallback)
        if battle.player_blocking:
            pygame.draw.circle(screen, (100, 200, 255), player_pos_screen, int(battle.player.radius + 5), 2)
    else:
        # Dead player (gray)
        pygame.draw.circle(screen, (80, 80, 80), player_pos_screen, int(battle.player.radius))

    # Enemies
    # Get relations for faction-based coloring (may be None)
    relations = getattr(battle, 'player_relations', None)

    for enemy in battle.enemies:
        if enemy.alive():
            enemy_pos_screen = (int(enemy.pos[0] + shake_x), int(enemy.pos[1] + shake_y))
            vfx.draw_entity_shadow(screen, enemy_pos_screen, enemy.radius)

            # Update facing direction
            prev_pos = battle.prev_positions.get(enemy.id)
            enemy_sprites.update_enemy_facing(enemy, prev_pos)

            # Check states for visual effects
            is_stunned = battle.enemy_stun_times.get(enemy.id, 0.0) > 0.0
            is_blocking = battle.enemy_blocking_states.get(enemy.id, False)

            # Try to render sprite; fallback to circle if not available
            drawn = enemy_sprites.draw_enemy_sprite(enemy, screen, enemy_pos_screen, relations)

            if not drawn:
                # Fallback: VARIED COLORS BY ENEMY TYPE
                enemy_type = getattr(enemy, 'enemy_type', 'bandit')
                if enemy_type == "bandit":
                    color = (220, 80, 80)  # Red
                elif enemy_type == "soldier":
                    color = (100, 100, 180)  # Blue (kingdom colors)
                elif enemy_type == "brute":
                    color = (180, 100, 40)  # Brown/orange (berserker)
                elif enemy_type == "beast":
                    color = (140, 80, 140)  # Purple (monster)
                else:
                    color = (220, 80, 80)  # Default red

                # Check if stunned (yellow tint)
                is_stunned = battle.enemy_stun_times.get(enemy.id, 0.0) > 0.0
                if is_stunned:
                    color = (200, 200, 80)

                # Darker tint when blocking
                is_blocking = battle.enemy_blocking_states.get(enemy.id, False)
                if is_blocking:
                    color = tuple(int(c * 0.6) for c in color)  # Darken by 40%

                # Flash when invulnerable
                if enemy._invuln > 0:
                    flash = int((enemy._invuln / 0.3) * 150)
                    color = (min(255, 220 + flash // 2), min(255, 80 + flash), min(255, 80 + flash))

                pygame.draw.circle(screen, color, enemy_pos_screen, int(enemy.radius))

            # IMPROVED BLOCKING VISUAL - much more obvious!
            if is_blocking:
                # Multiple bright blue shield rings
                for ring_offset in range(0, 20, 5):
                    ring_radius = enemy.radius + 8 + ring_offset
                    pygame.draw.circle(screen, (100, 200, 255), enemy_pos_screen, ring_radius, 3)

                # Bright blue glow effect
                shield_surf = pygame.Surface((enemy.radius * 3, enemy.radius * 3), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (100, 200, 255, 80),
                                 (enemy.radius * 1.5, enemy.radius * 1.5), enemy.radius + 10)
                screen.blit(shield_surf, (enemy_pos_screen[0] - enemy.radius * 1.5,
                                         enemy_pos_screen[1] - enemy.radius * 1.5))

                # "BLOCKING" text above enemy
                font = pygame.font.Font(None, 18)
                block_text = font.render("BLOCKING", True, (100, 220, 255))
                text_pos = (enemy_pos_screen[0] - 30, enemy_pos_screen[1] - 50)
                screen.blit(block_text, text_pos)

            # Stars when stunned
            if is_stunned:
                star_y = int(enemy.pos[1] + shake_y - enemy.radius - 15)
                pygame.draw.circle(screen, (255, 255, 100), (int(enemy.pos[0] + shake_x - 10), star_y), 3)
                pygame.draw.circle(screen, (255, 255, 100), (int(enemy.pos[0] + shake_x + 10), star_y), 3)

            # Enemy HP bar
            hp_ratio = enemy.stats.hp / enemy.stats.hp_max
            bar_width = 40
            bar_height = 4
            bar_x = int(enemy.pos[0] + shake_x - bar_width // 2)
            bar_y = int(enemy.pos[1] + shake_y - enemy.radius - 10)
            pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (200, 50, 50), pygame.Rect(bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        else:
            # Dead enemy (dark red X)
            enemy_pos_screen = (int(enemy.pos[0] + shake_x), int(enemy.pos[1] + shake_y))
            vfx.draw_entity_shadow(screen, enemy_pos_screen, enemy.radius)

            pygame.draw.circle(screen, (60, 20, 20), enemy_pos_screen, int(enemy.radius))
            # Draw X
            size = enemy.radius * 0.7
            cx, cy = enemy_pos_screen
            pygame.draw.line(screen, (100, 40, 40), (cx - size, cy - size), (cx + size, cy + size), 3)
            pygame.draw.line(screen, (100, 40, 40), (cx - size, cy + size), (cx + size, cy - size), 3)


def render_troops(battle: 'BattleController', screen: pygame.Surface, shake_x: int, shake_y: int) -> None:
    """Render allied troops.

    Args:
        battle: BattleController instance
        screen: Pygame surface
        shake_x: Screen shake offset X
        shake_y: Screen shake offset Y
    """
    for troop in battle.troops:
        if troop.alive():
            troop_pos_screen = (int(troop.pos[0] + shake_x), int(troop.pos[1] + shake_y))
            vfx.draw_entity_shadow(screen, troop_pos_screen, troop.radius)

            # Update facing direction
            prev_pos = battle.prev_positions.get(troop.id)
            troop_sprites.update_troop_facing(troop, prev_pos)

            # Try to render sprite; fallback to circle if not available
            drawn = troop_sprites.draw_troop_sprite(troop, screen, troop_pos_screen)

            if not drawn:
                # Fallback: Troop colors based on type
                troop_type = getattr(troop, 'troop_type', 'warrior')
                if troop_type == "warrior":
                    color = (100, 150, 255)  # Blue
                elif troop_type == "archer":
                    color = (100, 255, 150)  # Green
                elif troop_type == "tank":
                    color = (255, 200, 100)  # Orange
                else:
                    color = (100, 150, 255)

                # Veterancy visual: Tiers
                if troop.stats.level >= 2:
                    color = (100, 150, 255)

                # Flash when invulnerable
                if troop._invuln > 0:
                    flash = int((troop._invuln / 0.3) * 150)
                    color = (min(255, color[0] + flash // 2), min(255, color[1] + flash), min(255, color[2] + flash))

                pygame.draw.circle(screen, color, troop_pos_screen, int(troop.radius))

            # Veterancy visual: Borda por Tier
            if troop.stats.level == 2:
                pygame.draw.circle(screen, (200, 200, 255), (int(troop.pos[0] + shake_x), int(troop.pos[1] + shake_y)), int(troop.radius), 2)
            elif troop.stats.level >= 3:
                pygame.draw.circle(screen, (255, 215, 0), (int(troop.pos[0] + shake_x), int(troop.pos[1] + shake_y)), int(troop.radius), 2)
                pygame.draw.circle(screen, (255, 255, 255), (int(troop.pos[0] + shake_x), int(troop.pos[1] + shake_y)), int(troop.radius - 3), 1)

            # Troop HP bar
            hp_ratio = troop.stats.hp / troop.stats.hp_max
            bar_width = 35
            bar_height = 3
            bar_x = int(troop.pos[0] + shake_x - bar_width // 2)
            bar_y = int(troop.pos[1] + shake_y - troop.radius - 8)
            pygame.draw.rect(screen, (40, 40, 40), pygame.Rect(bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (100, 200, 255), pygame.Rect(bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

            # Veterancy: XP bar for troops
            xp_ratio = troop.stats.xp / max(1, troop.stats.xp_to_next_level)
            xp_bar_y = bar_y + bar_height + 1
            xp_bar_width = int(bar_width * xp_ratio)
            pygame.draw.rect(screen, (60, 40, 80), pygame.Rect(bar_x, xp_bar_y, bar_width, 2))
            pygame.draw.rect(screen, (200, 150, 255), pygame.Rect(bar_x, xp_bar_y, xp_bar_width, 2))

            # Type indicator (letter)
            font_small = pygame.font.SysFont("consolas", 12, bold=True)
            type_letter = troop_type[0].upper()  # W, A, T
            type_surf = font_small.render(type_letter, True, (0, 0, 0, 150))
            screen.blit(type_surf, (int(troop.pos[0] + shake_x - 4), int(troop.pos[1] + shake_y - 6)))
        else:
            # Dead troop (dark blue)
            troop_pos_screen = (int(troop.pos[0] + shake_x), int(troop.pos[1] + shake_y))
            vfx.draw_entity_shadow(screen, troop_pos_screen, troop.radius)

            pygame.draw.circle(screen, (40, 60, 100), troop_pos_screen, int(troop.radius))


def render_attacks(battle: 'BattleController', screen: pygame.Surface, shake_x: int, shake_y: int) -> None:
    """Render attack indicators with CLEAR visual feedback.

    Args:
        battle: BattleController instance
        screen: Pygame surface
        shake_x: Screen shake offset X
        shake_y: Screen shake offset Y
    """
    # Player attack arc - directional with BIG VISIBLE ARC
    if battle.player_attack_duration > 0.0:
        progress = 1 - (battle.player_attack_duration / 0.2)
        arc_radius = battle.player.radius + 50 + (progress * 30)  # Larger arc!

        # Determine attack angle based on direction
        dx, dy = battle.player_attack_direction
        attack_angle = math.atan2(dy, dx)

        # Combo visual: arc color pulls from combo tier palette
        tier = battle.combo_levels[battle.combo_chain_level]
        color = tier.get("color", (255, 255, 150))

        # DRAW BIG VISIBLE ARC (not just particles!)
        player_screen = (int(battle.player.pos[0] + shake_x), int(battle.player.pos[1] + shake_y))

        # Draw attack arc (90 degree sweep)
        arc_start = attack_angle - math.pi / 4  # -45 degrees
        arc_end = attack_angle + math.pi / 4  # +45 degrees

        # Draw multiple arc lines for visibility
        for radius_offset in range(0, 40, 8):
            current_radius = int(arc_radius + radius_offset)
            alpha = int(255 * (1 - progress) * (1 - radius_offset / 40))
            arc_color = (*color, max(100, alpha))

            # Draw arc using multiple line segments
            segments = 20
            points = []
            for i in range(segments + 1):
                angle = arc_start + (arc_end - arc_start) * (i / segments)
                x = player_screen[0] + math.cos(angle) * current_radius
                y = player_screen[1] + math.sin(angle) * current_radius
                points.append((int(x), int(y)))

            if len(points) > 1:
                pygame.draw.lines(screen, arc_color[:3], False, points, 3)

        # Add attack type indicator text
        type_text = battle.player_attack_type.upper()
        font = pygame.font.Font(None, 24)
        text_surf = font.render(type_text, True, color)
        text_surf.set_alpha(int(200 * (1 - progress)))
        text_pos = (player_screen[0] - 30, player_screen[1] - 60)
        screen.blit(text_surf, text_pos)

        # Create a trail of particles along the arc (keep original)
        for i in range(5):
            angle = attack_angle + battle.rng.uniform(-0.6, 0.6)
            vfx.create_weapon_trail(battle.player.pos, angle, color)

    # Enemy attack indicators - IMPROVED VISUAL FEEDBACK
    for enemy in battle.enemies:
        if not enemy.alive():
            continue
        duration = battle.enemy_attack_durations.get(enemy.id, 0.0)
        if duration > 0.0:
            progress = 1 - (duration / 0.3)
            enemy_screen = (int(enemy.pos[0] + shake_x), int(enemy.pos[1] + shake_y))

            # Large expanding attack circle (much more visible!)
            radius_base = enemy.radius + 30
            radius_grow = progress * 50  # Grows 50 pixels
            current_radius = int(radius_base + radius_grow)

            # Bright orange/red color
            alpha = int(220 * (1 - progress))
            attack_color = (255, 120, 0)  # Bright orange

            # Draw multiple concentric circles for visibility
            for offset in range(0, 15, 5):
                r = current_radius - offset
                circle_alpha = max(100, alpha - offset * 10)
                pygame.draw.circle(screen, attack_color, enemy_screen, r, 3)

            # Add "ATTACKING!" text above enemy
            font = pygame.font.Font(None, 20)
            attack_text = font.render("ATTACKING", True, (255, 200, 0))
            attack_text.set_alpha(int(200 * (1 - progress)))
            text_pos = (enemy_screen[0] - 35, enemy_screen[1] - 50)
            screen.blit(attack_text, text_pos)
