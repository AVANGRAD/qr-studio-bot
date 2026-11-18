from __future__ import annotations

import asyncio
import io
import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import LOGO_MODES, logo_menu
from ..services import ContentError, Draft, prepare_uploaded_logo
from ..states import Flow
from ..texts import LOGO_NEEDED, LOGO_PROMPT, MONOGRAM_PROMPT, NO_DRAFT
from .common import get_draft, send_preview

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
    await _show(
        callback,
        "<b>Логотип</b>\nЗагрузи картинку или выбери монограмму.\n"
        "Плашка — логотип на подложке, вырез — QR «расступается», "
        "текстура — логотип внутри модулей, фон — водяной знак, угол — маленький логотип в углу.",
        logo_menu(draft),
    )


@router.callback_query(F.data == "logo:upload")
async def logo_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.logo)
    await callback.message.answer(LOGO_PROMPT)


@router.callback_query(F.data.in_({"logo:monogram", "logo:mode:monogram"}))
async def logo_monogram(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(Flow.monogram)
    await callback.message.answer(MONOGRAM_PROMPT)


@router.callback_query(F.data.startswith("logo:mode:"))
async def logo_mode(callback: CallbackQuery, state: FSMContext) -> None:
    mode = (callback.data or "").split(":", 2)[-1]
    if mode not in LOGO_MODES:
        await callback.answer("Неизвестный режим", show_alert=True)
        return
    data = await state.get_data()
    draft = get_draft(data)
    if mode != "monogram" and draft is not None and not draft.has_logo and not data.get("pending_logo"):
        await callback.answer(LOGO_NEEDED, show_alert=True)
        return
    if draft is None:
        if not data.get("pending_logo"):
            await callback.answer(NO_DRAFT, show_alert=True)
            return
        data["pending_logo_mode"] = mode
        await state.set_data(data)
        await callback.answer("Режим сохранён")
        return
    draft.logo_mode = mode
    await callback.answer("Режим обновлён")
    await send_preview(callback.message, state, draft, size=640)


@router.callback_query(F.data == "logo:clear")
async def logo_clear(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    data.pop("pending_logo", None)
    data.pop("pending_logo_mode", None)
    await state.set_data(data)
    draft = get_draft(data)
    if draft is None:
        await callback.answer("Логотип убран")
        return
    draft.logo_png = None
    draft.logo_mode = "plate"
    await callback.answer("Логотип убран")
    await send_preview(callback.message, state, draft, size=640)


@router.message(StateFilter(Flow.logo), F.photo)
async def photo_logo(message: Message, state: FSMContext, bot: Bot) -> None:
    await _accept_logo(message, state, bot, message.photo[-1])


@router.message(StateFilter(Flow.logo), F.document)
async def document_logo(message: Message, state: FSMContext, bot: Bot) -> None:
    document = message.document
    if document is None or not (document.mime_type or "").startswith("image/"):
        await message.answer("Это не картинка. Пришли PNG, JPG или WebP.")
        return
    await _accept_logo(message, state, bot, document)


async def _accept_logo(message: Message, state: FSMContext, bot: Bot, file) -> None:
    if getattr(file, "file_size", None) and file.file_size > 8 * 1024 * 1024:
        await message.answer("Файл больше 8 МБ. Пришли картинку поменьше.")
        return
    await message.answer("Обрабатываю логотип…")
    buffer = io.BytesIO()
    try:
        await bot.download(file, destination=buffer)
        prepared = await asyncio.to_thread(prepare_uploaded_logo, buffer.getvalue())
    except ContentError as exc:
        await message.answer(str(exc))
        return
    except Exception:
        logger.exception("logo download failed")
        await message.answer("Не удалось скачать логотип. Попробуй ещё раз.")
        return
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_logo"] = prepared
        await state.set_data(data)
        await state.set_state(None)
        await message.answer("Логотип сохранён. Теперь пришли ссылку или текст для QR.")
        return
    draft.logo_png = prepared
    draft.logo_mode = "plate"
    await state.clear()
    await message.answer("Логотип добавлен.")
    await send_preview(message, state, draft, size=640)


@router.message(StateFilter(Flow.monogram), F.text)
async def on_monogram(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not 1 <= len(text) <= 2:
        await message.answer("Нужно 1–2 символа. Например: АК или QR.")
        return
    text = text.upper()
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        data["pending_monogram"] = text
        await state.set_data(data)
        await state.set_state(None)
        await message.answer("Монограмма сохранена. Теперь пришли ссылку или текст для QR.")
        return
    draft.logo_mode = "monogram"
    draft.logo_text = text
    await state.clear()
    await send_preview(message, state, draft, size=640)
