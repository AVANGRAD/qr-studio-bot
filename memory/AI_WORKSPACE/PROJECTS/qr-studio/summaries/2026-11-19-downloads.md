# 2026-11-19 — скачивание PNG/SVG

## Проблема

Кнопки «Скачать PNG» и «Скачать SVG» в боте не выдавали файл.

## Причина

В SVG-подписи документа `draft.content` вставлялся в HTML без экранирования. Для ссылок с `?a=1&b=2` Telegram отклонял caption (`can't parse entities`), и документ не отправлялся. Дополнительно SVG-мононограмма попадала в XML без экранирования.

## Исправление

- SVG caption теперь использует `html.escape(short(draft.content))`.
- Для SVG включён `disable_content_type_detection=True`.
- Добавлен fallback: при ошибке caption документ повторно отправляется без подписи.
- `logo_text` в SVG экранируется через `html.escape`.
- Добавлены тесты на SVG-caption с `&`, XML-экранирование мононограммы и fallback без caption.

## Проверки

- `pytest`: 49/49.
- `ruff`: без ошибок.
- `node --check webapp/app.js`: OK.
- `scripts/check_scans.py`: 262/262.
- Коммиты `457c137`, `3b1b1d8`; Render live `3b1b1d8`.

## Осталось

- Живая проверка PNG/SVG в Telegram после деплоя.
- Если кнопки всё ещё не отвечают, нужен скриншот/точное время нажатия для проверки webhook-логов.
