from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import asyncpg
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from .db import ssl_context

logger = logging.getLogger(__name__)

SCHEMA_STATEMENTS = (
    "CREATE SCHEMA IF NOT EXISTS analytics",
    """
    CREATE TABLE IF NOT EXISTS analytics.users (
        user_id BIGINT PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        language_code TEXT,
        first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
        updates_count BIGINT NOT NULL DEFAULT 0,
        starts_count BIGINT NOT NULL DEFAULT 0,
        last_event TEXT,
        blocked_at TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS analytics.events (
        id BIGSERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        event_type TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb
    )
    """,
    "CREATE INDEX IF NOT EXISTS users_last_seen_idx ON analytics.users (last_seen)",
    "CREATE INDEX IF NOT EXISTS users_first_seen_idx ON analytics.users (first_seen)",
    "CREATE INDEX IF NOT EXISTS events_created_at_idx ON analytics.events (created_at)",
    "CREATE INDEX IF NOT EXISTS events_user_created_idx ON analytics.events (user_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS events_type_created_idx ON analytics.events (event_type, created_at DESC)",
)

USER_UPSERT = """
INSERT INTO analytics.users (
    user_id, username, first_name, language_code,
    first_seen, last_seen, updates_count, starts_count, last_event, blocked_at
)
VALUES ($1, $2, $3, $4, now(), now(), 1, CASE WHEN $5 = 'start' THEN 1 ELSE 0 END, $5, NULL)
ON CONFLICT (user_id) DO UPDATE SET
    username = EXCLUDED.username,
    first_name = EXCLUDED.first_name,
    language_code = EXCLUDED.language_code,
    last_seen = now(),
    updates_count = analytics.users.updates_count + 1,
    starts_count = analytics.users.starts_count + CASE WHEN EXCLUDED.last_event = 'start' THEN 1 ELSE 0 END,
    last_event = EXCLUDED.last_event,
    blocked_at = NULL
"""

EVENT_INSERT = """
INSERT INTO analytics.events (user_id, event_type, metadata)
VALUES ($1, $2, $3::jsonb)
"""

USER_STATS = """
SELECT
    count(*)::int AS total,
    count(*) FILTER (WHERE first_seen >= date_trunc('day', now()))::int AS new_today,
    count(*) FILTER (WHERE first_seen >= now() - interval '7 days')::int AS new_week,
    count(*) FILTER (WHERE first_seen >= now() - interval '30 days')::int AS new_month,
    count(*) FILTER (WHERE last_seen >= now() - interval '15 minutes')::int AS online,
    count(*) FILTER (WHERE last_seen < now() - interval '30 days')::int AS dormant,
    count(*) FILTER (WHERE blocked_at IS NOT NULL)::int AS blocked
FROM analytics.users
"""

ACTIVITY_STATS = """
SELECT
    count(DISTINCT user_id) FILTER (WHERE created_at >= date_trunc('day', now()))::int AS dau,
    count(DISTINCT user_id) FILTER (WHERE created_at >= now() - interval '7 days')::int AS wau,
    count(DISTINCT user_id) FILTER (WHERE created_at >= now() - interval '30 days')::int AS mau
FROM analytics.events
"""

LANGUAGE_STATS = """
SELECT coalesce(language_code, '—') AS language, count(*)::int AS count
FROM analytics.users
GROUP BY 1
ORDER BY 2 DESC, 1
"""

EVENT_STATS = """
SELECT event_type, count(*)::int AS count
FROM analytics.events
WHERE created_at >= now() - interval '7 days'
GROUP BY 1
ORDER BY 2 DESC, 1
LIMIT 10
"""

TOTAL_EVENTS = """
SELECT count(*)::int AS total
FROM analytics.events
"""

EVENT_STATS_ALL = """
SELECT event_type, count(*)::int AS count
FROM analytics.events
GROUP BY 1
ORDER BY 2 DESC, 1
LIMIT 10
"""


class AnalyticsMiddleware(BaseMiddleware):
    def __init__(self, analytics: Analytics, admin_id: int | None = None) -> None:
        self.analytics = analytics
        self.admin_id = admin_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["analytics"] = self.analytics
        data["admin_id"] = self.admin_id
        if isinstance(event, Update):
            user = data.get("event_from_user")
            if isinstance(user, User):
                self.analytics.schedule_update(user, event_from_update(event))
        return await handler(event, data)


@dataclass(frozen=True)
class StatsSnapshot:
    total: int
    new_today: int
    new_week: int
    new_month: int
    online: int
    dau: int
    wau: int
    mau: int
    dormant: int
    blocked: int
    languages: tuple[tuple[str, int], ...]
    events: tuple[tuple[str, int], ...]
    total_events: int = 0
    events_all: tuple[tuple[str, int], ...] = ()


