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

## Дальше

- Закоммитить и задеплоить оба бота одним сервисом.
- Проверить `@QUaRc0DeSupport_bot` webhook, `/support` в основном боте и live-тикет.
- Администратору нажать `/start` в support-боте.
