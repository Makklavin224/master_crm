---
phase: 18-critical-fixes
plan: 01
subsystem: api, ui
tags: [fastapi, pydantic, react, antd, qrcode, telegram, deeplink]

# Dependency graph
requires: []
provides:
  - "bot_username field in ProfileSettings backend schema and API"
  - "tg_bot_username config field for TG_BOT_USERNAME env var"
  - "Dual QR codes in SettingsPage: web link + TG deeplink"
  - "Copy buttons for each link type"
affects: [frontend-settings, telegram-miniapp, deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config-driven bot username (TG_BOT_USERNAME env var) passed to frontend via API"
    - "Dual link pattern: web URL for browser + TG deeplink for Telegram camera"

key-files:
  created: []
  modified:
    - "backend/app/core/config.py"
    - "backend/app/schemas/settings.py"
    - "backend/app/api/v1/settings.py"
    - "web/src/api/settings.ts"
    - "web/src/pages/SettingsPage.tsx"

key-decisions:
  - "bot_username sourced from config (env var), not derived from bot token at runtime"
  - "TG deeplink uses master UUID as startapp parameter for mini-app routing"
  - "TG QR card conditionally rendered only when bot_username is configured"

patterns-established:
  - "Config field pattern: add to Settings class, expose via API schema, consume in frontend"

requirements-completed: [QRFIX-01, QRFIX-02, QRFIX-03]

# Metrics
duration: 2min
completed: 2026-03-21
---

# Phase 18 Plan 01: QR Code Fix Summary

**Dual QR codes in settings: web URL for browsers + TG deeplink (t.me/bot?startapp=masterid) for Telegram camera scanning**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T10:25:21Z
- **Completed:** 2026-03-21T10:27:29Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Backend returns bot_username from TG_BOT_USERNAME env var in profile settings API
- SettingsPage MyPageTab shows two separate cards: web link with QR and TG deeplink with QR
- Each card has its own copy button and descriptive helper text
- TG deeplink card only renders when bot_username is configured (graceful degradation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add bot_username to backend profile settings API** - `1b4a764` (feat)
2. **Task 2: Dual QR codes and links in SettingsPage MyPageTab** - `5fb9061` (feat)

## Files Created/Modified
- `backend/app/core/config.py` - Added tg_bot_username config field
- `backend/app/schemas/settings.py` - Added bot_username to ProfileSettings schema
- `backend/app/api/v1/settings.py` - Return bot_username from config in get/update endpoints
- `web/src/api/settings.ts` - Added bot_username to ProfileSettings TypeScript interface
- `web/src/pages/SettingsPage.tsx` - Rewrote MyPageTab with dual QR codes (web + TG deeplink)

## Decisions Made
- bot_username is sourced from a dedicated TG_BOT_USERNAME env var rather than being derived from the bot token at runtime -- simpler and more explicit
- TG deeplink uses master UUID (profile.id) as the startapp parameter, matching the existing mini-app routing pattern
- TG deeplink card is conditionally rendered only when bot_username is configured, so the UI degrades gracefully if env var is not set

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

**Environment variable needed:** Set `TG_BOT_USERNAME` in `.env` (or production environment) to the bot username without `@` (e.g., `MoiOkoshkiBot`). Without this, only the web link QR code will be shown.

## Next Phase Readiness
- QR code fix complete, ready for remaining critical fixes in 18-02
- Deployment requires TG_BOT_USERNAME env var to be set for TG deeplink to appear

## Self-Check: PASSED

All 5 modified files exist. Both task commits (1b4a764, 5fb9061) verified in git log.

---
*Phase: 18-critical-fixes*
*Completed: 2026-03-21*
