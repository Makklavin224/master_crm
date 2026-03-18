---
phase: 03-payments-tax-receipts
verified: 2026-03-18T05:30:00Z
status: passed
score: 17/17 must-haves verified
re_verification: false
---

# Phase 3: Payments + Tax Receipts Verification Report

**Phase Goal:** Masters can complete a visit and collect payment; when Robokassa is connected, the client receives an SBP payment link and a tax receipt is automatically generated in "Moy Nalog"
**Verified:** 2026-03-18T05:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Payment model stores amount, status, payment_method, receipt_status, robokassa fields, and fiscalization_level | VERIFIED | `backend/app/models/payment.py` — all columns present: `robokassa_inv_id`, `fiscalization_level`, `receipt_data`, `receipt_id`, `payment_url` |
| 2  | Master model stores payment requisites, encrypted Robokassa credentials, and fiscalization settings | VERIFIED | `backend/app/models/master.py` — all 11 Phase 3 columns present: `card_number`, `sbp_phone`, `bank_name`, `robokassa_merchant_login`, `robokassa_password1_encrypted`, `robokassa_password2_encrypted`, `robokassa_is_test`, `robokassa_hash_algorithm`, `fiscalization_level`, `has_seen_grey_warning`, `receipt_sno` |
| 3  | RobokassaService generates signed payment URLs and verifies ResultURL callback signatures | VERIFIED | `backend/app/services/robokassa_service.py` — `generate_payment_url` with HMAC, `verify_result_signature` with case-insensitive comparison. Live check confirmed: URL contains `MerchantLogin=login` and `SignatureValue`; signature verification returns True for valid input |
| 4  | EncryptionService encrypts and decrypts Robokassa passwords using Fernet symmetric encryption | VERIFIED | `backend/app/services/encryption_service.py` — `encrypt_value`/`decrypt_value` with `InvalidToken` guard. Live round-trip check passed: `decrypt_value(encrypt_value('test')) == 'test'` |
| 5  | QR service generates base64-encoded PNG QR codes from phone/card data | VERIFIED | `backend/app/services/qr_service.py` — `generate_payment_qr` returns 404-char base64 PNG for `+79161234567` |
| 6  | PaymentService orchestrates all 7 methods: create_manual, create_robokassa, create_requisites, confirm_requisites, handle_callback, get_history, cancel | VERIFIED | All 7 methods confirmed via `dir(PaymentService)`: `cancel_payment`, `confirm_requisites_payment`, `create_manual_payment`, `create_requisites_payment`, `create_robokassa_payment`, `format_receipt_data`, `get_payment_history`, `handle_robokassa_callback` |
| 7  | Master can create a manual payment via POST /api/v1/payments/manual (status=paid) | VERIFIED | Endpoint exists in router (7 routes confirmed). Sets `status="paid"`, `paid_at=now`, marks booking `"completed"`. Receipt data populated when `fiscalization="manual"` |
| 8  | Master can initiate a Robokassa payment and receive a payment URL | VERIFIED | `POST /api/v1/payments/robokassa` calls `PaymentService.create_robokassa_payment`, returns `PaymentRead` with `payment_url`. Decrypts credentials, gets InvId from sequence, builds signed URL |
| 9  | Robokassa callback at POST /webhook/robokassa/result verifies signature and returns OK{InvId} | VERIFIED | Webhook registered at app level (`/webhook/robokassa/result` present in all app routes). Parses form data, verifies HMAC via `RobokassaService.verify_result_signature`, returns `PlainTextResponse(f"OK{inv_id}")` on success, 403 on failure. Idempotent for already-paid payments |
| 10 | Payment link is sent to client via TelegramAdapter when Robokassa payment is created | VERIFIED | `payments.py` robokassa endpoint calls `notification_service.send_payment_link` (fire-and-forget try/except). `TelegramAdapter.send_payment_link` sends HTML message with `InlineKeyboardButton(url=payment_url)` |
| 11 | Master can save and disconnect Robokassa credentials via payment settings API | VERIFIED | `POST /api/v1/settings/payment/robokassa` encrypts and saves passwords via `encrypt_value`. `DELETE /api/v1/settings/payment/robokassa` nulls all robokassa columns |
| 12 | Master can set fiscalization level with one-time grey warning | VERIFIED | `POST /api/v1/settings/payment/grey-warning-seen` sets `has_seen_grey_warning=True`. Frontend `PaymentSheet` shows amber warning on "Без чеков" selection only when `!seenWarningLocal` |
| 13 | Master can tap Завершить on a booking and see a bottom sheet with 3 payment options | VERIFIED | `Bookings.tsx` imports `PaymentSheet` and renders it (line 197). "Завершить" button present (line 160). Sheet shows 3 cards: manual, Robokassa (disabled if `!hasRobokassa`), requisites (disabled if `!hasRequisites`) |
| 14 | Master can view payment history with status/receipt badges and date filters | VERIFIED | `PaymentHistory.tsx` — status pills (Все/Ожидает/Оплачено/Отменено), date range inputs, paginated list with `Badge` (status) and receipt badge. Pagination via "Показать ещё" |
| 15 | Master can configure payment requisites and connect Robokassa in Settings | VERIFIED | `Settings.tsx` has 3 new sections: "Реквизиты для оплаты" (card/phone/bank inputs), "Робокасса" (wizard or connected state), "Чеки и фискализация" (level pills, SNO selector). `RobokassaWizard` inline 3-step wizard confirmed |
| 16 | Manual fiscalization shows copyable receipt data and link to Moy Nalog | VERIFIED | `ReceiptDataCard.tsx` — 4-field display, "Скопировать данные" button uses `navigator.clipboard.writeText`, "Открыть Мой Налог" link opens `https://lknpd.nalog.ru/` in new tab |
| 17 | Test suite covers all requirement IDs | VERIFIED | 14 unit tests (test_robokassa.py, 14/14 passing), 11 integration tests (test_payments.py), 10 settings tests (test_settings.py, 6 new payment tests). Total: 35 tests |

