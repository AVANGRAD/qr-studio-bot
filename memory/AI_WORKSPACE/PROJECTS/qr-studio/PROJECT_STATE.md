# Project State

Обновлено: 2026-11-19

## Готово

- Библиотека `qrstudio`: 52 формы, 24 стиля модулей, 14 глаз, 19 палитр, 25 пресетов.
- Добавлены формы `squircle`, `burst`, `clover`, `cactus`, `frog`, `whale`, `anchor`, `music_note`; модули `flower`, `chevron`, `arch`, `spark`, `plus`, `brick`; глаза `capsule`, `octagon`, `spark`, `heart`.
- Добавлены палитры `berry`, `ocean`, `sunset`, `midnight` и пресеты `cosmic`, `forest`, `candy`, `ocean`, `retro`, `royal`, `sailor`.
- `flower` использует безопасную базу `dot` + overlay, чтобы сохранить сканируемость; `brick` получил два варианта раскладки.
- Логотипы: 7 режимов, включая новый `badge` («Медальон») с круглой подложкой; PNG и SVG.
- Добавлен `qrstudio/emblems.py`: 12 встроенных нейтральных иконок (`heart`, `star`, `crown`, `leaf`, `paw`, `rocket`, `flower`, `moon`, `planet`, `shield`, `music_note`, `anchor`) и меню «Готовые иконки» с пагинацией.
- `Draft.logo_emblem` хранит ключ встроенной иконки; `Draft.logo_label` оставлен для старых draft и загруженных логотипов. Подпись и кнопка редактора показывают выбранную иконку и режим.
- Рендер PNG/SVG, монограммы, safe-fallback, контраст, фото-режим.
- Telegram-бот на aiogram: меню, FSM, превью, PNG/SVG, лимиты.
- Telegram Mini App: `/app`, каталог, превью, 134 статические плитки, cache-bust `?v=variety1`; Apply через подписанный `POST /app/apply` + fallback `WebApp.sendData`.
- Mini App доступен кнопкой меню «QR Studio», командой `/app` и кнопкой «Выбрать визуально» в редакторе; для групп скрыт (только private).
- Настройки, выбранные до создания QR, сохраняются как `pending_webapp` и применяются к следующему тексту.
- QR встроен в силуэт: 36 из 51 не-square формы рендерятся без плашки; 15 сложных форм безопасно откатываются в frame с предупреждением.
- Фото-режим: фото полностью вписывается, фон — размытая cover-копия; QR на светлой карточке 42% справа снизу (`photo_inset=0.055`, `photo_opacity=244`).
- Фото-поддержка в PNG/SVG; `Draft.photo_bytes`, `prepare_uploaded_photo`, `Flow.photo`, `bot/handlers/photo.py`, кнопки «Фото + QR»/«Фото»; загрузка до и после текста.
- `pytest`: 81 тест проходит; `ruff` без ошибок; `node --check webapp/app.js` OK.
- `scripts/check_scans.py`: 262/262 QR декодируются, включая 52 формы в figure-режиме, 25 пресетов, 12 встроенных иконок и фото-сценарии.
- PNG download теперь принудительно отправляется как документ (`disable_content_type_detection=True`) и в текущий чат, а не в `callback.from_user.id`; это устраняет авто-обработку PNG как фото и сбои в группах.
- Локализация `ru/en`: `bot/i18n.py`, `t()`, `LanguageMiddleware`, `resolve_lang()`; выбор языка при первом `/start`, `/language`, callback `lang:set:*`; выбор сохраняется в FSM как `lang` и переживает `clear_flow`.
- Локализованы handlers, keyboards, errors, services, Mini App и каталог; `RenderResult.warning_codes` позволяет переводить предупреждения без потери raw-текста.
- Mini App: язык из URL → `localStorage` → Telegram → browser; `/app/catalog.json?lang=`; Apply передаёт `lang` и synthetic `User.language_code`.
- В Mini App добавлен переключатель RU/EN; язык сразу перерисовывает интерфейс и каталог, сохраняется в `localStorage`, а Apply синхронизирует FSM.
- `bot/services.set_menu_button()` обновляет per-chat menu button с `?lang=`; вызывается из `/start`, `/language` и Apply. Глобальная кнопка без `lang` остаётся fallback.
- Команды бота: default English + `ru` scope; `set_commands` исправлен, чтобы default не зависел от ContextVar.
- GitHub: feature `3f1062f`, docs `1d108fd`, docs `194d412`, feature `9654ddf`, analytics `afe6edf`, docs `b22e0b1`; `master` запушен.
- Render: `srv-dbun5pgjo6nc73ajoohg`, https://qr-studio-bot.onrender.com; support/all-time `f1f8f32` (`dep-dbvfl1mq1p3s738ero7g`) live 2026-11-19 13:32 UTC; предыдущий analytics deploy `afe6edf` (`dep-dbvf7jjm8hqs73b2r28g`).
- Аналитика: `bot/analytics.py` подключается к Supabase PostgreSQL через `asyncpg`, использует `analytics.users`/`analytics.events` (схемы создаются миграцией), пишет активность middleware и считает DAU/WAU/MAU; `/stats` доступен только при `ADMIN_ID` и только в private-чате. В `/stats` добавлены события за всё время (`total_events`, `events_all`).
- Схема аналитики: пользователь (`first_seen`, `last_seen`, `updates_count`, `starts_count`, `blocked_at`) и события (`start`, команды, сообщения, Mini App Apply, скачивания, смена настроек); текст сообщений и содержимое QR не сохраняются.
- Новый Supabase PostgreSQL 17.12 проверен: таблицы созданы, тестовые пользователь/события записаны и удалены; `DATABASE_URL` добавлен в локальный `.env` и Render Environment.
- `asyncpg==0.32.0` добавлен в `requirements.txt`, `DATABASE_URL` — в `.env.example` и `render.yaml`; `ADMIN_ID` найден через `getChat` и задан локально и в Render.
- Актуальные проверки: `pytest` 81/81, `ruff` OK, scans 262/262; live-деплой security-hardening выполнен.
- Поддержка: `bot/support.py` — отдельный `SupportBot` на `SUPPORT_BOT_TOKEN`, свой `Dispatcher` и webhook `/support/webhook/<secret>` на том же aiohttp-сервере. Сообщения пользователей пересылаются в `ADMIN_ID`, ответы администратора копируются пользователю; mapping хранится в `support.tickets` (fallback — память).
- Live support/all-time: `/healthz` вернул `support: true`; main/support webhook pending 0, last_error пустой; логи `support database connected`, `support webhook set`, `analytics database connected`; support route 200 с secret; synthetic `/stats` 200 и событие записано.
- Администратору отправлено сообщение в основном боте со ссылкой на `@QUaRc0DeSupport_bot`; support-бот пока не может писать админу до `/start` (`chat not found`), это ожидаемо.
- Основной бот получил `/support` со ссылкой на `@QUaRc0DeSupport_bot`; команда добавлена в меню. `SUPPORT_BOT_TOKEN` задан локально и в Render Environment. С 2026-11-19 задан отдельный случайный `SUPPORT_WEBHOOK_SECRET`; путь поддержки вычисляется отдельно.
- `SUPPORT_BOT_TOKEN` добавлен в `.env.example` и `render.yaml`; `support.tickets` создана и проверена в Supabase, тестовая строка удалена.
- Live 2026-11-19 после `afe6edf`: `analytics database connected`, `/healthz`, `/app`, `/app/static/app.js`, `/app/catalog.json?lang=ru` 200, webhook pending 0; synthetic `/stats` от ADMIN_ID прошёл 200, в `analytics.users`/`analytics.events` появилась запись; ошибок в логах нет.
- Live 2026-11-19 после `9654ddf`: `/healthz`, `/app`, `/app/static/app.js`, `/app/catalog.json?lang=en|ru`, `/app/preview.png` 200; live HTML и JS `?v=i18n2`, есть `id="lang"`, `setLanguage`, `qrstudio.lang`; EN-каталог `Geometry/Square/Golden leaf`, RU — `Геометрия/Квадрат/Золотой лист`; `/app/apply` 400 без initData; webhook pending 0, ошибок нет; бот `@QUaRc0De_bot` id `9062123985`.

