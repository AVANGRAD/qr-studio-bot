from __future__ import annotations

import asyncio
import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from qrstudio.emblems import EMBLEMS, emblem_image

from ..i18n import display_name, t
from ..keyboards import LOGO_MODES, emblem_menu, logo_menu
from ..services import ContentError, Draft, prepare_uploaded_logo
from ..states import Flow
from .common import clear_flow, get_draft, send_preview

router = Router(name="logo")
logger = logging.getLogger(__name__)


async def _show(callback: CallbackQuery, text: str, keyboard) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:  # noqa: BLE001
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "logo:menu")
async def logo_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    draft = get_draft(await state.get_data()) or Draft(content="")
    await _show(callback, t("logo_root"), logo_menu(draft))


@router.callback_query(F.data.startswith("logo:presets:"))
async def logo_presets(callback: CallbackQuery) -> None:
    parts = (callback.data or "").split(":")
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    await callback.answer()
    await _show(callback, t("logo_presets"), emblem_menu(page))


@router.callback_query(F.data.startswith("logo:preset:"))
async def logo_preset(callback: CallbackQuery, state: FSMContext) -> None:
    key = (callback.data or "").split(":", 2)[-1]
    emblem = EMBLEMS.get(key)
    if emblem is None:
        await callback.answer(t("unknown_icon"), show_alert=True)
        return
    image = emblem_image(key, 512)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    payload = buffer.getvalue()
    name = display_name("emblem", key)
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_logo"] = payload
        data["pending_logo_mode"] = "plate"
        data["pending_logo_emblem"] = key
        data["pending_logo_label"] = ""
        data.pop("pending_monogram", None)
        await state.set_data(data)
        await state.set_state(None)
        await callback.answer(t("icon_label", name=name))
        await callback.message.answer(t("icon_saved"))
        return
    draft.logo_png = payload
    if draft.logo_mode == "monogram":
        draft.logo_mode = "plate"
    draft.logo_emblem = key
    draft.logo_label = ""
    await callback.answer(t("icon_label", name=name))
    await send_preview(callback.message, state, draft, size=640)


@router.callback_query(F.data == "logo:upload")
async def logo_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.logo)
    await callback.message.answer(t("logo_prompt"))


@router.callback_query(F.data.in_({"logo:monogram", "logo:mode:monogram"}))
async def logo_monogram(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.monogram)
    await callback.message.answer(t("monogram_prompt"))


@router.callback_query(F.data.startswith("logo:mode:"))
async def logo_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = (callback.data or "").split(":", 2)[-1]
    if mode not in LOGO_MODES:
        await callback.answer(t("unknown_mode"), show_alert=True)
        return
    data = await state.get_data()
    draft = get_draft(data)
    if mode != "monogram" and draft is not None and not draft.has_logo and not data.get("pending_logo"):
        await callback.answer(t("logo_needed"), show_alert=True)
        return
    if draft is None:
        if not data.get("pending_logo"):
            await callback.answer(t("no_draft"), show_alert=True)
            return
        data["pending_logo_mode"] = mode
        await state.set_data(data)
        await callback.answer(t("mode_saved"))
        return
    draft.logo_mode = mode
    await callback.answer(t("mode_updated"))
    await send_preview(callback.message, state, draft, size=640)


@router.callback_query(F.data == "logo:clear")
async def logo_clear(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data.pop("pending_logo", None)
    data.pop("pending_logo_mode", None)
    data.pop("pending_logo_label", None)
    data.pop("pending_logo_emblem", None)
    await state.set_data(data)
    draft = get_draft(data)
    if draft is None:
        await callback.answer(t("logo_cleared"))
        return
    draft.logo_png = None
    draft.logo_mode = "plate"
    draft.logo_label = ""
    draft.logo_emblem = ""
    await callback.answer(t("logo_cleared"))
    await send_preview(callback.message, state, draft, size=640)


@router.message(StateFilter(Flow.logo), F.photo)
async def photo_logo(message: Message, state: FSMContext, bot: Bot) -> None:
    await _accept_logo(message, state, bot, message.photo[-1])


@router.message(StateFilter(Flow.logo), F.document)
async def document_logo(message: Message, state: FSMContext, bot: Bot) -> None:
    document = message.document
    if document is None or not (document.mime_type or "").startswith("image/"):
        await message.answer(t("not_image"))
        return
    await _accept_logo(message, state, bot, document)


async def _accept_logo(message: Message, state: FSMContext, bot: Bot, file) -> None:
    if getattr(file, "file_size", None) and file.file_size > 8 * 1024 * 1024:
        await message.answer(t("logo_too_large"))
        return
    await message.answer(t("logo_processing"))
    buffer = io.BytesIO()
    try:
        await bot.download(file, destination=buffer)
        prepared = await asyncio.to_thread(prepare_uploaded_logo, buffer.getvalue())
    except ContentError as exc:
        await message.answer(str(exc))
        return
    except Exception:
        logger.exception("logo download failed")
        await message.answer(t("logo_download_failed"))
        return
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_logo"] = prepared
        data["pending_logo_label"] = ""
        data["pending_logo_emblem"] = ""
        data.pop("pending_monogram", None)
        await state.set_data(data)
        await state.set_state(None)
        await message.answer(t("logo_saved"))
        return
    draft.logo_png = prepared
    draft.logo_mode = "plate"
    draft.logo_label = ""
    draft.logo_emblem = ""
    await clear_flow(state)
    await message.answer(t("logo_added"))
    await send_preview(message, state, draft, size=640)


@router.message(StateFilter(Flow.monogram), F.text)
async def on_monogram(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not 1 <= len(text) <= 2:
        await message.answer(t("monogram_length"))
        return
    text = text.upper()
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_monogram"] = text
        await state.set_data(data)
        await state.set_state(None)
        await message.answer(t("monogram_saved"))
        return
    draft.logo_mode = "monogram"
    draft.logo_text = text
    draft.logo_label = ""
    draft.logo_emblem = ""
    await clear_flow(state)
    await send_preview(message, state, draft, size=640)
