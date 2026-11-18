from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw

from .shapes import (
    Point,
    _polygon,
    flower_points,
    heart_points,
    leaf_points,
    star_points,
)

DrawFn = Callable[[ImageDraw.ImageDraw, int], None]


@dataclass(frozen=True)
class Shape:
    key: str
    name: str
    category: str
    draw: DrawFn
    clip_safe: bool = False


def _rect(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float], color: int = 255) -> None:
    d.rectangle(box, fill=color)


def _ellipse(d: ImageDraw.ImageDraw, box: tuple[float, float, float, float], color: int = 255) -> None:
    d.ellipse(box, fill=color)


def _circle(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color: int = 255) -> None:
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)


def _poly(d: ImageDraw.ImageDraw, points: list[Point], color: int = 255) -> None:
    d.polygon(_polygon(points), fill=color)


def _square(d: ImageDraw.ImageDraw, s: int) -> None:
    _rect(d, (s * 0.04, s * 0.04, s * 0.96, s * 0.96))


def _rounded(d: ImageDraw.ImageDraw, s: int) -> None:
    r = s * 0.13
    d.rounded_rectangle((s * 0.04, s * 0.04, s * 0.96, s * 0.96), radius=r, fill=255)


def _circle_shape(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.03, s * 0.03, s * 0.97, s * 0.97))


def _capsule(d: ImageDraw.ImageDraw, s: int) -> None:
    d.rounded_rectangle((s * 0.04, s * 0.18, s * 0.96, s * 0.82), radius=s * 0.32, fill=255)


def _diamond(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s / 2, s * 0.02), (s * 0.98, s / 2), (s / 2, s * 0.98), (s * 0.02, s / 2)])


def _triangle(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s / 2, s * 0.03), (s * 0.97, s * 0.95), (s * 0.03, s * 0.95)])


def _hexagon(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s / 2 + math.cos(math.pi / 3 * i) * s * 0.48, s / 2 + math.sin(math.pi / 3 * i) * s * 0.48) for i in range(6)])


