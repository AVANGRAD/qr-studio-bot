from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

logger = logging.getLogger(__name__)

DEFAULT_LANG = "ru"
SUPPORTED_LANGS = ("ru", "en")
current_lang: ContextVar[str] = ContextVar("current_lang", default=DEFAULT_LANG)

LANG_LABELS = {"ru": "Русский", "en": "English"}


def resolve_lang(code: str | None) -> str:
    if not code:
        return DEFAULT_LANG
    normalized = code.lower().replace("_", "-")
    if normalized.startswith("en"):
        return "en"
    if normalized.startswith(("ru", "uk", "be", "kk")):
        return "ru"
    return "en"


def language_label(lang: str) -> str:
    return LANG_LABELS.get(lang, LANG_LABELS[DEFAULT_LANG])


@contextmanager
def use_lang(lang: str):
    token = current_lang.set(lang if lang in SUPPORTED_LANGS else DEFAULT_LANG)
    try:
        yield
    finally:
        current_lang.reset(token)


def t(key: str, **params: object) -> str:
    lang = current_lang.get()
    template = TEXTS.get(lang, {}).get(key) or TEXTS[DEFAULT_LANG].get(key)
    if template is None:
        return key
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return template


SHAPE_NAMES = {
    "square": ("Квадрат", "Square"),
    "rounded": ("Скруглённый квадрат", "Rounded square"),
    "circle": ("Круг", "Circle"),
    "capsule": ("Капсула", "Capsule"),
    "diamond": ("Ромб", "Diamond"),
    "triangle": ("Треугольник", "Triangle"),
    "hexagon": ("Шестиугольник", "Hexagon"),
    "octagon": ("Восьмиугольник", "Octagon"),
    "star5": ("Звезда 5", "5-point star"),
    "star8": ("Звезда 8", "8-point star"),
    "cross": ("Крест", "Cross"),
    "shield": ("Щит", "Shield"),
    "squircle": ("Суперэллипс", "Squircle"),
    "burst": ("Вспышка", "Burst"),
    "heart": ("Сердце", "Heart"),
    "leaf": ("Лист", "Leaf"),
    "flower": ("Цветок", "Flower"),
    "cloud": ("Облако", "Cloud"),
    "sun": ("Солнце", "Sun"),
    "moon": ("Луна", "Moon"),
    "snowflake": ("Снежинка", "Snowflake"),
    "wave": ("Волна", "Wave"),
    "drop": ("Капля", "Drop"),
    "planet": ("Планета", "Planet"),
    "clover": ("Клевер", "Clover"),
    "cactus": ("Кактус", "Cactus"),
    "cat": ("Котик", "Cat"),
    "bear": ("Медвежонок", "Bear cub"),
    "bunny": ("Зайчик", "Bunny"),
    "fox": ("Лиса", "Fox"),
    "owl": ("Сова", "Owl"),
    "panda": ("Панда", "Panda"),
    "fish": ("Рыбка", "Fish"),
    "butterfly": ("Бабочка", "Butterfly"),
    "paw": ("Лапка", "Paw"),
    "ladybug": ("Божья коровка", "Ladybug"),
    "turtle": ("Черепаха", "Turtle"),
    "penguin": ("Пингвин", "Penguin"),
    "frog": ("Лягушка", "Frog"),
    "whale": ("Кит", "Whale"),
    "crown": ("Корона", "Crown"),
    "cup": ("Кубок", "Cup"),
    "mask": ("Маска", "Mask"),
    "rocket": ("Ракета", "Rocket"),
    "guitar": ("Гитара", "Guitar"),
    "speech_bubble": ("Пузырь чата", "Speech bubble"),
    "puzzle": ("Пазл", "Puzzle"),
    "gift": ("Подарок", "Gift"),
    "tree": ("Ёлка", "Fir tree"),
    "pumpkin": ("Тыква", "Pumpkin"),
    "anchor": ("Якорь", "Anchor"),
    "music_note": ("Нота", "Music note"),
}

