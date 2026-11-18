from __future__ import annotations

import logging

from aiogram.types import ErrorEvent

from .texts import RENDER_ERROR

logger = logging.getLogger(__name__)


async def error_handler(event: ErrorEvent) -> None:
    logger.exception("update failed: %s", event.exception, exc_info=event.exception)
    update = event.update
    message = update.message or (update.callback_query.message if update.callback_query else None)
    if message is not None:
        try:
            await message.answer(RENDER_ERROR)
        except Exception:
            logger.exception("failed to report error")
