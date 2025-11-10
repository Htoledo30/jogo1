"""Enemy sprites rendering with faction-based coloring.

Maps enemy sprites based on faction relations:
- Bandits → Yellow Units
- Hostile factions → Red Units
- Neutral factions → Black Units
- Allied factions → Blue Units
"""

from __future__ import annotations
import os
import pygame

from .sprite_manager import load_spritesheet

# Sprite scaling
ENEMY_SPRITE_HEIGHT_PER_RADIUS = 6.0
ENEMY_SPRITE_FOOT_OFFSET_PCT = 0.40

_CACHE: dict[str, pygame.Surface] = {}
_ENEMY_FACING_RIGHT: dict[int, bool] = {}
_ENEMY_LAST_POS: dict[int, tuple[float, float]] = {}
_ENEMY_LAST_FLIP_MS: dict[int, int] = {}
_ENEMY_SIGN_STREAK: dict[int, int] = {}
_ENEMY_LAST_POS: dict[int, tuple[float, float]] = {}
_FRAME_LIST_CACHE: dict[str, list[pygame.Surface]] = {}


def get_faction_color(enemy, relations) -> str:
    """Determine sprite color based on faction relations.

    Returns: "blue", "red", "yellow", or "black"
    """
    faction = getattr(enemy, 'faction', 'bandits')

    # Bandits always yellow
    if faction == 'bandits':
        return 'yellow'

    # Check relations
    if relations and hasattr(relations, 'relations'):
        try:
            rel_value = int(relations.relations.get(faction, 0))
            if rel_value > 30:
                return 'blue'  # Allied
            elif rel_value < -30:
                return 'red'   # Hostile
            else:
                return 'black'  # Neutral
        except Exception:
            pass

    # Default to red for unknown
    return 'red'


