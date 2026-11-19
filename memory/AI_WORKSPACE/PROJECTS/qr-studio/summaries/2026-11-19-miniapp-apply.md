# 2026-11-19 — применение настроек Mini App

## Проблема

Кнопка «Применить» в Telegram Mini App не возвращала настройки в бота.

## Причина

`WebApp.sendData` работает только для Mini App, открытых с keyboard-кнопки. Редактор открывается кнопкой меню, командой `/app` и inline-кнопкой, поэтому `sendData` в этих сценариях не доставлял данные.

## Исправление

- `webapp/app.js`: при непустом `tg.initData` настройки отправляются в `POST /app/apply`; для keyboard-кнопок сохранён fallback `tg.sendData`.
- `bot/miniapp.py`: endpoint `POST /app/apply` проверяет подпись `initData` (HMAC `WebAppData`, `auth_date` до 6 часов), создаёт synthetic `web_app_data` update и передаёт его в `Dispatcher.feed_update`.
- `bot/main.py`: в `setup_miniapp` передаются `bot` и `dispatcher`.
- `bot/handlers/webapp.py`: при валидных настройках preview отправляется даже если значения не изменились.
- `webapp/index.html`: cache-bust `app.js?v=apply1`, чтобы Telegram WebView не использовал старый JS.

## Проверки

- `pytest`: 46/46, включая подпись, просроченный initData и endpoint с fake dispatcher.
- `ruff`: без ошибок.
- `node --check webapp/app.js`: OK.
- `scripts/check_scans.py`: 262/262.
- Render live: `6c35f98`, затем cache-bust `ed3639e`; `/app/apply` без initData отвечает 400, live `app.js` содержит `/app/apply`, HTML подключает `?v=apply1`; webhook pending 0, ошибок нет.

## Осталось

- Живая проверка Apply в Telegram из menu/inline и keyboard-сценария.
- Уточнить запрос «QR на QR»: центральный логотип поверх QR или буквальное наложение QR на QR.
