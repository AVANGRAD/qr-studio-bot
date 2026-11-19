# Итог: поддержка и all-time статистика

Дата: 2026-11-19

## Сделано

- В `/stats` добавлены `total_events` и `events_all`: общее число событий и топ событий за всё время.
- Добавлен `bot/support.py` с отдельным `SupportBot` на `SUPPORT_BOT_TOKEN`.
- Support-бот обслуживается тем же aiohttp-сервером по `/support/webhook/<secret>`; основной webhook не меняется.
- Пользовательские сообщения пересылаются `ADMIN_ID`; ответ администратора reply на пересланное сообщение или карточку копируется пользователю.
- Mapping `admin_message_id → user_id` хранится в `support.tickets`; без БД используется память.
- В основной бот добавлена `/support` со ссылкой на `@QUaRc0DeSupport_bot` и команда в меню.
- `SUPPORT_BOT_TOKEN` добавлен в `.env`, `.env.example`, `render.yaml`, Render Environment. `SUPPORT_WEBHOOK_SECRET` не задан и выводится из токена.

## Проверки

- `pytest` 74/74, `ruff` OK.
- Support webhook route: 401 без secret, 200 с secret (локальный aiohttp test client).
- `support.tickets` создана в Supabase; тестовая строка удалена.
- Support bot `@QUaRc0DeSupport_bot` (`9194029190`) существует; webhook ещё не установлен до деплоя.
- Администратор ещё не запускал support-бота, поэтому `sendMessage(ADMIN_ID)` вернул `chat not found`.

## Деплой и live

- Коммит `f1f8f32`, deploy `dep-dbvfl1mq1p3s738ero7g` live 2026-11-19 13:32 UTC.
- `/healthz` вернул `support: true`; main и support webhook pending 0, last_error пустой.
- Логи: `analytics database connected`, `support database connected`, `support webhook set`; `support bot startup failed`/`Traceback` нет.
- Support route с secret — 200; synthetic `/stats` — 200, событие записано.
- В основной бот администратору отправлена ссылка на `@QUaRc0DeSupport_bot`.

## Дальше

- Администратору нажать `/start` в support-боте.
- Проверить реальный тикет: сообщение пользователя → карточка админу → reply → ответ пользователю.
