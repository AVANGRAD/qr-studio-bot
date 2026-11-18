from __future__ import annotations

from dataclasses import dataclass, field

from .colors import ColorSpec, Gradient

WHITE = (255, 255, 255, 255)
BLACK = (17, 17, 17, 255)


@dataclass(frozen=True)
class Palette:
    key: str
    name: str
    fg: ColorSpec
    bg: ColorSpec = WHITE
    accent: ColorSpec | None = None
    shape: ColorSpec | None = None
    shape_accent: ColorSpec | None = None
    outer_bg: ColorSpec = WHITE


@dataclass(frozen=True)
class Preset:
    key: str
    name: str
    shape: str
    module_style: str
    eye_style: str
    palette: str
    logo_mode: str = "plate"
    tags: tuple[str, ...] = field(default_factory=tuple)


PALETTES: dict[str, Palette] = {
    "mono": Palette("mono", "Чёрно-белый", "#101010", "#FFFFFF", "#101010", "#101010", "#6B6B6B"),
    "gold": Palette(
        "gold", "Золото", "#5C4314", "#FFF9EC", "#C9A227",
        Gradient(((201, 162, 39, 255), (122, 92, 24, 255)), angle=35),
        "#F3E2A0",
    ),
    "red": Palette(
        "red", "Красный halftone", "#A50F2D", "#FFF4F1", "#E63946",
        Gradient(((179, 18, 46, 255), (110, 8, 28, 255)), angle=30), "#FFB4A8",
    ),
    "blue": Palette(
        "blue", "Синие точки", "#0B4F9C", "#F3F9FF", "#2D7DD2",
        Gradient(((45, 125, 210, 255), (11, 79, 156, 255)), angle=25), "#A7D3F5",
    ),
    "purple": Palette(
        "purple", "Фиолетовая мозаика", "#4B1766", "#FBF4FF", "#9B5DE5",
        Gradient(((155, 93, 229, 255), (75, 23, 102, 255)), angle=40), "#D9B8FF",
    ),
    "green": Palette(
        "green", "Зелёные листья", "#1B5E20", "#F4FBF3", "#4CAF50",
        Gradient(((76, 175, 80, 255), (27, 94, 32, 255)), angle=35), "#B7DFB8",
    ),
    "magenta": Palette(
        "magenta", "Маджента", "#A30063", "#FFF0F8", "#FF4FA3",
        Gradient(((255, 79, 163, 255), (163, 0, 99, 255)), angle=20), "#FFC1E0",
    ),
    "navy": Palette(
        "navy", "Тёмно-синий", "#0A1F44", "#F2F6FF", "#1E3A8A",
        Gradient(((30, 58, 138, 255), (10, 31, 68, 255)), angle=45), "#8FA9D9",
    ),
    "khaki": Palette(
        "khaki", "Хаки", "#3F471B", "#F8F7ED", "#7C8445",
        Gradient(((108, 116, 61, 255), (63, 71, 27, 255)), angle=30), "#C9CFA0",
    ),
    "orange": Palette(
        "orange", "Оранжевый градиент", "#9E3300", "#FFF7EF", "#FF7A00",
        Gradient(((255, 158, 44, 255), (230, 81, 0, 255)), angle=35), "#FFD0A3",
    ),
    "neon": Palette(
        "neon", "Неон", "#081018", "#F0FFF9", "#00E5A8",
        Gradient(((0, 229, 168, 255), (0, 179, 255, 255)), angle=30), "#8CFFF0",
    ),
    "watercolor": Palette(
        "watercolor", "Акварель", "#3A2E5C", "#FFF9F2",
        Gradient(((244, 162, 97, 255), (231, 111, 81, 255), (42, 157, 143, 255)), angle=20),
        Gradient(((123, 108, 168, 255), (244, 162, 97, 255)), angle=40), "#FFE0C2",
    ),
    "metal": Palette(
        "metal", "Металл", "#2B2F36", "#F4F6F8",
        Gradient(((154, 164, 178, 255), (229, 233, 240, 255), (107, 114, 128, 255)), angle=45),
        Gradient(((107, 114, 128, 255), (43, 47, 54, 255)), angle=30), "#D7DCE5",
    ),
    "wood": Palette(
        "wood", "Дерево", "#3E2723", "#FFF8F0", "#8D6E63",
        Gradient(((161, 136, 127, 255), (78, 52, 46, 255)), angle=25), "#D7BFA8",
    ),
    "pastel": Palette(
        "pastel", "Пастель", "#5C4B8A", "#FFFDF7",
        Gradient(((247, 178, 217, 255), (167, 216, 240, 255), (184, 224, 176, 255)), angle=20),
        Gradient(((247, 178, 217, 255), (167, 216, 240, 255)), angle=35), "#EADFF5",
    ),
}


PRESETS: dict[str, Preset] = {
    "gold_leaf": Preset("gold_leaf", "Золотой лист", "leaf", "leaf", "leaf", "gold", tags=("элегантный", "природа")),
    "red_halftone": Preset("red_halftone", "Красный halftone", "square", "dot", "circle", "red", tags=("как на фото", "контраст")),
    "blue_dots": Preset("blue_dots", "Синие точки", "square", "dot", "circle", "blue", tags=("как на фото", "чистый")),
    "purple_mosaic": Preset("purple_mosaic", "Фиолетовая мозаика", "rounded", "rounded", "rounded", "purple", tags=("как на фото", "мягкий")),
    "green_leaves": Preset("green_leaves", "Зелёные листья", "leaf", "leaf", "leaf", "green", tags=("как на фото", "эко")),
    "magenta": Preset("magenta", "Маджента", "square", "heart", "flower", "magenta", tags=("как на фото", "яркий")),
    "navy": Preset("navy", "Navy squares", "square", "square", "square", "navy", tags=("как на фото", "строгий")),
    "khaki": Preset("khaki", "Хаки", "shield", "pixel", "square", "khaki", tags=("как на фото", "милитари")),
    "orange": Preset("orange", "Оранжевый градиент", "rounded", "rounded", "rounded", "orange", tags=("как на фото", "тёплый")),
    "neon": Preset("neon", "Неон", "square", "diamond", "diamond", "neon", tags=("яркий", "техно")),
    "watercolor": Preset("watercolor", "Акварель", "flower", "dot", "flower", "watercolor", tags=("нежный", "арт")),
    "metal": Preset("metal", "Металл", "shield", "hexagon", "hexagon", "metal", tags=("строгий", "премиум")),
    "wood": Preset("wood", "Дерево", "square", "vbar", "square", "wood", tags=("эко", "тёплый")),
    "pastel": Preset("pastel", "Пастель", "heart", "heart", "flower", "pastel", tags=("нежный", "подарок")),
    "cat": Preset("cat", "Котик", "cat", "paw", "cat_eye", "pastel", tags=("животные", "милый")),
    "panda": Preset("panda", "Панда", "panda", "dot", "circle", "mono", tags=("животные", "милый")),
    "rocket": Preset("rocket", "Ракета", "rocket", "triangle", "star", "navy", tags=("символы", "запуск")),
    "gift": Preset("gift", "Подарок", "gift", "confetti", "flower", "red", tags=("праздник", "яркий")),
}


def get_palette(key: str) -> Palette:
    return PALETTES.get(key, PALETTES["mono"])


def get_preset(key: str) -> Preset:
    return PRESETS.get(key, PRESETS["blue_dots"])


def palette_keys() -> list[str]:
    return list(PALETTES)


def preset_keys() -> list[str]:
    return list(PRESETS)