def _octagon(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(
        d,
        [
            (
                s / 2 + math.cos(math.pi / 8 + math.pi / 4 * i) * s * 0.48,
                s / 2 + math.sin(math.pi / 8 + math.pi / 4 * i) * s * 0.48,
            )
            for i in range(8)
        ],
    )


def _star5(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, star_points(s / 2, s / 2, s * 0.49, s * 0.2))


def _star8(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, star_points(s / 2, s / 2, s * 0.49, s * 0.28, points=8))


def _cross(d: ImageDraw.ImageDraw, s: int) -> None:
    a, b = s * 0.33, s * 0.67
    _poly(
        d,
        [
            (a, s * 0.05),
            (b, s * 0.05),
            (b, a),
            (s * 0.95, a),
            (s * 0.95, b),
            (b, b),
            (b, s * 0.95),
            (a, s * 0.95),
            (a, b),
            (s * 0.05, b),
            (s * 0.05, a),
            (a, a),
        ],
    )


def _shield(d: ImageDraw.ImageDraw, s: int) -> None:
    d.rounded_rectangle((s * 0.08, s * 0.06, s * 0.92, s * 0.5), radius=s * 0.1, fill=255)
    _poly(d, [(s * 0.08, s * 0.38), (s * 0.92, s * 0.38), (s * 0.5, s * 0.97)])


def _heart(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, heart_points(s / 2, s * 0.52, s * 0.47, steps=48))


def _leaf(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, leaf_points(s / 2, s * 0.51, s * 0.49, steps=48))


def _flower(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, flower_points(s / 2, s / 2, s * 0.49, petals=8))
    _circle(d, s / 2, s / 2, s * 0.16)


def _cloud(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.3, s * 0.58, s * 0.22)
    _circle(d, s * 0.5, s * 0.42, s * 0.27)
    _circle(d, s * 0.7, s * 0.58, s * 0.22)
    d.rounded_rectangle((s * 0.1, s * 0.52, s * 0.9, s * 0.82), radius=s * 0.14, fill=255)


def _sun(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s / 2, s / 2, s * 0.27)
    for i in range(12):
        angle = i * math.pi / 6
        x1, y1 = s / 2 + math.cos(angle) * s * 0.34, s / 2 + math.sin(angle) * s * 0.34
        x2, y2 = s / 2 + math.cos(angle) * s * 0.48, s / 2 + math.sin(angle) * s * 0.48
        dx, dy = -math.sin(angle) * s * 0.045, math.cos(angle) * s * 0.045
        _poly(d, [(x1 + dx, y1 + dy), (x2, y2), (x1 - dx, y1 - dy)])


def _moon(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.5, s * 0.52, s * 0.45)
    _circle(d, s * 0.68, s * 0.36, s * 0.38, 0)
    _circle(d, s * 0.79, s * 0.2, s * 0.035)


def _snowflake(d: ImageDraw.ImageDraw, s: int) -> None:
    width = max(2, round(s * 0.045))
    for i in range(6):
        angle = i * math.pi / 3
        x2, y2 = s / 2 + math.cos(angle) * s * 0.47, s / 2 + math.sin(angle) * s * 0.47
        d.line((s / 2, s / 2, x2, y2), fill=255, width=width)
        for t in (0.55, 0.78):
            bx = s / 2 + math.cos(angle) * s * 0.47 * t
            by = s / 2 + math.sin(angle) * s * 0.47 * t
            for sign in (-1, 1):
                ba = angle + sign * math.pi / 4
                d.line((bx, by, bx + math.cos(ba) * s * 0.12, by + math.sin(ba) * s * 0.12), fill=255, width=width)
    _circle(d, s / 2, s / 2, s * 0.08)


def _wave(d: ImageDraw.ImageDraw, s: int) -> None:
    top: list[Point] = []
    bottom: list[Point] = []
    for i in range(41):
        t = i / 40
        x = s * (0.03 + 0.94 * t)
        y = math.sin(t * math.pi * 3) * s * 0.12
        top.append((x, s * 0.5 + y - s * 0.22))
        bottom.append((x, s * 0.5 + y + s * 0.12))
    _poly(d, top + list(reversed(bottom)))


def _drop(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s / 2, s * 0.02), (s * 0.84, s * 0.46), (s * 0.72, s * 0.8), (s / 2, s * 0.98), (s * 0.28, s * 0.8), (s * 0.16, s * 0.46)])
    _circle(d, s / 2, s * 0.62, s * 0.3)


def _planet(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.48, s * 0.46, s * 0.32)
    d.ellipse((s * 0.04, s * 0.47, s * 0.96, s * 0.93), outline=255, width=max(2, round(s * 0.07)))
    _circle(d, s * 0.76, s * 0.2, s * 0.045)


def _cat(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s * 0.12, s * 0.34), (s * 0.1, s * 0.02), (s * 0.4, s * 0.2)])
    _poly(d, [(s * 0.88, s * 0.34), (s * 0.9, s * 0.02), (s * 0.6, s * 0.2)])
    _ellipse(d, (s * 0.1, s * 0.2, s * 0.9, s * 0.98))
    _ellipse(d, (s * 0.2, s * 0.78, s * 0.8, s * 0.99))


def _bear(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.21, s * 0.19, s * 0.15)
    _circle(d, s * 0.79, s * 0.19, s * 0.15)
    _ellipse(d, (s * 0.12, s * 0.18, s * 0.88, s * 0.97))
    _ellipse(d, (s * 0.28, s * 0.64, s * 0.72, s * 0.87), 0)
    _circle(d, s * 0.5, s * 0.72, s * 0.07)


def _bunny(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.22, s * 0.01, s * 0.43, s * 0.5))
    _ellipse(d, (s * 0.57, s * 0.01, s * 0.78, s * 0.5))
    _ellipse(d, (s * 0.17, s * 0.32, s * 0.83, s * 0.98))


