from __future__ import annotations

import io
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

from qrstudio.emblems import emblem_image, emblem_keys
from qrstudio.eyes import eye_keys
from qrstudio.masks import shape_keys
from qrstudio.presets import PRESETS, palette_keys
from qrstudio.render import RenderOptions, render, render_svg
from qrstudio.shapes import MODULE_STYLES


def _logo() -> Image.Image:
    image = Image.new("RGBA", (256, 256), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((20, 20, 236, 236), fill=(210, 40, 60, 255))
    return image


def test_default_render() -> None:
    result = render(RenderOptions(content="https://example.com", size=512))
    assert result.image.size == (512, 512)
    assert result.module_px > 4
    assert result.contrast >= 4.5
    assert result.qr.content == "https://example.com"


def test_all_shapes() -> None:
    for key in shape_keys():
        result = render(RenderOptions(content="https://example.com", shape=key, size=256))
        assert result.image.size == (256, 256)


def test_all_module_styles() -> None:
    for key in MODULE_STYLES:
        result = render(RenderOptions(content="https://example.com", module_style=key, size=320))
        assert result.image.size == (320, 320)


def test_all_eyes() -> None:
    for key in eye_keys():
        result = render(RenderOptions(content="https://example.com", eye_style=key, size=320))
        assert result.image.size == (320, 320)


def test_all_palettes() -> None:
    for key in palette_keys():
        result = render(RenderOptions(content="https://example.com", palette=key, size=320))
        assert result.contrast >= 4.5


def test_logo_modes() -> None:
    logo = _logo()
    for mode in ("plate", "badge", "knockout", "texture", "background", "corner"):
        result = render(RenderOptions(content="https://example.com", shape="cat", logo=logo, logo_mode=mode, size=512))
        assert result.image.size == (512, 512)
    result = render(RenderOptions(content="https://example.com", logo_mode="monogram", logo_text="AK", size=512))
    assert result.image.size == (512, 512)


def test_silhouette_fallback_is_honest() -> None:
    result = render(RenderOptions(content="https://example.com", shape="star5", silhouette=True, size=512))
    assert result.image.size == (512, 512)
    assert isinstance(result.warnings, list)


def test_svg_is_valid_xml() -> None:
    payload = render_svg(RenderOptions(content="https://example.com", shape="rounded", size=512))
    root = ET.fromstring(payload)
    assert root.tag.endswith("svg")
    assert 'width="512"' in payload


def test_svg_monogram_escapes_xml() -> None:
    payload = render_svg(
        RenderOptions(content="https://example.com", logo_mode="monogram", logo_text="A&B", size=512)
    )
    root = ET.fromstring(payload)
    assert root.tag.endswith("svg")
    assert "A&amp;B" in payload


def test_png_dpi() -> None:
    result = render(RenderOptions(content="https://example.com", size=512))
    buffer = io.BytesIO()
    result.image.save(buffer, format="PNG", dpi=(300, 300))
    image = Image.open(io.BytesIO(buffer.getvalue()))
    dpi = image.info.get("dpi")
    assert dpi is not None
    assert abs(dpi[0] - 300) < 1


def test_figure_mode_wraps_qr_in_shape() -> None:
    result = render(RenderOptions(content="https://example.com", shape="leaf", silhouette=True, size=512))
    assert result.masked is True
    assert not result.fallback
    assert result.image.size == (512, 512)


def test_draft_defaults_to_figure_mode() -> None:
    from bot.services import Draft

    assert Draft(content="https://example.com").silhouette is True


def test_photo_overlay_keeps_photo() -> None:
    photo = Image.new("RGB", (600, 900), (120, 180, 140))
    draw = ImageDraw.Draw(photo)
    draw.ellipse((180, 300, 420, 620), fill=(40, 90, 180))
    result = render(RenderOptions(content="https://example.com", photo=photo, size=512))
    assert result.photo is True
    assert result.image.size == (512, 512)
    assert result.qr_box[2] > 300


def test_photo_svg_is_valid_xml() -> None:
    photo = Image.new("RGB", (600, 900), (120, 180, 140))
    payload = render_svg(RenderOptions(content="https://example.com", photo=photo, size=512))
    root = ET.fromstring(payload)
    assert root.tag.endswith("svg")
    assert "<image" in payload


def test_all_presets_render() -> None:
    for key, preset in PRESETS.items():
        result = render(
            RenderOptions(
                content="https://example.com",
                shape=preset.shape,
                module_style=preset.module_style,
                eye_style=preset.eye_style,
                palette=preset.palette,
                size=256,
                silhouette=preset.shape != "square",
            )
        )
        assert result.image.size == (256, 256), key


def test_emblem_logos_render() -> None:
    for key in emblem_keys():
        logo = emblem_image(key, 256)
        result = render(RenderOptions(content="https://example.com", logo=logo, logo_mode="badge", size=512))
        assert result.image.size == (512, 512), key
