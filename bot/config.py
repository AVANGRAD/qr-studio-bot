from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot_token: str
    mode: str = "webhook"
    port: int = 10000
    webhook_base_url: str | None = None
    webhook_secret: str | None = None
    self_ping_interval: int = 600
    admin_id: int | None = None
    max_content: int = 1200
    max_logo_bytes: int = 6 * 1024 * 1024
    preview_size: int = 640
    version: str = "1.0.0"

    @classmethod
    def from_env(cls) -> Settings:
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("BOT_TOKEN is not set")
        mode = os.getenv("BOT_MODE", "webhook").strip().lower()
        if mode not in {"webhook", "polling"}:
            mode = "webhook"
        base = (os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").strip().rstrip("/") or None
        secret = (os.getenv("WEBHOOK_SECRET") or "").strip() or None
        if secret is None and mode == "webhook":
            import hashlib

            secret = hashlib.sha256(token.encode("utf-8")).hexdigest()[:40]
        admin = os.getenv("ADMIN_ID", "").strip()
        return cls(
            bot_token=token,
            mode=mode,
            port=int(os.getenv("PORT", "10000")),
            webhook_base_url=base,
            webhook_secret=secret,
            self_ping_interval=max(0, int(os.getenv("SELF_PING_INTERVAL_SECONDS", "600"))),
            admin_id=int(admin) if admin.isdigit() else None,
            max_content=max(200, int(os.getenv("MAX_CONTENT_LENGTH", "1200"))),
            max_logo_bytes=max(512 * 1024, int(os.getenv("MAX_LOGO_BYTES", str(6 * 1024 * 1024)))),
        )
