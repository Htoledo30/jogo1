"""Entry point for MVP B (Overworld-first).

Implements game loop, OVERWORLD/BATTLE states, input, and HUD.
Battle scene remains a stub to be implemented by Claude.
Target Python: 3.12
"""

import sys
import random
import time
import copy

try:
    import pygame
except Exception as exc:  # noqa: BLE001
    print("Pygame is required to run this project.")
    print("Install with: py -3.12 -m pip install -r requirements.txt")
    print(f"Import error: {exc}")
    sys.exit(1)

from src import world as world_mod
from src import entities
from src import rpg
from src import battle as battle_mod
from src import equipment as equip_mod
from src import vfx
from src import save_system
from src.constants import *
from src import items
from src import item_bridge
from src.inventory_ui_v2 import InventoryUI
from src.ui_shop import ShopUI
from src import transitions as trans_mod
from src.ui_components import Panel, ProgressBar, UIColors
from src.ui import hud as ui_hud
from src import ui_shop
from src import factions
from src.ui import hud as hud_module
from src.ui import menus
from src.resource_manager import get_font, Fonts
from src.logger import get_logger
import math

# Initialize logger for main module
logger = get_logger("main")


# Pre-create fonts once to avoid recreation every frame (PERFORMANCE OPTIMIZATION)
FONT_MAIN = None
FONT_SMALL = None
FONT_ICONS = None
FONT_TINY = None
FONT_LARGE = None  # New: for headers/important stats
FONT_LABEL = None  # New: for small labels
# Shop context (faction-themed shop inventory)
CURRENT_SHOP_FACTION_ID = "greeks"
SHOP_UI = None
SHOP_INVENTORY = None
SHOP_GOLD = 800
PERMADEATH_CHANCE = 0.35

def init_fonts():
    """Initialize fonts using Resource Manager (cached automatically)."""
    global FONT_MAIN, FONT_SMALL, FONT_ICONS, FONT_TINY, FONT_LARGE, FONT_LABEL
    # Using resource manager - fonts are automatically cached
    FONT_MAIN = get_font(18, bold=True)
    FONT_SMALL = get_font(16)
    FONT_ICONS = get_font(20, bold=True)
    FONT_TINY = get_font(14)
    FONT_LARGE = get_font(24, bold=True)
    FONT_LABEL = get_font(14)
    logger.info("Fonts initialized via Resource Manager")


def map_input(keys, mouse_buttons, mouse_pos) -> dict:
    return {
        "up": keys[pygame.K_w] or keys[pygame.K_UP],
        "down": keys[pygame.K_s] or keys[pygame.K_DOWN],
        "left": keys[pygame.K_a] or keys[pygame.K_LEFT],
        "right": keys[pygame.K_d] or keys[pygame.K_RIGHT],
        "attack": mouse_buttons[0],  # Left click
        # Special attack removed by user request - was Right click
        "block": keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT],  # Shift
        "mouse_pos": mouse_pos,
    }


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# draw_hud() moved to src/ui/hud.py


# draw_main_menu() and draw_pause_menu() moved to src/ui/menus.py


