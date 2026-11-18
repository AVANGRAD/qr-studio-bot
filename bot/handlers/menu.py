from __future__ import annotations

import random

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from ..keyboards import preset_menu
from ..services import get_preset
from ..states import Flow
from ..texts import CONTENT_PROMPT, NO_DRAFT
from .common import get_draft, refresh_preview

router = Router(name="menu")


async def _show(callback: CallbackQuery, text: str, keyboard) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "menu:presets")
async def presets_root(callback: CallbackQuery) -> None:
    await callback.answer()
    await _show(callback, "<b>Пресеты</b>\nГотовые сочетания формы, узора и цвета.", preset_menu(0))


@router.callback_query(F.data.startswith("preset:menu:"))
async def presets_page(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = (callback.data or "").split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    await _show(callback, "<b>Пресеты</b>\nГотовые сочетания формы, узора и цвета.", preset_menu(page))


@router.callback_query(F.data.startswith("preset:set:"))
async def presets_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        await state.set_state(Flow.content)
        await callback.message.answer(CONTENT_PROMPT)
        return
    preset = get_preset(key)
    draft.shape = preset.shape
    draft.module_style = preset.module_style
    draft.eye_style = preset.eye_style
    draft.palette = preset.palette
    await callback.answer(f"Пресет: {preset.name}")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data == "menu:random")
async def random_preset(callback: CallbackQuery, state: FSMContext) -> None:
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        await state.set_state(Flow.content)
        await callback.message.answer(CONTENT_PROMPT)
        return
    from qrstudio.presets import PRESETS

    key = random.choice(list(PRESETS))
    preset = PRESETS[key]
    draft.shape = preset.shape
    draft.module_style = preset.module_style
    draft.eye_style = preset.eye_style
    draft.palette = preset.palette
    await callback.answer(f"Случайный стиль: {preset.name}")
    await refresh_preview(callback, state, draft)