def event_from_update(update: Update) -> str:
    message = update.message
    if message is not None:
        if message.web_app_data is not None:
            return "mini_app_apply"
        if message.successful_payment is not None:
            return "payment"
        if message.photo:
            return "photo"
        if message.document:
            return "document"
        text = (message.text or "").lstrip()
        if text.startswith("/"):
            command = text.split(maxsplit=1)[0].split("@", 1)[0].lower()
            return "start" if command == "/start" else "command"
        return "message"

    callback = update.callback_query
    if callback is not None:
        data = callback.data or ""
        if data.startswith("lang:set:"):
            return "language_change"
        if data == "dl:png":
            return "png_download"
        if data == "dl:svg":
            return "svg_download"
        if data.startswith("preset:set:"):
            return "preset_apply"
        if data.startswith("shape:set:"):
            return "shape_change"
        if data.startswith("style:set:"):
            return "pattern_change"
        if data.startswith("eye:set:"):
            return "eye_change"
        if data.startswith("pal:set:"):
            return "palette_change"
        if data.startswith("size:set:"):
            return "size_change"
        if data.startswith("logo:"):
            return "logo_change"
        if data in {"menu:new", "draft:new"}:
            return "new_qr"
        if data == "menu:random":
            return "random_style"
        return "callback"

    for update_type in ("inline_query", "my_chat_member", "chat_member", "pre_checkout_query"):
        if getattr(update, update_type, None) is not None:
            return update_type
    if update.edited_message is not None:
        return "message_edit"
    return "other"


class Analytics:
    def __init__(self, database_url: str | None) -> None:
        self.database_url = database_url
        self._pool: asyncpg.Pool | None = None
        self._tasks: set[asyncio.Task[None]] = set()

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
                max_size=5,
                timeout=10,
                command_timeout=5,
                ssl=ssl_context(),
                statement_cache_size=0,
                server_settings={"application_name": "qr-studio-bot"},
            )
            logger.info("analytics database connected")
        except Exception:
            logger.exception("analytics database connection failed")
            if self._pool is not None:
                await self._pool.close()
                self._pool = None

    async def close(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            self._tasks.clear()
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def record_update(self, user: User | None, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        if self._pool is None or user is None:
            return
        payload = json.dumps(metadata or {}, ensure_ascii=False, separators=(",", ":"))
        async with self._pool.acquire() as connection, connection.transaction():
            await connection.execute(
                USER_UPSERT,
                int(user.id),
                user.username,
                user.first_name,
                user.language_code,
                event_type,
            )
            await connection.execute(EVENT_INSERT, int(user.id), event_type, payload)

    def schedule_update(self, user: User | None, event_type: str, metadata: dict[str, Any] | None = None) -> None:
        if self._pool is None or user is None:
            return
        task = asyncio.create_task(self._safe_record(user, event_type, metadata))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _safe_record(self, user: User, event_type: str, metadata: dict[str, Any] | None) -> None:
        try:
            await self.record_update(user, event_type, metadata)
        except Exception:
            logger.exception("analytics update failed")

    async def mark_blocked(self, user_id: int) -> None:
        if self._pool is None:
            return
        try:
            async with self._pool.acquire() as connection:
                await connection.execute(
                    "UPDATE analytics.users SET blocked_at = now() WHERE user_id = $1",
                    int(user_id),
                )
        except Exception:
            logger.exception("analytics blocked update failed")

    async def stats(self) -> StatsSnapshot | None:
        if self._pool is None:
            return None
        async with self._pool.acquire() as connection:
            users = await connection.fetchrow(USER_STATS)
            activity = await connection.fetchrow(ACTIVITY_STATS)
            languages = await connection.fetch(LANGUAGE_STATS)
            events = await connection.fetch(EVENT_STATS)
            total_events = await connection.fetchval(TOTAL_EVENTS)
            events_all = await connection.fetch(EVENT_STATS_ALL)
        if users is None or activity is None:
            return None
        return StatsSnapshot(
            total=int(users["total"]),
            new_today=int(users["new_today"]),
            new_week=int(users["new_week"]),
            new_month=int(users["new_month"]),
            online=int(users["online"]),
            dau=int(activity["dau"]),
            wau=int(activity["wau"]),
            mau=int(activity["mau"]),
            dormant=int(users["dormant"]),
            blocked=int(users["blocked"]),
            languages=tuple((str(row["language"]), int(row["count"])) for row in languages),
            events=tuple((str(row["event_type"]), int(row["count"])) for row in events),
            total_events=int(total_events or 0),
            events_all=tuple((str(row["event_type"]), int(row["count"])) for row in events_all),
        )
