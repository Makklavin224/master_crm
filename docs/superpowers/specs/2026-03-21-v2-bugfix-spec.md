# МоиОкошки v2.1 — Bugfix & Stabilization Spec

## Проблема

После деплоя v2.0 на прод обнаружено 27 проблем. Код писался без полной спецификации — модули не стыкуются, edge cases не обработаны, UI-элементы сломаны. Нужна стабилизация перед запуском пользователей.

## Scope

Только фиксы и доводка. Ноль новых фич. Цель: каждый экран работает end-to-end.

---

## Модуль 1: QR-код и Booking Link (CRITICAL)

### User Stories
- Как мастер, я хочу чтобы QR-код из настроек открывал мини-апп с booking flow, а не просто сайт
- Как клиент, я хочу отсканировать QR и сразу записаться

### Что сломано
- `web/src/pages/SettingsPage.tsx:90` — QR кодирует `https://moiokoshki.ru/m/{username}` (веб-страница)
- Должен кодировать deep link бота: `https://t.me/{BOT_USERNAME}?startapp={master_id}`

### Фикс
- **File:** `web/src/pages/SettingsPage.tsx`
- **Line 90:** Заменить `bookingUrl` на два варианта:
  - "Ссылка на страницу": `https://moiokoshki.ru/m/{username}` (для Instagram bio, сайта)
  - "QR для записи через Telegram": `https://t.me/{BOT_USERNAME}?startapp={master_id}`
- Два QR-кода или переключатель "Тип ссылки"
- BOT_USERNAME берётся из env `VITE_TG_BOT_USERNAME` или из API `/settings/profile`
- **File:** `web/src/api/settings.ts` — добавить `bot_username` в ProfileSettings response
- **File:** `backend/app/schemas/settings.py` — добавить `bot_username: str` в ProfileSettingsRead
- **File:** `backend/app/api/v1/settings.py` — возвращать `bot_username` из `settings.tg_bot_token.split(":")[0]` или из config

### Acceptance Criteria
- QR отсканированный через Telegram камеру → открывает мини-апп с booking flow мастера
- Ссылка скопированная → открывает публичную страницу мастера в браузере
- Оба варианта видны на странице "Моя страница"

---

## Модуль 2: Role Detection в мини-аппе (CRITICAL)

### User Stories
- Как мастер, я хочу открыть мини-апп и сразу увидеть панель управления
- Как клиент, я хочу открыть мини-апп и увидеть запись к мастеру

### Что сломано
- `frontend/src/stores/master-auth.ts` — `autoDetectRole` может вызываться дважды (race condition)
- `frontend/src/App.tsx` — RoleDetector не проверяет что bridge.ready() завершился
- Нет debounce на autoDetectRole

### Фикс
- **File:** `frontend/src/stores/master-auth.ts`
  - Добавить `_detecting: boolean` guard в store
  - `autoDetectRole`: if `_detecting` return early
  - Set `_detecting = true` at start, `false` at end (in finally)
- **File:** `frontend/src/App.tsx`
  - RoleDetector: дождаться `bridge.ready()` перед вызовом `autoDetectRole`
  - Показывать loading spinner пока role === "detecting"
- **File:** `frontend/src/components/RoleSwitcher.tsx`
  - Сохранять выбор роли в localStorage: `master_role_preference`
  - При autoDetectRole: если есть preference И user is master → использовать preference

### Acceptance Criteria
- Мастер открывает мини-апп → видит мастер-панель (не "мои записи")
- Клиент открывает мини-апп по ссылке мастера → видит booking flow
- Переключатель ролей сохраняется между перезагрузками
- Нет двойных вызовов autoDetectRole

---

## Модуль 3: Bot Registration Flow (HIGH)

### User Stories
- Как новый мастер, я хочу зарегистрироваться через TG бота нажав одну кнопку
- Как существующий мастер (зарегался через сайт), я хочу привязать TG аккаунт

### Что сломано
- `backend/app/bots/telegram/handlers/callbacks.py` — callback `register_master` может не существовать или не обработан
- `backend/app/bots/telegram/handlers/start.py` — после нажатия "Зарегистрироваться" ничего не происходит

### Фикс
- **File:** `backend/app/bots/telegram/handlers/callbacks.py`
  - Проверить что `cb_register_master` handler существует
  - Реализовать: создать Master через `auth_service.register_master_from_bot(name=user.full_name, tg_user_id=user.id)`
  - Ответить: "Вы зарегистрированы! Откройте мини-апп для настройки." + InlineKeyboardButton(text="Открыть", web_app=WebAppInfo(url=mini_app_url))
- **File:** `backend/app/bots/max/handlers/callbacks.py` — то же для MAX
- Проверить что `register_master_from_bot` в `auth_service.py` создаёт Master без пароля (пароль можно задать позже в админке)

