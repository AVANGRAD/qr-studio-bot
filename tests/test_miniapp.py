from __future__ import annotations

from bot.miniapp import catalog, preview_bytes, thumb_bytes
from bot.services import Draft, webapp_url


def test_catalog_counts() -> None:
    data = catalog()
    assert sum(len(group["items"]) for group in data["shapes"]) == 44
    assert len(data["modules"]) == 18
    assert len(data["eyes"]) == 10
    assert len(data["palettes"]) == 15
    assert len(data["presets"]) == 18
    assert data["sizes"] == [512, 1024, 2048]


def test_thumb_png_and_leaf() -> None:
    leaf = thumb_bytes("shape", "leaf")
    assert leaf.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(leaf) > 8000
    module = thumb_bytes("module", "leaf")
    assert module.startswith(b"\x89PNG\r\n\x1a\n")


def test_preview_fallback() -> None:
    payload = preview_bytes("nope", "nope", "nope", "nope", 400)
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(payload) > 5000


def test_webapp_url() -> None:
    url = webapp_url(Draft(content="https://example.com", shape="leaf", palette="wood", size=512))
    assert url.startswith("https://")
    assert "/app?" in url
    assert "shape=leaf" in url
    assert "palette=wood" in url
    assert "size=512" in url
