from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PIL import Image

from .colors import color_image
from .masks import shape_mask


@dataclass(frozen=True)
class Emblem:
    key: str
    name: str
    shape: str
    color: tuple[int, int, int, int]


EMBLEMS: dict[str, Emblem] = {
    "heart": Emblem("heart", "Сердце", "heart", (214, 38, 76, 255)),
    "star": Emblem("star", "Звезда", "star5", (244, 180, 0, 255)),
    "crown": Emblem("crown", "Корона", "crown", (201, 162, 39, 255)),
    "leaf": Emblem("leaf", "Лист", "leaf", (46, 125, 50, 255)),
    "paw": Emblem("paw", "Лапка", "paw", (141, 90, 59, 255)),
    "rocket": Emblem("rocket", "Ракета", "rocket", (40, 53, 147, 255)),
    "flower": Emblem("flower", "Цветок", "flower", (216, 27, 96, 255)),
    "moon": Emblem("moon", "Луна", "moon", (57, 73, 171, 255)),
    "planet": Emblem("planet", "Планета", "planet", (0, 137, 123, 255)),
    "shield": Emblem("shield", "Щит", "shield", (55, 71, 79, 255)),
    "music_note": Emblem("music_note", "Нота", "music_note", (123, 31, 162, 255)),
    "anchor": Emblem("anchor", "Якорь", "anchor", (21, 101, 192, 255)),
}


@lru_cache(maxsize=64)
def emblem_image(key: str, size: int = 512) -> Image.Image:
    emblem = EMBLEMS.get(key, EMBLEMS["star"])
    inner = max(64, int(size * 0.86))
    mask = shape_mask(emblem.shape, inner, ss=2)
    icon = color_image(inner, emblem.color)
    icon.putalpha(mask)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset = (size - inner) // 2
    canvas.alpha_composite(icon, (offset, offset))
    return canvas


def emblem_name(key: str) -> str:
    return EMBLEMS.get(key, EMBLEMS["star"]).name


def emblem_keys() -> list[str]:
    return list(EMBLEMS)
