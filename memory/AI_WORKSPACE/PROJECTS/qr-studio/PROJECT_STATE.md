# Project State

Обновлено: 2026-11-18

## Готово

- Библиотека `qrstudio`: 44 формы, 18 стилей модулей, 10 глаз, 15 палитр, 18 пресетов.
- Рендер PNG/SVG, логотипы, монограммы, safe-fallback, контраст.
- Telegram-бот на aiogram: меню, FSM, превью, PNG/SVG, лимиты.
- Шрифт Roboto с кириллицей и OFL.
- `pytest`: 23 теста проходят.
- `ruff`: без ошибок.
- `scripts/check_scans.py`: 140/140 QR декодируются.
- Polling-запуск проверен: бот подключается к Telegram.
- GitHub: https://github.com/AVANGRAD/qr-studio-bot (public).
- Render: `srv-dbun5pgjo6nc73ajoohg`, https://qr-studio-bot.onrender.com, деплой live.
- `/healthz` отвечает 200; webhook установлен, ошибок Telegram нет.

## Осталось

- Проверить сценарий живым сообщением в Telegram.
- Добавить скриншоты/примеры в README при необходимости.

## Известные ограничения

- SVG: силуэты и логотип — встроенный PNG, модули QR — вектор.
- Лимит 1200 символов и 2048 px.
- Free Render засыпает; self-ping 600 с.
