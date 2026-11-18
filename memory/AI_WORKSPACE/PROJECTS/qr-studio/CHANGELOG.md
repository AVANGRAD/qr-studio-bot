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
