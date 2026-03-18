---
phase: 03-payments-tax-receipts
plan: 03
subsystem: ui
tags: [react, tanstack-query, payment-sheet, robokassa-wizard, bottom-sheet, receipt-card, payment-history, tailwind]

# Dependency graph
requires:
  - phase: 03-payments-tax-receipts
    plan: 01
    provides: "Payment models, PaymentService, schemas, Robokassa/QR/Encryption services"
  - phase: 03-payments-tax-receipts
    plan: 02
    provides: "Payment API endpoints (7), settings API (5), Robokassa webhook, notification extensions"
  - phase: 02-booking-engine
    provides: "Bookings page, Settings page, master-settings API hooks, ConfirmDialog, UI components, App routes"
provides:
  - "PaymentSheet bottom sheet with 3 payment flows (manual, Robokassa SBP link, QR requisites)"
  - "ReceiptDataCard for manual fiscalization (copyable receipt data + Moy Nalog link)"
  - "PaymentHistory page with status/receipt badges, date filters, and pagination"
  - "RobokassaWizard 3-step inline wizard for merchant connection"
  - "Payment API hooks (7 hooks: 3 create mutations, confirm, cancel, history query, receipt query)"
  - "Payment settings hooks (5 hooks: get/update settings, setup/disconnect Robokassa, mark grey warning)"
  - "Settings payment sections: Requisites, Robokassa, Fiscalization + payment history link"
  - "Bookings Zavershit button opening PaymentSheet on confirmed bookings"
  - "/master/payments route for payment history"
affects: [04-notifications, 06-web-admin-panel]

# Tech tracking
tech-stack:
  added: []
  patterns: [payment-bottom-sheet, robokassa-wizard-flow, pill-selector-pattern, receipt-data-clipboard, fiscalization-override-ui]

key-files:
  created:
    - frontend/src/api/payments.ts
    - frontend/src/components/PaymentSheet.tsx
    - frontend/src/components/ReceiptDataCard.tsx
    - frontend/src/components/RobokassaWizard.tsx
    - frontend/src/pages/master/PaymentHistory.tsx
  modified:
    - frontend/src/api/master-settings.ts
    - frontend/src/pages/master/Bookings.tsx
    - frontend/src/pages/master/Settings.tsx
    - frontend/src/App.tsx

key-decisions:
  - "PaymentSheet uses same slide-up bottom sheet pattern as ConfirmDialog for UI consistency"
  - "Fiscalization override in PaymentSheet allows per-payment level change from master default"
  - "Grey warning shown once per master via has_seen_grey_warning flag with API persistence"
  - "RobokassaWizard rendered inline in Settings (not modal) for step-by-step credential entry"
  - "Payment history navigation link in Settings for discoverability"

patterns-established:
  - "Bottom sheet payment flow: option selection -> method-specific form -> result/receipt"
  - "Pill selector pattern for payment method and fiscalization level selection"
  - "Clipboard copy pattern for receipt data and payment links"
  - "Inline wizard pattern: multi-step form within Settings page section"
  - "Conditional option availability: disabled+greyed options based on master configuration state"

requirements-completed: [PAY-01, PAY-02, PAY-03, PAY-04, TAX-01, TAX-02, TAX-03]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 3 Plan 3: Payment Frontend UI Summary

**PaymentSheet bottom sheet with 3 payment flows (manual/Robokassa/requisites), PaymentHistory page with filters and badges, RobokassaWizard 3-step connection, ReceiptDataCard with clipboard copy, and Settings payment configuration sections**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T04:10:16Z
- **Completed:** 2026-03-18T04:13:22Z
- **Tasks:** 3 (2 auto + 1 checkpoint approved/deferred)
- **Files modified:** 9

## Accomplishments

- Built PaymentSheet bottom sheet with 3 payment options (manual income, Robokassa SBP link, QR requisites) including per-payment fiscalization override and grey warning
- Created PaymentHistory page with status/receipt badges, date range filters, status pill filters, and pagination
- Built RobokassaWizard with 3-step inline flow (instructions, credentials form, success confirmation)
- Extended Settings with 3 new sections (Requisites, Robokassa, Fiscalization) and payment history navigation link
- Added Zavershit button on confirmed bookings to trigger the payment flow
- Created 12 TanStack Query hooks (7 payment + 5 settings) wiring frontend to all backend payment endpoints

## Task Commits

Each task was committed atomically:

1. **Task 1: Payment API hooks, PaymentSheet, ReceiptDataCard, PaymentHistory, Bookings extension** - `602b165` (feat)
2. **Task 2: Settings payment sections, RobokassaWizard, master-settings hooks** - `5b1ce76` (feat)
3. **Task 3: End-to-end verification** - checkpoint approved (deferred, no code changes)

## Files Created/Modified

- `frontend/src/api/payments.ts` - 7 TanStack Query hooks for payment CRUD (manual, Robokassa, requisites, confirm, cancel, history, receipt-data)
- `frontend/src/components/PaymentSheet.tsx` - Bottom sheet with 3 payment flows, per-payment fiscalization override, grey warning
- `frontend/src/components/ReceiptDataCard.tsx` - Copyable receipt data card with Moy Nalog link
- `frontend/src/components/RobokassaWizard.tsx` - 3-step Robokassa connection wizard (instructions, form, success)
- `frontend/src/pages/master/PaymentHistory.tsx` - Payment list with status/receipt badges, date and status filters, pagination
- `frontend/src/api/master-settings.ts` - Extended with 5 payment settings hooks (get/update, Robokassa setup/disconnect, grey warning)
- `frontend/src/pages/master/Bookings.tsx` - Added Zavershit button on confirmed bookings, PaymentSheet integration
- `frontend/src/pages/master/Settings.tsx` - 3 new sections: Requisites (card/phone/bank), Robokassa (wizard/status), Fiscalization (level/SNO/warning)
- `frontend/src/App.tsx` - Added /master/payments route for PaymentHistory

## Decisions Made

- **Bottom sheet pattern reuse:** PaymentSheet follows the same slide-up animation and backdrop blur pattern as ConfirmDialog for visual consistency across the app.
- **Inline wizard:** RobokassaWizard renders inline within the Settings page section rather than as a modal, providing a more natural step-by-step flow alongside other settings.
- **Fiscalization override:** PaymentSheet includes per-payment fiscalization level override (pill selector) with fallback to master default, matching the backend's override cascade.
- **Grey warning persistence:** One-time amber warning for "Bez chekov" selection is tracked via `has_seen_grey_warning` API flag, so it persists across sessions.
- **Payment history link in Settings:** Added navigation link to /master/payments from Settings for discoverability, since payment history is not in the bottom tab bar.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Frontend hooks connect to backend endpoints from Plans 01-02.

## Next Phase Readiness

- Complete payment flow is now functional end-to-end: Settings configuration -> Bookings "Zavershit" -> PaymentSheet -> PaymentHistory
- Phase 3 (Payments + Tax Receipts) is complete: backend infrastructure (Plan 01), API + tests (Plan 02), frontend UI (Plan 03)
- Ready for Phase 4 (Notifications) which depends on Phase 2 (already complete)
- Ready for Phase 6 (Web Admin Panel) which depends on Phase 3 (now complete)

## Self-Check: PASSED

All 9 files verified on disk. Both task commits (602b165, 5b1ce76) verified in git log.

---
*Phase: 03-payments-tax-receipts*
*Completed: 2026-03-18*
