---
phase: 13-auto-receipts
plan: 01
subsystem: payments
tags: [robokassa, receipt-attach, fiscalization, apscheduler, httpx]

# Dependency graph
requires:
  - phase: 12-admin-payments
    provides: PaymentService, payment endpoints, Robokassa integration
provides:
  - ReceiptService with Robokassa ReceiptAttach HTTP calls
  - INN bind/unbind API endpoints
  - Background receipt retry via APScheduler (5-min interval)
  - Receipt link notification to client
  - Master error notification on permanent failure
affects: [14-client-cabinet, frontend payments UI]

# Tech tracking
tech-stack:
  added: [httpx (existing dep, now used for ReceiptAttach)]
  patterns: [fire-and-forget receipt generation after manual payment, APScheduler job for receipt retry]

key-files:
  created:
    - backend/app/services/receipt_service.py
  modified:
    - backend/app/services/robokassa_service.py
    - backend/app/services/payment_service.py
    - backend/app/api/v1/settings.py
    - backend/app/api/v1/payments.py
    - backend/app/schemas/settings.py
    - backend/app/schemas/payment.py
    - backend/app/services/reminder_service.py
    - backend/app/bots/common/notification.py

key-decisions:
  - "ReceiptAttach uses same URL for test and prod, with IsTest=1 flag for test mode"
  - "Receipt retry runs on same APScheduler as reminders (5-min interval, receipt_retry_poll job)"
  - "send_receipt_link is convenience wrapper on send_message (no new adapter method needed)"
  - "INN binding requires Robokassa connected first (400 if not)"

patterns-established:
  - "ReceiptAttach fire-and-forget: call after payment creation, retry via background job"
  - "Client platform lookup: source_platform first, then telegram > max > vk fallback"

requirements-completed: [ARCT-01, ARCT-02, ARCT-03, ARCT-04, ARCT-05]

# Metrics
duration: 7min
completed: 2026-03-21
---

# Phase 13 Plan 01: Auto-Receipts Backend Summary

**Robokassa ReceiptAttach service for cash/card fiscal receipts with INN binding, background retry, and client/master notifications**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-21T06:19:14Z
- **Completed:** 2026-03-21T06:26:14Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- ReceiptService with ReceiptAttach HTTP POST to Robokassa RoboFiscal API, retry logic (3 attempts), and client platform lookup
- INN bind/unbind endpoints (POST/DELETE /settings/payment/inn) with Robokassa prerequisite validation
- Background receipt retry via APScheduler job every 5 minutes, with client receipt link and master error notifications
- PaymentService integration: manual payments with auto fiscalization + fns_connected now trigger ReceiptAttach

## Task Commits

Each task was committed atomically:

1. **Task 1: ReceiptAttach service + INN binding endpoints + PaymentService integration** - `8f1e4fb` (feat)
2. **Task 2: Background retry scheduler + receipt link notification + master error notification** - `3ae1fbc` (feat)

## Files Created/Modified
- `backend/app/services/receipt_service.py` - ReceiptService class + process_pending_receipts scheduler function
- `backend/app/services/robokassa_service.py` - Added build_receipt_attach_payload static method
- `backend/app/services/payment_service.py` - Auto fiscalization sets receipt_status=pending for cash/card
- `backend/app/api/v1/settings.py` - INN bind/unbind endpoints, updated _build_payment_settings
- `backend/app/api/v1/payments.py` - Fire-and-forget ReceiptAttach after manual payment, fns_receipt_url in _payment_to_read
- `backend/app/schemas/settings.py` - Added inn, fns_connected to PaymentSettings; InnSetup schema
- `backend/app/schemas/payment.py` - Added fns_receipt_url to PaymentRead
- `backend/app/services/reminder_service.py` - Registered receipt_retry_poll APScheduler job
- `backend/app/bots/common/notification.py` - Added send_receipt_link convenience method

## Decisions Made
- ReceiptAttach uses same endpoint URL for test and production modes, differentiated by IsTest=1 flag in payload
- Receipt retry job reuses the existing APScheduler instance from reminder_service (no separate scheduler)
- send_receipt_link wraps send_message with formatted text (no new abstract method on MessengerAdapter needed)
- INN binding validates Robokassa is connected first and returns 400 if not

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ReceiptAttach backend is complete and ready for frontend integration
- Frontend can display receipt links via fns_receipt_url in PaymentRead responses
- INN binding UI can be built against POST/DELETE /settings/payment/inn endpoints

---
*Phase: 13-auto-receipts*
*Completed: 2026-03-21*
