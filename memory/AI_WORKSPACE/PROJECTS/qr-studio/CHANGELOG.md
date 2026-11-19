## 2026-11-19 — аналитика пользователей

- Добавлен `bot/analytics.py`: пул `asyncpg`, создание схемы `analytics`, upsert пользователей и запись событий.
- `analytics.users` хранит `first_seen`, `last_seen`, `updates_count`, `starts_count`, `last_event`, `blocked_at`; `analytics.events` — тип события, время и безопасные метаданные.
- `AnalyticsMiddleware` на `dp.update.outer_middleware` пишет активность; `/stats` доступен только при `ADMIN_ID` и показывает всего/новых/активных/неактивных/заблокировавших, языки и топ событий.
- `asyncpg==0.32.0` добавлен в requirements; `DATABASE_URL` добавлен в `.env.example` и `render.yaml`.
- Подключение к новому Supabase PostgreSQL 17.12 проверено; таблицы созданы, тестовые записи удалены.
- `DATABASE_URL` добавлен в Render Environment без изменения остальных переменных.
- Проверки: pytest 70/70, ruff OK.
- `ADMIN_ID` найден через `getChat` и задан локально/в Render; commit `afe6edf`, Render deploy `dep-dbvf7jjm8hqs73b2r28g` live.
- Live: `analytics database connected`; synthetic `/stats` от ADMIN_ID прошёл 200 и записал пользователя/событие; ошибок нет.

# Changelog

## 2026-11-18

- Добавлены `qrstudio/render.py`, `logo.py`, `contact_sheet.py`.
- Добавлены 44 формы, 18 модулей, 10 глаз, 15 палитр, 18 пресетов.
- Добавлен Telegram-бот и FSM-сценарии.
- Добавлены pytest-тесты и jsQR-регрессия.
- Исправлены SVG, `colorize_mask`, safe-стили и монограммы.
- Локальные проверки: ruff OK, pytest 23/23, scans 140/140.
- Опубликован GitHub-репозиторий и Render web service; webhook установлен.

## 2026-11-18 — визуальный Mini App

- Добавлен `bot/miniapp.py`: каталог, превью, плитки, `setup(app)`.
- Добавлены `webapp/index.html`, `app.js`, `style.css` и 105 статических PNG-плиток.
- В редактор добавлена кнопка `Выбрать визуально` (`WebAppInfo`), только private.
- Добавлен handler `web_app_data` с валидацией формы/стиля/глаз/палитры/размера.
- SVG и лист: silhouette leaf переделан, лимиты плашек уменьшены.
- `pytest` 29/29, `ruff` OK, `node --check` OK, scans 140/140.
- Render deploy live: `9199253`; HTTP-эндпоинты Mini App проверены.

## 2026-11-18 — доступ к Mini App

- Установлена кнопка меню «QR Studio» (`MenuButtonWebApp`) при старте webhook-сервера.
- Добавлена команда `/app` с inline-кнопкой открытия редактора.
- Настройки из Mini App до создания QR сохраняются в `pending_webapp` и применяются к следующему тексту.
- `pytest` 30/30; Render deploy `f40c4e9`.

## 2026-11-18 — QR внутри силуэта

- Добавлен figure-режим: QR вписывается в безопасный квадрат внутри формы, без квадратной плашки.
- `Draft.silhouette=True`; Mini App thumbnails/preview и shape/preset-плитки используют figure-режим.
- Добавлены тинт силуэта, внутренний рант, тень и декор; SVG получил те же правила.
- 11 сложных форм безопасно откатываются в frame с предупреждением.
- 105 плиток пересобраны; добавлен cache-bust `?v=figure2`, preview — `no-store`.
- `pytest` 32/32, `ruff` OK, `node --check` OK, scans 184/184.
- Render deploy `70b4d8d` live; live leaf preview декодируется jsQR.

## 2026-11-18 — фото-режим

- `RenderOptions` получил `photo`, `photo_card`, `photo_inset`, `photo_opacity`; `RenderResult.photo`.
- Добавлен `_photo_canvas`: полное фото + размытый затемнённый cover-фон; QR на светлой скруглённой карточке справа снизу.
- PNG/SVG фото-режим; фото в SVG встраивается PNG, модули остаются векторными.
- `Draft.photo_bytes`, `prepare_uploaded_photo` (12 МБ, EXIF, 1600 px), `Flow.photo`, `bot/handlers/photo.py`.
- Кнопки «Фото + QR» на старте и «Фото» в редакторе; фото можно загрузить до текста, удалить и заменить.
- `pytest` 38/38, `ruff` OK, scans 187/187; feature-коммит `c5dfbe5`.
- Feature deploy `c5dfbe5` live; docs-коммит `b78954e`; `/healthz`, `/app`, catalog и preview 200; webhook pending 0.

## 2026-11-19 — PNG/SVG download fix

- Причина: SVG-caption содержал `draft.content` без HTML-экранирования; ссылки с `&` ломали caption, документ не отправлялся.
- SVG-caption переведён на `html.escape(short(...))`; добавлен `disable_content_type_detection=True`.
- `logo_text` в SVG экранируется как XML.
- При ошибке caption документ повторно отправляется без подписи.
- Проверки: pytest 49/49, ruff OK, scans 262/262.
- Коммиты `457c137`, `3b1b1d8`; Render live `3b1b1d8`.

