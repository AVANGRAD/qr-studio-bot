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

## 2026-11-19 — Apply в Mini App не возвращает настройки

- Симптом: кнопка «Применить» закрывает редактор, но превью в боте не обновляется.
- Причина: `WebApp.sendData` доставляет данные только для Mini App, открытых с keyboard-кнопки; menu/inline-кнопки этот вызов игнорируют.
- Исправление: `POST /app/apply` с `initData`, HMAC-проверка, synthetic `web_app_data` и `Dispatcher.feed_update`; `sendData` оставлен fallback.
- Дополнительно: preview отправляется даже при повторном применении тех же настроек; `app.js?v=apply1` сбрасывает кэш WebView.
- Проверка: pytest 46/46, scans 262/262, live `/app/apply` 400 без initData; живой Telegram-тест за пользователем.

## 2026-11-19 — PNG/SVG download не отправляется

- Симптом: нажатие «Скачать PNG»/«Скачать SVG» не даёт файл.
- Причина: SVG-caption подставлял `draft.content` в HTML без экранирования; Telegram отклонял `&` в ссылках. XML-мононограмма также не экранировалась.
- Исправление: `html.escape(short(...))`, XML-escape `logo_text`, `disable_content_type_detection=True`, fallback без caption.
- Проверка: pytest 49/49, scans 262/262; живой Telegram-тест за пользователем.

## 2026-11-19 — PNG download всё ещё не отдаёт файл

- Симптом: после исправления SVG кнопка «Скачать PNG» всё ещё не работает.
- Гипотеза: PNG не был принудительно помечен как документ, и Telegram пытался обработать его как фото; также файл уходил в `from_user.id`, что ломает группы.
- Исправление: `disable_content_type_detection=True` для PNG, отправка в текущий чат, лог размера файла.
- Проверка: pytest 49/49, ruff OK; Render live `819253b`; живой Telegram-тест ещё не подтверждён.

## 2026-11-19 — LanguageMiddleware не применялся к handlers

- Симптом: при регистрации `dp.message.middleware(LanguageMiddleware())` и `dp.callback_query.middleware(...)` дочерние routers могли обрабатывать update без установленного языка.
- Причина: middleware на корневом `dp.message` выполняется только для handlers самого root observer; при include-router обработка уходит в дочерний router.
- Исправление: `dp.update.outer_middleware(LanguageMiddleware())` после FSM middleware; integration-тест `feed_update` подтверждает `current_lang == "en"`.
- Проверка: pytest 62/62, ruff OK.

## 2026-11-19 — default-команды оставались русскими

- Симптом: default `set_my_commands` вызывал `t()` без контекста, а `ContextVar` по умолчанию `ru`.
- Исправление: default-список оборачивается в `use_lang("en")`, затем отдельный вызов с `language_code="ru"`.
- Проверка: отдельный тест проверяет `Start` для default и `Начать` для `ru`.

## 2026-11-19 — язык терялся при очистке сценария

- Риск: `state.clear()` в handlers удалял бы выбранный `lang`.
- Исправление: единый `clear_flow()` читает `lang`, очищает state и восстанавливает `{"lang": ...}`; picker использует его же.
- Проверка: pytest-тест выбора языка и `clear_flow`.
