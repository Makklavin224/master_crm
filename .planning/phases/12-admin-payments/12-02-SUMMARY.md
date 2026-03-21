---
phase: 12-admin-payments
plan: 02
subsystem: payments, ui
tags: [csv-export, antd, react, fastapi, fullcalendar, streaming-response]

# Dependency graph
requires:
  - phase: 12-admin-payments
    plan: 01
    provides: PaymentListResponse with total_revenue, payment_method filter on history endpoint
  - phase: 02-booking-engine
    provides: BookingRead with booking IDs for calendar events
provides:
  - CSV export endpoint for payments with UTF-8 BOM
  - PaymentsPage with payment method filter, backend-driven revenue, CSV export button
  - Calendar events with ruble icon on paid bookings
affects: [16-analytics]

# Tech tracking
tech-stack:
  added: []
  patterns: [csv-streaming-response, cross-entity-lookup-for-ui-indicator]

key-files:
  created: []
  modified:
    - backend/app/api/v1/payments.py
    - web/src/api/payments.ts
    - web/src/pages/PaymentsPage.tsx
    - web/src/pages/CalendarPage.tsx

key-decisions:
  - "CSV export uses StreamingResponse with BOM prefix for Excel UTF-8 compatibility"
  - "Calendar uses lightweight payment query for same date range to cross-reference paid bookings"

patterns-established:
  - "CSV export pattern: StreamingResponse + io.StringIO + BOM prefix for Russian text"
  - "Cross-entity UI indicator: fetch related entity data and build Set for O(1) lookup in render"

requirements-completed: [APAY-04, APAY-05, APAY-06, APAY-07]

# Metrics
duration: 2min
completed: 2026-03-21
---

# Phase 12 Plan 02: Admin Payments - PaymentsPage Enhancements & Calendar Payment Indicator Summary

**CSV export with BOM for Excel, payment method filter dropdown, backend-driven revenue total, and ruble icon on calendar events with paid bookings**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T05:54:54Z
- **Completed:** 2026-03-21T05:57:34Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Backend GET /payments/export-csv endpoint with CSV streaming, BOM for Excel, Russian column headers, and all filter params
- PaymentsPage now shows backend-computed total_revenue (not client-side sum of visible page)
- PaymentsPage has payment method filter dropdown (cash/card_to_card/sbp/sbp_robokassa)
- PaymentsPage has "Экспорт CSV" button with loading state for filtered payments download
- Calendar events show ruble sign prefix on bookings that have paid payments

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend CSV export + Frontend PaymentsPage enhancements** - `66ae44c` (feat)
2. **Task 2: Calendar ruble icon on bookings with payments** - `848eb61` (feat)

## Files Created/Modified
- `backend/app/api/v1/payments.py` - Added GET /payments/export-csv endpoint with StreamingResponse and BOM
- `web/src/api/payments.ts` - Added exportPaymentsCsv function for CSV file download, added useAuth import
- `web/src/pages/PaymentsPage.tsx` - Payment method filter, backend total_revenue, CSV export button, sbp_robokassa label
- `web/src/pages/CalendarPage.tsx` - Payments query for date range, paidBookingIds Set, ruble prefix in event titles

## Decisions Made
- CSV export uses StreamingResponse with UTF-8 BOM (\ufeff) prefix for Excel compatibility with Russian text
- Calendar payment indicator uses a lightweight payments query for the same date range as bookings, building a Set of paid booking IDs for O(1) lookup during event rendering (no backend schema changes needed)
- Export endpoint placed before /{payment_id}/confirm route to prevent FastAPI treating "export-csv" as a path parameter

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 12 (Admin Payments) is fully complete with all 4 requirements (APAY-04 through APAY-07) delivered
- PaymentsPage has full filtering (status + payment method + date range), backend revenue, and CSV export
- Calendar shows payment status visually via ruble icon

## Self-Check: PASSED

All 4 files verified present. Both commit hashes (66ae44c, 848eb61) confirmed in git log.

---
*Phase: 12-admin-payments*
*Completed: 2026-03-21*
