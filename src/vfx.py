"""
Visual Effects (VFX) Module
Handles procedural texture generation, particle systems, and other visual enhancements.

Features object pooling to prevent memory leaks and improve performance.
"""

import pygame
import random
import math
from dataclasses import dataclass
from typing import List, Optional
from src.logger import get_logger

logger = get_logger(__name__)

# =============================================================================
# PARTICLE POOLING SYSTEM (Prevents memory leaks)
# =============================================================================

MAX_PARTICLES = 1000  # Maximum active particles
POOL_SIZE = 1200  # Pool size (larger than MAX for recycling)

# Global lists
particles: List['Particle'] = []  # Active particles
_particle_pool: List['Particle'] = []  # Inactive particles ready for reuse


def _get_particle_from_pool() -> 'Particle':
    """Get a particle from the pool or create new one if pool empty.

    Returns:
        Particle instance ready for use
    """
    if _particle_pool:
        return _particle_pool.pop()
    else:
        # Pool exhausted, create new particle
        return Particle([0, 0], [0, 0], 0, (255, 255, 255), 1)


def _return_particle_to_pool(particle: 'Particle') -> None:
    """Return particle to pool for reuse.

    Args:
        particle: Particle to return to pool
    """
    if len(_particle_pool) < POOL_SIZE:
        _particle_pool.append(particle)
    # Else: discard (pool full)


def add_particle(particle: 'Particle') -> None:
    """Add particle with automatic cap enforcement using pooling.

    Args:
        particle: Particle to add
    """
    global particles

    if len(particles) >= MAX_PARTICLES:
        # Return oldest particles to pool
        excess = len(particles) - (MAX_PARTICLES - 50)
        for old_particle in particles[:excess]:
            _return_particle_to_pool(old_particle)
        particles = particles[excess:]

    particles.append(particle)

@dataclass
class Particle:
    pos: list
    vel: list
    lifespan: float
    color: tuple
    size: float
    particle_type: str = "circle"  # circle, line, square, star
    rotation: float = 0.0
    gravity: float = 0.0

def create_procedural_texture(width, height, color1, color2, density=0.15):
    """Creates a procedural texture surface with two colors."""
    texture = pygame.Surface((width, height))
    texture.fill(color1)
    num_pixels = int(width * height * density)

    for _ in range(num_pixels):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        texture.set_at((x, y), color2)
    return texture


# Shadow cache to avoid creating surfaces every frame (PERFORMANCE OPTIMIZATION)
SHADOW_CACHE = {}

def draw_entity_shadow(screen, pos, radius):
    """Draws a soft shadow under an entity (with caching)."""
    # Get or create cached shadow surface
    if radius not in SHADOW_CACHE:
        shadow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, (0, 0, 0, 90), (radius, radius), radius)
        SHADOW_CACHE[radius] = shadow_surf
    else:
        shadow_surf = SHADOW_CACHE[radius]

    # Use normal alpha blending to avoid darkening the entire rectangle
    screen.blit(shadow_surf, (pos[0] - radius, pos[1] - radius))


def render_location_icon(screen, loc_type, pos):
    """Renders a more detailed icon for a location."""
    if loc_type == "town":
        pygame.draw.rect(screen, (139, 69, 19), (pos[0] - 10, pos[1] - 5, 20, 15)) # Base
        pygame.draw.polygon(screen, (210, 105, 30), [(pos[0] - 12, pos[1] - 5), (pos[0] + 12, pos[1] - 5), (pos[0], pos[1] - 15)]) # Roof
    elif loc_type == "castle":
        pygame.draw.rect(screen, (100, 100, 100), (pos[0] - 12, pos[1] - 15, 24, 25)) # Main tower
        pygame.draw.rect(screen, (80, 80, 80), (pos[0] - 12, pos[1] - 18, 5, 5)) # Turret 1
        pygame.draw.rect(screen, (80, 80, 80), (pos[0] + 7, pos[1] - 18, 5, 5)) # Turret 2
    elif loc_type == "bandit_camp":
        pygame.draw.polygon(screen, (139, 69, 19), [(pos[0], pos[1] - 12), (pos[0] - 10, pos[1] + 8), (pos[0] + 10, pos[1] + 8)])
        pygame.draw.line(screen, (0,0,0), (pos[0], pos[1] - 12), (pos[0], pos[1] + 8), 2)
    else:
        pygame.draw.circle(screen, (255, 255, 255), pos, 15)

