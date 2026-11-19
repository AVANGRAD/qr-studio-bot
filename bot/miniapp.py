from __future__ import annotations

import asyncio
import hashlib
import hmac
import io
import json
import logging
import time
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl

from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, Update, User, WebAppData
from aiohttp import web

from qrstudio.eyes import eye_keys
from qrstudio.masks import SHAPE_CATEGORIES, SHAPES
from qrstudio.presets import PALETTES, PRESETS, get_preset
from qrstudio.render import RenderOptions, render
from qrstudio.shapes import MODULE_STYLES

from .i18n import (
    DEFAULT_LANG,
    SUPPORTED_LANGS,
    category_key,
    display_name,
    resolve_lang,
)

logger = logging.getLogger(__name__)
BOT_KEY = web.AppKey("qrstudio_bot", object)
DISPATCHER_KEY = web.AppKey("qrstudio_dispatcher", object)
WEBAPP_DIR = Path(__file__).resolve().parent.parent / "webapp"
THUMBS_DIR = WEBAPP_DIR / "thumbs"
SAMPLE = "https://qr.studio"
THUMB_SIZE = 220
SIZES = (512, 1024, 2048)

SHAPE_KEYS = set(SHAPES)
MODULE_KEYS = set(MODULE_STYLES)
EYE_KEYS = set(eye_keys())
PALETTE_KEYS = set(PALETTES)
PRESET_KEYS = set(PRESETS)


def _card(kind: str, key: str, name: str, **extra) -> dict:
    return {"key": key, "name": name, "thumb": f"/app/thumbs/{kind}/{key}.png?v=variety1", **extra}


def catalog(lang: str = DEFAULT_LANG) -> dict:
    lang = lang if lang in SUPPORTED_LANGS else DEFAULT_LANG
    shapes = []
    for category, keys in SHAPE_CATEGORIES.items():
        key = category_key(category)
        shapes.append(
            {
                "key": key,
                "name": display_name("category", key, lang),
                "items": [_card("shape", item, display_name("shape", item, lang)) for item in keys],
            }
        )
    modules = [_card("module", key, display_name("module", key, lang)) for key in MODULE_STYLES]
    eyes = [_card("eye", key, display_name("eye", key, lang)) for key in eye_keys()]
    palettes = [_card("palette", key, display_name("palette", key, lang)) for key in PALETTES]
    presets = []
    for key, preset in PRESETS.items():
        presets.append(
            _card(
                "preset",
                key,
                display_name("preset", key, lang),
                shape=preset.shape,
                module_style=preset.module_style,
                eye_style=preset.eye_style,
                palette=preset.palette,
            )
        )
    return {
        "shapes": shapes,
        "modules": modules,
        "eyes": eyes,
        "palettes": palettes,
        "presets": presets,
        "sizes": list(SIZES),
        "sample": SAMPLE,
    }


def validate_init_data(init_data: str, bot_token: str, max_age: int = 6 * 3600) -> dict:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("missing hash")
    check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise ValueError("invalid signature")
    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid auth_date") from exc
    if time.time() - auth_date > max_age:
        raise ValueError("expired init data")
    return pairs


def _options(kind: str, key: str) -> RenderOptions:
    if kind == "shape":
        if key not in SHAPE_KEYS:
            raise KeyError(key)
        return RenderOptions(content=SAMPLE, shape=key, module_style="dot", eye_style="circle", palette="blue", size=THUMB_SIZE, silhouette=key != "square")
    if kind == "module":
        if key not in MODULE_KEYS:
            raise KeyError(key)
        return RenderOptions(content=SAMPLE, shape="rounded", module_style=key, eye_style="circle", palette="blue", size=THUMB_SIZE)
    if kind == "eye":
        if key not in EYE_KEYS:
            raise KeyError(key)
        return RenderOptions(content=SAMPLE, shape="rounded", module_style="dot", eye_style=key, palette="purple", size=THUMB_SIZE)
    if kind == "palette":
        if key not in PALETTE_KEYS:
            raise KeyError(key)
        return RenderOptions(content=SAMPLE, shape="rounded", module_style="rounded", eye_style="rounded", palette=key, size=THUMB_SIZE)
    if kind == "preset":
        if key not in PRESET_KEYS:
            raise KeyError(key)
        preset = get_preset(key)
        return RenderOptions(
            content=SAMPLE,
            shape=preset.shape,
            module_style=preset.module_style,
            eye_style=preset.eye_style,
            palette=preset.palette,
            size=THUMB_SIZE,
            silhouette=preset.shape != "square",
        )
    raise KeyError(kind)