def _fox(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s * 0.08, s * 0.3), (s * 0.22, s * 0.04), (s * 0.4, s * 0.24)])
    _poly(d, [(s * 0.92, s * 0.3), (s * 0.78, s * 0.04), (s * 0.6, s * 0.24)])
    _poly(d, [(s * 0.08, s * 0.28), (s * 0.5, s * 0.08), (s * 0.92, s * 0.28), (s * 0.76, s * 0.9), (s * 0.5, s * 0.99), (s * 0.24, s * 0.9)])
    _poly(d, [(s * 0.35, s * 0.66), (s * 0.5, s * 0.58), (s * 0.65, s * 0.66), (s * 0.5, s * 0.78)], 0)
    _circle(d, s * 0.5, s * 0.82, s * 0.05)


def _owl(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s * 0.18, s * 0.24), (s * 0.26, s * 0.02), (s * 0.4, s * 0.18)])
    _poly(d, [(s * 0.82, s * 0.24), (s * 0.74, s * 0.02), (s * 0.6, s * 0.18)])
    _ellipse(d, (s * 0.16, s * 0.16, s * 0.84, s * 0.98))
    _ellipse(d, (s * 0.24, s * 0.68, s * 0.46, s * 0.9), 0)
    _ellipse(d, (s * 0.54, s * 0.68, s * 0.76, s * 0.9), 0)
    _circle(d, s * 0.5, s * 0.8, s * 0.06)


def _panda(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.16, s * 0.17, s * 0.15)
    _circle(d, s * 0.84, s * 0.17, s * 0.15)
    _ellipse(d, (s * 0.1, s * 0.16, s * 0.9, s * 0.97))
    _ellipse(d, (s * 0.16, s * 0.4, s * 0.4, s * 0.62), 0)
    _ellipse(d, (s * 0.6, s * 0.4, s * 0.84, s * 0.62), 0)
    _ellipse(d, (s * 0.44, s * 0.74, s * 0.56, s * 0.86), 0)


def _fish(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.08, s * 0.28, s * 0.74, s * 0.94))
    _poly(d, [(s * 0.7, s * 0.61), (s * 0.97, s * 0.34), (s * 0.97, s * 0.88)])
    _poly(d, [(s * 0.36, s * 0.3), (s * 0.52, s * 0.08), (s * 0.58, s * 0.32)])
    _circle(d, s * 0.26, s * 0.52, s * 0.035, 0)


def _butterfly(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.08, s * 0.1, s * 0.5, s * 0.55))
    _ellipse(d, (s * 0.5, s * 0.1, s * 0.92, s * 0.55))
    _ellipse(d, (s * 0.13, s * 0.48, s * 0.48, s * 0.9))
    _ellipse(d, (s * 0.52, s * 0.48, s * 0.87, s * 0.9))
    _ellipse(d, (s * 0.45, s * 0.16, s * 0.55, s * 0.88))
    d.line((s * 0.48, s * 0.16, s * 0.36, s * 0.02), fill=255, width=max(2, round(s * 0.03)))
    d.line((s * 0.52, s * 0.16, s * 0.64, s * 0.02), fill=255, width=max(2, round(s * 0.03)))


def _paw(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.24, s * 0.4, s * 0.76, s * 0.96))
    for cx, cy in ((0.12, 0.26), (0.36, 0.1), (0.64, 0.1), (0.88, 0.26)):
        _circle(d, s * cx, s * cy, s * 0.12)


def _ladybug(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.12, s * 0.2, s * 0.88, s * 0.96))
    _ellipse(d, (s * 0.3, s * 0.08, s * 0.7, s * 0.4))
    d.line((s * 0.5, s * 0.28, s * 0.5, s * 0.92), fill=0, width=max(2, round(s * 0.035)))
    for cx, cy, r in ((0.32, 0.5, 0.07), (0.68, 0.5, 0.07), (0.3, 0.72, 0.06), (0.7, 0.72, 0.06), (0.5, 0.38, 0.05)):
        _circle(d, s * cx, s * cy, s * r, 0)
    _circle(d, s * 0.5, s * 0.14, s * 0.045, 0)


