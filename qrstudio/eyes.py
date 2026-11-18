from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageChops, ImageDraw

from .shapes import (
    Point,
    _polygon,
    flower_points,
    heart_points,
    leaf_points,
    star_points,
)


@dataclass(frozen=True)
class EyeStyle:
    key: str
    name: str


EYE_STYLES: dict[str, EyeStyle] = {
    "square": EyeStyle("square", "Квадрат"),
    "rounded": EyeStyle("rounded", "Скруглённый"),
    "circle": EyeStyle("circle", "Круг"),
    "leaf": EyeStyle("leaf", "Лист"),
    "diamond": EyeStyle("diamond", "Ромб"),
    "star": EyeStyle("star", "Звезда"),
    "cat_eye": EyeStyle("cat_eye", "Кошачий глаз"),
    "flower": EyeStyle("flower", "Цветок"),
    "hexagon": EyeStyle("hexagon", "Шестиугольник"),
    "shield": EyeStyle("shield", "Щит"),
    "capsule": EyeStyle("capsule", "Капсула"),
    "octagon": EyeStyle("octagon", "Восьмиугольник"),
    "spark": EyeStyle("spark", "Искра"),
    "heart": EyeStyle("heart", "Сердце"),
}


def _shield_points(cx: float, cy: float, radius: float) -> list[Point]:
    return [
        (cx - radius, cy - radius),
        (cx + radius, cy - radius),
        (cx + radius, cy + radius * 0.15),
        (cx, cy + radius),
        (cx - radius, cy + radius * 0.15),
    ]


def _shape(d: ImageDraw.ImageDraw, style: str, cx: float, cy: float, radius: float, fill: int) -> None:
    if style == "square":
        d.rectangle((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill)
    elif style == "rounded":
        d.rounded_rectangle((cx - radius, cy - radius, cx + radius, cy + radius), radius=radius * 0.32, fill=fill)
    elif style == "circle":
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill)
    elif style == "leaf":
        d.polygon(_polygon(leaf_points(cx, cy, radius)), fill=fill)
    elif style == "diamond":
        d.polygon(
            _polygon(
                [
                    (cx, cy - radius),
                    (cx + radius, cy),
                    (cx, cy + radius),
                    (cx - radius, cy),
                ]
            ),
            fill=fill,
        )
    elif style == "star":
        d.polygon(_polygon(star_points(cx, cy, radius, radius * 0.44)), fill=fill)
    elif style == "cat_eye":
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill)
    elif style == "flower":
        d.polygon(_polygon(flower_points(cx, cy, radius, petals=8)), fill=fill)
    elif style == "hexagon":
        pts = [
            (cx + math.cos(math.pi / 3 * i) * radius, cy + math.sin(math.pi / 3 * i) * radius)
            for i in range(6)
        ]
        d.polygon(_polygon(pts), fill=fill)
    elif style == "shield":
        d.polygon(_polygon(_shield_points(cx, cy, radius)), fill=fill)
    elif style == "capsule":
        d.rounded_rectangle((cx - radius, cy - radius, cx + radius, cy + radius), radius=radius * 0.5, fill=fill)
    elif style == "octagon":
        cut = radius * 0.14
        d.polygon(
            _polygon(
                [
                    (cx - radius + cut, cy - radius),
                    (cx + radius - cut, cy - radius),
                    (cx + radius, cy - radius + cut),
                    (cx + radius, cy + radius - cut),
                    (cx + radius - cut, cy + radius),
                    (cx - radius + cut, cy + radius),
                    (cx - radius, cy + radius - cut),
                    (cx - radius, cy - radius + cut),
                ]
            ),
            fill=fill,
        )
    elif style == "spark":
        d.polygon(_polygon(star_points(cx, cy, radius, radius * 0.34, points=4)), fill=fill)
    elif style == "heart":
        d.polygon(_polygon(heart_points(cx, cy, radius * 0.96)), fill=fill)
    else:
        d.rectangle((cx - radius, cy - radius, cx + radius, cy + radius), fill=fill)


def _shape_variant(d: ImageDraw.ImageDraw, style: str, cx: float, cy: float, radius: float, fill: int, scale: float) -> None:
    if style == "cat_eye":
        d.ellipse(
            (
                cx - radius * 0.72 * scale,
                cy - radius * 0.92 * scale,
                cx + radius * 0.72 * scale,
                cy + radius * 0.92 * scale,
            ),
            fill=fill,
        )
    else:
        _shape(d, style, cx, cy, radius * scale, fill)


UNSAFE_EYE_STYLES = {"leaf", "star", "cat_eye", "hexagon", "heart"}


@lru_cache(maxsize=512)
def eye_sprite(style: str, cell: int) -> Image.Image:
    size = cell * 7
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    cx = cy = size / 2
    radius = size / 2
    safe_style = "rounded" if style in UNSAFE_EYE_STYLES else style
    _shape(draw, safe_style, cx, cy, radius, 255)
    _shape_variant(draw, safe_style, cx, cy, radius, 0, 5.15 / 7)
    _shape_variant(draw, safe_style, cx, cy, radius, 255, 3 / 7)
    return image


def eye_overlay_sprite(style: str, cell: int) -> Image.Image | None:
    if style not in UNSAFE_EYE_STYLES:
        return None
    size = cell * 7
    shape = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(shape)
    _shape(draw, style, size / 2, size / 2, size / 2, 255)
    inner = Image.new("L", (size, size), 0)
    ImageDraw.Draw(inner).rectangle((cell, cell, size - cell - 1, size - cell - 1), fill=255)
    return ImageChops.subtract(shape, inner)


@lru_cache(maxsize=256)
def alignment_sprite(cell: int) -> Image.Image:
    size = cell * 5
    image = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(image)
    inset = cell * 0.04
    draw.rectangle((inset, inset, size - inset, size - inset), fill=255)
    draw.rectangle((cell + inset, cell + inset, size - cell - inset, size - cell - inset), fill=0)
    draw.rectangle((cell * 2, cell * 2, cell * 3, cell * 3), fill=255)
    return image


def eye_name(key: str) -> str:
    return EYE_STYLES.get(key, EYE_STYLES["square"]).name


def eye_keys() -> list[str]:
    return list(EYE_STYLES)
