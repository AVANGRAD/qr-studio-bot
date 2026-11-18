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

## 2026-11-18 — поиск свободного квадрата сделал QR нечитаемым

- Попытка: перебирать позиции/размеры QR внутри силуэта и проверять finder/data coverage.
- Результат: 6 форм (`snowflake`, `fox`, `turtle`, `mask`, `guitar`, `pumpkin`) прошли эвристику, но не декодировались; поиск был медленным (~55 с на 44 формы).
- Исправление: откат к центральному `_fit_plate` + безопасный frame-fallback; оставлен только фикс округления координат покрытия.
- Проверка: 184/184 scan, включая 44 figure-рендера.

## 2026-11-18 — scan-провал модуля «Цветочек»

- Симптом: `module_flower` и `preset_forest` не декодировались в `check_scans.py` на 512/768 px.
- Причина: overlay-фигура с внутренним вырезом давала слишком мало тёмного покрытия при мелком модуле.
- Исправление: `MODULE_BASE_STYLES["flower"] = "dot"` — безопасная база плюс цветочный overlay.
- Проверка: 262/262 scan, включая `flower` и `forest`.
