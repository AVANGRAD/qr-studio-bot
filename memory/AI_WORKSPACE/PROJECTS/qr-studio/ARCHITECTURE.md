# Architecture

## Слои

- `qrstudio/core.py` — матрица QR, типы модулей, finder/alignment.
- `qrstudio/colors.py` — парсинг цветов, градиенты, контраст, colorize.
- `qrstudio/shapes.py` — рисование модулей и overlay-спрайтов.
- `qrstudio/eyes.py` — угловые маркеры и безопасные overlay.
- `qrstudio/masks.py` — 44 силуэта, категории, центры.
- `qrstudio/presets.py` — палитры и пресеты.
- `qrstudio/logo.py` — подготовка логотипа, монограмма, шрифт.
- `qrstudio/render.py` — сборка PNG/SVG, safe-режимы, плашки, тени.
- `qrstudio/contact_sheet.py` — контактные листы для проверки.

## Бот

- `bot/main.py` — запуск webhook/polling, `/healthz`, self-ping.
- `bot/config.py` — настройки из env.
- `bot/services.py` — Draft, валидация, рендер, rate limit, caption.
- `bot/keyboards.py`, `bot/texts.py`, `bot/states.py` — UI и FSM.
- `bot/handlers/` — start, create, settings, menu, logo, common.
- `bot/errors.py` — глобальный error handler.

## Рендер

1. Нормализация опций и палитры; проверка контраста.
2. Построение QR с учётом логотипа/силуэта (ECC H при риске).
3. Маска силуэта, рамка/плашка, тень.
4. Слой модулей, глаз и alignment; overlay-безопасные стили.
5. Логотип: plate/knockout/texture/background/corner/monogram.
6. Downscale и предупреждения о мелких модулях.