**Score:** 17/17 truths verified

---

## Required Artifacts

| Artifact | Status | Line Count / Details |
|----------|--------|---------------------|
| `backend/alembic/versions/004_add_payment_and_settings_columns.py` | VERIFIED | 16 `op.add_column` calls; `CREATE SEQUENCE robokassa_inv_id_seq`; `ix_payments_master_id_created_at` composite index |
| `backend/app/services/robokassa_service.py` | VERIFIED | Exports `RobokassaService`, `RobokassaCredentials`; `_compute_hash`, `generate_payment_url`, `verify_result_signature`, `build_receipt_json` |
| `backend/app/services/encryption_service.py` | VERIFIED | Exports `encrypt_value`, `decrypt_value`; Fernet with `InvalidToken` guard |
| `backend/app/services/qr_service.py` | VERIFIED | Exports `generate_payment_qr`; returns base64 PNG string |
| `backend/app/services/payment_service.py` | VERIFIED | `PaymentService` with all 7 methods + `format_receipt_data` static helper |
| `backend/app/schemas/payment.py` | VERIFIED | `PaymentCreate`, `RobokassaPaymentCreate`, `PaymentRead`, `PaymentListResponse`, `ManualReceiptData`, `PaymentRequisites`, `PaymentConfirm` |
| `backend/app/schemas/settings.py` | VERIFIED | Extended with `PaymentSettings`, `PaymentSettingsUpdate`, `RobokassaSetup`, `RobokassaDisconnect` |
| `backend/app/api/v1/payments.py` | VERIFIED | 7 routes: `POST /manual`, `POST /robokassa`, `POST /requisites`, `POST /{id}/confirm`, `POST /{id}/cancel`, `GET /history`, `GET /{id}/receipt-data` |
| `backend/app/api/v1/settings.py` | VERIFIED | 5 new payment endpoints: `GET /payment`, `PUT /payment`, `POST /payment/robokassa`, `DELETE /payment/robokassa`, `POST /payment/grey-warning-seen` |
| `backend/app/api/v1/router.py` | VERIFIED | `payments_router` included with `/payments` prefix |
| `backend/app/main.py` | VERIFIED | `POST /webhook/robokassa/result` registered at app level; HMAC-based security |
| `backend/app/bots/common/adapter.py` | VERIFIED | `send_payment_link` and `send_payment_requisites` abstract methods added |
| `backend/app/bots/common/notification.py` | VERIFIED | `send_payment_link` and `send_payment_requisites` delegation methods added |
| `backend/app/bots/telegram/adapter.py` | VERIFIED | Both payment methods implemented with HTML formatting and inline keyboard |
| `backend/tests/test_robokassa.py` | VERIFIED | 228 lines, 14 tests, all passing |
| `backend/tests/test_payments.py` | VERIFIED | 420 lines, 11 tests |
| `backend/tests/test_settings.py` | VERIFIED | 159 lines, 10 tests (6 new payment settings tests) |
| `frontend/src/api/payments.ts` | VERIFIED | Exports 7 hooks: `useCreateManualPayment`, `useCreateRobokassaPayment`, `useCreateRequisitesPayment`, `useConfirmPayment`, `useCancelPayment`, `usePaymentHistory`, `useReceiptData` |
| `frontend/src/api/master-settings.ts` | VERIFIED | Extended with 5 payment hooks: `usePaymentSettings`, `useUpdatePaymentSettings`, `useSetupRobokassa`, `useDisconnectRobokassa`, `useMarkGreyWarningSeen` |
| `frontend/src/components/PaymentSheet.tsx` | VERIFIED | 569 lines; 3-state flow (options → manual/robokassa/requisites/receipt); all Russian strings present; grey warning logic wired |
| `frontend/src/components/ReceiptDataCard.tsx` | VERIFIED | 83 lines; clipboard copy + Moy Nalog link |
| `frontend/src/components/RobokassaWizard.tsx` | VERIFIED | 256 lines; 3-step wizard (instructions → credentials form → success) |
| `frontend/src/pages/master/PaymentHistory.tsx` | VERIFIED | 235 lines; status pills + date filters + pagination + receipt badge |
| `frontend/src/pages/master/Bookings.tsx` | VERIFIED | Imports `PaymentSheet` (line 11), renders it (line 197), "Завершить" button on confirmed bookings (line 160) |
| `frontend/src/pages/master/Settings.tsx` | VERIFIED | 3 new sections: Requisites, Robokassa (wizard or connected), Fiscalization; payment history navigation link |
| `frontend/src/App.tsx` | VERIFIED | `PaymentHistory` imported (line 22), `/master/payments` route registered (line 71) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `payment_service.py` | `robokassa_service.py` | `import RobokassaService, RobokassaCredentials` | WIRED | `RobokassaService.generate_payment_url` called in `create_robokassa_payment`; `verify_result_signature` called in `handle_robokassa_callback` |
| `payment_service.py` | `encryption_service.py` | `decrypt_value` for Robokassa passwords | WIRED | `decrypt_value(master.robokassa_password1_encrypted)` in both `create_robokassa_payment` and `handle_robokassa_callback` |
| `payment.py model` | `booking.py model` | `ForeignKey("bookings.id")` | WIRED | `booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))` |
| `payments.py API` | `payment_service.py` | `PaymentService` method calls | WIRED | All 7 endpoint handlers call `PaymentService.*` methods directly |
| `main.py` | `payment_service.py` | `handle_robokassa_callback` in webhook | WIRED | Webhook handler calls `PaymentService.handle_robokassa_callback(db, master_id, inv_id, out_sum, signature, shp_params)` |
| `router.py` | `payments.py API` | `include_router` with `/payments` prefix | WIRED | `api_v1_router.include_router(payments_router, prefix="/payments", tags=["payments"])` |
| `notification.py` | `adapter.py` | `send_payment_link` method on `MessengerAdapter` | WIRED | `NotificationService.send_payment_link` delegates to `adapter.send_payment_link` |
| `PaymentSheet.tsx` | `payments.ts` | mutation hooks | WIRED | All 3 create mutations + confirm used: `useCreateManualPayment`, `useCreateRobokassaPayment`, `useCreateRequisitesPayment`, `useConfirmPayment` |
| `Bookings.tsx` | `PaymentSheet.tsx` | "Завершить" button opens sheet | WIRED | `import { PaymentSheet }` line 11, rendered at line 197 |
| `Settings.tsx` | `RobokassaWizard.tsx` | Robokassa section renders wizard | WIRED | `import { RobokassaWizard }` line 18, rendered at line 360 |
| `Settings.tsx` | `master-settings.ts` | payment settings hooks | WIRED | `usePaymentSettings` and 4 mutations imported and called |

