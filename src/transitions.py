"""
Transition Manager for smooth visual transitions between game states.

Handles fade-in, fade-out, and crossfade effects for state changes.
"""

import pygame
from typing import Optional, Callable
from enum import Enum


class TransitionType(Enum):
    """Types of transitions available."""
    FADE_OUT = "fade_out"  # Fade to black
    FADE_IN = "fade_in"    # Fade from black
    CROSSFADE = "crossfade"  # Fade out then fade in


class TransitionState(Enum):
    """Current state of transition."""
    IDLE = "idle"
    FADING_OUT = "fading_out"
    FADING_IN = "fading_in"
    COMPLETE = "complete"


class TransitionManager:
    """Manages smooth fade transitions between game states."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Create black overlay surface for fades
        self.overlay = pygame.Surface((screen_width, screen_height))
        self.overlay.fill((0, 0, 0))

        # Transition state
        self.state = TransitionState.IDLE
        self.alpha = 0  # 0 = transparent, 255 = opaque black
        self.fade_speed = 400  # Alpha units per second (faster = 400, slower = 200)

        # Callback to execute at transition midpoint
        self.midpoint_callback: Optional[Callable] = None
        self.callback_executed = False

    def start_fade_out(self, callback: Optional[Callable] = None, speed: int = 400):
        """
        Start fading to black.

        Args:
            callback: Function to call when fade completes
            speed: Fade speed (alpha/second). 400=fast, 200=slow
        """
        self.state = TransitionState.FADING_OUT
        self.alpha = 0
        self.fade_speed = speed
        self.midpoint_callback = callback
        self.callback_executed = False

    def start_fade_in(self, callback: Optional[Callable] = None, speed: int = 400):
        """
        Start fading from black to transparent.

        Args:
            callback: Function to call when fade completes
            speed: Fade speed (alpha/second)
        """
        self.state = TransitionState.FADING_IN
        self.alpha = 255
        self.fade_speed = speed
        self.midpoint_callback = callback
        self.callback_executed = False

    def start_crossfade(self, callback: Optional[Callable] = None, speed: int = 400):
        """
        Fade out, execute callback at black screen, then fade in.

        This is the main transition for state changes (e.g., OVERWORLD → BATTLE).

        Args:
            callback: Function to call at the midpoint (when screen is black)
            speed: Fade speed (alpha/second)
        """
        self.state = TransitionState.FADING_OUT
        self.alpha = 0
        self.fade_speed = speed
        self.midpoint_callback = callback
        self.callback_executed = False

    def update(self, dt: float):
        """
        Update transition state.

        Args:
            dt: Delta time in seconds
        """
        if self.state == TransitionState.IDLE:
            return

        if self.state == TransitionState.FADING_OUT:
            # Increase alpha (fade to black)
            self.alpha += self.fade_speed * dt

            if self.alpha >= 255:
                self.alpha = 255

                # Execute callback at midpoint (screen fully black)
                if self.midpoint_callback and not self.callback_executed:
                    print(f"[TRANSITION DEBUG] Executing callback at midpoint (alpha={self.alpha})")
                    self.midpoint_callback()
                    self.callback_executed = True

                # For crossfade, continue to fade in
                # For simple fade out, mark complete
                if self.midpoint_callback:
                    print(f"[TRANSITION DEBUG] Starting fade-in")
                    self.state = TransitionState.FADING_IN
                else:
                    self.state = TransitionState.COMPLETE

        elif self.state == TransitionState.FADING_IN:
            # Decrease alpha (fade from black)
            self.alpha -= self.fade_speed * dt

            if self.alpha <= 0:
                self.alpha = 0
                print(f"[TRANSITION DEBUG] Fade-in complete, marking COMPLETE")
                self.state = TransitionState.COMPLETE

                # Execute callback if not already done
                if self.midpoint_callback and not self.callback_executed:
                    self.midpoint_callback()
                    self.callback_executed = True

    def render(self, screen: pygame.Surface):
        """
        Render the fade overlay.

        Call this LAST in your render pipeline to draw over everything.
        """
        # Don't render if idle or nearly transparent (prevents "ghost" overlay)
        if self.state == TransitionState.IDLE or self.alpha < 5:
            return

        # DEBUG: Print overlay render info
        if self.alpha > 200:
            print(f"[TRANSITION RENDER] Drawing overlay - state={self.state.value}, alpha={int(self.alpha)}")

        # Set overlay alpha and draw
        self.overlay.set_alpha(int(self.alpha))
        screen.blit(self.overlay, (0, 0))

    def is_active(self) -> bool:
        """Check if a transition is currently running."""
        return self.state != TransitionState.IDLE and self.state != TransitionState.COMPLETE

    def is_complete(self) -> bool:
        """Check if transition just completed this frame."""
        return self.state == TransitionState.COMPLETE

    def reset(self):
        """Reset transition to idle state."""
        self.state = TransitionState.IDLE
        self.alpha = 0
        self.midpoint_callback = None
        self.callback_executed = False


# ============================================================================
# PRESET TRANSITION FUNCTIONS
# ============================================================================

def create_battle_transition(manager: TransitionManager, on_enter_battle: Callable):
    """
    Create smooth transition into battle.

    Args:
        manager: TransitionManager instance
        on_enter_battle: Function that changes state to BATTLE
    """
    manager.start_crossfade(callback=on_enter_battle, speed=500)  # Fast transition


def create_victory_transition(manager: TransitionManager, on_victory: Callable):
    """
    Create slower, dramatic transition for battle victory.

    Args:
        manager: TransitionManager instance
        on_victory: Function to execute after fade
    """
    manager.start_crossfade(callback=on_victory, speed=300)  # Slower for drama


def create_menu_open_transition(manager: TransitionManager, on_open: Callable):
    """
    Quick fade for opening menus.

    Args:
        manager: TransitionManager instance
        on_open: Function to open menu
    """
    manager.start_fade_in(callback=on_open, speed=600)  # Very fast


def create_menu_close_transition(manager: TransitionManager, on_close: Callable):
    """
    Quick fade for closing menus.

    Args:
        manager: TransitionManager instance
        on_close: Function to close menu
    """
    manager.start_fade_out(callback=on_close, speed=600)  # Very fast
