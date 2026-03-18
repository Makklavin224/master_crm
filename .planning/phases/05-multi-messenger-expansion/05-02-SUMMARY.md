---
phase: 05-multi-messenger-expansion
plan: 02
subsystem: bot, api, frontend
tags: [max, httpx, messenger-adapter, platform-bridge, webhook, multi-platform, booking-generalization]

# Dependency graph
requires:
  - phase: 05-multi-messenger-expansion/01
    provides: "Shared backend config (MAX settings), validation, Master model columns (max_user_id), auth endpoints"
  - phase: 04-notifications
    provides: "NotificationService, MessengerAdapter ABC, TelegramAdapter reference implementation"
provides:
  - "MaxAdapter implementing all 6 MessengerAdapter methods via httpx"
  - "MAX bot handlers for bot_started, /start, /today, /link, message_callback events"
  - "process_max_update webhook router for MAX updates"
  - "/webhook/max FastAPI endpoint with secret header validation"
  - "MAX webhook subscription in lifespan startup"
  - "createMaxBridge() PlatformBridge adapter for MAX mini-app"
  - "MAX platform detection in detectPlatform()"
  - "Generic platform_user_id field in BookingCreate (replaces tg_user_id)"
  - "Multi-platform master notifications (_notify_master sends to all registered platforms)"
  - "CLNT-04: ClientPlatform creation for any platform via booking flow"
affects: [05-multi-messenger-expansion/03]

# Tech tracking
tech-stack:
  added: [max-web-app.js CDN]
  patterns: [httpx-based bot API calls (no framework dispatcher), raw JSON webhook processing, multi-platform notification fan-out]

key-files:
  created:
    - backend/app/bots/max/__init__.py
    - backend/app/bots/max/adapter.py
    - backend/app/bots/max/bot.py
    - backend/app/bots/max/handlers/__init__.py
    - backend/app/bots/max/handlers/start.py
    - backend/app/bots/max/handlers/today.py
    - backend/app/bots/max/handlers/link.py
    - backend/app/bots/max/handlers/callbacks.py
    - frontend/src/platform/adapters/max.ts
  modified:
    - backend/app/main.py
    - backend/app/schemas/booking.py
    - backend/app/services/booking_service.py
    - backend/app/api/v1/bookings.py
    - frontend/src/api/bookings.ts
    - frontend/src/pages/client/BookingForm.tsx
    - frontend/src/pages/client/MyBookings.tsx
    - frontend/src/platform/detect.ts
    - frontend/src/platform/context.tsx
    - frontend/index.html

key-decisions:
  - "httpx.AsyncClient for MAX API calls (no maxapi Dispatcher to avoid server conflict with FastAPI)"
  - "Generic platform_user_id replaces tg_user_id in BookingCreate schema for multi-platform support"
  - "_notify_master fans out to all registered platforms (TG+MAX+VK) instead of hardcoded Telegram"
  - "MAX expand() is no-op in bridge adapter (MAX Bridge has no expand API)"
  - "MAX detection checks window.WebApp.initData after Telegram check (order matters -- TG sets window.Telegram.WebApp, MAX sets window.WebApp directly)"

patterns-established:
  - "httpx bot API pattern: async with httpx.AsyncClient for each MAX API call with access_token= auth header"
  - "Raw JSON handler pattern: async functions receiving (body: dict, db: AsyncSession, token: str) instead of framework decorators"
  - "Multi-platform notification fan-out: iterate master platform IDs and send via each registered adapter"

requirements-completed: [MSG-03, MSG-04, CLNT-04]

# Metrics
duration: 11min
completed: 2026-03-18
---

# Phase 5 Plan 2: MAX Integration + Multi-Platform Booking Summary

**MAX bot module with httpx adapter (6 notification methods), webhook handlers (/start, /today, /link, callbacks), frontend MaxBridge adapter, and generalized platform_user_id booking flow enabling CLNT-04 for all messengers**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-18T12:37:39Z
- **Completed:** 2026-03-18T12:48:39Z
- **Tasks:** 3
- **Files modified:** 19

## Accomplishments
- MaxAdapter implements all 6 MessengerAdapter methods (send_booking_notification, send_message, send_payment_link, send_payment_requisites, send_reminder, send_booking_confirmation) using httpx + MAX Bot API
- MAX bot handlers process bot_started, /start (with deep link), /today, /link, and callback events -- master registration creates master with max_user_id
- Booking flow generalized: tg_user_id renamed to platform_user_id across backend schema, service, API, and frontend -- any platform's getUserId() now creates correct ClientPlatform entry
- Master notifications fan out to all registered platforms (TG, MAX, VK) instead of only Telegram