def _turtle(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.12, s * 0.22, s * 0.8, s * 0.86))
    _circle(d, s * 0.86, s * 0.42, s * 0.12)
    _circle(d, s * 0.9, s * 0.39, s * 0.025, 0)
    for cx in (0.24, 0.68):
        _ellipse(d, (s * (cx - 0.07), s * 0.78, s * (cx + 0.07), s * 0.95))
    _ellipse(d, (s * 0.32, s * 0.85, s * 0.46, s * 0.99))
    _ellipse(d, (s * 0.54, s * 0.85, s * 0.68, s * 0.99))
    _poly(d, [(s * 0.12, s * 0.62), (s * 0.02, s * 0.72), (s * 0.14, s * 0.78)])
    _ellipse(d, (s * 0.3, s * 0.36, s * 0.62, s * 0.68), 0)
    _ellipse(d, (s * 0.38, s * 0.44, s * 0.54, s * 0.6))


def _penguin(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.18, s * 0.1, s * 0.82, s * 0.99))
    _circle(d, s * 0.5, s * 0.28, s * 0.19)
    _poly(d, [(s * 0.44, s * 0.3), (s * 0.5, s * 0.4), (s * 0.56, s * 0.3)])
    _ellipse(d, (s * 0.04, s * 0.42, s * 0.22, s * 0.8))
    _ellipse(d, (s * 0.78, s * 0.42, s * 0.96, s * 0.8))
    _ellipse(d, (s * 0.3, s * 0.48, s * 0.7, s * 0.94), 0)
    _circle(d, s * 0.43, s * 0.25, s * 0.025, 0)
    _circle(d, s * 0.57, s * 0.25, s * 0.025, 0)


def _crown(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(
        d,
        [
            (s * 0.08, s * 0.78),
            (s * 0.1, s * 0.2),
            (s * 0.3, s * 0.5),
            (s * 0.5, s * 0.08),
            (s * 0.7, s * 0.5),
            (s * 0.9, s * 0.2),
            (s * 0.92, s * 0.78),
        ],
    )
    d.rounded_rectangle((s * 0.08, s * 0.7, s * 0.92, s * 0.92), radius=s * 0.05, fill=255)
    for cx, cy in ((0.1, 0.18), (0.5, 0.06), (0.9, 0.18)):
        _circle(d, s * cx, s * cy, s * 0.045)


def _cup(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s * 0.28, s * 0.24), (s * 0.72, s * 0.24), (s * 0.66, s * 0.72), (s * 0.34, s * 0.72)])
    d.arc((s * 0.12, s * 0.28, s * 0.34, s * 0.58), 90, 270, fill=255, width=max(2, round(s * 0.05)))
    d.arc((s * 0.66, s * 0.28, s * 0.88, s * 0.58), -90, 90, fill=255, width=max(2, round(s * 0.05)))
    _rect(d, (s * 0.4, s * 0.72, s * 0.6, s * 0.8))
    d.rounded_rectangle((s * 0.28, s * 0.8, s * 0.72, s * 0.92), radius=s * 0.03, fill=255)
    d.arc((s * 0.3, s * 0.12, s * 0.7, s * 0.4), 200, 340, fill=255, width=max(2, round(s * 0.03)))


def _mask(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.05, s * 0.18, s * 0.95, s * 0.92))
    _ellipse(d, (s * 0.2, s * 0.36, s * 0.42, s * 0.58), 0)
    _ellipse(d, (s * 0.58, s * 0.36, s * 0.8, s * 0.58), 0)
    d.arc((s * 0.32, s * 0.52, s * 0.68, s * 0.84), 20, 160, fill=0, width=max(2, round(s * 0.03)))


