"""Resource Manager - Centralized asset and font caching.

Prevents redundant font/surface creation and provides single source of truth
for all game resources.
"""

import pygame
from pathlib import Path
from typing import Dict, Optional, Tuple
from src.logger import get_logger

logger = get_logger(__name__)


class ResourceManager:
    """Singleton manager for caching fonts, surfaces, and other resources."""

    _instance: Optional['ResourceManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize resource manager (only once)."""
        if self._initialized:
            return

        self._initialized = True

        # Font cache: (font_name, size) -> pygame.Font
        self._fonts: Dict[Tuple[Optional[str], int], pygame.font.Font] = {}

        # Surface cache: name -> pygame.Surface
        self._surfaces: Dict[str, pygame.Surface] = {}

        # Stats for debugging
        self._font_cache_hits = 0
        self._font_cache_misses = 0

        logger.info("Resource Manager initialized")

    def get_font(self, size: int, font_name: Optional[str] = None, bold: bool = False) -> pygame.font.Font:
        """Get cached font or create new one.

        Args:
            size: Font size in points
            font_name: Font name (None for default system font)
            bold: Whether to make font bold

        Returns:
            Cached or newly created pygame.Font
        """
        # Create cache key
        cache_key = (font_name, size, bold)

        # Check cache
        if cache_key in self._fonts:
            self._font_cache_hits += 1
            return self._fonts[cache_key]

        # Cache miss - create new font
        self._font_cache_misses += 1

        try:
            if font_name:
                font = pygame.font.Font(font_name, size)
            else:
                font = pygame.font.Font(None, size)

            if bold:
                font.set_bold(True)

            # Cache it
            self._fonts[cache_key] = font

            logger.debug(f"Created and cached font: {font_name or 'default'} size {size}")

            return font

        except Exception as e:
            logger.error(f"Failed to create font {font_name or 'default'} size {size}: {e}")
            # Fallback to default font
            fallback = pygame.font.Font(None, size)
            self._fonts[cache_key] = fallback
            return fallback

    def cache_surface(self, name: str, surface: pygame.Surface) -> None:
        """Cache a surface for later retrieval.

        Args:
            name: Unique identifier for surface
            surface: Surface to cache
        """
        self._surfaces[name] = surface
        logger.debug(f"Cached surface: {name} ({surface.get_width()}x{surface.get_height()})")

    def get_surface(self, name: str) -> Optional[pygame.Surface]:
        """Retrieve cached surface.

        Args:
            name: Surface identifier

        Returns:
            Cached surface or None if not found
        """
        return self._surfaces.get(name)

    def clear_fonts(self) -> None:
        """Clear all cached fonts."""
        count = len(self._fonts)
        self._fonts.clear()
        logger.info(f"Cleared {count} cached fonts")

    def clear_surfaces(self) -> None:
        """Clear all cached surfaces."""
        count = len(self._surfaces)
        self._surfaces.clear()
        logger.info(f"Cleared {count} cached surfaces")

    def clear_all(self) -> None:
        """Clear all cached resources."""
        self.clear_fonts()
        self.clear_surfaces()

    def get_stats(self) -> dict:
        """Get resource manager statistics.

        Returns:
            Dict with cache stats
        """
        total_requests = self._font_cache_hits + self._font_cache_misses
        hit_rate = (self._font_cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'fonts_cached': len(self._fonts),
            'surfaces_cached': len(self._surfaces),
            'font_cache_hits': self._font_cache_hits,
            'font_cache_misses': self._font_cache_misses,
            'font_cache_hit_rate': hit_rate
        }

    def log_stats(self) -> None:
        """Log resource manager statistics."""
        stats = self.get_stats()
        logger.info(
            f"Resource Manager Stats - Fonts: {stats['fonts_cached']}, "
            f"Surfaces: {stats['surfaces_cached']}, "
            f"Font Cache Hit Rate: {stats['font_cache_hit_rate']:.1f}%"
        )


# Global singleton instance
_resource_manager = ResourceManager()


# Convenience functions
def get_font(size: int, font_name: Optional[str] = None, bold: bool = False) -> pygame.font.Font:
    """Get cached font (convenience function).

    Args:
        size: Font size
        font_name: Font file path (None for default)
        bold: Whether to use bold

    Returns:
        pygame.Font instance
    """
    return _resource_manager.get_font(size, font_name, bold)


def cache_surface(name: str, surface: pygame.Surface) -> None:
    """Cache a surface (convenience function).

    Args:
        name: Surface identifier
        surface: Surface to cache
    """
    _resource_manager.cache_surface(name, surface)


def get_surface(name: str) -> Optional[pygame.Surface]:
    """Get cached surface (convenience function).

    Args:
        name: Surface identifier

    Returns:
        Cached surface or None
    """
    return _resource_manager.get_surface(name)


def clear_all_resources() -> None:
    """Clear all cached resources (convenience function)."""
    _resource_manager.clear_all()


def log_resource_stats() -> None:
    """Log resource statistics (convenience function)."""
    _resource_manager.log_stats()


# =============================================================================
# STANDARD FONT PRESETS
# =============================================================================

class Fonts:
    """Standard font presets used throughout the game."""

    # These will be loaded on first access
    _small: Optional[pygame.font.Font] = None
    _main: Optional[pygame.font.Font] = None
    _large: Optional[pygame.font.Font] = None
    _title: Optional[pygame.font.Font] = None

    @classmethod
    def small(cls) -> pygame.font.Font:
        """Get small font (16pt)."""
        if cls._small is None:
            cls._small = get_font(16)
        return cls._small

    @classmethod
    def main(cls) -> pygame.font.Font:
        """Get main font (18pt)."""
        if cls._main is None:
            cls._main = get_font(18)
        return cls._main

    @classmethod
    def large(cls) -> pygame.font.Font:
        """Get large font (24pt)."""
        if cls._large is None:
            cls._large = get_font(24)
        return cls._large

    @classmethod
    def title(cls) -> pygame.font.Font:
        """Get title font (32pt bold)."""
        if cls._title is None:
            cls._title = get_font(32, bold=True)
        return cls._title

    @classmethod
    def custom(cls, size: int, bold: bool = False) -> pygame.font.Font:
        """Get custom sized font.

        Args:
            size: Font size
            bold: Whether to use bold

        Returns:
            Font instance
        """
        return get_font(size, bold=bold)


# Initialize on module load
logger.info("Resource manager module loaded")
