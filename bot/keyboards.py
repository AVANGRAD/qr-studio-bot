from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from qrstudio.emblems import emblem_keys
from qrstudio.eyes import eye_keys
from qrstudio.masks import SHAPE_CATEGORIES
from qrstudio.presets import PALETTES, PRESETS
from qrstudio.shapes import MODULE_STYLES

from .i18n import (
    CATEGORY_INTERNAL,
    SUPPORTED_LANGS,
    display_name,
    language_label,
    mode_name,
    t,
)
from .services import Draft, webapp_url

CATEGORY_KEYS = dict(CATEGORY_INTERNAL)
LOGO_MODES = ("plate", "knockout", "texture", "background", "corner", "badge", "monogram")
SIZES = (512, 1024, 2048)


def _mark(active: bool, label: str) -> str:
    return f"• {label}" if active else label


def _nav(builder: InlineKeyboardBuilder, prefix: str, page: int, pages: int, extra: list[InlineKeyboardButton] | None = None) -> None:
    if pages > 1:
        row: list[InlineKeyboardButton] = []
        if page > 0:
            row.append(InlineKeyboardButton(text=t("kb_back"), callback_data=f"{prefix}:{page - 1}"))
        row.append(InlineKeyboardButton(text=f"{page + 1}/{pages}", callback_data="noop"))
        if page + 1 < pages:
            row.append(InlineKeyboardButton(text=t("kb_next"), callback_data=f"{prefix}:{page + 1}"))
        builder.row(*row)
    if extra:
        builder.row(*extra)
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))


def welcome_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("kb_create_qr"), callback_data="menu:new"),
        InlineKeyboardButton(text=t("kb_photo_qr"), callback_data="photo:upload"),
    )
    builder.row(
        InlineKeyboardButton(text=t("kb_presets"), callback_data="menu:presets"),
        InlineKeyboardButton(text=t("kb_help"), callback_data="menu:help"),
    )
    builder.row(InlineKeyboardButton(text=t("kb_language"), callback_data="lang:menu"))
    return builder.as_markup()


def language_kb(current: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in SUPPORTED_LANGS:
        builder.button(
            text=_mark(code == current, language_label(code)),
            callback_data=f"lang:set:{code}",
        )
    builder.adjust(2)
    return builder.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t("kb_create_qr"), callback_data="menu:new"))
    builder.row(InlineKeyboardButton(text=t("kb_back"), callback_data="menu:home"))
    return builder.as_markup()


def editor_kb(draft: Draft, webapp: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    logo_label = t("kb_none")
    if draft.logo_mode == "monogram":
        logo_label = t("kb_monogram_short")
    elif draft.has_logo:
        if draft.logo_emblem:
            logo_label = display_name("emblem", draft.logo_emblem)
        elif draft.logo_label:
            logo_label = draft.logo_label
        else:
            logo_label = t("kb_uploaded")
    builder.row(
        InlineKeyboardButton(
            text=f"{t('kb_shape')}: {display_name('shape', draft.shape)}",
            callback_data="shape:menu",
        ),
        InlineKeyboardButton(
            text=f"{t('kb_palette')}: {display_name('palette', draft.palette)}",
            callback_data="pal:menu:0",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text=f"{t('kb_style')}: {display_name('module', draft.module_style)}",
            callback_data="style:menu:0",
        ),
        InlineKeyboardButton(
            text=f"{t('kb_eyes')}: {display_name('eye', draft.eye_style)}",
            callback_data="eye:menu",
        ),
    )
    builder.row(
        InlineKeyboardButton(text=f"{t('kb_logo')}: {logo_label}", callback_data="logo:menu"),
        InlineKeyboardButton(text=f"{t('kb_size')}: {draft.size}", callback_data="size:menu"),
    )
    photo_label = t("kb_loaded") if draft.has_photo else t("kb_none")
    builder.row(InlineKeyboardButton(text=f"{t('kb_photo')}: {photo_label}", callback_data="photo:menu"))
    builder.row(
        InlineKeyboardButton(text=t("kb_presets"), callback_data="menu:presets"),
        InlineKeyboardButton(text=t("kb_random"), callback_data="menu:random"),
    )
    if webapp:
        builder.row(InlineKeyboardButton(text=t("kb_visual"), web_app=WebAppInfo(url=webapp_url(draft))))
    builder.row(
        InlineKeyboardButton(text=t("kb_download_png"), callback_data="dl:png"),
        InlineKeyboardButton(text=t("kb_download_svg"), callback_data="dl:svg"),
    )
    builder.row(
        InlineKeyboardButton(text=t("kb_new_qr"), callback_data="draft:new"),
        InlineKeyboardButton(text=t("kb_language"), callback_data="lang:menu"),
    )
    return builder.as_markup()


def shape_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in CATEGORY_KEYS:
        builder.button(text=display_name("category", key), callback_data=f"shape:cat:{key}:0")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))
    return builder.as_markup()


