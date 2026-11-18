# Project State

Обновлено: 2026-11-18

## Готово

- Библиотека `qrstudio`: 44 формы, 18 стилей модулей, 10 глаз, 15 палитр, 18 пресетов.
- Рендер PNG/SVG, логотипы, монограммы, safe-fallback, контраст.
- Telegram-бот на aiogram: меню, FSM, превью, PNG/SVG, лимиты.
- Шрифт Roboto с кириллицей и OFL.
- Telegram Mini App: `/app`, каталог, превью, 105 статических плиток, `WebApp.sendData`.
- Кнопка «Выбрать визуально» в редакторе; для групп скрыта (только private).
- `pytest`: 29 тестов проходят.
- `ruff`: без ошибок; `node --check webapp/app.js` без ошибок.
- `scripts/check_scans.py`: 140/140 QR декодируются после правки листа и плашек.
- GitHub: https://github.com/AVANGRAD/qr-studio-bot (public), HEAD `9199253`.
- Render: `srv-dbun5pgjo6nc73ajoohg`, https://qr-studio-bot.onrender.com, deploy live.
- `/healthz`, `/app`, `/app/catalog.json`, `/app/static/*`, `/app/thumbs/*`, `/app/preview.png` отвечают 200.
- Webhook: pending 0, `last_error_message` пустой; бот `@QUaRc0De_bot` id `9062123985`.

## Осталось

- Проверить живым сообщением в Telegram: `/start` → редактор → «Выбрать визуально» → применить настройки.
- При необходимости добавить скриншоты/примеры Mini App в README.

## Известные ограничения

- SVG: силуэты и логотип — встроенный PNG, модули QR — вектор.
- Лимит 1200 символов и 2048 px.
- Free Render засыпает; self-ping 600 с; первый запуск после сна около минуты.
- Mini App требует HTTPS и открывается внутри Telegram.
- Статические плитки нужно пересобирать после изменения каталога: `python scripts/build_miniapp_thumbs.py`.
