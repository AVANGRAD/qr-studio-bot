from __future__ import annotations

import base64
import html
import io
import math
from dataclasses import dataclass, field, replace
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from . import colors as C
from .colors import (
    ColorSpec,
    Gradient,
    color_image,
    colorize_mask,
    mix,
    parse_color,
)
from .core import ALIGNMENT_TYPES, FINDER_TYPES, QR, make_qr
from .eyes import alignment_sprite, eye_keys, eye_overlay_sprite, eye_sprite
from .logo import dilate_alpha, mean_luminance, monogram_image, outline
from .masks import SHAPE_CENTERS, SHAPES, shape_mask, shape_name
from .presets import Palette, get_palette
from .shapes import MODULE_STYLES, module_overlay_sprite, module_sprite


@dataclass
class RenderOptions:
    content: str
    shape: str = "square"
    module_style: str = "rounded"
    eye_style: str = "rounded"
    palette: str = "mono"
    fg: ColorSpec | None = None
    bg: ColorSpec | None = None
    accent: ColorSpec | None = None
    shape_color: ColorSpec | None = None
    outer_bg: ColorSpec | None = None
    size: int = 1024
    border: int = 4
    error: str | None = None
    margin: float = 0.08
    frame: bool | None = None
    silhouette: bool = False
    photo: Image.Image | None = None
    photo_card: float = 0.42
    photo_inset: float = 0.055
    photo_opacity: int = 244
    transparent: bool = False
    logo: Image.Image | None = None
    logo_mode: str = "plate"
    logo_size: float = 0.2
    logo_text: str = "QR"
    logo_mono: bool = False
    logo_plate_color: ColorSpec | None = None
    shadow: bool = True
    safe_mode: bool = True
    dpi: int = 300
    seed: int = 0
    scan_check: bool = False

    def normalized(self) -> RenderOptions:
        size = max(256, min(4096, int(self.size)))
        border = max(0, min(8, int(self.border)))
        logo_size = max(0.08, min(0.26, float(self.logo_size)))
        margin = max(0.02, min(0.2, float(self.margin)))
        photo_card = max(0.32, min(0.54, float(self.photo_card)))
        photo_inset = max(0.02, min(0.12, float(self.photo_inset)))
        photo_opacity = max(160, min(255, int(self.photo_opacity)))
        return replace(
            self,
            size=size,
            border=border,
            logo_size=logo_size,
            margin=margin,
            photo_card=photo_card,
            photo_inset=photo_inset,
            photo_opacity=photo_opacity,
        )


@dataclass
class RenderResult:
    image: Image.Image
    qr: QR
    options: RenderOptions
    palette: Palette
    warnings: list[str] = field(default_factory=list)
    fallback: bool = False
    module_px: float = 0.0
    contrast: float = 0.0
    masked: bool = False
    photo: bool = False
    qr_box: tuple[int, int, int, int] = (0, 0, 0, 0)
    final_qr_fg: ColorSpec | None = None
    final_qr_bg: ColorSpec | None = None


def _spec_colors(spec: ColorSpec) -> list[C.RGBA]:
    if isinstance(spec, Gradient):
        return list(spec.colors)
    return [parse_color(spec)]


def _adjust_spec(spec: ColorSpec, toward: C.RGBA, amount: float) -> ColorSpec:
    if isinstance(spec, Gradient):
        return Gradient(tuple(mix(color, toward, amount) for color in spec.colors), spec.angle, spec.radial)
    return mix(parse_color(spec), toward, amount)


def _contrast_spec(fg: ColorSpec, bg: ColorSpec, minimum: float = 4.5) -> tuple[ColorSpec, ColorSpec, float]:
    worst = min(C.contrast_ratio(f, b) for f in _spec_colors(fg) for b in _spec_colors(bg))
    if worst >= minimum:
        return fg, bg, worst
    for step in range(1, 21):
        t = step / 20
        candidate_fg = _adjust_spec(fg, (0, 0, 0, 255), t * 0.9)
        candidate_bg = _adjust_spec(bg, (255, 255, 255, 255), t * 0.9)
        ratio = min(C.contrast_ratio(f, b) for f in _spec_colors(candidate_fg) for b in _spec_colors(candidate_bg))
        if ratio >= minimum:
            return candidate_fg, candidate_bg, ratio
    return (0, 0, 0, 255), (255, 255, 255, 255), C.contrast_ratio((0, 0, 0, 255), (255, 255, 255, 255))


def _fit_plate(shape: str, max_scale: float | None = None, min_scale: float = 0.3, pad: float = 0.015) -> tuple[float, tuple[float, float]]:
    center = SHAPE_CENTERS.get(shape, (0.5, 0.5))
    if shape == "square":
        return 0.92, center
    if max_scale is None:
        category = SHAPES.get(shape).category if shape in SHAPES else ""
        max_scale = 0.60 if category == "Животные" else 0.66
    probe = shape_mask(shape, 384, ss=2)
    pixels = probe.load()
    size = probe.width
    cx, cy = center[0] * size, center[1] * size

    def inside(scale: float) -> bool:
        half = scale * size / 2
        if half <= 0:
            return False
        points: list[tuple[float, float]] = []
        for t in (x / 12 for x in range(13)):
            points.append((cx - half + 2 * half * t, cy - half))
            points.append((cx - half + 2 * half * t, cy + half))
            points.append((cx - half, cy - half + 2 * half * t))
            points.append((cx + half, cy - half + 2 * half * t))
        for x, y in points:
            if not (0 <= x < size and 0 <= y < size):
                return False
            if pixels[round(x), round(y)] < 200:
                return False
        return True

    low, high = min_scale, max_scale
    if not inside(low):
        return min_scale, center
    for _ in range(18):
        mid = (low + high) / 2
        if inside(mid):
            low = mid
        else:
            high = mid
    return max(min_scale, low - pad), center


