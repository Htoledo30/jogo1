"""Save and load system for the game.

Saves game state to JSON file with validation, backup, and versioning.

Features:
- Automatic backup before overwriting saves
- Save file validation and corruption detection
- Schema versioning and migration
- Detailed error logging
"""

import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from . import entities
from . import equipment as equip_mod
from . import items
from . import factions
from .constants import SAVE_FILE_PATH
from .logger import get_logger

logger = get_logger(__name__)

# Save system configuration
CURRENT_SAVE_VERSION = "1.3"  # Updated for attribute system
BACKUP_DIR = Path("saves/backups")
MAX_BACKUPS = 5  # Keep last 5 backups


def _create_backup() -> bool:
    """Create backup of current save file before overwriting.

    Returns:
        True if backup created successfully
    """
    if not os.path.exists(SAVE_FILE_PATH):
        return True  # No existing save to backup

    try:
        # Create backup directory
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"savegame_{timestamp}.json"

        # Copy current save to backup
        shutil.copy2(SAVE_FILE_PATH, backup_path)

        logger.info(f"Created save backup: {backup_path.name}")

        # Cleanup old backups (keep only MAX_BACKUPS)
        _cleanup_old_backups()

        return True

    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        return False


def _cleanup_old_backups() -> None:
    """Remove old backup files, keeping only the most recent MAX_BACKUPS."""
    try:
        if not BACKUP_DIR.exists():
            return

        # Get all backup files sorted by modification time
        backups = sorted(
            BACKUP_DIR.glob("savegame_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove old backups
        for old_backup in backups[MAX_BACKUPS:]:
            old_backup.unlink()
            logger.debug(f"Removed old backup: {old_backup.name}")

    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")


def _validate_save_data(save_data: dict) -> bool:
    """Validate save data structure.

    Args:
        save_data: Save data dictionary

    Returns:
        True if valid, False otherwise
    """
    required_keys = ["version", "player", "troops", "relations"]

    # Check required top-level keys
    for key in required_keys:
        if key not in save_data:
            logger.error(f"Invalid save: missing required key '{key}'")
            return False

    # Check player data structure
    player_data = save_data.get("player", {})
    if not isinstance(player_data.get("stats"), dict):
        logger.error("Invalid save: player stats missing or invalid")
        return False

    if not isinstance(player_data.get("equipment"), dict):
        logger.error("Invalid save: player equipment missing or invalid")
        return False

    # Check troops is list
    if not isinstance(save_data.get("troops"), list):
        logger.error("Invalid save: troops not a list")
        return False

    # Check relations is dict
    if not isinstance(save_data.get("relations"), dict):
        logger.error("Invalid save: relations not a dict")
        return False

    logger.debug("Save data validation passed")
    return True


def save_game(player: entities.Entity, player_troops: list, player_relations: entities.FactionRelations,
              world, current_location, game_time: float) -> bool:
    """Save the current game state to a JSON file with automatic backup.

    Args:
        player: Player entity
        player_troops: List of player's troops
        player_relations: Faction relations object
        world: World object
        current_location: Current location (or None)
        game_time: Total game time in seconds

    Returns:
        True if save successful, False otherwise
    """
    logger.info("Saving game...")

    # Create backup before saving
    if not _create_backup():
        logger.warning("Continuing save despite backup failure")

    try:
        save_data = {
            "version": CURRENT_SAVE_VERSION,
            "game_time": game_time,
            "save_timestamp": datetime.now().isoformat(),

            # Player data
            "player": {
                "position": player.pos,
                "stats": {
                    # Core
                    "hp_max": player.stats.hp_max,
                    "hp": player.stats.hp,
                    "atk": player.stats.atk,
                    "spd": player.stats.spd,
                    "level": player.stats.level,
                    "xp": player.stats.xp,
                    "xp_to_next_level": player.stats.xp_to_next_level,
                    "food": player.stats.food,
                    "gold": player.stats.gold,
                    # Primary attributes
                    "strength": getattr(player.stats, "strength", 10),
                    "agility": getattr(player.stats, "agility", 10),
                    "vitality": getattr(player.stats, "vitality", 10),
                    "charisma": getattr(player.stats, "charisma", 10),
                    "skill": getattr(player.stats, "skill", 10),
                    "attribute_points": getattr(player.stats, "attribute_points", 0),
                    # Derived attributes
                    "stamina_max": getattr(player.stats, "stamina_max", 100.0),
                    "crit_chance": getattr(player.stats, "crit_chance", 0.05),
                    "crit_damage": getattr(player.stats, "crit_damage", 2.0),
                    "block_power": getattr(player.stats, "block_power", 0.30),
                    "gold_bonus": getattr(player.stats, "gold_bonus", 1.0),
                    "troop_bonus": getattr(player.stats, "troop_bonus", 0.0),
                    "defense": getattr(player.stats, "defense", 0.0),
                    "parry_window": getattr(player.stats, "parry_window", 0.2),
                    "attack_speed_bonus": getattr(player.stats, "attack_speed_bonus", 0.0),
                    "stamina_regen_bonus": getattr(player.stats, "stamina_regen_bonus", 0.0),
                    "shop_discount": getattr(player.stats, "shop_discount", 0.0),
                },
                "equipment": {
                    "weapon": player.equipment.weapon,
                    "helmet": player.equipment.helmet,
                    "chest": player.equipment.chest,
                    "legs": player.equipment.legs,
                    "boots": player.equipment.boots,
                },
                "inventory": [
                    (item.to_dict() if hasattr(item, 'to_dict') else None)
                    for item in player.inventory
                ],
            },

            # Troops data
            "troops": [
                {
                    "id": troop.id,
                    "type": getattr(troop, 'troop_type', 'warrior'),
                    "position": troop.pos,
                    "stats": {
                        "hp_max": troop.stats.hp_max,
                        "hp": troop.stats.hp,
                        "atk": troop.stats.atk,
                        "spd": troop.stats.spd,
                        "level": troop.stats.level,
                        "xp": troop.stats.xp,
                        "xp_to_next_level": troop.stats.xp_to_next_level,
                    }
                }
                for troop in player_troops
            ],

            # World data
            "world": {
                "seed": world.seed,
                "defeated_enemies": len([e for e in world.enemies if not e.alive()]),
            },

            # Diplomacy data
            "relations": player_relations.relations,

            # Current state
            "current_location": current_location.name if current_location else None,
        }

        # Validate save data before writing
        if not _validate_save_data(save_data):
            logger.error("Save data validation failed")
            return False

        # Ensure save directory exists
        save_path = Path(SAVE_FILE_PATH)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        with open(SAVE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Game saved successfully to {SAVE_FILE_PATH}")
        return True

    except (IOError, OSError) as e:
        logger.error(f"File I/O error saving game: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Unexpected error saving game: {e}", exc_info=True)
        return False


def _migrate_save_data(save_data: dict) -> dict:
    """Migrate older save structures to current schema.

    Handles migration from versions 1.0, 1.1 to current version.

    Args:
        save_data: Raw loaded save data

    Returns:
        Migrated save data
    """
    version = save_data.get("version", "1.0")
    logger.info(f"Migrating save from version {version} to {CURRENT_SAVE_VERSION}")

    try:
        # Migration from 1.0 or 1.1 to 1.2
        if version in ("1.0", "1.1"):
            # Fix relations structure
            rel = save_data.get("relations") or save_data.get("player", {}).get("relations")
            if rel is None:
                rel = {}

            # Fill missing factions with neutral (0)
            all_factions = set(factions.list_factions())
            all_factions.update({"greeks", "bandits", "monsters"})  # Backward compatibility

            for fid in all_factions:
                rel.setdefault(fid, 0)

            save_data["relations"] = rel

            # Add missing fields with defaults
            save_data.setdefault("save_timestamp", datetime.now().isoformat())

        # Migration from 1.0, 1.1, 1.2 to 1.3 (Attribute System)
        if version in ("1.0", "1.1", "1.2"):
            player_stats = save_data.get("player", {}).get("stats", {})

            # Add attribute system if not present
            if "strength" not in player_stats:
                logger.info("Migrating save to attribute system (v1.3)")

                level = player_stats.get("level", 1)
                base_attr = 10

                # Calculate total points earned from leveling
                # Each level gives 1 point, so (level-1) * 1 total points
                total_points = (level - 1) * 1

                # Distribute evenly across 5 attributes (balanced build)
                points_per_attr = total_points // 5
                remainder = total_points % 5

                # Set primary attributes
                player_stats["strength"] = base_attr + points_per_attr + (1 if remainder > 0 else 0)
                player_stats["agility"] = base_attr + points_per_attr + (1 if remainder > 1 else 0)
                player_stats["vitality"] = base_attr + points_per_attr + (1 if remainder > 2 else 0)
                player_stats["charisma"] = base_attr + points_per_attr + (1 if remainder > 3 else 0)
                player_stats["skill"] = base_attr + points_per_attr
                player_stats["attribute_points"] = 0  # No pending points

                # Set derived stats (will be recalculated on load)
                player_stats["stamina_max"] = 100.0
                player_stats["crit_chance"] = 0.05
                player_stats["crit_damage"] = 2.0
                player_stats["block_power"] = 0.30
                player_stats["gold_bonus"] = 1.0
                player_stats["troop_bonus"] = 0.0
                player_stats["defense"] = 0.0
                player_stats["parry_window"] = 0.2
                player_stats["attack_speed_bonus"] = 0.0
                player_stats["stamina_regen_bonus"] = 0.0
                player_stats["shop_discount"] = 0.0

                logger.info(f"Migrated level {level} save to balanced attribute build")
                logger.debug(f"Attributes: STR={player_stats['strength']}, AGI={player_stats['agility']}, "
                           f"VIT={player_stats['vitality']}, CHA={player_stats['charisma']}, SKL={player_stats['skill']}")

        # Update version to current
        save_data["version"] = CURRENT_SAVE_VERSION
        logger.debug(f"Migration successful to version {CURRENT_SAVE_VERSION}")

    except Exception as e:
        logger.warning(f"Migration encountered issues: {e}, using best-effort")
        save_data.setdefault("version", CURRENT_SAVE_VERSION)

    return save_data


def load_game() -> Optional[dict]:
    """Load game state from JSON file with validation.

    Returns:
        Dictionary with game state, or None if load failed
    """
    logger.info(f"Loading game from {SAVE_FILE_PATH}...")

    try:
        if not os.path.exists(SAVE_FILE_PATH):
            logger.info("No save file found")
            return None

        # Load JSON
        with open(SAVE_FILE_PATH, 'r', encoding='utf-8') as f:
            save_data = json.load(f)

        logger.debug(f"Loaded save version: {save_data.get('version', 'unknown')}")

        # Migrate to current schema
        save_data = _migrate_save_data(save_data)

        # Validate migrated data
        if not _validate_save_data(save_data):
            logger.error("Save file validation failed after migration")
            return None

        logger.info("Game loaded successfully")
        return save_data

    except json.JSONDecodeError as e:
        logger.error(f"Save file corrupted (invalid JSON): {e}", exc_info=True)
        return None
    except (IOError, OSError) as e:
        logger.error(f"File I/O error loading game: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading game: {e}", exc_info=True)
        return None


def save_exists() -> bool:
    """Check if a save file exists.

    Returns:
        True if save file exists, False otherwise
    """
    return os.path.exists(SAVE_FILE_PATH)


def apply_save_data(save_data: dict, player: entities.Entity, world) -> tuple:
    """Apply loaded save data to game objects with error handling.

    Args:
        save_data: Loaded save data dictionary
        player: Player entity to update
        world: World object to update

    Returns:
        Tuple of (player_troops, player_relations, current_location_name)

    Raises:
        ValueError: If save data is invalid or missing critical fields
    """
    logger.info("Applying save data to game objects...")

    try:
        # Restore player stats
        player_data = save_data["player"]
        stats_data = player_data["stats"]

        player.pos = player_data["position"]
        player.stats.hp_max = stats_data["hp_max"]
        player.stats.hp = stats_data["hp"]
        player.stats.atk = stats_data["atk"]
        player.stats.spd = stats_data["spd"]
        player.stats.level = stats_data["level"]
        player.stats.xp = stats_data["xp"]
        player.stats.xp_to_next_level = stats_data["xp_to_next_level"]
        player.stats.food = stats_data["food"]
        player.stats.gold = stats_data["gold"]

        # Restore primary attributes (if present)
        for k in ("strength", "agility", "vitality", "charisma", "skill", "attribute_points"):
            if k in stats_data:
                setattr(player.stats, k, stats_data[k])

        # Restore derived stats (optional; will be recalculated)
        for k in (
            "stamina_max", "crit_chance", "crit_damage", "block_power", "gold_bonus",
            "troop_bonus", "defense", "parry_window", "attack_speed_bonus",
            "stamina_regen_bonus", "shop_discount",
        ):
            if k in stats_data:
                setattr(player.stats, k, stats_data[k])

        # Ensure derived stats are consistent after attribute restore
        try:
            from .attributes import calculate_derived_stats
            calculate_derived_stats(player)
        except Exception:
            pass

        logger.debug(f"Restored player: Level {player.stats.level}, HP {player.stats.hp}/{player.stats.hp_max}")

        # Restore equipment
        equip_data = player_data["equipment"]
        player.equipment = equip_mod.Equipment(
            weapon=equip_data["weapon"],
            helmet=equip_data["helmet"],
            chest=equip_data["chest"],
            legs=equip_data["legs"],
            boots=equip_data["boots"],
        )

        # Restore inventory with error handling
        inv_list = player_data.get("inventory", [])
        player.inventory = []
        failed_items = 0

        for entry in inv_list:
            if isinstance(entry, dict):
                try:
                    it = items.Item.from_dict(entry)
                    player.inventory.append(it)
                except Exception as e:
                    logger.warning(f"Failed to restore inventory item: {e}")
                    failed_items += 1
            else:
                # Backward compatibility: ignore unknown entries
                failed_items += 1

        if failed_items > 0:
            logger.warning(f"Failed to restore {failed_items} inventory items")

        logger.debug(f"Restored {len(player.inventory)} inventory items")

        # Restore troops
        player_troops = []
        for troop_data in save_data["troops"]:
            try:
                troop_stats = troop_data["stats"]
                stats = entities.Stats(
                    hp_max=troop_stats["hp_max"],
                    hp=troop_stats["hp"],
                    atk=troop_stats["atk"],
                    spd=troop_stats["spd"],
                    level=troop_stats["level"],
                    xp=troop_stats["xp"],
                    xp_to_next_level=troop_stats["xp_to_next_level"],
                )

                troop = entities.Entity(
                    ent_id=troop_data["id"],
                    kind=f"troop_{troop_data['type']}",
                    pos=tuple(troop_data["position"]),
                    radius=14.0,
                    stats=stats
                )
                troop.troop_type = troop_data["type"]
                player_troops.append(troop)
            except Exception as e:
                logger.warning(f"Failed to restore troop: {e}")

        logger.debug(f"Restored {len(player_troops)} troops")

        # Restore relations
        player_relations = entities.FactionRelations()
        player_relations.relations = save_data["relations"]

        logger.debug(f"Restored {len(player_relations.relations)} faction relations")

        # Get current location name
        current_location_name = save_data.get("current_location")

        logger.info("Save data applied successfully")
        return player_troops, player_relations, current_location_name

    except KeyError as e:
        logger.error(f"Missing required field in save data: {e}", exc_info=True)
        raise ValueError(f"Invalid save data: missing field {e}")
    except Exception as e:
        logger.error(f"Failed to apply save data: {e}", exc_info=True)
        raise
