# Tasks

## Выполнено

- [x] Библиотека QR и 52 формы.
- [x] 24 модуля, 14 глаз, 19 палитр, 25 пресетов.
- [x] 7 режимов логотипа, включая «Медальон».
- [x] 12 встроенных нейтральных иконок и меню с пагинацией.
- [x] Логотипы и монограммы.
- [x] PNG/SVG рендер.
- [x] Safe-fallback для сканируемости.
- [x] Telegram-бот и меню.
- [x] Telegram Mini App: каталог, превью, плитки, `sendData` + серверный Apply, handler.
- [x] Кнопка Mini App только для private-чатов.
- [x] Кнопка меню «QR Studio» и команда `/app`.
- [x] Сохранение выбранных настроек до создания QR.
- [x] QR встроен в силуэт без квадратной плашки; 36/51 не-square форм.
- [x] Пересобраны 134 плитки Mini App; cache-bust `?v=variety1`.
- [x] GitHub-репозиторий и Render web service.
- [x] 62 pytest-теста и 262/262 scan-регрессия, включая figure, пресеты, иконки и фото.
- [x] Фото-режим PNG/SVG: карточка QR поверх фото, размытый фон, EXIF-поворот, лимит 12 МБ.
- [x] Бот: `Flow.photo`, загрузка фото до/после текста, preview, удаление, кнопки «Фото + QR»/«Фото».
- [x] Проверить diff, закоммитить, запушить и задеплоить расширение (`0e01ca3`, docs `e12f6f5`).
- [x] Apply fix: подписанный `POST /app/apply`, HMAC initData, synthetic `web_app_data`, cache-bust `?v=apply1` (`6c35f98`, `ed3639e`).
- [x] Download fix: HTML-экранирование SVG-caption, XML-escape мононограммы, fallback без caption (`457c137`, `3b1b1d8`).
- [x] PNG download: принудительная отправка документом, текущий чат, лог размера (`819253b`).
- [x] Локализация `ru/en`: `bot/i18n.py`, middleware, handlers, keyboards, errors, services, warnings, Mini App и каталог.
- [x] Выбор языка при первом `/start`, `/language`, `clear_flow` сохраняет `lang`.
- [x] Default English + `ru` scope для Telegram-команд; synthetic `User.language_code` для Apply.
- [x] Проверки локализации: pytest 62/62, ruff OK, `node --check` OK, scans 262/262.
- [x] Закоммитить и задеплоить локализацию (`3f1062f`, docs `1d108fd`; deploy `dep-dbvcimjrjlhs73ed143g`, docs redeploy `dep-dbvck6p7lnhs739caeu0`).
- [ ] Живая проверка picker/`/language`/EN/Mini App.
- [ ] Живая проверка Apply в Telegram: menu/inline и keyboard.
- [ ] Живая проверка PNG после `disable_content_type_detection` (`819253b`); SVG подтверждён пользователем.
- [ ] Живая проверка Telegram: фото, фото + логотип, фото-первый сценарий, иконки и «Медальон».

## Идеи

- [ ] UI-тумблер монохромного логотипа.
- [ ] UI-переключатель «QR в фигуре / с плашкой».
- [ ] Выбор позиции/размера фото-карточки (сейчас правый нижний угол, 42%).
- [ ] Кнопка сброса настроек в редакторе.
- [ ] Примеры QR и скриншоты Mini App/фото-режима в README.
- [ ] Уточнить «QR на QR»: логотип поверх QR или буквальное наложение.
- [ ] Добавить постоянный storage, чтобы выбранный язык переживал рестарт Render.
- [ ] Синхронизировать Telegram-команды и menu button с выбором языка (сейчас default/Telegram).