def main():
    pygame.init()
    init_fonts()  # Pre-create fonts once for performance
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Mount & Blade 2D RPG - MVP B")
    clock = pygame.time.Clock()

    # Initialize transition manager for smooth state changes
    transition_mgr = trans_mod.TransitionManager(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Start with main menu
    state = "MAIN_MENU"
    menu_selected = 0
    pause_selected = 0

    # Game state (will be initialized on New Game or Load Game)
    player = None
    player_troops = []
    world = None
    player_relations = None
    food_timer = None
    last_battle_faction = None
    battle = None
    start_time = None
    current_location = None
    selected_menu_option = 0
    inventory_ui = None  # Modern inventory UI
    shop_ui = None       # Modern shop UI
    shop_inventory = []  # Persistent shop inventory
    shop_gold = 500      # Shop keeper's gold
    pre_battle_player_pos = None  # Restore player's world position after battle
    CURRENT_SHOP_WEAK_ONLY = False
    game_over_reason = ""
    map_open = False

    # Non-blocking notification system
    active_notifications = []

    # Helper function to initialize new game
    def init_new_game():
        nonlocal player, player_troops, world, player_relations, food_timer, last_battle_faction
        nonlocal battle, start_time, current_location, selected_menu_option, shop_inventory, shop_gold

        rng_seed = int(time.time()) & 0xFFFFFFFF
        player = entities.create_player(rng_seed)
        player_troops = []
        world = world_mod.init_world(rng_seed)
        player.equipment = equip_mod.Equipment()
        player.inventory = []
        player_relations = entities.FactionRelations()
        food_timer = time.time()
        last_battle_faction = None
        battle = None
        start_time = time.time()
        current_location = None

        # Initialize shop inventory (persistent)
        shop_inventory = item_bridge.create_shop_inventory()
        shop_gold = 500
        selected_menu_option = 0

        # Move player spawn to Starting Village
        try:
            start_loc = next((loc for loc in world.locations if getattr(loc, 'name', '') == 'Starting Village'), None)
            if start_loc:
                player.pos = [float(start_loc.pos[0]), float(start_loc.pos[1])]
                # Mark starting village as discovered for the map overlay
                try:
                    if hasattr(world, 'visited_locations'):
                        world.visited_locations.add(start_loc.name)
                except Exception:
                    pass
        except Exception:
            pass

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # Update transition manager
        transition_mgr.update(dt)

        # Auto-reset transition when complete
        if transition_mgr.is_complete():
            transition_mgr.reset()

        # Centralized event handling
        events = pygame.event.get()
        # Handle general events first
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # Handle all key presses in one block
            if event.type == pygame.KEYDOWN:
                # Toggle Inventory
                if event.key == pygame.K_i:
                    # This check is a bit complex, might need a refactor later
                    # For now, it tries to find the inventory_ui instance
                    ui_instance = None
                    if 'self' in locals() and hasattr(self, "inventory_ui"):
                        ui_instance = self.inventory_ui
                    elif 'inventory_ui' in locals() and inventory_ui is not None:
                        ui_instance = inventory_ui

                    if ui_instance:
                        ui_instance.toggle()

                # Open Character Screen (C key) - always opens; Enter triggers Level Up when points > 0
                if event.key == pygame.K_c:
                    if state in ("OVERWORLD", "PAUSED") and player:
                        from src.ui.character_screen import CharacterScreen
                        cs = CharacterScreen(screen, player)
                        result = cs.run()
                        if result == 'levelup':
                            try:
                                from src.ui.levelup_screen import LevelUpScreen
                                lvl = LevelUpScreen(screen, player)
                                if lvl.run():
                                    menus.show_notification(screen, "Attributes updated!", duration=1.5, color=(100, 255, 100))
                            except Exception:
                                pass

                # Main Menu navigation
                if state == "MAIN_MENU":
                    has_save = save_system.save_exists()
                    max_options = 3 if has_save else 2
                    if event.key == pygame.K_UP:
                        menu_selected = (menu_selected - 1) % max_options
                    elif event.key == pygame.K_DOWN:
                        menu_selected = (menu_selected + 1) % max_options
                    elif event.key == pygame.K_RETURN:
                        options = ["New Game", "Load Game", "Quit"] if has_save else ["New Game", "Quit"]
                        selected = options[menu_selected]
                        if selected == "New Game":
                            init_new_game()
                            state = "OVERWORLD"
                        elif selected == "Load Game":
                            save_data = save_system.load_game()
                            if save_data:
                                init_new_game()
                                player_troops, player_relations, loc_name = save_system.apply_save_data(
                                    save_data, player, world
                                )
                                try:
                                    from src.attributes import calculate_derived_stats
                                    calculate_derived_stats(player)
                                except Exception:
                                    pass
                                start_time = time.time() - save_data.get("game_time", 0)
                                state = "OVERWORLD"
                        elif selected == "Quit":
                            running = False

                # Pause Menu navigation
                elif state == "PAUSED":
                    if event.key == pygame.K_UP:
                        pause_selected = (pause_selected - 1) % 4
                    elif event.key == pygame.K_DOWN:
                        pause_selected = (pause_selected + 1) % 4
                    elif event.key == pygame.K_RETURN:
                        options = ["Resume", "Save Game", "Quit to Menu", "Quit Game"]
                        selected = options[pause_selected]
                        if selected == "Resume":
                            state = "OVERWORLD"
                        elif selected == "Save Game":
                            if player:
                                game_time = time.time() - start_time
                                success = save_system.save_game(player, player_troops, player_relations, world, current_location, game_time)
                                if success:
                                    menus.show_notification(screen, "Game Saved!", color=(100, 255, 100))
                                else:
                                    menus.show_notification(screen, "Save Failed!", color=(255, 100, 100))
                        elif selected == "Quit to Menu":
                            state = "MAIN_MENU"
                            menu_selected = 0
                        elif selected == "Quit Game":
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        state = "OVERWORLD"

                # Inventory toggle with I key
                elif event.key == pygame.K_i and state == "OVERWORLD":
                    state = "INVENTORY"

                # World map toggle (M) in overworld
                elif event.key == pygame.K_m and state == "OVERWORLD":
                    map_open = not map_open

                # General ESC key handling for other states
                elif event.key == pygame.K_ESCAPE:
                    if state in ["INVENTORY", "SHOP_MENU"]:
                        state = "OVERWORLD"
                        inventory_ui = None  # Reset inventory UI
                    elif state == "LOCATION_MENU":
                        state = "OVERWORLD"
                        current_location = None
                    elif state == "OVERWORLD" or state == "BATTLE":
                        state = "PAUSED"

        # Main menu rendering (skip game logic)
        if state == "MAIN_MENU":
            menus.draw_main_menu(screen, menu_selected, save_system.save_exists())
            pygame.display.flip()
            continue

        # Pause menu overlay (render after game state)
        if state == "PAUSED":
            # Still render game underneath, then overlay pause menu
            pass  # Will render at end

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Block input during transitions EXCEPT during battle (allow fade-in input)
        if transition_mgr.is_active() and state != "BATTLE":
            # Create empty input state (all False)
            input_state = {
                "up": False, "down": False, "left": False, "right": False,
                "attack": False, "block": False,
                "mouse_pos": mouse_pos
            }
        else:
            input_state = map_input(keys, mouse_buttons, mouse_pos)

        # Inventory opening moved to event handling (above) to prevent multiple triggers

        # Update global VFX
        vfx.update_particles(dt)

        screen.fill((18, 18, 28))

        if state == "OVERWORLD" and player:
            # Hunger System
            food_status = ""
            if time.time() - food_timer > 60:
                player.stats.food = max(0, player.stats.food - 1)
                food_timer = time.time()
            if player.stats.food == 0:
                food_status = "STARVING!"
            
            # Move player in overworld (with world bounds instead of screen bounds)
            vx = (-1 if input_state["left"] else 0) + (1 if input_state["right"] else 0)
            vy = (-1 if input_state["up"] else 0) + (1 if input_state["down"] else 0)

            # Dust particles on move
            is_moving = vx != 0 or vy != 0
            if is_moving:
                vfx.create_dust_cloud(player.pos, 1)

            # Normalize diagonal movement
            if vx != 0 and vy != 0:
                vx *= 0.707
                vy *= 0.707

            # Apply armor speed penalty
            speed_penalty = player.equipment.get_speed_penalty()
            # Terrain effects (forests/desert/swamp slow; roads speed up; mountains/rivers block)
            terrain_slow = 1.0
            try:
                if world.in_forest(player.pos):
                    terrain_slow *= 0.8
                if world.in_desert(player.pos):
                    terrain_slow *= 0.9
                if world.in_swamp(player.pos):
                    terrain_slow *= 0.6
                if hasattr(world, 'is_on_road') and world.is_on_road(player.pos):
                    terrain_slow *= 1.3
            except Exception:
                pass
            speed = player.stats.spd * (1.0 - speed_penalty) * terrain_slow
            # Reveal fog around player
            # Fog of War removido: exploração livre sem névoa

            # Attempt axis-wise movement with river blocking (mountains disabled)
            new_x = player.pos[0] + vx * speed * dt
            new_y = player.pos[1] + vy * speed * dt
            try:
                # Rivers block
                if not world.in_river((new_x, player.pos[1])):
                    player.pos[0] = new_x
                if not world.in_river((player.pos[0], new_y)):
                    player.pos[1] = new_y
            except Exception:
                player.pos[0] = new_x
                player.pos[1] = new_y

            # Clamp to world bounds (not screen bounds)
            player.pos[0] = clamp(player.pos[0], player.radius, world_mod.WORLD_WIDTH - player.radius)
            player.pos[1] = clamp(player.pos[1], player.radius, world_mod.WORLD_HEIGHT - player.radius)

            # Update troops to follow player in formation
            for i, troop in enumerate(player_troops):
                if not troop.alive():
                    continue

                # Formation: troops spread in a circle behind player
                angle = (i / max(1, len(player_troops))) * math.tau
                formation_dist = 50 + (i // 6) * 30  # Rings of troops
                target_x = player.pos[0] + math.cos(angle) * formation_dist
                target_y = player.pos[1] + math.sin(angle) * formation_dist

                # Move troop toward formation position
                dx = target_x - troop.pos[0]
                dy = target_y - troop.pos[1]
                dist = math.hypot(dx, dy)

                if dist > 10:  # Only move if far from target
                    # Speed up when far from formation
                    troop_speed = troop.stats.spd * (1.2 if dist > 100 else 1.0)
                    move_x = (dx / dist) * troop_speed * dt
                    move_y = (dy / dist) * troop_speed * dt
                    troop.pos[0] += move_x
                    troop.pos[1] += move_y

                # Clamp troops to world bounds
                troop.pos[0] = clamp(troop.pos[0], troop.radius, world_mod.WORLD_WIDTH - troop.radius)
                troop.pos[1] = clamp(troop.pos[1], troop.radius, world_mod.WORLD_HEIGHT - troop.radius)

            encounter = world_mod.update_world(world, player, dt, relations=player_relations)
            world_mod.render_world(screen, world, player, player_troops, player_relations)
            vfx.render_particles(screen, world.camera) # Render particles in overworld
            # Diplomacy HUD (compact)
            if player_relations:
                try:
                    ui_hud.draw_diplomacy_hud(screen, player_relations, SCREEN_WIDTH - 240, 10)
                except Exception:
                    pass
            hud_module.draw_hud(screen, player, len(player_troops), relations=player_relations, food_status=food_status,
                               troops_list=player_troops, font_main=FONT_MAIN, font_small=FONT_SMALL, font_label=FONT_LABEL, font_large=FONT_LARGE)

            # World Map overlay (shows discovered towns + your position)
            if map_open:
                world_mod.render_world_map(screen, world, player)

            # Check for nearby locations
            nearest_location = None
            nearest_dist = float('inf')
            for loc in world.locations:
                dist = loc.distance_to(player)
                # Tighter interaction radius by location type (smaller than visual radius)
                try:
                    lt = getattr(loc, 'location_type', '')
                    base_r = float(getattr(loc, 'radius', 60) or 60)
                    if lt == 'castle':
                        eff_r = max(18.0, base_r * 0.65)
                    elif lt == 'bandit_camp':
                        eff_r = max(16.0, base_r * 0.60)
                    else:  # town and others
                        eff_r = max(16.0, base_r * 0.60)
                except Exception:
                    eff_r = 24.0
                if dist < nearest_dist and dist <= eff_r:
                    nearest_location = loc
                    nearest_dist = dist

            # Display prompt if near location
            if nearest_location:
                font = get_font(24)  # Cached
                prompt = f"Press E to enter {nearest_location.name}"
                prompt_surf = font.render(prompt, True, (255, 255, 100))
                prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
                bg_rect = prompt_rect.inflate(20, 10)
                pygame.draw.rect(screen, (0, 0, 0, 200), bg_rect)
                screen.blit(prompt_surf, prompt_rect)

                # Mark as discovered when inside its radius (no need to press E)
                try:
                    # Use reduced radius for discovery as well to match feel
                    lt = getattr(nearest_location, 'location_type', '')
                    base_r = float(getattr(nearest_location, 'radius', 60) or 60)
                    if lt == 'castle':
                        disc_r = max(10.0, base_r * 0.65)
                    elif lt == 'bandit_camp':
                        disc_r = max(10.0, base_r * 0.60)
                    else:
                        disc_r = max(10.0, base_r * 0.60)
                    if hasattr(world, 'visited_locations') and nearest_dist <= disc_r:
                        if nearest_location.name not in world.visited_locations:
                            world.visited_locations.add(nearest_location.name)
                            menus.show_notification(screen, f"Discovered: {nearest_location.name}")
                except Exception:
                    pass

                # Enter location on 'E' key
                if keys[pygame.K_e]:
                    current_location = nearest_location
                    selected_menu_option = 0
                    # Adventure memory: record visited (redundant with auto-mark above, kept for safety)
                    try:
                        if hasattr(world, 'visited_locations') and current_location.name not in world.visited_locations:
                            world.visited_locations.add(current_location.name)
                            menus.show_notification(screen, f"Discovered: {current_location.name}")
                    except Exception:
                        pass
                    # Set default shop faction based on location faction
                    try:
                        loc_f = getattr(current_location, 'faction', 'greeks')
                        from src import factions as _fx
                        if loc_f in ("bandits",):
                            globals()["CURRENT_SHOP_FACTION_ID"] = _fx.map_world_faction_to_faction_id(loc_f)
                        else:
                            globals()["CURRENT_SHOP_FACTION_ID"] = loc_f
                        # Weak-only shop in Starting Village
                        is_start_village = (getattr(current_location, 'name', '') == 'Starting Village')
                        globals()["CURRENT_SHOP_WEAK_ONLY"] = is_start_village
                        if is_start_village:
                            # Force bandit-themed shop in the starting village
                            globals()["CURRENT_SHOP_FACTION_ID"] = 'bandits'
                    except Exception:
                        globals()["CURRENT_SHOP_FACTION_ID"] = "greeks"
                        globals()["CURRENT_SHOP_WEAK_ONLY"] = False
                    state = "LOCATION_MENU"

            if encounter is not None:
                # Pass troops to battle
                encounter["troops"] = player_troops
                last_battle_faction = encounter.get("faction", "bandits")

                # CRITICAL FIX: Deep copy encounter to preserve enemy list during transition
                # Python closures capture by reference - encounter can be modified before callback runs!
                encounter_data = copy.deepcopy(encounter)
                print(f"[MAIN DEBUG] Creating transition with encounter: {len(encounter_data.get('enemies', []))} enemies")

                # Start transition to battle
                def enter_battle():
                    nonlocal battle, state
                    nonlocal pre_battle_player_pos
                    print(f"[MAIN DEBUG] Callback executing with encounter: {len(encounter_data.get('enemies', []))} enemies")
                    # Save player's world position to restore after battle
                    try:
                        pre_battle_player_pos = (float(player.pos[0]), float(player.pos[1]))
                    except Exception:
                        pre_battle_player_pos = None
                    battle = battle_mod.start_battle(player, encounter_data)
                    state = "BATTLE"

                trans_mod.create_battle_transition(transition_mgr, enter_battle)

        elif state == "BATTLE":
            # Note: battle is Claude's module; placeholder supports update/render/is_done
            battle.update(dt, input_state)
            battle.render(screen)
            # Pass the battle instance to the HUD to show stamina
            hud_module.draw_hud(screen, player, len(player_troops), battle_instance=battle, relations=player_relations, food_status="",
                               troops_list=player_troops, font_main=FONT_MAIN, font_small=FONT_SMALL, font_label=FONT_LABEL, font_large=FONT_LARGE)

            # CRITICAL FIX: Only process rewards once per battle
            if battle.is_done() and not getattr(battle, '_rewards_processed', False):
                result = battle.outcome()
                if result.get("victory", False):
                    player.stats.hp = min(player.stats.hp_max, result.get("player_state", {}).get("hp", player.stats.hp))

                    # Grant XP with difficulty scaling
                    gained = result.get("xp", 0)
                    minutes = (time.time() - start_time) / 60.0
                    diff = rpg.current_difficulty(minutes, player.stats.level)
                    level_up_result = rpg.grant_xp(player, int(gained * max(1.0, diff)))
                    if level_up_result.get("leveled_up", False):
                        vfx.create_levelup_glow(player.pos)
                        points_earned = level_up_result.get("points_earned", 0)
                        menus.show_notification(screen, f"LEVEL UP! Now Level {player.stats.level}! (+{points_earned} attribute points)", duration=2.5, color=(255, 215, 0))

                        # Open level up screen if player has points to spend
                        if player.stats.attribute_points > 0:
                            from src.ui.levelup_screen import LevelUpScreen
                            levelup_ui = LevelUpScreen(screen, player)
                            confirmed = levelup_ui.run()
                            if confirmed:
                                menus.show_notification(screen, "Attributes updated!", duration=1.5, color=(100, 255, 100))
                            else:
                                # Player cancelled, keep points for later
                                menus.show_notification(screen, "Level up cancelled (points saved)", duration=1.5, color=(255, 200, 100))

                    # Grant Gold (with CHA bonus)
                    gold_gained = result.get("gold", 0)
                    gold_with_bonus = int(gold_gained * player.stats.gold_bonus)
                    player.stats.gold += gold_with_bonus

                    # Show gold notification if significant
                    if gold_with_bonus > 0:
                        bonus_pct = int((player.stats.gold_bonus - 1.0) * 100)
                        if bonus_pct > 0:
                            menus.show_notification(screen, f"+{gold_with_bonus} gold (+{bonus_pct}% CHA bonus)", duration=1.5, color=(255, 215, 0))

                    # Veterancy: Check for troop promotions
                    promoted_troops = result.get("promoted_troops", [])
                    if promoted_troops:
                        menus.show_notification(screen, f"{len(promoted_troops)} troop(s) promoted!")

                    # Update diplomacy: adjust relation with the defeated faction
                    defeated_enemies = result.get("defeated_enemies", [])
                    if last_battle_faction:
                        # Defeating a faction worsens relation with it
                        player_relations.update_relation(last_battle_faction, -2 * len(defeated_enemies))

                    # Update troops list with survivors
                    player_troops = result.get("surviving_troops", [])

                    defeated_enemies = result.get("defeated_enemies", [])

                    # --- Item Drop Logic ---
                    # 1) Unique monster legendary drops
                    try:
                        if last_battle_faction == 'monsters' or any(getattr(en, 'is_unique_monster', False) for en in defeated_enemies):
                            MONSTER_LOOT = {
                                'cyclops': 'cyclops_club',
                                'dire wolf': 'dire_wolf_pelt',
                                'minotaur': 'minotaur_labrys',
                                'hydra': 'hydra_scale_mail',
                                'giant boar': 'boar_tusk_spear',
                                'sabertooth': 'sabertooth_claws',
                                'nemean lion': 'nemean_lion_hide',
                                'harpy': 'harpy_feather_cloak',
                                'gorgon': 'gorgon_visor',
                                'centaur': 'centaur_lance',
                            }
                            for en in defeated_enemies:
                                if getattr(en, 'is_unique_monster', False):
                                    key = str(getattr(en, 'enemy_type', '')).lower()
                                    iid = MONSTER_LOOT.get(key)
                                    if iid and len(player.inventory) < 20:
                                        it = items.get_item_by_id(iid)
                                        if it:
                                            player.inventory.append(it)
                                            menus.show_notification(screen, f"Legendary Loot: {it.get_display_name()}!")
                    except Exception:
                        pass

                    # 2) Faction-based regular drops (skip if monsters battle)
                    if last_battle_faction != 'monsters':
                        fac_id = factions.map_world_faction_to_faction_id(last_battle_faction)
                        for _ in defeated_enemies:
                            loot_item = factions.roll_loot(fac_id, tier_hint=2, chance=0.20)
                            if loot_item and len(player.inventory) < 20:
                                player.inventory.append(loot_item)
                                menus.show_notification(screen, f"Loot: {loot_item.get_display_name()}!")

                    # Auto-recruitment REMOVED - player must recruit manually at towns
                    # Troops only recruited through taverns/towns now
                else:
                    # Permadeath roll: sometimes defeat = permanent death
                    if random.random() < PERMADEATH_CHANCE:
                        game_over_reason = "Seus ferimentos foram fatais em combate."
                        menus.show_notification(screen, "Você caiu em batalha!", duration=2.5, color=(255, 80, 80))
                        battle = None
                        state = "GAME_OVER"
                        player = None
                        world = None
                        player_troops = []
                        continue

                    # On defeat: 50% chance of enslavement if against bandits
                    if last_battle_faction == "bandits" and random.random() < 0.5:
                        print("Captured by bandits!")
                        player.stats.gold = int(player.stats.gold * 0.5)
                        player_troops = [] # All troops are lost
                        player.stats.hp = player.stats.hp_max * 0.3
                        state = "ENSLAVED" # New game state
                        battle = None
                        continue # Skip the rest of the loop to go directly to the ENSLAVED state
                    else:
                        # Normal defeat: small penalty and heal
                        player.stats.xp = max(0, player.stats.xp - 5)
                        player.stats.hp = player.stats.hp_max
                        for troop in player_troops:
                            troop.stats.hp = troop.stats.hp_max

                # Mark rewards as processed to prevent infinite XP/gold/recruitment
                battle._rewards_processed = True

                # Transition back to overworld (victory or defeat)
                def exit_battle():
                    nonlocal state, battle
                    nonlocal pre_battle_player_pos
                    state = "OVERWORLD"
                    battle = None
                    # Restore player's world position
                    if pre_battle_player_pos is not None:
                        try:
                            player.pos = [pre_battle_player_pos[0], pre_battle_player_pos[1]]
                        except Exception:
                            pass

                trans_mod.create_victory_transition(transition_mgr, exit_battle)

        elif state == "LOCATION_MENU":
            # Render background (darkened overworld)
            world_mod.render_world(screen, world, player, player_troops, player_relations)
            dark_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            dark_overlay.set_alpha(180)
            dark_overlay.fill((0, 0, 0))
            screen.blit(dark_overlay, (0, 0))

            # Menu box
            menu_width = 500
            menu_height = 400
            menu_x = (SCREEN_WIDTH - menu_width) // 2
            menu_y = (SCREEN_HEIGHT - menu_height) // 2

            pygame.draw.rect(screen, (40, 40, 50), (menu_x, menu_y, menu_width, menu_height))
            pygame.draw.rect(screen, (100, 150, 200), (menu_x, menu_y, menu_width, menu_height), 3)

            # Title
            title_font = get_font(36)  # Cached
            title_surf = title_font.render(current_location.name, True, (255, 255, 255))
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, menu_y + 40))
            screen.blit(title_surf, title_rect)

            # Menu options based on location type
            menu_options = []
            if current_location.location_type == "town":
                options = ["Tavern (Rest - 10 Gold)", "Recruit Troops (30 Gold)", "Buy Food (15 Gold)", "Equipment Shop"]
                # Only show the peace option if at war (use location faction)
                try:
                    loc_fid = getattr(current_location, 'faction', 'greeks')
                except Exception:
                    loc_fid = 'greeks'
                if player_relations.get_status(loc_fid) == "GUERRA":
                    options.append("Propose Peace (100 Gold)")
                options.append("Leave")
                menu_options = options
            elif current_location.location_type == "castle":
                menu_options = ["Rest (Free)", "Recruit Troops", "Equipment Shop", "Leave"]
            elif current_location.location_type == "bandit_camp":
                menu_options = ["Attack Camp", "Leave"]

            # Handle input for menu navigation
            font = get_font(30)  # Cached
            for event in events: # Use the centralized event list
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        selected_menu_option = (selected_menu_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        selected_menu_option = (selected_menu_option + 1) % len(menu_options)
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE or event.key == pygame.K_e:
                        # Execute selected option
                        selected_text = menu_options[selected_menu_option]

                        if "Leave" in selected_text:
                            state = "OVERWORLD"
                            current_location = None

                        elif "Descansar" in selected_text:
                            # Heal player and troops
                            cost = 10 if "10 Gold" in selected_text else 0
                            if player.stats.gold >= cost:
                                player.stats.hp = player.stats.hp_max
                                for troop in player_troops:
                                    troop.stats.hp = troop.stats.hp_max
                                player.stats.gold -= cost
                                # print(f"Descansou! HP restaurado. (-{cost} gold)")
                                menus.show_notification(screen, f"Rested! HP restored. (-{cost} gold)")
                            else:
                                # print("Gold insuficiente para descansar!")
                                menus.show_notification(screen, "Not enough gold to rest!", color=(255,100,100))
                            pygame.time.delay(500) # Pequeno delay para ver a notificação
                        elif "Recruit Troops" in selected_text:
                            # Simple recruitment
                            max_troops = player.stats.level + 1
                            if len(player_troops) >= max_troops:
                                print(f"Você já tem o máximo de tropas! ({max_troops})")
                            else:
                                recruit_cost = 30
                                if player.stats.gold >= recruit_cost:
                                    troop_types = ["warrior", "archer", "tank"]
                                    tier = max(1, player.stats.level // 2)
                                    troop_type = random.choice(troop_types)
                                    new_troop = entities.create_troop(int(time.time() * 1000) % 1000000, troop_type, tier)
                                    player_troops.append(new_troop)
                                    player.stats.gold -= recruit_cost
                                    menus.show_notification(screen, f"Recruited {troop_type} tier {tier}! (-{recruit_cost} gold)")
                                else:
                                    menus.show_notification(screen, "Not enough gold to recruit!", color=(255,100,100))
                            pygame.time.delay(500)

                        elif "Buy Food" in selected_text:
                            cost = 15
                            if player.stats.gold >= cost:
                                player.stats.gold -= cost
                                player.stats.food += 10
                                menus.show_notification(screen, f"Bought 10 rations! (-{cost} gold)")
                            else:
                                menus.show_notification(screen, "Not enough gold!", color=(255,100,100))
                            pygame.time.delay(500)

                        elif "Equipment Shop" in selected_text:
                            state = "SHOP_MENU"
                            current_location = None # Sair do menu de localização
                            continue

                        elif "Propose Peace" in selected_text:
                            cost = 100
                            if player.stats.gold >= cost:
                                player.stats.gold -= cost
                                try:
                                    loc_fid = getattr(current_location, 'faction', 'greeks')
                                except Exception:
                                    loc_fid = 'greeks'
                                player_relations.update_relation(loc_fid, 30)
                                menus.show_notification(screen, "Relações com o Reino melhoraram!")

                        elif "Attack Camp" in selected_text:
                            # Create encounter with multiple enemies
                            enemies = []
                            encounter_seed = int(time.time()) & 0xFFFFFFFF
                            for i in range(3, 6):  # 3-5 bandits
                                tier = max(1, player.stats.level)
                                enemy = entities.create_enemy(encounter_seed ^ i, tier)
                                rpg.scale_enemy(enemy, 1.0 + 0.2 * tier)
                                enemies.append(enemy)

                            encounter = {"enemies": enemies, "troops": player_troops, "rng_seed": encounter_seed, "faction": "bandits"}
                            battle = battle_mod.start_battle(player, encounter)
                            state = "BATTLE"
                            current_location = None

            # Render menu options
            for i, option in enumerate(menu_options):
                color = (255, 255, 100) if i == selected_menu_option else (200, 200, 200)
                option_surf = font.render(f"{'> ' if i == selected_menu_option else '  '}{option}", True, color)
                option_y = menu_y + 100 + i * 50
                screen.blit(option_surf, (menu_x + 50, option_y))

            # Tooltips
            selected_text = menu_options[selected_menu_option]
            tooltip_text = ""
            if "Rest" in selected_text:
                tooltip_text = "Restores all HP for the player and troops."
            elif "Recruit Troops" in selected_text:
                tooltip_text = f"Hires a new troop of tier {max(1, player.stats.level // 2)}."
            elif "Buy Food" in selected_text:
                tooltip_text = "Buys 10 rations to prevent starvation."
            elif "Propose Peace" in selected_text:
                tooltip_text = "Significantly improves your relation with the Kingdom."
            elif "Attack Camp" in selected_text:
                tooltip_text = "Starts a difficult battle against multiple bandits."
            menus.render_tooltip(screen, tooltip_text, pygame.mouse.get_pos())

            # Display player gold and troops
            info_font = get_font(22)  # Cached
            info_text = f"Gold: {player.stats.gold} | Tropas: {len(player_troops)}/{player.stats.level + 1}"
            info_surf = info_font.render(info_text, True, (255, 215, 0))
            screen.blit(info_surf, (menu_x + 20, menu_y + menu_height - 40))

        elif state == "ENSLAVED":
            screen.fill((20, 10, 10))
            font_large = get_font(60)  # Cached
            font_med = get_font(32)  # Cached

            title_surf = font_large.render("ENSLAVED", True, (200, 50, 50))
            screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)))

            instr_surf = font_med.render("Press SPACE repeatedly to escape!", True, (220, 220, 220))
            screen.blit(instr_surf, instr_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

            # Mini-game logic (simples por enquanto)
            # Em uma implementação real, isso teria uma barra de progresso.
            if keys[pygame.K_SPACE]:
                # Simula a fuga após alguns apertos
                if random.random() < 0.1:
                    print("You escaped!")
                    player.stats.hp = player.stats.hp_max * 0.5 # Recupera um pouco de vida
                    # Move player near the starting town
                    player.pos = [550, 1550]
                    state = "OVERWORLD"

        elif state == "INVENTORY":
            # Render overworld as background (frozen)
            world_mod.render_world(screen, world, player, player_troops, player_relations)
            

            # Darken background slightly
            darken_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            darken_overlay.set_alpha(100)
            darken_overlay.fill((0, 0, 0))
            screen.blit(darken_overlay, (0, 0))

            if not inventory_ui:
                inventory_ui = InventoryUI(SCREEN_WIDTH, SCREEN_HEIGHT)

            # Force inventory to be visible (bypass fade system for now)
            inventory_ui.visible = True
            inventory_ui._state = "open"
            inventory_ui._alpha = 255

            # Convert inventory to new Item format for display
            display_inventory = item_bridge.convert_inventory_to_items(player.inventory)

            # Get equipped items summary
            equipped_items = item_bridge.get_equipped_summary(player.equipment)

            # Player stats for display
            player_stats = {
                "gold": player.stats.gold,
                "hp": player.stats.hp,
                "hp_max": player.stats.hp_max,
            }

            # Equip callback (expects an Item instance)
            def on_equip(item):
                if item:
                    try:
                        equip_mod.equip_item(player, item)
                        name = item.get_display_name() if hasattr(item, "get_display_name") else str(item)
                        menus.show_notification(screen, f"Equipped: {name}", color=(100, 255, 100))
                    except Exception as exc:
                        menus.show_notification(screen, f"Equip failed: {exc}", color=(255, 100, 100))

            # Drop callback (expects an Item instance)
            def on_drop(item):
                if item and item in player.inventory:
                    try:
                        player.inventory.remove(item)
                        name = item.get_display_name() if hasattr(item, "get_display_name") else str(item)
                        menus.show_notification(screen, f"Dropped: {name}", color=(255, 100, 100))
                    except Exception as exc:
                        menus.show_notification(screen, f"Drop failed: {exc}", color=(255, 100, 100))

            # Update UI with callbacks
            inventory_ui.update(events, mouse_pos, player, on_equip, on_drop)

            # Render UI (signature: screen, player, equipped_items, mouse_pos)
            inventory_ui.render(screen, player, equipped_items, mouse_pos)

            # Close inventory
            if inventory_ui.should_close_inventory():
                state = "OVERWORLD"
                inventory_ui = None

        elif state == "SHOP_MENU":
            # Initialize ShopUI and inventory once
            global SHOP_UI, SHOP_INVENTORY, SHOP_GOLD
            if SHOP_UI is None:
                SHOP_UI = ui_shop.ShopUI(SCREEN_WIDTH, SCREEN_HEIGHT)
            if SHOP_INVENTORY is None:
                try:
                    SHOP_INVENTORY = equip_mod.get_random_shop_inventory(12, faction_id=CURRENT_SHOP_FACTION_ID)
                except Exception:
                    SHOP_INVENTORY = equip_mod.get_random_shop_inventory(12)
                # Filter to weak-only (bandit-tier) in Starting Village
                try:
                    if CURRENT_SHOP_WEAK_ONLY and SHOP_INVENTORY:
                        SHOP_INVENTORY = [it for it in SHOP_INVENTORY if (not it) or getattr(it, 'tier', 1) <= 1]
                        # Ensure we still have some items; if too few, top-up from generic T1 pools
                        if len([it for it in SHOP_INVENTORY if it]) < 4:
                            # Pull generic tier 1 items from item DB
                            from src import items as _itdb
                            from src import factions as _fx
                            thr = _fx.get_faction('thrace') or {}
                            thr_keys = set((thr.get('shop_weights') or {}).keys())
                            t1_weapons = [k for k, v in _itdb.ITEM_DATABASE.items() if k in thr_keys and v.get('tier',1)==1 and ('damage' in v or 'defense' in v)]
                            import random as _r
                            for k in _r.sample(t1_weapons, min(8, len(t1_weapons))):
                                SHOP_INVENTORY.append(_itdb.get_item_by_id(k, with_random_quality=True))
                except Exception:
                    pass

            # Wire buttons
            def on_close():
                nonlocal state
                global SHOP_UI, SHOP_INVENTORY
                SHOP_UI.should_close = True
                # Cleanup and return to overworld
                state = "OVERWORLD"
                SHOP_UI = None
                SHOP_INVENTORY = None

            def on_buy():
                sel = getattr(SHOP_UI, 'selected_shop_item', None)
                if sel is None or sel >= len(SHOP_INVENTORY):
                    return
                item = SHOP_INVENTORY[sel]
                if not item:
                    return
                cost = item.get_value() if hasattr(item, 'get_value') else 0
                try:
                    discount = float(getattr(player.stats, 'shop_discount', 0.0))
                except Exception:
                    discount = 0.0
                cost = max(0, int(cost * (1.0 - discount)))
                if cost <= player.stats.gold and len(player.inventory) < 20:
                    player.stats.gold -= cost
                    player.inventory.append(item)
                    SHOP_INVENTORY.pop(sel)
                    menus.show_notification(screen, f"Bought: {item.get_display_name()}")

            def on_sell():
                sel = getattr(SHOP_UI, 'selected_player_item', None)
                # Player inventory is list of Items
                if sel is None or sel >= len(player.inventory):
                    return
                item = player.inventory[sel]
                if not item:
                    return
                price = item.get_sell_price() if hasattr(item, 'get_sell_price') else 0
                try:
                    bonus = float(getattr(player.stats, 'shop_discount', 0.0))
                except Exception:
                    bonus = 0.0
                price = max(0, int(price * (1.0 + bonus)))
                player.stats.gold += price
                # Remove from player inventory and optionally add to shop (buy-back)
                try:
                    player.inventory.remove(item)
                    if SHOP_INVENTORY is not None:
                        SHOP_INVENTORY.append(item)
                except Exception:
                    pass
                menus.show_notification(screen, f"Sold: {item.get_display_name()}")

            SHOP_UI.close_btn.callback = on_close
            SHOP_UI.buy_btn.callback = on_buy
            SHOP_UI.sell_btn.callback = on_sell

            # Update and Render ShopUI
            SHOP_UI.update(events, mouse_pos, SHOP_INVENTORY or [], player.inventory, player.stats.gold, SHOP_GOLD)

            # Facção da loja: título colorido
            try:
                fac = factions.get_faction(CURRENT_SHOP_FACTION_ID)
                fac_name = fac.get('name', CURRENT_SHOP_FACTION_ID) if fac else CURRENT_SHOP_FACTION_ID
                color = fac.get('palette', {}).get('primary', (255,255,255)) if fac else (255,255,255)
            except Exception:
                fac_name = CURRENT_SHOP_FACTION_ID
                color = (255,255,255)

            title_font = get_font(40)  # Cached
            title_surf = title_font.render(f"Equipment Shop — {fac_name}", True, color)
            screen.blit(title_surf, (70, 60))

            SHOP_UI.render(screen, SHOP_INVENTORY or [], player.inventory, player.stats.gold, SHOP_GOLD, mouse_pos, player)

        elif state == "GAME_OVER":
            screen.fill((8, 0, 0))
            title_font = get_font(64)
            title_surf = title_font.render("VOCE MORREU", True, (200, 20, 20))
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
            screen.blit(title_surf, title_rect)

            reason_text = game_over_reason or "A derrota foi definitiva."
            reason_font = get_font(28)
            reason_surf = reason_font.render(reason_text, True, (240, 220, 220))
            reason_rect = reason_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            screen.blit(reason_surf, reason_rect)

            prompt_font = get_font(22)
            prompt_surf = prompt_font.render("Pressione ENTER para voltar ao menu", True, (255, 255, 255))
            prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            screen.blit(prompt_surf, prompt_rect)

            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    state = "MAIN_MENU"
                    menu_selected = 0
                    player = None
                    world = None
                    player_troops = []
                    current_location = None
                    battle = None
                    break

        # Render pause menu overlay (on top of everything except notifications)
        if state == "PAUSED":
            menus.draw_pause_menu(screen, pause_selected)

        # Render notifications last (on top of everything)
        menus.render_notifications(screen)

        # Tiny FPS counter (top-left)
        try:
            fps_font = get_font(18)  # Cached
            fps_text = fps_font.render(f"{int(clock.get_fps())} FPS", True, (180, 180, 200))
            screen.blit(fps_text, (6, 4))
        except (AttributeError, ValueError):
            # Skip FPS counter if clock not available
            pass

        # Render transition overlay (absolute last - over everything including notifications)
        transition_mgr.render(screen)

        pygame.display.flip()

    pygame.quit()


# menus.show_notification(), render_notifications(), and menus.render_tooltip() moved to src/ui/menus.py


# draw_shop_screen() moved to src/ui/shop_screen.py


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Game closed by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to run the game!")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nCheck if Pygame is installed:")
        print("  Execute: install.bat")
    finally:
        # Ensure pygame quits properly
        try:
            import pygame
            pygame.quit()
        except:
            pass

