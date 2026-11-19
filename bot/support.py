from __future__ import annotations

import asyncio
import html
import logging

import asyncpg
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from .config import Settings
from .i18n import resolve_lang, t, use_lang

logger = logging.getLogger(__name__)

SUPPORT_SCHEMA = (
    "CREATE SCHEMA IF NOT EXISTS support",
    """
    CREATE TABLE IF NOT EXISTS support.tickets (
        admin_message_id BIGINT PRIMARY KEY,
        user_id BIGINT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        replied_at TIMESTAMPTZ
    )
    """,
    "CREATE INDEX IF NOT EXISTS support_tickets_user_idx ON support.tickets (user_id)",
)


class SupportStore:
    def __init__(self, database_url: str | None) -> None:
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None
        self._memory: dict[int, int] = {}
        self._lock = asyncio.Lock()

    @property
    def ready(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        if self._pool is not None or not self.database_url:
            return
        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=2,
                timeout=10,
                command_timeout=5,
                ssl="require",
                statement_cache_size=0,
                server_settings={"application_name": "qr-studio-support"},
            )
            async with self._pool.acquire() as connection:
                for statement in SUPPORT_SCHEMA:
                    await connection.execute(statement)
            logger.info("support database connected")
        except Exception:
            logger.exception("support database connection failed; using memory mapping")
            if self._pool is not None:
                await self._pool.close()
                self._pool = None

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
        self._memory.clear()

    async def remember(self, admin_message_id: int, user_id: int) -> None:
        if self._pool is None:
            async with self._lock:
                self._memory[int(admin_message_id)] = int(user_id)
            return
        async with self._pool.acquire() as connection:
            await connection.execute(
                """
                INSERT INTO support.tickets (admin_message_id, user_id)
                VALUES ($1, $2)
                ON CONFLICT (admin_message_id) DO UPDATE SET user_id = EXCLUDED.user_id
                """,
                int(admin_message_id),
                int(user_id),
            )

    async def resolve(self, admin_message_id: int) -> int | None:
        if self._pool is None:
            async with self._lock:
                return self._memory.get(int(admin_message_id))
        async with self._pool.acquire() as connection:
            value = await connection.fetchval(
                "SELECT user_id FROM support.tickets WHERE admin_message_id = $1",
                int(admin_message_id),
            )
        return int(value) if value is not None else None

    async def mark_replied(self, admin_message_id: int) -> None:
        if self._pool is None:
            return
        async with self._pool.acquire() as connection:
            await connection.execute(
                "UPDATE support.tickets SET replied_at = now() WHERE admin_message_id = $1",
                int(admin_message_id),
            )


router = Router(name="support")


def _lang_for(message: Message) -> str:
    return resolve_lang(message.from_user.language_code if message.from_user else None)


def _ticket_header(message: Message, ticket_id: int) -> str:
    user = message.from_user
    assert user is not None
    username = f"@{user.username}" if user.username else "—"
    return t(
        "support_ticket",
        ticket_id=ticket_id,
        name=html.escape(user.full_name),
        username=html.escape(username),
        user_id=user.id,
    )


@router.message(CommandStart())
async def support_start(message: Message) -> None:
    with use_lang(_lang_for(message)):
        await message.answer(t("support_welcome"))


@router.message(Command("help"))
async def support_help(message: Message) -> None:
    with use_lang(_lang_for(message)):
        await message.answer(t("support_help"))


async def _user_message(message: Message, bot: Bot, store: SupportStore, admin_id: int) -> None:
    user = message.from_user
    assert user is not None
    lang = _lang_for(message)
    with use_lang(lang):
        if message.chat.type != "private":
            await message.answer(t("support_private_only"))
            return
        try:
            forwarded = await bot.forward_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id,
            )
        except TelegramForbiddenError:
            logger.exception("support admin is unavailable")
            await message.answer(t("support_unavailable"))
            return
        except TelegramBadRequest:
            logger.exception("support forward failed")
            await message.answer(t("support_forward_failed"))
            return
        try:
            await store.remember(forwarded.message_id, user.id)
            header = await bot.send_message(
                admin_id,
                _ticket_header(message, forwarded.message_id),
                reply_to_message_id=forwarded.message_id,
            )
            await store.remember(header.message_id, user.id)
        except Exception:
            logger.exception("support ticket mapping failed")
            await message.answer(t("support_forward_failed"))
            return
        await message.answer(t("support_received"))


