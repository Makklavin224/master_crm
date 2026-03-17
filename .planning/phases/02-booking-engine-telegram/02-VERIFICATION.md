---
phase: 02-booking-engine-telegram
verified: 2026-03-17T18:00:00Z
status: human_needed
score: 5/5 must-haves verified
human_verification:
  - test: "Run full backend test suite in Docker and confirm all 58 tests pass"
    expected: "docker compose exec api uv run pytest tests/ -x -v --tb=short exits 0 with 58 tests passing (services:7, schedule:9, bookings:10, clients:4, auth_tg:4, settings:4, bot:20)"
    why_human: "Tests were written and code was AST-verified but Docker was unavailable on dev machine during execution. No automated test run was recorded."
  - test: "Run frontend tests and confirm format smoke tests pass"
    expected: "cd frontend && pnpm test exits 0 with 12 vitest tests passing (formatPrice:4, formatDuration:4, formatDate:2, formatTime:1)"
    why_human: "pnpm test was not executed during Plan 03 execution due to session structure. Test code exists and is syntactically correct."
  - test: "Run docker compose up and open http://localhost:3000/book/{MASTER_ID} -- complete the full 5-step client booking flow"
    expected: "Service list loads, calendar appears with Russian locale, time slots render in 3-column grid, name+phone form submits, confirmation page shows booking summary with checkmark animation"
    why_human: "Visual layout, inter font rendering, #6C5CE7 accent color, 44px touch targets, and Russian copy can only be verified visually in a browser."
  - test: "Open http://localhost:3000/master/dashboard and verify the master management panel"
    expected: "Bottom tab bar shows 5 tabs (Сегодня, Записи, Услуги, Клиенты, Настройки) with CalendarDays/BookOpen/Scissors/Users/Settings Lucide icons; active tab shows accent label; each screen loads with correct Russian headings"
    why_human: "Visual rendering, tab icon rendering, and accent active state require browser verification."
  - test: "Verify Telegram bot commands work end-to-end with a real bot token"
    expected: "/start creates a master; /start MASTER_ID shows booking button opening mini-app; /today shows today's bookings; /link returns t.me/bot?start=MASTER_ID; booking creates notification in master's TG chat"
    why_human: "Bot commands require a real TG bot token, live Telegram connection, and ngrok/VPS webhook registration -- not verifiable from code alone."
---

# Phase 2: Booking Engine + Telegram Verification Report

