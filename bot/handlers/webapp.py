from __future__ import annotations

import json
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from qrstudio.eyes import eye_keys
from qrstudio.masks import SHAPES
from qrstudio.presets import PALETTES, get_preset
from qrstudio.shapes import MODULE_STYLES

from ..states import Flow
from .common import get_draft, send_preview

router = Router(name="webapp")
logger = logging.getLogger(__name__)
SIZES = {512, 1024, 2048}


@router.message(F.web_app_data)
async def on_web_app_data(message: Message, state: FSMContext) -> None:
    raw = message.web_app_data.data if message.web_app_data else ""
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        await message.answer("Не удалось прочитать настройки. Открой редактор ещё раз.")
        return
    if not isinstance(payload, dict):
        await message.answer("Не удалось прочитать настройки. Открой редактор ещё раз.")
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await state.set_state(Flow.content)
        await message.answer("Сначала пришли ссылку или текст для QR, потом открой визуальный редактор.")
        return

    changed = False
    preset_key = payload.get("preset")
    if preset_key:
        try:
            preset = get_preset(preset_key)
        except KeyError:
            preset = None
        if preset is not None:
            draft.shape = preset.shape
            draft.module_style = preset.module_style
            draft.eye_style = preset.eye_style
            draft.palette = preset.palette
            changed = True

    shape = payload.get("shape")
    if isinstance(shape, str) and shape in SHAPES:
        draft.shape = shape
        changed = True
    module = payload.get("module_style")
    if isinstance(module, str) and module in MODULE_STYLES:
        draft.module_style = module
        changed = True
    eye = payload.get("eye_style")
    if isinstance(eye, str) and eye in eye_keys():
        draft.eye_style = eye
        changed = True
    palette = payload.get("palette")
    if isinstance(palette, str) and palette in PALETTES:
        draft.palette = palette
        changed = True
    size = payload.get("size")
    try:
        size_value = int(size)
    except (TypeError, ValueError):
        size_value = 0
    if size_value in SIZES:
        draft.size = size_value
        changed = True

    if not changed:
        await message.answer("Настройки не изменились. Попробуй выбрать другой вариант.")
        return
    await send_preview(message, state, draft, size=640)