def create_blood_splatter(pos, amount, direction=None):
    """Creates varied blood particles - droplets, splatters, mist."""
    for _ in range(amount):
        particle_choice = random.choice(["droplet", "splatter", "mist"])

        if particle_choice == "droplet":
            # Heavy blood droplets with gravity
            angle = random.uniform(0, math.tau) if not direction else direction + random.uniform(-0.5, 0.5)
            speed = random.uniform(3, 6)
            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
            lifespan = random.uniform(0.4, 0.7)
            size = random.uniform(2, 4)
            color = (180, 0, 0)
            add_particle(Particle(list(pos), vel, lifespan, color, size, "circle", 0.0, 200))

        elif particle_choice == "splatter":
            # Elongated blood splatters
            angle = random.uniform(0, math.tau) if not direction else direction + random.uniform(-0.8, 0.8)
            speed = random.uniform(2, 5)
            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
            lifespan = random.uniform(0.3, 0.5)
            size = random.uniform(3, 5)
            color = (220, 10, 10)
            add_particle(Particle(list(pos), vel, lifespan, color, size, "line", angle, 100))

        else:  # mist
            # Fine blood mist
            angle = random.uniform(0, math.tau)
            speed = random.uniform(1, 3)
            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
            lifespan = random.uniform(0.2, 0.4)
            size = random.uniform(1, 2)
            color = (200, 50, 50)
            add_particle(Particle(list(pos), vel, lifespan, color, size, "circle", 0.0, 0))

def create_dust_cloud(pos, amount):
    for _ in range(amount):
        vel = [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)]
        lifespan = random.uniform(0.4, 0.8)
        size = random.uniform(2, 5)
        color = (139, 115, 85)
        add_particle(Particle([pos[0], pos[1] + 10], vel, lifespan, color, size))

def create_block_spark(pos, amount, direction=None):
    """Metal-on-metal sparks when blocking."""
    for _ in range(amount):
        # Sparks fly away from impact direction
        if direction:
            angle = direction + random.uniform(-1.0, 1.0)
        else:
            angle = random.uniform(0, math.tau)

        speed = random.uniform(3, 7)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = random.uniform(0.2, 0.5)
        size = random.uniform(1, 3)
        color = random.choice([(255, 255, 150), (255, 255, 255), (255, 220, 100), (255, 180, 0)])
        add_particle(Particle(list(pos), vel, lifespan, color, size, "star", angle, 50))

def create_slash_effect(pos, direction, slash_type="horizontal"):
    """Visual slash trail for different attack types."""
    if slash_type == "horizontal":
        # Wide horizontal slash
        for i in range(15):
            offset_x = (i - 7) * 8
            offset_y = random.uniform(-5, 5)
            particle_pos = [pos[0] + offset_x, pos[1] + offset_y]
            vel = [math.cos(direction) * 5, math.sin(direction) * 5]
            lifespan = 0.15
            size = random.uniform(3, 6)
            color = (200, 220, 255)
            add_particle(Particle(particle_pos, vel, lifespan, color, size, "line", direction, 0))

    elif slash_type == "vertical":
        # Vertical overhead slash
        for i in range(15):
            offset_y = (i - 7) * 8
            offset_x = random.uniform(-5, 5)
            particle_pos = [pos[0] + offset_x, pos[1] + offset_y]
            vel = [math.cos(direction) * 5, math.sin(direction) * 5]
            lifespan = 0.15
            size = random.uniform(3, 6)
            color = (255, 200, 200)
            add_particle(Particle(particle_pos, vel, lifespan, color, size, "line", direction + math.pi/2, 0))

    elif slash_type == "thrust":
        # Forward thrust with concentrated particles
        for i in range(10):
            spread = random.uniform(-0.3, 0.3)
            speed = random.uniform(6, 10)
            vel = [math.cos(direction + spread) * speed, math.sin(direction + spread) * speed]
            lifespan = 0.2
            size = random.uniform(2, 4)
            color = (255, 255, 200)
            add_particle(Particle(list(pos), vel, lifespan, color, size, "circle", direction, 0))

def create_impact_dust(pos, amount, direction=None):
    """Heavy dust cloud on impact."""
    for _ in range(amount):
        if direction:
            angle = direction + random.uniform(-0.8, 0.8)
        else:
            angle = random.uniform(0, math.tau)

        speed = random.uniform(2, 4)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = random.uniform(0.5, 1.0)
        size = random.uniform(3, 7)
        color_var = random.randint(-15, 15)
        color = (139 + color_var, 115 + color_var, 85 + color_var)
        add_particle(Particle([pos[0], pos[1] + 10], vel, lifespan, color, size, "circle", 0.0, 30))

def create_weapon_trail(pos, angle, color):
    speed = random.uniform(150, 200)
    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
    lifespan = 0.2
    size = random.uniform(3, 5)
    add_particle(Particle(list(pos), vel, lifespan, color, size))

def create_charge_up_effect(pos):
    for i in range(20):
        angle = (i / 20) * math.tau
        speed = random.uniform(0.5, 1.5)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = 0.3
        size = random.uniform(1, 3)
        color = (200, 200, 255)
        add_particle(Particle(list(pos), vel, lifespan, color, size))

def create_whirlwind_effect(pos):
    for i in range(60):
        angle = (i / 60) * math.tau
        speed = 200 + random.uniform(-20, 20)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = 0.4
        size = random.uniform(2, 4)
        color = (200, 200, 255)
        add_particle(Particle(list(pos), vel, lifespan, color, size))

def create_smash_effect(pos, direction):
    for i in range(30):
        angle = math.atan2(direction[1], direction[0]) + random.uniform(-0.8, 0.8)
        speed = random.uniform(50, 150)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = 0.5
        size = random.uniform(2, 5)
        color = (139, 69, 19)
        add_particle(Particle(list(pos), vel, lifespan, color, size))

