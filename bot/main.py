from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import ClientSession, web

from .analytics import Analytics, AnalyticsMiddleware
from .config import Settings
from .errors import error_handler
from .handlers import admin, create, logo, menu, photo, settings, start, webapp
from .i18n import LanguageMiddleware, t, use_lang
from .miniapp import setup as setup_miniapp
from .services import set_menu_button

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

STARTED_AT = time.time()


async def health(_: web.Request) -> web.Response:
    return web.json_response(
        {
            "ok": True,
            "service": "qr-studio",
            "version": "1.0.0",
            "uptime": int(time.time() - STARTED_AT),
            "mode": "webhook",
        }
    )


def build() -> tuple[Bot, Dispatcher, Settings, Analytics]:
    cfg = Settings.from_env()
    bot = Bot(token=cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    analytics = Analytics(cfg.database_url)
    dp.update.outer_middleware(LanguageMiddleware())
    dp.update.outer_middleware(AnalyticsMiddleware(analytics, cfg.admin_id))
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(webapp.router)
    dp.include_router(logo.router)
    dp.include_router(photo.router)
    dp.include_router(create.router)
    dp.include_router(menu.router)
    dp.include_router(settings.router)
    dp.errors.register(error_handler)
    return bot, dp, cfg, analytics


async def set_commands(bot: Bot) -> None:
    def commands() -> list[BotCommand]:
        return [
            BotCommand(command="start", description=t("cmd_start")),
            BotCommand(command="language", description=t("cmd_language")),
            BotCommand(command="app", description=t("cmd_app")),
            BotCommand(command="qr", description=t("cmd_qr")),
            BotCommand(command="help", description=t("cmd_help")),
        ]

    with use_lang("en"):
        await bot.set_my_commands(commands())
    with use_lang("ru"):
        await bot.set_my_commands(commands(), language_code="ru")


async def self_ping(url: str, interval: int) -> None:
    await asyncio.sleep(60)
    async with ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=20) as response:
                    logger.info("self-ping %s -> %s", url, response.status)
            except Exception as exc:  # noqa: BLE001
                logger.warning("self-ping failed: %s", exc)
            await asyncio.sleep(interval)


async def run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    if not settings.webhook_base_url:
        raise RuntimeError("Set WEBHOOK_BASE_URL or RENDER_EXTERNAL_URL for webhook mode")
    if not settings.webhook_secret:
        raise RuntimeError("WEBHOOK_SECRET is empty")
    path = f"/webhook/{settings.webhook_secret}"
    webhook_url = settings.webhook_base_url + path
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/healthz", health)
    setup_miniapp(app, bot=bot, dispatcher=dp)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=settings.webhook_secret).register(app, path=path)
    setup_application(app, dp, bot=bot)

    async def on_startup(_: web.Application) -> None:
        await set_commands(bot)
        await set_menu_button(bot)
        await bot.set_webhook(
            webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
        logger.info("webhook set: %s", webhook_url)
        if settings.self_ping_interval > 0:
            _ = asyncio.create_task(self_ping(settings.webhook_base_url + "/healthz", settings.self_ping_interval))

    app.on_startup.append(on_startup)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.port)
    await site.start()
    logger.info("web server started on port %s", settings.port)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands(bot)
    logger.info("polling started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main() -> None:
    bot, dp, cfg, analytics = build()
    await analytics.connect()
    try:
        if cfg.mode == "polling":
            await run_polling(bot, dp)
        else:
            await run_webhook(bot, dp, cfg)
    finally:
        await analytics.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
