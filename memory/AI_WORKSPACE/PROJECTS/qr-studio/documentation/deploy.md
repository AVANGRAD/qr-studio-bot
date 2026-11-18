# Deploy Notes

- Render Blueprint: `render.yaml`.
- Start: `python -m bot.main`.
- Health: `/healthz`.
- Env: `BOT_TOKEN`, `BOT_MODE=webhook`, `WEBHOOK_SECRET` (generate), `SELF_PING_INTERVAL_SECONDS=600`.
- `WEBHOOK_BASE_URL` берётся из `RENDER_EXTERNAL_URL`.
- Секреты хранятся только в Render/env, не в git.
