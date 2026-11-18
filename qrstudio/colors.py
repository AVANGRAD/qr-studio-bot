from __future__ import annotations

import colorsys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageOps

RGBA = tuple[int, int, int, int]
RGB = tuple[int, int, int]


@dataclass(frozen=True)
class Gradient:
    colors: tuple[RGBA, ...]
    angle: float = 0.0
    radial: bool = False

    def __post_init__(self) -> None:
        if len(self.colors) < 2:
            raise ValueError("gradient needs at least two colors")


ColorSpec = RGBA | Gradient | str


def parse_color(value: ColorSpec | None, default: RGBA = (0, 0, 0, 255)) -> RGBA:
    if value is None:
        return default
    if isinstance(value, Gradient):
        return value.colors[0]
    if isinstance(value, tuple):
        if len(value) == 3:
            return (int(value[0]), int(value[1]), int(value[2]), 255)
        if len(value) == 4:
            return tuple(int(v) for v in value)  # type: ignore[return-value]
        raise ValueError(f"invalid color tuple: {value!r}")
    text = str(value).strip()
    if not text:
        return default
    try:
        rgb = ImageColor.getrgb(text)
    except ValueError as exc:
        raise ValueError(f"invalid color: {value!r}") from exc
    if len(rgb) == 4:
        return rgb  # type: ignore[return-value]
    return (rgb[0], rgb[1], rgb[2], 255)


def to_rgb(color: RGBA) -> RGB:
    return color[0], color[1], color[2]


def with_alpha(color: RGBA, alpha: int) -> RGBA:
    return color[0], color[1], color[2], max(0, min(255, alpha))


def mix(a: RGBA, b: RGBA, t: float) -> RGBA:
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
        round(a[3] + (b[3] - a[3]) * t),
    )


def lighten(color: RGBA, amount: float = 0.2) -> RGBA:
    return mix(color, (255, 255, 255, color[3]), amount)


def darken(color: RGBA, amount: float = 0.2) -> RGBA:
    return mix(color, (0, 0, 0, color[3]), amount)


def _linear_channel(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: RGBA) -> float:
    r, g, b = (c / 255.0 for c in color[:3])
    return 0.2126 * _linear_channel(r) + 0.7152 * _linear_channel(g) + 0.0722 * _linear_channel(b)


def contrast_ratio(a: RGBA, b: RGBA) -> float:
    la = relative_luminance(a)
    lb = relative_luminance(b)
    if la < lb:
        la, lb = lb, la
    return (la + 0.05) / (lb + 0.05)


def ensure_contrast(
    fg: RGBA,
    bg: RGBA,
    min_ratio: float = 4.5,
    prefer_dark_fg: bool = True,
) -> tuple[RGBA, RGBA]:
    if prefer_dark_fg and relative_luminance(fg) > relative_luminance(bg):
        fg, bg = bg, fg
    if contrast_ratio(fg, bg) >= min_ratio:
        return fg, bg
    original_bg = bg
    for step in range(1, 21):
        t = step / 20
        candidate_fg = mix(fg, (0, 0, 0, fg[3]), t * 0.9)
        candidate_bg = mix(original_bg, (255, 255, 255, bg[3]), t * 0.9)
        if contrast_ratio(candidate_fg, candidate_bg) >= min_ratio:
            return candidate_fg, candidate_bg
    return (0, 0, 0, 255), (255, 255, 255, 255)


def _gradient_gray(size: int, angle: float, radial: bool) -> Image.Image:
    if radial:
        gray = Image.radial_gradient("L")
        return gray.resize((size, size), Image.Resampling.BICUBIC)
    gray = Image.linear_gradient("L")
    base = gray.resize((max(size * 2, 512), max(size * 2, 512)), Image.Resampling.BICUBIC)
    rotated = base.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    left = (rotated.width - size) // 2
    top = (rotated.height - size) // 2
    return rotated.crop((left, top, left + size, top + size))


