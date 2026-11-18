from __future__ import annotations

from bot.keyboards import (
    editor_kb,
    eye_menu,
    logo_menu,
    palette_menu,
    preset_menu,
    shape_list,
    shape_menu,
    size_menu,
    style_menu,
)
from bot.services import Draft


def _markups():
    draft = Draft(content="https://example.com")
    return [
        editor_kb(draft),
        shape_menu(),
        shape_list("animals"),
        style_menu(0),
        eye_menu(),
        palette_menu(0),
        preset_menu(0),
        logo_menu(draft),
        size_menu(1024),
    ]


def test_callback_data_fits_telegram_limit() -> None:
    for markup in _markups():
        for row in markup.inline_keyboard:
            for button in row:
                assert button.callback_data
                assert len(button.callback_data.encode("utf-8")) <= 64, button.callback_data


def test_editor_has_downloads() -> None:
    callbacks = {button.callback_data for row in editor_kb(Draft(content="x")).inline_keyboard for button in row}
    assert {"dl:png", "dl:svg", "shape:menu", "pal:menu:0"}.issubset(callbacks)
