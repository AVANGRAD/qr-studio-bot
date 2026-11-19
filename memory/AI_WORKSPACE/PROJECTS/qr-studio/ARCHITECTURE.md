# Architecture

## Слои

- `qrstudio/core.py` — матрица QR, типы модулей, finder/alignment.
- `qrstudio/colors.py` — парсинг цветов, градиенты, контраст, colorize.
- `qrstudio/shapes.py` — 24 стиля модулей и overlay-спрайты.
- `qrstudio/eyes.py` — угловые маркеры и безопасные overlay.
- `qrstudio/masks.py` — 52 силуэта, категории, центры.
- `qrstudio/presets.py` — 19 палитр и 25 пресетов.
- `qrstudio/logo.py` — подготовка логотипа, монограмма, шрифт.
- `qrstudio/emblems.py` — 12 встроенных нейтральных иконок для центра QR.
- `qrstudio/render.py` — сборка PNG/SVG, safe-режимы, плашки, тени.
- `qrstudio/contact_sheet.py` — контактные листы для проверки.

## Бот

- `bot/main.py` — запуск webhook/polling, `/healthz`, self-ping, `LanguageMiddleware`, команды default English + `ru` scope.
- `bot/config.py` — настройки из env.
- `bot/i18n.py` — словари `ru/en`, `t()`, `resolve_lang()`, `LanguageMiddleware`, локализованные названия каталога и warning-коды.
- `bot/services.py` — Draft, валидация, рендер, rate limit, caption, language-aware URL.
- `bot/keyboards.py`, `bot/states.py` — UI и FSM; все подписи через `t()`.
- `bot/handlers/` — start (picker/`/language`), create, settings, menu, logo, photo, webapp, common; меню готовых иконок и режим «Медальон».
- `bot/errors.py` — глобальный error handler с языком из FSM/Telegram.

## Рендер

1. Нормализация опций и палитры; проверка контраста.
2. Построение QR с учётом логотипа/силуэта (ECC H при риске).
3. Маска силуэта, рамка/плашка, figure-режим или фото-режим: QR внутри силуэта/на карточке, тинт/рант/тень, безопасный fallback в рамку для 15 из 51 формы.
4. Фото-режим: полное фото + размытый cover-фон, светлая карточка QR справа снизу; shape/silhouette/frame отключаются.
5. Слой модулей, глаз и alignment; overlay-безопасные стили.
6. Логотип: plate/badge/knockout/texture/background/corner/monogram; встроенная иконка хранится как PNG, ключ — в `Draft.logo_emblem`.
7. Downscale и предупреждения о мелких модулях; `RenderResult.warning_codes` хранит код+параметры для локализации.

## Язык

- `LanguageMiddleware` на `dp.update.outer_middleware` читает FSM `lang`, затем `event_from_user.language_code`; выставляет `ContextVar current_lang`.
- Первый `/start` без `lang` показывает picker; `/language` доступен в любой момент; `clear_flow()` сохраняет `lang`.
- Mini App выбирает язык URL → Telegram → browser; серверный каталог и Apply используют `lang`/synthetic `User.language_code`.