MODULE_NAMES = {
    "square": ("Квадрат", "Square"),
    "rounded": ("Скруглённый", "Rounded"),
    "dot": ("Точка", "Dot"),
    "diamond": ("Ромб", "Diamond"),
    "star": ("Звезда", "Star"),
    "heart": ("Сердечко", "Heart"),
    "paw": ("Лапка", "Paw"),
    "hexagon": ("Шестиугольник", "Hexagon"),
    "triangle": ("Треугольник", "Triangle"),
    "cross": ("Крест", "Cross"),
    "leaf": ("Листик", "Leaf"),
    "wave": ("Волна", "Wave"),
    "vbar": ("Вертикальные полосы", "Vertical bars"),
    "hbar": ("Горизонтальные полосы", "Horizontal bars"),
    "liquid": ("Жидкие капли", "Liquid drops"),
    "pixel": ("Пиксель", "Pixel"),
    "ring": ("Кольцо", "Ring"),
    "confetti": ("Конфетти", "Confetti"),
    "flower": ("Цветочек", "Flower"),
    "chevron": ("Галочка", "Chevron"),
    "arch": ("Арка", "Arch"),
    "spark": ("Искра", "Spark"),
    "plus": ("Плюс", "Plus"),
    "brick": ("Кирпичик", "Brick"),
}

EYE_NAMES = {
    "square": ("Квадрат", "Square"),
    "rounded": ("Скруглённый", "Rounded"),
    "circle": ("Круг", "Circle"),
    "leaf": ("Лист", "Leaf"),
    "diamond": ("Ромб", "Diamond"),
    "star": ("Звезда", "Star"),
    "cat_eye": ("Кошачий глаз", "Cat eye"),
    "flower": ("Цветок", "Flower"),
    "hexagon": ("Шестиугольник", "Hexagon"),
    "shield": ("Щит", "Shield"),
    "capsule": ("Капсула", "Capsule"),
    "octagon": ("Восьмиугольник", "Octagon"),
    "spark": ("Искра", "Spark"),
    "heart": ("Сердце", "Heart"),
}

PALETTE_NAMES = {
    "mono": ("Чёрно-белый", "Black & white"),
    "gold": ("Золото", "Gold"),
    "red": ("Красный halftone", "Red halftone"),
    "blue": ("Синие точки", "Blue dots"),
    "purple": ("Фиолетовая мозаика", "Purple mosaic"),
    "green": ("Зелёные листья", "Green leaves"),
    "magenta": ("Маджента", "Magenta"),
    "navy": ("Тёмно-синий", "Navy"),
    "khaki": ("Хаки", "Khaki"),
    "orange": ("Оранжевый градиент", "Orange gradient"),
    "neon": ("Неон", "Neon"),
    "watercolor": ("Акварель", "Watercolor"),
    "metal": ("Металл", "Metal"),
    "wood": ("Дерево", "Wood"),
    "pastel": ("Пастель", "Pastel"),
    "berry": ("Ягодный", "Berry"),
    "ocean": ("Океан", "Ocean"),
    "sunset": ("Закат", "Sunset"),
    "midnight": ("Полночь", "Midnight"),
}

PRESET_NAMES = {
    "gold_leaf": ("Золотой лист", "Golden leaf"),
    "red_halftone": ("Красный halftone", "Red halftone"),
    "blue_dots": ("Синие точки", "Blue dots"),
    "purple_mosaic": ("Фиолетовая мозаика", "Purple mosaic"),
    "green_leaves": ("Зелёные листья", "Green leaves"),
    "magenta": ("Маджента", "Magenta"),
    "navy": ("Navy squares", "Navy squares"),
    "khaki": ("Хаки", "Khaki"),
    "orange": ("Оранжевый градиент", "Orange gradient"),
    "neon": ("Неон", "Neon"),
    "watercolor": ("Акварель", "Watercolor"),
    "metal": ("Металл", "Metal"),
    "wood": ("Дерево", "Wood"),
    "pastel": ("Пастель", "Pastel"),
    "cat": ("Котик", "Cat"),
    "panda": ("Панда", "Panda"),
    "rocket": ("Ракета", "Rocket"),
    "gift": ("Подарок", "Gift"),
    "cosmic": ("Космос", "Cosmos"),
    "forest": ("Лесная сказка", "Forest tale"),
    "candy": ("Карамель", "Candy"),
    "ocean": ("Океан", "Ocean"),
    "retro": ("Ретро", "Retro"),
    "royal": ("Королевский", "Royal"),
    "sailor": ("Морской", "Nautical"),
}