def _finder_coverage(mask: Image.Image, qr: QR, x0: int, y0: int, cell: float) -> float:
    points = 0
    inside = 0
    for rx, ry in qr.finder_regions():
        for yy in range(7):
            for xx in range(7):
                px = round(x0 + (rx + xx + 0.5) * cell)
                py = round(y0 + (ry + yy + 0.5) * cell)
                points += 1
                if 0 <= px < mask.width and 0 <= py < mask.height and mask.getpixel((px, py)) > 200:
                    inside += 1
    return inside / points if points else 0.0


def _data_coverage(mask: Image.Image, qr: QR, x0: int, y0: int, cell: float) -> float:
    total = 0
    inside = 0
    for x, y in qr.dark_modules():
        if qr.module_type(x, y) in FINDER_TYPES or qr.module_type(x, y) in ALIGNMENT_TYPES:
            continue
        px = round(x0 + (x + 0.5) * cell)
        py = round(y0 + (y + 0.5) * cell)
        total += 1
        if 0 <= px < mask.width and 0 <= py < mask.height and mask.getpixel((px, py)) > 160:
            inside += 1
    return inside / total if total else 1.0


def _safe_in_mask(mask: Image.Image, qr: QR, cell: float, x0: int, y0: int) -> tuple[bool, float, float]:
    finder = _finder_coverage(mask, qr, x0, y0, cell)
    data = _data_coverage(mask, qr, x0, y0, cell)
    return finder >= 0.995 and data >= 0.78, finder, data


def silhouette_safe(shape: str, qr: QR, canvas: int, cell: float, x0: int, y0: int) -> tuple[bool, float, float]:
    return _safe_in_mask(shape_mask(shape, canvas, ss=2), qr, cell, x0, y0)


def _draw_shape_decor(canvas: Image.Image, shape: str, size: int, accent: C.RGBA, mask: Image.Image) -> None:
    if shape not in {"cat", "bear", "bunny", "gift", "crown", "tree", "ladybug", "turtle"}:
        return
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    s = size
    color = accent
    if shape == "cat":
        draw.polygon([(s * 0.16, s * 0.3), (s * 0.15, s * 0.09), (s * 0.35, s * 0.2)], fill=color)
        draw.polygon([(s * 0.84, s * 0.3), (s * 0.85, s * 0.09), (s * 0.65, s * 0.2)], fill=color)
    elif shape == "bear":
        draw.ellipse((s * 0.15, s * 0.13, s * 0.27, s * 0.25), fill=color)
        draw.ellipse((s * 0.73, s * 0.13, s * 0.85, s * 0.25), fill=color)
    elif shape == "bunny":
        draw.ellipse((s * 0.28, s * 0.06, s * 0.37, s * 0.4), fill=color)
        draw.ellipse((s * 0.63, s * 0.06, s * 0.72, s * 0.4), fill=color)
    elif shape == "gift":
        draw.rectangle((s * 0.43, s * 0.22, s * 0.57, s * 0.94), fill=color)
        draw.rectangle((s * 0.08, s * 0.5, s * 0.92, s * 0.62), fill=color)
    elif shape == "crown":
        for cx in (0.1, 0.3, 0.5, 0.7, 0.9):
            draw.ellipse((s * (cx - 0.028), s * 0.4, s * (cx + 0.028), s * 0.456), fill=color)
    elif shape == "tree":
        draw.polygon([(s * 0.5, s * 0.02), (s * 0.56, s * 0.1), (s * 0.5, s * 0.18), (s * 0.44, s * 0.1)], fill=color)
    elif shape == "ladybug":
        for cx, cy in ((0.24, 0.38), (0.76, 0.38), (0.22, 0.72), (0.78, 0.72)):
            draw.ellipse((s * (cx - 0.04), s * (cy - 0.04), s * (cx + 0.04), s * (cy + 0.04)), fill=color)
    elif shape == "turtle":
        draw.arc((s * 0.18, s * 0.28, s * 0.74, s * 0.8), 0, 360, fill=color, width=max(2, round(s * 0.01)))
    canvas.alpha_composite(layer)


def _rounded_layer(size: int, box: tuple[float, float, float, float], color: C.RGBA, radius: float, outline_color: C.RGBA | None = None, outline_width: int = 0) -> Image.Image:
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(box, radius=radius, fill=color)
    if outline_color and outline_width:
        draw.rounded_rectangle(box, radius=radius, outline=outline_color, width=outline_width)
    return layer


def _shadow_layer(size: int, mask: Image.Image, alpha: int = 70, blur: int = 8, offset: tuple[int, int] = (0, 6)) -> Image.Image:
    blur = max(1, blur)
    shadow = mask.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow = shadow.point(lambda v: int(v * alpha / 255))
    layer.putalpha(shadow)
    shifted = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shifted.alpha_composite(layer, dest=(max(0, offset[0]), max(0, offset[1])))
    return shifted


