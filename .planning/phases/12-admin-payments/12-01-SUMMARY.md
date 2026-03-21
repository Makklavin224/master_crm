---
phase: 12-admin-payments
plan: 01
subsystem: payments, ui
tags: [antd, react, fastapi, pydantic, mutation-hooks, modal]

# Dependency graph
requires:
  - phase: 03-payments-tax
    provides: Payment model, PaymentService, payment endpoints
  - phase: 08-web-admin-ux-polish
    provides: BookingDrawer with action buttons
provides:
  - CompleteVisitModal component with amount/method/fiscalization
  - useCreateManualPayment and useCreateRobokassaPayment hooks
  - Backend amount_override support for custom pricing
  - Payment method filter on history endpoint
  - total_revenue in payment list response
affects: [12-02, 13-auto-receipts, 16-analytics]

# Tech tracking
tech-stack:
  added: []
  patterns: [modal-with-mutation, amount-override-pattern]

key-files:
  created:
    - web/src/components/CompleteVisitModal.tsx
  modified:
    - backend/app/schemas/payment.py
    - backend/app/services/payment_service.py
    - backend/app/api/v1/payments.py
    - web/src/api/payments.ts
    - web/src/components/BookingDrawer.tsx

key-decisions:
  - "amount_override sent only when differs from service price (avoids unnecessary override)"
  - "SBP payment via Robokassa when has_robokassa, otherwise manual payment for all methods"
  - "Revenue query always filters status=paid regardless of status_filter (revenue = actual paid money)"

patterns-established:
  - "Amount override pattern: optional kopecks field, falls back to service price"
  - "Complete visit flow: single modal replaces direct booking completion"

requirements-completed: [APAY-01, APAY-02, APAY-03]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 12 Plan 01: Admin Payments - Complete Visit Flow Summary

**CompleteVisitModal with editable amount, payment method pills, conditional fiscalization, and backend amount_override + payment_method filter + total_revenue support**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T05:47:51Z
- **Completed:** 2026-03-21T05:52:03Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Backend PaymentCreate/RobokassaPaymentCreate accept optional amount_override (kopecks) for discounts/extras
- Backend payment history endpoint supports payment_method filter and returns total_revenue
- CompleteVisitModal component with pre-filled editable amount, cash/card/SBP pills, and conditional fiscalization section
- BookingDrawer "Завершить визит" button opens CompleteVisitModal instead of directly completing

## Task Commits

Each task was committed atomically:

1. **Task 1: Backend -- add amount_override + payment_method filter + total_revenue** - `35d1c25` (feat)
2. **Task 2: Frontend -- payment API hooks + CompleteVisitModal + BookingDrawer integration** - `6dae1bd` (feat)

## Files Created/Modified
- `backend/app/schemas/payment.py` - Added amount_override to PaymentCreate/RobokassaPaymentCreate, total_revenue to PaymentListResponse
- `backend/app/services/payment_service.py` - amount_override in create methods, payment_method filter + total_revenue in get_payment_history
- `backend/app/api/v1/payments.py` - Pass amount_override to service, payment_method query param, 3-tuple return handling
- `web/src/api/payments.ts` - useCreateManualPayment, useCreateRobokassaPayment hooks, updated interfaces
- `web/src/components/CompleteVisitModal.tsx` - New modal with amount input, payment method pills, fiscalization pills
- `web/src/components/BookingDrawer.tsx` - Replaced direct completion with CompleteVisitModal integration

## Decisions Made
- amount_override is sent only when the entered amount differs from the service price, avoiding unnecessary overrides
- SBP payment method routes through Robokassa (useCreateRobokassaPayment) when has_robokassa is true; all other methods use useCreateManualPayment
- Total revenue query always filters on status="paid" regardless of the status_filter param, because revenue should only reflect actually paid amounts

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CompleteVisitModal and payment hooks are ready for plan 12-02 (PaymentsPage enhancements, CSV export, calendar ruble icon)
- total_revenue backend support is ready for PaymentsPage revenue display
- payment_method filter is ready for PaymentsPage method filter dropdown

## Self-Check: PASSED

All 6 files verified present. Both commit hashes (35d1c25, 6dae1bd) confirmed in git log.

---
*Phase: 12-admin-payments*
*Completed: 2026-03-21*
