from __future__ import annotations

import math
import random
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw

Point = tuple[float, float]


@dataclass(frozen=True)
class ModuleStyle:
    key: str
    name: str
    inset: float = 0.08
    variants: int = 1


MODULE_STYLES: dict[str, ModuleStyle] = {
    "square": ModuleStyle("square", "Квадрат"),
    "rounded": ModuleStyle("rounded", "Скруглённый", 0.04),
    "dot": ModuleStyle("dot", "Точка", 0.08),
    "diamond": ModuleStyle("diamond", "Ромб", 0.06),
    "star": ModuleStyle("star", "Звезда", 0.06),
    "heart": ModuleStyle("heart", "Сердечко", 0.06),
    "paw": ModuleStyle("paw", "Лапка", 0.04),
    "hexagon": ModuleStyle("hexagon", "Шестиугольник", 0.06),
    "triangle": ModuleStyle("triangle", "Треугольник", 0.08),
    "cross": ModuleStyle("cross", "Крест", 0.1),
    "leaf": ModuleStyle("leaf", "Листик", 0.06),
    "wave": ModuleStyle("wave", "Волна", 0.02, variants=4),
    "vbar": ModuleStyle("vbar", "Вертикальные полосы", 0.06),
    "hbar": ModuleStyle("hbar", "Горизонтальные полосы", 0.06),
    "liquid": ModuleStyle("liquid", "Жидкие капли", 0.08),
    "pixel": ModuleStyle("pixel", "Пиксель", 0.14, variants=3),
    "ring": ModuleStyle("ring", "Кольцо", 0.06),
    "confetti": ModuleStyle("confetti", "Конфетти", 0.02, variants=6),
}


def _polygon(points: list[Point]) -> list[tuple[int, int]]:
    return [(round(x), round(y)) for x, y in points]


def star_points(cx: float, cy: float, outer: float, inner: float, points: int = 5, rotation: float = -math.pi / 2) -> list[Point]:
    result: list[Point] = []
    for i in range(points * 2):
        radius = outer if i % 2 == 0 else inner
        angle = rotation + i * math.pi / points
        result.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    return result


def heart_points(cx: float, cy: float, radius: float, steps: int = 32) -> list[Point]:
    raw: list[Point] = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        raw.append((x, y))
    max_x = max(abs(x) for x, _ in raw) or 1
    min_y = min(y for _, y in raw)
    max_y = max(y for _, y in raw)
    scale = (radius * 2) / max(max_x - (-max_x), max_y - min_y)
    return [
        (cx + x * scale, cy - (y - (min_y + max_y) / 2) * scale)
        for x, y in raw
    ]


def leaf_points(cx: float, cy: float, radius: float, steps: int = 36, stem: bool = True) -> list[Point]:
    pts: list[Point] = []
    width_scale = 0.66 * radius
    height = 1.72 * radius
    for i in range(steps + 1):
        t = i / steps
        width = math.sin(math.pi * t) ** 0.72
        pts.append((cx + width_scale * width, cy - radius + height * t))
    if stem:
        stem_w = 0.085 * radius
        stem_top = cy + 0.76 * radius
        stem_bottom = cy + 1.04 * radius
        pts.extend(
            [
                (cx + stem_w, stem_top),
                (cx + stem_w * 0.7, stem_bottom),
                (cx - stem_w * 0.7, stem_bottom),
                (cx - stem_w, stem_top),
            ]
        )
    for i in range(steps, -1, -1):
        t = i / steps
        width = math.sin(math.pi * t) ** 0.72
        pts.append((cx - width_scale * width, cy - radius + height * t))
    return pts


def flower_points(cx: float, cy: float, radius: float, petals: int = 6) -> list[Point]:
    pts: list[Point] = []
    count = petals * 2
    for i in range(count * 2):
        angle = i * math.pi / (count)
        wobble = 0.72 if i % 2 else 1.0
        r = radius * wobble
        pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return pts


def _draw_heart(d: ImageDraw.ImageDraw, x: float, y: float, c: float) -> None:
    inset = c * 0.06
    d.polygon(_polygon(heart_points(x + c / 2, y + c / 2 + inset * 0.5, (c - inset * 2) / 2)), fill=255)


def _draw_paw(d: ImageDraw.ImageDraw, x: float, y: float, c: float) -> None:
    pad_w = c * 0.52
    pad_h = c * 0.44
    d.ellipse((x + c * 0.24, y + c * 0.42, x + c * 0.24 + pad_w, y + c * 0.42 + pad_h), fill=255)
    toe = c * 0.2
    for dx, dy in ((0.12, 0.2), (0.32, 0.08), (0.52, 0.08), (0.72, 0.2)):
        d.ellipse((x + c * dx, y + c * dy, x + c * dx + toe, y + c * dy + toe), fill=255)


def _draw_leaf(d: ImageDraw.ImageDraw, x: float, y: float, c: float) -> None:
    d.polygon(_polygon(leaf_points(x + c / 2, y + c / 2, c * 0.43, stem=False)), fill=255)


def _draw_flower(d: ImageDraw.ImageDraw, x: float, y: float, c: float) -> None:
    d.polygon(_polygon(flower_points(x + c / 2, y + c / 2, c * 0.44)), fill=255)
    d.ellipse((x + c * 0.36, y + c * 0.36, x + c * 0.64, y + c * 0.64), fill=0)


