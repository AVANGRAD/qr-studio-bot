from __future__ import annotations

import asyncio
import html
import io
import logging
import os
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode, urlparse

from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
from PIL import Image, ImageOps, UnidentifiedImageError

from qrstudio.logo import prepare_logo
from qrstudio.presets import get_preset
from qrstudio.render import RenderOptions, RenderResult, render, render_svg

from .i18n import current_lang, display_name, mode_name, t, warning_text

MAX_CONTENT = 1200
logger = logging.getLogger(__name__)


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
    logo_label: str = ""
    logo_emblem: str = ""
    silhouette: bool = True
    photo_bytes: bytes | None = None

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

    @property
    def has_photo(self) -> bool:
        return bool(self.photo_bytes)

    def photo_image(self) -> Image.Image | None:
        if not self.photo_bytes:
            return None
        try:
            return Image.open(io.BytesIO(self.photo_bytes)).convert("RGBA")
        except Exception:  # noqa: BLE001
            return None


def normalize_content(value: str, max_length: int = MAX_CONTENT) -> str:
    text = (value or "").strip()
    if not text:
        raise ContentError(t("empty_content"))
    if len(text) > max_length:
        raise ContentError(t("too_long_content", length=len(text), max_length=max_length))
    if text.startswith("www."):
        text = "https://" + text
    if "://" in text and not text.lower().startswith(("http://", "https://", "tg://")):
        raise ContentError(t("bad_scheme"))
    if text.lower().startswith(("http://", "https://")):
        parsed = urlparse(text)
        if not parsed.netloc or " " in parsed.netloc:
            raise ContentError(t("bad_url"))
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
        silhouette=draft.silhouette,
        photo=draft.photo_image(),
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


def webapp_base_url() -> str:
    base = (os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://qr-studio-bot.onrender.com").rstrip("/")
    if not base.startswith("https://"):
        base = "https://qr-studio-bot.onrender.com"
    return base


def webapp_entry_url(lang: str | None = None) -> str:
    base = f"{webapp_base_url()}/app"
    if lang:
        return f"{base}?{urlencode({'lang': lang})}"
    return base


async def set_menu_button(bot: Bot, lang: str | None = None, chat_id: int | None = None) -> None:
    try:
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonWebApp(
                text="QR Studio",
                web_app=WebAppInfo(url=webapp_entry_url(lang)),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("menu button update failed for chat %s: %s", chat_id, exc)


def webapp_url(draft: Draft, lang: str | None = None) -> str:
    base = webapp_base_url()
    query = urlencode(
        {
            "shape": draft.shape,
            "module": draft.module_style,
            "eye": draft.eye_style,
            "palette": draft.palette,
            "size": draft.size,
            "lang": lang or current_lang.get(),
        }
    )
    return f"{base}/app?{query}"


def caption(draft: Draft, result: RenderResult | None = None) -> str:
    logo = t("logo_none")
    if draft.logo_mode == "monogram":
        logo = t("logo_monogram", text=html.escape(draft.logo_text))
    elif draft.has_logo:
        logo = mode_name(draft.logo_mode)
        if draft.logo_emblem:
            logo = f"{html.escape(display_name('emblem', draft.logo_emblem))} · {logo}"
        elif draft.logo_label:
            logo = f"{html.escape(draft.logo_label)} · {logo}"
    lines = [
        f"<b>QR Studio</b> · {draft.size} px",
        f"<code>{html.escape(short(draft.content))}</code>",
        "",
    ]
    if draft.has_photo:
        lines.append(t("caption_photo"))
    else:
        lines.append(
            t(
                "caption_form",
                shape=display_name("shape", draft.shape),
                style=display_name("module", draft.module_style),
            )
        )
    lines.extend(
        [
            t(
                "caption_eyes",
                eyes=display_name("eye", draft.eye_style),
                palette=display_name("palette", draft.palette),
            ),
            t("caption_logo", logo=logo),
        ]
    )
    if result:
        lines.append(t("caption_metrics", module=result.module_px, contrast=result.contrast))
        if result.warning_codes:
            for code, params in result.warning_codes:
                lines.append(f"<i>{html.escape(warning_text(code, params))}</i>")
        else:
            for warning in result.warnings:
                lines.append(f"<i>{html.escape(warning)}</i>")
        if result.module_px < 4.5:
            lines.append(f"<i>{t('caption_small')}</i>")
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


def prepare_uploaded_photo(raw: bytes) -> bytes:
    if len(raw) > 12 * 1024 * 1024:
        raise ContentError(t("photo_too_large"))
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ContentError(t("photo_unreadable")) from exc
    image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=88, optimize=True)
    payload = buffer.getvalue()
    if len(payload) > 3 * 1024 * 1024:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=76, optimize=True)
        payload = buffer.getvalue()
    return payload


def prepare_uploaded_logo(raw: bytes) -> bytes:
    if len(raw) > 8 * 1024 * 1024:
        raise ContentError(t("logo_too_large"))
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ContentError(t("logo_unreadable")) from exc
    prepared = prepare_logo(raw, max_side=1024)
    buffer = io.BytesIO()
    prepared.save(buffer, format="PNG")
    if len(buffer.getvalue()) > 4 * 1024 * 1024:
        raise ContentError(t("logo_too_heavy"))
    return buffer.getvalue()


class RateLimiter:
    def __init__(self, per_minute: int = 14, per_day: int = 240, per_hour: int = 0) -> None:
        self.per_minute = per_minute
        self.per_hour = per_hour
        self.per_day = per_day
        self._events: dict[int, deque[float]] = defaultdict(deque)

    def allow(self, user_id: int) -> tuple[bool, str]:
        now = time.monotonic()
        events = self._events[user_id]
        while events and now - events[0] > 86400:
            events.popleft()
        if sum(1 for value in events if now - value <= 60) >= self.per_minute:
            return False, t("rate_minute")
        if self.per_hour and sum(1 for value in events if now - value <= 3600) >= self.per_hour:
            return False, t("rate_hour")
        if len(events) >= self.per_day:
            return False, t("rate_day")
        events.append(now)
        return True, ""

    def reset(self) -> None:
        self._events.clear()


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
