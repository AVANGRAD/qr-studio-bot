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
- [x] 64 pytest-теста и 262/262 scan-регрессия, включая figure, пресеты, иконки и фото.
- [x] Фото-режим PNG/SVG: карточка QR поверх фото, размытый фон, EXIF-поворот, лимит 12 МБ.
- [x] Бот: `Flow.photo`, загрузка фото до/после текста, preview, удаление, кнопки «Фото + QR»/«Фото».
- [x] Проверить diff, закоммитить, запушить и задеплоить расширение (`0e01ca3`, docs `e12f6f5`).
- [x] Apply fix: подписанный `POST /app/apply`, HMAC initData, synthetic `web_app_data`, cache-bust `?v=apply1` (`6c35f98`, `ed3639e`).
- [x] Download fix: HTML-экранирование SVG-caption, XML-escape мононограммы, fallback без caption (`457c137`, `3b1b1d8`).
- [x] PNG download: принудительная отправка документом, текущий чат, лог размера (`819253b`).
- [x] Локализация `ru/en`: `bot/i18n.py`, middleware, handlers, keyboards, errors, services, warnings, Mini App и каталог.
- [x] Выбор языка при первом `/start`, `/language`, `clear_flow` сохраняет `lang`.
- [x] Default English + `ru` scope для Telegram-команд; synthetic `User.language_code` для Apply.
- [x] Проверки локализации: pytest 64/64, ruff OK, `node --check` OK, scans 262/262.
- [x] Mini App RU/EN toggle с перерисовкой интерфейса/каталога и сохранением в `localStorage`.
- [x] Apply передаёт `lang`; `on_web_app_data` обновляет FSM и per-chat menu button.
- [x] Per-chat `MenuButtonWebApp?lang=` после `/start`, `/language` и Apply; global fallback.
- [x] Headless Chromium smoke: toggle EN→RU, каталог `Квадрат`, Apply payload `lang=ru`.
- [x] Commit/push/deploy Mini App language switching (`9654ddf`, deploy `dep-dbvdvip42hec73bceqng`).
- [x] Закоммитить и задеплоить локализацию (`3f1062f`, docs `1d108fd`; deploy `dep-dbvcimjrjlhs73ed143g`, docs redeploy `dep-dbvck6p7lnhs739caeu0`).
- [x] Аналитика: `analytics.users`/`analytics.events`, `asyncpg`, middleware на каждом update.
- [x] `/stats` для админа: новые, активные, неактивные, заблокированные, языки и топ событий.
- [x] Проверено подключение к Supabase PostgreSQL 17.12; тестовые записи созданы и удалены.
- [x] `DATABASE_URL` добавлен в `.env`, Render Environment, `.env.example`, `render.yaml`; `asyncpg` — в requirements.
- [x] Проверки: pytest 70/70, ruff OK.
- [x] `/stats`: добавлены всего событий и топ событий за всё время.
- [x] Support-бот: отдельный токен, `/support` в основном боте, пересылка тикетов админу, reply обратно пользователю, `support.tickets`.
- [x] Support-тесты и UI-команда `/support`; pytest 74/74, ruff OK.
- [x] `SUPPORT_BOT_TOKEN` добавлен в `.env`, `.env.example`, `render.yaml`, Render Environment; таблица `support.tickets` проверена; `SUPPORT_WEBHOOK_SECRET` ротирован 19.11.
- [x] Получить Telegram ID администратора и задать `ADMIN_ID` локально и в Render.
- [x] Закоммитить и задеплоить аналитику (`afe6edf`, deploy `dep-dbvf7jjm8hqs73b2r28g`).
- [x] Live-проверка `/stats` через synthetic webhook: 200, запись в `analytics.users`/`analytics.events`, ошибок нет.
- [x] Задеплоить support/all-time (`f1f8f32`, deploy `dep-dbvfl1mq1p3s738ero7g`); live `/healthz` `support:true`, оба webhook pending 0, support route 200, `/stats` synthetic 200.
- [x] Администратор доступен в `@QUaRc0DeSupport_bot` (`getChat` 200).
- [ ] Проверить live-тикет вторым пользователем.
- [ ] При необходимости добавить рассылку с обработкой 403 для `blocked_at`.
- [ ] Живая проверка picker/`/language`/EN/Mini App.
- [ ] Живая проверка Apply в Telegram: menu/inline и keyboard.
- [ ] Живая проверка PNG после `disable_content_type_detection` (`819253b`); SVG подтверждён пользователем.
- [ ] Живая проверка Telegram: фото, фото + логотип, фото-первый сценарий, иконки и «Медальон».

