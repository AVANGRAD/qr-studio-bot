from __future__ import annotations

import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from bot import miniapp
from bot.abuse import SlidingWindowLimiter
from bot.miniapp import catalog, preview_bytes, setup, thumb_bytes, validate_init_data
from bot.services import Draft, RateLimiter, webapp_url


def test_catalog_counts() -> None:
    data = catalog()
    assert sum(len(group["items"]) for group in data["shapes"]) == 52
    assert len(data["modules"]) == 24
    assert len(data["eyes"]) == 14
    assert len(data["palettes"]) == 19
    assert len(data["presets"]) == 25
    assert data["sizes"] == [512, 1024, 2048]


def test_catalog_languages() -> None:
    ru = catalog("ru")
    en = catalog("en")
    assert ru["shapes"][0]["name"] == "Геометрия"
    assert en["shapes"][0]["name"] == "Geometry"
    assert en["shapes"][0]["items"][0]["name"] == "Square"
    assert en["presets"][0]["name"] == "Golden leaf"


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


TOKEN = "123456:test-token"


def _signed_init_data(user_id: int, auth_date: int | None = None, language_code: str | None = None) -> str:
    user = {"id": user_id, "first_name": "Test"}
    if language_code:
        user["language_code"] = language_code
    pairs = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "test-query",
        "user": json.dumps(user, separators=(",", ":")),
    }
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**pairs, "hash": signature})


def test_validate_init_data() -> None:
    init_data = _signed_init_data(42)
    parsed = validate_init_data(init_data, TOKEN)
    assert parsed["user"] == '{"id":42,"first_name":"Test"}'


def test_validate_init_data_rejects_bad_signature() -> None:
    with pytest.raises(ValueError):
        validate_init_data(_signed_init_data(42) + "tampered", TOKEN)


def test_validate_init_data_rejects_expired() -> None:
    with pytest.raises(ValueError):
        validate_init_data(_signed_init_data(42, int(time.time()) - 7 * 3600), TOKEN)


def test_validate_init_data_rejects_future() -> None:
    with pytest.raises(ValueError):
        validate_init_data(_signed_init_data(42, int(time.time()) + 3600), TOKEN)


@pytest.mark.asyncio
async def test_apply_endpoint_dispatches_to_bot() -> None:
    class FakeDispatcher:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, int, str | None]] = []

        async def feed_update(self, bot, update) -> None:
            self.calls.append(
                (
                    bot.token,
                    update.message.web_app_data.data,
                    update.message.chat.id,
                    update.message.from_user.language_code,
                )
            )

    dispatcher = FakeDispatcher()
    app = web.Application()
    setup(app, bot=SimpleNamespace(token=TOKEN), dispatcher=dispatcher)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        response = await client.post(
            "/app/apply",
            json={"init_data": _signed_init_data(42, language_code="en-US"), "data": {"shape": "leaf", "size": 512}},
        )
        assert response.status == 200
        assert dispatcher.calls
        token, raw, chat_id, language_code = dispatcher.calls[0]
        assert token == TOKEN
        assert json.loads(raw) == {"shape": "leaf", "size": 512}
        assert chat_id == 42
        assert language_code == "en-US"

        bad = await client.post(
            "/app/apply",
            json={"init_data": _signed_init_data(42) + "tampered", "data": {"shape": "leaf"}},
        )
        assert bad.status == 401
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_preview_endpoint_rate_limits(monkeypatch) -> None:
    monkeypatch.setattr(miniapp, "preview_limiter", SlidingWindowLimiter(limit=1, window=60))
    app = web.Application()
    setup(app)
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        first = await client.get("/app/preview.png?shape=leaf&size=280")
        assert first.status == 200
        second = await client.get("/app/preview.png?shape=leaf&size=280")
        assert second.status == 429
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_apply_endpoint_rate_limits(monkeypatch) -> None:
    class FakeDispatcher:
        async def feed_update(self, bot, update) -> None:
            return None

    monkeypatch.setattr(miniapp, "apply_limiter", RateLimiter(per_minute=1, per_day=10))
    app = web.Application()
    setup(app, bot=SimpleNamespace(token=TOKEN), dispatcher=FakeDispatcher())
    client = TestClient(TestServer(app))
    await client.start_server()
    try:
        payload = {"init_data": _signed_init_data(42), "data": {"shape": "leaf"}}
        first = await client.post("/app/apply", json=payload)
        assert first.status == 200
        second = await client.post("/app/apply", json=payload)
        assert second.status == 429
    finally:
        await client.close()
