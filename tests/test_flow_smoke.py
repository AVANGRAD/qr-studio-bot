from __future__ import annotations

from types import SimpleNamespace

import pytest
from aiogram.types import User

from bot.handlers import create, logo, settings, webapp
from bot.services import Draft
from bot.states import Flow


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
        self.message_id = 100
        self.from_user = User(id=42, is_bot=False, first_name="Test")
        self.text = ""
        self.web_app_data = None
        self.answers: list[tuple] = []
        self.photos: list[dict] = []
        self.documents: list[dict] = []
        self.edits: list[dict] = []

    async def answer(self, text: str, **kwargs):
        self.answers.append((text, kwargs))
        return SimpleNamespace(message_id=self.message_id + 1)

    async def answer_photo(self, photo, caption=None, **kwargs):
        self.photos.append({"photo": photo, "caption": caption, **kwargs})
        return SimpleNamespace(message_id=self.message_id + 2)

    async def edit_text(self, text: str, **kwargs):
        self.edits.append({"text": text, **kwargs})
        return True

    async def edit_media(self, media, **kwargs):
        self.edits.append({"media": media, **kwargs})
        return True


class FakeCallback:
    def __init__(self) -> None:
        self.data = ""
        self.message = FakeMessage()
        self.from_user = User(id=42, is_bot=False, first_name="Test")
        self.bot = SimpleNamespace(send_document=self._send_document)
        self.alerts: list[str | None] = []

    async def answer(self, text: str | None = None, show_alert: bool = False):
        self.alerts.append(text)
        return True

    async def _send_document(self, chat_id, document=None, caption=None, **kwargs):
        self.message.documents.append({"chat_id": chat_id, "document": document, "caption": caption, **kwargs})
        return SimpleNamespace(message_id=200)


@pytest.mark.asyncio
async def test_text_creates_preview_and_settings_update() -> None:
    state = FakeState()
    message = FakeMessage()
    message.text = "https://example.com"
    await create.on_text(message, state)
    draft = Draft.from_data(await state.get_data())
    assert draft is not None
    assert draft.content == "https://example.com"
    assert message.photos

    callback = FakeCallback()
    callback.data = "shape:set:cat"
    await settings.shapes_set(callback, state)
    draft = Draft.from_data(await state.get_data())
    assert draft is not None
    assert draft.shape == "cat"
    assert callback.message.edits

    callback = FakeCallback()
    callback.data = "pal:set:purple"
    await settings.palettes_set(callback, state)
    draft = Draft.from_data(await state.get_data())
    assert draft is not None
    assert draft.palette == "purple"


@pytest.mark.asyncio
async def test_monogram_pending_then_text() -> None:
    state = FakeState()
    await state.set_state(Flow.monogram)
    message = FakeMessage()
    message.text = "ак"
    await logo.on_monogram(message, state)
    assert state.state is None
    assert (await state.get_data())["pending_monogram"] == "АК"

    message.text = "https://example.com"
    await create.on_text(message, state)
    draft = Draft.from_data(await state.get_data())
    assert draft is not None
    assert draft.logo_mode == "monogram"
    assert draft.logo_text == "АК"


@pytest.mark.asyncio
async def test_download_png() -> None:
    state = FakeState()
    message = FakeMessage()
    message.text = "https://example.com"
    await create.on_text(message, state)
    callback = FakeCallback()
    callback.data = "dl:png"
    await create.download_png(callback, state)
    assert callback.message.documents
    document = callback.message.documents[0]["document"]
    assert document.data.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_webapp_applies_settings() -> None:
    state = FakeState()
    message = FakeMessage()
    message.text = "https://example.com"
    await create.on_text(message, state)
    message.web_app_data = SimpleNamespace(data='{"shape":"leaf","module_style":"dot","eye_style":"circle","palette":"wood","size":512}')
    await webapp.on_web_app_data(message, state)
    draft = Draft.from_data(await state.get_data())
    assert draft is not None
    assert draft.shape == "leaf"
    assert draft.palette == "wood"
    assert draft.size == 512
    assert message.photos


@pytest.mark.asyncio
async def test_webapp_rejects_bad_payload() -> None:
    state = FakeState()
    message = FakeMessage()
    message.web_app_data = SimpleNamespace(data="not-json")
    await webapp.on_web_app_data(message, state)
    assert message.answers