## Осталось

- Живая проверка Telegram: `/start`, picker RU/EN, `/language`, `en`-Telegram, Mini App `?lang=en` и команды.
- Живая проверка обычных пользовательских событий после первого реального `/start`/QR; synthetic `/stats` уже проверен.
- Проверить live-тикет: администратор уже доступен (`getChat` 200), нужен второй пользователь для реального сообщения.
- Проверить `/support` и `/stats` в реальном Telegram-клиенте; synthetic webhook уже прошёл.
- Живая проверка переключателя RU/EN в Mini App и per-chat menu button после `/language`/Apply.
- Живая проверка Apply в Telegram: menu/inline и keyboard-сценарий.
- Живая проверка PNG после принудительной отправки документом (`819253b`); SVG уже проверен пользователем.
- Живая проверка в Telegram: фото, фото + логотип, фото-первый сценарий, новые формы/узоры/глаза, встроенные иконки и режим «Медальон».
- Проверить экстремальные комбинации вроде `frog + flower + spark` на 512–640 px: локально они могут не декодироваться, на 1024 px проходят.
- Проверить, что новая карточка фото не закрывает важный объект; при необходимости изменить `photo_card`/`photo_inset`.
- Решить, нужен ли UI-переключатель «в фигуре / с плашкой»; сейчас figure-режим включён по умолчанию.
- При необходимости добавить скриншоты/примеры Mini App и фото-режима в README.
- Уточнить запрос «QR на QR»: центральный логотип поверх QR или буквальное наложение QR на QR.

## Известные ограничения

