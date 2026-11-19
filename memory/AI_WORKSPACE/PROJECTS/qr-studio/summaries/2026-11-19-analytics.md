# Итог: аналитика пользователей

Обновлено: 2026-11-19

## Что сделано

- Добавлен `bot/analytics.py`: подключение к PostgreSQL через `asyncpg`, схема `analytics`, upsert пользователей и запись событий.
- Схема: `analytics.users` (`user_id`, `username`, `first_name`, `language_code`, `first_seen`, `last_seen`, `updates_count`, `starts_count`, `last_event`, `blocked_at`) и `analytics.events` (`user_id`, `event_type`, `created_at`, `metadata`).
- `AnalyticsMiddleware` на `dp.update.outer_middleware` пишет активность по каждому update и пробрасывает `analytics`/`admin_id` в handlers.
- `/stats` доступен только при заданном `ADMIN_ID`; показывает всего/новых/активных/неактивных/заблокировавших и топ событий.
- Для Mini App Apply пишется `mini_app_apply`; для скачиваний — `png_download`/`svg_download`; для смен языка/стиля и пресетов — отдельные события.
- Тексты сообщений и содержимое QR не сохраняются.
- `asyncpg==0.32.0` добавлен в `requirements.txt`, `DATABASE_URL` — в `.env.example` и `render.yaml`.

## Проверки

- Локальное подключение к новому Supabase PostgreSQL 17.12: успешно; таблицы созданы.
- Тестовая запись пользователя и двух событий, проверка `stats()`, удаление тестовых строк: успешно.
- `pytest`: 70/70; `ruff`: OK.
- Render Environment: `DATABASE_URL` добавлен, существующие переменные сохранены.
- `ADMIN_ID` найден через `getChat` по ID из пользовательских секретов и задан локально и в Render; `/stats` активирован после деплоя.

## Ограничения

- Telegram не присылает событие «пользователь ушёл»; `dormant` — это отсутствие активности 30+ дней, `blocked_at` — только при получении 403 от Telegram.
- Если БД недоступна, аналитика пропускает записи, бот продолжает работать.
- Язык по-прежнему хранится в `MemoryStorage`; аналитическая БД не заменяет FSM.

## Деплой и live

- Коммит `afe6edf`, Render deploy `dep-dbvf7jjm8hqs73b2r28g` live 2026-11-19 13:04 UTC.
- Live-проверки: `/healthz`, `/app`, `/app/static/app.js`, `/app/catalog.json?lang=ru` — 200; webhook pending 0; в логах `analytics database connected`.
- Synthetic `/stats` от ADMIN_ID прошёл 200; `analytics.users`/`analytics.events` получили запись, ошибок нет.

## Далее

- Живая проверка обычных пользовательских событий после `/start`/QR.
- Закоммитить и задеплоить изменения, проверить `/stats` и события в live.
