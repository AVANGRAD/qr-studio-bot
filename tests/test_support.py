from __future__ import annotations

from types import SimpleNamespace

import pytest
from aiogram.types import Chat, User

from bot.i18n import use_lang
from bot.services import RateLimiter
from bot.support import SupportStore, _ticket_header, support_message


def _user(user_id: int, username: str = "user") -> User:
    return User(id=user_id, is_bot=False, first_name="Test", username=username, language_code="ru")


class FakeMessage:
    def __init__(self, user: User, message_id: int = 1, chat_type: str = "private") -> None:
        self.from_user = user
        self.message_id = message_id
        self.chat = Chat(id=user.id, type=chat_type)
        self.reply_to_message = None
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs) -> None:
        self.answers.append(text)


class FakeBot:
    def __init__(self) -> None:
        self.forwarded: list[tuple[int, int, int]] = []
        self.sent: list[tuple[int, str]] = []
        self.copied: list[tuple[int, int, int]] = []

    async def forward_message(self, chat_id: int, from_chat_id: int, message_id: int):
        self.forwarded.append((chat_id, from_chat_id, message_id))
        return SimpleNamespace(message_id=100)

    async def send_message(self, chat_id: int, text: str, **kwargs):
        self.sent.append((chat_id, text))
        return SimpleNamespace(message_id=101)

    async def copy_message(self, chat_id: int, from_chat_id: int, message_id: int):
        self.copied.append((chat_id, from_chat_id, message_id))


def test_ticket_header_contains_user_and_ticket() -> None:
    message = FakeMessage(_user(42, "tester"), message_id=7)
    with use_lang("ru"):
        text = _ticket_header(message, 100)
    assert "Обращение #100" in text
    assert "Test" in text
    assert "@tester" in text
    assert "42" in text


@pytest.mark.asyncio
async def test_support_store_memory_mapping() -> None:
    store = SupportStore(None)
    await store.connect()
    assert not store.ready
    await store.remember(100, 42)
    assert await store.resolve(100) == 42
    assert await store.resolve(999) is None
    await store.close()


@pytest.mark.asyncio
async def test_support_user_message_forwards_to_admin_and_maps_reply() -> None:
    store = SupportStore(None)
    await store.connect()
    bot = FakeBot()
    user = _user(42, "tester")
    message = FakeMessage(user, message_id=7)
    await support_message(message, bot, support_store=store, admin_id=99)
    assert bot.forwarded == [(99, 42, 7)]
    assert await store.resolve(100) == 42
    assert await store.resolve(101) == 42
    assert message.answers == ["✅ Сообщение отправлено в поддержку. Ответ придёт в этот чат."]

    reply = FakeMessage(_user(99, "admin"), message_id=5)
    reply.reply_to_message = SimpleNamespace(message_id=101, forward_from=None)
    await support_message(reply, bot, support_store=store, admin_id=99)
    assert bot.copied == [(42, 99, 5)]
    assert reply.answers == ["✅ Ответ отправлен пользователю <code>42</code>."]


@pytest.mark.asyncio
async def test_support_requires_private_chat_and_admin_context() -> None:
    store = SupportStore(None)
    await store.connect()
    bot = FakeBot()
    group = FakeMessage(_user(42), chat_type="group")
    await support_message(group, bot, support_store=store, admin_id=99)
    assert group.answers == ["Напиши в личные сообщения бота, чтобы обратиться в поддержку."]
    assert bot.forwarded == []

    stranger = FakeMessage(_user(42), chat_type="private")
    await support_message(stranger, bot, support_store=None, admin_id=None)
    assert stranger.answers == ["Поддержка ещё не настроена."]


@pytest.mark.asyncio
async def test_support_rate_limits_user_messages() -> None:
    store = SupportStore(None)
    await store.connect()
    bot = FakeBot()
    limiter = RateLimiter(per_minute=1, per_hour=10, per_day=10)
    first = FakeMessage(_user(42), message_id=7)
    await support_message(first, bot, support_store=store, admin_id=99, limiter=limiter)
    second = FakeMessage(_user(42), message_id=8)
    await support_message(second, bot, support_store=store, admin_id=99, limiter=limiter)
    assert len(bot.forwarded) == 1
    assert second.answers == ["Слишком много сообщений. Подожди немного и попробуй снова."]
