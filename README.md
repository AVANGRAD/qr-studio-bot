# QR Studio Bot

Telegram-бот `@QUaRc0De_bot`: превращает ссылку или текст в стилизованный QR-код.

## Возможности

- 44 силуэта: геометрия, природа, животные, символы.
- 18 стилей модулей и 10 стилей «глаз» (угловых маркеров).
- 15 палитр, включая градиенты, металл, дерево и акварель.
- 18 готовых пресетов и случайный стиль.
- Логотип: плашка, вырез, текстура, фон, угол, монограмма.
- PNG до 2048 px с DPI 300 и SVG для печати.
- Проверка контраста и безопасные fallback-стили, чтобы QR оставался читаемым.
- Русский интерфейс, подсказки и предупреждения о рисках сканирования.

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
| `WEBHOOK_SECRET` | hash токена | Секрет заголовка `X-Telegram-Bot-Api-Secret-Token` |
| `SELF_PING_INTERVAL_SECONDS` | `600` | Пинг `/healthz`, чтобы free-сервис не засыпал |
| `ADMIN_ID` | — | Telegram ID администратора |
| `MAX_CONTENT_LENGTH` | `1200` | Максимум символов в QR |
| `MAX_LOGO_BYTES` | `6291456` | Максимум размера логотипа |

Секреты не коммитятся: `.env` и `.secrets/` уже в `.gitignore`.

## Деплой на Render

В репозитории есть `render.yaml` (free web service, Frankfurt, health check `/healthz`).

1. Создай Blueprint или Web Service из репозитория.
2. Укажи `BOT_TOKEN`; `WEBHOOK_SECRET` Render сгенерирует сам.
3. `WEBHOOK_BASE_URL` подхватится из `RENDER_EXTERNAL_URL`.
4. После деплоя открой `https://<service>.onrender.com/healthz`.

Free-план засыпает без трафика. Бот пингует себя раз в 10 минут; первый запуск после сна занимает около минуты.

## Проверки

```bash
ruff check qrstudio bot scripts tests
pytest -q
python scripts/check_scans.py
```

`scripts/check_scans.py` рендерит 140 QR-кодов и декодирует их через jsQR (`tests/js/decode.js`). Нужен Node.js и `npm install` в `tests/js/`.

## Структура

```
qrstudio/   генерация QR, формы, глаза, палитры, рендер PNG/SVG
bot/        aiogram-бот: меню, FSM, лимиты, превью
scripts/    регрессия сканирования
tests/      pytest и jsQR-декодер
assets/     шрифт Roboto и лицензия OFL
memory/     рабочая память проекта
```

## Ограничения

- Максимум 1200 символов и 2048 px.
- Логотип до 6 МБ (жёсткий лимит загрузки — 8 МБ).
- В SVG силуэты и логотип встраиваются как PNG, а модули QR остаются векторными. Это сохраняет точное совпадение с PNG.
- При мелких модулях бот автоматически упрощает слишком детальный узор и предупреждает об этом.
