# 2026-11-19 — Mini App Apply

Пользователь: кнопка «Применить» в Mini App не работает.

Диагностика: `WebApp.sendData` не работает для menu/inline Mini App. Решение: серверный `POST /app/apply` с проверкой `initData` и synthetic `web_app_data`; `sendData` оставлен для keyboard-кнопок. Добавлен cache-bust `app.js?v=apply1`.

Проверки: pytest 46/46, ruff OK, node OK, scans 262/262. Live deploy `6c35f98`, cache-bust `ed3639e`; webhook pending 0. Осталось: живая проверка Apply в Telegram и уточнение запроса «QR на QR».

После Apply пользователь сообщил, что не работают кнопки скачивания PNG/SVG. Найден caption-баг для ссылок с `&`; исправлены SVG-caption, XML-escape мононограммы и добавлен fallback без caption.