### Acceptance Criteria
- Новый пользователь → /start → "Зарегистрироваться как мастер" → нажал → зарегистрирован → кнопка "Открыть мини-апп"
- Существующий мастер → /start → "Привязать аккаунт" → ввёл email → привязано → "Откройте мини-апп"
- После регистрации/привязки мини-апп открывается в мастер-панели

---

## Модуль 4: Client Cabinet Auth (HIGH)

### User Stories
- Как клиент, я хочу войти в кабинет по номеру телефона и увидеть свои записи

### Что сломано
- `public/src/stores/auth.ts` — session cookie handling неконсистентный
- `backend/app/api/v1/client_auth.py` — OTP может не доставляться если клиент не в боте
- `public/src/api/client-cabinet.ts` — credentials: "include" может не работать cross-origin

### Фикс
- **File:** `backend/app/api/v1/client_auth.py`
  - verify-code: возвращать session token в response body (не только cookie)
  - Добавить `Set-Cookie` header с `SameSite=None; Secure` для cross-origin
- **File:** `public/src/stores/auth.ts`
  - Хранить token в localStorage как fallback (если cookie не работает)
  - При каждом запросе: отправлять token в `Authorization: Bearer` header
- **File:** `public/src/api/client-cabinet.ts`
  - Добавить Authorization header из auth store
- **File:** `backend/app/core/dependencies.py`
  - `get_current_client`: проверять и cookie, и Bearer header

### Acceptance Criteria
- Клиент вводит телефон → получает OTP в мессенджер → вводит код → видит свои записи
- Работает и через cookie, и через Bearer token
- Session сохраняется 7 дней

---

## Модуль 5: Analytics Page Robustness (CRITICAL)

### Что сломано
- `web/src/pages/AnalyticsPage.tsx` — нет null checking на данные от API
- Charts ломаются если API возвращает пустые/неполные данные

### Фикс
- **File:** `web/src/pages/AnalyticsPage.tsx`
  - Обернуть все charts в conditional rendering: `if (!summary) return <Empty />`
  - PieChart: проверять `summary.new_clients + summary.repeat_clients > 0` перед рендером
  - LineChart: проверять `chartData?.length > 0`
  - Добавить `isError` handling с EmptyState и кнопкой "Повторить"
  - Все числовые значения: `Number(value) || 0`

### Acceptance Criteria
- Пустая аналитика (новый мастер без данных) → показывает "Нет данных за выбранный период"
- API ошибка → "Ошибка загрузки" + кнопка "Повторить"
- Частичные данные → не ломают charts

---

## Модуль 6: Mini-App Booking Flow Validation (HIGH)

### Что сломано
- `frontend/src/App.tsx` — `/book/:masterId` не валидирует что мастер существует
- Невалидный UUID в URL → пустой экран

### Фикс
- **File:** `frontend/src/pages/client/ServiceSelection.tsx`
  - Если `useServices(masterId)` возвращает 404 → показать EmptyState "Мастер не найден"
  - Добавить проверку что masterId — валидный UUID перед API запросом
- **File:** `public/src/pages/MasterPage.tsx`
  - Улучшить 404 страницу: "Мастер не найден. Проверьте ссылку или попросите мастера отправить новую."

### Acceptance Criteria
- Невалидный URL `/book/garbage` → "Мастер не найден"
- Несуществующий UUID → "Мастер не найден"
- Работающая ссылка → нормальный booking flow

---

## Модуль 7: Error Handling & UX Polish (MEDIUM)

### Список мелких фиксов

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `web/src/pages/ReviewsPage.tsx` | Нет error handling | Добавить isError + EmptyState |
| 2 | `frontend/src/components/RoleSwitcher.tsx` | Role не сохраняется при refresh | localStorage persistence |
| 3 | `web/src/pages/SettingsPage.tsx:60` | Hardcoded domain | Использовать env variable |
| 4 | `web/src/pages/SettingsPage.tsx:702` | Card number без валидации | Добавить format + basic validation |
| 5 | `web/src/pages/SettingsPage.tsx:743` | Test mode без предупреждения | Добавить Alert "Тестовый режим — платежи не обрабатываются" |
| 6 | All API clients | Нет timeout | Добавить AbortController с 30s timeout |
| 7 | All error messages | Микс EN/RU | Стандартизировать на русском |

---

## Приоритет реализации (фазы GSD)

| Phase | Модули | Severity |
|-------|--------|----------|
| 18 | Модули 1, 2, 5 (QR, Role Detection, Analytics) | CRITICAL |
| 19 | Модули 3, 4, 6 (Bot Registration, Client Auth, Booking Validation) | HIGH |
| 20 | Модуль 7 (Error Handling & UX Polish) | MEDIUM |

---

*Spec created: 2026-03-21*
*Based on: full project audit (27 issues found)*
*Methodology: Spec-First — fix spec before code*
