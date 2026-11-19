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
- `pytest`: 62 теста проходят; `ruff` без ошибок; `node --check webapp/app.js` OK.
- `scripts/check_scans.py`: 262/262 QR декодируются, включая 52 формы в figure-режиме, 25 пресетов, 12 встроенных иконок и фото-сценарии.
- PNG download теперь принудительно отправляется как документ (`disable_content_type_detection=True`) и в текущий чат, а не в `callback.from_user.id`; это устраняет авто-обработку PNG как фото и сбои в группах.
- Локализация `ru/en`: `bot/i18n.py`, `t()`, `LanguageMiddleware`, `resolve_lang()`; выбор языка при первом `/start`, `/language`, callback `lang:set:*`; выбор сохраняется в FSM как `lang` и переживает `clear_flow`.
- Локализованы handlers, keyboards, errors, services, Mini App и каталог; `RenderResult.warning_codes` позволяет переводить предупреждения без потери raw-текста.
- Mini App: язык из URL → Telegram → browser; `/app/catalog.json?lang=`; Apply передаёт synthetic `User.language_code`.
- Команды бота: default English + `ru` scope; `set_commands` исправлен, чтобы default не зависел от ContextVar.
- GitHub: feature `3f1062f` (`feat: add ru/en localization and language picker`), docs `1d108fd` (`docs: record ru/en localization and deploy`); `master` запушен.
- Render: `srv-dbun5pgjo6nc73ajoohg`, https://qr-studio-bot.onrender.com; feature deploy `3f1062f` (`dep-dbvcimjrjlhs73ed143g`), docs redeploy `1d108fd` (`dep-dbvck6p7lnhs739caeu0`), оба live.
- Live 2026-11-19: `/healthz`, `/app`, `/app/static/app.js`, `/app/catalog.json?lang=en|ru`, `/app/preview.png` 200; `/app/apply` 400 без initData; HTML подключает `?v=i18n1`; EN-каталог `Geometry/Square/Golden leaf`, RU — `Геометрия/Квадрат`; команды default EN и `ru` scope; webhook pending 0, ошибок нет; бот `@QUaRc0De_bot` id `9062123985`.

## Осталось

- Живая проверка Telegram: `/start`, picker RU/EN, `/language`, `en`-Telegram, Mini App `?lang=en` и команды.
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
- Постоянная кнопка меню Mini App не передаёт выбранный в FSM язык; `/app` передаёт его явно, меню использует язык Telegram.
- `WebApp.sendData` не работает для menu/inline Mini App; для них используется серверный `/app/apply` с подписанным `initData`.
- SVG-caption экранирует HTML; при ошибке caption документ отправляется без подписи.
- Статические плитки нужно пересобирать после изменения каталога: `python scripts/build_miniapp_thumbs.py`.
- 15 сложных силуэтов (`moon`, `snowflake`, `wave`, `fox`, `ladybug`, `turtle`, `penguin`, `frog`, `whale`, `mask`, `rocket`, `guitar`, `pumpkin`, `anchor`, `music_note`) используют безопасную плашку.
- Встроенные иконки нейтральные, без брендовых логотипов; брендовый знак можно загрузить своим файлом.
- `set_my_commands` задаёт default English и `ru` scope; смена языка в picker не меняет Telegram-команды для уже открытого чата.
