import pygame
from functools import lru_cache


@lru_cache(maxsize=256)
def load_spritesheet(path: str, frame_w: int, frame_h: int, num_frames: int | None = None):
    sheet = pygame.image.load(path).convert_alpha()
    frames = []
    sw, sh = sheet.get_width(), sheet.get_height()
    cols = max(1, sw // frame_w)
    rows = max(1, sh // frame_h)
    count = cols * rows if num_frames is None else min(num_frames, cols * rows)
    i = 0
    for ry in range(rows):
        for cx in range(cols):
            if i >= count:
                return frames
            rect = pygame.Rect(cx * frame_w, ry * frame_h, frame_w, frame_h)
            frames.append(sheet.subsurface(rect))
            i += 1
    return frames

