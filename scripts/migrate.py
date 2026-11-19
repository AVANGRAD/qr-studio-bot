from __future__ import annotations

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

from bot.analytics import SCHEMA_STATEMENTS
from bot.db import ssl_context
from bot.support import SUPPORT_SCHEMA


async def main() -> None:
    load_dotenv()
    url = (os.getenv("DATABASE_ADMIN_URL") or os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_ADMIN_URL or DATABASE_URL is not set")
    connection = await asyncpg.connect(
        url,
        ssl=ssl_context(),
        statement_cache_size=0,
        server_settings={"application_name": "qr-studio-migrate"},
    )
    try:
        for statement in (*SCHEMA_STATEMENTS, *SUPPORT_SCHEMA):
            await connection.execute(statement)
    finally:
        await connection.close()
    print("migrations applied")


if __name__ == "__main__":
    asyncio.run(main())