---

## Requirements Coverage

| Requirement | Phase 3 Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| PAY-01 | 03-01, 03-02, 03-03 | Master can complete a visit and mark "Paid" (simple mode, cash/card-to-card) | SATISFIED | `POST /api/v1/payments/manual` with `payment_method` in [cash, card_to_card, transfer, sbp]. Frontend "Завершить" → PaymentSheet → "Внести доход вручную" |
| PAY-02 | 03-01, 03-02, 03-03 | Master can optionally connect their own Robokassa for automatic SBP link | SATISFIED | `POST /api/v1/settings/payment/robokassa` encrypts and stores credentials. `DELETE` disconnects. RobokassaWizard in Settings |
| PAY-03 | 03-01, 03-02, 03-03 | With Robokassa connected: master taps "Complete" → client gets SBP payment link | SATISFIED | `POST /api/v1/payments/robokassa` generates signed URL and fires `notification_service.send_payment_link` via TelegramAdapter with inline button |
| PAY-04 | 03-01, 03-02, 03-03 | Payment history with statuses (pending, paid, cancelled) | SATISFIED | `GET /api/v1/payments/history` with status/date filters. PaymentHistory page with Badge per status |
| TAX-01 | 03-01, 03-02, 03-03 | Three fiscalization levels: no receipts / manual / automatic | SATISFIED | Master model `fiscalization_level` in ["none", "manual", "auto"]. Per-payment override in PaymentCreate. Both backend and frontend enforce levels |
| TAX-02 | 03-01, 03-02, 03-03 | No receipts: master sees warning but can continue | SATISFIED | `has_seen_grey_warning` flag + `POST /settings/payment/grey-warning-seen`. Frontend shows amber warning card once, master dismisses with "Понятно" |
| TAX-03 | 03-01, 03-02, 03-03 | Manual: after payment, CRM shows ready data for "Moy Nalog" (amount, service, client) | SATISFIED | `GET /api/v1/payments/{id}/receipt-data` returns `ManualReceiptData`. `ReceiptDataCard` shows all fields with clipboard copy and "Открыть Мой Налог" link |
| TAX-04 | 03-01, 03-02 | Automatic: with Robokassa connected, receipt auto-generated via Robochecks → FNS | SATISFIED | `RobokassaService.build_receipt_json` builds 54-FZ Receipt JSON. `create_robokassa_payment` includes Receipt in URL when `fiscalization="auto"`. `handle_robokassa_callback` sets `receipt_status="issued"` |