async def _admin_message(message: Message, bot: Bot, store: SupportStore, admin_id: int) -> None:
    lang = _lang_for(message)
    with use_lang(lang):
        reply = message.reply_to_message
        if reply is None:
            await message.answer(t("support_admin_hint"))
            return
        user_id = await store.resolve(reply.message_id)
        if user_id is None and reply.forward_from is not None:
            user_id = reply.forward_from.id
        if user_id is None:
            await message.answer(t("support_ticket_not_found"))
            return
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=admin_id,
                message_id=message.message_id,
            )
        except TelegramForbiddenError:
            await message.answer(t("support_user_blocked", user_id=user_id))
            return
        except TelegramBadRequest as exc:
            logger.warning("support reply failed: %s", exc)
            await message.answer(t("support_reply_failed", error=html.escape(str(exc))))
            return
        await store.mark_replied(reply.message_id)
        await message.answer(t("support_reply_sent", user_id=user_id))


@router.message()
async def support_message(
    message: Message,
    bot: Bot,
    support_store: SupportStore | None = None,
    admin_id: int | None = None,
) -> None:
    if support_store is None or admin_id is None:
        with use_lang(_lang_for(message)):
            await message.answer(t("support_not_configured"))
        return
    if message.from_user is None:
        return
    if message.from_user.id == admin_id:
        await _admin_message(message, bot, support_store, admin_id)
        return
    await _user_message(message, bot, support_store, admin_id)


class SupportBot:
    def __init__(self, settings: Settings) -> None:
        if not settings.support_bot_token:
            raise ValueError("SUPPORT_BOT_TOKEN is not set")
        if not settings.support_webhook_secret:
            raise ValueError("SUPPORT_WEBHOOK_SECRET is not set")
        self.settings = settings
        self.admin_id = settings.admin_id
        self.secret = settings.support_webhook_secret
        self.path = f"/support/webhook/{self.secret}"
        self.bot = Bot(
            token=settings.support_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.store = SupportStore(settings.database_url)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.dp["support_store"] = self.store
        self.dp["admin_id"] = self.admin_id
        self.dp.include_router(router)

    async def connect(self) -> None:
        await self.store.connect()

    async def close(self) -> None:
        await self.store.close()
        await self.bot.session.close()

    async def set_commands(self) -> None:
        def commands() -> list[BotCommand]:
            return [
                BotCommand(command="start", description=t("cmd_start")),
                BotCommand(command="help", description=t("cmd_help")),
            ]

        with use_lang("en"):
            await self.bot.set_my_commands(commands())
        with use_lang("ru"):
            await self.bot.set_my_commands(commands(), language_code="ru")

    async def set_webhook(self, base_url: str) -> None:
        url = base_url.rstrip("/") + self.path
        await self.bot.set_webhook(
            url,
            secret_token=self.secret,
            allowed_updates=self.dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info("support webhook set: %s/support/webhook/***", base_url.rstrip("/"))

    async def run_polling(self) -> None:
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.set_commands()
        logger.info("support polling started")
        await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())

    def register(self, app: web.Application) -> None:
        SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
            secret_token=self.secret,
        ).register(app, path=self.path)
        setup_application(app, self.dp, bot=self.bot)


def build_support(settings: Settings) -> SupportBot | None:
    if not settings.support_bot_token:
        return None
    if settings.support_bot_token == settings.bot_token:
        logger.error("SUPPORT_BOT_TOKEN must belong to a different bot")
        return None
    return SupportBot(settings)
