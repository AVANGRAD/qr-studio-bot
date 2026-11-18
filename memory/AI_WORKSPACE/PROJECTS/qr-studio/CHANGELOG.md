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
