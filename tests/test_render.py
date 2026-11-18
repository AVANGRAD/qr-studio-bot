from __future__ import annotations

import io
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

from qrstudio.eyes import eye_keys
from qrstudio.masks import shape_keys
from qrstudio.presets import palette_keys
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
    for mode in ("plate", "knockout", "texture", "background", "corner"):
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
