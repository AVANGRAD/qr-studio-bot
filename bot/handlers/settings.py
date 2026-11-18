from __future__ import annotations

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from qrstudio.eyes import EYE_STYLES
from qrstudio.masks import SHAPES
from qrstudio.presets import PALETTES
from qrstudio.shapes import MODULE_STYLES

from ..keyboards import (
    eye_menu,
    palette_menu,
    shape_list,
    shape_menu,
    size_menu,
    style_menu,
)
from ..states import Flow
from ..texts import CONTENT_PROMPT, NO_DRAFT
from .common import get_draft, refresh_preview

router = Router(name="settings")


async def _show(callback: CallbackQuery, text: str, keyboard) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "shape:menu")
async def shapes_root(callback: CallbackQuery) -> None:
    await callback.answer()
    await _show(callback, "<b>Форма</b>\nВыбери категорию.", shape_menu())


@router.callback_query(F.data.startswith("shape:cat:"))
async def shapes_category(callback: CallbackQuery) -> None:
    await callback.answer()
    parts = (callback.data or "").split(":")
    category = parts[2] if len(parts) > 2 else "geometry"
    page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
    await _show(callback, "<b>Форма</b>\nВыбери силуэт.", shape_list(category, page))


@router.callback_query(F.data.startswith("shape:set:"))
async def shapes_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    if key not in SHAPES:
        await callback.answer("Неизвестная форма", show_alert=True)
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    draft.shape = key
    await callback.answer("Форма обновлена")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data.startswith("style:menu:"))
async def styles_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = (callback.data or "").split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    draft = get_draft(await state.get_data())
    await _show(callback, "<b>Узор модулей</b>\nВыбери рисунок точек.", style_menu(page, draft.module_style if draft else None))


@router.callback_query(F.data.startswith("style:set:"))
async def styles_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    if key not in MODULE_STYLES:
        await callback.answer("Неизвестный узор", show_alert=True)
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    draft.module_style = key
    await callback.answer("Узор обновлён")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data == "eye:menu")
async def eyes_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    draft = get_draft(await state.get_data())
    await _show(callback, "<b>Глаза</b>\nСтиль трёх угловых маркеров.", eye_menu(draft.eye_style if draft else None))


@router.callback_query(F.data.startswith("eye:set:"))
async def eyes_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    if key not in EYE_STYLES:
        await callback.answer("Неизвестный стиль глаз", show_alert=True)
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    draft.eye_style = key
    await callback.answer("Глаза обновлены")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data.startswith("pal:menu:"))
async def palettes_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    parts = (callback.data or "").split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    draft = get_draft(await state.get_data())
    await _show(callback, "<b>Палитра</b>\nЦвет и контраст.", palette_menu(page, draft.palette if draft else None))


@router.callback_query(F.data.startswith("pal:set:"))
async def palettes_set(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    if key not in PALETTES:
        await callback.answer("Неизвестная палитра", show_alert=True)
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    draft.palette = key
    await callback.answer("Палитра обновлена")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data == "size:menu")
async def sizes_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    await _show(callback, "<b>Размер</b>\nДля печати лучше 1024–2048 px.", size_menu(draft.size))


@router.callback_query(F.data.startswith("size:set:"))
async def sizes_set(callback: CallbackQuery, state: FSMContext) -> None:
    raw = (callback.data or "").split(":")[-1]
    if raw not in {"512", "1024", "2048"}:
        await callback.answer("Неизвестный размер", show_alert=True)
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    draft.size = int(raw)
    await callback.answer("Размер обновлён")
    await refresh_preview(callback, state, draft)


@router.callback_query(F.data == "back:editor")
async def back_editor(callback: CallbackQuery, state: FSMContext) -> None:
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer()
        await state.set_state(Flow.content)
        await callback.message.answer(CONTENT_PROMPT)
        return
    await callback.answer()
    await refresh_preview(callback, state, draft)
