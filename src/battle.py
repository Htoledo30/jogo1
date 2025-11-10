"""Battle system implementation for MVP B.

Complete top-down arena combat with:
- Player movement (WASD) and attack (Space)
- Enemy AI (seek + attack behavior)
- Circle collision detection
- Attack cooldowns
- Invincibility frames (0.3s)
- Victory/defeat conditions
- XP calculation based on enemy tiers and difficulty
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict

import pygame

from . import entities
from src import vfx
from src import battle_ai
from src import battle_effects
from src import battle_sprites
from src.battle_projectiles import ProjectileManager

# Refactored modules (extracted from this file for better organization)
from src import battle_rendering
from src import battle_systems
from src import battle_ai_enhanced
from src import battle_combat
from src import battle_arena
from src import battle_orders
from src import battle_input
from src.constants_battle import PLAYER_HEAVY_ATTACK_MOVE_MULT


# Battle arena constants (sync with global constants)\nfrom src.constants import ARENA_WIDTH as GLOBAL_ARENA_WIDTH, ARENA_HEIGHT as GLOBAL_ARENA_HEIGHT\nARENA_WIDTH = GLOBAL_ARENA_WIDTH\nARENA_HEIGHT = GLOBAL_ARENA_HEIGHT\nARENA_BORDER = 40


class BattleController:
    """Manages a single battle encounter."""

    def __init__(self, player, encounter):
        """Initialize battle with player and enemy encounter.

        Args:
            player: Player Entity
            encounter: Dict with 'enemies' list, 'troops' list, and 'rng_seed'
        """
        # CRITICAL: Clear all particles from previous frames
        vfx.particles.clear()

        self.player = player
        self.enemies = encounter.get("enemies", []) if isinstance(encounter, dict) else []
        # Optional second enemy side for AI-vs-AI
        side_b = encounter.get("enemies_b", []) if isinstance(encounter, dict) else []
        self.troops = encounter.get("troops", []) if isinstance(encounter, dict) else []
        self.rng = random.Random(encounter.get("rng_seed", 0) if isinstance(encounter, dict) else 0)

        # Assign teams and print debug
        for e in self.enemies:
            setattr(e, 'team', getattr(e, 'team', 'A'))
        for e in side_b:
            setattr(e, 'team', 'B')
        self.enemies.extend(side_b)

        # DEBUG: Print enemy loading
        print(f"[BATTLE DEBUG] Loaded {len(self.enemies)} enemies")
        for i, e in enumerate(self.enemies):
            print(f"  Enemy {i}: {e.name if hasattr(e, 'name') else 'UNNAMED'} at pos {e.pos}")

        # Battle state
        self._done = False
        self._victory = False
        self._battle_time = 0.0

        # Expose arena constants on the instance for helper modules
        self.ARENA_WIDTH = ARENA_WIDTH
        self.ARENA_HEIGHT = ARENA_HEIGHT
        self.ARENA_BORDER = ARENA_BORDER

        # Position entities in arena
        self._setup_arena()

        # Combat state
        self.player_attack_cooldown = 0.0
        self.player_attack_duration = 0.0

        self.player_attack_direction = [0, 0]  # Current attack direction
        self.player_attack_type = "slash"  # slash, thrust, overhead
        self.attack_type_combo = []  # Track combo sequence
        self.enemy_attack_cooldowns = {e.id: 0.0 for e in self.enemies}
        self.enemy_attack_durations = {e.id: 0.0 for e in self.enemies}
        self.troop_attack_cooldowns = {t.id: 0.0 for t in self.troops}
        self.troop_attack_durations = {t.id: 0.0 for t in self.troops}
        self._frame_toggle = False  # used for LOD/throttle logic

        # NEW: Stamina system
        try:
            self.player_stamina_max = float(getattr(self.player.stats, "stamina_max", 100.0))
        except Exception:
            self.player_stamina_max = 100.0
        self.player_stamina = self.player_stamina_max

        # NEW: Blocking state
        self.player_blocking = False
        self.player_block_time = 0.0
        self.enemy_stun_times = {e.id: 0.0 for e in self.enemies}  # Parry stun
        self.enemy_blocking_states = {e.id: False for e in self.enemies} # NEW: Enemy blocking
        self.enemy_block_decision_timers = {e.id: 0.0 for e in self.enemies}  # Decision lock timer
        self.enemy_block_decisions = {e.id: False for e in self.enemies}  # Locked decision

        # NEW: Combo system (Dark Souls + streak UI)
        self.combo_levels = [
            {"hits": 0, "mult": 1.0, "label": "FLOW", "color": (200, 230, 255)},
            {"hits": 3, "mult": 1.18, "label": "FURY", "color": (255, 220, 140)},
            {"hits": 6, "mult": 1.35, "label": "BRUTAL", "color": (255, 170, 100)},
            {"hits": 9, "mult": 1.55, "label": "BERSERK", "color": (255, 120, 120)},
            {"hits": 12, "mult": 1.8, "label": "ASCEND", "color": (210, 150, 255)},
        ]
        self.player_combo_count = 0
        self.player_combo_timer = 0.0
        self.combo_chain_hits = 0
        self.combo_chain_level = 0
        self.combo_chain_timer = 0.0
        self.combo_chain_feedback = 0.0

        # Track which enemies were hit during the current player attack swing
        self.player_hit_enemies: set[int] = set()

        # Enemy AI state (moved to helper module)
        battle_ai.init_enemy_ai_state(self)

        # Projectile manager (for archers/sling)
        self.projectiles = ProjectileManager()

        # Previous positions for simple velocity estimation (for projectile leading)
        self.prev_positions = {}

        # NEW: Formation system (Rome Total War)
        self.formation_mode = 0  # 0=circle, 1=line, 2=wedge

        # Light/Heavy attack input tracking
        self.attack_input_time = 0  # When attack was pressed
        self.prev_attack_state = False
        self.is_charging_attack = False
        self.current_attack_type = "light"

        # NEW: Troop orders (FOLLOW/HOLD/CHARGE/DEFEND/FOCUS)
        self.troop_order = "FOLLOW"
        self.order_flash_timer = 0.0
        self.focus_target_id = None

        # Visual effects and arena metadata
        self.hit_flashes = []  # [(x, y, time_left, color)]
        self.damage_numbers = []  # [(x, y, time_left, damage, color)]
        self.screen_shake = 0.0
        self.hit_pause = 0.0  # Hit pause for impactful hits
        self.hit_pause_intensity = 1.0  # Multiplier for time slow

        # Arena variants / terrain setup
        battle_arena.init_arena_theme(self)
        if not hasattr(self, "high_ground_rects"):
            self.high_ground_rects = []
        if not hasattr(self, "hill_zone"):
            hill_x = ARENA_WIDTH // 2 - 200
            hill_y = ARENA_HEIGHT // 2 - 100
            self.hill_zone = pygame.Rect(hill_x, hill_y, 400, 200)

        # Veterancy tracking
        for troop in self.troops:
            troop.stats.xp_to_next_level = troop.stats.level * 10 # XP to promote

        # Tracking promotions during battle
        self.promoted_troops_this_battle = []

        # Timers for VFX
        self.dust_timer = 0.0

        # TARGET DISTRIBUTION: Assign each troop a different enemy
        self.troop_target_assignments = {}  # {troop_id: enemy_id}
        battle_systems.redistribute_troop_targets(self)

    def _setup_arena(self):
        """Position player, troops, and enemies in battle arena.

        Layout: Player + allies spawn on LEFT side; enemies on RIGHT side.
        This improves readability vs. top/bottom spawns.
        """
        left_x = self.ARENA_BORDER + 140
        right_x = self.ARENA_WIDTH - self.ARENA_BORDER - 140

        # Player starts mid-left
        self.player.pos[0] = left_x
        self.player.pos[1] = self.ARENA_HEIGHT // 2

        # Troops near player (compact line/wedge around player, still on left)
        rows = max(1, int(len(self.troops) ** 0.5))
        cols = max(1, (len(self.troops) + rows - 1) // rows)
        spacing_x = 36
        spacing_y = 28
        origin_y = int(self.player.pos[1] - (rows - 1) * spacing_y / 2)
        for idx, troop in enumerate(self.troops):
            r = idx // cols
            c = idx % cols
            tx = left_x + 40 + c * spacing_x
            ty = origin_y + r * spacing_y
            troop.pos[0] = tx
            troop.pos[1] = ty

        # Enemies along the RIGHT side, vertically distributed
        num_enemies = len(self.enemies)
        if num_enemies > 0:
            top_y = self.ARENA_BORDER + 80
            usable_h = max(100, self.ARENA_HEIGHT - 2 * (self.ARENA_BORDER + 80))
            for i, enemy in enumerate(self.enemies):
                # Even vertical spacing
                y = top_y + int((i + 1) * (usable_h / (num_enemies + 1))) + self.rng.randint(-6, 6)
                x = right_x + self.rng.randint(-10, 10)
                enemy.pos[0] = x
                enemy.pos[1] = y

    # Formation, terrain, and veterancy methods moved to battle_systems module

    def update(self, dt: float, input_state: Dict[str, bool]):
        """Update battle state.

        Args:
            dt: Delta time in seconds
            input_state: Dict with keys: up, down, left, right, attack
        """
        if self._done:
            return

        # HIT PAUSE: Slow down time for impactful hits
        if self.hit_pause > 0:
            dt *= 0.3  # Slow down to 30% speed
            self.hit_pause -= dt / 0.3  # Countdown at normal speed
            self.hit_pause = max(0, self.hit_pause)

        self._battle_time += dt
        self._frame_toggle = not self._frame_toggle
        # Expose last dt for helper modules (projectile leading)
        self._last_dt = dt

        # Update cooldowns
        self.player_attack_cooldown = max(0.0, self.player_attack_cooldown - dt)
        self.player_attack_duration = max(0.0, self.player_attack_duration - dt)
        self.player_combo_timer = max(0.0, self.player_combo_timer - dt)
        self.player_block_time += dt if self.player_blocking else 0.0

        # Reset combo if timer expires
        if self.player_combo_timer <= 0.0:
            self.player_combo_count = 0

        for eid in self.enemy_attack_cooldowns:
            self.enemy_attack_cooldowns[eid] = max(0.0, self.enemy_attack_cooldowns[eid] - dt)
            self.enemy_attack_durations[eid] = max(0.0, self.enemy_attack_durations[eid] - dt)
            self.enemy_stun_times[eid] = max(0.0, self.enemy_stun_times.get(eid, 0.0) - dt)
            # We don't reset the blocking state here, it's controlled by the AI

        for tid in list(self.troop_attack_cooldowns.keys()):
            self.troop_attack_cooldowns[tid] = max(0.0, self.troop_attack_cooldowns.get(tid, 0.0) - dt)
            self.troop_attack_durations[tid] = max(0.0, self.troop_attack_durations.get(tid, 0.0) - dt)

        # Update entities
        self.player.update(dt)

        # NOTE: Player animation update moved to battle_rendering.py to avoid duplication
        # battle_sprites.update_player_animation(self, dt)  # REMOVED - called in render instead

        for enemy in self.enemies:
            enemy.update(dt)
        for troop in self.troops:
            troop.update(dt)

        # Stamina regeneration (slower when blocking)
        if self.player_blocking:
            self.player_stamina = max(0.0, self.player_stamina - 5.0 * dt)  # Drain while blocking
        else:
            self.player_stamina = min(self.player_stamina_max, self.player_stamina + 20.0 * dt)

        # Update visual effects lists via helper
        battle_effects.update_effects(self, dt)

        # Update projectiles (ranged attacks)
        if hasattr(self, 'projectiles') and self.projectiles:
            self.projectiles.update(self, dt)

        # Formation change (1/2/3 keys for circle/line/wedge)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]:
            self.formation_mode = 0  # Circle
        elif keys[pygame.K_2]:
            self.formation_mode = 1  # Line
        elif keys[pygame.K_3]:
            self.formation_mode = 2  # Wedge

        # Troop orders (F1..F5) handled in dedicated module
        battle_orders.handle_orders(self)

        # Player blocking (Shift key)
        self.player_blocking = input_state.get("block", False) and self.player_stamina > 0

        # Player movement
        if self.player.alive():
            vx = (-1 if input_state.get("left") else 0) + (1 if input_state.get("right") else 0)
            vy = (-1 if input_state.get("up") else 0) + (1 if input_state.get("down") else 0)

            # Dust particles on move
            self.dust_timer += dt
            if (vx != 0 or vy != 0) and self.dust_timer > 0.1:
                vfx.create_dust_cloud(self.player.pos, 2)
                self.dust_timer = 0.0

            # Normalize diagonal movement
            if vx != 0 and vy != 0:
                length = math.sqrt(vx * vx + vy * vy)
                vx /= length
                vy /= length

            # Slower movement when blocking / charging heavies
            speed_mult = 0.5 if self.player_blocking else 1.0
            heavy_penalty = False
            if getattr(self, "current_attack_type", "light") == "heavy" and getattr(self, "is_charging_attack", False):
                heavy_penalty = True
            if self.player_attack_duration > 0.0 and self.player_attack_type == "overhead":
                heavy_penalty = True
            if heavy_penalty:
                speed_mult *= PLAYER_HEAVY_ATTACK_MOVE_MULT
            speed = self.player.stats.spd * speed_mult
            self.player.pos[0] += vx * speed * dt
            self.player.pos[1] += vy * speed * dt

            # Clamp to arena bounds
            self.player.pos[0] = max(ARENA_BORDER + self.player.radius,
                                    min(ARENA_WIDTH - ARENA_BORDER - self.player.radius, self.player.pos[0]))
            self.player.pos[1] = max(ARENA_BORDER + self.player.radius,
                                    min(ARENA_HEIGHT - ARENA_BORDER - self.player.radius, self.player.pos[1]))

        # Player attack input (delegated to module)
        battle_input.handle_player_attack_input(self, input_state, dt)

        # Enemy AI update (spacing/target/stamina) moved to helper module
        battle_ai.update_enemies(self, dt)

        # Troop AI moved to module (movement/engagement)
        from src import battle_troop_ai
        battle_troop_ai.update_troops(self, dt)

        # Troop attacks hitting enemies (skip archers here; handled by projectiles)
        for troop in self.troops:
            if not troop.alive():
                continue
            troop_type = getattr(troop, 'troop_type', 'warrior')
            if troop_type == 'archer':
                continue
            duration = self.troop_attack_durations.get(troop.id, 0.0)
            if duration > 0.0:
                # Melee range attack processing
                attack_range = troop.radius + 20  # Melee range

                for enemy in self.enemies:
                    if enemy.alive():
                        dist = entities.distance(troop, enemy)
                        if dist <= attack_range:
                            damage = troop.stats.atk

                            # Terrain advantage: +20% damage if troop on high ground
                            if battle_systems.is_on_high_ground(self, troop):
                                damage *= 1.2

                            enemy.apply_damage(damage)
                            battle_effects.add_damage_number(self, enemy.pos[0], enemy.pos[1], int(damage), (150, 200, 255))
                            if not enemy.alive():
                                battle_effects.add_hit_flash(self, enemy.pos[0], enemy.pos[1], (255, 200, 0))
                                # Veterancy: Grant XP to troop for kill
                                xp_gained = enemy.stats.level * 2
                                troop.stats.xp += xp_gained
                                print(f"Troop {troop.id} gained {xp_gained} XP!")
                            else:
                                battle_effects.add_hit_flash(self, enemy.pos[0], enemy.pos[1], (255, 150, 150))
                            # Reset duration
                            self.troop_attack_durations[troop.id] = 0.0
                            vfx.create_blood_splatter(enemy.pos, 5)
                            break  # One enemy per attack

        # Store positions for next-frame velocity estimation
        try:
            self.prev_positions[self.player.id] = (float(self.player.pos[0]), float(self.player.pos[1]))
            for e in self.enemies:
                self.prev_positions[e.id] = (float(e.pos[0]), float(e.pos[1]))
            for t in self.troops:
                self.prev_positions[t.id] = (float(t.pos[0]), float(t.pos[1]))
        except Exception:
            pass

        # Decay order flash timer
        if self.order_flash_timer > 0.0:
            self.order_flash_timer = max(0.0, self.order_flash_timer - dt)

        # Check player attacks hitting enemies
        if self.player_attack_duration > 0.0:
            # Reach depends on equipped weapon range
            weapon = self.player.equipment.get_weapon()
            w_range = float(getattr(weapon, "range", 75.0))
            # Increase effective reach; thrusts get longer reach
            base = w_range * (1.3 if self.player_attack_type == "thrust" else 1.1)
            attack_range = self.player.radius + max(50.0, min(base, 170.0))

            # Combo damage multiplier: 1x -> 1.3x -> 1.6x
            combo_mult = 1.0 + (self.player_combo_count - 1) * 0.3

            for enemy in self.enemies:
                if enemy.alive():
                    dist = entities.distance(self.player, enemy)
                    if dist <= attack_range:
                        # Check if enemy is blocking
                        is_enemy_blocking = self.enemy_blocking_states.get(enemy.id, False)

                        if is_enemy_blocking:
                            # BLOCKED ATTACK: Sparks, reduced damage, no hit pause
                            damage = 0
                            attack_angle = math.atan2(self.player_attack_direction[1], self.player_attack_direction[0])
                            vfx.create_block_spark(enemy.pos, 15, attack_angle + math.pi)  # Sparks fly back
                            self._add_damage_number(enemy.pos[0], enemy.pos[1], 0, (200, 200, 255))  # Shows "PARRY!"
                            self._add_hit_flash(enemy.pos[0], enemy.pos[1], (150, 200, 255))
                            self.screen_shake = 0.2
                            # Only show parry once per swing per enemy
                            self.player_hit_enemies.add(enemy.id)
                            continue  # Skip damage application

                        # Dano baseado na arma equipada
                        weapon = self.player.equipment.get_weapon()
                        damage = (self.player.stats.atk * weapon.damage) * combo_mult

                        # Spear thrust: light shield penetration
                        try:
                            if self.player_attack_type == "thrust" and getattr(weapon, 'weapon_type', '') == 'spear':
                                # If the target wields a shield, grant a small penetration bonus
                                # (enemies may not have equipment yet; guard accordingly)
                                if hasattr(enemy, 'equipment') and enemy.equipment:
                                    enemy_weapon = enemy.equipment.get_weapon()
                                    if getattr(enemy_weapon, 'weapon_type', '') == 'shield':
                                        damage *= 1.15  # ~15% bonus vs shield
                        except Exception:
                            pass
                        hp_before = enemy.stats.hp

                        # Terrain advantage: +20% damage if player on high ground
                        if battle_systems.is_on_high_ground(self, self.player):
                            damage *= 1.2

                        enemy.apply_damage(damage)
                        if enemy.stats.hp >= hp_before:
                            # No actual damage applied (i-frames or other), avoid spawning duplicate numbers
                            continue
                        # Mark as hit so this swing won't re-hit the same enemy
                        self.player_hit_enemies.add(enemy.id)

                        # VARIED PARTICLES based on attack type
                        attack_angle = math.atan2(self.player_attack_direction[1], self.player_attack_direction[0])
                        if self.player_attack_type == "slash":
                            vfx.create_blood_splatter(enemy.pos, 12, attack_angle)
                            vfx.create_impact_dust(enemy.pos, 5, attack_angle)
                        elif self.player_attack_type == "thrust":
                            vfx.create_blood_splatter(enemy.pos, 15, attack_angle)  # More blood on thrust
                            self.screen_shake = 0.3
                        else:  # overhead
                            vfx.create_blood_splatter(enemy.pos, 20, attack_angle)  # Heavy blood on overhead
                            vfx.create_impact_dust(enemy.pos, 10, attack_angle)
                            self.screen_shake = 0.6  # Bigger shake for overhead

                        # Add damage number with attack type color
                        color = (255, 255, 100) if self.player_attack_type != "overhead" else (255, 180, 50)
                        battle_effects.add_damage_number(self, enemy.pos[0], enemy.pos[1], int(damage), color)

                        if not enemy.alive():
                            # Death effects
                            battle_effects.add_hit_flash(self, enemy.pos[0], enemy.pos[1], (255, 200, 0))
                            battle_effects.shake(self, 0.8)
                            battle_effects.add_hit_pause(self, 0.15)
                            vfx.create_blood_splatter(enemy.pos, 30, attack_angle)  # Massive blood on kill
                        else:
                            battle_effects.add_hit_flash(self, enemy.pos[0], enemy.pos[1], (255, 100, 100))
                            battle_effects.add_hit_pause(self, 0.05 if self.player_attack_type != "overhead" else 0.1)

        # Enemy AI and attacks (IMPROVED: target nearest threat)
        # Special attacks removed by user request

        for enemy in self.enemies:
            if not enemy.alive():
                continue

            # Check if stunned (from parry)
            is_stunned = self.enemy_stun_times.get(enemy.id, 0.0) > 0.0

            # Reset blocking state at the start of each frame
            self.enemy_blocking_states[enemy.id] = False

            # TARGET PRIORITIZATION SYSTEM (replaces simple nearest-target)
            targets = [self.player] + [t for t in self.troops if t.alive()]
            nearest_target = None
            best_score = -1
            min_dist = float('inf')

            for target in targets:
                if not target.alive():
                    continue

                dist = entities.distance(enemy, target)

                # Calculate priority score (0-100)
                score = 0

                # HP Factor (40%): Prioritize low HP targets for kills
                hp_percent = target.stats.hp / target.stats.hp_max
                score += (1.0 - hp_percent) * 40  # Lower HP = higher score

                # Threat Factor (30%): Prioritize high ATK targets
                threat = target.stats.atk / 20.0  # Normalize (typical ATK 10-40)
                score += min(threat, 1.0) * 30

                # Distance Factor (20%): Slightly prefer closer targets
                max_dist = 400  # Normalize distance
                distance_score = max(0, 1.0 - (dist / max_dist))
                score += distance_score * 20

                # Type Factor (10%): Prioritize player over troops
                if target == self.player:
                    score += 10

                # Select best target
                if score > best_score:
                    best_score = score
                    nearest_target = target
                    min_dist = dist

            # --- IMPROVED BEHAVIORAL AI ---
            # AI State Machine: Chasing, Attacking, Blocking, Fleeing
            enemy_state = "CHASING" # Default

            # BLOCKING INTELLIGENCE: Lock decision for 1-2 seconds
            block_timer = self.enemy_block_decision_timers.get(enemy.id, 0.0)
            block_timer -= dt

            if not is_stunned:
                # If timer expired, make a new blocking decision
                if block_timer <= 0.0:
                    # Check if player is attacking toward this enemy
                    player_attacking = self.player_attack_duration > 0.0
                    close_to_player = entities.distance(enemy, self.player) < 120

                    if player_attacking and close_to_player:
                        # Check attack direction (is player attacking toward this enemy?)
                        attack_toward_enemy = False
                        if self.player_attack_direction[0] != 0 or self.player_attack_direction[1] != 0:
                            # Calculate direction from player to enemy
                            dx_to_enemy = enemy.pos[0] - self.player.pos[0]
                            dy_to_enemy = enemy.pos[1] - self.player.pos[1]
                            dist = math.hypot(dx_to_enemy, dy_to_enemy)
                            if dist > 0:
                                dx_to_enemy /= dist
                                dy_to_enemy /= dist
                                # Dot product: check if attack direction aligns with enemy direction
                                dot = (self.player_attack_direction[0] * dx_to_enemy +
                                       self.player_attack_direction[1] * dy_to_enemy)
                                attack_toward_enemy = dot > 0.5  # 60-degree cone

                        # Make blocking decision
                        if attack_toward_enemy:
                            # Higher chance to block when HP is low
                            block_chance = 0.5 if enemy.stats.hp > enemy.stats.hp_max * 0.5 else 0.75
                            self.enemy_block_decisions[enemy.id] = self.rng.random() < block_chance
                        else:
                            self.enemy_block_decisions[enemy.id] = False

                        # Lock decision for 1.0-2.0 seconds
                        self.enemy_block_decision_timers[enemy.id] = self.rng.uniform(1.0, 2.0)
                    else:
                        self.enemy_block_decisions[enemy.id] = False
                        self.enemy_block_decision_timers[enemy.id] = self.rng.uniform(0.3, 0.6)
                else:
                    # Update timer
                    self.enemy_block_decision_timers[enemy.id] = block_timer

                # Use locked decision
                if self.enemy_block_decisions.get(enemy.id, False):
                    enemy_state = "BLOCKING"
            
            # Use troop_type if available, fallback to enemy_type detection
            troop_type = getattr(enemy, 'troop_type', None)
            if troop_type:
                is_archer = troop_type == 'archer'
            else:
                enemy_type_lower = getattr(enemy, 'enemy_type', '').lower()
                is_archer = 'archer' in enemy_type_lower or 'bow' in enemy_type_lower
            kiting_distance = 180
            if is_archer and nearest_target and entities.distance(enemy, nearest_target) < kiting_distance:
                enemy_state = "FLEEING" # Archers try to keep their distance

            # IMPROVED AI: Self-preservation - retreat when HP is critical
            hp_ratio = enemy.stats.hp / max(1, enemy.stats.hp_max)
            if hp_ratio < 0.3 and not is_archer:
                enemy_state = "RETREATING"  # Low HP enemies retreat!

            # --- State Execution ---
            self.enemy_blocking_states[enemy.id] = (enemy_state == "BLOCKING")

            # Movimento e Ataque (apenas se não estiver atordoado)
            if not is_stunned and nearest_target:
                move_speed = enemy.stats.spd * 0.9

                if enemy_state == "RETREATING":
                    # RETREAT: Move away from nearest target
                    dx = enemy.pos[0] - nearest_target.pos[0]
                    dy = enemy.pos[1] - nearest_target.pos[1]
                    move_speed *= 1.2  # Faster when fleeing for life!
                elif enemy_state == "FLEEING":
                    # Flee to maintain distance
                    dx = enemy.pos[0] - nearest_target.pos[0]
                    dy = enemy.pos[1] - nearest_target.pos[1]
                    move_speed *= 0.8 # Moves a bit slower when retreating
                elif enemy_state == "CHASING":
                    # IMPROVED: Add circling/flanking behavior (40% chance)
                    if self.rng.random() < 0.4:
                        # Circle around target instead of direct rush
                        dx_base = nearest_target.pos[0] - enemy.pos[0]
                        dy_base = nearest_target.pos[1] - enemy.pos[1]
                        # Rotate 90 degrees (perpendicular movement)
                        dx = -dy_base
                        dy = dx_base
                        move_speed *= 0.85  # Slightly slower when circling
                    else:
                        # Direct chase
                        dx = nearest_target.pos[0] - enemy.pos[0]
                        dy = nearest_target.pos[1] - enemy.pos[1]

                    # SPACING: Avoid stacking on top of each other
                    for other_enemy in self.enemies:
                        if other_enemy.id != enemy.id and other_enemy.alive():
                            dist_to_other = entities.distance(enemy, other_enemy)
                            if dist_to_other < 50:  # Too close to another enemy
                                # Push away from other enemy
                                push_dx = enemy.pos[0] - other_enemy.pos[0]
                                push_dy = enemy.pos[1] - other_enemy.pos[1]
                                push_dist = math.hypot(push_dx, push_dy)
                                if push_dist > 0:
                                    dx += (push_dx / push_dist) * 100
                                    dy += (push_dy / push_dist) * 100
                elif enemy_state == "BLOCKING":
                    # Stand still or move slowly backwards
                    dx = enemy.pos[0] - nearest_target.pos[0]
                    dy = enemy.pos[1] - nearest_target.pos[1]
                    move_speed *= 0.2 # Very slow when blocking
                else: # Attacking or other states
                    dx, dy = 0, 0

                # Execute movement
                if dx != 0 or dy != 0:
                    dist = math.hypot(dx, dy)
                    # Normalize direction

                    # Dust particles for enemy movement
                    self.dust_timer += dt
                    if self.dust_timer > 0.05:
                        vfx.create_dust_cloud(enemy.pos, 1)
                        self.dust_timer = 0.0

                    dx /= dist
                    dy /= dist
                    enemy.pos[0] += dx * move_speed * dt
                    enemy.pos[1] += dy * move_speed * dt

                    # Clamp to arena
                    enemy.pos[0] = max(ARENA_BORDER + enemy.radius,
                                      min(ARENA_WIDTH - ARENA_BORDER - enemy.radius, enemy.pos[0]))
                    enemy.pos[1] = max(ARENA_BORDER + enemy.radius,
                                      min(ARENA_HEIGHT - ARENA_BORDER - enemy.radius, enemy.pos[1]))

            # Attack Logic (separate from movement)
            if not is_stunned and nearest_target and enemy_state != "BLOCKING":
                attack_range = (kiting_distance if is_archer else enemy.radius + nearest_target.radius + 15)
                if min_dist <= attack_range:
                    if self.enemy_attack_cooldowns.get(enemy.id, 0.0) <= 0.0:
                        self.enemy_attack_cooldowns[enemy.id] = self.rng.uniform(1.0, 1.4) # More variable attack cooldown
                        self.enemy_attack_durations[enemy.id] = 0.3
            else:
                # Stunned or no target: use player distance as fallback
                if nearest_target:
                    dx = nearest_target.pos[0] - enemy.pos[0]
                    dy = nearest_target.pos[1] - enemy.pos[1]
                    dist = math.hypot(dx, dy)
                    attack_range = enemy.radius + nearest_target.radius + 10
                else:
                    dist = float('inf')
                    attack_range = 0

            # Apply enemy damage to nearest target
            duration = self.enemy_attack_durations.get(enemy.id, 0.0)
            if duration > 0.0 and min_dist <= attack_range and nearest_target:
                damage = enemy.stats.atk

                # Terrain advantage: -10% damage if defender on high ground
                if battle_systems.is_on_high_ground(self, nearest_target):
                    damage *= 0.9

                # Check if target is player (for blocking mechanics)
                is_player_target = (nearest_target.id == self.player.id)

                # Blocking mechanics (only for player)
                if is_player_target and self.player_blocking: # Bloqueio do Jogador
                    # Perfect Parry: Block pressed within 0.2s of attack
                    if self.player_block_time < 0.2:
                        # Perfect parry! No damage, stun enemy
                        damage = 0
                        self.enemy_stun_times[enemy.id] = 1.5  # Stun for 1.5s
                        self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (100, 200, 255))
                        self._add_damage_number(nearest_target.pos[0], nearest_target.pos[1] - 30, 0, (100, 255, 255))
                        self.screen_shake = 0.1
                    else:
                        # Regular block: 70% damage reduction
                        damage *= 0.3
                        self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (150, 150, 200))
                        vfx.create_block_spark(nearest_target.pos, 15)
                        self._add_damage_number(nearest_target.pos[0], nearest_target.pos[1] - 30, int(damage), (200, 200, 255))
                        self.screen_shake = 0.15
                elif not is_player_target and self.enemy_blocking_states.get(nearest_target.id, False): # Bloqueio do Inimigo (se o alvo for outro inimigo, hipoteticamente)
                    # This logic is for troops, but the structure is here.
                    damage *= 0.3 # Redução de dano para tropas que bloqueiam
                    vfx.create_block_spark(nearest_target.pos, 10)
                    self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (150, 150, 150))
                else:
                    # No block: full damage
                    self._add_damage_number(nearest_target.pos[0], nearest_target.pos[1] - 30, int(damage), (255, 100, 100))
                    if is_player_target:
                        if not self.player.alive():
                            self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (200, 200, 255))
                            self.screen_shake = 0.8
                        else:
                            self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (255, 150, 150))
                            self.screen_shake = 0.3
                    else:
                        self._add_hit_flash(nearest_target.pos[0], nearest_target.pos[1], (255, 150, 150))

                vfx.create_blood_splatter(nearest_target.pos, 8)
                nearest_target.apply_damage(damage)
                # Reset duration and block timer to prevent multi-hit
                self.enemy_attack_durations[enemy.id] = 0.0
                if is_player_target:
                    self.player_block_time = 0.0

        # Check victory/defeat conditions
        all_enemies_dead = all(not e.alive() for e in self.enemies)
        if all_enemies_dead:
            self._victory = True
            # Veterancy: Check for promotions
            for troop in self.troops:
                if troop.stats.xp >= troop.stats.xp_to_next_level:
                    troop.stats.level += 1
                    troop.stats.xp = 0 # Reset XP for next level
                    troop.stats.xp_to_next_level = troop.stats.level * 10
                    # Heal on promotion
                    troop.stats.hp = troop.stats.hp_max
                    # Track promoted troop
                    self.promoted_troops_this_battle.append(troop)
                    print(f"Troop {troop.id} promoted to Tier {troop.stats.level}!")
            self._done = True
        elif not self.player.alive():
            self._victory = False
            self._done = True

    def _add_hit_flash(self, x: float, y: float, color: tuple):
        """Add a hit flash effect."""
        self.hit_flashes.append((x, y, 0.3, color))

    def _add_damage_number(self, x: float, y: float, damage: int, color: tuple):
        """Add a floating damage number."""
        self.damage_numbers.append((x, y, 1.0, damage, color))

    def render(self, screen: pygame.Surface) -> None:
        """Render battle scene using refactored rendering module.

        Args:
            screen: Pygame surface to draw on
        """
        # Delegate to refactored rendering module
        battle_rendering.render_battle(self, screen)

    def is_done(self) -> bool:
        """Return True if the battle is over."""
        return self._done

    def outcome(self) -> dict:
        """Return the results of the battle.

        Returns:
            dict with keys:
                - victory (bool): True if player won
                - player_state (dict): {"hp": player's current HP}
                - xp (int): Experience points gained
                - gold (int): Gold gained
                - promoted_troops (list): Troops that were promoted
                - defeated_enemies (list): All defeated enemies
                - surviving_troops (list): Troops that survived
        """
        defeated_enemies = [e for e in self.enemies if not e.alive()]
        xp_gained = sum(enemy.stats.level * 5 for enemy in defeated_enemies)

        # --- NEW: Dynamic Gold Loot ---
        # Gold is now based on defeated enemies and has a random factor
        gold_gained = sum(self.rng.randint(enemy.stats.level * 5, enemy.stats.level * 15) for enemy in defeated_enemies)

        # Surviving troops (still alive)
        surviving_troops = [t for t in self.troops if t.alive()]

        return {
            "victory": self._victory,
            "player_state": {"hp": self.player.stats.hp},
            "xp": xp_gained,
            "gold": gold_gained,
            "promoted_troops": self.promoted_troops_this_battle,
            "defeated_enemies": defeated_enemies,
            "surviving_troops": surviving_troops
        }


def start_battle(player: entities.Entity, encounter: Dict[str, Any]) -> BattleController:
    """Factory function to create and return a BattleController instance."""
    return BattleController(player, encounter)