def _rocket(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, [(s * 0.5, s * 0.02), (s * 0.72, s * 0.32), (s * 0.72, s * 0.72), (s * 0.6, s * 0.9), (s * 0.4, s * 0.9), (s * 0.28, s * 0.72), (s * 0.28, s * 0.32)])
    _poly(d, [(s * 0.28, s * 0.52), (s * 0.08, s * 0.9), (s * 0.28, s * 0.82)])
    _poly(d, [(s * 0.72, s * 0.52), (s * 0.92, s * 0.9), (s * 0.72, s * 0.82)])
    _circle(d, s * 0.5, s * 0.38, s * 0.1, 0)
    _circle(d, s * 0.5, s * 0.38, s * 0.06)


def _guitar(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.08, s * 0.44, s * 0.58, s * 0.98))
    _ellipse(d, (s * 0.16, s * 0.24, s * 0.54, s * 0.68))
    _rect(d, (s * 0.47, s * 0.05, s * 0.57, s * 0.5))
    d.rounded_rectangle((s * 0.43, s * 0.01, s * 0.61, s * 0.14), radius=s * 0.03, fill=255)
    _circle(d, s * 0.33, s * 0.62, s * 0.08, 0)
    for i in range(3):
        d.line((s * 0.5, s * 0.12 + i * s * 0.04, s * 0.5, s * 0.7), fill=0, width=max(1, round(s * 0.008)))


def _speech_bubble(d: ImageDraw.ImageDraw, s: int) -> None:
    d.rounded_rectangle((s * 0.06, s * 0.1, s * 0.94, s * 0.76), radius=s * 0.16, fill=255)
    _poly(d, [(s * 0.24, s * 0.7), (s * 0.34, s * 0.97), (s * 0.46, s * 0.72)])
    _circle(d, s * 0.3, s * 0.42, s * 0.035, 0)
    _circle(d, s * 0.5, s * 0.42, s * 0.035, 0)
    _circle(d, s * 0.7, s * 0.42, s * 0.035, 0)


def _puzzle(d: ImageDraw.ImageDraw, s: int) -> None:
    d.rounded_rectangle((s * 0.08, s * 0.12, s * 0.92, s * 0.92), radius=s * 0.06, fill=255)
    _circle(d, s * 0.5, s * 0.1, s * 0.12)
    _circle(d, s * 0.94, s * 0.52, s * 0.11, 0)
    _circle(d, s * 0.5, s * 0.52, s * 0.06, 0)


def _gift(d: ImageDraw.ImageDraw, s: int) -> None:
    _rect(d, (s * 0.14, s * 0.32, s * 0.86, s * 0.94))
    d.rounded_rectangle((s * 0.08, s * 0.2, s * 0.92, s * 0.38), radius=s * 0.04, fill=255)
    _rect(d, (s * 0.43, s * 0.38, s * 0.57, s * 0.94))
    _circle(d, s * 0.36, s * 0.16, s * 0.13)
    _circle(d, s * 0.64, s * 0.16, s * 0.13)
    _circle(d, s * 0.5, s * 0.2, s * 0.06, 0)


def _tree(d: ImageDraw.ImageDraw, s: int) -> None:
    _rect(d, (s * 0.44, s * 0.72, s * 0.56, s * 0.97))
    _poly(d, [(s * 0.5, s * 0.02), (s * 0.82, s * 0.44), (s * 0.18, s * 0.44)])
    _poly(d, [(s * 0.5, s * 0.22), (s * 0.9, s * 0.64), (s * 0.1, s * 0.64)])
    _poly(d, [(s * 0.5, s * 0.42), (s * 0.97, s * 0.82), (s * 0.03, s * 0.82)])