## Безопасность (19.11.2026)

- [x] Webhook path отделён от header-секрета; лог маскирован; тест `test_security.py`.
- [x] Ротированы `WEBHOOK_SECRET` и `SUPPORT_WEBHOOK_SECRET`; старые пути больше не работают.
- [x] Создана least-privilege роль `qr_app` без CREATEDB/CREATEROLE; права только на `analytics`/`support`.
- [x] Убран runtime DDL из приложения; добавлен `scripts/migrate.py` и инструкция в README.
- [x] TLS к Supabase проверяет CA и hostname (`certs/prod-ca-2021.crt`, `bot/db.py`).
- [x] Support rate limit 5/мин, 30/час, 100/день; privacy-тексты обновлены.
- [x] Mini App: apply rate limit, preview rate limit + render semaphore/timeout, content-type, future auth_date.
- [x] `/stats` только в private-чате.
- [x] Проверки: pytest 81/81, ruff OK; live `/healthz`/`/app` 200, webhook 200 с секретом и 401 без, pending 0.
- [x] Коммит `e6b592b`, deploy `dep-dbvhh1ek1f9s73cj5vt0` live с ролью `qr_app`.
- [ ] Владелец: при желании включить 2FA/secret scanning/push protection в GitHub, Render, Supabase и Telegram.
- [ ] Владелец: проверить, что администратор нажал `/start` в support-боте, и пройти live-тикет.
- [ ] При необходимости вынести rate-limit счётчики в Redis/БД (сейчас in-memory, сбрасываются рестартом).

## Продвижение (19.11.2026)

- [x] Аудит профиля: `getMyDescription`/`getMyShortDescription` пустые, `getUserProfilePhotos` 0.
- [x] Заданы описания через Bot API: short 82 симв., description 403 симв.
- [x] Сгенерированы `assets/promo/avatar.png` (1024) и `avatar-512.png`.
- [x] Создан `documentation/PROMOTION.md`: позиционирование, каталоги, тексты, статусы.
- [x] 50bots: заявка «QR Studio — QR-коды в Telegram» принята, модерация.
- [x] BotPulse: карточка отправлена на модерацию.
- [x] Catalog Telegram: карточка «QR Studio» принята, модерация.
- [x] Промо-картинка `assets/promo/showcase.png` (6 пресетов, 1200×1000).
- [ ] Владелец: `/setuserpic` в BotFather → `assets/promo/avatar.png`.
- [ ] Владелец: подтвердить владение в BotPulse через @RBSFamilySupportBot.
- [ ] Владелец: подтвердить владение в 50bots через @verif_50_bot.
- [ ] Владелец: пройти капчу на tlg.me/add и telegram.menu/add.
- [ ] Владелец: создать публичный канал и дать боту право публикации.
- [ ] Учитывать deep-link `?start=<source>` в `/start` для атрибуции каталогов.
- [ ] Кнопка «Поделиться ботом» и inline-режим.

## Идеи

- [ ] UI-тумблер монохромного логотипа.
- [ ] UI-переключатель «QR в фигуре / с плашкой».
- [ ] Выбор позиции/размера фото-карточки (сейчас правый нижний угол, 42%).
- [ ] Кнопка сброса настроек в редакторе.
- [ ] Примеры QR и скриншоты Mini App/фото-режима в README.
- [ ] Уточнить «QR на QR»: логотип поверх QR или буквальное наложение.
- [ ] Добавить постоянный storage, чтобы выбранный язык переживал рестарт Render.
- [ ] Синхронизировать Telegram-команды с выбранным языком (сейчас default EN + `ru` scope; menu button уже per-chat).
