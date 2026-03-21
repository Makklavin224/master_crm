---
phase: 19-high-priority-fixes
plan: 01
subsystem: auth, bots
tags: [fastapi, cookie, bearer-token, samesite, telegram-bot, max-bot, otp]

# Dependency graph
requires:
  - phase: 18-critical-fixes
    provides: "QR code fix, role detection race fix"
provides:
  - "Dual-path client auth: cookie + Bearer token fallback"
  - "SameSite=None cross-origin cookie for webviews"
  - "Plain Russian strings in bot registration/linking handlers"
affects: [19-02, 20-medium-fixes, client-cabinet, mini-app]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-path auth: cookie first, Bearer fallback"
    - "SameSite=None + Secure for cross-origin cookies"

key-files:
  created: []
  modified:
    - backend/app/api/v1/client_auth.py
    - backend/app/core/dependencies.py
    - backend/app/bots/telegram/handlers/callbacks.py
    - backend/app/bots/max/handlers/callbacks.py

key-decisions:
  - "SameSite=None for cross-origin cookie support in mobile webviews"
  - "Cookie-first, Bearer-fallback auth strategy for get_current_client"

patterns-established:
  - "Dual-path auth: try cookie, fallback to Authorization Bearer header"
  - "Plain UTF-8 Russian strings in bot messages (no unicode escapes)"

requirements-completed: [BREG-01, BREG-02, BREG-03, CAUTH-01, CAUTH-03]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 19 Plan 01: High-Priority Fixes Summary

**Dual-path client auth (cookie + Bearer fallback) with SameSite=None cross-origin cookie, and plain Russian strings in TG/MAX bot registration handlers**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T10:31:37Z
- **Completed:** 2026-03-21T10:36:17Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Fixed `status` import bug in client_auth.py (was using `status.HTTP_503_SERVICE_UNAVAILABLE` without importing `status`)
- Changed SameSite from "lax" to "none" for cross-origin cookie support in mobile webviews and different subdomains
- Added Bearer token fallback to `get_current_client` -- tries cookie first, then Authorization header
- Replaced Unicode escape sequences with plain UTF-8 Russian in TG and MAX bot registration/linking/keyboard handlers

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix client_auth.py -- dual-path token delivery + status import bug** - `7e1c552` (fix)
2. **Task 2: Fix get_current_client -- accept cookie OR Bearer token** - `5f3b280` (fix)
3. **Task 3: Audit and harden bot registration handlers (TG + MAX)** - `5730acd` (fix)

## Files Created/Modified
- `backend/app/api/v1/client_auth.py` - Added `status` to imports, changed SameSite to "none"
- `backend/app/core/dependencies.py` - Added Bearer token fallback in get_current_client
- `backend/app/bots/telegram/handlers/callbacks.py` - Plain Russian in registration/linking/keyboard
- `backend/app/bots/max/handlers/callbacks.py` - Plain Russian in registration/linking/keyboard

## Decisions Made
- SameSite=None chosen for cross-origin support (webviews, subdomains); Secure=True already present as required
- Cookie-first auth preserves backward compatibility; Bearer fallback enables API clients/webviews where cookies are blocked

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Client auth dual-path ready for mini-app cross-origin scenarios
- Bot registration handlers clean and readable
- Ready for 19-02 (remaining high-priority fixes)

---
*Phase: 19-high-priority-fixes*
*Completed: 2026-03-21*
