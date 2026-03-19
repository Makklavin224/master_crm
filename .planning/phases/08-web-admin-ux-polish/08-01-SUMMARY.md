---
phase: 08-web-admin-ux-polish
plan: 01
subsystem: ui
tags: [antd, react, i18n, a11y, breadcrumb, dark-mode, react-query]

requires:
  - phase: 06-web-admin-panel
    provides: AdminLayout shell, StatusTag component, App.tsx routing
provides:
  - Plain UTF-8 Russian strings in StatusTag and AdminLayout menu items
  - Accessible dark mode toggle (SunOutlined/MoonOutlined + aria-label)
  - Breadcrumb navigation showing current page in header
  - Profile business_name display in header
  - Sidebar collapsed state persistence via localStorage
  - Per-route document.title for browser tab identification
  - QueryClient 5-minute default staleTime for smart caching
  - React Router navigate() for magic link callback (no full page reload)
affects: [08-web-admin-ux-polish]

tech-stack:
  added: []
  patterns:
    - "PAGE_TITLES map for route-to-label mapping (breadcrumb + document.title)"
    - "localStorage sidebar persistence with try/catch guards"

key-files:
  created: []
  modified:
    - web/src/components/StatusTag.tsx
    - web/src/layouts/AdminLayout.tsx
    - web/src/App.tsx

key-decisions:
  - "Used PAGE_TITLES const map for both breadcrumb and document.title to avoid duplication"
  - "Sidebar collapse key: admin_sidebar_collapsed (matches admin_token naming convention)"

patterns-established:
  - "PAGE_TITLES map: centralized route-to-label mapping reused by breadcrumb and document.title"
  - "localStorage guards: try/catch around all localStorage calls for SSR/privacy safety"

requirements-completed: [WCRT-03, WCRT-04, WAUX-01, WAUX-02, WAUX-06, WAUX-09, WAUX-10]

duration: 2min
completed: 2026-03-19
---

# Phase 8 Plan 1: Web Admin Global UX Summary

**Plain UTF-8 Russian strings in StatusTag/AdminLayout, accessible dark mode toggle, breadcrumb header with profile display, sidebar persistence, per-route page titles, and QueryClient 5-min staleTime**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-19T04:07:03Z
- **Completed:** 2026-03-19T04:08:57Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Replaced all Unicode escape sequences with plain UTF-8 Russian text in StatusTag and AdminLayout menu items
- Dark mode toggle now uses SunOutlined/MoonOutlined icons with descriptive aria-label for accessibility
- Header shows breadcrumb navigation (MasterCRM > current page) and profile business_name
- Sidebar collapsed state persists across page reloads via localStorage
- Each admin route sets a unique document.title (e.g. "Календарь -- MasterCRM")
- Magic link callback uses React Router navigate() instead of window.location.href
- QueryClient configured with 5-minute default staleTime and retry: 1

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix StatusTag UTF-8 strings + App.tsx magic link + QueryClient staleTime** - `e7680d9` (feat)
2. **Task 2: AdminLayout dark mode a11y, breadcrumb, profile, sidebar persist, page titles** - `a1d984c` (feat)

## Files Created/Modified
- `web/src/components/StatusTag.tsx` - Booking/payment status tags with plain Russian labels
- `web/src/App.tsx` - React Router magic link navigation + QueryClient 5-min staleTime
- `web/src/layouts/AdminLayout.tsx` - Admin shell with breadcrumb, profile, a11y toggle, sidebar persistence, page titles

## Decisions Made
- Used a centralized PAGE_TITLES map shared between breadcrumb rendering and document.title to avoid label duplication
- Sidebar collapse localStorage key named `admin_sidebar_collapsed` following the existing `admin_token` naming pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Global UI foundation complete: Russian strings, accessible controls, navigation breadcrumb, caching
- Ready for 08-02 (table/list page improvements) and 08-03 (form/detail page polish)

## Self-Check: PASSED

All 3 modified files exist. Both task commits verified (e7680d9, a1d984c). TypeScript compilation passes.

---
*Phase: 08-web-admin-ux-polish*
*Completed: 2026-03-19*