@lru_cache(maxsize=512)
def thumb_bytes(kind: str, key: str) -> bytes:
    result = render(_options(kind, key))
    buffer = io.BytesIO()
    result.image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


@lru_cache(maxsize=256)
def preview_bytes(shape: str, module: str, eye: str, palette: str, size: int) -> bytes:
    shape = shape if shape in SHAPE_KEYS else "square"
    module = module if module in MODULE_KEYS else "dot"
    eye = eye if eye in EYE_KEYS else "circle"
    palette = palette if palette in PALETTE_KEYS else "blue"
    result = render(
        RenderOptions(
            content=SAMPLE,
            shape=shape,
            module_style=module,
            eye_style=eye,
            palette=palette,
            size=max(280, min(size, 640)),
            silhouette=shape != "square",
        )
    )
    buffer = io.BytesIO()
    result.image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


async def index(_: web.Request) -> web.StreamResponse:
    return web.FileResponse(WEBAPP_DIR / "index.html", headers={"Cache-Control": "no-cache"})


async def catalog_handler(request: web.Request) -> web.Response:
    lang = resolve_lang(request.query.get("lang"))
    return web.json_response(catalog(lang), dumps=lambda value: json.dumps(value, ensure_ascii=False), headers={"Cache-Control": "no-cache"})


async def thumb_handler(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    key = request.match_info["key"]
    try:
        payload = await asyncio.to_thread(thumb_bytes, kind, key)
    except KeyError:
        raise web.HTTPNotFound()
    return web.Response(body=payload, content_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


async def apply_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        raise web.HTTPBadRequest(text="invalid json")
    if not isinstance(body, dict):
        raise web.HTTPBadRequest(text="invalid payload")
    init_data = body.get("init_data")
    settings = body.get("data")
    if not isinstance(init_data, str) or not init_data or not isinstance(settings, dict):
        raise web.HTTPBadRequest(text="missing init data")
    bot = request.app.get(BOT_KEY)
    dispatcher = request.app.get(DISPATCHER_KEY)
    if bot is None or dispatcher is None:
        raise web.HTTPServiceUnavailable(text="bot is not ready")
    try:
        pairs = validate_init_data(init_data, bot.token)
        user_data = json.loads(pairs.get("user", "{}"))
        user_id = int(user_data["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise web.HTTPUnauthorized(text="invalid init data")
    first_name = str(user_data.get("first_name") or "User")
    language_code = user_data.get("language_code")
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=user_id, type="private"),
        from_user=User(
            id=user_id,
            is_bot=False,
            first_name=first_name,
            language_code=language_code if isinstance(language_code, str) else None,
        ),
        web_app_data=WebAppData(data=json.dumps(settings, ensure_ascii=False), button_text="QR Studio"),
    )
    update = Update(update_id=int(time.time() * 1000), message=message)
    try:
        await dispatcher.feed_update(bot, update)
    except Exception as exc:
        logger.exception("mini app apply failed")
        raise web.HTTPInternalServerError(text="apply failed") from exc
    return web.json_response({"ok": True})


async def preview_handler(request: web.Request) -> web.Response:
    query = request.query
    try:
        size = int(query.get("size", "400"))
    except ValueError:
        size = 400
    payload = await asyncio.to_thread(
        preview_bytes,
        query.get("shape", "square"),
        query.get("module") or query.get("module_style", "dot"),
        query.get("eye") or query.get("eye_style", "circle"),
        query.get("palette", "blue"),
        size,
    )
    return web.Response(body=payload, content_type="image/png", headers={"Cache-Control": "no-store"})


def setup(app: web.Application, bot: Bot | None = None, dispatcher: Dispatcher | None = None) -> None:
    app[BOT_KEY] = bot
    app[DISPATCHER_KEY] = dispatcher
    app.router.add_get("/app", index)
    app.router.add_get("/app/", index)
    app.router.add_get("/app/catalog.json", catalog_handler)
    app.router.add_get("/app/thumb/{kind}/{key}.png", thumb_handler)
    app.router.add_get("/app/preview.png", preview_handler)
    app.router.add_post("/app/apply", apply_handler)
    app.router.add_static("/app/static/", WEBAPP_DIR, name="webapp-static")
    if THUMBS_DIR.exists():
        app.router.add_static("/app/thumbs/", THUMBS_DIR, name="webapp-thumbs")