def _logo_plate(canvas: Image.Image, options: RenderOptions, qr_box: tuple[int, int, int, int], qr_fg: C.RGBA, qr_bg: C.RGBA) -> None:
    logo = options.logo
    if logo is None and options.logo_mode != "monogram":
        return
    x0, y0, x1, y1 = qr_box
    qr_px = x1 - x0
    if options.logo_mode == "corner":
        logo_size = max(24, int(qr_px * min(options.logo_size, 0.105)))
    else:
        logo_size = max(24, int(qr_px * options.logo_size))
    logo_size = min(logo_size, int(qr_px * 0.25))
    is_badge = options.logo_mode == "badge"
    if options.logo_mode == "monogram":
        logo_img = monogram_image(options.logo_text or "QR", logo_size, qr_fg, (0, 0, 0, 0))
    else:
        logo_img = logo.copy()
        logo_img.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        if options.logo_mono:
            from .logo import monochrome

            logo_img = monochrome(logo_img, qr_fg)
    plate_size = int(logo_size * (1.2 if options.logo_mode == "corner" else (1.4 if is_badge else 1.32)))
    if options.logo_mode == "corner":
        margin = max(8, int(qr_px * 0.02))
        left = x1 - plate_size - margin
        top = y1 - plate_size - margin
    else:
        left = x0 + (qr_px - plate_size) // 2
        top = y0 + (qr_px - plate_size) // 2
    bright = mean_luminance(logo_img) > 0.72
    plate_color = parse_color(options.logo_plate_color, default=qr_bg)
    if bright and options.logo_plate_color is None:
        plate_color = qr_fg
    plate_box = (left, top, left + plate_size, top + plate_size)
    radius = plate_size / 2 if is_badge else plate_size * (0.28 if options.logo_mode != "corner" else 0.22)
    shadow = Image.new("RGBA", (canvas.width, canvas.height), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_box = (
        left + 2,
        top + max(2, canvas.width // 400),
        left + plate_size + 2,
        top + plate_size + max(2, canvas.width // 400),
    )
    if is_badge:
        shadow_draw.ellipse(shadow_box, fill=(0, 0, 0, 70))
    else:
        shadow_draw.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, canvas.width // 350)))
    canvas.alpha_composite(shadow)
    plate = _rounded_layer(
        canvas.width,
        plate_box,
        plate_color,
        radius,
        outline_color=mix(plate_color, qr_fg, 0.22) if plate_color == qr_bg else mix(plate_color, (0, 0, 0, 255), 0.12),
        outline_width=max(1, canvas.width // 700),
    )
    canvas.alpha_composite(plate)
    paste_x = left + (plate_size - logo_img.width) // 2
    paste_y = top + (plate_size - logo_img.height) // 2
    canvas.alpha_composite(logo_img, (paste_x, paste_y))


def _texture_fill(logo: Image.Image, size: int, qr_fg: C.RGBA, qr_bg: C.RGBA) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), qr_bg)
    scaled = logo.copy()
    scaled.thumbnail((size, size), Image.Resampling.LANCZOS)
    x = (size - scaled.width) // 2
    y = (size - scaled.height) // 2
    canvas.alpha_composite(scaled, (x, y))
    gray = ImageOps.grayscale(canvas)
    gray = ImageOps.autocontrast(gray)
    light, _, _ = _contrast_spec(mix(qr_fg, qr_bg, 0.42), qr_bg, 4.8)
    light_rgba = parse_color(light)
    result = ImageOps.colorize(gray, qr_fg[:3], light_rgba[:3]).convert("RGBA")
    overlay = Image.new("RGBA", (size, size), qr_fg[:3] + (28,))
    result.alpha_composite(overlay)
    return result


def _apply_texture(mask: Image.Image, texture: Image.Image) -> Image.Image:
    result = texture.copy()
    result.putalpha(mask.convert("L"))
    return result


def _photo_canvas(photo: Image.Image, size: int) -> Image.Image:
    source = photo.convert("RGB")
    background = ImageOps.fit(source, (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    background = background.filter(ImageFilter.GaussianBlur(max(2, size // 80)))
    background = ImageEnhance.Brightness(background).enhance(0.64)
    foreground = ImageOps.contain(source, (size, size), method=Image.Resampling.LANCZOS)
    canvas = background.convert("RGBA")
    canvas.alpha_composite(foreground.convert("RGBA"), ((size - foreground.width) // 2, (size - foreground.height) // 2))
    return canvas


def render(options: RenderOptions) -> RenderResult:
    opts = options.normalized()
    warnings: list[str] = []
    fallback = False
    pal = get_palette(opts.palette)
    fg_spec: ColorSpec = opts.fg if opts.fg is not None else pal.fg
    bg_spec: ColorSpec = opts.bg if opts.bg is not None else pal.bg
    accent_spec: ColorSpec = opts.accent if opts.accent is not None else (pal.accent or fg_spec)
    shape_spec: ColorSpec = opts.shape_color if opts.shape_color is not None else (pal.shape or fg_spec)
    outer_spec: ColorSpec = opts.outer_bg if opts.outer_bg is not None else pal.outer_bg
    qr_fg_spec, qr_bg_spec, contrast = _contrast_spec(fg_spec, bg_spec)
    qr_fg = parse_color(qr_fg_spec)
    qr_bg = parse_color(qr_bg_spec)
    eye_spec = accent_spec
    if C.contrast_ratio(parse_color(eye_spec), qr_bg) < 3.5:
        eye_spec = qr_fg_spec
    eye_color = parse_color(eye_spec)

    photo_mode = opts.photo is not None
    silhouette = opts.silhouette and opts.shape != "square" and not photo_mode
    frame = opts.frame if opts.frame is not None else (opts.shape != "square" and not silhouette)
    if opts.shape == "square" and opts.frame is None:
        frame = False
    if photo_mode:
        frame = False
    error = opts.error or ("h" if (opts.logo is not None or silhouette) else "m")
    qr = make_qr(opts.content, error=error, border=opts.border)
    n = qr.size

    S = opts.size
    ss = 2 if S <= 1024 else 1
    W = S * ss
    p_scale, center = _fit_plate(opts.shape) if (frame or silhouette) else (0.92, (0.5, 0.5))
    if photo_mode:
        card = W * opts.photo_card
        cell = max(2, int((card * 0.86) // n))
        qr_px = cell * n
        card = qr_px / 0.86
        margin = round(W * opts.photo_inset)
        card_x1 = W - margin
        card_y1 = W - margin
        card_x0 = card_x1 - card
        card_y0 = card_y1 - card
        qr_x0 = round(card_x0 + (card - qr_px) / 2)
        qr_y0 = round(card_y0 + (card - qr_px) / 2)
        plate_px = card
        plate_box = (card_x0, card_y0, card_x1, card_y1)
    elif frame:
        plate_target = p_scale * W
        cell = max(2, int((plate_target * 0.86) // n))
        qr_px = cell * n
        plate_px = qr_px / 0.86
        cx, cy = center[0] * W, center[1] * W
        qr_x0 = round(cx - qr_px / 2)
        qr_y0 = round(cy - qr_px / 2)
        plate_box = (cx - plate_px / 2, cy - plate_px / 2, cx + plate_px / 2, cy + plate_px / 2)
    elif silhouette:
        target = p_scale * W * 0.86
        cell = max(2, int(target // n))
        qr_px = cell * n
        cx, cy = center[0] * W, center[1] * W
        qr_x0 = round(cx - qr_px / 2)
        qr_y0 = round(cy - qr_px / 2)
        plate_px = qr_px
        plate_box = (qr_x0, qr_y0, qr_x0 + qr_px, qr_y0 + qr_px)
    else:
        cell = max(2, int((W * (1 - 2 * opts.margin)) // n))
        qr_px = cell * n
        qr_x0 = (W - qr_px) // 2
        qr_y0 = (W - qr_px) // 2
        plate_px = qr_px
        plate_box = (qr_x0, qr_y0, qr_x0 + qr_px, qr_y0 + qr_px)

    if silhouette:
        safe, finder_cov, data_cov = silhouette_safe(opts.shape, qr, W, cell, qr_x0, qr_y0)
        if not safe:
            warnings.append(f"Силуэт «{shape_name(opts.shape)}» режет finder-узоры ({finder_cov:.0%}) или данные ({data_cov:.0%}) — использую безопасную рамку.")
            silhouette = False
            frame = True
            fallback = True
            p_scale, center = _fit_plate(opts.shape)
            plate_target = p_scale * W
            cell = max(2, int((plate_target * 0.86) // n))
            qr_px = cell * n
            plate_px = qr_px / 0.86
            cx, cy = center[0] * W, center[1] * W
            qr_x0 = round(cx - qr_px / 2)
            qr_y0 = round(cy - qr_px / 2)
            plate_box = (cx - plate_px / 2, cy - plate_px / 2, cx + plate_px / 2, cy + plate_px / 2)

    if opts.module_style not in MODULE_STYLES:
        warnings.append(f"Неизвестный стиль модулей «{opts.module_style}», использую rounded.")
        opts = replace(opts, module_style="rounded")
    if opts.eye_style not in eye_keys():
        warnings.append(f"Неизвестный стиль глаз «{opts.eye_style}», использую rounded.")
        opts = replace(opts, eye_style="rounded")
    if cell < 7 and opts.module_style in {"heart", "paw", "star", "confetti", "flower"}:
        warnings.append("Модуль слишком мелкий для выбранного узора — упрощаю до точек.")
        opts = replace(opts, module_style="dot")
        fallback = True
    if cell < 9 and opts.eye_style in {"cat_eye", "star", "flower", "leaf"}:
        warnings.append("Глаза слишком мелкие для выбранного узора — упрощаю до скруглённых.")
        opts = replace(opts, eye_style="rounded")
        fallback = True

    if photo_mode:
        canvas = _photo_canvas(opts.photo, W)
        card_mask = Image.new("L", (W, W), 0)
        ImageDraw.Draw(card_mask).rounded_rectangle(plate_box, radius=plate_px * 0.07, fill=255)
        canvas.alpha_composite(_shadow_layer(W, card_mask, alpha=104, blur=max(2, W // 55), offset=(0, max(2, W // 100))))
        card_color = parse_color(qr_bg)
        canvas.alpha_composite(
            _rounded_layer(
                W,
                plate_box,
                card_color[:3] + (opts.photo_opacity,),
                radius=plate_px * 0.07,
                outline_color=mix(card_color, (0, 0, 0, 255), 0.16),
                outline_width=max(1, W // 700),
            )
        )
        mask = None
    elif opts.transparent:
        canvas = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        mask = None
    else:
        canvas = color_image(W, outer_spec)
        mask = None

    if photo_mode:
        pass
    elif frame:
        mask = shape_mask(opts.shape, W, ss=2)
        if opts.shadow:
            canvas.alpha_composite(_shadow_layer(W, mask, alpha=76, blur=max(2, W // 90), offset=(0, max(2, W // 120))))
        canvas.paste(color_image(W, shape_spec), (0, 0), mask)
        edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask)
        if edge.getbbox():
            edge_layer = Image.new("RGBA", (W, W), _spec_colors(shape_spec)[0][:3] + (160,))
            edge_layer.putalpha(edge)
            canvas.alpha_composite(edge_layer)
        decor = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        _draw_shape_decor(decor, opts.shape, W, parse_color(pal.shape_accent or shape_spec), mask)
        decor.putalpha(ImageChops.multiply(decor.getchannel("A"), mask))
        canvas.alpha_composite(decor)
        radius = plate_px * 0.065
        plate = _rounded_layer(
            W,
            plate_box,
            qr_bg,
            radius,
            outline_color=mix(qr_bg, (0, 0, 0, 255), 0.12),
            outline_width=max(1, W // 800),
        )
        canvas.alpha_composite(plate)
    elif silhouette:
        mask = shape_mask(opts.shape, W, ss=2)
        if opts.shadow and not opts.transparent:
            canvas.alpha_composite(_shadow_layer(W, mask, alpha=76, blur=max(2, W // 90), offset=(0, max(2, W // 120))))
        silhouette_fill = mix(parse_color(qr_bg), _spec_colors(shape_spec)[0], 0.07)
        canvas.paste(color_image(W, silhouette_fill), (0, 0), mask)
        rim_width = max(4, W // 220)
        if rim_width % 2 == 0:
            rim_width += 1
        rim = ImageChops.subtract(mask, mask.filter(ImageFilter.MinFilter(rim_width)))
        if rim.getbbox():
            rim_layer = Image.new("RGBA", (W, W), _spec_colors(shape_spec)[0][:3] + (235,))
            rim_layer.putalpha(rim)
            canvas.alpha_composite(rim_layer)
        decor = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        _draw_shape_decor(decor, opts.shape, W, parse_color(pal.shape_accent or shape_spec), mask)
        decor.putalpha(ImageChops.multiply(decor.getchannel("A"), mask))
        canvas.alpha_composite(decor)
    else:
        mask = None

    if (opts.logo is not None or opts.logo_mode == "monogram") and opts.logo_mode == "background":
        logo = opts.logo.copy()
        target = max(32, int(qr_px * 0.86))
        logo.thumbnail((target, target), Image.Resampling.LANCZOS)
        watermark = logo.convert("RGBA")
        watermark.putalpha(watermark.getchannel("A").point(lambda v: int(v * 0.22)))
        watermark = watermark.filter(ImageFilter.GaussianBlur(max(1, target // 120)))
        canvas.alpha_composite(watermark, (qr_x0 + (qr_px - watermark.width) // 2, qr_y0 + (qr_px - watermark.height) // 2))

    body = Image.new("L", (W, W), 0)
    body_overlay = Image.new("L", (W, W), 0)
    eyes = Image.new("L", (W, W), 0)
    eyes_overlay = Image.new("L", (W, W), 0)
    align = Image.new("L", (W, W), 0)
    draw_body = ImageDraw.Draw(body)
    variant_seed = opts.seed or 0
    for x, y in qr.dark_modules():
        mt = qr.module_type(x, y)
        if mt in FINDER_TYPES or mt in ALIGNMENT_TYPES:
            continue
        style = opts.module_style
        if style == "wave":
            variant = (x + y) % 4
        elif style == "pixel":
            variant = (x * 3 + y * 5) % 3
        elif style == "confetti":
            variant = (x * 31 + y * 17 + variant_seed) % 6
        elif style == "brick":
            variant = (x + y) % 2
        else:
            variant = 0
        sprite = module_sprite(style, cell, variant)
        body.paste(sprite, (qr_x0 + x * cell, qr_y0 + y * cell))
        overlay = module_overlay_sprite(style, cell, variant)
        if overlay is not None:
            body_overlay.paste(overlay, (qr_x0 + x * cell, qr_y0 + y * cell))
    if opts.module_style == "liquid":
        width = max(2, round(cell * 0.42))
        for x, y in qr.dark_modules():
            mt = qr.module_type(x, y)
            if mt in FINDER_TYPES or mt in ALIGNMENT_TYPES:
                continue
            cx = qr_x0 + x * cell + cell // 2
            cy = qr_y0 + y * cell + cell // 2
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if qr.is_dark(nx, ny) and qr.module_type(nx, ny) not in FINDER_TYPES and qr.module_type(nx, ny) not in ALIGNMENT_TYPES:
                    nx_c = qr_x0 + nx * cell + cell // 2
                    ny_c = qr_y0 + ny * cell + cell // 2
                    if dx:
                        draw_body.rounded_rectangle((cx, cy - width // 2, nx_c, cy + width // 2), radius=width // 2, fill=255)
                    else:
                        draw_body.rounded_rectangle((cx - width // 2, cy, cx + width // 2, ny_c), radius=width // 2, fill=255)
    for fx, fy in qr.finder_regions():
        eyes.paste(eye_sprite(opts.eye_style, cell), (qr_x0 + fx * cell, qr_y0 + fy * cell))
        overlay = eye_overlay_sprite(opts.eye_style, cell)
        if overlay is not None:
            eyes_overlay.paste(overlay, (qr_x0 + fx * cell, qr_y0 + fy * cell))
    for ax, ay in qr.alignment_regions():
        align.paste(alignment_sprite(cell), (qr_x0 + ax * cell, qr_y0 + ay * cell))

    knockout_mask = None
    if opts.logo is not None and opts.logo_mode == "knockout":
        knockout_mask = Image.new("L", (W, W), 0)
        logo_size = max(24, int(qr_px * opts.logo_size))
        logo = opts.logo.copy()
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        dilated = dilate_alpha(logo, max(2, logo_size // 20))
        knockout_mask.paste(dilated.getchannel("A"), (qr_x0 + (qr_px - dilated.width) // 2, qr_y0 + (qr_px - dilated.height) // 2))
        inv = ImageOps.invert(knockout_mask)
        body = ImageChops.multiply(body, inv)
        eyes = ImageChops.multiply(eyes, inv)
        align = ImageChops.multiply(align, inv)

    if silhouette and mask is not None:
        body = ImageChops.multiply(body, mask)
        eyes = ImageChops.multiply(eyes, mask)
        align = ImageChops.multiply(align, mask)

    if opts.logo is not None and opts.logo_mode == "texture":
        texture = _texture_fill(opts.logo, W, qr_fg, qr_bg)
        body_img = _apply_texture(body, texture)
    else:
        body_img = colorize_mask(body, qr_fg_spec, W)
    eye_img = colorize_mask(eyes, eye_spec, W)
    align_img = colorize_mask(align, eye_spec, W)
    canvas.alpha_composite(body_img)
    if body_overlay.getbbox():
        canvas.alpha_composite(colorize_mask(body_overlay, mix(parse_color(qr_fg_spec), qr_bg, 0.28), W))
    canvas.alpha_composite(eye_img)
    if eyes_overlay.getbbox():
        canvas.alpha_composite(colorize_mask(eyes_overlay, mix(eye_color, qr_fg, 0.35), W))
    canvas.alpha_composite(align_img)

    if opts.logo is not None and opts.logo_mode == "knockout":
        logo = opts.logo.copy()
        logo_size = max(24, int(qr_px * opts.logo_size))
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        if mean_luminance(logo) > 0.6:
            logo = outline(logo, qr_fg, max(2, logo_size // 30))
        else:
            logo = outline(logo, qr_bg, max(2, logo_size // 30))
        canvas.alpha_composite(logo, (qr_x0 + (qr_px - logo.width) // 2, qr_y0 + (qr_px - logo.height) // 2))
    elif (opts.logo is not None or opts.logo_mode == "monogram") and opts.logo_mode in {"plate", "corner", "badge", "monogram"}:
        _logo_plate(canvas, opts, (qr_x0, qr_y0, qr_x0 + qr_px, qr_y0 + qr_px), qr_fg, qr_bg)

    final = canvas.resize((S, S), Image.Resampling.LANCZOS)
    if opts.safe_mode and opts.logo is not None and opts.logo_mode in {"plate", "corner", "badge"} and qr_px:
        plate_ratio = 1.2 if opts.logo_mode == "corner" else (1.4 if opts.logo_mode == "badge" else 1.32)
        coverage = (opts.logo_size * plate_ratio) ** 2
        if coverage > 0.085:
            warnings.append("Логотип крупный — проверь сканирование камерой.")
    final_qr_fg = qr_fg_spec
    final_qr_bg = qr_bg_spec
    return RenderResult(
        image=final,
        qr=qr,
        options=opts,
        palette=pal,
        warnings=warnings,
        fallback=fallback,
        module_px=cell / ss,
        contrast=contrast,
        masked=silhouette,
        photo=photo_mode,
        qr_box=(round(qr_x0 / ss), round(qr_y0 / ss), round((qr_x0 + qr_px) / ss), round((qr_y0 + qr_px) / ss)),
        final_qr_fg=final_qr_fg,
        final_qr_bg=final_qr_bg,
    )


def render_png(options: RenderOptions, path: str | Path | None = None, dpi: int | None = None) -> bytes | Path:
    result = render(options)
    if path is None:
        buffer = io.BytesIO()
        result.image.save(buffer, format="PNG", dpi=(dpi or options.dpi, dpi or options.dpi))
        return buffer.getvalue()
    result.image.save(path, format="PNG", dpi=(dpi or options.dpi, dpi or options.dpi))
    return Path(path)


def render_preview(options: RenderOptions, size: int = 512) -> bytes:
    return render_png(replace(options, size=size))


def _svg_color(color: C.RGBA) -> str:
    if color[3] < 255:
        return f"rgba({color[0]},{color[1]},{color[2]},{color[3] / 255:.3f})"
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def _svg_paint(spec: ColorSpec, ident: str) -> tuple[str, str]:
    if isinstance(spec, Gradient):
        stops = "".join(
            f'<stop offset="{i / (len(spec.colors) - 1) * 100:.1f}%" stop-color="{_svg_color(color)}"/>'
            for i, color in enumerate(spec.colors)
        )
        if spec.radial:
            definition = f'<radialGradient id="{ident}" cx="50%" cy="50%" r="70%">{stops}</radialGradient>'
        else:
            angle = (spec.angle % 360) * math.pi / 180
            x1 = 50 - math.cos(angle) * 50
            y1 = 50 - math.sin(angle) * 50
            x2 = 50 + math.cos(angle) * 50
            y2 = 50 + math.sin(angle) * 50
            definition = f'<linearGradient id="{ident}" x1="{x1:.1f}%" y1="{y1:.1f}%" x2="{x2:.1f}%" y2="{y2:.1f}%">{stops}</linearGradient>'
        return f"url(#{ident})", definition
    return _svg_color(parse_color(spec)), ""


def _embedded_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _svg_shape_image(shape: str, spec: ColorSpec, size: int, fill: C.RGBA | None = None) -> str:
    mask = shape_mask(shape, size, ss=2)
    image = color_image(size, spec if fill is None else fill)
    image.putalpha(mask)
    return _embedded_png(image)


def render_svg(options: RenderOptions) -> str:
    opts = options.normalized()
    pal = get_palette(opts.palette)
    fg_spec: ColorSpec = opts.fg if opts.fg is not None else pal.fg
    bg_spec: ColorSpec = opts.bg if opts.bg is not None else pal.bg
    shape_spec: ColorSpec = opts.shape_color if opts.shape_color is not None else (pal.shape or fg_spec)
    outer_spec: ColorSpec = opts.outer_bg if opts.outer_bg is not None else pal.outer_bg
    qr_fg_spec, qr_bg_spec, _ = _contrast_spec(fg_spec, bg_spec)
    qr_fg = parse_color(qr_fg_spec)
    qr_bg = parse_color(qr_bg_spec)
    eye_color = parse_color(pal.accent or qr_fg_spec)
    if C.contrast_ratio(eye_color, qr_bg) < 3.5:
        eye_color = qr_fg
    photo_mode = opts.photo is not None
    silhouette = opts.silhouette and opts.shape != "square" and not photo_mode
    frame = opts.frame if opts.frame is not None else (opts.shape != "square" and not silhouette)
    if opts.shape == "square" and opts.frame is None:
        frame = False
    if photo_mode:
        frame = False
    qr = make_qr(opts.content, error=opts.error or ("h" if (opts.logo is not None or silhouette) else "m"), border=opts.border)
    n = qr.size
    S = opts.size
    fg_paint, fg_def = _svg_paint(qr_fg_spec, "fg")
    bg_paint, bg_def = _svg_paint(qr_bg_spec, "bg")
    _, shape_def = _svg_paint(shape_spec, "shape")
    outer_paint, outer_def = _svg_paint(outer_spec, "outer")
    if photo_mode:
        card = S * opts.photo_card
        cell = card * 0.86 / n
        qr_px = cell * n
        card = qr_px / 0.86
        margin = S * opts.photo_inset
        card_x1 = S - margin
        card_y1 = S - margin
        card_x0 = card_x1 - card
        card_y0 = card_y1 - card
        qx = card_x0 + (card - qr_px) / 2
        qy = card_y0 + (card - qr_px) / 2
        plate = None
    elif silhouette:
        scale, center = _fit_plate(opts.shape)
        cx, cy = center[0] * S, center[1] * S
        area = scale * S * 0.86
        qx = cx - area / 2
        qy = cy - area / 2
        cell = area / n
        safe, _, _ = silhouette_safe(opts.shape, qr, S, cell, round(qx), round(qy))
        if not safe:
            silhouette = False
            frame = True
        plate = None
    if photo_mode:
        pass
    elif not silhouette and frame:
        scale, center = _fit_plate(opts.shape)
        plate = scale * S
        cx, cy = center[0] * S, center[1] * S
        qx = cx - plate * 0.43
        qy = cy - plate * 0.43
        cell = plate * 0.86 / n
    elif not silhouette:
        area = S * (1 - 2 * opts.margin)
        qx = (S - area) / 2
        qy = (S - area) / 2
        cell = area / n
        plate = None
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}" shape-rendering="geometricPrecision">',
        "<defs>",
        fg_def,
        bg_def,
        shape_def,
        outer_def,
        "</defs>",
    ]
    if photo_mode:
        photo_image = _embedded_png(_photo_canvas(opts.photo, 1024).convert("RGB"))
        parts.append(f'<image href="data:image/png;base64,{photo_image}" x="0" y="0" width="{S}" height="{S}"/>')
        parts.append(
            f'<rect x="{card_x0:.2f}" y="{card_y0:.2f}" width="{card:.2f}" height="{card:.2f}" rx="{card * 0.07:.2f}" fill="{_svg_color(qr_bg)}" fill-opacity="{opts.photo_opacity / 255:.3f}" stroke="{_svg_color(mix(qr_bg, (0, 0, 0, 255), 0.16))}" stroke-width="{max(1, S // 700)}"/>'
        )
    elif not opts.transparent:
        parts.append(f'<rect width="{S}" height="{S}" fill="{outer_paint}"/>')
    shape_fill = mix(parse_color(qr_bg_spec), parse_color(shape_spec), 0.07) if silhouette else None
    effective_bg = _svg_color(qr_bg) if photo_mode else (_svg_color(shape_fill) if shape_fill is not None else bg_paint)
    if not photo_mode and opts.shape != "square":
        shape_image = _svg_shape_image(opts.shape, shape_fill if shape_fill is not None else shape_spec, 1024)
        parts.append(f'<image href="data:image/png;base64,{shape_image}" x="0" y="0" width="{S}" height="{S}"/>')
    if silhouette:
        rim_mask = shape_mask(opts.shape, 1024, ss=2)
        rim = ImageChops.subtract(rim_mask, rim_mask.filter(ImageFilter.MinFilter(7)))
        rim_image = color_image(1024, shape_spec)
        rim_image.putalpha(rim)
        parts.append(f'<image href="data:image/png;base64,{_embedded_png(rim_image)}" x="0" y="0" width="{S}" height="{S}"/>')
        mask_image = _embedded_png(shape_mask(opts.shape, 1024, ss=2).convert("L"))
        parts.append(f'<mask id="shapeClip"><image href="data:image/png;base64,{mask_image}" x="0" y="0" width="{S}" height="{S}"/></mask>')
        parts.append('<g mask="url(#shapeClip)">')
    if plate is not None and frame:
        box = (cx - plate / 2, cy - plate / 2, cx + plate / 2, cy + plate / 2)
        parts.append(
            f'<rect x="{box[0]:.2f}" y="{box[1]:.2f}" width="{plate:.2f}" height="{plate:.2f}" rx="{plate * 0.065:.2f}" fill="{bg_paint}" stroke="{_svg_color(mix(qr_bg, (0, 0, 0, 255), 0.12))}" stroke-width="{max(1, S // 700)}"/>'
        )
        parts.append(f'<rect x="{qx:.2f}" y="{qy:.2f}" width="{cell * n:.2f}" height="{cell * n:.2f}" fill="{bg_paint}"/>')
    parts.append(f'<g fill="{fg_paint}">')
    for y in range(n):
        for x in range(n):
            if not qr.is_dark(x, y):
                continue
            if qr.module_type(x, y) in FINDER_TYPES or qr.module_type(x, y) in ALIGNMENT_TYPES:
                continue
            px = qx + x * cell
            py = qy + y * cell
            if opts.module_style in {"dot", "ring"}:
                if opts.module_style == "ring":
                    parts.append(
                        f'<circle cx="{px + cell / 2:.2f}" cy="{py + cell / 2:.2f}" r="{cell * 0.42:.2f}" fill="none" stroke="{fg_paint}" stroke-width="{cell * 0.2:.2f}"/>'
                    )
                else:
                    parts.append(f'<circle cx="{px + cell / 2:.2f}" cy="{py + cell / 2:.2f}" r="{cell * 0.42:.2f}"/>')
            elif opts.module_style in {"diamond"}:
                parts.append(
                    f'<polygon points="{px + cell / 2:.2f},{py + cell * 0.06:.2f} {px + cell * 0.94:.2f},{py + cell / 2:.2f} {px + cell / 2:.2f},{py + cell * 0.94:.2f} {px + cell * 0.06:.2f},{py + cell / 2:.2f}"/>'
                )
            else:
                radius = cell * (0.28 if opts.module_style == "rounded" else 0.02)
                parts.append(f'<rect x="{px + cell * 0.04:.2f}" y="{py + cell * 0.04:.2f}" width="{cell * 0.92:.2f}" height="{cell * 0.92:.2f}" rx="{radius:.2f}"/>')
    parts.append("</g>")
    for fx, fy in qr.finder_regions():
        px = qx + fx * cell
        py = qy + fy * cell
        parts.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{cell * 7:.2f}" height="{cell * 7:.2f}" fill="{fg_paint}"/>')
        parts.append(f'<rect x="{px + cell:.2f}" y="{py + cell:.2f}" width="{cell * 5:.2f}" height="{cell * 5:.2f}" fill="{effective_bg}"/>')
        parts.append(f'<rect x="{px + cell * 2:.2f}" y="{py + cell * 2:.2f}" width="{cell * 3:.2f}" height="{cell * 3:.2f}" fill="{fg_paint}"/>')
    for ax, ay in qr.alignment_regions():
        px = qx + ax * cell
        py = qy + ay * cell
        parts.append(f'<rect x="{px:.2f}" y="{py:.2f}" width="{cell * 5:.2f}" height="{cell * 5:.2f}" fill="{fg_paint}"/>')
        parts.append(f'<rect x="{px + cell:.2f}" y="{py + cell:.2f}" width="{cell * 3:.2f}" height="{cell * 3:.2f}" fill="{effective_bg}"/>')
        parts.append(f'<rect x="{px + cell * 2:.2f}" y="{py + cell * 2:.2f}" width="{cell:.2f}" height="{cell:.2f}" fill="{fg_paint}"/>')
    if silhouette:
        parts.append("</g>")
    logo = opts.logo
    if logo is not None and opts.logo_mode in {"plate", "corner", "knockout", "badge"}:
        logo_size = max(24, int(cell * n * opts.logo_size))
        if opts.logo_mode == "corner":
            logo_size = max(24, int(cell * n * min(opts.logo_size, 0.105)))
        badge = opts.logo_mode == "badge"
        plate_size = int(logo_size * (1.2 if opts.logo_mode == "corner" else (1.4 if badge else 1.32)))
        if opts.logo_mode == "corner":
            left = qx + cell * n - plate_size - max(8, int(cell * n * 0.02))
            top = qy + cell * n - plate_size - max(8, int(cell * n * 0.02))
        else:
            left = qx + (cell * n - plate_size) / 2
            top = qy + (cell * n - plate_size) / 2
        if badge:
            parts.append(
                f'<circle cx="{left + plate_size / 2:.2f}" cy="{top + plate_size / 2:.2f}" r="{plate_size / 2:.2f}" fill="{bg_paint}" stroke="{_svg_color(mix(qr_bg, (0, 0, 0, 255), 0.18))}" stroke-width="{max(1, S // 700)}"/>'
            )
        elif opts.logo_mode != "knockout":
            parts.append(
                f'<rect x="{left:.2f}" y="{top:.2f}" width="{plate_size}" height="{plate_size}" rx="{plate_size * 0.28:.2f}" fill="{bg_paint}" stroke="{_svg_color(mix(qr_bg, (0, 0, 0, 255), 0.18))}" stroke-width="{max(1, S // 700)}"/>'
            )
        buffer = io.BytesIO()
        logo.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        parts.append(
            f'<image href="data:image/png;base64,{encoded}" x="{left + (plate_size - logo_size) / 2:.2f}" y="{top + (plate_size - logo_size) / 2:.2f}" width="{logo_size}" height="{logo_size}"/>'
        )
    elif opts.logo_mode == "monogram":
        size = int(cell * n * opts.logo_size * 1.32)
        left = qx + (cell * n - size) / 2
        top = qy + (cell * n - size) / 2
        parts.append(
            f'<rect x="{left:.2f}" y="{top:.2f}" width="{size}" height="{size}" rx="{size * 0.28:.2f}" fill="{bg_paint}" stroke="{_svg_color(mix(qr_bg, (0, 0, 0, 255), 0.18))}" stroke-width="{max(1, S // 700)}"/>'
        )
        parts.append(
            f'<text x="{left + size / 2:.2f}" y="{top + size * 0.62:.2f}" text-anchor="middle" font-family="Roboto, Arial, sans-serif" font-weight="700" font-size="{size * 0.46:.2f}" fill="{_svg_color(qr_fg)}">{html.escape(opts.logo_text)}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)
