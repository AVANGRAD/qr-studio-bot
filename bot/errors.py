from __future__ import annotations

import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import ErrorEvent

from .i18n import SUPPORTED_LANGS, resolve_lang, t, use_lang

logger = logging.getLogger(__name__)


async def error_handler(event: ErrorEvent, state: FSMContext | None = None) -> None:
    logger.exception("update failed: %s", event.exception, exc_info=event.exception)
    update = event.update
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if message is not None:
        lang: str | None = None
        if state is not None:
            try:
                stored = (await state.get_data()).get("lang")
            except Exception:
                logger.exception("failed to read language from state")
            else:
                if stored in SUPPORTED_LANGS:
                    lang = stored
        if lang is None:
            user = message.from_user
            lang = resolve_lang(getattr(user, "language_code", None))
        with use_lang(lang):
            try:
                await message.answer(t("render_error"))
            except Exception:
                logger.exception("failed to report error")