def create_lunge_trail(pos, direction):
    # This is similar to weapon trail but could be customized
    create_weapon_trail(pos, math.atan2(direction[1], direction[0]), (255, 255, 255))

def create_levelup_glow(pos):
    for i in range(40):
        angle = (i / 40) * math.tau
        speed = random.uniform(1, 3)
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        lifespan = random.uniform(0.8, 1.5)
        size = random.uniform(2, 4)
        color = (255, 215, 0)
        add_particle(Particle(list(pos), vel, lifespan, color, size))

def update_particles(dt):
    """Update all active particles and return dead ones to pool.

    Args:
        dt: Delta time in seconds
    """
    global particles

    # Update each particle
    for p in particles:
        p.pos[0] += p.vel[0] * dt * 60  # Scale velocity
        p.pos[1] += p.vel[1] * dt * 60

        # Apply gravity
        if p.gravity > 0:
            p.vel[1] += p.gravity * dt

        # Update rotation
        p.rotation += dt * 10

        p.lifespan -= dt
        p.size = max(0, p.size - 2 * dt)

    # Separate living and dead particles
    alive = []
    for p in particles:
        if p.lifespan > 0 and p.size > 0:
            alive.append(p)
        else:
            # Return dead particle to pool
            _return_particle_to_pool(p)

    particles = alive

def render_particles(screen, camera=None):
    for p in particles:
        pos = p.pos
        if camera:
            pos = camera.world_to_screen(pos)

        alpha = int(255 * (p.lifespan / 0.5)) if p.lifespan < 0.5 else 255
        size = int(p.size)

        if size < 1:
            continue

        # Render based on particle type
        if p.particle_type == "circle":
            temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, p.color + (alpha,), (size, size), size)
            screen.blit(temp_surf, (pos[0] - size, pos[1] - size))

        elif p.particle_type == "line":
            # Elongated particle (slash trails, blood splatters)
            length = size * 3
            end_x = pos[0] + math.cos(p.rotation) * length
            end_y = pos[1] + math.sin(p.rotation) * length
            temp_surf = pygame.Surface((length * 2, length * 2), pygame.SRCALPHA)
            center = (length, length)
            end_point = (length + math.cos(p.rotation) * length, length + math.sin(p.rotation) * length)
            pygame.draw.line(temp_surf, p.color + (alpha,), center, end_point, max(1, size // 2))
            screen.blit(temp_surf, (pos[0] - length, pos[1] - length))

        elif p.particle_type == "star":
            # Star-shaped particle (sparks)
            temp_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            center = (size * 1.5, size * 1.5)
            # Draw 4-point star
            for angle_offset in [0, math.pi/2, math.pi, 3*math.pi/2]:
                angle = p.rotation + angle_offset
                end_x = center[0] + math.cos(angle) * size * 1.5
                end_y = center[1] + math.sin(angle) * size * 1.5
                pygame.draw.line(temp_surf, p.color + (alpha,), center, (end_x, end_y), max(1, size // 3))
            screen.blit(temp_surf, (pos[0] - size * 1.5, pos[1] - size * 1.5))

        elif p.particle_type == "square":
            temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, p.color + (alpha,), (0, 0, size * 2, size * 2))
            screen.blit(temp_surf, (pos[0] - size, pos[1] - size))

# Pre-generate textures on module load to avoid doing it in the loop
GRASS_TEXTURE = create_procedural_texture(1280, 720, (18, 48, 18), (25, 60, 25))
DIRT_TEXTURE = create_procedural_texture(1280, 720, (80, 60, 40), (95, 70, 50))
BATTLE_GROUND_TEXTURE = create_procedural_texture(1280, 720, (40, 35, 50), (55, 50, 65))
HILL_TEXTURE = create_procedural_texture(400, 200, (139, 90, 43), (160, 105, 50), density=0.2)


# =============================================================================
# DIAGNOSTICS & UTILITIES
# =============================================================================

def get_particle_stats() -> dict:
    """Get current particle system statistics.

    Returns:
        Dict with stats: active, pooled, total_created
    """
    return {
        'active': len(particles),
        'pooled': len(_particle_pool),
        'capacity': MAX_PARTICLES,
        'pool_capacity': POOL_SIZE,
        'usage_percent': (len(particles) / MAX_PARTICLES) * 100 if MAX_PARTICLES > 0 else 0
    }


def clear_all_particles() -> None:
    """Clear all active particles and return them to pool.

    Useful for scene transitions.
    """
    global particles
    for p in particles:
        _return_particle_to_pool(p)
    particles.clear()
    logger.debug(f"Cleared all particles. Pool size: {len(_particle_pool)}")


def log_particle_stats() -> None:
    """Log current particle statistics (for debugging)."""
    stats = get_particle_stats()
    logger.debug(
        f"Particles - Active: {stats['active']}/{stats['capacity']} "
        f"({stats['usage_percent']:.1f}%), Pooled: {stats['pooled']}/{stats['pool_capacity']}"
    )
