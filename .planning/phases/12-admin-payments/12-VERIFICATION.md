---
phase: 12-admin-payments
verified: 2026-03-21T06:15:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 12: Admin Payments Verification Report

**Phase Goal:** A master can complete a visit from the web admin panel by selecting a payment method, adjusting the amount, and choosing a fiscalization option; the payments page shows revenue totals, supports filtering and CSV export
**Verified:** 2026-03-21T06:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Master clicks "Zavershit vizit" on a confirmed booking and sees a modal with editable amount, payment method pills, and fiscalization pills | VERIFIED | `BookingDrawer.tsx` line 187: `onClick={() => setCompleteModalOpen(true)}`; `CompleteVisitModal.tsx` renders InputNumber + Radio.Group for method + conditional Radio.Group for fiscalization |
| 2 | Payment amount pre-fills from service price but can be edited by master | VERIFIED | `CompleteVisitModal.tsx` lines 40-45: `useEffect` sets `amount = servicePrice / 100`; InputNumber is uncontrolled-editable |
| 3 | Fiscalization options appear only if master has Robokassa connected | VERIFIED | `CompleteVisitModal.tsx` line 129: `{paymentSettings?.has_robokassa && (...)}`; matches plan task specification exactly |
| 4 | Submitting modal completes booking AND creates payment in one flow | VERIFIED | `payment_service.py` lines 154-172: `create_manual_payment` creates Payment(status=paid) and sets `booking.status = "completed"` in same DB flush |
| 5 | Payments page shows total revenue from backend for the selected period, not client-side sum | VERIFIED | `PaymentsPage.tsx` line 164: `value={(data.total_revenue \|\| 0) / 100}`; `payment_service.py` lines 571-585: separate revenue query with `func.sum(Payment.amount)` |
| 6 | Payments page can filter by payment method (all/cash/card/SBP) | VERIFIED | `PaymentsPage.tsx` lines 144-154: Select dropdown with paymentMethodOptions; `usePayments` passes `payment_method` query param |
| 7 | Master can export payments list to CSV | VERIFIED | `payments.py` lines 158-224: GET `/payments/export-csv` endpoint with StreamingResponse, BOM (`\ufeff`), Russian headers; `PaymentsPage.tsx` lines 172-191: "Экспорт CSV" button calling `exportPaymentsCsv` |
| 8 | Calendar events show a ruble icon on bookings that have associated payments | VERIFIED | `CalendarPage.tsx` lines 59-77: `usePayments` query builds `paidBookingIds` Set; lines 112-130: event title prepends "₽" if `paidBookingIds.has(b.id)` |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/components/CompleteVisitModal.tsx` | Complete visit modal with amount, payment method, fiscalization | VERIFIED | 155 lines; substantive: InputNumber, Radio.Group, conditional fiscalization, modal submit logic |
| `web/src/api/payments.ts` | useCreateManualPayment, useCreateRobokassaPayment hooks; exportPaymentsCsv; total_revenue in PaymentListResponse | VERIFIED | All three hooks present; `exportPaymentsCsv` at line 105; `total_revenue: number` in PaymentListResponse at line 25 |
| `backend/app/schemas/payment.py` | PaymentCreate with amount_override; PaymentListResponse with total_revenue | VERIFIED | `amount_override: int \| None = None` at line 16; `total_revenue: int = 0` at line 66 |
| `backend/app/services/payment_service.py` | create_manual_payment uses amount_override; get_payment_history returns total_revenue | VERIFIED | Line 138: `final_amount = amount_override if amount_override is not None else booking.service.price`; line 530: returns `tuple[list[dict], int, int]` |
| `web/src/pages/PaymentsPage.tsx` | Enhanced payments page with method filter, backend-driven revenue, CSV export | VERIFIED | Contains `payment_method` state, Select dropdown, `data.total_revenue`, `exportPaymentsCsv` call |
| `web/src/pages/CalendarPage.tsx` | Calendar events with ruble icon on paid bookings | VERIFIED | Contains `₽` in title construction at line 117 |
| `backend/app/api/v1/payments.py` | CSV export endpoint; payment_method filter on history; amount_override passed to service | VERIFIED | GET `/payments/export-csv` at line 158; `payment_method` Query param on `/history` at line 266; `amount_override=data.amount_override` at line 68 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `CompleteVisitModal.tsx` | `/payments/manual` | `useCreateManualPayment` mutation | WIRED | Line 69: `manualMutation.mutateAsync({booking_id, payment_method, fiscalization_level, amount_override})` |
| `BookingDrawer.tsx` | `CompleteVisitModal.tsx` | `completeModalOpen` state | WIRED | Line 30: `import { CompleteVisitModal }`; lines 52, 277-285: state and rendered component |
| `PaymentsPage.tsx` | `/payments/history` | `usePayments` with `payment_method` + `total_revenue` | WIRED | Lines 61-68: filters include `payment_method: paymentMethod`; line 164: `data.total_revenue` consumed |
| `PaymentsPage.tsx` | `/payments/export-csv` | `exportPaymentsCsv` fetch call | WIRED | Lines 178-184: `await exportPaymentsCsv({status, payment_method, date_from, date_to})` |
| `CalendarPage.tsx` | `extendedProps.booking` | payment lookup for ruble icon via `paidBookingIds` Set | WIRED | Lines 59-77: `usePayments` query; lines 116-119: `hasPaid ? "₽" : null` in title |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| APAY-01 | 12-01 | Master can finish a visit from web admin with payment method selection (cash/card/SBP) | SATISFIED | CompleteVisitModal.tsx: cash/card_to_card/SBP Radio.Group; BookingDrawer "Завершить визит" opens modal |
| APAY-02 | 12-01 | Payment amount pre-filled from service price, editable (discount/extra) | SATISFIED | CompleteVisitModal.tsx: useEffect pre-fills `servicePrice / 100`; InputNumber is editable; `amount_override` in PaymentCreate |
| APAY-03 | 12-01 | Fiscalization option on payment completion (auto/manual/none) | SATISFIED | CompleteVisitModal.tsx: conditional Чек Radio.Group with auto/manual/none when `has_robokassa`; backend propagates `fiscalization_level` override |
| APAY-04 | 12-02 | Payments page shows total revenue for selected period | SATISFIED | PaymentsPage.tsx: `data.total_revenue / 100` Statistic; backend: separate `func.sum` query on paid payments with same date/method filters |
| APAY-05 | 12-02 | Payments page has filter by payment method | SATISFIED | PaymentsPage.tsx: Select dropdown with cash/card_to_card/sbp/sbp_robokassa options; passed to `usePayments` |
| APAY-06 | 12-02 | Payments page has CSV export | SATISFIED | PaymentsPage.tsx: "Экспорт CSV" Button; exportPaymentsCsv function; backend GET /payments/export-csv with BOM + Russian headers |
| APAY-07 | 12-02 | Calendar event shows ruble icon for quick payment access | SATISFIED | CalendarPage.tsx: paidBookingIds Set; "₽" prepended to event title for paid bookings |

No orphaned requirements — all 7 APAY requirements claimed in plans (12-01: APAY-01,02,03; 12-02: APAY-04,05,06,07) and all verified present in code.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TODO/FIXME/placeholder comments found in phase 12 files. No empty implementations. No stub handlers. The `return null` in `BookingDrawer.tsx` line 55 is a valid early-exit guard (`if (!booking) return null`), not a stub.

**Routing order note:** In `payments.py`, GET `/history` (line 259) is declared after POST `/{payment_id}/confirm` (line 227) and POST `/{payment_id}/cancel` (line 244). Since those are POST routes and `/history` is GET, there is no HTTP method conflict. GET `/export-csv` (line 158) is correctly placed before GET `/{payment_id}/receipt-data` (line 288), preventing the "export-csv" literal from being matched as a `payment_id` path parameter. Route ordering is correct.

### Human Verification Required

#### 1. CompleteVisitModal — SBP via Robokassa routing

**Test:** With Robokassa connected (`has_robokassa = true`), select "СБП" payment method and submit. Verify the booking is completed and a payment record of type `sbp_robokassa` appears, with a `payment_url`.
**Expected:** Booking status changes to "completed"; payment has `payment_method = "sbp_robokassa"` and a valid Robokassa URL.
**Why human:** Requires a live master account with Robokassa credentials configured.

#### 2. CSV export — Excel UTF-8 BOM

**Test:** Download CSV export via "Экспорт CSV" button and open in Microsoft Excel.
**Expected:** Russian column headers and data display correctly without encoding corruption.
**Why human:** BOM presence (`\ufeff`) is verified in code (payments.py line 199) but Excel rendering requires manual confirmation.

#### 3. Calendar ruble icon — live data

**Test:** On a date with a completed booking that has a paid payment, open the calendar.
**Expected:** The calendar event shows "₽ — ServiceName — ClientName" as its title.
**Why human:** Requires a live environment with bookings in "completed" status and associated paid payments.

### Gaps Summary

No gaps found. All 8 observable truths verified, all 7 artifacts pass all three levels (exists, substantive, wired), all 5 key links confirmed wired, all 7 APAY requirements satisfied. TypeScript compiles with zero errors. All 4 commit hashes (35d1c25, 6dae1bd, 66ae44c, 848eb61) present in git log.

---

_Verified: 2026-03-21T06:15:00Z_
_Verifier: Claude (gsd-verifier)_
