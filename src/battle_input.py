"""Player attack input handling (light/heavy)."""

from __future__ import annotations
import math
from typing import TYPE_CHECKING
import pygame

from . import vfx
from .constants_battle import (
    PLAYER_LIGHT_ATTACK_STAMINA,
    PLAYER_HEAVY_ATTACK_STAMINA,
    PLAYER_HEAVY_ATTACK_CHARGE_TIME,
    PLAYER_HEAVY_ATTACK_COOLDOWN_MULT,
    PLAYER_LIGHT_ATTACK_DURATION,
    PLAYER_HEAVY_ATTACK_DURATION,
)

if TYPE_CHECKING:
    from .battle import BattleController


def handle_player_attack_input(ctrl: "BattleController", input_state: dict, dt: float) -> None:
    if not ctrl.player.alive():
        ctrl.is_charging_attack = False
        ctrl.prev_attack_state = False
        return

    attack_pressed = input_state.get("attack", False)
    current_time = pygame.time.get_ticks()

    if attack_pressed and not ctrl.prev_attack_state:
        ctrl.attack_input_time = current_time
        ctrl.is_charging_attack = True

    if attack_pressed and ctrl.is_charging_attack:
        hold_duration = (current_time - ctrl.attack_input_time) / 1000.0
        if hold_duration >= PLAYER_HEAVY_ATTACK_CHARGE_TIME:
            ctrl.current_attack_type = "heavy"
    else:
        if ctrl.is_charging_attack and ctrl.prev_attack_state:
            hold_duration = (current_time - ctrl.attack_input_time) / 1000.0
            ctrl.current_attack_type = (
                "heavy" if hold_duration >= PLAYER_HEAVY_ATTACK_CHARGE_TIME else "light"
            )

            if ctrl.player_attack_cooldown <= 0.0:
                stamina_cost = (
                    PLAYER_HEAVY_ATTACK_STAMINA
                    if ctrl.current_attack_type == "heavy"
                    else PLAYER_LIGHT_ATTACK_STAMINA
                )
                if ctrl.player_stamina >= stamina_cost:
                    mouse_pos = input_state.get("mouse_pos", (ctrl.player.pos[0], ctrl.player.pos[1] + 50))
                    dx_mouse = mouse_pos[0] - ctrl.player.pos[0]
                    dy_mouse = mouse_pos[1] - ctrl.player.pos[1]
                    dist_mouse = math.hypot(dx_mouse, dy_mouse)
                    if dist_mouse > 0:
                        attack_vx = dx_mouse / dist_mouse
                        attack_vy = dy_mouse / dist_mouse
                    else:
                        attack_vx = 0
                        attack_vy = 1
                    ctrl.player_attack_direction = [attack_vx, attack_vy]
                    weapon = ctrl.player.equipment.get_weapon()
                    base_cd = max(0.3, float(getattr(weapon, "cooldown", 0.5)))

                    if ctrl.current_attack_type == "heavy":
                        ctrl.player_attack_type = "overhead"
                        ctrl.player_attack_cooldown = base_cd * PLAYER_HEAVY_ATTACK_COOLDOWN_MULT
                        ctrl.player_attack_duration = PLAYER_HEAVY_ATTACK_DURATION
                        ctrl.player_stamina -= stamina_cost
                        attack_angle = math.atan2(attack_vy, attack_vx)
                        vfx.create_slash_effect(ctrl.player.pos, attack_angle, "vertical")
                        ctrl.screen_shake = 0.6
                    else:
                        ctrl.player_attack_type = "slash"
                        ctrl.player_attack_cooldown = base_cd
                        ctrl.player_attack_duration = PLAYER_LIGHT_ATTACK_DURATION
                        ctrl.player_stamina -= stamina_cost
                        attack_angle = math.atan2(attack_vy, attack_vx)
                        vfx.create_slash_effect(ctrl.player.pos, attack_angle, "horizontal")

                    try:
                        speed_bonus = float(getattr(ctrl.player.stats, 'attack_speed_bonus', 0.0))
                        ctrl.player_attack_cooldown = max(0.2, ctrl.player_attack_cooldown * (1.0 + speed_bonus))
                    except Exception:
                        pass

                    ctrl.player_hit_enemies.clear()
                    ctrl.player_combo_count = min(3, ctrl.player_combo_count + 1)
                    ctrl.player_combo_timer = 1.5

        ctrl.is_charging_attack = False
        ctrl.attack_input_time = 0

    ctrl.prev_attack_state = attack_pressed
