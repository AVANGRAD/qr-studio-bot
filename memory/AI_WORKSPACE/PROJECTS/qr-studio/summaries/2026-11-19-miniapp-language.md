# Итог: переключение языка в Mini App

## Запрос

Mini App должен менять язык вместе с ботом и позволять переключить его внутри редактора.

## Сделано

- В `webapp/index.html`/`app.js` добавлен RU/EN toggle; строки, вкладки и названия каталога обновляются без перезагрузки.
- Язык выбирается в порядке URL `?lang=` → `localStorage` → Telegram `language_code` → `navigator.language`.
- Выбор сохраняется в `localStorage`; Apply отправляет `lang` вместе с настройками.
- `on_web_app_data` сохраняет `lang` в FSM, применяет `use_lang()` к ответам/preview и обновляет per-chat menu button.
- `set_menu_button()` вынесен в `bot/services.py`; `/start`, `/language` и Apply обновляют `MenuButtonWebApp` с `?lang=`.
- Глобальная menu button без `lang` оставлена fallback.

## Проверки

- `pytest`: 64/64.
- `ruff`: OK.
- `node --check webapp/app.js`: OK.
- `scripts/check_scans.py`: 262/262.
- Headless Chromium: EN→RU toggle, каталог `Квадрат`, кнопка `EN`, Apply payload `lang=ru`.

## Осталось

- Commit/push/deploy.
- Живая проверка toggle и per-chat menu button в Telegram.
