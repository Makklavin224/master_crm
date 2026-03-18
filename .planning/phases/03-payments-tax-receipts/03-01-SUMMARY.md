---
phase: 03-payments-tax-receipts
plan: 01
subsystem: payments
tags: [robokassa, fernet, encryption, qrcode, payment-service, alembic, pydantic]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: "SQLAlchemy models (Payment, Master, Booking), Alembic migrations, FastAPI config"
  - phase: 02-booking-engine
    provides: "Booking CRUD service, client/service models, notification patterns"
provides:
  - "Payment model with Robokassa fields (inv_id, payment_url, receipt_data, fiscalization_level)"
  - "Master model with payment requisites, encrypted Robokassa credentials, fiscalization settings"
  - "EncryptionService (Fernet encrypt/decrypt for credentials)"
  - "RobokassaService (payment URL generation, callback signature verification, receipt JSON)"
  - "QrService (base64 PNG QR codes for manual payments)"
  - "PaymentService (7 methods: create_manual, create_robokassa, create_requisites, confirm_requisites, handle_callback, get_history, cancel)"
  - "Payment schemas (PaymentCreate, PaymentRead, PaymentListResponse, etc.)"
  - "Settings schemas (PaymentSettings, RobokassaSetup, PaymentSettingsUpdate)"
  - "Alembic migration 004 with composite index and InvId sequence"
affects: [03-payments-tax-receipts, 04-master-panel]

# Tech tracking
tech-stack:
  added: [cryptography 46.0.5, qrcode 8.2, pillow 12.1.1]
  patterns: [fernet-encryption, robokassa-hmac-signing, qr-base64-generation, payment-service-orchestration]

key-files:
  created:
    - backend/alembic/versions/004_add_payment_and_settings_columns.py
    - backend/app/services/encryption_service.py
    - backend/app/services/robokassa_service.py
    - backend/app/services/qr_service.py
    - backend/app/services/payment_service.py
    - backend/app/schemas/payment.py
  modified:
    - backend/app/models/payment.py
    - backend/app/models/master.py
    - backend/app/core/config.py
    - backend/app/schemas/settings.py
    - backend/pyproject.toml

key-decisions:
  - "Fernet symmetric encryption for Robokassa passwords with ENCRYPTION_KEY env var"
  - "Pillow as qrcode image backend (over pypng pure-Python) for reliable PNG generation"
  - "Payment URL signature includes Shp_master_id and Shp_booking_id for callback routing"
  - "Idempotent Robokassa callback: already-paid returns True without re-processing"
  - "Per-payment fiscalization override with fallback to master default"
  - "SELECT FOR UPDATE on payment mutations to prevent race conditions"

patterns-established:
  - "EncryptionService: encrypt_value/decrypt_value for any sensitive credential storage"
  - "RobokassaService: stateless class with static methods for payment URL/signature operations"
  - "PaymentService: orchestrator pattern loading booking, validating state, creating payment, updating booking status"
  - "Requisites payment: two-step flow (create pending -> confirm paid) unlike manual (instant paid)"

requirements-completed: [PAY-01, PAY-02, PAY-03, PAY-04, TAX-01, TAX-04]

# Metrics
duration: 7min
completed: 2026-03-18
---

# Phase 3 Plan 1: Payment Infrastructure Summary

**Payment model extensions, Robokassa HMAC-signed URL service, Fernet credential encryption, QR code generation, and PaymentService orchestrating 3 payment flows (manual/Robokassa/requisites) with fiscalization support**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-18T03:43:17Z
- **Completed:** 2026-03-18T03:50:36Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Extended Payment and Master models with all payment, Robokassa, and fiscalization columns
- Built 3 utility services: EncryptionService (Fernet), RobokassaService (HMAC signatures + receipt JSON), QrService (base64 PNG)
- Created PaymentService with 7 methods covering all 3 payment flows and history/cancellation
- Added payment and settings schemas for API consumption with proper validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migration, model extensions, and utility services** - `0787592` (feat)
2. **Task 2: PaymentService and payment schemas** - `f2902ad` (feat)

