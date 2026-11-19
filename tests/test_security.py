from __future__ import annotations

from bot.config import Settings
from bot.services import RateLimiter


def test_webhook_paths_do_not_expose_header_secrets() -> None:
    settings = Settings(
        bot_token="token",
        webhook_secret="main-secret-" + "a" * 32,
        support_bot_token="support-token",
        support_webhook_secret="support-secret-" + "b" * 32,
    )
    assert settings.webhook_secret not in settings.webhook_path
    assert settings.support_webhook_secret not in settings.support_webhook_path
    assert settings.webhook_path.startswith("/webhook/")
    assert settings.support_webhook_path.startswith("/support/webhook/")


def test_webhook_paths_are_stable() -> None:
    first = Settings(bot_token="token", webhook_secret="x" * 32)
    second = Settings(bot_token="token", webhook_secret="x" * 32)
    assert first.webhook_path == second.webhook_path


def test_rate_limiter_hour_bucket() -> None:
    limiter = RateLimiter(per_minute=10, per_hour=2, per_day=10)
    assert limiter.allow(1)[0]
    assert limiter.allow(1)[0]
    assert not limiter.allow(1)[0]
