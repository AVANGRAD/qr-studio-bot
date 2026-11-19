from __future__ import annotations

import json
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from ..services import webapp_entry_url, webapp_url
from ..states import Flow
from ..webapp_settings import apply_settings, sanitize_settings
from .common import get_draft, send_preview

router = Router(name="webapp")
logger = logging.getLogger(__name__)


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
        pending = sanitize_settings(payload)
        if not pending:
            await message.answer("Не удалось прочитать настройки. Попробуй выбрать другой вариант.")
            return
        data = await state.get_data()
        data["pending_webapp"] = pending
        await state.set_data(data)
        await state.set_state(Flow.content)
        await message.answer("Настройки сохранены. Пришли ссылку или текст — применю их.")
        return

    if not sanitize_settings(payload):
        await message.answer("Настройки не изменились. Попробуй выбрать другой вариант.")
        return
    apply_settings(draft, payload)
    await send_preview(message, state, draft, size=640)


@router.message(Command("app"))
async def open_app(message: Message, state: FSMContext) -> None:
    if getattr(message.chat, "type", "private") != "private":
        await message.answer("Визуальный редактор доступен в личном чате с ботом.")
        return
    draft = get_draft(await state.get_data())
    url = webapp_url(draft) if draft is not None else webapp_entry_url()
    await message.answer(
        "Открой визуальный редактор:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Открыть редактор", web_app=WebAppInfo(url=url))]]
        ),
    )
