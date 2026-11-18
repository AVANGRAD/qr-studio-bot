from __future__ import annotations

import asyncio
import io
import json
from functools import lru_cache
from pathlib import Path

from aiohttp import web

from qrstudio.eyes import eye_keys, eye_name
from qrstudio.masks import SHAPE_CATEGORIES, SHAPES, shape_name
from qrstudio.presets import PALETTES, PRESETS, get_palette, get_preset
from qrstudio.render import RenderOptions, render
from qrstudio.shapes import MODULE_STYLES, style_name

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


def catalog() -> dict:
    shapes = []
    for category, keys in SHAPE_CATEGORIES.items():
        shapes.append(
            {
                "key": category,
                "name": category,
                "items": [_card("shape", key, shape_name(key)) for key in keys],
            }
        )
    modules = [_card("module", key, style_name(key)) for key in MODULE_STYLES]
    eyes = [_card("eye", key, eye_name(key)) for key in eye_keys()]
    palettes = [_card("palette", key, get_palette(key).name) for key in PALETTES]
    presets = []
    for key, preset in PRESETS.items():
        presets.append(
            _card(
                "preset",
                key,
                preset.name,
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


async def catalog_handler(_: web.Request) -> web.Response:
    return web.json_response(catalog(), dumps=lambda value: json.dumps(value, ensure_ascii=False), headers={"Cache-Control": "no-cache"})


async def thumb_handler(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    key = request.match_info["key"]
    try:
        payload = await asyncio.to_thread(thumb_bytes, kind, key)
    except KeyError:
        raise web.HTTPNotFound()
    return web.Response(body=payload, content_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


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


def setup(app: web.Application) -> None:
    app.router.add_get("/app", index)
    app.router.add_get("/app/", index)
    app.router.add_get("/app/catalog.json", catalog_handler)
    app.router.add_get("/app/thumb/{kind}/{key}.png", thumb_handler)
    app.router.add_get("/app/preview.png", preview_handler)
    app.router.add_static("/app/static/", WEBAPP_DIR, name="webapp-static")
    if THUMBS_DIR.exists():
        app.router.add_static("/app/thumbs/", THUMBS_DIR, name="webapp-thumbs")
