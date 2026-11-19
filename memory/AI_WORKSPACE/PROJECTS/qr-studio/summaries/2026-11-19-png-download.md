# 2026-11-19 — PNG download

## Сделано

- PNG-документ теперь отправляется с `disable_content_type_detection=True`, чтобы Telegram не обрабатывал его как фото.
- Отправка идёт в `callback.message.chat.id` с fallback на `callback.from_user.id`; это также покрывает группы.
- В лог добавлен размер PNG для диагностики.
- Тест PNG проверяет `disable_content_type_detection` и chat id.

## Проверки

- `pytest`: 49/49.
- `ruff`: OK.
- Коммит `819253b`, Render deploy live `819253b`, `/healthz` 200.

## Открыто

- Живая проверка кнопки PNG в Telegram за пользователем.
- Точная причина не подтверждена логами; если PNG снова не придёт, нужен скриншот/время нажатия.
