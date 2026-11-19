from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from aiogram import Dispatcher, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, Message, Update, User

from bot import i18n
from bot.handlers import start
from bot.handlers.common import clear_flow
from bot.keyboards import editor_kb
from bot.main import set_commands
from bot.services import Draft, caption
from bot.states import Flow
from qrstudio.render import RenderOptions, render


class FakeState:
    def __init__(self) -> None:
        self.data: dict = {}
        self.state: str | None = None

    async def get_data(self) -> dict:
        return dict(self.data)

    async def set_data(self, data: dict) -> None:
        self.data = dict(data)

    async def clear(self) -> None:
        self.data.clear()
        self.state = None

    async def set_state(self, state) -> None:
        self.state = state.state if state is not None else None

    async def get_state(self) -> str | None:
        return self.state


class FakeMessage:
    def __init__(self) -> None:
        self.message_id = 1
        self.chat = SimpleNamespace(id=42)
        self.from_user = User(id=42, is_bot=False, first_name="Test")
        self.answers: list[tuple[str, dict]] = []
        self.edits: list[dict] = []

    async def answer(self, text: str, **kwargs):
        self.answers.append((text, kwargs))
        return SimpleNamespace(message_id=2)

    async def edit_text(self, text: str, **kwargs):
        self.edits.append({"text": text, **kwargs})
        return True


class FakeCallback:
    def __init__(self) -> None:
        self.data = ""
        self.message = FakeMessage()
        self.from_user = User(id=42, is_bot=False, first_name="Test")
        self.alerts: list[str | None] = []

    async def answer(self, text: str | None = None, show_alert: bool = False):
        self.alerts.append(text)
        return True


def test_resolve_lang() -> None:
    assert i18n.resolve_lang(None) == "ru"
    assert i18n.resolve_lang("ru-RU") == "ru"
    assert i18n.resolve_lang("uk") == "ru"
    assert i18n.resolve_lang("en-US") == "en"
    assert i18n.resolve_lang("de") == "en"


def test_dictionaries_have_same_keys() -> None:
    assert set(i18n.TEXTS["ru"]) == set(i18n.TEXTS["en"])


def test_names_have_same_keys() -> None:
    for mapping in i18n.NAME_MAPS.values():
        assert all(len(pair) == 2 for pair in mapping.values())


def test_english_caption_and_buttons() -> None:
    draft = Draft(content="https://example.com", shape="cat", module_style="paw", eye_style="star", palette="gold")
    with i18n.use_lang("en"):
        text = caption(draft)
        buttons = {button.text for row in editor_kb(draft).inline_keyboard for button in row}
    assert "Shape: Cat" in text
    assert "Pattern: Paw" in text
    assert "Download PNG" in buttons
    assert "Скачать" not in " ".join(buttons)


def test_english_emblem_caption() -> None:
    draft = Draft(
        content="https://example.com",
        logo_png=b"png",
        logo_mode="badge",
        logo_emblem="heart",
    )
    with i18n.use_lang("en"):
        text = caption(draft)
    assert "Heart · Badge" in text


def test_english_warning() -> None:
    draft = Draft(content="https://example.com", module_style="unknown")
    result = render(RenderOptions(content=draft.content, module_style=draft.module_style, size=256))
    with i18n.use_lang("en"):
        text = caption(draft, result)
    assert "Unknown module style" in text


@pytest.mark.asyncio
async def test_first_start_shows_language_picker_then_english() -> None:
    state = FakeState()
    message = FakeMessage()
    with i18n.use_lang("en"):
        await start.start(message, state)
    assert message.answers
    assert "Choose your language" in message.answers[0][0]
    keyboard = message.answers[0][1]["reply_markup"].inline_keyboard
    assert {button.callback_data for row in keyboard for button in row} == {"lang:set:ru", "lang:set:en"}

    callback = FakeCallback()
    callback.data = "lang:set:en"
    await start.language_set(callback, state)
    assert state.data == {"lang": "en"}
    assert callback.message.edits
    assert "Send a link or text" in callback.message.edits[0]["text"]

    await clear_flow(state)
    assert state.data == {"lang": "en"}
    assert state.state is None


@pytest.mark.asyncio
async def test_saved_language_wins_over_telegram() -> None:
    state = FakeState()
    await state.set_data({"lang": "en"})
    event = SimpleNamespace()
    user = SimpleNamespace(language_code="ru-RU")
    middleware = i18n.LanguageMiddleware()

    async def handler(event, data):
        return i18n.current_lang.get()

    result = await middleware(handler, event, {"state": state, "event_from_user": user})
    assert result == "en"


@pytest.mark.asyncio
async def test_command_menu_defaults_to_english() -> None:
    class FakeBot:
        def __init__(self) -> None:
            self.calls: list[tuple[list, str | None]] = []

        async def set_my_commands(self, commands, language_code=None):
            self.calls.append((commands, language_code))

    bot = FakeBot()
    await set_commands(bot)
    assert bot.calls[0][1] is None
    assert bot.calls[0][0][0].description == "Start"
    assert bot.calls[1][1] == "ru"
    assert bot.calls[1][0][0].description == "Начать"


@pytest.mark.asyncio
async def test_language_middleware_is_used_by_dispatcher() -> None:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(i18n.LanguageMiddleware())
    router = Router()

    @router.message(CommandStart())
    async def handler(message: Message):
        return i18n.current_lang.get()

    dispatcher.include_router(router)
    update = Update(
        update_id=1,
        message=Message(
            message_id=1,
            date=datetime.now(UTC),
            chat=Chat(id=42, type="private"),
            from_user=User(id=42, is_bot=False, first_name="Test", language_code="en-US"),
            text="/start",
        ),
    )
    assert await dispatcher.feed_update(SimpleNamespace(id=1), update) == "en"


@pytest.mark.asyncio
async def test_saved_language_is_read_from_real_fsm_storage() -> None:
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.outer_middleware(i18n.LanguageMiddleware())
    router = Router()

    @router.message(Command("choose-en"))
    async def choose(message: Message, state):
        await state.set_data({"lang": "en"})
        return "saved"

    @router.message(Command("who"))
    async def who(message: Message):
        return i18n.current_lang.get()

    dispatcher.include_router(router)

    def msg(text: str) -> Update:
        return Update(
            update_id=1,
            message=Message(
                message_id=1,
                date=datetime.now(UTC),
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test", language_code="ru-RU"),
                text=text,
            ),
        )

    bot = SimpleNamespace(id=1)
    assert await dispatcher.feed_update(bot, msg("/choose-en")) == "saved"
    assert await dispatcher.feed_update(bot, msg("/who")) == "en"


@pytest.mark.asyncio
async def test_telegram_language_is_fallback() -> None:
    state = FakeState()
    await state.set_state(Flow.content)
    event = SimpleNamespace()
    user = SimpleNamespace(language_code="en-US")
    middleware = i18n.LanguageMiddleware()

    async def handler(event, data):
        assert data["lang"] == "en"
        return i18n.current_lang.get()

    result = await middleware(handler, event, {"state": state, "event_from_user": user})
    assert result == "en"
