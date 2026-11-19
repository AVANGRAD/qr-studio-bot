from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..analytics import Analytics, StatsSnapshot
from ..i18n import current_lang, t

router = Router(name="admin")
logger = logging.getLogger(__name__)

EVENT_LABELS = {
    "start": ("старт", "start"),
    "command": ("команда", "command"),
    "message": ("сообщение", "message"),
    "message_edit": ("изменение сообщения", "message edit"),
    "mini_app_apply": ("настройки Mini App", "Mini App settings"),
    "png_download": ("скачивание PNG", "PNG download"),
    "svg_download": ("скачивание SVG", "SVG download"),
    "language_change": ("смена языка", "language change"),
    "preset_apply": ("пресет", "preset"),
    "shape_change": ("форма", "shape"),
    "pattern_change": ("узор", "pattern"),
    "eye_change": ("глаза", "eyes"),
    "palette_change": ("палитра", "palette"),
    "size_change": ("размер", "size"),
    "logo_change": ("логотип", "logo"),
    "new_qr": ("новый QR", "new QR"),
    "random_style": ("случайный стиль", "random style"),
    "photo": ("фото", "photo"),
    "document": ("документ", "document"),
    "callback": ("кнопка", "button"),
    "payment": ("оплата", "payment"),
    "inline_query": ("inline-запрос", "inline query"),
    "chat_member": ("участник чата", "chat member"),
    "pre_checkout_query": ("проверка оплаты", "checkout"),
    "other": ("другое", "other"),
}


def event_label(name: str) -> str:
    pair = EVENT_LABELS.get(name)
    if pair is None:
        return name
    return pair[1] if current_lang.get() == "en" else pair[0]


def format_stats(snapshot: StatsSnapshot) -> str:
    languages = " · ".join(f"{code}: {count}" for code, count in snapshot.languages) or "—"
    lines = [
        t("stats_title"),
        "",
        t("stats_total", total=snapshot.total),
        t("stats_all_time_events", total=snapshot.total_events),
        t("stats_new", today=snapshot.new_today, week=snapshot.new_week, month=snapshot.new_month),
        t(
            "stats_active",
            online=snapshot.online,
            dau=snapshot.dau,
            wau=snapshot.wau,
            mau=snapshot.mau,
        ),
        t("stats_inactive", dormant=snapshot.dormant),
        t("stats_blocked", blocked=snapshot.blocked),
        t("stats_languages", languages=languages),
    ]
    if snapshot.events:
        lines.extend(["", t("stats_events")])
        lines.extend(
            t("stats_event_line", name=event_label(name), count=count) for name, count in snapshot.events
        )
    if snapshot.events_all:
        lines.extend(["", t("stats_events_all")])
        lines.extend(
            t("stats_event_line", name=event_label(name), count=count) for name, count in snapshot.events_all
        )
    return "\n".join(lines)


@router.message(Command("stats"))
async def stats_command(
    message: Message,
    analytics: Analytics | None = None,
    admin_id: int | None = None,
) -> None:
    if admin_id is None or message.from_user is None or message.from_user.id != admin_id:
        return
    chat = getattr(message, "chat", None)
    if chat is not None and getattr(chat, "type", "private") != "private":
        return
    if analytics is not None and not analytics.ready:
        await analytics.connect()
    if analytics is None or not analytics.ready:
        await message.answer(t("stats_unavailable"))
        return
    try:
        snapshot = await analytics.stats()
    except Exception:
        logger.exception("failed to load analytics")
        await message.answer(t("stats_error"))
        return
    if snapshot is None:
        await message.answer(t("stats_unavailable"))
        return
    await message.answer(format_stats(snapshot))
