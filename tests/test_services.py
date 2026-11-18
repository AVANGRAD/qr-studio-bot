from __future__ import annotations

import io

import pytest
from PIL import Image

from bot.services import (
    ContentError,
    Draft,
    RateLimiter,
    caption,
    normalize_content,
    prepare_uploaded_logo,
    prepare_uploaded_photo,
)
from qrstudio.render import RenderOptions, render


def test_normalize_plain_text() -> None:
    assert normalize_content("  hello world  ") == "hello world"


def test_normalize_www() -> None:
    assert normalize_content("www.example.com") == "https://www.example.com"


def test_normalize_url() -> None:
    assert normalize_content("https://example.com/a?b=1") == "https://example.com/a?b=1"


def test_reject_empty() -> None:
    with pytest.raises(ContentError):
        normalize_content("   ")


def test_reject_long() -> None:
    with pytest.raises(ContentError):
        normalize_content("x" * 11, max_length=10)


def test_reject_weird_scheme() -> None:
    with pytest.raises(ContentError):
        normalize_content("ftp://example.com/file")


def test_rate_limiter() -> None:
    limiter = RateLimiter(per_minute=2, per_day=2)
    assert limiter.allow(1)[0]
    assert limiter.allow(1)[0]
    assert not limiter.allow(1)[0]


def test_prepare_logo() -> None:
    image = Image.new("RGB", (200, 120), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    prepared = prepare_uploaded_logo(buffer.getvalue())
    assert prepared.startswith(b"\x89PNG")
    assert len(prepared) > 100


def test_caption_escapes_content() -> None:
    draft = Draft(content="<b>test</b>")
    result = render(RenderOptions(content=draft.content, size=256))
    text = caption(draft, result)
    assert "&lt;b&gt;test&lt;/b&gt;" in text
    assert "<b>QR Studio</b>" in text


def test_prepare_photo_normalizes_to_jpeg() -> None:
    image = Image.new("RGB", (2400, 1600), (90, 140, 180))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    prepared = prepare_uploaded_photo(buffer.getvalue())
    assert prepared.startswith(b"\xff\xd8")
    with Image.open(io.BytesIO(prepared)) as result:
        assert max(result.size) <= 1600


def test_caption_marks_photo_mode() -> None:
    draft = Draft(content="https://example.com", photo_bytes=b"jpeg")
    assert "Фон: фото" in caption(draft)