## 2026-11-19 — Apply в Mini App

- Причина бага: `WebApp.sendData` не работает для Mini App, открытых из menu/inline.
- Добавлен `POST /app/apply`: проверка HMAC `initData` и `auth_date`, synthetic `web_app_data`, `Dispatcher.feed_update`.
- `webapp/app.js` отправляет `initData` на сервер; `sendData` оставлен fallback для keyboard-кнопок.
- Preview теперь отправляется и при повторном применении тех же настроек.
- `app.js?v=apply1` для сброса кэша Telegram WebView.
- Проверки: pytest 46/46, ruff OK, `node --check` OK, scans 262/262.
- Коммиты `6c35f98`, `ed3639e`; Render live; `/app/apply` 400 без initData, live JS содержит endpoint; webhook pending 0.

## 2026-11-18 — расширение каталога и встроенные логотипы

- Формы: +8 (`squircle`, `burst`, `clover`, `cactus`, `frog`, `whale`, `anchor`, `music_note`), всего 52.
- Модули: +6 (`flower`, `chevron`, `arch`, `spark`, `plus`, `brick`), всего 24; `brick` — 2 варианта.
- Глаза: +4 (`capsule`, `octagon`, `spark`, `heart`), всего 14; `capsule`/`octagon`/`spark` рендерятся безопасными фигурами, `heart` — через safe-base overlay.
- Палитры: +4 (`berry`, `ocean`, `sunset`, `midnight`), всего 19; пресеты: +7, всего 25.
- Логотипы: режим `badge` («Медальон») в PNG/SVG и меню; `qrstudio/emblems.py` с 12 нейтральными иконками; `Draft.logo_label` и подписи.
- `flower` переведён на безопасную базу `dot` + overlay после scan-провала.
- Mini App: 134 плитки, cache-bust `?v=variety1`; тесты каталога обновлены.
- Проверки: pytest 42/42, ruff OK, `node --check` OK, scans 262/262.
- Feature-коммит `0e01ca3`, docs `e12f6f5`; Render deploy live; `/healthz`, `/app`, catalog 200; live-каталог 52/24/14/19/25; webhook pending 0.

## 2026-11-19 — локализация RU/EN и выбор языка

- Добавлен `bot/i18n.py`: словари `ru/en`, `t()`, `resolve_lang()`, `LanguageMiddleware`, локализованные названия каталога и warning-коды.
- Первый `/start` без сохранённого языка показывает RU/EN picker; `/language` меняет язык; `clear_flow()` сохраняет выбор.
- Локализованы handlers, клавиатуры, ошибки, rate-limit, caption PNG/SVG, сервисные сообщения, каталог и Mini App.
- `Draft.logo_emblem` отделяет ключ встроенной иконки от старого русского `logo_label`; `RenderResult.warning_codes` локализует предупреждения.
- Mini App: `?lang=`, `/app/catalog.json?lang=`, Apply с synthetic `User.language_code`; JS выбирает URL → Telegram → browser.
- `LanguageMiddleware` зарегистрирован на `dp.update.outer_middleware`, иначе дочерние routers обходили middleware.
- Telegram-команды: default English + `ru` scope; исправлен захват ContextVar.
- Удалён устаревший `bot/texts.py`; добавлен `tests/test_i18n.py`.
- Проверки: pytest 62/62, ruff OK, `node --check webapp/app.js` OK, scans 262/262.
- Коммит `3f1062f`, docs `1d108fd`; Render live `3f1062f` (`dep-dbvcimjrjlhs73ed143g`), docs redeploy `1d108fd` (`dep-dbvck6p7lnhs739caeu0`); `/healthz`, `/app`, EN/RU catalog и preview 200, Apply без initData 400, команды EN/RU, webhook pending 0.

## 2026-11-19 — переключение языка в Mini App

- В шапку Mini App добавлен RU/EN toggle; интерфейс и каталог перерисовываются без перезагрузки.
- `app.js` выбирает язык URL → `localStorage` → Telegram → browser, сохраняет выбор и отправляет `lang` в Apply.
- `on_web_app_data` сохраняет `lang` в FSM, применяет его к preview/ответам и обновляет per-chat menu button.
- `set_menu_button()` вынесен в `bot/services.py`; `/start`, `/language` и Apply обновляют `MenuButtonWebApp?lang=`.
- Добавлены тесты языка из payload и per-chat menu button; проверки: pytest 64/64, ruff OK, `node --check` OK, scans 262/262.
- Headless Chromium: EN→RU toggle, каталог `Квадрат`, Apply payload `lang=ru`.
- Коммит `9654ddf`; Render deploy `dep-dbvdvip42hec73bceqng` live; live HTML/JS `i18n2`, каталог EN/RU, Apply без initData 400, webhook pending 0.

## 2026-11-19 — PNG download принудительно документом

- PNG теперь отправляется с `disable_content_type_detection=True`, чтобы Telegram не обрабатывал файл как фото.
- Документ отправляется в текущий чат (`callback.message.chat.id`) с fallback на `from_user.id`; это исправляет сценарий группы.
- Добавлена запись размера PNG в лог для диагностики.
- Проверки: pytest 49/49, ruff OK.
- Коммит `819253b`; Render live `819253b`; живой тест PNG за пользователем.
