# Phase 3: Payments + Tax Receipts - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Add payment processing and tax receipt functionality to the existing booking system. Masters can collect payment (manually or via Robokassa SBP), and the system handles tax receipts at three levels (no receipts, manual data for "Мой Налог", automatic via Robochecks). Extends the master panel with payment screens and adds payment-related notifications to clients.

</domain>

<decisions>
## Implementation Decisions

### Payment Flow (3 options for master)
- **Option 1: Внести доход вручную** — master records payment received (наличные/карта/перевод на карту/СБП). Just a record in the system.
- **Option 2: Отправить ссылку/QR клиенту** — via Robokassa SBP link (requires Robokassa connected). Client pays → callback → auto-confirmation.
- **Option 3: Показать реквизиты + QR** — CRM generates QR code with master's card number/phone. Client scans → opens banking app with prefilled transfer. Master confirms manually.
- Master chooses which option at each payment, not locked globally
- "Завершить" button on booking → payment options bottom sheet
- Payment can happen right after booking confirmation OR after actual visit — master decides when

### Simple Mode (without Robokassa)
- Master enters their payment requisites in Settings: card number, phone for SBP, bank name
- When requesting payment: CRM shows master's requisites to client + generated QR code
- Master taps "Оплачено" + selects payment method (наличные, карта, перевод, СБП)
- Payment recorded in history

### Robokassa Connection
- Poshаговый wizard in Settings: step-by-step guide with screenshots
- Master enters: merchant_login, password1 (for payment links), password2 (for callback validation)
- Test mode toggle (Robokassa test environment)
- Credentials stored encrypted in DB (per-master, not platform-level)

### Fiscalization (3 levels, set in Settings with per-payment override)
- Default level chosen in Settings (applies to all payments)
- Per-payment override: master can switch level for specific payment
- **Level 1 — Без чеков (серый):** One-time warning when selected in Settings ("Рекомендуем выставлять чеки для защиты от штрафов"). After that, no nagging.
- **Level 2 — Ручной:** After payment marked as paid, CRM shows ready-to-copy data for "Мой Налог": amount, service name, client name. Button "Скопировать данные" or "Открыть Мой Налог".
- **Level 3 — Автоматический:** Only with Robokassa connected. Receipt auto-generated via Robochecks СМЗ → ФНС. Status shown in payment history.

### Refunds & Cancellations
- Refunds are manual — master decides whether to return money. CRM shows status "отменено, оплачено" so master knows.
- No auto-refund through Robokassa in v1 (complex, edge cases)
- Receipt cancellation: if Robokassa connected → auto-cancel receipt via Robochecks. If manual mode → CRM reminds "Не забудьте отменить чек в Мой Налог".

### Payment History
- List of all payments with statuses: pending, paid, cancelled, refunded
- Receipt status: not applicable, pending, issued, cancelled
- Filterable by date range, status
- Visible in both mini-app master panel and web panel (Phase 6)

### Claude's Discretion
- QR code generation library
- Robokassa API integration details (HMAC signing, URL format)
- Robochecks API for receipt generation/cancellation
- Payment webhook security (idempotency, signature validation)
- Database migration for payment-related columns
- Encryption approach for Robokassa credentials
- Payment notification message format

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/PROJECT.md` — Pricing model, Robokassa context, three-tier fiscalization concept
- `.planning/REQUIREMENTS.md` — PAY-01..04, TAX-01..04

### Research
- `.planning/research/STACK.md` — Robokassa API, Robochecks integration approach
- `.planning/research/ARCHITECTURE.md` — Payment flow architecture, callback handling
- `.planning/research/PITFALLS.md` — Robokassa callback idempotency, receipt cancellation, Password case sensitivity

### Phase 1 & 2 Code
- `backend/app/models/payment.py` — PaymentModel (already exists from Phase 1)
- `backend/app/services/booking_service.py` — Booking CRUD with notification hooks
- `backend/app/bots/common/notification.py` — NotificationService for sending payment confirmations
- `backend/app/bots/telegram/adapter.py` — TelegramAdapter for HTML notifications
- `backend/app/api/v1/settings.py` — Master settings API (extend with payment settings)
- `frontend/src/pages/master/Settings.tsx` — Settings screen (extend with payment config)
- `frontend/src/pages/master/Bookings.tsx` — Booking list (add "Завершить" + payment flow)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/payment.py` — PaymentModel exists but may need extension (payment_method, receipt_status, robokassa fields)
- `backend/app/services/booking_service.py` — Has notification integration pattern (fire-and-forget)
- `backend/app/bots/common/adapter.py` — MessengerAdapter ABC with send_booking_notification()
- `backend/app/bots/common/notification.py` — NotificationService singleton
- `backend/app/core/security.py` — HMAC validation pattern (reusable for Robokassa signature)
- `frontend/src/components/ui/` — Button, Card, Badge, Toast, ConfirmDialog
- `frontend/src/api/` — TanStack Query hooks pattern established

### Established Patterns
- Routers → Services → Models (FastAPI)
- TDD with pytest (backend), vitest (frontend)
- Alembic migrations
- NotificationService adapter pattern
- TanStack Query + Zustand on frontend

### Integration Points
- Extend `PaymentModel` with new fields (migration)
- Add payment service alongside booking_service
- Add Robokassa callback webhook route to FastAPI
- Extend master Settings screen with payment configuration
- Add payment flow to Bookings screen (bottom sheet after "Завершить")
- Add payment notification to TelegramAdapter

</code_context>

<specifics>
## Specific Ideas

- QR code generation for manual payments — client scans → banking app opens with prefilled transfer data
- Robokassa wizard should have actual screenshots/instructions for where to find credentials
- "Скопировать данные" button for manual receipt mode — copies amount + service + client name formatted for "Мой Налог"
- Payment flow is a bottom sheet over the booking detail, not a separate screen

</specifics>

<deferred>
## Deferred Ideas

- Auto-refund through Robokassa API — too complex for v1, manual refunds sufficient
- Per-service pricing variants (short hair vs long hair pricing) — v2
- Subscription/recurring payment support — v2
- Revenue analytics from payments — Phase after all core features

</deferred>

---

*Phase: 03-payments-tax-receipts*
*Context gathered: 2026-03-18*
