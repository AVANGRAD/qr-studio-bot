from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from .colors import RGBA, parse_color, relative_luminance


def load_logo(source: bytes | str | Path, max_side: int = 1024) -> Image.Image:
    if isinstance(source, (str, Path)):
        image = Image.open(source)
    else:
        import io

        image = Image.open(io.BytesIO(source))
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGBA")
    if max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return image


def _near_white_mask(image: Image.Image, threshold: int = 238, spread: int = 18) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    mask = Image.new("L", rgb.size, 0)
    out = mask.load()
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if min(r, g, b) >= threshold and max(r, g, b) - min(r, g, b) <= spread:
                out[x, y] = 255
    return mask


def _border_connected(mask: Image.Image) -> Image.Image:
    width, height = mask.size
    src = mask.load()
    result = Image.new("L", (width, height), 0)
    dst = result.load()
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        for y in (0, height - 1):
            if src[x, y] and not dst[x, y]:
                dst[x, y] = 255
                queue.append((x, y))
    for y in range(height):
        for x in (0, width - 1):
            if src[x, y] and not dst[x, y]:
                dst[x, y] = 255
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height and src[nx, ny] and not dst[nx, ny]:
                dst[nx, ny] = 255
                queue.append((nx, ny))
    return result


def remove_white_background(image: Image.Image, threshold: int = 238, spread: int = 18) -> Image.Image:
    image = image.convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box and alpha_box != (0, 0, image.width, image.height):
        return image
    probe = image.copy()
    probe.thumbnail((512, 512), Image.Resampling.LANCZOS)
    near = _near_white_mask(probe, threshold=threshold, spread=spread)
    connected = _border_connected(near)
    connected = connected.resize(image.size, Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(1.0))
    alpha = image.getchannel("A")
    keep = ImageChops.subtract(alpha, connected)
    image.putalpha(keep)
    return image


def trim(image: Image.Image, padding: float = 0.04) -> Image.Image:
    image = image.convert("RGBA")
    bbox = image.getchannel("A").getbbox()
    if not bbox:
        return image
    cropped = image.crop(bbox)
    pad = round(max(cropped.size) * padding)
    canvas = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(cropped, (pad, pad))
    return canvas


def pad_square(image: Image.Image) -> Image.Image:
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas


def mean_luminance(image: Image.Image) -> float:
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    if alpha.getbbox() is None:
        return 1.0
    pixels = image.load()
    total = 0.0
    count = 0
    step = max(1, image.width // 256)
    for y in range(0, image.height, step):
        for x in range(0, image.width, step):
            r, g, b, a = pixels[x, y]
            if a > 20:
                total += relative_luminance((r, g, b, a))
                count += 1
    return total / count if count else 1.0


def monochrome(image: Image.Image, color: RGBA, prefer_dark: bool = True) -> Image.Image:
    image = image.convert("RGBA")
    gray = ImageOps.grayscale(image)
    alpha = image.getchannel("A")
    luminance = mean_luminance(image)
    invert = luminance > 0.55 if prefer_dark else luminance < 0.45
    if invert:
        mask = ImageOps.invert(gray)
    else:
        mask = gray
    mask = ImageChops.multiply(mask.convert("L"), alpha)
    mask = ImageOps.autocontrast(mask)
    result = Image.new("RGBA", image.size, color[:3] + (0,))
    result.putalpha(mask)
    return result


def prepare_logo(
    source: bytes | str | Path,
    max_side: int = 1024,
    remove_bg: bool = True,
    mono: bool = False,
    mono_color: RGBA = (0, 0, 0, 255),
) -> Image.Image:
    image = load_logo(source, max_side=max_side)
    if remove_bg:
        image = remove_white_background(image)
    image = trim(image, padding=0.03)
    image = pad_square(image)
    if mono:
        image = monochrome(image, parse_color(mono_color), prefer_dark=True)
    return image


def dilate_alpha(image: Image.Image, radius: int = 4) -> Image.Image:
    alpha = image.getchannel("A")
    expanded = alpha.filter(ImageFilter.MaxFilter(radius * 2 + 1))
    result = image.copy()
    result.putalpha(expanded)
    return result


def outline(image: Image.Image, color: RGBA = (255, 255, 255, 255), width: int = 3) -> Image.Image:
    alpha = image.getchannel("A")
    expanded = alpha.filter(ImageFilter.MaxFilter(width * 2 + 1))
    contour = ImageChops.subtract(expanded, alpha)
    layer = Image.new("RGBA", image.size, color)
    layer.putalpha(contour)
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    result.alpha_composite(layer)
    result.alpha_composite(image)
    return result


FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Roboto.ttf"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()


def monogram_image(text: str, size: int, color: RGBA, background: RGBA) -> Image.Image:
    image = Image.new("RGBA", (size, size), background)
    draw = ImageDraw.Draw(image)
    parts = text.split()
    if len(parts) >= 2:
        initials = "".join(part[0] for part in parts[:2]).upper()
    else:
        initials = (parts[0][:2] if parts else "QR").upper()
    current = font(round(size * 0.5))
    bbox = draw.textbbox((0, 0), initials, font=current)
    while bbox[2] - bbox[0] > size * 0.7 and current.size > 8:
        current = font(max(8, current.size - 2))
        bbox = draw.textbbox((0, 0), initials, font=current)
    x = (size - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), initials, font=current, fill=color)
    return image
