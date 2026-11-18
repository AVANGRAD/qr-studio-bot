from __future__ import annotations

import asyncio
import html
import io
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode, urlparse

from PIL import Image, UnidentifiedImageError

from qrstudio.eyes import eye_name
from qrstudio.logo import prepare_logo
from qrstudio.masks import shape_name
from qrstudio.presets import get_palette, get_preset
from qrstudio.render import RenderOptions, RenderResult, render, render_svg
from qrstudio.shapes import style_name

MAX_CONTENT = 1200


class ContentError(ValueError):
    pass


@dataclass
class Draft:
    content: str
    shape: str = "square"
    module_style: str = "dot"
    eye_style: str = "circle"
    palette: str = "blue"
    size: int = 1024
    logo_png: bytes | None = None
    logo_mode: str = "plate"
    logo_text: str = "QR"
    logo_mono: bool = False

    @classmethod
    def from_data(cls, data: dict) -> Draft | None:
        raw = data.get("draft")
        if not isinstance(raw, dict):
            return None
        try:
            return cls(**raw)
        except TypeError:
            return None

    def to_data(self) -> dict:
        return asdict(self)

    @property
    def has_logo(self) -> bool:
        return bool(self.logo_png)

    def logo_image(self) -> Image.Image | None:
        if not self.logo_png:
            return None
        try:
            return Image.open(io.BytesIO(self.logo_png)).convert("RGBA")
        except Exception:  # noqa: BLE001
            return None


def normalize_content(value: str, max_length: int = MAX_CONTENT) -> str:
    text = (value or "").strip()
    if not text:
        raise ContentError("Пустой текст. Пришли ссылку или текст для QR.")
    if len(text) > max_length:
        raise ContentError(f"Слишком длинный текст: {len(text)} символов. Максимум — {max_length}.")
    if text.startswith("www."):
        text = "https://" + text
    if "://" in text and not text.lower().startswith(("http://", "https://", "tg://")):
        raise ContentError("Поддерживаются ссылки http://, https:// и tg://, либо обычный текст.")
    if text.lower().startswith(("http://", "https://")):
        parsed = urlparse(text)
        if not parsed.netloc or " " in parsed.netloc:
            raise ContentError("Не похоже на корректную ссылку.")
    return text


def _options(draft: Draft, size: int | None = None) -> RenderOptions:
    logo = draft.logo_image() if draft.logo_mode != "monogram" else None
    return RenderOptions(
        content=draft.content,
        shape=draft.shape,
        module_style=draft.module_style,
        eye_style=draft.eye_style,
        palette=draft.palette,
        size=size or draft.size,
        logo=logo,
        logo_mode=draft.logo_mode,
        logo_text=draft.logo_text,
        logo_mono=draft.logo_mono,
    )


def render_draft(draft: Draft, size: int | None = None) -> RenderResult:
    return render(_options(draft, size))


def png_bytes(draft: Draft, size: int | None = None) -> tuple[bytes, RenderResult]:
    result = render_draft(draft, size)
    buffer = io.BytesIO()
    result.image.save(buffer, format="PNG", dpi=(300, 300))
    return buffer.getvalue(), result


def svg_bytes(draft: Draft) -> str:
    return render_svg(_options(draft, draft.size))


def short(text: str, limit: int = 120) -> str:
    clean = " ".join(text.split())
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def webapp_url(draft: Draft) -> str:
    base = (os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://qr-studio-bot.onrender.com").rstrip("/")
    if not base.startswith("https://"):
        base = "https://qr-studio-bot.onrender.com"
    query = urlencode(
        {
            "shape": draft.shape,
            "module": draft.module_style,
            "eye": draft.eye_style,
            "palette": draft.palette,
            "size": draft.size,
        }
    )
    return f"{base}/app?{query}"


def caption(draft: Draft, result: RenderResult | None = None) -> str:
    mode_names = {
        "plate": "плашка",
        "knockout": "вырез",
        "texture": "текстура",
        "background": "фон",
        "corner": "угол",
        "monogram": "монограмма",
    }
    logo = "нет"
    if draft.logo_mode == "monogram":
        logo = f"монограмма «{html.escape(draft.logo_text)}»"
    elif draft.has_logo:
        logo = mode_names.get(draft.logo_mode, draft.logo_mode)
    lines = [
        f"<b>QR Studio</b> · {draft.size} px",
        f"<code>{html.escape(short(draft.content))}</code>",
        "",
        f"Форма: {shape_name(draft.shape)} · Узор: {style_name(draft.module_style)}",
        f"Глаза: {eye_name(draft.eye_style)} · Палитра: {get_palette(draft.palette).name}",
        f"Логотип: {logo}",
    ]
    if result:
        lines.append(f"Модуль: {result.module_px:.1f} px · Контраст: {result.contrast:.1f}:1")
        for warning in result.warnings:
            lines.append(f"<i>{html.escape(warning)}</i>")
        if result.module_px < 4.5:
            lines.append("<i>Модуль мелкий: увеличь размер или сократи текст.</i>")
    return "\n".join(lines)


def preset_draft(content: str, key: str) -> Draft:
    preset = get_preset(key)
    draft = Draft(content=content)
    draft.shape = preset.shape
    draft.module_style = preset.module_style
    draft.eye_style = preset.eye_style
    draft.palette = preset.palette
    draft.logo_mode = preset.logo_mode
    return draft


def prepare_uploaded_logo(raw: bytes) -> bytes:
    if len(raw) > 8 * 1024 * 1024:
        raise ContentError("Логотип слишком большой. Максимум — 8 МБ.")
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ContentError("Не удалось прочитать изображение. Пришли PNG, JPG или WebP.") from exc
    prepared = prepare_logo(raw, max_side=1024)
    buffer = io.BytesIO()
    prepared.save(buffer, format="PNG")
    if len(buffer.getvalue()) > 4 * 1024 * 1024:
        raise ContentError("Логотип слишком тяжёлый после обработки. Попробуй картинку поменьше.")
    return buffer.getvalue()


class RateLimiter:
    def __init__(self, per_minute: int = 14, per_day: int = 240) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> tuple[bool, str]:
        now = time.monotonic()
        events = self._events[user_id]
        while events and now - events[0] > 86400:
            events.popleft()
        if sum(1 for value in events if now - value <= 60) >= self.per_minute:
            return False, "Слишком часто. Подожди минуту."
        if len(events) >= self.per_day:
            return False, "Дневной лимит исчерпан. Попробуй завтра."
        events.append(now)
        return True, ""


rate_limiter = RateLimiter()
_render_sem: asyncio.Semaphore | None = None


def render_semaphore() -> asyncio.Semaphore:
    global _render_sem
    if _render_sem is None:
        _render_sem = asyncio.Semaphore(2)
    return _render_sem


async def run_render(func, *args, timeout: float = 30.0):
    async with render_semaphore():
        return await asyncio.wait_for(asyncio.to_thread(func, *args), timeout=timeout)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent
