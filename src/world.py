from __future__ import annotations
import math
import random
from typing import Any, Dict, Optional
import pygame
from . import entities
from . import rpg
from . import vfx
from . import factions


WORLD_WIDTH = 8000
WORLD_HEIGHT = 6000

# Ground texture generation constants
GRASS_TUFT_DENSITY = 18000  # Lower = more dense
STONE_DENSITY = 26000  # Lower = more dense
DIRT_SPECKLE_DENSITY = 16000  # Lower = more dense
MIN_GRASS_TUFTS = 20
MIN_STONES = 12
MIN_DIRT_SPECKLES = 40


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.pos[0] + int(self.width / 2)
        y = -target.pos[1] + int(self.height / 2)

        # Limit scrolling to map size
        x = min(0, x)  # left
        y = min(0, y)  # top
        x = max(-(WORLD_WIDTH - self.width), x)  # right
        y = max(-(WORLD_HEIGHT - self.height), y)  # bottom
        self.camera = pygame.Rect(x, y, self.width, self.height)

    def world_to_screen(self, pos):
        return pos[0] + self.camera.x, pos[1] + self.camera.y

    def is_visible(self, pos, radius=50):
        screen_pos = self.world_to_screen(pos)
        return -radius < screen_pos[0] < self.width + radius and -radius < screen_pos[1] < self.height + radius


