---
phase: 18-critical-fixes
plan: 02
subsystem: auth, ui
tags: [zustand, localStorage, race-condition, null-safety, react-query, recharts]

# Dependency graph
requires:
  - phase: none
    provides: none
provides:
  - Race-condition-safe autoDetectRole with _detecting debounce guard
  - localStorage-persisted role preference (master_role_preference)
  - bridge.ready() call before role detection in RoleDetector
  - Null-safe analytics dashboard with empty state and error handling
affects: [19-high-priority-fixes, 20-medium-fixes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level _detecting guard for async singleton operations"
    - "Null-safe numeric coercion helper: const n = (v) => Number(v) || 0"
    - "Error state + retry button pattern for React Query hooks"

key-files:
  created: []
  modified:
    - frontend/src/stores/master-auth.ts
    - frontend/src/App.tsx
    - frontend/src/components/RoleSwitcher.tsx
    - web/src/pages/AnalyticsPage.tsx

key-decisions:
  - "Used module-level let _detecting instead of store state to avoid unnecessary re-renders on guard changes"
  - "Role preference defaults to 'master' when no saved preference exists (savedPref !== 'client')"
  - "RoleSwitcher visibility changed to isAuthenticated check instead of role === 'master' (deviation fix)"

patterns-established:
  - "Async guard pattern: module-level boolean + try/finally for singleton async operations"
  - "Empty state pattern: check data nullity after loading/error, show centered gray text"

requirements-completed: [ROLE-01, ROLE-02, ROLE-03, ANLTR-01, ANLTR-02, ANLTR-03]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 18 Plan 02: Role Detection Race Fix & Analytics Null Safety Summary

**Race-condition guard on autoDetectRole with localStorage role persistence; null-safe analytics with empty state placeholders and error retry buttons**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T10:25:31Z
- **Completed:** 2026-03-21T10:28:30Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- autoDetectRole protected by _detecting guard preventing double-call race condition
- Role preference (master/client toggle) persists in localStorage across app restarts
- bridge.ready() called before autoDetectRole ensuring platform bridge initialization
- Analytics dashboard crash-proof: all numeric values wrapped in null-safe helper n()
- Empty analytics shows "Net dannykh za period" placeholder instead of blank/crash
- API errors show "Oshibka zagruzki" with "Povtorit" retry button in both tabs

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix role detection race condition and localStorage persistence** - `feb96b0` (fix)
2. **Task 2: Analytics page null safety, empty state, and error handling** - `bd7acd0` (fix)

## Files Created/Modified
- `frontend/src/stores/master-auth.ts` - Added _detecting guard, ROLE_PREF_KEY, localStorage persistence in setRole, getSavedRole in autoDetectRole
- `frontend/src/App.tsx` - Added bridge.ready() call before autoDetectRole in RoleDetector useEffect
- `frontend/src/components/RoleSwitcher.tsx` - Changed visibility condition from role=master to isAuthenticated
- `web/src/pages/AnalyticsPage.tsx` - Added n() helper, isError/refetch destructuring, empty state, error state with retry button, conditional chart rendering

## Decisions Made
- Used module-level `let _detecting` instead of Zustand store state to avoid re-renders on guard flag changes
- Role preference defaults to "master" when no localStorage value exists (only explicit "client" overrides)
- Changed RoleSwitcher visibility from `role !== "master"` to `!isAuthenticated || role === "detecting"` (deviation -- see below)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed RoleSwitcher disappearing when master switches to client view**
- **Found during:** Task 1 (RoleSwitcher verification)
- **Issue:** RoleSwitcher rendered only when `role === "master"`, but switching to client view sets `role = "client"`, causing the switcher to disappear. Master would have no way to switch back to panel view.
- **Fix:** Changed visibility condition to `!isAuthenticated || role === "detecting"` so the switcher remains visible for all authenticated users regardless of current role view.
- **Files modified:** frontend/src/components/RoleSwitcher.tsx
- **Verification:** Code review confirms switcher visible in both master and client views for authenticated users
- **Committed in:** feb96b0 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for role switching to actually work. Without this, localStorage persistence would save the preference but the user couldn't toggle back. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Role detection and analytics critical fixes are complete
- Ready for phase 18 plan 01 (if not yet executed) or phase 19 (high-priority fixes)

## Self-Check: PASSED

- All 4 modified files exist on disk
- Commit feb96b0 (Task 1) verified in git log
- Commit bd7acd0 (Task 2) verified in git log
- All 6 plan verification grep checks pass

---
*Phase: 18-critical-fixes*
*Completed: 2026-03-21*
