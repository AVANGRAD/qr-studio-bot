# Deploy Notes

- Render Blueprint: `render.yaml`.
- Start: `python -m bot.main`.
- Health: `/healthz`.
- Mini App: `/app`, каталог `/app/catalog.json`, плитки `/app/thumbs/`, превью `/app/preview.png`.
- Env: `BOT_TOKEN`, `BOT_MODE=webhook`, `SELF_PING_INTERVAL_SECONDS=600`.
- `WEBHOOK_SECRET` можно не задавать: будет hash токена. Если задавать — только URL-safe/hex; `generateValue` не использовать.
- `WEBHOOK_BASE_URL` берётся из `RENDER_EXTERNAL_URL`.
- Плитки Mini App пересобираются локально: `python scripts/build_miniapp_thumbs.py`; результат коммитится.
- Секреты хранятся только в Render/env, не в git.