def _pumpkin(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.06, s * 0.16, s * 0.94, s * 0.92))
    d.rounded_rectangle((s * 0.45, s * 0.01, s * 0.55, s * 0.18), radius=s * 0.02, fill=255)
    for x in (0.32, 0.5, 0.68):
        d.arc((s * (x - 0.12), s * 0.2, s * (x + 0.12), s * 0.88), 90, 270, fill=0, width=max(2, round(s * 0.022)))
    _poly(d, [(s * 0.38, s * 0.6), (s * 0.62, s * 0.6), (s * 0.5, s * 0.7)], 0)
    _poly(d, [(s * 0.3, s * 0.48), (s * 0.42, s * 0.56), (s * 0.3, s * 0.58)], 0)
    _poly(d, [(s * 0.7, s * 0.48), (s * 0.58, s * 0.56), (s * 0.7, s * 0.58)], 0)


def _squircle(d: ImageDraw.ImageDraw, s: int) -> None:
    pts: list[Point] = []
    for i in range(96):
        angle = 2 * math.pi * i / 96
        c, sn = math.cos(angle), math.sin(angle)
        x = math.copysign(abs(c) ** 0.5, c)
        y = math.copysign(abs(sn) ** 0.5, sn)
        pts.append((s * (0.5 + 0.47 * x), s * (0.5 + 0.47 * y)))
    _poly(d, pts)


def _burst(d: ImageDraw.ImageDraw, s: int) -> None:
    _poly(d, star_points(s / 2, s / 2, s * 0.49, s * 0.3, points=12))


def _clover(d: ImageDraw.ImageDraw, s: int) -> None:
    for cx, cy in ((0.31, 0.31), (0.69, 0.31), (0.31, 0.69), (0.69, 0.69)):
        _circle(d, s * cx, s * cy, s * 0.24)
    _circle(d, s * 0.5, s * 0.5, s * 0.25)


def _cactus(d: ImageDraw.ImageDraw, s: int) -> None:
    d.rounded_rectangle((s * 0.38, s * 0.12, s * 0.62, s * 0.94), radius=s * 0.12, fill=255)
    d.rounded_rectangle((s * 0.17, s * 0.4, s * 0.43, s * 0.53), radius=s * 0.06, fill=255)
    d.rounded_rectangle((s * 0.17, s * 0.4, s * 0.3, s * 0.72), radius=s * 0.06, fill=255)
    d.rounded_rectangle((s * 0.57, s * 0.3, s * 0.83, s * 0.43), radius=s * 0.06, fill=255)
    d.rounded_rectangle((s * 0.7, s * 0.3, s * 0.83, s * 0.64), radius=s * 0.06, fill=255)


def _frog(d: ImageDraw.ImageDraw, s: int) -> None:
    _circle(d, s * 0.25, s * 0.23, s * 0.15)
    _circle(d, s * 0.75, s * 0.23, s * 0.15)
    _ellipse(d, (s * 0.06, s * 0.26, s * 0.94, s * 0.92))
    _ellipse(d, (s * 0.25, s * 0.38, s * 0.75, s * 0.78), 0)
    _circle(d, s * 0.25, s * 0.23, s * 0.045, 0)
    _circle(d, s * 0.75, s * 0.23, s * 0.045, 0)
    d.arc((s * 0.32, s * 0.5, s * 0.68, s * 0.82), 20, 160, fill=0, width=max(2, round(s * 0.025)))


def _whale(d: ImageDraw.ImageDraw, s: int) -> None:
    _ellipse(d, (s * 0.06, s * 0.38, s * 0.84, s * 0.92))
    _poly(d, [(s * 0.76, s * 0.58), (s * 0.97, s * 0.3), (s * 0.92, s * 0.86)])
    _poly(d, [(s * 0.35, s * 0.62), (s * 0.48, s * 0.84), (s * 0.58, s * 0.68)])
    _circle(d, s * 0.25, s * 0.58, s * 0.035, 0)
    d.arc((s * 0.12, s * 0.46, s * 0.4, s * 0.72), 20, 120, fill=0, width=max(2, round(s * 0.025)))


