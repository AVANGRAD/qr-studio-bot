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

- `bot/main.py` — запуск webhook/polling, `/healthz`, self-ping, `LanguageMiddleware`, `AnalyticsMiddleware`, команды default English + `ru` scope.
- `bot/config.py` — настройки из env.
- `bot/i18n.py` — словари `ru/en`, `t()`, `resolve_lang()`, `LanguageMiddleware`, локализованные названия каталога и warning-коды.
- `bot/services.py` — Draft, валидация, рендер, rate limit, caption, language-aware URL, `set_menu_button()` для per-chat `?lang=`.
- `bot/keyboards.py`, `bot/states.py` — UI и FSM; все подписи через `t()`.
- `bot/handlers/` — start (picker/`/language`), create, settings, menu, logo, photo, webapp, common, admin (`/stats`); меню готовых иконок и режим «Медальон».
- `bot/analytics.py` — пул PostgreSQL, схема `analytics`, запись update-событий и расчёт статистики.
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
- Mini App выбирает язык URL → `localStorage` → Telegram → browser; серверный каталог и Apply используют `lang`/synthetic `User.language_code`.
- В Mini App есть переключатель RU/EN; Apply отправляет `lang`, handler сохраняет его в FSM и обновляет per-chat menu button. `/start` и `/language` также обновляют кнопку.

## Аналитика

- `Analytics.connect()` создаёт пул `asyncpg` и схему `analytics`; при ошибке бот продолжает работать без аналитики.
- `AnalyticsMiddleware` получает `event_from_user`, классифицирует update и асинхронно пишет пользователя и событие; ошибки записи логируются.
- `analytics.users` — текущее состояние (`first_seen`, `last_seen`, `updates_count`, `starts_count`, `blocked_at`); `analytics.events` — история для DAU/WAU/MAU и топ-событий.
- `/stats` проверяет `admin_id`, читает агрегаты и форматирует их через `t()`; без `DATABASE_URL` отвечает, что аналитика недоступна.
