# Project State

Обновлено: 2026-11-18

## Готово

- Библиотека `qrstudio`: 44 формы, 18 стилей модулей, 10 глаз, 15 палитр, 18 пресетов.
- Рендер PNG/SVG, логотипы, монограммы, safe-fallback, контраст.
- Telegram-бот на aiogram: меню, FSM, превью, PNG/SVG, лимиты.
- Шрифт Roboto с кириллицей и OFL.
- Telegram Mini App: `/app`, каталог, превью, 105 статических плиток, `WebApp.sendData`.
- Mini App доступен кнопкой меню «QR Studio», командой `/app` и кнопкой «Выбрать визуально» в редакторе; для групп скрыт (только private).
- Настройки, выбранные до создания QR, сохраняются как `pending_webapp` и применяются к следующему тексту.
- QR встроен в силуэт: `Draft.silhouette=True`, Mini App thumbnails/preview используют `silhouette` для не-square форм; убрана квадратная светлая плашка, добавлены тинт, рант, тень и декор. 32 из 43 не-square силуэтов рендерятся без плашки; 11 сложных форм безопасно откатываются в frame с предупреждением.
- Статические плитки пересобраны; catalog/thumbnail URL с cache-bust `?v=figure2`, preview отдаётся с `no-store`.
- `pytest`: 32 теста проходят.
- `ruff`: без ошибок; `node --check webapp/app.js` без ошибок.
- `scripts/check_scans.py`: 184/184 QR декодируются, включая все 44 формы в figure-режиме.
- GitHub: https://github.com/AVANGRAD/qr-studio-bot (public), HEAD `70b4d8d`.
- Render: `srv-dbun5pgjo6nc73ajoohg`, https://qr-studio-bot.onrender.com, deploy `70b4d8d` live.
- `/healthz`, `/app`, `/app/catalog.json`, `/app/static/*`, `/app/thumbs/*`, `/app/preview.png` отвечают 200; live preview с leaf декодируется jsQR.
- Webhook: pending 0, `last_error_message` пустой; бот `@QUaRc0De_bot` id `9062123985`; menu button «QR Studio» ведёт на `/app`.

## Осталось

- Проверить живым сообщением в Telegram: `/start` → редактор → «Выбрать визуально» → применить настройки и убедиться, что QR в фигуре выглядит ожидаемо.
- Решить, нужен ли пользователю UI-переключатель «в фигуре / с плашкой»; сейчас figure-режим включён по умолчанию.
- При необходимости добавить скриншоты/примеры Mini App в README.

## Известные ограничения

- SVG: силуэты и логотип — встроенный PNG, модули QR — вектор.
- Лимит 1200 символов и 2048 px.
- Free Render засыпает; self-ping 600 с; первый запуск после сна около минуты.
- Mini App требует HTTPS и открывается внутри Telegram.
- Статические плитки нужно пересобирать после изменения каталога: `python scripts/build_miniapp_thumbs.py`.
- 11 сложных силуэтов (`moon`, `snowflake`, `wave`, `fox`, `ladybug`, `turtle`, `penguin`, `mask`, `rocket`, `guitar`, `pumpkin`) используют безопасную плашку: центральный квадрат QR задевает вырезы/края. Это осознанный fallback, не ошибка рендера.