def _draw_star(d: ImageDraw.ImageDraw, x: float, y: float, c: float) -> None:
    d.polygon(_polygon(star_points(x + c / 2, y + c / 2, c * 0.48, c * 0.2)), fill=255)


def _draw_wave(d: ImageDraw.ImageDraw, x: float, y: float, c: float, variant: int = 0) -> None:
    phase = variant * math.pi / 2
    top: list[Point] = []
    bottom: list[Point] = []
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        px = x + c * (0.04 + 0.92 * t)
        wave = math.sin(t * math.pi * 2 + phase) * c * 0.08
        top.append((px, y + c * 0.33 + wave))
        bottom.append((px, y + c * 0.67 + wave))
    d.polygon(_polygon(top + list(reversed(bottom))), fill=255)


def _draw_confetti(d: ImageDraw.ImageDraw, x: float, y: float, c: float, variant: int = 0) -> None:
    rng = random.Random(7919 + variant)
    for _ in range(3):
        w = c * rng.uniform(0.18, 0.34)
        h = c * rng.uniform(0.18, 0.34)
        px = x + rng.uniform(0.08, 0.9 - w / c) * c
        py = y + rng.uniform(0.08, 0.9 - h / c) * c
        d.rectangle((px, py, px + w, py + h), fill=255)


def _draw_pixel(d: ImageDraw.ImageDraw, x: float, y: float, c: float, variant: int = 0) -> None:
    offset = (variant - 1) * c * 0.04
    size = c * 0.62
    d.rectangle((x + (c - size) / 2 + offset, y + (c - size) / 2, x + (c + size) / 2 + offset, y + (c + size) / 2), fill=255)


def draw_module(d: ImageDraw.ImageDraw, style: str, x: float, y: float, c: float, variant: int = 0) -> None:
    inset = MODULE_STYLES.get(style, MODULE_STYLES["square"]).inset * c
    x0, y0, x1, y1 = x + inset, y + inset, x + c - inset, y + c - inset
    size = x1 - x0
    if style == "square":
        d.rectangle((x0, y0, x1, y1), fill=255)
    elif style == "rounded":
        d.rounded_rectangle((x0, y0, x1, y1), radius=size * 0.28, fill=255)
    elif style == "dot":
        d.ellipse((x0, y0, x1, y1), fill=255)
    elif style == "diamond":
        cx, cy = x + c / 2, y + c / 2
        r = size / 2
        d.polygon(_polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), fill=255)
    elif style == "star":
        _draw_star(d, x, y, c)
    elif style == "heart":
        _draw_heart(d, x, y, c)
    elif style == "paw":
        _draw_paw(d, x, y, c)
    elif style == "hexagon":
        cx, cy = x + c / 2, y + c / 2
        r = size / 2
        pts = [(cx + math.cos(math.pi / 3 * i) * r, cy + math.sin(math.pi / 3 * i) * r) for i in range(6)]
        d.polygon(_polygon(pts), fill=255)
    elif style == "triangle":
        d.polygon(_polygon([(x + c / 2, y0), (x1, y1), (x0, y1)]), fill=255)
    elif style == "cross":
        w = size * 0.34
        cx, cy = x + c / 2, y + c / 2
        d.rectangle((cx - w / 2, y0, cx + w / 2, y1), fill=255)
        d.rectangle((x0, cy - w / 2, x1, cy + w / 2), fill=255)
    elif style == "leaf":
        d.rounded_rectangle((x0, y0, x1, y1), radius=size * 0.22, fill=255)
    elif style == "wave":
        _draw_wave(d, x, y, c, variant)
    elif style == "vbar":
        d.rounded_rectangle((x + c * 0.34, y0, x + c * 0.66, y1), radius=c * 0.12, fill=255)
    elif style == "hbar":
        d.rounded_rectangle((x0, y + c * 0.34, x1, y + c * 0.66), radius=c * 0.12, fill=255)
    elif style == "liquid":
        d.ellipse((x0, y0, x1, y1), fill=255)
    elif style == "pixel":
        _draw_pixel(d, x, y, c, variant)
    elif style == "ring":
        d.ellipse((x0, y0, x1, y1), fill=255)
    elif style == "confetti":
        _draw_confetti(d, x, y, c, variant)
    elif style == "flower":
        _draw_flower(d, x, y, c)
    else:
        d.rectangle((x0, y0, x1, y1), fill=255)


MODULE_BASE_STYLES = {"leaf": "rounded", "ring": "dot"}


@lru_cache(maxsize=4096)
def module_sprite(style: str, cell: int, variant: int = 0) -> Image.Image:
    image = Image.new("L", (cell, cell), 0)
    draw = ImageDraw.Draw(image)
    draw_module(draw, MODULE_BASE_STYLES.get(style, style), 0, 0, cell, variant)
    return image


@lru_cache(maxsize=4096)
def module_overlay_sprite(style: str, cell: int, variant: int = 0) -> Image.Image | None:
    if style not in MODULE_BASE_STYLES:
        return None
    image = Image.new("L", (cell, cell), 0)
    draw = ImageDraw.Draw(image)
    if style == "leaf":
        _draw_leaf(draw, 0, 0, cell)
    elif style == "ring":
        width = max(1, round(cell * 0.14))
        inset = round(cell * 0.16)
        draw.ellipse((inset, inset, cell - inset - 1, cell - inset - 1), outline=255, width=width)
    return image


def style_name(key: str) -> str:
    return MODULE_STYLES.get(key, MODULE_STYLES["square"]).name


def style_keys() -> list[str]:
    return list(MODULE_STYLES)