def _anchor(d: ImageDraw.ImageDraw, s: int) -> None:
    width = max(3, round(s * 0.065))
    d.ellipse((s * 0.4, s * 0.03, s * 0.6, s * 0.23), outline=255, width=width)
    _rect(d, (s * 0.465, s * 0.22, s * 0.535, s * 0.9))
    _rect(d, (s * 0.28, s * 0.35, s * 0.72, s * 0.43))
    d.arc((s * 0.12, s * 0.38, s * 0.88, s * 0.98), 20, 160, fill=255, width=width)
    _poly(d, [(s * 0.12, s * 0.78), (s * 0.04, s * 0.66), (s * 0.18, s * 0.64)])
    _poly(d, [(s * 0.88, s * 0.78), (s * 0.96, s * 0.66), (s * 0.82, s * 0.64)])
    _circle(d, s * 0.5, s * 0.13, s * 0.035, 0)


def _music_note(d: ImageDraw.ImageDraw, s: int) -> None:
    _rect(d, (s * 0.55, s * 0.1, s * 0.64, s * 0.72))
    _ellipse(d, (s * 0.26, s * 0.62, s * 0.6, s * 0.83))
    _poly(d, [(s * 0.62, s * 0.1), (s * 0.82, s * 0.2), (s * 0.82, s * 0.34), (s * 0.62, s * 0.25)])
    _ellipse(d, (s * 0.3, s * 0.66, s * 0.42, s * 0.8), 0)


SHAPES: dict[str, Shape] = {
    "square": Shape("square", "Квадрат", "Геометрия", _square, True),
    "rounded": Shape("rounded", "Скруглённый квадрат", "Геометрия", _rounded),
    "circle": Shape("circle", "Круг", "Геометрия", _circle_shape),
    "capsule": Shape("capsule", "Капсула", "Геометрия", _capsule),
    "diamond": Shape("diamond", "Ромб", "Геометрия", _diamond),
    "triangle": Shape("triangle", "Треугольник", "Геометрия", _triangle),
    "hexagon": Shape("hexagon", "Шестиугольник", "Геометрия", _hexagon),
    "octagon": Shape("octagon", "Восьмиугольник", "Геометрия", _octagon),
    "star5": Shape("star5", "Звезда 5", "Геометрия", _star5),
    "star8": Shape("star8", "Звезда 8", "Геометрия", _star8),
    "cross": Shape("cross", "Крест", "Геометрия", _cross),
    "shield": Shape("shield", "Щит", "Геометрия", _shield),
    "squircle": Shape("squircle", "Суперэллипс", "Геометрия", _squircle),
    "burst": Shape("burst", "Вспышка", "Геометрия", _burst),
    "heart": Shape("heart", "Сердце", "Природа", _heart),
    "leaf": Shape("leaf", "Лист", "Природа", _leaf),
    "flower": Shape("flower", "Цветок", "Природа", _flower),
    "cloud": Shape("cloud", "Облако", "Природа", _cloud),
    "sun": Shape("sun", "Солнце", "Природа", _sun),
    "moon": Shape("moon", "Луна", "Природа", _moon),
    "snowflake": Shape("snowflake", "Снежинка", "Природа", _snowflake),
    "wave": Shape("wave", "Волна", "Природа", _wave),
    "drop": Shape("drop", "Капля", "Природа", _drop),
    "planet": Shape("planet", "Планета", "Природа", _planet),
    "clover": Shape("clover", "Клевер", "Природа", _clover),
    "cactus": Shape("cactus", "Кактус", "Природа", _cactus),
    "cat": Shape("cat", "Котик", "Животные", _cat),
    "bear": Shape("bear", "Медвежонок", "Животные", _bear),
    "bunny": Shape("bunny", "Зайчик", "Животные", _bunny),
    "fox": Shape("fox", "Лиса", "Животные", _fox),
    "owl": Shape("owl", "Сова", "Животные", _owl),
    "panda": Shape("panda", "Панда", "Животные", _panda),
    "fish": Shape("fish", "Рыбка", "Животные", _fish),
    "butterfly": Shape("butterfly", "Бабочка", "Животные", _butterfly),
    "paw": Shape("paw", "Лапка", "Животные", _paw),
    "ladybug": Shape("ladybug", "Божья коровка", "Животные", _ladybug),
    "turtle": Shape("turtle", "Черепаха", "Животные", _turtle),
    "penguin": Shape("penguin", "Пингвин", "Животные", _penguin),
    "frog": Shape("frog", "Лягушка", "Животные", _frog),
    "whale": Shape("whale", "Кит", "Животные", _whale),
    "crown": Shape("crown", "Корона", "Символы", _crown),
    "cup": Shape("cup", "Кубок", "Символы", _cup),
    "mask": Shape("mask", "Маска", "Символы", _mask),
    "rocket": Shape("rocket", "Ракета", "Символы", _rocket),
    "guitar": Shape("guitar", "Гитара", "Символы", _guitar),
    "speech_bubble": Shape("speech_bubble", "Пузырь чата", "Символы", _speech_bubble),
    "puzzle": Shape("puzzle", "Пазл", "Символы", _puzzle),
    "gift": Shape("gift", "Подарок", "Символы", _gift),
    "tree": Shape("tree", "Ёлка", "Символы", _tree),
    "pumpkin": Shape("pumpkin", "Тыква", "Символы", _pumpkin),
    "anchor": Shape("anchor", "Якорь", "Символы", _anchor),
    "music_note": Shape("music_note", "Нота", "Символы", _music_note),
}