## Files Created/Modified

- `backend/alembic/versions/004_add_payment_and_settings_columns.py` - Migration adding 5 payment columns, 11 master columns, composite index, InvId sequence
- `backend/app/models/payment.py` - Extended with robokassa_inv_id, fiscalization_level, receipt_data, receipt_id, payment_url
- `backend/app/models/master.py` - Extended with card_number, sbp_phone, bank_name, Robokassa credentials (encrypted), fiscalization settings
- `backend/app/core/config.py` - Added encryption_key and robokassa_result_url to Settings
- `backend/app/services/encryption_service.py` - Fernet encrypt/decrypt for credential storage
- `backend/app/services/robokassa_service.py` - Payment URL generation, callback signature verification, receipt JSON builder
- `backend/app/services/qr_service.py` - QR code PNG generation as base64
- `backend/app/services/payment_service.py` - PaymentService with 7 methods + format_receipt_data helper
- `backend/app/schemas/payment.py` - PaymentCreate, RobokassaPaymentCreate, PaymentRead, PaymentListResponse, etc.
- `backend/app/schemas/settings.py` - Extended with PaymentSettings, PaymentSettingsUpdate, RobokassaSetup, RobokassaDisconnect
- `backend/pyproject.toml` - Added cryptography, qrcode, pillow dependencies

## Decisions Made

- **Fernet encryption:** Used cryptography.fernet for Robokassa password encryption. Single ENCRYPTION_KEY env var, base64-encoded ciphertext in DB columns.
- **Pillow for QR:** Installed pillow as qrcode image backend instead of relying on pypng pure-Python fallback. More reliable PNG output.
- **Shp_ routing params:** Payment URL includes Shp_master_id and Shp_booking_id for callback routing back to the correct master and booking.
- **Idempotent callbacks:** handle_robokassa_callback returns True without re-processing if payment is already "paid". Prevents duplicate status transitions.
- **SELECT FOR UPDATE:** Used on payment mutation queries (confirm, cancel, callback) to prevent race conditions from concurrent requests.
- **Fiscalization cascade:** Per-payment override > master default. Manual fiscalization populates receipt_data JSON immediately at payment creation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed Pillow for qrcode image generation**
- **Found during:** Task 1 (QR service verification)
- **Issue:** qrcode library's default make_image() requires PIL (Pillow) which was not installed
- **Fix:** Ran `uv add "qrcode[pil]"` to install pillow 12.1.1 alongside qrcode
- **Files modified:** backend/pyproject.toml, backend/uv.lock
- **Verification:** generate_payment_qr('+79161234567') returns valid base64 PNG (404 chars)
- **Committed in:** 0787592 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking dependency)
**Impact on plan:** Necessary for QR service to function. No scope creep.

## Issues Encountered

- Database (PostgreSQL) is not accessible in the current environment (Docker not in PATH). Migration 004 is written and will apply on next `docker compose up` / `alembic upgrade head`. All services verified at Python import and unit level without database.

## User Setup Required

Add to `.env` file (already done for local dev):
- `ENCRYPTION_KEY` - Fernet key generated with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `ROBOKASSA_RESULT_URL` - Public URL for Robokassa callback (e.g. `https://yourdomain.com/webhook/robokassa/result`)

## Next Phase Readiness

- Payment models, services, and schemas are ready for API endpoint creation (Plan 03-02)
- PaymentService methods are designed to be called directly from FastAPI route handlers
- Settings schemas ready for extending the master settings API with payment configuration
- Robokassa callback handler ready for webhook route registration

## Self-Check: PASSED

All 6 created files verified on disk. Both task commits (0787592, f2902ad) verified in git log.

---
*Phase: 03-payments-tax-receipts*
*Completed: 2026-03-18*
