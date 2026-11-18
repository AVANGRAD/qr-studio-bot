from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..services import ContentError, Draft, get_preset, normalize_content, rate_limiter
from ..states import Flow
from ..texts import NO_DRAFT, PHOTO_NEEDED, RENDER_ERROR, RESET
from ..webapp_settings import apply_settings
from .common import get_draft, send_document, send_preview

router = Router(name="create")
logger = logging.getLogger(__name__)


@router.message(Command("qr"))
async def qr_command(message: Message, command: CommandObject, state: FSMContext) -> None:
    if not command.args:
        await state.set_state(Flow.content)
        await message.answer("Пришли текст после /qr или просто отправь ссылку.")
        return
    await _accept_content(message, state, command.args)


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current == Flow.logo.state:
        await message.answer("Жду картинку-логотип: PNG, JPG или WebP до 6 МБ.")
        return
    if current == Flow.monogram.state:
        return
    if current == Flow.photo.state:
        await message.answer(PHOTO_NEEDED)
        return
    if current == Flow.content.state:
        data = await state.get_data()
        if data.get("pending_webapp"):
            await state.set_state(None)
        else:
            await state.clear()
    await _accept_content(message, state, message.text or "")


async def _accept_content(message: Message, state: FSMContext, raw: str) -> None:
    if message.from_user is None:
        return
    allowed, reason = rate_limiter.allow(message.from_user.id)
    if not allowed:
        await message.answer(reason)
        return
    try:
        content = normalize_content(raw)
    except ContentError as exc:
        await message.answer(str(exc))
        return
    data = await state.get_data()
    draft = get_draft(data)
    if draft is None:
        draft = Draft(content=content)
        preset = get_preset("blue_dots")
        draft.shape = preset.shape
        draft.module_style = preset.module_style
        draft.eye_style = preset.eye_style
        draft.palette = preset.palette
        if data.get("pending_logo"):
            draft.logo_png = data["pending_logo"]
            draft.logo_mode = data.get("pending_logo_mode", "plate")
        if data.get("pending_monogram"):
            draft.logo_mode = "monogram"
            draft.logo_text = data["pending_monogram"]
        if data.get("pending_photo"):
            draft.photo_bytes = data["pending_photo"]
        pending_webapp = data.get("pending_webapp")
        if isinstance(pending_webapp, dict):
            apply_settings(draft, pending_webapp)
        data.pop("pending_logo", None)
        data.pop("pending_logo_mode", None)
        data.pop("pending_monogram", None)
        data.pop("pending_photo", None)
        data.pop("pending_webapp", None)
        await state.set_data(data)
    else:
        draft.content = content
    try:
        await send_preview(message, state, draft)
    except Exception:
        logger.exception("failed to render preview")
        await message.answer(RENDER_ERROR)


@router.callback_query(F.data == "dl:png")
async def download_png(callback: CallbackQuery, state: FSMContext) -> None:
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    await callback.answer("Собираю PNG…")
    try:
        await send_document(callback.bot, callback.from_user.id, draft, "png")
    except Exception:
        logger.exception("png download failed")
        await callback.message.answer(RENDER_ERROR)


@router.callback_query(F.data == "dl:svg")
async def download_svg(callback: CallbackQuery, state: FSMContext) -> None:
    draft = get_draft(await state.get_data())
    if draft is None:
        await callback.answer(NO_DRAFT, show_alert=True)
        return
    await callback.answer("Собираю SVG…")
    try:
        await send_document(callback.bot, callback.from_user.id, draft, "svg")
    except Exception:
        logger.exception("svg download failed")
        await callback.message.answer(RENDER_ERROR)


@router.callback_query(F.data == "draft:reset")
async def reset_draft(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(RESET)