No orphaned requirements: all 8 IDs (PAY-01 through PAY-04, TAX-01 through TAX-04) appear in at least one plan's `requirements` field and are fully covered.

---

## Anti-Patterns Found

No blockers or stubs found.

| File | Pattern Checked | Result |
|------|----------------|--------|
| `payment_service.py` | Empty implementations, placeholder returns | None — all 7 methods have real business logic |
| `payments.py API` | Return null / static data | None — all endpoints call PaymentService methods |
| `robokassa_service.py` | TODO/FIXME | None |
| `PaymentSheet.tsx` | Placeholder JSX, empty handlers | None — full 3-state flow with real mutations |
| `ReceiptDataCard.tsx` | Stub buttons | None — `navigator.clipboard.writeText` called, Moy Nalog link is real |
| `RobokassaWizard.tsx` | Empty form submit | None — `setupRobokassa.mutate` called with validated fields |
| `Bookings.tsx` | Завершить button with no-op handler | None — opens PaymentSheet with booking data |
| `Settings.tsx` | Payment sections without save | None — each section calls update mutations |

---

## Human Verification Required

Automated checks cover all backend logic (imports, route registration, service methods, 14 unit tests passing). The following items require manual testing due to UI/UX and external service nature:

### 1. Full Payment Flow End-to-End (Bookings → PaymentSheet → History)

**Test:** Open master panel in Telegram Mini App → navigate to Bookings → find a confirmed booking → tap "Завершить"
**Expected:** Bottom sheet slides up with 3 option cards; manual option is always enabled; Robokassa option greyed if not connected; requisites option greyed if no card/phone configured
**Why human:** Slide-up animation, touch targets, visual state of disabled options cannot be verified by grep

### 2. Grey Warning One-Time Display

**Test:** Go to Settings → Fiscalization section → select "Без чеков" for the first time
**Expected:** Amber warning card appears; tap "Понятно"; navigate away and return; warning does not appear again
**Why human:** Session/flag persistence across navigation requires live app testing

### 3. QR Code Renders in Requisites Flow

**Test:** Configure SBP phone in Settings → tap Завершить on a booking → select "Показать реквизиты + QR"
**Expected:** 192×192 QR code image renders with phone number encoded; card number shows with copy button
**Why human:** Base64 PNG rendering in `<img>` tag requires visual inspection

### 4. TelegramAdapter Payment Link Delivery

**Test:** Configure Robokassa credentials (test mode) → tap Завершить → select "Отправить ссылку клиенту"
**Expected:** Client Telegram account receives message with "Оплатить" inline button pointing to Robokassa URL
**Why human:** Requires live Telegram bot + real Robokassa test credentials + client TG account with `tg_user_id` set

### 5. Robokassa ResultURL Callback (Test Mode)

**Test:** Create a Robokassa payment (test mode) → Robokassa sends callback to `/webhook/robokassa/result`
**Expected:** Payment status changes to "paid"; booking status changes to "completed"; response body is `OK{InvId}`
**Why human:** Requires Docker running (PostgreSQL accessible) + Robokassa test environment reachable

---

## Summary

Phase 3 goal is fully achieved at the code level. All three payment flows are implemented:

1. **Manual payment** — master marks visit as paid (cash/card/transfer/SBP), optionally with fiscalization level override and receipt data for Moy Nalog
2. **Robokassa SBP link** — signed payment URL generated, sent to client via Telegram inline button, callback verified via HMAC
3. **QR requisites** — QR code generated from SBP phone or card, two-step confirm flow

All 8 requirement IDs are satisfied. Backend services pass live import and unit tests (14/14 test_robokassa.py). TypeScript frontend compiles with zero errors. All key links are wired: services to models, API endpoints to services, frontend hooks to API, components to pages, routes registered. No stubs or placeholder implementations found.

The 5 human verification items are runtime/UX concerns (visual rendering, live bot delivery, external service integration) that cannot be verified programmatically.

---

_Verified: 2026-03-18T05:30:00Z_
_Verifier: Claude (gsd-verifier)_