- SVG: силуэты и логотип — встроенный PNG, модули QR — вектор; фото также встроено PNG.
- Лимит 1200 символов и 2048 px; логотип до 6 МБ, фото до 12 МБ.
- В фото-режиме фото уменьшается до 1600 px; итоговый QR PNG/SVG остаётся векторным (модули), фото — растровое.
- Free Render засыпает; self-ping 600 с; первый запуск после сна около минуты.
- Mini App требует HTTPS; загрузка фото и своих файлов в Mini App не поддерживается.
- Выбор языка хранится в `MemoryStorage` и теряется после рестарта Render; при следующем `/start` picker появится снова, direct messages используют Telegram fallback.
- Support-бот работает в том же процессе и на том же Render-сервисе; без `SUPPORT_BOT_TOKEN` отключается. Без `DATABASE_URL` mapping тикетов живёт в памяти до рестарта.
- Администратор должен один раз запустить support-бота; Telegram не разрешает боту писать первым.
- Аналитика опциональна: без `DATABASE_URL` бот работает как раньше. Точного события «ушёл» Telegram не даёт; `dormant` — отсутствие активности 30+ дней, `blocked_at` — только при 403 от Telegram, например при рассылке.
- Per-chat menu button обновляется после `/start`, `/language` и Apply; если Telegram API недоступен, остаётся глобальная кнопка без `lang`.
- `WebApp.sendData` не работает для menu/inline Mini App; для них используется серверный `/app/apply` с подписанным `initData`.
- SVG-caption экранирует HTML; при ошибке caption документ отправляется без подписи.
- Статические плитки нужно пересобирать после изменения каталога: `python scripts/build_miniapp_thumbs.py`.
- 15 сложных силуэтов (`moon`, `snowflake`, `wave`, `fox`, `ladybug`, `turtle`, `penguin`, `frog`, `whale`, `mask`, `rocket`, `guitar`, `pumpkin`, `anchor`, `music_note`) используют безопасную плашку.
- Встроенные иконки нейтральные, без брендовых логотипов; брендовый знак можно загрузить своим файлом.
- `set_my_commands` задаёт default English и `ru` scope; смена языка в picker не меняет Telegram-команды для уже открытого чата.

## Безопасность (2026-11-19)

- Webhook path отделён от header-секрета: `_webhook_path_token()` в `bot/config.py` даёт SHA256-хеш, а Telegram получает секрет только в `X-Telegram-Bot-Api-Secret-Token`; стартовый лог маскирован.
- `WEBHOOK_SECRET` и `SUPPORT_WEBHOOK_SECRET` ротированы в Render; пути main/support webhook изменились, pending 0, неверный секрет даёт 401.
- Создана роль `qr_app` (`NOSUPERUSER NOCREATEDB NOCREATEROLE`) с доступом только к таблицам/последовательностям `analytics` и `support`; `DATABASE_URL` в Render и `.env` переключён на неё.
- Runtime DDL убран из `Analytics.connect()`/`SupportStore.connect()`; схемы применяет `python -m scripts.migrate` от административной роли (`DATABASE_ADMIN_URL`).
- `bot/db.py` проверяет Supabase CA `certs/prod-ca-2021.crt` и hostname; `ssl=ssl_context()` заменил `ssl="require"` в аналитике и поддержке.
- Support rate limit: 5/мин, 30/час, 100/день; Mini App `/app/apply` — 10/мин, 100/день на пользователя, `/app/preview.png` — 40/мин на IP и общий семафор рендера с таймаутами.
- `/stats` игнорируется в группах; `/app/apply` требует `application/json`, проверяет HMAC, `auth_date` не старше 6 часов и не из будущего (>5 минут).
- GitHub-коммит `e6b592b`; Render deploy сначала `dep-dbvheo7f3r2c7380gemg`, затем с новыми env `dep-dbvhh1ek1f9s73cj5vt0` live. Live: `/healthz` 200, `/app` 200, main/support webhook 200 с секретом и 401 с неверным, support route 404 на неверном пути, `analytics database connected`, `support database connected`.
- `DATABASE_URL` app user в Render — `qr_app.wttemlygheqkwutwagpk`; административный URL после настройки удалён из `/tmp` и не хранится в репозитории/`.env`.

## Продвижение

- Профиль бота заполнен 2026-11-19: короткое и полное описание установлены через Bot API; до этого оба были пустыми.
- Аватар сгенерирован (`assets/promo/avatar.png`, `avatar-512.png`); в BotFather его загружает владелец.
- Промо-картинка `assets/promo/showcase.png` (6 пресетов) готова для постов.
- План и тексты: `documentation/PROMOTION.md`. Заявки: 50bots — принята (модерация), BotPulse — на модерации,
  Catalog Telegram — принята (модерация).
- BotPulse повторная подача блокируется как дубль; подтверждение владения — только через поддержку.
- Не поданы: tlg.me и telegram.menu (капча), BotList и TG App Market (аккаунт), StoreBot (Telegram), tgreef.com (аккаунт).
- Мёртвые: katalogtelegram.ru (DNS), telegram-store.com/add (404).
- WebGrupos проверен, но пропущен: англоязычный каталог с NSFW-разделами, бренд-риск.
- Для атрибуции каналов пока не логируется `?start=` payload; кнопка «Поделиться» и inline-режим не реализованы.
