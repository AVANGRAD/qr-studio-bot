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

from ..i18n import current_lang, t
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
        await message.answer(t("settings_bad_json"))
        return
    if not isinstance(payload, dict):
        await message.answer(t("settings_bad_json"))
        return
    draft = get_draft(await state.get_data())
    if draft is None:
        pending = sanitize_settings(payload)
        if not pending:
            await message.answer(t("settings_bad_values"))
            return
        data = await state.get_data()
        data["pending_webapp"] = pending
        await state.set_data(data)
        await state.set_state(Flow.content)
        await message.answer(t("settings_pending_saved"))
        return

    if not sanitize_settings(payload):
        await message.answer(t("settings_unchanged"))
        return
    apply_settings(draft, payload)
    await send_preview(message, state, draft, size=640)


@router.message(Command("app"))
async def open_app(message: Message, state: FSMContext) -> None:
    if getattr(message.chat, "type", "private") != "private":
        await message.answer(t("webapp_private"))
        return
    draft = get_draft(await state.get_data())
    url = webapp_url(draft) if draft is not None else webapp_entry_url(current_lang.get())
    await message.answer(
        t("webapp_open"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t("webapp_open_button"), web_app=WebAppInfo(url=url))]]
        ),
    )