def _colorize_stops(gray: Image.Image, colors: Sequence[RGBA]) -> Image.Image:
    if len(colors) == 2:
        rgb = ImageOps.colorize(gray.convert("L"), to_rgb(colors[0]), to_rgb(colors[1]))
    else:
        mid = 128
        lo = gray.point(lambda v: min(255, v * 2))
        hi = gray.point(lambda v: max(0, (v - mid) * 2))
        c0 = ImageOps.colorize(lo, to_rgb(colors[0]), to_rgb(colors[1]))
        c1 = ImageOps.colorize(hi, to_rgb(colors[1]), to_rgb(colors[-1]))
        mask = gray.point(lambda v: 255 if v >= mid else 0)
        rgb = Image.composite(c1, c0, mask)
    alpha = round(sum(c[3] for c in colors) / len(colors))
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def gradient_image(size: int, spec: Gradient) -> Image.Image:
    gray = _gradient_gray(size, spec.angle, spec.radial)
    return _colorize_stops(gray, spec.colors)


def color_image(size: int, spec: ColorSpec) -> Image.Image:
    if isinstance(spec, Gradient):
        return gradient_image(size, spec)
    color = parse_color(spec)
    return Image.new("RGBA", (size, size), color)


def colorize_mask(mask: Image.Image, spec: ColorSpec, size: int | None = None) -> Image.Image:
    if size is None:
        size = mask.width
    base = color_image(size, spec)
    if base.size != mask.size:
        base = base.resize(mask.size, Image.Resampling.BICUBIC)
    alpha = mask.convert("L")
    if base.getchannel("A").getextrema()[0] < 255:
        alpha = ImageChops.multiply(alpha, base.getchannel("A"))
    base.putalpha(alpha)
    return base


def accent_colors(spec: ColorSpec, count: int = 4) -> list[RGBA]:
    if isinstance(spec, Gradient):
        colors = list(spec.colors)
        if len(colors) >= count:
            return colors[:count]
        while len(colors) < count:
            colors.append(mix(colors[-1], colors[-2], 0.5))
        return colors[:count]
    base = parse_color(spec)
    variants = [
        base,
        mix(base, (255, 255, 255, 255), 0.35),
        mix(base, (0, 0, 0, 255), 0.35),
        mix(base, (255, 255, 255, 255), 0.6),
    ]
    return variants[:count]


def extract_palette(image: Image.Image, count: int = 6) -> list[RGBA]:
    img = image.convert("RGBA")
    img.thumbnail((256, 256))
    background = Image.new("RGBA", img.size, (255, 255, 255, 0))
    img = Image.alpha_composite(background, img).convert("RGB")
    quantized = img.quantize(colors=max(4, count), method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette() or []
    color_counts = quantized.getcolors() or []
    ranked: list[tuple[float, RGBA]] = []
    for amount, index in color_counts:
        if index * 3 + 2 >= len(palette):
            continue
        r, g, b = palette[index * 3 : index * 3 + 3]
        color = (r, g, b, 255)
        _, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if v < 0.08 or v > 0.97:
            continue
        score = amount * (0.2 + s) * (0.5 + abs(v - 0.5))
        ranked.append((score, color))
    ranked.sort(key=lambda item: item[0], reverse=True)
    result: list[RGBA] = []
    for _, color in ranked:
        if all(contrast_ratio(color, other) > 1.15 for other in result):
            result.append(color)
        if len(result) >= count:
            break
    if not result:
        result = [(30, 30, 30, 255), (120, 120, 120, 255), (240, 240, 240, 255)]
    return result


def palette_gradient(colors: Iterable[RGBA], angle: float = 0.0, radial: bool = False) -> Gradient:
    values = tuple(colors)
    if len(values) < 2:
        values = (values[0] if values else (0, 0, 0, 255), (255, 255, 255, 255))
    return Gradient(values[:3], angle=angle, radial=radial)


def contrast_report(fg: ColorSpec, bg: ColorSpec) -> dict[str, float | bool]:
    fg_colors = list(fg.colors) if isinstance(fg, Gradient) else [parse_color(fg)]
    bg_colors = list(bg.colors) if isinstance(bg, Gradient) else [parse_color(bg)]
    worst = min(contrast_ratio(f, b) for f in fg_colors for b in bg_colors)
    return {"ratio": worst, "ok": worst >= 4.5}


def draw_checkerboard(size: int, cell: int = 16, a: RGBA = (235, 235, 235, 255), b: RGBA = (255, 255, 255, 255)) -> Image.Image:
    img = Image.new("RGBA", (size, size), a)
    draw = ImageDraw.Draw(img)
    for y in range(0, size, cell):
        for x in range(0, size, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=b)
    return img