SHAPE_CATEGORIES: dict[str, list[str]] = {}
for _key, _shape in SHAPES.items():
    SHAPE_CATEGORIES.setdefault(_shape.category, []).append(_key)


SHAPE_CENTERS: dict[str, tuple[float, float]] = {
    "triangle": (0.5, 0.62),
    "shield": (0.5, 0.42),
    "heart": (0.5, 0.48),
    "leaf": (0.5, 0.53),
    "cloud": (0.5, 0.62),
    "moon": (0.42, 0.55),
    "wave": (0.5, 0.55),
    "drop": (0.5, 0.54),
    "planet": (0.48, 0.46),
    "cat": (0.5, 0.55),
    "bear": (0.5, 0.54),
    "bunny": (0.5, 0.62),
    "fox": (0.5, 0.58),
    "owl": (0.5, 0.56),
    "panda": (0.5, 0.56),
    "fish": (0.42, 0.62),
    "butterfly": (0.5, 0.52),
    "paw": (0.5, 0.62),
    "ladybug": (0.5, 0.6),
    "turtle": (0.43, 0.55),
    "penguin": (0.5, 0.58),
    "crown": (0.5, 0.72),
    "mask": (0.5, 0.55),
    "rocket": (0.5, 0.55),
    "guitar": (0.36, 0.68),
    "speech_bubble": (0.5, 0.42),
    "puzzle": (0.5, 0.52),
    "gift": (0.5, 0.62),
    "tree": (0.5, 0.55),
    "pumpkin": (0.5, 0.58),
    "squircle": (0.5, 0.5),
    "burst": (0.5, 0.5),
    "clover": (0.5, 0.5),
    "cactus": (0.5, 0.55),
    "frog": (0.5, 0.55),
    "whale": (0.45, 0.58),
    "anchor": (0.5, 0.5),
    "music_note": (0.5, 0.54),
}


@lru_cache(maxsize=256)
def shape_mask(key: str, size: int, ss: int = 2) -> Image.Image:
    shape = SHAPES[key]
    big = max(size * ss, 256)
    image = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(image)
    shape.draw(draw, big)
    return image.resize((size, size), Image.Resampling.LANCZOS)


def shape_name(key: str) -> str:
    return SHAPES.get(key, SHAPES["square"]).name


def shape_keys() -> list[str]:
    return list(SHAPES)
