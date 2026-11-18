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

- `bot/main.py` — запуск webhook/polling, `/healthz`, self-ping.
- `bot/config.py` — настройки из env.
- `bot/services.py` — Draft, валидация, рендер, rate limit, caption.
- `bot/keyboards.py`, `bot/texts.py`, `bot/states.py` — UI и FSM.
- `bot/handlers/` — start, create, settings, menu, logo, photo, common; меню готовых иконок и режим «Медальон».
- `bot/errors.py` — глобальный error handler.

## Рендер

1. Нормализация опций и палитры; проверка контраста.
2. Построение QR с учётом логотипа/силуэта (ECC H при риске).
3. Маска силуэта, рамка/плашка, figure-режим или фото-режим: QR внутри силуэта/на карточке, тинт/рант/тень, безопасный fallback в рамку для 15 из 51 формы.
4. Фото-режим: полное фото + размытый cover-фон, светлая карточка QR справа снизу; shape/silhouette/frame отключаются.
5. Слой модулей, глаз и alignment; overlay-безопасные стили.
6. Логотип: plate/badge/knockout/texture/background/corner/monogram; встроенная иконка хранится как PNG, название — в `Draft.logo_label`.
7. Downscale и предупреждения о мелких модулях.