EMBLEM_NAMES = {
    "heart": ("Сердце", "Heart"),
    "star": ("Звезда", "Star"),
    "crown": ("Корона", "Crown"),
    "leaf": ("Лист", "Leaf"),
    "paw": ("Лапка", "Paw"),
    "rocket": ("Ракета", "Rocket"),
    "flower": ("Цветок", "Flower"),
    "moon": ("Луна", "Moon"),
    "planet": ("Планета", "Planet"),
    "shield": ("Щит", "Shield"),
    "music_note": ("Нота", "Music note"),
    "anchor": ("Якорь", "Anchor"),
}

CATEGORY_NAMES = {
    "geometry": ("Геометрия", "Geometry"),
    "nature": ("Природа", "Nature"),
    "animals": ("Животные", "Animals"),
    "symbols": ("Символы", "Symbols"),
}

CATEGORY_INTERNAL = {
    "geometry": "Геометрия",
    "nature": "Природа",
    "animals": "Животные",
    "symbols": "Символы",
}

LOGO_MODE_NAMES = {
    "plate": ("плашка", "Plate"),
    "knockout": ("вырез", "Knockout"),
    "texture": ("текстура", "Texture"),
    "background": ("фон", "Background"),
    "corner": ("угол", "Corner"),
    "badge": ("медальон", "Badge"),
    "monogram": ("монограмма", "Monogram"),
}

NAME_MAPS = {
    "shape": SHAPE_NAMES,
    "module": MODULE_NAMES,
    "eye": EYE_NAMES,
    "palette": PALETTE_NAMES,
    "preset": PRESET_NAMES,
    "emblem": EMBLEM_NAMES,
    "category": CATEGORY_NAMES,
}


def display_name(kind: str, key: str, lang: str | None = None) -> str:
    mapping = NAME_MAPS.get(kind, {})
    pair = mapping.get(key)
    if pair is None:
        return key
    return pair[1] if (lang or current_lang.get()) == "en" else pair[0]


def mode_name(key: str, lang: str | None = None) -> str:
    pair = LOGO_MODE_NAMES.get(key)
    if pair is None:
        return key
    return pair[1] if (lang or current_lang.get()) == "en" else pair[0]


def category_key(internal: str) -> str:
    for key, name in CATEGORY_INTERNAL.items():
        if name == internal:
            return key
    return "geometry"


def warning_text(code: str, params: dict[str, Any]) -> str:
    values = dict(params)
    if "shape" in values:
        values["shape"] = display_name("shape", str(values["shape"]))
    return t(f"warning_{code}", **values)


TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        "welcome": """<b>QR Studio</b>

Пришли ссылку или текст — соберу красивый QR-код.
Можно выбрать форму, узор, глаза, палитру и добавить логотип.

Что умею:
• 52 формы: от котика и сердца до ракеты и щита
• 24 узора модулей, 14 стилей глаз и 19 палитр
• 25 готовых пресетов и 7 режимов логотипа
• 12 встроенных иконок для центра QR
• QR поверх твоего фото — фото остаётся видимым
• PNG до 2048 px и SVG

Просто отправь ссылку или нажми «Создать QR».""",
        "help": """<b>Как пользоваться</b>

1. Пришли ссылку, текст или нажми «Создать QR».
2. Меняй форму, узор, глаза и палитру кнопками под превью.
3. Логотип: пришли PNG/JPG/WebP, выбери готовую иконку или монограмму — я впишу его в QR.
4. Фото: нажми «Фото», пришли картинку — QR ляжет на светлую карточку в углу, фото будет видно вокруг.
5. Скачай PNG или SVG.

<b>Команды</b>
/start — начало
/language — сменить язык
/qr &lt;текст&gt; — сразу создать QR
/help — эта справка

<b>Советы</b>
• Для логотипа лучше PNG с прозрачным фоном.
• Чем длиннее текст, тем мельче модули. Для печати выбирай 1024–2048 px.
• Фигурные формы и логотип используют повышенную коррекцию ошибок.
• Если QR нужен для камеры на улице, оставь светлый фон и высокий контраст.""",
        "choose_language": "<b>Выбери язык / Choose your language</b>\n\nТак бот будет говорить с тобой. Потом можно сменить в меню.",
        "content_prompt": "Пришли ссылку или текст для QR-кода. Можно одним сообщением.",
        "qr_prompt": "Пришли текст после /qr или просто отправь ссылку.",
        "photo_prompt": "Пришли фото картинкой или файлом PNG/JPG/WebP до 12 МБ. Сделаю его фоном, а QR — на светлой карточке в углу.",
        "photo_needed": "Жду фото: пришли картинку PNG/JPG/WebP до 12 МБ.",
        "logo_prompt": "Пришли логотип картинкой или файлом PNG/JPG/WebP до 6 МБ. Я уберу белый фон.",
        "logo_text_prompt": "Жду картинку-логотип: PNG, JPG или WebP до 6 МБ.",
        "monogram_prompt": "Пришли 1–2 буквы для монограммы. Например: АК или QR.",
        "render_error": "Не получилось собрать QR. Попробуй другой текст или стиль.",
        "reset": "Настройки сброшены. Пришли новый текст.",
        "no_draft": "Сначала пришли ссылку или текст.",
        "logo_needed": "Сначала загрузи логотип, выбери готовую иконку или монограмму.",
        "presets_root": "<b>Пресеты</b>\nГотовые сочетания формы, узора и цвета.",
        "preset_applied": "Пресет: {name}",
        "random_style": "Случайный стиль: {name}",
        "shape_root": "<b>Форма</b>\nВыбери категорию.",
        "shape_category": "<b>Форма</b>\nВыбери силуэт.",
        "unknown_shape": "Неизвестная форма",
        "shape_updated": "Форма обновлена",
        "style_root": "<b>Узор модулей</b>\nВыбери рисунок точек.",
        "unknown_style": "Неизвестный узор",
        "style_updated": "Узор обновлён",
        "eyes_root": "<b>Глаза</b>\nСтиль трёх угловых маркеров.",
        "unknown_eyes": "Неизвестный стиль глаз",
        "eyes_updated": "Глаза обновлены",
        "palette_root": "<b>Палитра</b>\nЦвет и контраст.",
        "unknown_palette": "Неизвестная палитра",
        "palette_updated": "Палитра обновлена",
        "size_root": "<b>Размер</b>\nДля печати лучше 1024–2048 px.",
        "unknown_size": "Неизвестный размер",
        "size_updated": "Размер обновлён",
        "logo_root": "<b>Логотип</b>\nЗагрузи картинку, выбери готовую иконку или монограмму.\nПлашка — логотип на подложке, медальон — круглая подложка, вырез — QR «расступается», текстура — логотип внутри модулей, фон — водяной знак, угол — маленький логотип в углу.",
        "logo_presets": "<b>Готовые иконки</b>\nВыбери нейтральную иконку — она встанет в центр QR. Потом можно сменить режим на плашку, медальон, вырез или текстуру.",
        "unknown_icon": "Неизвестная иконка",
        "icon_label": "Иконка: {name}",
        "icon_saved": "Иконка сохранена. Теперь пришли ссылку или текст для QR.",
        "unknown_mode": "Неизвестный режим",
        "mode_saved": "Режим сохранён",
        "mode_updated": "Режим обновлён",
        "logo_cleared": "Логотип убран",
        "not_image": "Это не картинка. Пришли PNG, JPG или WebP.",
        "logo_too_large": "Файл больше 8 МБ. Пришли картинку поменьше.",
        "logo_processing": "Обрабатываю логотип…",
        "logo_download_failed": "Не удалось скачать логотип. Попробуй ещё раз.",
        "logo_saved": "Логотип сохранён. Теперь пришли ссылку или текст для QR.",
        "logo_added": "Логотип добавлен.",
        "monogram_length": "Нужно 1–2 символа. Например: АК или QR.",
        "monogram_saved": "Монограмма сохранена. Теперь пришли ссылку или текст для QR.",
        "photo_root": "<b>Фото + QR</b>\n\nПришли фотографию — она станет фоном. QR будет на светлой карточке в правом нижнем углу, поэтому фотография останется видимой.\n\nЛучше выбирать фото с крупным объектом и свободным местом в углу.",
        "photo_cleared": "Фото убрано",
        "photo_too_large": "Фото больше 12 МБ. Пришли картинку поменьше.",
        "photo_processing": "Обрабатываю фото…",
        "photo_download_failed": "Не удалось скачать фото. Попробуй ещё раз.",
        "photo_saved": "Фото сохранено. Теперь пришли ссылку или текст для QR.",
        "photo_added": "Фото добавлено — QR будет на карточке в углу.",
        "settings_bad_json": "Не удалось прочитать настройки. Открой редактор ещё раз.",
        "settings_bad_values": "Не удалось прочитать настройки. Попробуй выбрать другой вариант.",
        "settings_pending_saved": "Настройки сохранены. Пришли ссылку или текст — применю их.",
        "settings_unchanged": "Настройки не изменились. Попробуй выбрать другой вариант.",
        "language_saved": "Язык изменён.",
        "webapp_private": "Визуальный редактор доступен в личном чате с ботом.",
        "webapp_open": "Открой визуальный редактор:",
        "webapp_open_button": "Открыть редактор",
        "unknown_language": "Язык недоступен",
        "png_collecting": "Собираю PNG…",
        "svg_collecting": "Собираю SVG…",
        "empty_content": "Пустой текст. Пришли ссылку или текст для QR.",
        "too_long_content": "Слишком длинный текст: {length} символов. Максимум — {max_length}.",
        "bad_scheme": "Поддерживаются ссылки http://, https:// и tg://, либо обычный текст.",
        "bad_url": "Не похоже на корректную ссылку.",
        "photo_unreadable": "Не удалось прочитать фото. Пришли PNG, JPG или WebP.",
        "logo_unreadable": "Не удалось прочитать изображение. Пришли PNG, JPG или WebP.",
        "logo_too_heavy": "Логотип слишком тяжёлый после обработки. Попробуй картинку поменьше.",
        "rate_minute": "Слишком часто. Подожди минуту.",
        "rate_day": "Дневной лимит исчерпан. Попробуй завтра.",
        "caption_photo": "Фон: фото · QR на светлой карточке",
        "caption_form": "Форма: {shape} · Узор: {style}",
        "caption_eyes": "Глаза: {eyes} · Палитра: {palette}",
        "caption_logo": "Логотип: {logo}",
        "caption_metrics": "Модуль: {module:.1f} px · Контраст: {contrast:.1f}:1",
        "caption_small": "Модуль мелкий: увеличь размер или сократи текст.",
        "logo_none": "нет",
        "logo_uploaded": "загружен",
        "logo_monogram": "монограмма «{text}»",
        "svg_caption": "<b>QR Studio</b> · SVG\n<code>{content}</code>",
        "warning_silhouette_cut": "Силуэт «{shape}» режет finder-узоры ({finder:.0%}) или данные ({data:.0%}) — использую безопасную рамку.",
        "warning_unknown_module": "Неизвестный стиль модулей «{style}», использую rounded.",
        "warning_unknown_eye": "Неизвестный стиль глаз «{style}», использую rounded.",
        "warning_small_module": "Модуль слишком мелкий для выбранного узора — упрощаю до точек.",
        "warning_small_eye": "Глаза слишком мелкие для выбранного узора — упрощаю до скруглённых.",
        "warning_logo_large": "Логотип крупный — проверь сканирование камерой.",
        "kb_back": "Назад",
        "kb_next": "Дальше",
        "kb_editor": "К редактору",
        "kb_shape": "Форма",
        "kb_palette": "Палитра",
        "kb_style": "Узор",
        "kb_eyes": "Глаза",
        "kb_logo": "Логотип",
        "kb_size": "Размер",
        "kb_photo": "Фото",
        "kb_presets": "Пресеты",
        "kb_random": "Случайный стиль",
        "kb_visual": "Выбрать визуально",
        "kb_download_png": "Скачать PNG",
        "kb_download_svg": "Скачать SVG",
        "kb_new_qr": "Новый QR",
        "kb_create_qr": "Создать QR",
        "kb_photo_qr": "Фото + QR",
        "kb_help": "Помощь",
        "kb_language": "🌐 Язык / Language",
        "kb_upload_logo": "Загрузить логотип",
        "kb_upload_photo": "Загрузить фото",
        "kb_monogram": "Монограмма",
        "kb_emblem_presets": "Готовые иконки",
        "kb_remove_logo": "Убрать логотип",
        "kb_remove_photo": "Убрать фото",
        "kb_none": "нет",
        "kb_loaded": "загружено",
        "kb_monogram_short": "монограмма",
        "kb_uploaded": "загружен",
        "cmd_start": "Начать",
        "cmd_language": "Сменить язык",
        "cmd_app": "Визуальный редактор",
        "cmd_qr": "Создать QR из текста",
        "cmd_help": "Справка",
    },
    "en": {
        "welcome": """<b>QR Studio</b>

Send a link or text — I'll build a beautiful QR code.
Choose shape, pattern, eyes, palette and add a logo.

What I can do:
• 52 shapes: from cat and heart to rocket and shield
• 24 module patterns, 14 eye styles and 19 palettes
• 25 ready presets and 7 logo modes
• 12 built-in icons for the QR center
• QR over your photo — the photo stays visible
• PNG up to 2048 px and SVG

Just send a link or tap “Create QR”.""",
        "help": """<b>How to use</b>

1. Send a link, text or tap “Create QR”.
2. Change shape, pattern, eyes and palette with the buttons under the preview.
3. Logo: send PNG/JPG/WebP, choose a ready icon or a monogram — I'll fit it into the QR.
4. Photo: tap “Photo”, send an image — the QR will sit on a light card in the corner, with the photo visible around it.
5. Download PNG or SVG.

<b>Commands</b>
/start — start
/language — change language
/qr &lt;text&gt; — create a QR right away
/help — this help

<b>Tips</b>
• For a logo, PNG with a transparent background works best.
• Longer text means smaller modules. For print choose 1024–2048 px.
• Figure shapes and logos use higher error correction.
• If the QR is for an outdoor camera, keep a light background and high contrast.""",
        "choose_language": "<b>Выбери язык / Choose your language</b>\n\nThis is how the bot will talk to you. You can change it later in the menu.",
        "content_prompt": "Send a link or text for the QR code. One message is enough.",
        "qr_prompt": "Send text after /qr or just send a link.",
        "photo_prompt": "Send a photo as an image or a PNG/JPG/WebP file up to 12 MB. I'll use it as the background and put the QR on a light card in the corner.",
        "photo_needed": "Waiting for a photo: send a PNG/JPG/WebP image up to 12 MB.",
        "logo_prompt": "Send a logo as an image or a PNG/JPG/WebP file up to 6 MB. I'll remove the white background.",
        "logo_text_prompt": "Waiting for a logo image: PNG, JPG or WebP up to 6 MB.",
        "monogram_prompt": "Send 1–2 letters for the monogram. For example: AK or QR.",
        "render_error": "Couldn't build the QR. Try another text or style.",
        "reset": "Settings reset. Send a new text.",
        "no_draft": "First send a link or text.",
        "logo_needed": "First upload a logo, choose a ready icon or a monogram.",
        "presets_root": "<b>Presets</b>\nReady combinations of shape, pattern and color.",
        "preset_applied": "Preset: {name}",
        "random_style": "Random style: {name}",
        "shape_root": "<b>Shape</b>\nChoose a category.",
        "shape_category": "<b>Shape</b>\nChoose a silhouette.",
        "unknown_shape": "Unknown shape",
        "shape_updated": "Shape updated",
        "style_root": "<b>Module pattern</b>\nChoose the dot pattern.",
        "unknown_style": "Unknown pattern",
        "style_updated": "Pattern updated",
        "eyes_root": "<b>Eyes</b>\nStyle of the three corner markers.",
        "unknown_eyes": "Unknown eye style",
        "eyes_updated": "Eyes updated",
        "palette_root": "<b>Palette</b>\nColor and contrast.",
        "unknown_palette": "Unknown palette",
        "palette_updated": "Palette updated",
        "size_root": "<b>Size</b>\nFor print, 1024–2048 px works best.",
        "unknown_size": "Unknown size",
        "size_updated": "Size updated",
        "logo_root": "<b>Logo</b>\nUpload an image, choose a ready icon or a monogram.\nPlate — logo on a backing, badge — round backing, knockout — the QR “steps aside”, texture — logo inside modules, background — watermark, corner — small logo in the corner.",
        "logo_presets": "<b>Ready icons</b>\nChoose a neutral icon — it will go in the center of the QR. Then you can switch to plate, badge, knockout or texture.",
        "unknown_icon": "Unknown icon",
        "icon_label": "Icon: {name}",
        "icon_saved": "Icon saved. Now send a link or text for the QR.",
        "unknown_mode": "Unknown mode",
        "mode_saved": "Mode saved",
        "mode_updated": "Mode updated",
        "logo_cleared": "Logo removed",
        "not_image": "That's not an image. Send PNG, JPG or WebP.",
        "logo_too_large": "The file is larger than 8 MB. Send a smaller image.",
        "logo_processing": "Processing the logo…",
        "logo_download_failed": "Couldn't download the logo. Try again.",
        "logo_saved": "Logo saved. Now send a link or text for the QR.",
        "logo_added": "Logo added.",
        "monogram_length": "Need 1–2 characters. For example: AK or QR.",
        "monogram_saved": "Monogram saved. Now send a link or text for the QR.",
        "photo_root": "<b>Photo + QR</b>\n\nSend a photo — it will become the background. The QR will be on a light card in the bottom right corner, so the photo stays visible.\n\nA photo with a large subject and free space in the corner works best.",
        "photo_cleared": "Photo removed",
        "photo_too_large": "The photo is larger than 12 MB. Send a smaller image.",
        "photo_processing": "Processing the photo…",
        "photo_download_failed": "Couldn't download the photo. Try again.",
        "photo_saved": "Photo saved. Now send a link or text for the QR.",
        "photo_added": "Photo added — the QR will be on a card in the corner.",
        "settings_bad_json": "Couldn't read the settings. Open the editor again.",
        "settings_bad_values": "Couldn't read the settings. Try another option.",
        "settings_pending_saved": "Settings saved. Send a link or text — I'll apply them.",
        "settings_unchanged": "Settings didn't change. Try another option.",
        "language_saved": "Language updated.",
        "webapp_private": "The visual editor is available in a private chat with the bot.",
        "webapp_open": "Open the visual editor:",
        "webapp_open_button": "Open editor",
        "unknown_language": "Language unavailable",
        "png_collecting": "Preparing PNG…",
        "svg_collecting": "Preparing SVG…",
        "empty_content": "Empty text. Send a link or text for the QR.",
        "too_long_content": "Text is too long: {length} characters. Maximum is {max_length}.",
        "bad_scheme": "Supported links: http://, https:// and tg://, or plain text.",
        "bad_url": "This doesn't look like a valid link.",
        "photo_unreadable": "Couldn't read the photo. Send PNG, JPG or WebP.",
        "logo_unreadable": "Couldn't read the image. Send PNG, JPG or WebP.",
        "logo_too_heavy": "The logo is too heavy after processing. Try a smaller image.",
        "rate_minute": "Too often. Wait a minute.",
        "rate_day": "Daily limit reached. Try again tomorrow.",
        "caption_photo": "Background: photo · QR on a light card",
        "caption_form": "Shape: {shape} · Pattern: {style}",
        "caption_eyes": "Eyes: {eyes} · Palette: {palette}",
        "caption_logo": "Logo: {logo}",
        "caption_metrics": "Module: {module:.1f} px · Contrast: {contrast:.1f}:1",
        "caption_small": "The module is small: increase the size or shorten the text.",
        "logo_none": "none",
        "logo_uploaded": "uploaded",
        "logo_monogram": "monogram “{text}”",
        "svg_caption": "<b>QR Studio</b> · SVG\n<code>{content}</code>",
        "warning_silhouette_cut": "The “{shape}” silhouette clips finder patterns ({finder:.0%}) or data ({data:.0%}); using a safe frame.",
        "warning_unknown_module": "Unknown module style “{style}”; using rounded.",
        "warning_unknown_eye": "Unknown eye style “{style}”; using rounded.",
        "warning_small_module": "The module is too small for this pattern; simplifying to dots.",
        "warning_small_eye": "The eyes are too small for this style; simplifying to rounded.",
        "warning_logo_large": "The logo is large — check camera scanning.",
        "kb_back": "Back",
        "kb_next": "Next",
        "kb_editor": "Back to editor",
        "kb_shape": "Shape",
        "kb_palette": "Palette",
        "kb_style": "Pattern",
        "kb_eyes": "Eyes",
        "kb_logo": "Logo",
        "kb_size": "Size",
        "kb_photo": "Photo",
        "kb_presets": "Presets",
        "kb_random": "Random style",
        "kb_visual": "Choose visually",
        "kb_download_png": "Download PNG",
        "kb_download_svg": "Download SVG",
        "kb_new_qr": "New QR",
        "kb_create_qr": "Create QR",
        "kb_photo_qr": "Photo + QR",
        "kb_help": "Help",
        "kb_language": "🌐 Language / Язык",
        "kb_upload_logo": "Upload logo",
        "kb_upload_photo": "Upload photo",
        "kb_monogram": "Monogram",
        "kb_emblem_presets": "Ready icons",
        "kb_remove_logo": "Remove logo",
        "kb_remove_photo": "Remove photo",
        "kb_none": "none",
        "kb_loaded": "loaded",
        "kb_monogram_short": "monogram",
        "kb_uploaded": "uploaded",
        "cmd_start": "Start",
        "cmd_language": "Change language",
        "cmd_app": "Visual editor",
        "cmd_qr": "Create QR from text",
        "cmd_help": "Help",
    },
}


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        lang: str | None = None
        state = data.get("state")
        if state is not None:
            try:
                stored = (await state.get_data()).get("lang")
            except Exception:
                logger.exception("failed to read language from state")
            else:
                if stored in SUPPORTED_LANGS:
                    lang = stored
        if lang is None:
            user = data.get("event_from_user")
            lang = resolve_lang(getattr(user, "language_code", None))
        token = current_lang.set(lang)
        data["lang"] = lang
        try:
            return await handler(event, data)
        finally:
            current_lang.reset(token)