## Task Commits

Each task was committed atomically:

1. **Task 1: MAX backend bot module -- adapter, bot singleton, handlers** - `2348bb6` (feat)
2. **Task 2: MAX webhook route + frontend bridge adapter + platform detection** - `4e529c7` (feat)
3. **Task 3: Generalize booking flow for multi-platform ClientPlatform creation** - `f4acd54` (feat)

## Files Created/Modified
- `backend/app/bots/max/adapter.py` - MaxAdapter with all 6 notification methods via httpx
- `backend/app/bots/max/bot.py` - Module singleton, adapter registration, process_max_update router
- `backend/app/bots/max/handlers/start.py` - bot_started + /start handlers with deep link support
- `backend/app/bots/max/handlers/today.py` - /today handler with format_today_bookings_text
- `backend/app/bots/max/handlers/link.py` - /link handler generating MAX deep links
- `backend/app/bots/max/handlers/callbacks.py` - Callback router for today, link, booking, cancel, cancel_client, my_bookings
- `backend/app/main.py` - Added MAX webhook endpoint and lifespan webhook registration
- `frontend/src/platform/adapters/max.ts` - createMaxBridge() wrapping window.WebApp
- `frontend/src/platform/detect.ts` - MAX detection via window.WebApp.initData
- `frontend/src/platform/context.tsx` - MAX case in PlatformProvider switch
- `frontend/index.html` - max-web-app.js CDN script
- `backend/app/schemas/booking.py` - tg_user_id renamed to platform_user_id
- `backend/app/services/booking_service.py` - platform_user_id param + multi-platform _notify_master
- `backend/app/api/v1/bookings.py` - platform_user_id in endpoint call
- `frontend/src/api/bookings.ts` - platform_user_id in BookingCreate + useMyBookings
- `frontend/src/pages/client/BookingForm.tsx` - source_platform: platform.platform, platform_user_id: getUserId()
- `frontend/src/pages/client/MyBookings.tsx` - userId variable rename for clarity

## Decisions Made
- Used httpx.AsyncClient for MAX API calls instead of maxapi Dispatcher to avoid server conflicts with FastAPI
- Renamed tg_user_id to platform_user_id for generic multi-platform booking support
- Enhanced _notify_master to fan out notifications to all platforms master is registered on
- MAX expand() implemented as no-op (MAX Bridge lacks this API)
- MAX platform detection ordered after Telegram but before VK (TG uses window.Telegram.WebApp, MAX uses window.WebApp directly)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Multi-platform master notification fan-out**
- **Found during:** Task 3 (booking flow generalization)
- **Issue:** _notify_master hardcoded Telegram-only notifications (master.tg_user_id + "telegram" adapter). Masters registered via MAX would never receive booking notifications.
- **Fix:** Changed _notify_master to collect all platform IDs (tg_user_id, max_user_id, vk_user_id) and send notifications via each registered adapter
- **Files modified:** backend/app/services/booking_service.py
- **Verification:** Import check passes, logic review confirms fan-out
- **Committed in:** f4acd54 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical functionality)
**Impact on plan:** Essential for correctness -- without this fix, MAX-registered masters would never receive booking notifications. No scope creep.

## Issues Encountered
- VK plan (05-03) was already executed and committed before this plan, so main.py/detect.ts/context.tsx already contained VK additions. MAX changes layered cleanly on top with no conflicts.
- Test suite fails with DNS resolution error (database not running locally) -- pre-existing infrastructure issue, not caused by our changes.

## User Setup Required

External services require manual configuration. The plan's user_setup section specifies:
- **MAX_BOT_TOKEN**: From MAX Partners -> Chatbots -> Your Bot -> Token
- **MAX_WEBHOOK_SECRET**: Random secret string for webhook validation
- **MAX_BOT_USERNAME**: From MAX Partners -> Chatbots -> Your Bot -> Username (without @)
- Register bot on MAX Partners platform (requires verified legal entity)
- Create MAX Mini App linked to bot

## Next Phase Readiness
- MAX integration complete -- bot receives webhooks, handlers process events, adapter sends notifications
- Frontend detects MAX platform and provides bridge adapter
- Booking flow is now platform-agnostic (CLNT-04 complete for all platforms)
- Ready for VK integration (Plan 05-03) or Phase 6

## Self-Check: PASSED

All 9 created files verified present. All 3 task commits verified in git log.

---
*Phase: 05-multi-messenger-expansion*
*Completed: 2026-03-18*
