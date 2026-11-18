# QR Studio Bot

Telegram-бот `@QUaRc0De_bot`: превращает ссылку или текст в стилизованный QR-код.

Демо: https://qr-studio-bot.onrender.com/healthz

## Возможности

- 44 силуэта: геометрия, природа, животные, символы.
- 18 стилей модулей и 10 стилей «глаз» (угловых маркеров).
- 15 палитр, включая градиенты, металл, дерево и акварель.
- 18 готовых пресетов и случайный стиль.
- Логотип: плашка, вырез, текстура, фон, угол, монограмма.
- QR вписывается в силуэт: без квадратной плашки, с лёгким тинтом и рантом; для сложных форм используется безопасная рамка.
- PNG до 2048 px с DPI 300 и SVG для печати.
- Проверка контраста и безопасные fallback-стили, чтобы QR оставался читаемым.
- Русский интерфейс, подсказки и предупреждения о рисках сканирования.
- Визуальный редактор в Telegram Mini App: превью и плитки вариантов вместо текстовых списков.

## Стек

- Python 3.13+ (проверено на 3.14)
- aiogram 3.32
- segno 1.6.6
- Pillow 13
- aiohttp

## Локальный запуск

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# впиши BOT_TOKEN
BOT_MODE=polling python -m bot.main
```

Для polling токен можно получить у [@BotFather](https://t.me/BotFather).

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BOT_TOKEN` | — | Токен Telegram-бота, обязателен |
| `BOT_MODE` | `webhook` | `webhook` или `polling` |
| `WEBHOOK_BASE_URL` | `RENDER_EXTERNAL_URL` | Публичный HTTPS-адрес сервиса |
| `WEBHOOK_SECRET` | hash токена | Hex-секрет заголовка `X-Telegram-Bot-Api-Secret-Token`; можно не задавать |
| `SELF_PING_INTERVAL_SECONDS` | `600` | Пинг `/healthz`, чтобы free-сервис не засыпал |
| `ADMIN_ID` | — | Telegram ID администратора |
| `MAX_CONTENT_LENGTH` | `1200` | Максимум символов в QR |
| `MAX_LOGO_BYTES` | `6291456` | Максимум размера логотипа |

Секреты не коммитятся: `.env` и `.secrets/` уже в `.gitignore`.

## Деплой на Render

В репозитории есть `render.yaml` (free web service, Frankfurt, health check `/healthz`).

1. Создай Blueprint или Web Service из репозитория.
2. Укажи `BOT_TOKEN`; `WEBHOOK_SECRET` можно не задавать — он будет вычислен из токена. Если задаёшь вручную, используй только hex (без спецсимволов), иначе Telegram отклонит webhook.
3. `WEBHOOK_BASE_URL` подхватится из `RENDER_EXTERNAL_URL`.
4. После деплоя открой `https://<service>.onrender.com/healthz` и `/app`.

Free-план засыпает без трафика. Бот пингует себя раз в 10 минут; первый запуск после сна занимает около минуты.

## Визуальный редактор (Mini App)

Mini App открывается кнопкой меню «QR Studio» рядом с полем ввода, командой `/app` или кнопкой «Выбрать визуально» в редакторе. Превью и плитки формируются на том же aiohttp-сервере; выбор отправляется в бота через `WebApp.sendData`. Если настройки выбраны до создания QR, бот сохранит их и применит к следующему тексту.

Статические плитки лежат в `webapp/thumbs/`. После изменения форм или стилей пересобери их:

```bash
python scripts/build_miniapp_thumbs.py
```

Mini App работает в webhook-режиме; в polling-режиме кнопка ведёт на публичный Render-адрес. Статика и шаблоны находятся в `webapp/`.

## Проверки

```bash
ruff check qrstudio bot scripts tests
pytest -q
python scripts/check_scans.py
```

`scripts/check_scans.py` рендерит 184 QR-кода (включая все 44 формы в режиме силуэта) и декодирует их через jsQR (`tests/js/decode.js`). Нужен Node.js и `npm install` в `tests/js/`.

## Структура

```
qrstudio/   генерация QR, формы, глаза, палитры, рендер PNG/SVG
bot/        aiogram-бот: меню, FSM, лимиты, превью
scripts/    регрессия сканирования и сборка плиток Mini App
webapp/     HTML/CSS/JS Mini App и статические плитки
assets/     шрифт Roboto и лицензия OFL
memory/     рабочая память проекта
```

## Ограничения

- Максимум 1200 символов и 2048 px.
- Логотип до 6 МБ (жёсткий лимит загрузки — 8 МБ).
- В SVG силуэты и логотип встраиваются как PNG, а модули QR остаются векторными. Это сохраняет точное совпадение с PNG.
- Mini App требует HTTPS. В локальном polling-режиме кнопка использует публичный адрес сервиса, а не localhost.
- При мелких модулях бот автоматически упрощает слишком детальный узор и предупреждает об этом.
