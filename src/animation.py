import pygame


class Animation:
    def __init__(self, frames: list[pygame.Surface], fps: int = 10, loop: bool = True):
        self.frames = frames or []
        self.fps = max(1, int(fps))
        self.loop = loop
        self.index = 0
        self.timer = 0.0

    def reset(self):
        self.index = 0
        self.timer = 0.0

    def update(self, dt: float):
        if not self.frames:
            return
        self.timer += dt
        frame_time = 1.0 / self.fps
        while self.timer >= frame_time:
            self.timer -= frame_time
            self.index += 1
            if self.index >= len(self.frames):
                self.index = 0 if self.loop else len(self.frames) - 1

    def current_frame(self) -> pygame.Surface | None:
        if not self.frames:
            return None
        return self.frames[self.index]


class AnimationController:
    def __init__(self, sequences: dict[str, Animation], default: str = "idle"):
        self.sequences = sequences
        self.state = default if default in sequences else (next(iter(sequences)) if sequences else "")

    def set(self, name: str, fps: int | None = None):
        if name == self.state or name not in self.sequences:
            return
        self.state = name
        if fps is not None:
            self.sequences[name].fps = max(1, int(fps))
        self.sequences[name].reset()

    def update(self, dt: float):
        anim = self.sequences.get(self.state)
        if anim:
            anim.update(dt)

    def frame(self) -> pygame.Surface | None:
        anim = self.sequences.get(self.state)
        return anim.current_frame() if anim else None

