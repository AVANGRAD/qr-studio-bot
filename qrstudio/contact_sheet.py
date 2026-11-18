from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PIL import Image, ImageDraw

from .eyes import eye_keys, eye_name
from .logo import font
from .masks import SHAPE_CATEGORIES, shape_name
from .presets import get_palette, palette_keys
from .render import RenderOptions, render
from .shapes import MODULE_STYLES, style_name

LABEL_HEIGHT = 46
BG = (246, 247, 249, 255)


def _label(draw: ImageDraw.ImageDraw, x: int, y: int, title: str, subtitle: str) -> None:
    draw.text((x + 10, y + 3), title, font=font(19), fill=(20, 22, 26, 255))
    draw.text((x + 10, y + 25), subtitle, font=font(13), fill=(105, 110, 120, 255))


def _sheet(
    keys: list[str],
    path: str | Path,
    title_for: Callable[[str], str],
    subtitle_for: Callable[[str, object], str],
    make_options: Callable[[str], RenderOptions],
    size: int = 300,
    columns: int = 8,
) -> Path:
    rows = (len(keys) + columns - 1) // columns
    tile = size + LABEL_HEIGHT
    margin = 14
    gap = 12
    width = margin * 2 + columns * tile + (columns - 1) * gap
    height = margin * 2 + rows * tile + (rows - 1) * gap
    sheet = Image.new("RGBA", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    for index, key in enumerate(keys):
        row, column = divmod(index, columns)
        left = margin + column * (tile + gap)
        top = margin + row * (tile + gap)
        result = render(make_options(key))
        tile_img = Image.new("RGBA", (size + 12, size + 12), (255, 255, 255, 255))
        tile_img.alpha_composite(result.image.resize((size, size), Image.Resampling.LANCZOS), (6, 6))
        sheet.alpha_composite(tile_img, (left, top))
        _label(draw, left, top + size + 12, title_for(key), subtitle_for(key, result))
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(out, quality=92)
    return out


def shape_sheet(path: str | Path = "assets/previews/shapes.png", size: int = 300) -> Path:
    keys = [key for category in SHAPE_CATEGORIES.values() for key in category]
    return _sheet(
        keys,
        path,
        lambda key: shape_name(key),
        lambda key, result: f"{key} · v{result.qr.version} · {result.module_px:.1f}px",
        lambda key: RenderOptions(content="https://example.com", size=size, shape=key, module_style="dot", eye_style="circle", palette="blue"),
        size=size,
        columns=8,
    )


def module_sheet(path: str | Path = "assets/previews/modules.png", size: int = 300) -> Path:
    return _sheet(
        list(MODULE_STYLES),
        path,
        lambda key: style_name(key),
        lambda key, result: key,
        lambda key: RenderOptions(content="https://example.com", size=size, shape="square", module_style=key, eye_style="circle", palette="navy"),
        size=size,
        columns=6,
    )


def eye_sheet(path: str | Path = "assets/previews/eyes.png", size: int = 300) -> Path:
    return _sheet(
        eye_keys(),
        path,
        lambda key: eye_name(key),
        lambda key, result: key,
        lambda key: RenderOptions(content="https://example.com", size=size, shape="square", module_style="dot", eye_style=key, palette="purple"),
        size=size,
        columns=5,
    )


def palette_sheet(path: str | Path = "assets/previews/palettes.png", size: int = 300) -> Path:
    return _sheet(
        palette_keys(),
        path,
        lambda key: get_palette(key).name,
        lambda key, result: key,
        lambda key: RenderOptions(content="https://example.com", size=size, shape="rounded", module_style="rounded", eye_style="rounded", palette=key),
        size=size,
        columns=5,
    )
