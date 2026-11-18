# Errors

## 2026-11-18 — SVG mismatched tag

- Причина: в `render_svg` открывался `<defs>`, но не закрывался.
- Исправление: добавлен `</defs>`.
- Проверка: XML-парсинг всех 44 форм.

## 2026-11-18 — NameError `contrast` в render()

- Причина: при правке `_contrast_spec` переменная заменена на `_` в PNG-рендере.
- Исправление: вернули `contrast`, оставили `_` только в SVG.
- Проверка: pytest 23/23.

## 2026-11-18 — Ложные scan-провалы

- Причина: слишком агрессивные формы глаз/модулей и крупный угловой логотип.
- Исправление: safe-base + overlay, лимит углового логотипа 0.105.
- Проверка: 140/140.

## 2026-11-18 — webhook: Cannot run the event loop while another loop is running

- Причина: `web.run_app()` вызывался внутри `asyncio.run()`.
- Исправление: `AppRunner` + `TCPSite` внутри уже работающего loop.
- Проверка: Render deploy live, `/healthz` 200.

## 2026-11-18 — secret token contains illegal characters

- Причина: Render `generateValue` выдал секрет с недопустимыми для Telegram символами.
- Исправление: hex-секрет + нормализация секрета в `Settings`.
- Проверка: webhook установлен, `last_error_message` пустой.

## 2026-11-18 — AttributeError: FakeMessage has no attribute chat

- Причина: после ограничения Mini App private-чатами `common.send_preview` напрямую читал `message.chat`, а тестовый FakeMessage его не имел.
- Исправление: `getattr(message, "chat", None)` и проверка типа с fallback `private`.
- Проверка: pytest 29/29.
