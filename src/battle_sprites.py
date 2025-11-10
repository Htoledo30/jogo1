"""Battle-only sprite helpers (player).

Centralizes the player sprite rendering for arenas, keeping overworld untouched.
"""

from __future__ import annotations
import os
import math
import pygame

from .sprite_manager import load_spritesheet
from .animation import AnimationController, Animation

# Public knobs
PLAYER_SPRITE_HEIGHT_PER_RADIUS = 6.0
PLAYER_SPRITE_FOOT_OFFSET_PCT = 0.40

# Animation settings
# Instant switch request: keep threshold very low so any movement flips to run
ANIMATION_IDLE_THRESHOLD = 0.1  # pixels/second

_CACHE: dict[str, list[pygame.Surface]] = {}
_PLAYER_ANIMATION_CONTROLLERS: dict[int, AnimationController] = {}
# Track last seen player position per frame (independent from battle.prev_positions)
_LAST_PLAYER_POS: dict[int, tuple[float, float]] = {}
# Track facing direction (True = facing right, False = facing left)
_PLAYER_FACING_RIGHT: dict[int, bool] = {}


def _get_player_idle_frames() -> list[pygame.Surface]:
    key = "player_idle"
    if key in _CACHE:
        return _CACHE[key]
    path = os.path.join(
        "Tiny Swords (Free Pack)", "Units", "Blue Units", "Warrior", "Warrior_Idle.png"
    )
    try:
        sheet = pygame.image.load(path).convert_alpha()
        sw, sh = sheet.get_width(), sheet.get_height()
        frames = load_spritesheet(path, sh, sh)
        if len(frames) <= 1 and sw > 0:
            # Fallback: assume 8 frames laid horizontally
            fw = max(1, sw // 8)
            frames = load_spritesheet(path, fw, sh, num_frames=8)
    except Exception:
        frames = []
    _CACHE[key] = frames
    return frames


def _get_player_run_frames() -> list[pygame.Surface]:
    """Load Warrior_Run.png frames."""
    key = "player_run"
    if key in _CACHE:
        return _CACHE[key]
    path = os.path.join(
        "Tiny Swords (Free Pack)", "Units", "Blue Units", "Warrior", "Warrior_Run.png"
    )
    try:
        sheet = pygame.image.load(path).convert_alpha()
        sw, sh = sheet.get_width(), sheet.get_height()
        frames = load_spritesheet(path, sh, sh)

        if len(frames) <= 1 and sw > 0:
            # Fallback: assume 8 frames laid horizontally
            fw = max(1, sw // 8)
            frames = load_spritesheet(path, fw, sh, num_frames=8)
    except Exception:
        frames = []
    _CACHE[key] = frames
    return frames


def _get_player_guard_frames() -> list[pygame.Surface]:
    """Load Warrior_Guard.png frames."""
    key = "player_guard"
    if key in _CACHE:
        return _CACHE[key]
    path = os.path.join(
        "Tiny Swords (Free Pack)", "Units", "Blue Units", "Warrior", "Warrior_Guard.png"
    )
    try:
        sheet = pygame.image.load(path).convert_alpha()
        sw, sh = sheet.get_width(), sheet.get_height()
        frames = load_spritesheet(path, sh, sh)
        if len(frames) <= 1 and sw > 0:
            fw = max(1, sw // 8)
            frames = load_spritesheet(path, fw, sh, num_frames=8)
    except Exception:
        frames = []
    _CACHE[key] = frames
    return frames


def _get_player_animation_controller(player_id: int) -> AnimationController:
    """Lazy-load animation controller for player."""
    if player_id in _PLAYER_ANIMATION_CONTROLLERS:
        return _PLAYER_ANIMATION_CONTROLLERS[player_id]

    # Load sprite frames
    idle_frames = _get_player_idle_frames()
    run_frames = _get_player_run_frames()
    guard_frames = _get_player_guard_frames()

    # Create animations
    idle_anim = Animation(frames=idle_frames, fps=10, loop=True)
    run_anim = Animation(frames=run_frames, fps=12, loop=True)
    guard_anim = Animation(frames=guard_frames, fps=8, loop=True)

    # Create controller
    controller = AnimationController(
        sequences={
            "idle": idle_anim,
            "run": run_anim,
            "guard": guard_anim,
        },
        default="idle"
    )

    _PLAYER_ANIMATION_CONTROLLERS[player_id] = controller
    return controller


def update_player_animation(battle, dt: float) -> None:
    """Update player animation state (idle/run) and controller with instant switching."""
    controller = _get_player_animation_controller(battle.player.id)

    # Highest priority: guarding when blocking (Shift)
    try:
        if bool(getattr(battle, 'player_blocking', False)):
            controller.set("guard")
            controller.update(dt)
            return
    except Exception:
        pass

    # Detect idle vs run using our own last-position tracker to avoid sync issues
    pid = battle.player.id
    cur_x = float(battle.player.pos[0])
    cur_y = float(battle.player.pos[1])
    prev = _LAST_PLAYER_POS.get(pid)

    if prev is not None:
        dist = math.hypot(cur_x - prev[0], cur_y - prev[1])
        velocity = dist / max(dt, 1e-6)
        new_state = "run" if velocity > ANIMATION_IDLE_THRESHOLD else "idle"

        # Update facing direction based on horizontal movement
        dx = cur_x - prev[0]
        if abs(dx) > 0.1:  # Only update direction if significant horizontal movement
            _PLAYER_FACING_RIGHT[pid] = dx > 0  # True = moving right, False = moving left

        controller.set(new_state)
    else:
        controller.set("idle")
        _PLAYER_FACING_RIGHT[pid] = True  # Default facing right

    # Update animation frame
    controller.update(dt)

    # Store current as last for next frame
    _LAST_PLAYER_POS[pid] = (cur_x, cur_y)


def draw_player_sprite(battle, screen: pygame.Surface, player_screen_pos: tuple[int, int]) -> bool:
    """Draw the player sprite with animation; return True if drawn (else caller can fallback).

    Note: The animation state (idle/run) and frame advancement are handled in
    update_player_animation during render_battle. Here we only render the current
    frame, avoiding state changes that could fight with the updater.
    """
    pid = battle.player.id
    controller = _get_player_animation_controller(pid)
    frame = controller.frame()
    if not frame:
        # Fallback to manual selection based on controller.state
        state = getattr(controller, 'state', 'idle')
        frames = _get_player_run_frames() if state == 'run' else _get_player_idle_frames()
        if not frames:
            return False
        ms = 80 if state == 'run' else 120
        idx = (pygame.time.get_ticks() // ms) % max(1, len(frames))
        frame = frames[int(idx)]

    # Scale to player radius
    target_h = max(8, int(battle.player.radius * PLAYER_SPRITE_HEIGHT_PER_RADIUS))
    scale = target_h / max(1, frame.get_height())
    target_w = max(8, int(frame.get_width() * scale))
    frame_s = pygame.transform.smoothscale(frame, (target_w, target_h))

    # Apply horizontal flip based on facing direction
    facing_right = _PLAYER_FACING_RIGHT.get(pid, True)
    if not facing_right:
        frame_s = pygame.transform.flip(frame_s, True, False)  # flip_x=True, flip_y=False

    # Draw sprite with foot offset
    x, y = player_screen_pos
    offset_y = int(target_h * PLAYER_SPRITE_FOOT_OFFSET_PCT)
    blit_pos = (int(x - target_w // 2), int(y - target_h + offset_y))
    screen.blit(frame_s, blit_pos)
    return True