class World:
    def __init__(self, seed: int, screen_width: int, screen_height: int):
        self.seed = seed
        self.rng = random.Random(seed)
        self.enemies: list[entities.Entity] = []
        self.locations: list[entities.Location] = []
        self.camera = Camera(screen_width, screen_height)
        self._create_terrain()
        self._create_locations()
        self._generate_roads()
        self._spawn_unique_monsters()
        self._spawn_initial_enemies()
        self._build_ground_chunks()
        # Fog of War removido: modo aventura sem mapa/névoa
        # Track active army groups per castle (for patrol caps)
        self._castle_active_groups: dict[str, int] = {}
        # FPS helpers
        self._auto_resolve_timer = 0.0
        self._global_army_cap = 120
        # Places the player has visited (adventure-style memory)
        self.visited_locations: set[str] = set()

    # ---- Terrain -----------------------------------------------------------
    def _create_terrain(self):
        """Create impassable mountains and slow forests as world-space rects."""
        self.terrain_mountains: list[pygame.Rect] = []
        self.terrain_forests: list[pygame.Rect] = []
        self.terrain_desert: list[pygame.Rect] = []
        self.terrain_swamp: list[pygame.Rect] = []
        self.terrain_rivers: list[pygame.Rect] = []
        self.roads: list[list[tuple[float, float]]] = []  # list of polylines
        self.road_width: int = 14

        rng = self.rng
        # Mountains disabled per user request (blocking issues on cities)
        self.terrain_mountains = []

        # Forests: more frequent, medium patches
        for _ in range(18):
            w = rng.randint(280, 520)
            h = rng.randint(240, 440)
            x = rng.randint(100, WORLD_WIDTH - w - 100)
            y = rng.randint(100, WORLD_HEIGHT - h - 100)
            self.terrain_forests.append(pygame.Rect(x, y, w, h))

        # Desert patches (south/southeast bias)
        for _ in range(12):
            w = rng.randint(400, 900)
            h = rng.randint(300, 700)
            x = rng.randint(WORLD_WIDTH//3, WORLD_WIDTH - w - 120)
            y = rng.randint(2*WORLD_HEIGHT//3, WORLD_HEIGHT - h - 120)
            self.terrain_desert.append(pygame.Rect(x, y, w, h))

        # Swamps (southeast/riverine)
        for _ in range(8):
            w = rng.randint(300, 700)
            h = rng.randint(280, 600)
            x = rng.randint(WORLD_WIDTH//2, WORLD_WIDTH - w - 150)
            y = rng.randint(WORLD_HEIGHT//2, WORLD_HEIGHT - h - 150)
            self.terrain_swamp.append(pygame.Rect(x, y, w, h))

        # Simple rivers: long thin rectangles
        for _ in range(3):
            rw = rng.randint(80, 120)
            rh = rng.randint(1600, 2200)
            x = rng.randint(400, WORLD_WIDTH - rw - 400)
            y = rng.randint(200, WORLD_HEIGHT - rh - 200)
            self.terrain_rivers.append(pygame.Rect(x, y, rw, rh))

        # Ensure some terrain near the starting area so differences are visible
        try:
            start_x, start_y = 800, 3000
            self.terrain_forests.append(pygame.Rect(start_x - 300, start_y - 225, 600, 450))
            # Do not place mountain near start
        except Exception:
            pass

        # Precompose nice-looking surfaces for patches (performance + visuals)
        try:
            from . import terrain_renderer as tr
        except Exception:
            tr = None

        self._patch_cache = {"mountain": [], "forest": [], "desert": [], "swamp": []}
        rng = self.rng
        if tr:
            for r in self.terrain_mountains:
                surf = tr.build_patch_surface((r.width, r.height), "mountain", rng.randint(0, 1_000_000))
                self._patch_cache["mountain"].append((r, surf))
            for r in self.terrain_forests:
                biome = "forest"
                surf = tr.build_patch_surface((r.width, r.height), biome, rng.randint(0, 1_000_000))
                self._patch_cache["forest"].append((r, surf))
            for r in self.terrain_desert:
                surf = tr.build_patch_surface((r.width, r.height), "desert", rng.randint(0, 1_000_000))
                self._patch_cache["desert"].append((r, surf))
            for r in self.terrain_swamp:
                surf = tr.build_patch_surface((r.width, r.height), "swamp", rng.randint(0, 1_000_000))
                self._patch_cache["swamp"].append((r, surf))

    def in_mountain(self, pos: tuple[float, float]) -> bool:
        x, y = int(pos[0]), int(pos[1])
        return any(r.collidepoint(x, y) for r in self.terrain_mountains)

    def in_forest(self, pos: tuple[float, float]) -> bool:
        x, y = int(pos[0]), int(pos[1])
        return any(r.collidepoint(x, y) for r in self.terrain_forests)

    def in_desert(self, pos: tuple[float, float]) -> bool:
        x, y = int(pos[0]), int(pos[1])
        return any(r.collidepoint(x, y) for r in self.terrain_desert)

    def in_swamp(self, pos: tuple[float, float]) -> bool:
        x, y = int(pos[0]), int(pos[1])
        return any(r.collidepoint(x, y) for r in self.terrain_swamp)

    def in_river(self, pos: tuple[float, float]) -> bool:
        x, y = int(pos[0]), int(pos[1])
        return any(r.collidepoint(x, y) for r in self.terrain_rivers)

    # ---- Fog of War ---------------------------------------------------------
    # Fog of War removido

    # ---- Roads --------------------------------------------------------------
    def _generate_roads(self):
        """Generate curved roads connecting major locations.

        - Connect each castle to its nearest town
        - Connect towns in a loose chain by nearest-neighbor to reach ~10-15 roads
        """
        try:
            from . import road_generator as rg
        except Exception:
            self.roads = []
            return

        towns = [loc for loc in self.locations if loc.location_type == 'town']
        castles = [loc for loc in self.locations if loc.location_type == 'castle']
        rng = self.rng

        roads: list[list[tuple[float, float]]] = []

        # Helper to add a road polyline A->B
        def add_road(a_pos, b_pos):
            seed = rng.randint(0, 1_000_000)
            pts = rg.build_road_polyline(a_pos, b_pos, seed, curviness=0.22, samples=48)
            roads.append(pts)

        # 1) Each castle to nearest town
        for c in castles:
            best_t = None
            best_d2 = 1e18
            for t in towns:
                dx = t.pos[0] - c.pos[0]
                dy = t.pos[1] - c.pos[1]
                d2 = dx*dx + dy*dy
                if d2 < best_d2:
                    best_d2 = d2
                    best_t = t
            if best_t:
                add_road(c.pos, best_t.pos)

        # 2) Connect towns in a nearest-neighbor chain (limit to ~10)
        if towns:
            remaining = towns[:]
            current = remaining.pop(0)
            chain_count = 0
            while remaining and chain_count < 10:
                # pick nearest
                best_i = 0
                best_d2 = 1e18
                for i, t in enumerate(remaining):
                    dx = t.pos[0] - current.pos[0]
                    dy = t.pos[1] - current.pos[1]
                    d2 = dx*dx + dy*dy
                    if d2 < best_d2:
                        best_d2 = d2
                        best_i = i
                nxt = remaining.pop(best_i)
                add_road(current.pos, nxt.pos)
                current = nxt
                chain_count += 1

        self.roads = roads

    def is_on_road(self, pos: tuple[float, float], pad: float = 10.0) -> bool:
        """Return True if pos is within road corridor."""
        try:
            from .road_generator import distance_point_to_segment
        except Exception:
            return False
        px, py = float(pos[0]), float(pos[1])
        radius = (self.road_width * 0.5) + float(pad)
        r2 = radius
        for poly in self.roads:
            for i in range(1, len(poly)):
                if distance_point_to_segment((px, py), poly[i-1], poly[i]) <= r2:
                    return True
        return False

    # ---- Ground texture ----------------------------------------------------
    def _build_ground_chunks(self, chunk: int = 512):
        """Pre-compose subtle ground texture chunks to avoid a flat green map.

        Draws small stones, grass tufts and speckles with low alpha.
        """
        self.ground_chunks: list[tuple[pygame.Rect, pygame.Surface]] = []
        cols = (WORLD_WIDTH + chunk - 1) // chunk
        rows = (WORLD_HEIGHT + chunk - 1) // chunk
        for cy in range(rows):
            for cx in range(cols):
                x0 = cx * chunk
                y0 = cy * chunk
                w = min(chunk, WORLD_WIDTH - x0)
                h = min(chunk, WORLD_HEIGHT - y0)
                rect = pygame.Rect(x0, y0, w, h)
                surf = pygame.Surface((w, h), pygame.SRCALPHA)

                # Deterministic RNG per chunk
                rng = random.Random((self.seed << 8) ^ (cx * 73856093) ^ (cy * 19349663))

                # Grass tufts
                tufts = max(MIN_GRASS_TUFTS, (w * h) // GRASS_TUFT_DENSITY)
                for _ in range(tufts):
                    x = rng.randint(2, w - 3)
                    y = rng.randint(2, h - 3)
                    length = rng.randint(3, 7)
                    color = (50, 140, 70, 70)
                    pygame.draw.line(surf, color, (x, y), (x, y - length), 1)
                    # side blades
                    if rng.random() < 0.5:
                        pygame.draw.line(surf, (60, 150, 80, 60), (x, y - 1), (x + 2, y - length + 2), 1)

                # Small stones
                stones = max(MIN_STONES, (w * h) // STONE_DENSITY)
                for _ in range(stones):
                    sx = rng.randint(0, w - 2)
                    sy = rng.randint(0, h - 2)
                    rw = rng.randint(2, 4)
                    rh = rng.randint(2, 4)
                    col = (120, 120, 120, 90)
                    pygame.draw.ellipse(surf, col, (sx, sy, rw, rh))

                # Speckles/dirt
                dots = max(MIN_DIRT_SPECKLES, (w * h) // DIRT_SPECKLE_DENSITY)
                for _ in range(dots):
                    dx = rng.randint(0, w - 1)
                    dy = rng.randint(0, h - 1)
                    col = (30, 90, 50, 25)
                    surf.set_at((dx, dy), col)

                self.ground_chunks.append((rect, surf))

    def _create_locations(self):
        self.locations = []
        # Starting towns (center-ish and east-ish)
        self.locations.append(entities.Location("Starting Village", (800, 3000), "town", 90, "greeks"))
        self.locations.append(entities.Location("Merchant's Port", (7400, 1200), "town", 90, "greeks"))

        # Programmatic castles: 3 per faction (except bandits)
        facs = [f for f in factions.list_factions() if f != "bandits"]
        zones = [
            (0, WORLD_WIDTH//3, 0, WORLD_HEIGHT//3),                # NW
            (WORLD_WIDTH//3, 2*WORLD_WIDTH//3, 0, WORLD_HEIGHT//3), # N
            (2*WORLD_WIDTH//3, WORLD_WIDTH, 0, WORLD_HEIGHT//3),    # NE
            (0, WORLD_WIDTH//3, WORLD_HEIGHT//3, 2*WORLD_HEIGHT//3), # W
            (WORLD_WIDTH//3, 2*WORLD_WIDTH//3, WORLD_HEIGHT//3, 2*WORLD_HEIGHT//3), # C
            (2*WORLD_WIDTH//3, WORLD_WIDTH, WORLD_HEIGHT//3, 2*WORLD_HEIGHT//3),    # E
            (0, WORLD_WIDTH//3, 2*WORLD_HEIGHT//3, WORLD_HEIGHT),   # SW
            (WORLD_WIDTH//3, 2*WORLD_WIDTH//3, 2*WORLD_HEIGHT//3, WORLD_HEIGHT),    # S
            (2*WORLD_WIDTH//3, WORLD_WIDTH, 2*WORLD_HEIGHT//3, WORLD_HEIGHT),       # SE
        ]

        def rnd_in_zone(ix: int) -> tuple[int, int]:
            x0, x1, y0, y1 = zones[ix]
            return (
                self.rng.randint(x0 + 120, x1 - 120),
                self.rng.randint(y0 + 120, y1 - 120),
            )

        # Preferred zones by faction (rough historical mapping)
        pref = {
            "macedon": [0,1], "thrace": [0,3], "greeks": [1,4,5],
            "ptolemaic": [7,8], "kush": [7], "seleucid": [2,5],
            "pontus": [2], "rome": [3,4], "carthage": [6,3],
            "maurya": [8]
        }

        for fi, fid in enumerate(facs):
            pz = pref.get(fid, [])
            for k in range(3):
                if pz:
                    zone_index = pz[min(k, len(pz)-1)]
                else:
                    zone_index = (fi*3 + k) % len(zones)
                px, py = rnd_in_zone(zone_index)
                name = f"{factions.get_faction(fid).get('name', fid)} Keep {k+1}"
                self.locations.append(entities.Location(name, (px, py), "castle", 110, fid))

        # Bandit camps (3+)
        for i in range(5):
            px = self.rng.randint(400, WORLD_WIDTH-400)
            py = self.rng.randint(400, WORLD_HEIGHT-400)
            self.locations.append(entities.Location(f"Bandit Camp {i+1}", (px, py), "bandit_camp", 70, "bandits"))
        # Timers/counters para patrulhas
        self._patrol_timer = 0.0
        # Máximo de exércitos por castelo (bolinhas)
        self._patrol_cap_per_faction = 5
        # Diplomacia dinâmica entre facções (guerras/paz)
        self._diplo_timer = 0.0
        self.ai_wars: set[tuple[str, str]] = set()

        # Initialize bandits in permanent war with all factions
        from . import factions as fac_module
        all_factions = fac_module.list_factions()
        for fac in all_factions:
            if fac != 'bandits':
                self.ai_wars.add(tuple(sorted(('bandits', fac))))

    def _spawn_initial_enemies(self, num_enemies=15):
        # Seed the world by spawning around faction castles for distribution
        castles = [loc for loc in self.locations if loc.location_type == "castle"]
        if castles:
            for i in range(num_enemies):
                castle = self.rng.choice(castles)
                self._spawn_enemy(anchor_castle=castle)
        else:
            for i in range(num_enemies):
                self._spawn_enemy()

    def _spawn_enemy(self, anchor_castle: entities.Location | None = None):
        tier = self.rng.randint(1, 3)
        # Choose a faction anchor (nearest or provided castle)
        if anchor_castle is None:
            castles = [loc for loc in self.locations if loc.location_type == "castle"]
            anchor_castle = self.rng.choice(castles) if castles else None

        if anchor_castle is not None:
            fac_id = anchor_castle.faction
            # Map legacy tags to internal faction ids when necessary
            if fac_id in ("bandits",):
                fac_id = factions.map_world_faction_to_faction_id(fac_id)
            enemy_type = factions.roll_enemy_type(fac_id) or None
            e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=tier, enemy_type=enemy_type)
            # Spawn near castle
            sx = anchor_castle.pos[0] + self.rng.randint(-280, 280)
            sy = anchor_castle.pos[1] + self.rng.randint(-280, 280)
            e.pos = [max(50, min(WORLD_WIDTH - 50, sx)), max(50, min(WORLD_HEIGHT - 50, sy))]
            e.faction = fac_id
        else:
            # Fallback generic spawn (rare case)
            fac_id = "thrace"
            enemy_type = factions.roll_enemy_type(fac_id) or None
            e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=tier, enemy_type=enemy_type)
            # Random safe position away from Greek towns
            max_attempts = 100
            attempts = 0
            while attempts < max_attempts:
                e.pos = [self.rng.randint(50, WORLD_WIDTH - 50), self.rng.randint(50, WORLD_HEIGHT - 50)]
                is_safe_spawn = True
                for loc in self.locations:
                    if loc.faction == "greeks" and loc.distance_to(e) < 400:
                        is_safe_spawn = False
                        break
                if is_safe_spawn:
                    break
                attempts += 1
            if attempts >= max_attempts:
                e.pos = [self.rng.randint(50, WORLD_WIDTH - 50), self.rng.randint(50, WORLD_HEIGHT - 50)]
            e.faction = fac_id

        self.enemies.append(e)

    def _spawn_patrol_from_castle(self, castle: entities.Location):
        """Spawna uma pequena patrulha (1 inimigo por vez, simples) a partir de um castelo."""
        tier = self.rng.randint(1, 3)
        fac_id = castle.faction
        etype = factions.roll_enemy_type(fac_id) or None
        e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=tier, enemy_type=etype)
        # Spawn próximo ao castelo
        e.pos = [castle.pos[0] + self.rng.randint(-80, 80), castle.pos[1] + self.rng.randint(-80, 80)]
        # Marca metadados
        e.faction = fac_id
        e.home_pos = castle.pos
        e.ai_state = "PATROLLING"
        e.patrol_timer = 0.0
        e.patrol_target = None
        e.chase_alert_cooldown = 0.0
        self.enemies.append(e)

    def _spawn_army_from_castle(self, castle: entities.Location):
        """Spawn a single army marker with internal soldier count (1..10)."""
        tier = self.rng.randint(1, 3)
        fac_id = castle.faction
        etype = factions.roll_enemy_type(fac_id) or None
        e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=tier, enemy_type=etype)
        e.pos = [castle.pos[0] + self.rng.randint(-80, 80), castle.pos[1] + self.rng.randint(-80, 80)]
        e.faction = fac_id
        e.home_pos = castle.pos
        e.ai_state = "PATROLLING"
        e.patrol_timer = 0.0
        e.patrol_target = None
        e.chase_alert_cooldown = 0.0
        e.is_army = True
        e.army_size = self.rng.randint(1, 10)
        e.avg_tier = tier
        self.enemies.append(e)

    def _spawn_unique_monsters(self):
        """Spawn 10 unique, strong monsters across the map. Hostile to all."""
        monsters = [
            ("Cyclops", 420, 40, 110, 20),
            ("Dire Wolf", 220, 20, 190, 14),
            ("Minotaur", 380, 30, 130, 18),
            ("Hydra", 500, 28, 120, 20),
            ("Giant Boar", 260, 22, 170, 15),
            ("Sabertooth", 280, 24, 185, 14),
            ("Nemean Lion", 360, 26, 175, 16),
            ("Harpy", 240, 18, 200, 13),
            ("Gorgon", 340, 27, 140, 16),
            ("Centaur", 300, 25, 180, 16),
        ]
        for name, hp, atk, spd, radius in monsters:
            e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=3, enemy_type=name.lower())
            e.pos = [self.rng.randint(200, WORLD_WIDTH - 200), self.rng.randint(200, WORLD_HEIGHT - 200)]
            e.faction = 'monsters'
            e.enemy_type = name.lower()
            # Set archetype for sprite selection when available
            if name.lower() == 'minotaur':
                e.archetype = 'minotaur'
            e.stats.hp_max = hp
            e.stats.hp = hp
            e.stats.atk = atk
            e.stats.spd = spd
            e.radius = radius
            e.is_unique_monster = True
            e.is_army = False
            e.is_monster = True
            self.enemies.append(e)

        # Extra Minotaur near the Starting Village for testing
        try:
            start_loc = next((loc for loc in self.locations if getattr(loc, 'name', '') == 'Starting Village'), None)
            sx, sy = (800, 3000)
            if start_loc:
                sx, sy = start_loc.pos
            # Offset a bit so it doesn't sit exactly on top of the village icon
            sx += 160
            sy += 120
            e = entities.create_enemy(self.rng.randint(0, 1_000_000), tier=3, enemy_type='minotaur')
            e.pos = [max(50, min(WORLD_WIDTH - 50, sx)), max(50, min(WORLD_HEIGHT - 50, sy))]
            e.faction = 'monsters'
            e.enemy_type = 'minotaur'
            e.archetype = 'minotaur'
            e.stats.hp_max = 380
            e.stats.hp = 380
            e.stats.atk = 30
            e.stats.spd = 130
            e.radius = 18
            e.is_unique_monster = True
            e.is_army = False
            e.is_monster = True
            self.enemies.append(e)
        except Exception:
            pass


def init_world(seed: int) -> World:
    return World(seed, 1280, 720)


def update_world(world: World, player: entities.Entity, dt: float, relations: Optional[entities.FactionRelations] = None) -> Optional[Dict[str, Any]]:
    world.camera.update(player)

    # AI wars/peace toggles between factions (periodic)
    try:
        world._diplo_timer += dt
        if world._diplo_timer >= 30.0:
            world._diplo_timer = 0.0
            facs = [loc.faction for loc in world.locations if getattr(loc, 'faction', None) and loc.faction != 'bandits']
            facs = sorted(set(facs))
            if len(facs) >= 2:
                a = world.rng.choice(facs)
                b = world.rng.choice([f for f in facs if f != a])
                key = tuple(sorted((a, b)))
                if key in world.ai_wars:
                    world.ai_wars.remove(key)
                    print(f"[DIPLO] {a} e {b} firmaram PAZ")
                else:
                    world.ai_wars.add(key)
                    print(f"[DIPLO] {a} e {b} entraram em GUERRA")

            # Ensure bandits remain at war with all factions
            for fac in facs:
                bandit_key = tuple(sorted(('bandits', fac)))
                if bandit_key not in world.ai_wars:
                    world.ai_wars.add(bandit_key)
    except Exception:
        pass

    # AI vs AI auto-resolve in overworld: armies from warring factions that get close reduce each other's sizes
    try:
        # Throttle auto-resolve to reduce CPU
        world._auto_resolve_timer += dt
        if world._auto_resolve_timer >= 0.4:
            world._auto_resolve_timer = 0.0
            # Pre-filter armies near player to reduce iterations
            all_armies = [ee for ee in world.enemies if getattr(ee, 'is_army', False)]
            armies = [a for a in all_armies if entities.distance(a, player) <= 1400]

            checks = 0
            # Only check armies that are reasonably close to each other
            for i in range(len(armies)):
                a = armies[i]
                for j in range(i+1, len(armies)):
                    b = armies[j]
                    # Early distance check before faction checks (cheaper)
                    dist_ab = entities.distance(a, b)
                    if dist_ab >= 140:
                        continue

                    af = getattr(a, 'faction', None); bf = getattr(b, 'faction', None)
                    if not af or not bf or af == bf:
                        continue
                    if tuple(sorted((af, bf))) not in world.ai_wars:
                        continue

                    # Probabilistic casualty: chance based on opponent power (army_size and avg tier)
                    a_size = max(1, int(getattr(a, 'army_size', 1)))
                    b_size = max(1, int(getattr(b, 'army_size', 1)))
                    a_tier = max(1, min(3, int(getattr(a, 'avg_tier', getattr(a.stats, 'level', 1)))))
                    b_tier = max(1, min(3, int(getattr(b, 'avg_tier', getattr(b.stats, 'level', 1)))))
                    # Power scales: tier 1=1.0, 2=1.4, 3=1.8
                    tier_scale = {1:1.0, 2:1.4, 3:1.8}
                    power_a = a_size * tier_scale.get(a_tier, 1.0)
                    power_b = b_size * tier_scale.get(b_tier, 1.0)
                    total = power_a + power_b
                    if total <= 0:
                        continue
                    # Perform 1-2 casualty events per tick depending on total power
                    events = 1 + (1 if total > 20 else 0)
                    for _ in range(events):
                        r = world.rng.random()
                        # Probability of A losing a unit is proportional to B's power and vice-versa
                        if r < (power_b / total) and a_size > 0:
                            a_size -= 1
                        elif b_size > 0:
                            b_size -= 1
                    a.army_size = a_size
                    b.army_size = b_size
                    checks += 1
                    if checks > 60:
                        break
                if checks > 60:
                    break
            # Remove eliminated armies
            world.enemies = [ee for ee in world.enemies if not (getattr(ee, 'is_army', False) and getattr(ee, 'army_size', 0) <= 0)]
    except Exception:
        pass

    for e in list(world.enemies):
        # Initialize AI state
        if not hasattr(e, 'patrol_timer'):
            e.patrol_timer = 0
            e.patrol_target = None
            e.ai_state = "PATROLLING"  # PATROLLING or CHASING
            e.chase_alert_cooldown = 0

        dist_to_player = entities.distance(e, player)

        # LOD activation: only simulate enemies near the player (hysteresis)
        if not hasattr(e, '_active'):
            e._active = dist_to_player < 1500
        if e._active and dist_to_player > 1700:
            e._active = False
        elif (not e._active) and dist_to_player < 1500:
            e._active = True
        if not e._active:
            # Keep tiny cooldowns ticking down
            if hasattr(e, 'chase_alert_cooldown') and e.chase_alert_cooldown > 0:
                e.chase_alert_cooldown = max(0.0, e.chase_alert_cooldown - dt)
            # Light drift can be added if desired; for now, just clamp bounds
            e.pos[0] = max(e.radius, min(WORLD_WIDTH - e.radius, e.pos[0]))
            e.pos[1] = max(e.radius, min(WORLD_HEIGHT - e.radius, e.pos[1]))
            continue

        # STATE MACHINE: PATROLLING → CHASING
        if e.ai_state == "PATROLLING":
            # Get faction for this entity (needed for both player detection and bandit AI)
            fac_id = getattr(e, 'faction', 'bandits')

            # Detect player within 300 units
            if dist_to_player < 300:
                # Only aggressive if faction is at war with player (relation <= -30) or bandits
                rel_val = 0
                try:
                    if relations and hasattr(relations, 'relations'):
                        rel_val = relations.relations.get(fac_id, 0)
                except Exception:
                    rel_val = 0
                if fac_id in ('bandits', 'monsters') or rel_val <= -30:
                    e.ai_state = "CHASING"
                    e.chase_alert_cooldown = 2.0  # Can alert nearby enemies
                    # Alert nearby enemies to also chase (pack behavior)
                    for ally in world.enemies:
                        if ally.id != e.id and entities.distance(ally, e) < 200:
                            if hasattr(ally, 'ai_state'):
                                ally.ai_state = "CHASING"
                else:
                    # Neutral/allied: ignore player
                    pass

            # Random patrol behavior
            e.patrol_timer -= dt

            # BANDIT AGGRESSION: Hunt nearby enemy patrols
            hunt_target = None
            if fac_id == 'bandits':
                # Search for nearby enemy armies to hunt
                for other in world.enemies:
                    if not getattr(other, 'is_army', False):
                        continue
                    other_fac = getattr(other, 'faction', None)
                    if not other_fac or other_fac == 'bandits':
                        continue
                    # Check if at war (should always be true for bandits)
                    if tuple(sorted((fac_id, other_fac))) in world.ai_wars:
                        dist_to_other = entities.distance(e, other)
                        if dist_to_other < 300:  # Hunt range
                            hunt_target = other
                            break

            if hunt_target:
                # Move toward enemy patrol
                dx = hunt_target.pos[0] - e.pos[0]
                dy = hunt_target.pos[1] - e.pos[1]
                dist = math.hypot(dx, dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                    speed = e.stats.spd * 0.5  # Faster when hunting
                    if world.in_forest(e.pos):
                        speed *= 0.8
                    nx = e.pos[0] + dx * speed * dt
                    ny = e.pos[1] + dy * speed * dt
                    if not world.in_mountain((nx, e.pos[1])):
                        e.pos[0] = nx
                    if not world.in_mountain((e.pos[0], ny)):
                        e.pos[1] = ny
            else:
                # Regular random patrol
                if e.patrol_timer <= 0:
                    e.patrol_timer = world.rng.uniform(2.0, 4.0)
                    angle = world.rng.uniform(0, math.tau)
                    e.patrol_target = (math.cos(angle), math.sin(angle))

                if e.patrol_target:
                    speed = e.stats.spd * 0.4
                    # Forest slow
                    if world.in_forest(e.pos):
                        speed *= 0.8
                    dx = e.patrol_target[0] * speed * dt
                    dy = e.patrol_target[1] * speed * dt
                    nx = e.pos[0] + dx
                    ny = e.pos[1] + dy
                    # Block mountains
                    if not world.in_mountain((nx, e.pos[1])):
                        e.pos[0] = nx
                    if not world.in_mountain((e.pos[0], ny)):
                        e.pos[1] = ny

        elif e.ai_state == "CHASING":
            # Stop chasing if player gets too far (450 units)
            if dist_to_player > 450:
                e.ai_state = "PATROLLING"
                e.patrol_timer = 0  # Reset patrol immediately
            else:
                # Chase player at 1.2x speed
                dx = player.pos[0] - e.pos[0]
                dy = player.pos[1] - e.pos[1]
                dist = math.hypot(dx, dy)
                if dist > 0:
                    dx /= dist
                    dy /= dist
                    speed = e.stats.spd * 0.55
                    if world.in_forest(e.pos):
                        speed *= 0.85
                    nx = e.pos[0] + dx * speed * dt
                    ny = e.pos[1] + dy * speed * dt
                    if not world.in_mountain((nx, e.pos[1])):
                        e.pos[0] = nx
                    if not world.in_mountain((e.pos[0], ny)):
                        e.pos[1] = ny

            # Alert nearby enemies (cooldown to prevent spam)
            if getattr(e, 'chase_alert_cooldown', 0.0) > 0.0:
                e.chase_alert_cooldown = max(0.0, e.chase_alert_cooldown - dt)

        # Clamp to world bounds
        e.pos[0] = max(e.radius, min(WORLD_WIDTH - e.radius, e.pos[0]))
        e.pos[1] = max(e.radius, min(WORLD_HEIGHT - e.radius, e.pos[1]))

        # Collision with player triggers encounter if faction is hostile
        if dist_to_player <= (e.radius + player.radius + 5):
            fac_id = getattr(e, 'faction', 'bandits')
            rel_val = 0
            try:
                if relations and hasattr(relations, 'relations'):
                    rel_val = relations.relations.get(fac_id, 0)
            except Exception:
                rel_val = 0
            if fac_id not in ('bandits', 'monsters') and rel_val > -30:
                # Neutral/allied do not engage; skip encounter
                continue
            # If this is an army marker, expand into multiple soldiers (enemy team)
            enemies_in_encounter: list[entities.Entity] = []
            fac = getattr(e, 'faction', 'bandits')
            if getattr(e, 'is_army', False):
                count = max(1, min(10, int(getattr(e, 'army_size', 1))))
                for _ in range(count):
                    tier = max(1, getattr(e.stats, 'level', 1))
                    etype = factions.roll_enemy_type(fac) or None
                    ne = entities.create_enemy(world.rng.randint(0, 1_000_000), tier=tier, enemy_type=etype)
                    ne.faction = fac
                    # NOTE: Don't set team here - it's set in battle.py based on encounter dict keys
                    ang = world.rng.uniform(0, math.tau)
                    rad = world.rng.uniform(8, 45)
                    ne.pos = [player.pos[0] + math.cos(ang) * rad, player.pos[1] + math.sin(ang) * rad]
                    enemies_in_encounter.append(ne)
                # remove army marker from world
                if e in world.enemies:
                    world.enemies.remove(e)
            else:
                nearby = [ee for ee in world.enemies if entities.distance(ee, player) < 250 and ee.id != e.id][:4]
                enemies_in_encounter = [e] + nearby
            print(f"[WORLD DEBUG] Collision detected! Creating encounter with {len(enemies_in_encounter)} enemies")
            for ee in enemies_in_encounter:
                if ee in world.enemies:
                    world.enemies.remove(ee)
                    print(f"  Removed enemy {ee.id} from world")
            fac = getattr(e, 'faction', 'bandits')
            # Allies assist: collect friendly/allied entities nearby and add as ally troops
            ally_troops: list[entities.Entity] = []
            for ally in list(world.enemies):
                try:
                    af = getattr(ally, 'faction', None)
                    if af and relations and hasattr(relations, 'relations'):
                        if relations.relations.get(af, 0) > 30 and entities.distance(ally, player) < 320:
                            ally_troops.append(ally)
                            world.enemies.remove(ally)
                except Exception:
                    pass
            # Build side B from nearby armies at war with fac
            enemies_side_b: list[entities.Entity] = []
            try:
                for opp in list(world.enemies):
                    of = getattr(opp, 'faction', None)
                    if of and of != fac and tuple(sorted((fac, of))) in world.ai_wars and entities.distance(opp, player) < 380:
                        # Expand opp army into soldiers
                        if getattr(opp, 'is_army', False):
                            count_b = max(1, min(10, int(getattr(opp, 'army_size', 1))))
                            for _ in range(count_b):
                                tier = max(1, getattr(opp.stats, 'level', 1))
                                etype = factions.roll_enemy_type(of) or None
                                nb = entities.create_enemy(world.rng.randint(0, 1_000_000), tier=tier, enemy_type=etype)
                                nb.faction = of
                                # NOTE: Don't set team here - it's set in battle.py based on encounter dict keys
                                ang = world.rng.uniform(0, math.tau)
                                rad = world.rng.uniform(8, 45)
                                nb.pos = [player.pos[0] + math.cos(ang) * rad, player.pos[1] + math.sin(ang) * rad]
                                enemies_side_b.append(nb)
                            world.enemies.remove(opp)
            except Exception:
                pass

            print(f"[WORLD DEBUG] Encounter dict: enemies={len(enemies_in_encounter)} vs {len(enemies_side_b)}, faction={fac}")
            return {"enemies": enemies_in_encounter, "enemies_b": enemies_side_b, "ally_troops": ally_troops, "rng_seed": world.rng.randint(0, 1_000_000), "faction": fac}

    # Respawn enemies if count is low
    if len(world.enemies) < 15:
        world._spawn_enemy()

    # Periodically spawn patrols from each faction castle
    world._patrol_timer += dt
    if world._patrol_timer >= 6.0:
        world._patrol_timer = 0.0
        # Include both castles and bandit camps for spawning patrols
        spawn_locations = [loc for loc in world.locations if loc.location_type in ("castle", "bandit_camp")]
        for c in spawn_locations:
            # Bandits have smaller cap (more agile, smaller groups)
            cap = 3 if c.location_type == "bandit_camp" else world._patrol_cap_per_faction

            # Count nearby enemies belonging to this faction around the location
            nearby = 0
            global_armies = 0
            for e in world.enemies:
                if getattr(e, 'is_army', False):
                    global_armies += 1
                if getattr(e, 'faction', None) == c.faction and entities.distance(e, c) < 600 and getattr(e, 'is_army', False):
                    nearby += 1
            if nearby < cap and global_armies < getattr(world, '_global_army_cap', 120):
                # Spawn a single army marker per tick until cap
                try:
                    world._spawn_army_from_castle(c)
                except Exception:
                    world._spawn_patrol_from_castle(c)

    return None


def render_world(screen: pygame.Surface, world: World, player: entities.Entity, troops: list[entities.Entity], relations: entities.FactionRelations | None = None):
    # Tile the procedural grass texture
    for y in range(0, screen.get_height(), vfx.GRASS_TEXTURE.get_height()):
        for x in range(0, screen.get_width(), vfx.GRASS_TEXTURE.get_width()):
            screen.blit(vfx.GRASS_TEXTURE, (x, y))

    # Subtle ground texture chunks (stones/tufts), shift by camera
    if hasattr(world, 'ground_chunks'):
        for rect, gs in world.ground_chunks:
            sx, sy = world.camera.world_to_screen((rect.x, rect.y))
            if sx < screen.get_width() and sy < screen.get_height() and (sx + gs.get_width()) > 0 and (sy + gs.get_height()) > 0:
                screen.blit(gs, (sx, sy))

    # Draw terrain first
    def draw_alpha_rect(color_rgba: tuple[int,int,int,int], rect: pygame.Rect):
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        surf.fill(color_rgba)
        tl = world.camera.world_to_screen((rect.x, rect.y))
        screen.blit(surf, (tl[0], tl[1]))

    # Mountains (dark, strong alpha)
    if hasattr(world, '_patch_cache') and world._patch_cache.get('mountain'):
        for r, surf in world._patch_cache['mountain']:
            tl = world.camera.world_to_screen((r.x, r.y))
            screen.blit(surf, (tl[0], tl[1]))
    else:
        for r in world.terrain_mountains:
            draw_alpha_rect((70, 70, 75, 200), r)

    # Forests
    if hasattr(world, '_patch_cache') and world._patch_cache.get('forest'):
        for r, surf in world._patch_cache['forest']:
            tl = world.camera.world_to_screen((r.x, r.y))
            screen.blit(surf, (tl[0], tl[1]))
    else:
        for r in world.terrain_forests:
            draw_alpha_rect((30, 120, 60, 120), r)

    # Desert
    if hasattr(world, '_patch_cache') and world._patch_cache.get('desert'):
        for r, surf in world._patch_cache['desert']:
            tl = world.camera.world_to_screen((r.x, r.y))
            screen.blit(surf, (tl[0], tl[1]))
    else:
        for r in world.terrain_desert:
            draw_alpha_rect((220, 190, 90, 130), r)

    # Swamp
    if hasattr(world, '_patch_cache') and world._patch_cache.get('swamp'):
        for r, surf in world._patch_cache['swamp']:
            tl = world.camera.world_to_screen((r.x, r.y))
            screen.blit(surf, (tl[0], tl[1]))
    else:
        for r in world.terrain_swamp:
            draw_alpha_rect((25, 80, 60, 150), r)
    # Rivers (strong blue overlay)
    for r in world.terrain_rivers:
        draw_alpha_rect((40, 120, 200, 180), r)

    # Draw roads
    if getattr(world, 'roads', None):
        for poly in world.roads:
            # draw thick center line by connecting segments
            for i in range(1, len(poly)):
                a = world.camera.world_to_screen(poly[i-1])
                b = world.camera.world_to_screen(poly[i])
                pygame.draw.line(screen, (95, 70, 50), a, b, max(8, world.road_width))
                pygame.draw.line(screen, (80, 60, 40), a, b, max(6, world.road_width - 3))

    # Draw locations
    from .resource_manager import get_font
    font_loc = get_font(22)
    from . import world_sprites
    for loc in world.locations:
        if world.camera.is_visible(loc.pos):
            pos = world.camera.world_to_screen(loc.pos)
            # Try sprite-first; fallback to old icon if not available
            drawn = world_sprites.draw_location_sprite(screen, loc, pos, relations)
            if not drawn:
                vfx.render_location_icon(screen, loc.location_type, pos)
            
            name_surf = font_loc.render(loc.name, True, (240, 240, 240))
            name_rect = name_surf.get_rect(center=(pos[0], pos[1] - 25))
            pygame.draw.rect(screen, (0,0,0,150), name_rect.inflate(10,4))
            screen.blit(name_surf, name_rect)

            # Faction banner for castles
            if loc.location_type == "castle":
                try:
                    fac = factions.get_faction(loc.faction)
                    if fac and "palette" in fac:
                        col = fac["palette"].get("primary", (150,150,150))
                        # Small banner rectangle above the name
                        banner = pygame.Rect(pos[0]-10, pos[1]-40, 20, 6)
                        pygame.draw.rect(screen, col, banner)
                        # Optional icon/letters
                        icon_text = fac.get("icon", "")
                        if icon_text:
                            icon_font = get_font(16)
                            icon_surf = icon_font.render(str(icon_text), True, (240,240,240))
                            screen.blit(icon_surf, (pos[0]-icon_surf.get_width()//2, pos[1]-56))
                except Exception:
                    pass

    # Draw enemies
    mouse_pos = pygame.mouse.get_pos()
    for e in world.enemies:
        if world.camera.is_visible(e.pos):
            pos = world.camera.world_to_screen(e.pos)
            vfx.draw_entity_shadow(screen, pos, e.radius)

            # Choose color by faction palette if available
            base_color = (220, 80, 80)
            try:
                fac_id = getattr(e, 'faction', None)
                if fac_id:
                    fac = factions.get_faction(fac_id)
                    if fac and "palette" in fac:
                        base_color = fac["palette"].get("primary", base_color)
            except Exception:
                pass

            # Show different color when chasing (lighter ring)
            if hasattr(e, 'ai_state') and e.ai_state == "CHASING":
                pygame.draw.circle(screen, (min(base_color[0]+40,255), min(base_color[1]+40,255), min(base_color[2]+40,255)), pos, int(e.radius)+2, 2)
            pygame.draw.circle(screen, base_color, pos, int(e.radius))
            # If this is an army marker, draw the size
            if getattr(e, 'is_army', False):
                try:
                    font_army = get_font(18)
                    num = int(getattr(e, 'army_size', 1))
                    num_surf = font_army.render(str(num), True, (255,255,255))
                    screen.blit(num_surf, (pos[0] - num_surf.get_width()//2, pos[1] - int(e.radius) - 12))
                except Exception:
                    pass
                pygame.draw.circle(screen, (255, 200, 0), pos, int(e.radius) + 3, 2)
                # Tooltip on hover: Faction + Size
                try:
                    dx = mouse_pos[0] - pos[0]
                    dy = mouse_pos[1] - pos[1]
                    if (dx*dx + dy*dy) <= (max(12, int(e.radius) + 6) ** 2):
                        fac = getattr(e, 'faction', '') or ''
                        fac_name = fac
                        try:
                            fobj = factions.get_faction(fac)
                            if fobj:
                                fac_name = fobj.get('name', fac)
                        except Exception:
                            pass
                        tip = f"{fac_name} — {int(getattr(e,'army_size',1))}"
                        tip_font = get_font(18)
                        ts = tip_font.render(tip, True, (255,255,255))
                        bg = pygame.Surface((ts.get_width()+8, ts.get_height()+6), pygame.SRCALPHA)
                        bg.fill((10,10,10,200))
                        screen.blit(bg, (pos[0]+12, pos[1]-ts.get_height()-18))
                        screen.blit(ts, (pos[0]+16, pos[1]-ts.get_height()-16))
                except Exception:
                    pass
            else:
                pygame.draw.circle(screen, base_color, pos, int(e.radius))

    # Draw troops (DISABLED - Mount & Blade style: troops only visible in battle)
    # for t in troops:
    #     if world.camera.is_visible(t.pos):
    #         pos = world.camera.world_to_screen(t.pos)
    #         vfx.draw_entity_shadow(screen, pos, t.radius * 0.8)
    #         pygame.draw.circle(screen, (100, 150, 255), pos, int(t.radius * 0.8))

    # Draw player
    player_pos_screen = world.camera.world_to_screen(player.pos)

    # Fog of War overlay (after drawing world, before UI)
    # Sem Fog of War
    vfx.draw_entity_shadow(screen, player_pos_screen, player.radius)
    
    pygame.draw.circle(screen, (80, 220, 140), player_pos_screen, int(player.radius))


def render_minimap(screen: pygame.Surface, world: World, player: entities.Entity, troops: list[entities.Entity]):
    map_w, map_h = 180, 180
    map_x, map_y = screen.get_width() - map_w - 20, 20
    
    # Background
    pygame.draw.rect(screen, (0, 0, 0, 180), (map_x, map_y, map_w, map_h))
    pygame.draw.rect(screen, (100, 150, 200), (map_x, map_y, map_w, map_h), 1)

    def world_to_map(pos):
        x = int((pos[0] / WORLD_WIDTH) * map_w)
        y = int((pos[1] / WORLD_HEIGHT) * map_h)
        return map_x + x, map_y + y

    # Draw locations
    for loc in world.locations:
        pos = world_to_map(loc.pos)
        color = {"town": (100, 150, 255), "castle": (150, 150, 150), "bandit_camp": (200, 80, 80)}.get(loc.location_type, (255,255,255))
        # Override castle color by faction palette if available
        if loc.location_type == "castle":
            try:
                fac = factions.get_faction(loc.faction)
                if fac and "palette" in fac:
                    color = fac["palette"].get("primary", color)
            except Exception:
                pass
        pygame.draw.circle(screen, color, pos, 3)

    # Draw terrain overlays on minimap
    def rect_to_map(r: pygame.Rect):
        x = int((r.x / WORLD_WIDTH) * map_w)
        y = int((r.y / WORLD_HEIGHT) * map_h)
        w = max(1, int((r.width / WORLD_WIDTH) * map_w))
        h = max(1, int((r.height / WORLD_HEIGHT) * map_h))
        return (map_x + x, map_y + y, w, h)

    for r in world.terrain_mountains:
        pygame.draw.rect(screen, (120, 120, 120), rect_to_map(r))
    for r in world.terrain_forests:
        pygame.draw.rect(screen, (20, 80, 40), rect_to_map(r))

    # Roads on minimap
    if getattr(world, 'roads', None):
        def w2m(p):
            x = int((p[0] / WORLD_WIDTH) * map_w)
            y = int((p[1] / WORLD_HEIGHT) * map_h)
            return (map_x + x, map_y + y)
        for poly in world.roads:
            for i in range(1, len(poly)):
                pygame.draw.line(screen, (120, 100, 80), w2m(poly[i-1]), w2m(poly[i]), 2)

    # Draw enemies
    for e in world.enemies:
        pos = world_to_map(e.pos)
        color = (220, 80, 80)
        try:
            fac_id = getattr(e, 'faction', None)
            if fac_id:
                fac = factions.get_faction(fac_id)
                if fac and "palette" in fac:
                    color = fac["palette"].get("primary", color)
        except Exception:
            pass
        pygame.draw.circle(screen, color, pos, 1)
        # Army size label on minimap
        if getattr(e, 'is_army', False):
            try:
                font_mm = get_font(14)
                num = int(getattr(e, 'army_size', 1))
                surf = font_mm.render(str(num), True, (255, 255, 255))
                screen.blit(surf, (pos[0] + 2, pos[1] - 6))
            except Exception:
                pass

    # Draw troops (DISABLED - Mount & Blade style: troops only visible in battle)
    # for t in troops:
    #     pos = world_to_map(t.pos)
    #     pygame.draw.circle(screen, (100, 150, 255), pos, 1)

    # Draw player
    player_pos_screen = world.camera.world_to_screen(player.pos)
    pygame.draw.circle(screen, (80, 220, 140), player_pos_screen, 6)


def render_world_map(screen: pygame.Surface, world: World, player: entities.Entity):
    """Overlay world map showing only discovered towns and player position."""
    sw, sh = screen.get_width(), screen.get_height()
    # Dark overlay
    bg = pygame.Surface((sw, sh), pygame.SRCALPHA)
    bg.fill((10, 10, 18, 230))
    screen.blit(bg, (0, 0))

    margin = 60
    map_w = sw - margin * 2
    map_h = sh - margin * 2
    pygame.draw.rect(screen, (90, 90, 120), (margin-2, margin-2, map_w+4, map_h+4), 2)

    def w2m(p):
        x = margin + int((p[0] / WORLD_WIDTH) * map_w)
        y = margin + int((p[1] / WORLD_HEIGHT) * map_h)
        return x, y

    # Discovered towns
    from .resource_manager import get_font as _get_font
    font = _get_font(20)
    for loc in world.locations:
        if loc.location_type != 'town':
            continue
        name = getattr(loc, 'name', '')
        if hasattr(world, 'visited_locations') and name not in world.visited_locations:
            continue
        pos = w2m(loc.pos)
        pygame.draw.circle(screen, (120, 170, 255), pos, 4)
        name_surf = font.render(name, True, (220, 220, 240))
        screen.blit(name_surf, (pos[0] + 6, pos[1] - 6))

    # Discovered castles (colored by faction)
    for loc in world.locations:
        if loc.location_type != 'castle':
            continue
        name = getattr(loc, 'name', '')
        if hasattr(world, 'visited_locations') and name not in world.visited_locations:
            continue
        pos = w2m(loc.pos)
        # Color by faction palette primary
        col = (180, 180, 180)
        try:
            fac = factions.get_faction(getattr(loc, 'faction', None))
            if fac and 'palette' in fac:
                col = fac['palette'].get('primary', col)
        except Exception:
            pass
        pygame.draw.circle(screen, col, pos, 5)
        name_surf = font.render(name, True, (230, 230, 230))
        screen.blit(name_surf, (pos[0] + 6, pos[1] - 6))

    # Player marker
    ppos = w2m(player.pos)
    pygame.draw.circle(screen, (80, 255, 160), ppos, 6)
    pygame.draw.circle(screen, (255, 255, 255), ppos, 8, 1)

    # Hint
    hint_font = _get_font(18)
    hint = hint_font.render("M: Close Map", True, (200, 200, 200))
    screen.blit(hint, (sw - hint.get_width() - 20, sh - hint.get_height() - 20))
