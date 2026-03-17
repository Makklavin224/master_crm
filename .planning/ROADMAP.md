# Roadmap: Master-CRM

## Overview

Master-CRM delivers a multi-messenger CRM for self-employed professionals in Russia. The build follows the core dependency chain: data model and infrastructure first, then the booking engine with Telegram as the first messenger, then the killer differentiator (SBP payments + auto tax receipts), then automated reminders, then multi-messenger expansion (MAX + VK), and finally the web admin panel. Each phase delivers a complete, verifiable capability. Telegram is built first to validate the full booking-to-payment-to-receipt flow before adding multi-messenger complexity.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Project scaffolding, data model, auth, Docker deployment
- [ ] **Phase 2: Booking Engine + Telegram** - Service catalog, schedule, booking flow, TG bot + mini-app
- [ ] **Phase 3: Payments + Tax Receipts** - Robokassa SBP payments, three-tier fiscalization, auto-receipts
- [ ] **Phase 4: Notifications** - Automated reminders (24h/2h), booking confirmations, master alerts
- [ ] **Phase 5: Multi-Messenger Expansion** - MAX bot + mini-app, VK bot + mini-app, cross-messenger client identity
- [ ] **Phase 6: Web Admin Panel** - Desktop management panel with Ant Design (calendar, clients, services, payments)

## Phase Details

### Phase 1: Foundation
**Goal**: The backend is running, the database schema captures all domain entities, masters can authenticate, and the project deploys via Docker Compose
**Depends on**: Nothing (first phase)
**Requirements**: INFR-01, INFR-02, INFR-04, INFR-05, CLNT-02
**Success Criteria** (what must be TRUE):
  1. FastAPI application starts and responds to health check requests behind Caddy reverse proxy
  2. PostgreSQL database contains all core tables (masters, services, clients, client_platforms, bookings, payments, schedules) with master_id scoping and RLS policies
  3. A master can register and log in, receiving a JWT token that authenticates subsequent API requests
  4. Phone numbers are normalized to E.164 format at the API boundary ("+79161234567" and "89161234567" resolve to the same client record)
  5. The entire stack (FastAPI + PostgreSQL + Caddy) deploys with a single `docker compose up` command on a VPS
**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md -- Scaffolding, Docker stack, domain models, Alembic migrations, phone normalization, RLS policies
- [ ] 01-02-PLAN.md -- Auth system (register/login/me), REST API structure, integration tests, stack verification

### Phase 2: Booking Engine + Telegram
**Goal**: Clients can discover services, view available slots, and book appointments through the Telegram mini-app; masters receive notifications and can manage bookings through the TG bot and mini-app
**Depends on**: Phase 1
**Requirements**: BOOK-01, BOOK-02, BOOK-03, BOOK-04, BOOK-05, BOOK-06, CLNT-01, CLNT-03, MSG-01, MSG-02, MSG-07, MSG-08, INFR-03
**Success Criteria** (what must be TRUE):
  1. Master can create a service catalog (name, duration, price, category) and configure working hours (per-day hours, breaks, days off) via the API
  2. Client opens the TG mini-app, sees available services, picks a date, sees only genuinely free time slots, and completes a booking
  3. Two clients attempting to book the same slot simultaneously results in one success and one rejection (no double-booking)
  4. Client can cancel or reschedule a booking (respecting the master's configurable deadline); master can cancel, reschedule, or manually add a booking
  5. Master receives a Telegram bot notification when a new booking is created or cancelled; client data (name, phone) is auto-captured into the client database with visit history visible
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD
- [ ] 02-03: TBD
- [ ] 02-04: TBD

### Phase 3: Payments + Tax Receipts
**Goal**: Masters can complete a visit and collect payment; when Robokassa is connected, the client receives an SBP payment link and a tax receipt is automatically generated in "Moy Nalog"
**Depends on**: Phase 2
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, TAX-01, TAX-02, TAX-03, TAX-04
**Success Criteria** (what must be TRUE):
  1. Master without Robokassa can mark a visit as "Paid" (simple mode -- cash or card-to-card) and the payment appears in history
  2. Master can connect their own Robokassa account in settings; after connecting, tapping "Complete" on a visit sends the client an SBP payment link via the messenger bot
  3. When the client pays via SBP, the Robokassa callback is processed idempotently (duplicate callbacks do not create duplicate payments) and the payment status updates to "Paid"
  4. Master can choose one of three fiscalization levels: no receipts (with a warning), manual (CRM shows ready-to-copy data for "Moy Nalog"), or automatic (Robochecks generates the receipt via FNS)
  5. Payment history shows all transactions with statuses (pending, paid, cancelled) and receipt statuses (not applicable, pending, issued)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Notifications
**Goal**: Clients receive automated booking confirmations and reminders through their messenger; masters receive alerts about new bookings and cancellations
**Depends on**: Phase 2
**Requirements**: NOTF-01, NOTF-02, NOTF-03, BOOK-07
**Success Criteria** (what must be TRUE):
  1. Client receives an immediate booking confirmation message via the messenger bot after completing a booking
  2. Client receives automated reminder messages 24 hours and 2 hours before their appointment (timezone-aware, via the messenger they booked through)
  3. Master receives bot notifications for new bookings, cancellations, and reschedules
  4. Reminders are processed idempotently (server restart does not cause duplicate reminders; past-due reminders are skipped, not queued)
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Multi-Messenger Expansion
**Goal**: The same booking, payment, and notification experience works in MAX and VK messengers; clients from different messengers are recognized as the same person by phone number
**Depends on**: Phase 2, Phase 4
**Requirements**: MSG-03, MSG-04, MSG-05, MSG-06, CLNT-04
**Success Criteria** (what must be TRUE):
  1. Client can open the mini-app in MAX, see the master's services, and complete a booking (same experience as TG)
  2. Client can open the mini-app in VK, see the master's services, and complete a booking (same experience as TG)
  3. MAX and VK bots send booking confirmations, reminders, and master alerts (same notification behavior as TG)
  4. A client who books via TG and later opens the VK mini-app sees their existing booking history (cross-messenger identity via phone number)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD
- [ ] 05-03: TBD

### Phase 6: Web Admin Panel
**Goal**: Masters can manage their entire business from a desktop web panel -- schedule, clients, services, payments, and settings
**Depends on**: Phase 3
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05
**Success Criteria** (what must be TRUE):
  1. Master can view their schedule in day and week views, seeing all bookings with client names, services, and times
  2. Master can search clients by name or phone and view each client's full visit history
  3. Master can create, edit, and delete services with categories; changes are immediately reflected in the mini-app
  4. Master can view payment history with statuses and receipt statuses; can configure schedule settings (working hours, breaks, days off) and profile information
**Plans**: TBD

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD
- [ ] 06-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Note: Phase 4 (Notifications) depends on Phase 2 only. Phase 6 (Web Panel) depends on Phase 3 only. Phases 4-5 and Phase 6 could potentially overlap after their dependencies are met.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/2 | Planning complete | - |
| 2. Booking Engine + Telegram | 0/4 | Not started | - |
| 3. Payments + Tax Receipts | 0/3 | Not started | - |
| 4. Notifications | 0/2 | Not started | - |
| 5. Multi-Messenger Expansion | 0/3 | Not started | - |
| 6. Web Admin Panel | 0/3 | Not started | - |