def shape_list(category_key: str, page: int = 0) -> InlineKeyboardMarkup:
    category = CATEGORY_KEYS.get(category_key, CATEGORY_KEYS["geometry"])
    keys = SHAPE_CATEGORIES.get(category, [])
    per_page = 8
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    slice_keys = keys[page * per_page : (page + 1) * per_page]
    builder = InlineKeyboardBuilder()
    for key in slice_keys:
        builder.button(text=display_name("shape", key), callback_data=f"shape:set:{key}")
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
        builder.button(text=_mark(key == current, display_name("module", key)), callback_data=f"style:set:{key}")
    builder.adjust(2)
    _nav(builder, "style:menu", page, pages)
    return builder.as_markup()


def eye_menu(current: str | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key in eye_keys():
        builder.button(text=_mark(key == current, display_name("eye", key)), callback_data=f"eye:set:{key}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))
    return builder.as_markup()


def palette_menu(page: int = 0, current: str | None = None) -> InlineKeyboardMarkup:
    keys = list(PALETTES)
    per_page = 8
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    builder = InlineKeyboardBuilder()
    for key in keys[page * per_page : (page + 1) * per_page]:
        builder.button(text=_mark(key == current, display_name("palette", key)), callback_data=f"pal:set:{key}")
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
        builder.button(text=_mark(key == current, display_name("preset", key)), callback_data=f"preset:set:{key}")
    builder.adjust(2)
    _nav(builder, "preset:menu", page, pages)
    return builder.as_markup()


def logo_menu(draft: Draft) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=t("kb_upload_logo"), callback_data="logo:upload"),
        InlineKeyboardButton(text=t("kb_monogram"), callback_data="logo:monogram"),
    )
    builder.row(InlineKeyboardButton(text=t("kb_emblem_presets"), callback_data="logo:presets:0"))
    for key in LOGO_MODES:
        if key == "monogram":
            continue
        builder.button(text=_mark(draft.logo_mode == key, mode_name(key)), callback_data=f"logo:mode:{key}")
    builder.adjust(2)
    if draft.has_logo:
        builder.row(InlineKeyboardButton(text=t("kb_remove_logo"), callback_data="logo:clear"))
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))
    return builder.as_markup()


def emblem_menu(page: int = 0) -> InlineKeyboardMarkup:
    keys = emblem_keys()
    per_page = 8
    pages = max(1, (len(keys) + per_page - 1) // per_page)
    page = min(max(0, page), pages - 1)
    builder = InlineKeyboardBuilder()
    for key in keys[page * per_page : (page + 1) * per_page]:
        builder.button(text=display_name("emblem", key), callback_data=f"logo:preset:{key}")
    builder.adjust(2)
    _nav(builder, "logo:presets", page, pages)
    return builder.as_markup()


def photo_menu(draft: Draft | None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=t("kb_upload_photo"), callback_data="photo:upload"))
    if draft is not None and draft.has_photo:
        builder.row(InlineKeyboardButton(text=t("kb_remove_photo"), callback_data="photo:clear"))
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))
    return builder.as_markup()


def size_menu(current: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for size in SIZES:
        builder.button(text=_mark(size == current, f"{size} px"), callback_data=f"size:set:{size}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text=t("kb_editor"), callback_data="back:editor"))
    return builder.as_markup()
