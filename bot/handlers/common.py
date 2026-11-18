from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InputMediaPhoto, Message

from ..keyboards import editor_kb
from ..services import Draft, caption, png_bytes, run_render

logger = logging.getLogger(__name__)


def get_draft(data: dict) -> Draft | None:
    return Draft.from_data(data)


async def _preview_payload(draft: Draft, size: int) -> tuple[BufferedInputFile, str]:
    png, result = await run_render(png_bytes, draft, size)
    return BufferedInputFile(png, filename="qr-preview.png"), caption(draft, result)


async def send_preview(message: Message, state: FSMContext, draft: Draft, size: int = 640) -> None:
    photo, text = await _preview_payload(draft, min(size, max(512, draft.size)))
    sent = await message.answer_photo(photo=photo, caption=text, reply_markup=editor_kb(draft), parse_mode=ParseMode.HTML)
    data = await state.get_data()
    data["draft"] = draft.to_data()
    data["preview_mid"] = sent.message_id
    await state.set_data(data)


async def edit_preview(callback: CallbackQuery, state: FSMContext, draft: Draft, size: int = 640) -> None:
    photo, text = await _preview_payload(draft, min(size, max(512, draft.size)))
    media = InputMediaPhoto(media=photo, caption=text, parse_mode=ParseMode.HTML)
    try:
        await callback.message.edit_media(media, reply_markup=editor_kb(draft))
        message_id = callback.message.message_id
    except TelegramBadRequest as exc:
        logger.debug("edit_media failed: %s", exc)
        sent = await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=editor_kb(draft),
            parse_mode=ParseMode.HTML,
        )
        message_id = sent.message_id
    data = await state.get_data()
    data["draft"] = draft.to_data()
    data["preview_mid"] = message_id
    await state.set_data(data)


async def refresh_preview(callback: CallbackQuery, state: FSMContext, draft: Draft) -> None:
    await edit_preview(callback, state, draft)


async def send_document(bot: Bot, chat_id: int, draft: Draft, kind: str) -> None:
    if kind == "png":
        from ..services import png_bytes as make_png

        payload, result = await run_render(make_png, draft, draft.size, timeout=45)
        document = BufferedInputFile(payload, filename=f"qr-{draft.size}.png")
        await bot.send_document(chat_id, document=document, caption=caption(draft, result), parse_mode=ParseMode.HTML)
    else:
        from ..services import svg_bytes

        payload = await run_render(svg_bytes, draft, timeout=45)
        document = BufferedInputFile(payload.encode("utf-8"), filename=f"qr-{draft.size}.svg")
        await bot.send_document(
            chat_id,
            document=document,
            caption=f"<b>QR Studio</b> · SVG\n<code>{draft.content[:120]}</code>",
            parse_mode=ParseMode.HTML,
        )
