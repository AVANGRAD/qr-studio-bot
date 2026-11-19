from __future__ import annotations

import asyncio
import io
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..i18n import t
from ..keyboards import photo_menu
from ..services import ContentError, prepare_uploaded_photo
from ..states import Flow
from .common import clear_flow, get_draft, send_preview

router = Router(name="photo")
logger = logging.getLogger(__name__)


async def _show(callback: CallbackQuery, text: str, keyboard) -> None:
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        await callback.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "photo:menu")
async def photo_root(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    draft = get_draft(await state.get_data())
    await _show(
        callback,
        t("photo_root"),
        photo_menu(draft),
    )


@router.callback_query(F.data == "photo:upload")
async def photo_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.photo)
    await callback.message.answer(t("photo_prompt"))


@router.callback_query(F.data == "photo:clear")
async def photo_clear(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data.pop("pending_photo", None)
    await state.set_data(data)
    draft = get_draft(data)
    if draft is None:
        await callback.answer(t("photo_cleared"))
        return
    draft.photo_bytes = None
    await callback.answer(t("photo_cleared"))
    await send_preview(callback.message, state, draft, size=640)


@router.message(StateFilter(None, Flow.content), F.photo)
@router.message(StateFilter(Flow.photo), F.photo)
async def photo_message(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.photo is None:
        return
    await _accept_photo(message, state, bot, message.photo[-1])


@router.message(StateFilter(None, Flow.content), F.document)
@router.message(StateFilter(Flow.photo), F.document)
async def document_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    document = message.document
    if document is None or not (document.mime_type or "").startswith("image/"):
        await message.answer(t("not_image"))
        return
    await _accept_photo(message, state, bot, document)


@router.message(StateFilter(Flow.photo), F.text)
async def photo_text(message: Message) -> None:
    await message.answer(t("photo_needed"))


async def _accept_photo(message: Message, state: FSMContext, bot: Bot, file) -> None:
    if getattr(file, "file_size", None) and file.file_size > 12 * 1024 * 1024:
        await message.answer(t("photo_too_large"))
        return
    await message.answer(t("photo_processing"))
    buffer = io.BytesIO()
    try:
        await bot.download(file, destination=buffer)
        prepared = await asyncio.to_thread(prepare_uploaded_photo, buffer.getvalue())
    except ContentError as exc:
        await message.answer(str(exc))
        return
    except Exception:
        logger.exception("photo download failed")
        await message.answer(t("photo_download_failed"))
        return
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_photo"] = prepared
        await state.set_data(data)
        await state.set_state(None)
        await message.answer(t("photo_saved"))
        return
    draft.photo_bytes = prepared
    await clear_flow(state)
    await message.answer(t("photo_added"))
    await send_preview(message, state, draft, size=640)