def _load_enemy_sprite(color: str, archetype: str, enemy=None) -> pygame.Surface | None:
    """Load first frame of enemy sprite from colored units."""
    key = f"enemy_{color}_{archetype}"
    if key in _CACHE:
        return _CACHE[key]

    # If this is a special monster like minotaur, use non-colored folder
    if archetype.lower() == "minotaur":
        # Use the Minotaur_2 folder as specified by the user
        # Files present: Idle.png, Walk.png, Attack.png, Hurt.png, Dead.png
        path = os.path.join("Tiny Swords (Free Pack)", "Units", "Minotaur_2", "Idle.png")
        try:
            sheet = pygame.image.load(path).convert_alpha()
            sw, sh = sheet.get_width(), sheet.get_height()
            frames = load_spritesheet(path, sh, sh) or []
            if len(frames) <= 1 and sw > 0:
                fw = max(1, sw // 8)
                frames = load_spritesheet(path, fw, sh, num_frames=8)
            sprite = frames[0] if frames else None
            _CACHE[key] = sprite
            return sprite
        except Exception:
            _CACHE[key] = None
            return None

    # Map archetypes to sprite files (colored sets)
    sprite_map = {
        "melee": "Warrior/Warrior_Idle.png",
        "warrior": "Warrior/Warrior_Idle.png",
        "ranged": "Archer/Archer_Idle.png",
        "archer": "Archer/Archer_Idle.png",
        "tank": "Lancer/Lancer_Idle.png",
        "cavalry": "Lancer/Lancer_Idle.png",
        "lancer": "Lancer/Lancer_Idle.png",
        "minotaur": "Minotaur/Minotaur_Idle.png",
        "beast": "Minotaur/Minotaur_Idle.png",
    }

    # Map colors to folder names (kept for fallback)
    color_folders = {
        "blue": "Blue Units",
        "red": "Red Units",
        "yellow": "Yellow Units",
        "black": "Black Units",
    }

    # Determine archetype robustly with enemy fields (troop_type has priority)
    a = archetype.lower()
    if enemy is not None:
        tt = str(getattr(enemy, 'troop_type', '')).lower()
        if tt:
            a = tt
        else:
            et = str(getattr(enemy, 'enemy_type', '')).lower()
            if 'minotaur' in et:
                a = 'minotaur'
            elif 'archer' in et or 'bow' in et:
                a = 'archer'
    # Visual diversification per faction/type: choose which ground unit uses Lancer vs Warrior
    sprite_key = a
    if enemy is not None and a == 'warrior':
        fac = str(getattr(enemy, 'faction', '')).lower()
        et = str(getattr(enemy, 'enemy_type', '')).lower()

        # Faction-specific overrides (only for non-bandits)
        # Format: { faction: { enemy_type: 'lancer'|'warrior' } }
        DIVERSIFY = {
            'rome': {
                'soldier': 'lancer',
                'legionary': 'warrior',
            },
            'carthage': {
                'soldier': 'lancer',
                'carthaginian': 'warrior',
            },
            'pontus': {
                'pontic_raider': 'lancer',
                'soldier': 'warrior',
            },
            'maurya': {
                'maurya_spearman': 'lancer',
                'soldier': 'warrior',
            },
            # Greeks/Macedon/Seleucid já têm phalangite/cataphract (tank → Lancer), hoplite/soldier (warrior)
        }

        if fac != 'bandits':
            choice = DIVERSIFY.get(fac, {}).get(et)
            if choice == 'lancer':
                sprite_key = 'lancer'
            elif choice == 'warrior':
                sprite_key = 'warrior'

    sprite_file = sprite_map.get(sprite_key, "Warrior/Warrior_Idle.png")
    # Freeze color set by faction to match available assets:
    # - Bandits => Yellow Units
    # - Others => Red Units
    if enemy is not None:
        fac = str(getattr(enemy, 'faction', '')).lower()
        color_folder = "Yellow Units" if fac == 'bandits' else "Red Units"
    else:
        color_folder = color_folders.get(color.lower(), "Red Units")
    path = os.path.join("Tiny Swords (Free Pack)", "Units", color_folder, sprite_file)

    try:
        sheet = pygame.image.load(path).convert_alpha()
        sw, sh = sheet.get_width(), sheet.get_height()

        # Try square frames first
        frames = load_spritesheet(path, sh, sh)

        # Fallback: assume 8 frames horizontally
        if len(frames) <= 1 and sw > 0:
            fw = max(1, sw // 8)
            frames = load_spritesheet(path, fw, sh, num_frames=8)

        # Get first frame
        sprite = frames[0] if frames else None
        _CACHE[key] = sprite
        return sprite
    except Exception:
        _CACHE[key] = None
        return None


def update_enemy_facing(enemy, prev_pos: tuple[float, float] | None) -> None:
    """Update facing with hysteresis to avoid jittery flipping."""
    eid = enemy.id
    if prev_pos is None:
        _ENEMY_FACING_RIGHT[eid] = _ENEMY_FACING_RIGHT.get(eid, True)
        _ENEMY_SIGN_STREAK[eid] = 0
        _ENEMY_LAST_FLIP_MS[eid] = _ENEMY_LAST_FLIP_MS.get(eid, 0)
        _ENEMY_LAST_POS[eid] = (float(enemy.pos[0]), float(enemy.pos[1]))
        return

    dx = float(enemy.pos[0]) - float(prev_pos[0])
    # Ignore tiny horizontal jitters
    if abs(dx) < 1.0:
        _ENEMY_SIGN_STREAK[eid] = 0
        _ENEMY_LAST_POS[eid] = (float(enemy.pos[0]), float(enemy.pos[1]))
        return

    want_right = dx > 0
    curr_right = _ENEMY_FACING_RIGHT.get(eid, True)
    # If already facing desired direction, reset streak and exit
    if want_right == curr_right:
        _ENEMY_SIGN_STREAK[eid] = 0
        _ENEMY_LAST_POS[eid] = (float(enemy.pos[0]), float(enemy.pos[1]))
        return

    # Hysteresis: require a few consecutive frames and a cooldown between flips
    _ENEMY_SIGN_STREAK[eid] = _ENEMY_SIGN_STREAK.get(eid, 0) + 1
    now = pygame.time.get_ticks()
    last_flip = _ENEMY_LAST_FLIP_MS.get(eid, 0)
    if _ENEMY_SIGN_STREAK[eid] >= 3 and (now - last_flip) >= 200:
        _ENEMY_FACING_RIGHT[eid] = want_right
        _ENEMY_SIGN_STREAK[eid] = 0
        _ENEMY_LAST_FLIP_MS[eid] = now
    _ENEMY_LAST_POS[eid] = (float(enemy.pos[0]), float(enemy.pos[1]))


def draw_enemy_sprite(enemy, screen: pygame.Surface, screen_pos: tuple[int, int], relations) -> bool:
    """Draw enemy sprite with faction-based coloring. Returns True if drawn."""
    # Determine color and archetype
    color = get_faction_color(enemy, relations)
    archetype = getattr(enemy, 'archetype', 'melee')

    # Special case: Animated Minotaur (Idle/Walk)
    if str(archetype).lower() == 'minotaur':
        def _get_frames(anim_name: str) -> list[pygame.Surface]:
            key = f"minotaur2_{anim_name}"
            if key in _FRAME_LIST_CACHE:
                return _FRAME_LIST_CACHE[key]
            path = os.path.join("Tiny Swords (Free Pack)", "Units", "Minotaur_2", f"{anim_name}.png")
            try:
                sheet = pygame.image.load(path).convert_alpha()
                sw, sh = sheet.get_width(), sheet.get_height()
                frames = load_spritesheet(path, sh, sh)
                if len(frames) <= 1 and sw > 0:
                    fw = max(1, sw // 8)
                    frames = load_spritesheet(path, fw, sh, num_frames=8)
            except Exception:
                frames = []
            _FRAME_LIST_CACHE[key] = frames
            return frames

        idle_frames = _get_frames('Idle')
        walk_frames = _get_frames('Walk')
        # simple movement detection using last pos
        prev = _ENEMY_LAST_POS.get(enemy.id)
        cur = (float(enemy.pos[0]), float(enemy.pos[1]))
        moving = False
        if prev is not None:
            dx = cur[0] - prev[0]
            dy = cur[1] - prev[1]
            moving = (abs(dx) + abs(dy)) > 0.5
        _ENEMY_LAST_POS[enemy.id] = cur

        frames = walk_frames if (moving and walk_frames) else idle_frames
        if frames:
            ms = 100 if moving else 140
            idx = (pygame.time.get_ticks() // ms) % max(1, len(frames))
            frame = frames[int(idx)]

            # Scale
            target_h = max(8, int(getattr(enemy, 'radius', 10) * ENEMY_SPRITE_HEIGHT_PER_RADIUS))
            scale = target_h / max(1, frame.get_height())
            target_w = max(8, int(frame.get_width() * scale))
            sprite_scaled = pygame.transform.smoothscale(frame, (target_w, target_h))

            # Flip according to facing
            facing_right = _ENEMY_FACING_RIGHT.get(enemy.id, True)
            if not facing_right:
                sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

            # Draw with foot offset
            x, y = screen_pos
            offset_y = int(target_h * ENEMY_SPRITE_FOOT_OFFSET_PCT)
            blit_pos = (int(x - target_w // 2), int(y - target_h + offset_y))
            screen.blit(sprite_scaled, blit_pos)
            return True

    sprite = _load_enemy_sprite(color, archetype, enemy)
    if not sprite:
        return False

    # Scale to enemy radius
    target_h = max(8, int(getattr(enemy, 'radius', 10) * ENEMY_SPRITE_HEIGHT_PER_RADIUS))
    scale = target_h / max(1, sprite.get_height())
    target_w = max(8, int(sprite.get_width() * scale))
    sprite_scaled = pygame.transform.smoothscale(sprite, (target_w, target_h))

    # Apply flip
    facing_right = _ENEMY_FACING_RIGHT.get(enemy.id, True)
    if not facing_right:
        sprite_scaled = pygame.transform.flip(sprite_scaled, True, False)

    # Draw with foot offset
    x, y = screen_pos
    offset_y = int(target_h * ENEMY_SPRITE_FOOT_OFFSET_PCT)
    blit_pos = (int(x - target_w // 2), int(y - target_h + offset_y))
    screen.blit(sprite_scaled, blit_pos)
    return True

