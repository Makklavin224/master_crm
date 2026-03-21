---
phase: 17-cross-platform-auth-role-detection
plan: 01
subsystem: auth, api
tags: [fastapi, jwt, telegram, max, platform-linking, bot-handlers]

# Dependency graph
requires:
  - phase: 05-multi-messenger-expansion
    provides: Multi-messenger Master model columns (tg_user_id, max_user_id, vk_user_id)
  - phase: 06-web-admin-panel
    provides: Web admin auth (email/password registration, JWT)
provides:
  - GET /settings/platforms -- platform connection status API
  - DELETE /settings/platforms/{platform} -- platform unlink API
  - POST /auth/bot-register -- passwordless master creation from bot
  - POST /auth/link-account -- link existing master to messenger platform
  - TG/MAX bot link_account conversational flow (email-based lookup)
  - register_master_from_bot service helper
affects: [17-02-PLAN, frontend-settings, mini-app-role-detection]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PLATFORM_COLUMN_MAP dict for platform-to-column mapping (telegram->tg_user_id, max->max_user_id, vk->vk_user_id)"
    - "Module-level _pending_link_email dict for conversational state tracking in bot handlers"

key-files:
  created: []
  modified:
    - backend/app/schemas/settings.py
    - backend/app/schemas/auth.py
    - backend/app/services/auth_service.py
    - backend/app/api/v1/settings.py
    - backend/app/api/v1/auth.py
    - backend/app/bots/telegram/handlers/start.py
    - backend/app/bots/telegram/handlers/callbacks.py
    - backend/app/bots/max/handlers/start.py
    - backend/app/bots/max/handlers/callbacks.py
    - backend/app/bots/max/bot.py

key-decisions:
  - "Bot registration creates Master without password (can set password later via web admin)"
  - "Account linking uses email lookup (not phone) since web-registered masters always have email"
  - "Link-email handler registered before review-text handler in MAX message router to prevent conflict"

patterns-established:
  - "PLATFORM_COLUMN_MAP: centralized platform-to-column mapping reused across auth_service, settings API, and auth API"
  - "_pending_link_email module-level dict: same pattern as _pending_review_text for conversational state"

requirements-completed: [XAUTH-01, XAUTH-03, XAUTH-05]

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 17 Plan 01: Cross-Platform Auth Backend Summary

**Platform link/unlink API + bot account linking flow with email-based master recognition for TG and MAX**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-21T09:14:22Z
- **Completed:** 2026-03-21T09:20:35Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Platform status API (GET /settings/platforms) and unlink endpoint (DELETE /settings/platforms/{platform}) for web admin
- Bot registration endpoint (POST /auth/bot-register) creates passwordless Master with platform binding
- Account linking endpoint (POST /auth/link-account) binds existing master to messenger via email lookup
- TG and MAX bots show "Привязать существующий аккаунт" button for unrecognized users alongside register button
- Conversational link-account flow: user enters email, bot looks up Master, links platform_user_id, shows master keyboard

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend platform link/unlink API + bot registration endpoint** - `bf7fb07` (feat)
2. **Task 2: Bot handlers -- master recognition, account linking, registration flow** - `3b18764` (feat)

## Files Created/Modified
- `backend/app/schemas/settings.py` - Added PlatformStatus and PlatformUnlinkResponse models
- `backend/app/schemas/auth.py` - Added BotRegisterRequest and LinkAccountRequest models
- `backend/app/services/auth_service.py` - Added register_master_from_bot helper and PLATFORM_COLUMN_MAP
- `backend/app/api/v1/settings.py` - Added GET /settings/platforms and DELETE /settings/platforms/{platform}
- `backend/app/api/v1/auth.py` - Added POST /auth/bot-register and POST /auth/link-account
- `backend/app/bots/telegram/handlers/start.py` - Added link_account button to unrecognized user keyboard
- `backend/app/bots/telegram/handlers/callbacks.py` - Added link_account callback, email text handler, _build_master_keyboard
- `backend/app/bots/max/handlers/start.py` - Added link_account button to unrecognized user keyboard
- `backend/app/bots/max/handlers/callbacks.py` - Added _cb_link_account, handle_link_email_message, _master_buttons_for_linked
- `backend/app/bots/max/bot.py` - Wired handle_link_email_message into message router

## Decisions Made
- Bot registration creates Master without password -- masters can set password later via web admin settings
- Account linking uses email lookup (not phone) since web-registered masters always have email set
- Link-email message handler is checked before review-text handler in MAX message router to prevent state conflicts
- Register callback now shows email hint ("Рекомендуем добавить email в настройках для входа через веб-панель")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Backend platform linking infrastructure complete, ready for 17-02 (mini-app role detection + web admin platforms tab)
- All API endpoints exist for frontend consumption: /settings/platforms, /auth/bot-register, /auth/link-account
- Bot handlers support both new registration and existing account linking flows

## Self-Check: PASSED

All 10 modified files verified present. Both task commits (bf7fb07, 3b18764) verified in git log.

---
*Phase: 17-cross-platform-auth-role-detection*
*Completed: 2026-03-21*
