from __future__ import annotations

from typing import List, Tuple
import math
import random

Point = Tuple[float, float]


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def quad_bezier(a: Point, c: Point, b: Point, samples: int = 32) -> List[Point]:
    """Quadratic Bezier polyline from A->B with single control C."""
    pts: List[Point] = []
    for i in range(samples + 1):
        t = i / samples
        # B(t) = (1-t)^2 A + 2(1-t)t C + t^2 B
        x = (1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0]
        y = (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]
        pts.append((x, y))
    return pts


def build_road_polyline(a: Point, b: Point, seed: int, curviness: float = 0.25, samples: int = 40) -> List[Point]:
    """Create a smooth road polyline between points a and b.

    Uses a single quadratic control point offset perpendicular to the segment.
    Curviness controls lateral offset as a fraction of distance.
    """
    rng = random.Random(seed)
    ax, ay = a; bx, by = b
    mx, my = (ax + bx) * 0.5, (ay + by) * 0.5
    dx, dy = bx - ax, by - ay
    dist = math.hypot(dx, dy) or 1.0
    # Perpendicular
    nx, ny = -dy / dist, dx / dist
    # Lateral offset with slight randomness
    off = dist * (curviness * (0.8 + 0.4 * rng.random()))
    # Random side
    if rng.random() < 0.5:
        off = -off
    cx, cy = mx + nx * off, my + ny * off
    return quad_bezier((ax, ay), (cx, cy), (bx, by), samples=samples)


def polyline_length(pts: List[Point]) -> float:
    total = 0.0
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i - 1][0]
        dy = pts[i][1] - pts[i - 1][1]
        total += math.hypot(dx, dy)
    return total


def distance_point_to_segment(p: Point, a: Point, b: Point) -> float:
    """Shortest distance from point P to segment AB."""
    px, py = p; ax, ay = a; bx, by = b
    abx, aby = bx - ax, by - ay
    ab2 = abx * abx + aby * aby
    if ab2 <= 1e-6:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * abx + (py - ay) * aby) / ab2
    t = max(0.0, min(1.0, t))
    cx, cy = ax + abx * t, ay + aby * t
    return math.hypot(px - cx, py - cy)

