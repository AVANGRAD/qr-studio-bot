from __future__ import annotations

from datetime import UTC, datetime

import pytest
from aiogram.types import CallbackQuery, Chat, Message, Update, User, WebAppData

from bot.analytics import (
    Analytics,
    AnalyticsMiddleware,
    StatsSnapshot,
    event_from_update,
)
from bot.handlers.admin import format_stats, stats_command
from bot.i18n import use_lang


def _user(user_id: int = 42) -> User:
    return User(id=user_id, is_bot=False, first_name="Test", username="tester", language_code="ru")


def _message(text: str | None = None, web_app_data: str | None = None) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=42, type="private"),
        from_user=_user(),
        text=text,
        web_app_data=WebAppData(button_text="Open", data=web_app_data) if web_app_data is not None else None,
    )


def _snapshot() -> StatsSnapshot:
    return StatsSnapshot(
        total=10,
        new_today=2,
        new_week=5,
        new_month=7,
        online=1,
        dau=3,
        wau=8,
        mau=9,
        dormant=4,
        blocked=1,
        languages=(("ru", 7), ("en", 3)),
        events=(("png_download", 6), ("start", 4)),
        total_events=42,
        events_all=(("message", 20), ("png_download", 8)),
    )


def test_event_from_update_maps_known_updates() -> None:
    assert event_from_update(Update(update_id=1, message=_message("/start"))) == "start"
    assert event_from_update(Update(update_id=2, message=_message("/qr hello"))) == "command"
    assert event_from_update(Update(update_id=3, message=_message("hello"))) == "message"
    assert event_from_update(Update(update_id=4, message=_message(web_app_data="{}"))) == "mini_app_apply"
    callback = CallbackQuery(id="1", from_user=_user(), chat_instance="test", data="dl:png")
    assert event_from_update(Update(update_id=5, callback_query=callback)) == "png_download"
    callback = CallbackQuery(id="2", from_user=_user(), chat_instance="test", data="lang:set:en")
    assert event_from_update(Update(update_id=6, callback_query=callback)) == "language_change"
    callback = CallbackQuery(id="3", from_user=_user(), chat_instance="test", data="unknown")
    assert event_from_update(Update(update_id=7, callback_query=callback)) == "callback"


def test_format_stats_ru_and_en() -> None:
    with use_lang("ru"):
        text = format_stats(_snapshot())
    assert "Всего пользователей: 10" in text
    assert "Всего событий за всё время: 42" in text
    assert "События за всё время:" in text
    assert "сообщение: 20" in text
    assert "скачивание PNG: 6" in text
    assert "ru: 7 · en: 3" in text

    with use_lang("en"):
        text = format_stats(_snapshot())
    assert "Total users: 10" in text
    assert "Total events all time: 42" in text
    assert "Events all time:" in text
    assert "message: 20" in text
    assert "PNG download: 6" in text
    assert "ru: 7 · en: 3" in text


class FakeMessage:
    def __init__(self, chat_type: str = "private") -> None:
        self.from_user = _user()
        self.chat = Chat(id=42, type=chat_type)
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs) -> None:
        self.answers.append(text)


class FakeAnalytics:
    ready = True

    def __init__(self) -> None:
        self.events: list[tuple[int, str]] = []

    def schedule_update(self, user, event_type: str, metadata=None) -> None:
        self.events.append((user.id, event_type))

    async def stats(self) -> StatsSnapshot:
        return _snapshot()


@pytest.mark.asyncio
async def test_stats_command_is_private_to_admin() -> None:
    analytics = FakeAnalytics()
    message = FakeMessage()
    await stats_command(message, analytics=analytics, admin_id=42)
    assert message.answers

    stranger = FakeMessage()
    stranger.from_user = _user(99)
    await stats_command(stranger, analytics=analytics, admin_id=42)
    assert not stranger.answers

    unconfigured = FakeMessage()
    await stats_command(unconfigured, analytics=analytics, admin_id=None)
    assert not unconfigured.answers

    group = FakeMessage(chat_type="group")
    await stats_command(group, analytics=analytics, admin_id=42)
    assert not group.answers


@pytest.mark.asyncio
async def test_stats_command_reports_unavailable_database() -> None:
    message = FakeMessage()
    await stats_command(message, analytics=Analytics(None), admin_id=42)
    assert message.answers == ["Аналитика недоступна: нет подключения к базе."]


@pytest.mark.asyncio
async def test_analytics_middleware_injects_data_and_records_event() -> None:
    analytics = FakeAnalytics()
    middleware = AnalyticsMiddleware(analytics, admin_id=42)
    update = Update(update_id=1, message=_message("/start"))

    async def handler(event, data):
        return data

    data = await middleware(handler, update, {"event_from_user": _user()})
    assert data["admin_id"] == 42
    assert data["analytics"] is analytics
    assert analytics.events == [(42, "start")]


@pytest.mark.asyncio
async def test_analytics_without_database_is_disabled() -> None:
    analytics = Analytics(None)
    await analytics.connect()
    assert not analytics.ready
    analytics.schedule_update(_user(), "start")
    assert analytics._tasks == set()
    assert await analytics.stats() is None
    await analytics.close()
