---
phase: 17-cross-platform-auth-role-detection
plan: 02
subsystem: frontend, ui
tags: [react, zustand, role-detection, mini-app, platform-toggle, antd, react-query]

# Dependency graph
requires:
  - phase: 17-cross-platform-auth-role-detection
    provides: Platform link/unlink API, bot registration, auth endpoints for TG/MAX/VK
  - phase: 05-multi-messenger-expansion
    provides: Multi-platform bridge adapters (telegram, max, vk, web)
provides:
  - RoleDetector component auto-detecting master vs client on mini-app load
  - autoDetectRole function in master-auth store (platform-aware auth)
  - RoleSwitcher floating toggle for masters to switch between panel and client view
  - PlatformsTab in web admin Settings showing connected platforms with unlink
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "getAuthConfig helper maps platform to auth endpoint and body key"
    - "autoDetectRole replaces hydrate on app mount for platform-aware role detection"
    - "RoleSwitcher uses useLocation to determine current view and show correct toggle label"

key-files:
  created:
    - frontend/src/components/RoleSwitcher.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/stores/master-auth.ts
    - web/src/api/settings.ts
    - web/src/pages/SettingsPage.tsx

key-decisions:
  - "autoDetectRole checks localStorage first (instant if token exists), then tries platform auth"
  - "401/404 from auth endpoint treated as normal client detection (no error toast)"
  - "RoleSwitcher renders outside Routes so it appears on all pages for masters"
  - "Master with ?master= param still goes to booking flow (master acting as client for another master)"

patterns-established:
  - "MasterRole type: 'master' | 'client' | 'detecting' -- three-state role detection"
  - "Platform-to-auth mapping via getAuthConfig helper function"

requirements-completed: [XAUTH-02, XAUTH-03, XAUTH-04]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 17 Plan 02: Mini-App Role Detection + Web Platforms Tab Summary

**Auto-detecting master/client role on mini-app load with platform-aware auth, floating view toggle, and web admin platform management UI**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T09:24:34Z
- **Completed:** 2026-03-21T09:28:26Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Mini-app auto-detects master role via platform auth endpoint on load and navigates to /master/dashboard
- Clients (or unrecognized users) see booking flow / /my-bookings with no error shown
- Masters get a floating "Мои записи" / "Панель мастера" toggle pill to switch views
- Web admin Settings > Платформы tab shows TG/MAX/VK connection status with unlink buttons

## Task Commits

Each task was committed atomically:

1. **Task 1: Mini-app role auto-detection and master/client toggle** - `4aab047` (feat)
2. **Task 2: Web admin Settings -- Platforms tab** - `c6b81e7` (feat)

## Files Created/Modified
- `frontend/src/stores/master-auth.ts` - Added MasterRole type, autoDetectRole, setRole, getAuthConfig helper
- `frontend/src/components/RoleSwitcher.tsx` - New floating pill toggle for master/client view switching
- `frontend/src/App.tsx` - Replaced EntryRedirect with RoleDetector, added RoleSwitcher, removed standalone hydrate
- `web/src/api/settings.ts` - Added PlatformStatusResponse, usePlatformStatus, useUnlinkPlatform hooks
- `web/src/pages/SettingsPage.tsx` - Added PlatformsTab with platform status badges and unlink Popconfirm

## Decisions Made
- autoDetectRole checks localStorage first for instant detection if token exists, avoiding unnecessary API call
- 401/404 from auth endpoint treated as normal "not a master" signal -- no error toast or console logging
- RoleSwitcher placed outside Routes (after them) so it renders as overlay on all pages
- Master with ?master= query param navigates to booking flow (master acting as client for another master)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 17 complete -- all cross-platform auth and role detection features implemented
- Backend (17-01) + Frontend (17-02) fully integrated: platform linking, role detection, view toggle, platform management

## Self-Check: PASSED

All 5 files verified present. Both task commits (4aab047, c6b81e7) verified in git log.

---
*Phase: 17-cross-platform-auth-role-detection*
*Completed: 2026-03-21*
