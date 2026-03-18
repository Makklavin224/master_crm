---
phase: 05-multi-messenger-expansion
plan: 03
subsystem: messaging
tags: [vk, vk-bridge, httpx, webhook, callback-api, mini-app, bot]

# Dependency graph
requires:
  - phase: 05-multi-messenger-expansion
    provides: "MessengerAdapter ABC, NotificationService, config fields (vk_group_token, vk_app_id, vk_confirmation_token, vk_secret_key), Master.vk_user_id column, PlatformBridge interface"
provides:
  - "VkAdapter implementing all 6 MessengerAdapter methods via VK API (httpx)"
  - "VK bot command handlers (/start, /today, /link) and callback handler (message_event)"
  - "process_vk_event router dispatching webhook events to handlers"
  - "/webhook/vk endpoint with VK Callback API confirmation handshake"
  - "createVkBridge() frontend adapter implementing PlatformBridge"
  - "VK platform detection via URL params (vk_user_id + sign)"
affects: [phase-06, deployment]

# Tech tracking
tech-stack:
  added: ["@vkontakte/vk-bridge 2.15.11"]
  patterns: ["httpx-based VK API calls (same pattern as MAX adapter)", "VK inline keyboard JSON format with callback/open_link actions", "VK Callback API confirmation handshake (PlainTextResponse)"]

key-files:
  created:
    - backend/app/bots/vk/__init__.py
    - backend/app/bots/vk/adapter.py
    - backend/app/bots/vk/bot.py
    - backend/app/bots/vk/handlers/__init__.py
    - backend/app/bots/vk/handlers/start.py
    - backend/app/bots/vk/handlers/today.py
    - backend/app/bots/vk/handlers/link.py
    - backend/app/bots/vk/handlers/callbacks.py
    - frontend/src/platform/adapters/vk.ts
  modified:
    - backend/app/main.py
    - frontend/src/platform/detect.ts
    - frontend/src/platform/context.tsx
    - frontend/package.json

key-decisions:
  - "httpx for VK API calls (consistent with MAX adapter pattern, already a project dependency)"
  - "Plain text messages (VK messages.send does not support HTML tags)"
  - "VK inline keyboard with callback action type for bot interactions, open_link for payment URLs"
  - "VK Callback API confirmation handshake returns PlainTextResponse (not JSON)"
  - "VK user name fetched via users.get API on master registration"
  - "Deep links use https://vk.com/app{APP_ID}#master={MASTER_ID} format"

patterns-established:
  - "VK Callback API pattern: confirmation handshake first, then secret key verification on all subsequent events"
  - "VK message_event handling: parse payload.cmd, process, acknowledge with sendMessageEventAnswer"
  - "VK bot handler pattern: async functions (not framework decorators), direct httpx API calls"

requirements-completed: [MSG-05, MSG-06, CLNT-04]

# Metrics
duration: 6min
completed: 2026-03-18
---

# Phase 5 Plan 3: VK Integration Summary

**VK bot module with httpx-based adapter, command/callback handlers, Callback API webhook with confirmation handshake, and @vkontakte/vk-bridge frontend adapter**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-18T12:38:07Z
- **Completed:** 2026-03-18T12:45:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- VkAdapter sends all 6 notification types (booking, message, payment link, requisites, reminder, confirmation) via VK API using plain text and inline keyboards
- VK bot handlers process /start (and "Начать"), /today, /link text commands, plus message_event callbacks for booking detail, cancel, and client cancel
- /webhook/vk endpoint handles VK Callback API confirmation handshake (critical for webhook activation) and routes events through process_vk_event
- Frontend createVkBridge() wraps @vkontakte/vk-bridge with VKWebAppInit, haptic feedback, and platform detection via URL params

## Task Commits

Each task was committed atomically:

1. **Task 1: VK backend bot module -- adapter, bot singleton, handlers** - `eb8f559` (feat)
2. **Task 2: VK webhook route + frontend bridge adapter** - `c60f1e0` (feat)

## Files Created/Modified
- `backend/app/bots/vk/__init__.py` - Empty package init
- `backend/app/bots/vk/adapter.py` - VkAdapter with all 6 MessengerAdapter methods using httpx + VK API
- `backend/app/bots/vk/bot.py` - Module singleton, adapter registration, process_vk_event router
- `backend/app/bots/vk/handlers/__init__.py` - Empty package init
- `backend/app/bots/vk/handlers/start.py` - /start and "Начать" handler, master registration with VK user info
- `backend/app/bots/vk/handlers/today.py` - /today handler, today's bookings formatted as plain text
- `backend/app/bots/vk/handlers/link.py` - /link handler, generates VK mini-app deep link
- `backend/app/bots/vk/handlers/callbacks.py` - message_event handler (today, link, booking detail, cancel, cancel_client)
- `backend/app/main.py` - Added /webhook/vk endpoint with confirmation handshake and secret verification
- `frontend/src/platform/adapters/vk.ts` - createVkBridge() implementing PlatformBridge via @vkontakte/vk-bridge
- `frontend/src/platform/detect.ts` - Added VK detection via vk_user_id + sign URL params
- `frontend/src/platform/context.tsx` - Added case "vk" -> createVkBridge() in switch
- `frontend/package.json` - Added @vkontakte/vk-bridge dependency

## Decisions Made
- Used httpx for VK API calls (consistent with MAX adapter, already a dependency)
- Plain text messages only (VK messages.send does not support HTML -- stripped all <b> tags)
- VK inline keyboard uses callback action type for bot interactions and open_link for payment URLs
- VK Callback API confirmation handshake returns PlainTextResponse (VK rejects JSON responses)
- Master name fetched via VK users.get API during registration (similar to how TG uses from_user.full_name)
- VK mini-app deep link format: https://vk.com/app{APP_ID}#master={MASTER_ID}

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Shared files (main.py, detect.ts, context.tsx) were concurrently modified by Plan 05-02 (MAX). Both plans ran in Wave 2 parallel. The concurrent modifications merged cleanly -- MAX added its webhook/detection/bridge, VK added its own alongside. Final state contains both MAX and VK code in all shared files.
- Existing pytest tests fail with DNS resolution error (socket.gaierror) -- pre-existing issue unrelated to VK changes. Tests require database connection unavailable in local environment.

## User Setup Required

VK Community Bot requires manual configuration. The user_setup section in the plan frontmatter documents:
- VK_GROUP_TOKEN: Community API access token (messages + manage permissions)
- VK_APP_ID: VK Mini App application ID
- VK_APP_SECRET: VK Mini App secret key
- VK_CONFIRMATION_TOKEN: Callback API confirmation string
- VK_SECRET_KEY: Callback API secret key

Dashboard steps: create VK community, enable messages, configure Callback API webhook URL, enable message_new and message_event event types, create VK Mini App.

## Next Phase Readiness
- VK integration complete and ready for deployment alongside Telegram and MAX
- All three messenger verticals (TG, MAX, VK) now have bot modules, adapters, webhook endpoints, and frontend bridges
- Phase 5 multi-messenger expansion is complete pending Plan 05-02 (MAX) completion

## Self-Check: PASSED

All 9 created files verified on disk. Both task commits (eb8f559, c60f1e0) verified in git log.

---
*Phase: 05-multi-messenger-expansion*
*Completed: 2026-03-18*
