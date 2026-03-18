---
phase: 06-web-admin-panel
plan: 02
subsystem: ui
tags: [fullcalendar, react, antd, tanstack-query, calendar, services, crud]

# Dependency graph
requires:
  - phase: 06-web-admin-panel/01
    provides: "Admin layout, auth store, API client, StatusTag, routes skeleton"
provides:
  - "CalendarPage with FullCalendar day/week/month views and booking events"
  - "BookingDrawer for booking detail display with cancel action"
  - "ServicesPage with CRUD table and ServiceModal form"
  - "TanStack Query hooks for bookings, services, and schedule APIs"
affects: [06-web-admin-panel/03]

# Tech tracking
tech-stack:
  added: ["@fullcalendar/core@6.1.20 (explicit dep)"]
  patterns: ["FullCalendar with TanStack Query data source", "Ant Design Table + Modal CRUD pattern", "Kopecks/rubles conversion at form boundary"]

key-files:
  created:
    - web/src/api/bookings.ts
    - web/src/api/services.ts
    - web/src/api/schedule.ts
    - web/src/pages/CalendarPage.tsx
    - web/src/pages/ServicesPage.tsx
    - web/src/components/BookingDrawer.tsx
    - web/src/components/ServiceModal.tsx
  modified:
    - web/src/App.tsx
    - web/package.json

key-decisions:
  - "FullCalendar core added as explicit dependency (pnpm strict mode requires it, not just transitive)"
  - "Booking calendar staleTime:0 (always refetch, consistent with mini-app pattern)"
  - "Services staleTime:60s (less volatile data, consistent with mini-app pattern)"
  - "AntApp wrapper added for App.useApp() message API in drawers/modals"
  - "Price displayed in rubles in UI, converted to/from kopecks at form boundary"

patterns-established:
  - "CRUD table pattern: Ant Design Table + Modal form with create/edit modes"
  - "Drawer pattern: side panel for entity detail with action buttons"
  - "Calendar-to-query bridge: datesSet callback updates filter state for useBookings"

requirements-completed: [WEB-01, WEB-03]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 6 Plan 2: Calendar & Services Pages Summary

**FullCalendar schedule view with day/week/month booking display, BookingDrawer detail panel, and ServicesPage CRUD table with modal form and kopecks conversion**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T16:21:08Z
- **Completed:** 2026-03-18T16:26:48Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- CalendarPage with FullCalendar rendering bookings as status-colored time blocks (purple/gold/green/red)
- BookingDrawer showing client details, phone link, service info, status tag, and cancel action
- ServicesPage with sortable table (name, duration, price, category, active status) and full CRUD
- ServiceModal handling both create and edit modes with automatic kopecks conversion
- TanStack Query hooks for bookings (with date range filter), services (CRUD), and schedule template

## Task Commits

Each task was committed atomically:

1. **Task 1: API hooks + CalendarPage + BookingDrawer** - `4c3612e` (feat)
2. **Task 2: ServicesPage + ServiceModal + route wiring** - `d942bcb` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `web/src/api/bookings.ts` - Booking TanStack Query hooks (useBookings, useCancelBooking, useCreateManualBooking)
- `web/src/api/services.ts` - Service TanStack Query hooks (useServices, useCreateService, useUpdateService, useDeleteService)
- `web/src/api/schedule.ts` - Schedule template and exceptions query hooks
- `web/src/pages/CalendarPage.tsx` - FullCalendar with day/week/month views, Russian locale, schedule-derived time bounds
- `web/src/pages/ServicesPage.tsx` - Ant Design Table with 6 columns, add/edit/delete actions
- `web/src/components/BookingDrawer.tsx` - Side drawer with booking details and cancel button
- `web/src/components/ServiceModal.tsx` - Modal form for service create/edit with kopecks conversion
- `web/src/App.tsx` - Added CalendarPage, ServicesPage routes, AntApp wrapper, removed PlaceholderPage

## Decisions Made
- Added @fullcalendar/core as explicit dependency (pnpm strict mode does not hoist transitive deps for type resolution)
- Wrapped App in AntApp provider to enable App.useApp() for message/notification APIs in child components
- Booking calendar uses staleTime:0 (always refetch to prevent stale slot display) matching mini-app pattern
- Price conversion at form boundary: display rubles in UI, store kopecks via multiply/divide by 100

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added @fullcalendar/core as explicit dependency**
- **Found during:** Task 1 (CalendarPage build)
- **Issue:** TypeScript could not resolve @fullcalendar/core types (pnpm strict mode, not hoisted from transitive deps)
- **Fix:** `pnpm add @fullcalendar/core@6.1.20`
- **Files modified:** web/package.json, web/pnpm-lock.yaml
- **Verification:** pnpm build succeeds
- **Committed in:** 4c3612e (Task 1 commit)

**2. [Rule 1 - Bug] Removed unused formatPrice variable**
- **Found during:** Task 1 (build verification)
- **Issue:** TS6133 error for unused `formatPrice` function in BookingDrawer
- **Fix:** Removed the unused function
- **Files modified:** web/src/components/BookingDrawer.tsx
- **Verification:** pnpm build succeeds
- **Committed in:** 4c3612e (Task 1 commit)

**3. [Rule 1 - Bug] Removed unused PlaceholderPage component**
- **Found during:** Task 2 (build verification)
- **Issue:** TS6133 error after all routes replaced with real pages
- **Fix:** Removed PlaceholderPage function from App.tsx
- **Files modified:** web/src/App.tsx
- **Verification:** pnpm build succeeds
- **Committed in:** d942bcb (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 2 bug)
**Impact on plan:** All auto-fixes necessary for build success. No scope creep.

## Issues Encountered
- Uncommitted files from Plan 01 (auth.ts profile fetching, settings.ts) found in working directory -- included in Task 1 commit since they were needed for complete functionality

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Calendar and Services pages complete, ready for Plan 03 (Settings/Schedule pages)
- All placeholder routes replaced with real components
- AntApp wrapper in place for future modal/drawer components

---
*Phase: 06-web-admin-panel*
*Completed: 2026-03-18*