**Phase Goal:** Clients can discover services, view available slots, and book appointments through the Telegram mini-app; masters receive notifications and can manage bookings through the TG bot and mini-app
**Verified:** 2026-03-17T18:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Master can create a service catalog (name, duration, price, category) and configure working hours via the API | VERIFIED | `backend/app/api/v1/services.py` with full CRUD; `backend/app/api/v1/schedule.py` with PUT /schedule and exception endpoints; both routers mounted in `router.py` |
| 2 | Client opens TG mini-app, sees available services, picks a date, sees only genuinely free time slots, and completes a booking | VERIFIED | `frontend/src/pages/client/ServiceSelection.tsx` (useServices), `DatePicker.tsx` (react-day-picker), `TimePicker.tsx` (useAvailableSlots), `BookingForm.tsx` (useCreateBooking with 409 race condition handling), `Confirmation.tsx` (checkmark + booking summary) |
| 3 | Two clients attempting to book the same slot simultaneously results in one success and one rejection (no double-booking) | VERIFIED | `booking_service.py` lines 131-148: `.with_for_update()` on overlap query; `alembic/versions/003_add_booking_exclusion_and_master_settings.py` adds btree_gist extension + tstzrange booking_range + exclusion constraint as safety net |
| 4 | Client can cancel or reschedule a booking (respecting the master's configurable deadline); master can cancel, reschedule, or manually add a booking | VERIFIED | `booking_service.py`: `cancel_booking()` enforces deadline for "client" caller, skips for "master"; `reschedule_booking()` same pattern; `create_manual_booking()` for master-only adds; `bookings.py` API router exposes all three paths |
| 5 | Master receives a Telegram bot notification when a new booking is created or cancelled; client data is auto-captured into the client database with visit history visible | VERIFIED | `booking_service.py` `_notify_master()` called from `create_booking()`, `cancel_booking()`, and `reschedule_booking()` (fire-and-forget); `client_service.py` `find_or_create_client()` normalizes phone + creates/links Client + ClientPlatform; `get_or_create_master_client()` + `update_visit_stats()` track per-master visits |

**Score:** 5/5 truths verified

### Required Artifacts

#### Plan 02-01 (Backend Booking Engine)

| Artifact | Status | Evidence |
|----------|--------|----------|
| `backend/app/services/schedule_service.py` | VERIFIED | 142 lines; `get_available_slots()` fully implemented: checks ScheduleException, falls back to MasterSchedule, queries existing bookings, generates candidate slots, filters breaks/overlaps, uses ZoneInfo |
| `backend/app/services/booking_service.py` | VERIFIED | 351 lines; `create_booking`, `cancel_booking`, `reschedule_booking`, `create_manual_booking`, `get_master_bookings` all implemented |
| `backend/app/services/client_service.py` | VERIFIED | 154 lines; `find_or_create_client`, `get_or_create_master_client`, `update_visit_stats`, `get_master_clients`, `get_client_with_history` all implemented |
| `backend/app/api/v1/services.py` | VERIFIED | Router with POST/GET/PUT/DELETE /services and mounted in router.py at prefix="/services" |
| `backend/app/api/v1/schedule.py` | VERIFIED | Router with GET/PUT /schedule, GET/POST/DELETE /schedule/exceptions |
| `backend/app/api/v1/bookings.py` | VERIFIED | Router with POST /bookings, GET /bookings, POST /bookings/manual, PUT /{id}/cancel, PUT /{id}/reschedule |
| `backend/app/api/v1/clients.py` | VERIFIED | Router with GET /clients, GET /clients/{id} |
| `backend/app/api/v1/auth.py` | VERIFIED | POST /auth/tg endpoint validates TG initData HMAC-SHA256, looks up master by tg_user_id, returns JWT |
| `backend/app/api/v1/settings.py` | VERIFIED | GET/PUT /settings for buffer_minutes, cancellation_deadline_hours, slot_interval_minutes |
| `backend/alembic/versions/003_add_booking_exclusion_and_master_settings.py` | VERIFIED | File exists |
| `backend/app/models/master.py` | VERIFIED | tg_user_id (String 100, unique, index), buffer_minutes (Integer, default=0), cancellation_deadline_hours (Integer, default=24), slot_interval_minutes (Integer, default=30) |
| `backend/app/core/security.py` | VERIFIED | `validate_tg_init_data()` with HMAC-SHA256 and `hmac.compare_digest()` (timing-safe) |

#### Plan 02-02 (Telegram Bot)

| Artifact | Status | Evidence |
|----------|--------|----------|
| `backend/app/bots/telegram/bot.py` | VERIFIED | `bot = Bot(...)` and `dp = Dispatcher()` singletons; guarded by token presence; registers 5 handler routers + DatabaseMiddleware + TelegramAdapter |
| `backend/app/bots/common/adapter.py` | VERIFIED | `MessengerAdapter` ABC with `send_booking_notification()` and `send_message()` abstractmethods; `BookingNotification` dataclass |
| `backend/app/bots/common/notification.py` | VERIFIED | `NotificationService` with `register_adapter()` and `send_booking_notification()`; module-level `notification_service` singleton |
| `backend/app/bots/telegram/adapter.py` | VERIFIED | `TelegramAdapter` implements MessengerAdapter; HTML-formatted Russian messages (new/cancelled/rescheduled); inline buttons (Подробнее/Расписание) |
| `backend/app/bots/telegram/handlers/start.py` | VERIFIED | `CommandStart(deep_link=False)` creates/welcomes master; `CommandStart(deep_link=True)` validates UUID, verifies active master, shows WebAppInfo booking button |
| `backend/app/main.py` | VERIFIED | POST /webhook/telegram with `x_telegram_bot_api_secret_token` validation, `dp.feed_update()` dispatch; lifespan registers/deregisters webhook |

#### Plan 02-03 (React Mini-App Client Flow)

| Artifact | Status | Evidence |
|----------|--------|----------|
| `frontend/src/platform/types.ts` | VERIFIED | `Platform` type union + `PlatformBridge` interface with all 9 methods |
| `frontend/src/platform/adapters/telegram.ts` | VERIFIED | `createTelegramBridge()` using @telegram-apps/sdk-react; all PlatformBridge methods implemented |
| `frontend/src/stores/booking-flow.ts` | VERIFIED | Zustand store with 5-step wizard state; `useBookingFlow` exported |
| `frontend/src/pages/client/ServiceSelection.tsx` | VERIFIED | Uses `useServices`, `useBookingFlow`, `usePlatform`; heading "Выберите услугу"; loading skeletons; empty state; haptic + navigate on select |
| `frontend/src/pages/client/DatePicker.tsx` | VERIFIED | Uses react-day-picker; heading "Выберите дату" |
| `frontend/src/pages/client/TimePicker.tsx` | VERIFIED | Uses `useAvailableSlots`, `SlotGrid`; heading "Выберите время" |
| `frontend/src/pages/client/BookingForm.tsx` | VERIFIED | Uses `useCreateBooking`; heading "Ваши данные"; +7 phone mask; 409 conflict handling with toast + redirect to step 3 |
| `frontend/src/pages/client/Confirmation.tsx` | VERIFIED | Heading "Вы записаны!"; checkmark animation; booking summary card; "Мои записи" link |
| `frontend/vitest.config.ts` | VERIFIED | File exists; jsdom environment configured |

#### Plan 02-04 (Master Management Panel)

| Artifact | Status | Evidence |
|----------|--------|----------|
| `frontend/src/pages/master/Dashboard.tsx` | VERIFIED | Uses `useMasterBookings` with today filter; heading "Сегодня"; sorted booking list; share button |
| `frontend/src/pages/master/Services.tsx` | VERIFIED | File exists; heading "Услуги" |
| `frontend/src/pages/master/Schedule.tsx` | VERIFIED | File exists; heading "Расписание" |
| `frontend/src/pages/master/Bookings.tsx` | VERIFIED | File exists; heading "Все записи" |
| `frontend/src/pages/master/Clients.tsx` | VERIFIED | File exists; heading "Клиенты" |
| `frontend/src/pages/master/Settings.tsx` | VERIFIED | Uses `useMasterSettings` + `useUpdateSettings`; heading "Настройки"; pill selectors for buffer/deadline/interval; save calls PUT /settings |
| `frontend/src/components/BottomTabBar.tsx` | VERIFIED | NavLink-based; CalendarDays/BookOpen/Scissors/Users/Settings icons; aria-label on inactive tabs; accent active state |
| `frontend/src/stores/master-auth.ts` | VERIFIED | Calls `POST /api/v1/auth/tg` with `{ init_data: initDataRaw }`; stores JWT; `masterApiRequest` helper attaches Bearer token |

### Key Link Verification

#### Plan 02-01 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `api/v1/bookings.py` | `services/booking_service.py` | `create_booking()`, `cancel_booking()`, `reschedule_booking()` | WIRED | Lines 21-25 import all three; lines 56/164/201 call them |
| `services/booking_service.py` | `services/client_service.py` | `find_or_create_client()` on booking creation | WIRED | Line 151: `client = await find_or_create_client(...)` |
| `api/v1/masters.py` | `services/schedule_service.py` | `get_available_slots()` for slot calculation | WIRED | Line 16: import; line 69: call |
| `api/v1/auth.py` | `core/security.py` | `validate_tg_init_data()` + `create_access_token()` | WIRED | Lines 9 import; line 57 validate call; line 84 token creation |
| `api/v1/settings.py` | `models/master.py` | Read/update `buffer_minutes`, `cancellation_deadline_hours`, `slot_interval_minutes` | WIRED | Master model has all three columns; settings endpoint reads/writes them |

#### Plan 02-02 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `app/main.py` | `bots/telegram/bot.py` | webhook route + lifespan `bot.set_webhook()` | WIRED | `main.py` imports `bot, dp`; lifespan calls `bot.set_webhook()`; webhook handler calls `dp.feed_update(bot, update)` |
| `services/booking_service.py` | `bots/common/notification.py` | `_notify_master()` calls `notification_service.send_booking_notification()` | WIRED | `_notify_master()` lines 35/79 import and call `notification_service.send_booking_notification("telegram", notif)`; called from `create_booking()`, `cancel_booking()`, `reschedule_booking()` |
| `bots/common/notification.py` | `bots/telegram/adapter.py` | `TelegramAdapter.send_booking_notification()` | WIRED | `bot.py` registers `TelegramAdapter(bot)` via `notification_service.register_adapter("telegram", ...)`; notification routes to it by platform key |

#### Plan 02-03 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `api/client.ts` | backend `/api/v1/*` | `fetch` with `X-Init-Data` header | WIRED | `client.ts` line 24: `headers["X-Init-Data"] = initDataRaw` when present |
| `stores/booking-flow.ts` | `pages/client/*.tsx` | Zustand `useBookingFlow` consumed by all 5 booking pages | WIRED | All 5 pages import and destructure `useBookingFlow` |
| `platform/context.tsx` | `platform/adapters/telegram.ts` | `PlatformProvider` creates bridge on mount | WIRED | `context.tsx` lines 4-5 import both adapters; line 18 calls `createTelegramBridge()` when TG detected |

#### Plan 02-04 Key Links

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `stores/master-auth.ts` | `POST /api/v1/auth/tg` | Sends TG initData, receives JWT | WIRED | Lines 26-29: `fetch(...auth/tg...)` with `{ init_data: initDataRaw }` body |
| `pages/master/*.tsx` | `api/master-*.ts` | TanStack Query hooks with Bearer token auth | WIRED | Dashboard uses `useMasterBookings`; Settings uses `useMasterSettings`/`useUpdateSettings`; all master API hooks call `masterApiRequest` |
| `api/master-settings.ts` | `GET /api/v1/settings` and `PUT /api/v1/settings` | `useMasterSettings` and `useUpdateSettings` hooks | WIRED | Lines 17-37: queryFn calls `masterApiRequest("/settings")` and mutation calls `masterApiRequest("/settings", { method: "PUT", ... })` |
| `components/BottomTabBar.tsx` | `App.tsx` | NavLink from react-router-dom | WIRED | BottomTabBar uses NavLink with ROUTES constants; App.tsx defines all `/master/*` routes with `MasterLayout` wrapping `BottomTabBar` |

### Requirements Coverage

| Requirement | Plan | Description | Status | Evidence |
|-------------|------|-------------|--------|----------|
| BOOK-01 | 02-01 | Master can create a service catalog (name, duration, price, category) | SATISFIED | Service CRUD API in `api/v1/services.py` with ServiceCreate schema |
| BOOK-02 | 02-01 | Master can configure schedule (working hours per day, breaks, days off) | SATISFIED | Schedule API in `api/v1/schedule.py`; weekly template + exceptions |
| BOOK-03 | 02-01, 02-03 | Client can see available slots and book (select service -> date -> time) | SATISFIED | `get_available_slots()` backend + 5-step client booking flow frontend |
| BOOK-04 | 02-01 | System prevents double-booking (PostgreSQL exclusion constraints) | SATISFIED | SELECT FOR UPDATE + btree_gist tstzrange exclusion constraint in migration 003 |
| BOOK-05 | 02-01, 02-04 | Client can cancel or reschedule a booking (with configurable deadline) | SATISFIED | `cancel_booking()` + `reschedule_booking()` with deadline enforcement; cancel exposed in master Bookings screen |
| BOOK-06 | 02-01, 02-04 | Master can cancel, reschedule, or manually add a booking | SATISFIED | `create_manual_booking()` + master cancel endpoint (no deadline check); master Bookings screen with cancel action |
| CLNT-01 | 02-01 | Client database auto-populated from bookings (name, phone) | SATISFIED | `find_or_create_client()` called atomically in `create_booking()` |
| CLNT-03 | 02-01, 02-04 | Master can view client visit history | SATISFIED | `get_client_with_history()` + ClientDetail screen with booking history list |
| MSG-01 | 02-02 | Telegram Bot -- webhook processing, notifications to master and clients | SATISFIED | Webhook at POST /webhook/telegram; `_notify_master()` sends on create/cancel/reschedule |
| MSG-02 | 02-03, 02-04 | Telegram Mini App -- client booking, master management | SATISFIED | 5-step client booking flow + 6-screen master management panel |
| MSG-07 | 02-03 | Unified React Mini App code with platform detection (TG/MAX/VK bridge adapters) | SATISFIED | PlatformBridge interface + TelegramAdapter + StubAdapter; context.tsx detects platform |
| MSG-08 | 02-02 | Messenger Adapter pattern on backend (unified notification router) | SATISFIED | MessengerAdapter ABC + TelegramAdapter + NotificationService with `register_adapter()` |
| INFR-03 | 02-02 | Webhook handlers for TG, MAX, VK bots | PARTIALLY SATISFIED | TG webhook handler fully implemented. MAX and VK webhook handlers are Phase 5 scope -- not expected in Phase 2 |

**Note on INFR-03:** The requirement is marked complete in REQUIREMENTS.md traceability table ("Phase 2, Complete"). Reviewing the actual requirement text: "Webhook handlers for TG, MAX, VK bots" -- this maps to Phase 5 (MAX/VK) as well. The TG webhook handler is complete; MAX/VK are intentionally deferred to Phase 5. The REQUIREMENTS.md marking it as "Complete" for Phase 2 appears to mean the TG portion is done. This is consistent with the plan's intent.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/pages/master/Settings.tsx` | 63 | `const bookingLink = \`${window.location.origin}/book/me\`` -- hardcoded "/book/me" instead of actual master ID | Warning | Share link in settings shows wrong URL; master has no way to know their ID from this page |
| `backend/app/bots/telegram/handlers/start.py` | 45-75 | Russian strings encoded as Unicode escapes (e.g. `\u0421 \u0432\u043e\u0437\u0432\u0440\u0430\u0449\u0435\u043d\u0438\u0435`) | Info | Functionally correct; makes code harder to read and review but does not affect behavior |
| Tests (all) | - | No Docker run record: all 58 backend tests and 12 frontend tests were NOT executed -- code was AST-verified only | Blocker | Cannot confirm passing test suite without runtime execution |

**Blocker explanation:** Both summaries (02-01, 02-02) note that Docker was unavailable during execution and tests were AST-parsed but not run. The test files are substantive (58 total backend test functions), but the verification cannot confirm they actually pass against the database and application code without execution.

### Human Verification Required

#### 1. Full Backend Test Suite

**Test:** `docker compose exec api uv run pytest tests/ -x -v --tb=short`
**Expected:** 58 tests pass across 7 test files (services:7, schedule:9, bookings:10, clients:4, auth_tg:4, settings:4, bot:20) plus existing auth/RLS/health tests
**Why human:** Tests were written and AST-verified but Docker was not available on the dev machine during both Plan 01 and Plan 02 executions. This is the most critical gap -- the slot calculation, double-booking prevention, TG HMAC validation, and notification pattern all have test coverage that must be confirmed running.

#### 2. Frontend Test Suite

**Test:** `cd frontend && pnpm test`
**Expected:** 12 vitest tests pass (formatPrice:4, formatDuration:4, formatDate:2, formatTime:1)
**Why human:** pnpm test was not explicitly run during Plan 03 execution (only pnpm build was confirmed). Test file exists and is substantive (12 `it()` assertions verified in code).

#### 3. Client Booking Flow (Visual + Functional)

**Test:** Start Docker stack; open `http://localhost:3000/book/{MASTER_ID}` in browser at 360px viewport
**Expected:**
- Step 1: Service cards with emoji, name, duration, price in Russian; accent border on selection; skeleton loading states
- Step 2: Calendar with Russian month names, Monday-first week, past dates disabled; accent circle on selected date
- Step 3: 3-column slot grid with 48px cells; empty state "Нет свободного времени" if no slots
- Step 4: Name + phone form with +7 prefix auto-fill; validation errors on empty submit
- Step 5: Checkmark animation (scale-in 400ms), booking summary card, "Мастер получил уведомление"
- Inter font, #6C5CE7 accent color, all 44px touch targets
**Why human:** Visual rendering, animation, Russian copy, and mobile layout cannot be verified from source code alone.

#### 4. Master Management Panel (Visual + Functional)

**Test:** Open `http://localhost:3000/master/dashboard` in browser
**Expected:**
- Bottom tab bar with 5 tabs; CalendarDays/BookOpen/Scissors/Users/Settings icons; accent color + label on active tab; aria-labels on inactive tabs
- Dashboard shows today's bookings; empty state "Сегодня записей нет" when no bookings
- Settings screen: pill selectors for buffer/deadline/interval pre-populate from GET /settings; save calls PUT /settings; toast "Настройки сохранены" on success
- Services CRUD: add service form validates required name; delete shows ConfirmDialog bottom sheet
**Why human:** Tab icon rendering, active state accent, pill selector UI, bottom sheet animation, and settings persistence require browser verification.

#### 5. Telegram Bot End-to-End

**Test:** Configure real TG bot token + ngrok/VPS webhook; send /start, /start MASTER_ID, /today, /link; create a booking and verify TG notification
**Expected:**
- /start without args: creates master, sends welcome message with "Открыть панель" WebAppInfo button
- /start MASTER_ID: validates UUID, finds master, sends "Записаться" WebAppInfo button with correct mini_app_url
- /today: shows today's bookings formatted with times and client names in master's timezone
- /link: returns `t.me/{bot}?start={master_id}` formatted deep link
- Booking creation: master receives notification within 2 seconds via TG bot
**Why human:** Requires live Telegram API connection, real bot token, and webhook registration -- not reproducible from code inspection alone.

## Summary

### What Is Verified

All four plans (02-01 through 02-04) are substantively implemented. Every artifact in every plan's `must_haves` section exists on disk and is substantive -- no stubs or placeholder returns were found. All key wiring links are confirmed: the booking service calls client_service for auto-population, the notification_service is called fire-and-forget on booking create/cancel/reschedule, the TG adapter is registered with the notification_service, the frontend booking flow store is wired to all 5 booking pages, and the master auth store correctly calls POST /auth/tg.

The 13 required phase requirements (BOOK-01 through BOOK-06, CLNT-01, CLNT-03, MSG-01, MSG-02, MSG-07, MSG-08, INFR-03) are all satisfied. The one note on INFR-03 is that MAX/VK webhook handlers are correctly deferred to Phase 5 -- the TG webhook portion is complete.

The one notable code issue (settings page showing `/book/me` instead of the real master ID deep link) is a warning-level cosmetic bug, not a blocking gap.

### What Needs Human Confirmation

The phase cannot be declared fully passed because:

1. **No test run on record** -- 58 backend tests and 12 frontend tests were AST-verified but never executed due to Docker unavailability during development. These must be run before Phase 3 starts.

2. **Visual/UX verification** -- The mini-app visual design, animation, Russian copy rendering, and touch target sizes require browser inspection.

3. **Telegram bot live test** -- The notification and command handler flows require a real TG bot token and webhook endpoint.

---

_Verified: 2026-03-17T18:00:00Z_
_Verifier: Claude (gsd-verifier)_
