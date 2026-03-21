---
phase: 13-auto-receipts
plan: 02
subsystem: ui
tags: [react, antd, react-query, inn, fiscalization, auto-receipts]

requires:
  - phase: 13-auto-receipts-01
    provides: "POST/DELETE /settings/payment/inn endpoints and PaymentSettings schema with inn/fns_connected"
provides:
  - "INN binding UI in mini-app Settings (Card section with 3-state flow)"
  - "INN binding UI in web admin Payments tab (Descriptions row with 3-state flow)"
  - "useBindInn and useUnbindInn mutation hooks in both frontend/ and web/"
affects: []

tech-stack:
  added: []
  patterns:
    - "3-state conditional UI: connected / needs-robokassa / inn-input"

key-files:
  created: []
  modified:
    - frontend/src/api/master-settings.ts
    - frontend/src/pages/master/Settings.tsx
    - web/src/api/settings.ts
    - web/src/pages/SettingsPage.tsx

key-decisions:
  - "INN input uses digit-only filter with maxLength 12 and inputMode numeric"
  - "Web admin allows INN binding directly (not read-only) for convenience"

patterns-established:
  - "INN binding follows same connect/disconnect pattern as Robokassa (bind button + ConfirmDialog/Popconfirm for unbind)"

requirements-completed: [ARCT-01]

duration: 3min
completed: 2026-03-21
---

# Phase 13 Plan 02: Frontend INN Binding UI Summary

**INN binding UI in mini-app and web admin settings with 3-state flow: connected (badge + disconnect), needs Robokassa (info message), and INN input (12-digit field + bind button)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T06:31:05Z
- **Completed:** 2026-03-21T06:33:49Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Mini-app Settings has "Налоги и чеки" card section with INN input, bind/unbind flow, and ConfirmDialog
- Web admin Settings Payments tab has "Авточеки (ФНС)" row with INN input, Popconfirm disconnect
- Both UIs share same 3-state pattern: connected, needs Robokassa, INN input
- Both PaymentSettings interfaces updated with inn and fns_connected fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Mini-app Settings -- INN binding section + API hooks** - `6995689` (feat)
2. **Task 2: Web admin Settings -- INN status in Payments tab + API hooks** - `c1c7fb0` (feat)

## Files Created/Modified
- `frontend/src/api/master-settings.ts` - Added inn/fns_connected to PaymentSettings, useBindInn and useUnbindInn hooks
- `frontend/src/pages/master/Settings.tsx` - Added "Налоги и чеки" Card section with 3-state UI + ConfirmDialog
- `web/src/api/settings.ts` - Added inn/fns_connected to PaymentSettings, useBindInn and useUnbindInn hooks
- `web/src/pages/SettingsPage.tsx` - Extended PaymentsTab with "Авточеки (ФНС)" Descriptions row + bind/unbind handlers

## Decisions Made
- INN input uses digit-only filter (`replace(/\D/g, "")`) with maxLength 12 and inputMode numeric for mobile UX
- Web admin allows INN binding directly (not just read-only display) for admin convenience

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 13 (Auto-Receipts) complete -- backend endpoints and frontend UI both delivered
- Ready for next phase in the v2.0 roadmap

## Self-Check: PASSED

All 4 modified files verified present. Both task commits (6995689, c1c7fb0) verified in git log.

---
*Phase: 13-auto-receipts*
*Completed: 2026-03-21*
