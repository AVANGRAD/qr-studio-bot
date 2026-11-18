from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from qrstudio.eyes import eye_keys, eye_name
from qrstudio.masks import SHAPE_CATEGORIES, shape_name
from qrstudio.presets import PALETTES, PRESETS, get_palette, get_preset
from qrstudio.shapes import MODULE_STYLES, style_name

from .services import Draft, webapp_url

CATEGORY_LABELS = {
    "Геометрия": "Геометрия",
    "Природа": "Природа",
    "Животные": "Животные",
    "Символы": "Символы",
}
CATEGORY_KEYS = {
    "geometry": "Геометрия",
    "nature": "Природа",
    "animals": "Животные",
    "symbols": "Символы",
}
LOGO_MODES = {
    "plate": "Плашка",
    "knockout": "Вырез",
    "texture": "Текстура",
    "background": "Фон",
    "corner": "Угол",
    "monogram": "Монограмма",
}
SIZES = (512, 1024, 2048)


def _mark(active: bool, label: str) -> str:
    return f"• {label}" if active else label


def _nav(builder: InlineKeyboardBuilder, prefix: str, page: int, pages: int, extra: list[InlineKeyboardButton] | None = None) -> None:
    if pages > 1:
        row: list[InlineKeyboardButton] = []
        if page > 0:
            row.append(InlineKeyboardButton(text="Назад", callback_data=f"{prefix}:{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
        if page + 1 < pages:
            row.append(InlineKeyboardButton(text="Дальше", callback_data=f"{prefix}:{page + 1}"))
        builder.row(*row)
    if extra:
        builder.row(*extra)
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))


def welcome_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Создать QR", callback_data="menu:new"),
        InlineKeyboardButton(text="Фото + QR", callback_data="photo:upload"),
    )
    builder.row(
        InlineKeyboardButton(text="Пресеты", callback_data="menu:presets"),
        InlineKeyboardButton(text="Помощь", callback_data="menu:help"),
    )
    return builder.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Создать QR", callback_data="menu:new"))
    builder.row(InlineKeyboardButton(text="Назад", callback_data="menu:home"))
    return builder.as_markup()


def editor_kb(draft: Draft, webapp: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    logo_label = "нет"
    if draft.logo_mode == "monogram":
        logo_label = "монограмма"
    elif draft.has_logo:
        logo_label = LOGO_MODES.get(draft.logo_mode, "загружен")
    builder.row(
        InlineKeyboardButton(text=f"Форма: {shape_name(draft.shape)}", callback_data="shape:menu"),
        InlineKeyboardButton(text=f"Палитра: {get_palette(draft.palette).name}", callback_data="pal:menu:0"),
    )
    builder.row(
        InlineKeyboardButton(text=f"Узор: {style_name(draft.module_style)}", callback_data="style:menu:0"),
        InlineKeyboardButton(text=f"Глаза: {eye_name(draft.eye_style)}", callback_data="eye:menu"),
    )
    builder.row(
        InlineKeyboardButton(text=f"Логотип: {logo_label}", callback_data="logo:menu"),
        InlineKeyboardButton(text=f"Размер: {draft.size}", callback_data="size:menu"),
    )
    builder.row(InlineKeyboardButton(text=f"Фото: {'загружено' if draft.has_photo else 'нет'}", callback_data="photo:menu"))
    builder.row(
        InlineKeyboardButton(text="Пресеты", callback_data="menu:presets"),
        InlineKeyboardButton(text="Случайный стиль", callback_data="menu:random"),
    )
    if webapp:
        builder.row(InlineKeyboardButton(text="Выбрать визуально", web_app=WebAppInfo(url=webapp_url(draft))))
    builder.row(
        InlineKeyboardButton(text="Скачать PNG", callback_data="dl:png"),
        InlineKeyboardButton(text="Скачать SVG", callback_data="dl:svg"),
    )
    builder.row(InlineKeyboardButton(text="Новый QR", callback_data="draft:new"))
    return builder.as_markup()


def shape_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in CATEGORY_KEYS.items():
        builder.button(text=label, callback_data=f"shape:cat:{key}:0")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))
    return builder.as_markup()


def shape_list(category_key: str, page: int = 0) -> InlineKeyboardMarkup:
    category = CATEGORY_KEYS.get(category_key, "Геометрия")
    keys = SHAPE_CATEGORIES.get(category, [])
    per_page = 8
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    slice_keys = keys[page * per_page : (page + 1) * per_page]
    builder = InlineKeyboardBuilder()
    for key in slice_keys:
        builder.button(text=shape_name(key), callback_data=f"shape:set:{key}")
    builder.adjust(2)
    _nav(builder, f"shape:cat:{category_key}", page, pages)
    return builder.as_markup()


def style_menu(page: int = 0, current: str | None = None) -> InlineKeyboardMarkup:
    keys = list(MODULE_STYLES)
    per_page = 6
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    builder = InlineKeyboardBuilder()
    for key in keys[page * per_page : (page + 1) * per_page]:
        builder.button(text=_mark(key == current, style_name(key)), callback_data=f"style:set:{key}")
    builder.adjust(2)
    _nav(builder, "style:menu", page, pages)
    return builder.as_markup()


def eye_menu(current: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in eye_keys():
        builder.button(text=_mark(key == current, eye_name(key)), callback_data=f"eye:set:{key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))
    return builder.as_markup()


def palette_menu(page: int = 0, current: str | None = None) -> InlineKeyboardMarkup:
    keys = list(PALETTES)
    per_page = 8
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    builder = InlineKeyboardBuilder()
    for key in keys[page * per_page : (page + 1) * per_page]:
        builder.button(text=_mark(key == current, get_palette(key).name), callback_data=f"pal:set:{key}")
    builder.adjust(2)
    _nav(builder, "pal:menu", page, pages)
    return builder.as_markup()


def preset_menu(page: int = 0, current: str | None = None) -> InlineKeyboardMarkup:
    keys = list(PRESETS)
    per_page = 6
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    builder = InlineKeyboardBuilder()
    for key in keys[page * per_page : (page + 1) * per_page]:
        preset = get_preset(key)
        builder.button(text=_mark(key == current, preset.name), callback_data=f"preset:set:{key}")
    builder.adjust(2)
    _nav(builder, "preset:menu", page, pages)
    return builder.as_markup()


def logo_menu(draft: Draft) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Загрузить логотип", callback_data="logo:upload"),
        InlineKeyboardButton(text="Монограмма", callback_data="logo:monogram"),
    )
    for key, label in LOGO_MODES.items():
        if key == "monogram":
            continue
        builder.button(text=_mark(draft.logo_mode == key, label), callback_data=f"logo:mode:{key}")
    builder.adjust(2)
    if draft.has_logo:
        builder.row(InlineKeyboardButton(text="Убрать логотип", callback_data="logo:clear"))
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))
    return builder.as_markup()


def photo_menu(draft: Draft | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Загрузить фото", callback_data="photo:upload"))
    if draft is not None and draft.has_photo:
        builder.row(InlineKeyboardButton(text="Убрать фото", callback_data="photo:clear"))
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))
    return builder.as_markup()


def size_menu(current: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in SIZES:
        builder.button(text=_mark(size == current, f"{size} px"), callback_data=f"size:set:{size}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="К редактору", callback_data="back:editor"))
    return builder.as_markup()
