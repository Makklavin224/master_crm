---
phase: 20-error-handling-ux
plan: 01
subsystem: api
tags: [fetch, abort-controller, timeout, error-handling, i18n-russian]

# Dependency graph
requires:
  - phase: 19-high-priority-fixes
    provides: API client functions across all three frontends
provides:
  - 30-second AbortController timeout on all API request functions
  - Russian-only error messages across all frontend surfaces
affects: [all frontend API consumers, error display components]

# Tech tracking
tech-stack:
  added: []
  patterns: [AbortController timeout with AbortSignal.any merge, Russian-only error strings]

key-files:
  created: []
  modified:
    - web/src/api/client.ts
    - frontend/src/api/client.ts
    - public/src/api/client.ts
    - frontend/src/stores/master-auth.ts
    - web/src/stores/auth.ts
    - web/src/pages/LoginPage.tsx

key-decisions:
  - "AbortSignal.any used with typeof guard for caller signal merging (graceful degradation)"
  - "Timeout set to 30 seconds as specified -- covers slow API without interrupting file uploads"

patterns-established:
  - "API timeout pattern: AbortController + 30s setTimeout + finally clearTimeout + AbortError catch"
  - "All user-facing error messages must be in Russian"

requirements-completed: [ERRH-02, ERRH-03]

# Metrics
duration: 2min
completed: 2026-03-21
---

# Phase 20 Plan 01: Error Handling UX Summary

**30s AbortController timeout on all 4 API functions with AbortSignal.any merge, plus full English-to-Russian error message migration across all three frontends**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T10:43:55Z
- **Completed:** 2026-03-21T10:46:03Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- All 4 API request functions (web apiRequest, frontend apiRequest, public apiRequest, masterApiRequest) now abort after 30 seconds with Russian timeout error
- AbortSignal.any merges caller-provided signals with timeout signal, with typeof guard for browser compatibility
- Zero English error messages remain across all three frontends (web admin, mini-app, public site)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add AbortController 30s timeout to all 4 API request functions** - `a0eeae1` (feat)
2. **Task 2: Replace all English error messages with Russian** - `521c881` (fix)

## Files Created/Modified
- `web/src/api/client.ts` - Added AbortController timeout + signal merge + Russian "Ошибка сети" fallback
- `frontend/src/api/client.ts` - Added AbortController timeout + signal merge (already had Russian errors)
- `public/src/api/client.ts` - Added AbortController timeout + signal merge (already had Russian errors)
- `frontend/src/stores/master-auth.ts` - Added AbortController timeout to masterApiRequest + Russian auth errors
- `web/src/stores/auth.ts` - "Login failed" -> "Не удалось войти", "Network error" -> "Ошибка сети"
- `web/src/pages/LoginPage.tsx` - "Failed to create QR session" -> "Не удалось создать QR-сессию"

## Decisions Made
- Used AbortSignal.any with typeof guard -- supported in modern browsers, gracefully falls back to timeout-only signal
- Timeout error uses status code 0 to distinguish from HTTP errors in ApiError

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Fixed additional English error messages in master-auth.ts**
- **Found during:** Task 2 (Russian error message replacement)
- **Issue:** Plan listed 5 English strings to replace but master-auth.ts login() had 2 more: "Auth error" (line 84) and "Auth failed" (line 102) not in the plan's list
- **Fix:** Replaced "Auth error" -> "Ошибка авторизации" and "Auth failed" -> "Не удалось авторизоваться"
- **Files modified:** frontend/src/stores/master-auth.ts
- **Verification:** grep for English error strings returns 0 results
- **Committed in:** 521c881 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for complete Russian error coverage. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All API clients now have consistent timeout and Russian error handling
- Ready for 20-02 plan execution

---
*Phase: 20-error-handling-ux*
*Completed: 2026-03-21*
