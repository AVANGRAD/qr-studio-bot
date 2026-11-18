from __future__ import annotations

import asyncio
import io
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import photo_menu
from ..services import ContentError, prepare_uploaded_photo
from ..states import Flow
from ..texts import PHOTO_NEEDED, PHOTO_PROMPT
from .common import get_draft, send_preview

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
        "<b>Фото + QR</b>\n\n"
        "Пришли фотографию — она станет фоном. QR будет на светлой карточке "
        "в правом нижнем углу, поэтому фотография останется видимой.\n\n"
        "Лучше выбирать фото с крупным объектом и свободным местом в углу.",
        photo_menu(draft),
    )


@router.callback_query(F.data == "photo:upload")
async def photo_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.photo)
    await callback.message.answer(PHOTO_PROMPT)


@router.callback_query(F.data == "photo:clear")
async def photo_clear(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data.pop("pending_photo", None)
    await state.set_data(data)
    draft = get_draft(data)
    if draft is None:
        await callback.answer("Фото убрано")
        return
    draft.photo_bytes = None
    await callback.answer("Фото убрано")
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
        await message.answer("Это не картинка. Пришли PNG, JPG или WebP.")
        return
    await _accept_photo(message, state, bot, document)


@router.message(StateFilter(Flow.photo), F.text)
async def photo_text(message: Message) -> None:
    await message.answer(PHOTO_NEEDED)


async def _accept_photo(message: Message, state: FSMContext, bot: Bot, file) -> None:
    if getattr(file, "file_size", None) and file.file_size > 12 * 1024 * 1024:
        await message.answer("Фото больше 12 МБ. Пришли картинку поменьше.")
        return
    await message.answer("Обрабатываю фото…")
    buffer = io.BytesIO()
    try:
        await bot.download(file, destination=buffer)
        prepared = await asyncio.to_thread(prepare_uploaded_photo, buffer.getvalue())
    except ContentError as exc:
        await message.answer(str(exc))
        return
    except Exception:
        logger.exception("photo download failed")
        await message.answer("Не удалось скачать фото. Попробуй ещё раз.")
        return
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_photo"] = prepared
        await state.set_data(data)
        await state.set_state(None)
        await message.answer("Фото сохранено. Теперь пришли ссылку или текст для QR.")
        return
    draft.photo_bytes = prepared
    await state.clear()
    await message.answer("Фото добавлено — QR будет на карточке в углу.")
    await send_preview(message, state, draft, size=640)
