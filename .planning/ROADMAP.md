# Roadmap: Master-CRM

## Milestones

- **v1.0 MVP** - Phases 1-6 (shipped 2026-03-18)
- **v1.1 UX Polish** - Phases 7-8 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v1.0 MVP (Phases 1-6) -- SHIPPED 2026-03-18</summary>

- [x] **Phase 1: Foundation** - Project scaffolding, data model, auth, Docker deployment (completed 2026-03-17)
- [x] **Phase 2: Booking Engine + Telegram** - Service catalog, schedule, booking flow, TG bot + mini-app (completed 2026-03-17)
- [x] **Phase 3: Payments + Tax Receipts** - Robokassa SBP payments, three-tier fiscalization, auto-receipts (completed 2026-03-18)
- [x] **Phase 4: Notifications** - Automated reminders (24h/2h), booking confirmations, master alerts (completed 2026-03-18)
- [x] **Phase 5: Multi-Messenger Expansion** - MAX bot + mini-app, VK bot + mini-app, cross-messenger client identity (completed 2026-03-18)
- [x] **Phase 6: Web Admin Panel** - Desktop management panel with Ant Design (calendar, clients, services, payments) (completed 2026-03-18)

</details>

### v1.1 UX Polish (In Progress)

- [ ] **Phase 7: Mini-App UX Polish** - Accessibility, mobile UX, visual polish, and Telegram theme support
- [ ] **Phase 8: Web Admin UX Polish** - Critical fixes, missing features, and UX improvements for the admin panel

## Phase Details

<details>
<summary>v1.0 MVP Phase Details (Phases 1-6)</summary>

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
**Plans:** 2/2 plans complete

Plans:
- [x] 01-01-PLAN.md -- Scaffolding, Docker stack, domain models, Alembic migrations, phone normalization, RLS policies
- [x] 01-02-PLAN.md -- Auth system (register/login/me), REST API structure, integration tests, stack verification

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
**Plans:** 4/4 plans complete

Plans:
- [x] 02-01-PLAN.md -- Backend booking engine: service CRUD, schedule management, slot calculation, booking CRUD with double-booking prevention, client auto-population
- [x] 02-02-PLAN.md -- Telegram bot: aiogram webhook integration, command handlers (/start, /today, /link, /settings), MessengerAdapter notification pattern
- [x] 02-03-PLAN.md -- React mini-app: platform detection shell, UI components per design contract, 5-step client booking flow
- [x] 02-04-PLAN.md -- Master management panel: dashboard, service CRUD, schedule editor, booking management, client list with history, settings

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
**Plans:** 3/3 plans complete

Plans:
- [x] 03-01-PLAN.md -- Backend payment infrastructure: Alembic migration, model extensions, encryption/QR/Robokassa services, PaymentService orchestration
- [x] 03-02-PLAN.md -- Payment API endpoints, Robokassa webhook, notification extensions, comprehensive test suite
- [x] 03-03-PLAN.md -- Frontend payment UI: PaymentSheet (3 options), PaymentHistory, ReceiptDataCard, RobokassaWizard, Settings payment sections

### Phase 4: Notifications
**Goal**: Clients receive automated booking confirmations and reminders through their messenger; masters receive alerts about new bookings and cancellations
**Depends on**: Phase 2
**Requirements**: NOTF-01, NOTF-02, NOTF-03, BOOK-07
**Success Criteria** (what must be TRUE):
  1. Client receives an immediate booking confirmation message via the messenger bot after completing a booking
  2. Client receives automated reminder messages 24 hours and 2 hours before their appointment (timezone-aware, via the messenger they booked through)
  3. Master receives bot notifications for new bookings, cancellations, and reschedules
  4. Reminders are processed idempotently (server restart does not cause duplicate reminders; past-due reminders are skipped, not queued)
**Plans:** 2/2 plans complete

Plans:
- [x] 04-01-PLAN.md -- Backend notification infrastructure: models, migration, adapter extensions, booking confirmation, master alerts, notification settings API, client cancel callback, test suite
- [x] 04-02-PLAN.md -- APScheduler reminder service with polling and idempotency, frontend notification settings UI

### Phase 5: Multi-Messenger Expansion
**Goal**: The same booking, payment, and notification experience works in MAX and VK messengers; clients from different messengers are recognized as the same person by phone number
**Depends on**: Phase 2, Phase 4
**Requirements**: MSG-03, MSG-04, MSG-05, MSG-06, CLNT-04
**Success Criteria** (what must be TRUE):
  1. Client can open the mini-app in MAX, see the master's services, and complete a booking (same experience as TG)
  2. Client can open the mini-app in VK, see the master's services, and complete a booking (same experience as TG)
  3. MAX and VK bots send booking confirmations, reminders, and master alerts (same notification behavior as TG)
  4. A client who books via TG and later opens the VK mini-app sees their existing booking history (cross-messenger identity via phone number)
**Plans:** 3/3 plans complete

Plans:
- [x] 05-01-PLAN.md -- Shared backend infrastructure: config settings, MAX/VK validation functions, Master model columns (max_user_id, vk_user_id), Alembic migration, auth endpoints
- [x] 05-02-PLAN.md -- MAX full stack: bot adapter + handlers, webhook route, frontend MaxBridge adapter, platform detection
- [x] 05-03-PLAN.md -- VK full stack: bot adapter + handlers, webhook route with confirmation handshake, frontend VkBridge adapter, vk-bridge package

### Phase 6: Web Admin Panel
**Goal**: Masters can manage their entire business from a desktop web panel -- schedule, clients, services, payments, and settings
**Depends on**: Phase 3
**Requirements**: WEB-01, WEB-02, WEB-03, WEB-04, WEB-05
**Success Criteria** (what must be TRUE):
  1. Master can view their schedule in day and week views, seeing all bookings with client names, services, and times
  2. Master can search clients by name or phone and view each client's full visit history
  3. Master can create, edit, and delete services with categories; changes are immediately reflected in the mini-app
  4. Master can view payment history with statuses and receipt statuses; can configure schedule settings (working hours, breaks, days off) and profile information
**Plans:** 3/3 plans complete

Plans:
- [x] 06-01-PLAN.md -- Project scaffolding, auth (email + QR + magic link), sidebar layout, theme toggle, Docker/Caddy integration
- [x] 06-02-PLAN.md -- Calendar page (FullCalendar day/week/month views) + Services page (CRUD table with modal)
- [x] 06-03-PLAN.md -- Clients page (search + detail), Payments page (history + filters), Settings page (schedule/notifications/payment/profile)

</details>

### Phase 7: Mini-App UX Polish
**Goal**: The mini-app meets accessibility standards, works flawlessly on mobile devices, and has a polished visual identity with Telegram theme integration
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: MACC-01, MACC-02, MACC-03, MACC-04, MACC-05, MMUX-01, MMUX-02, MMUX-03, MMUX-04, MMUX-05, MVIS-01, MVIS-02, MVIS-03, MVIS-04, MVIS-05, MVIS-06, MVIS-07, MVIS-08
**Success Criteria** (what must be TRUE):
  1. A screen reader user can navigate the mini-app: async content changes are announced, the PaymentSheet traps focus, toggles report their state, and tab bar items are labeled
  2. On an iPhone with safe-area insets, all touch targets (tab bar items, filter pills, action buttons, delete buttons) are at least 44px and fully reachable without accidental taps
  3. Every master-panel page (Dashboard, Services, Schedule, Bookings, Clients, ClientDetail, Settings, PaymentHistory) shows a meaningful Russian error state when the API call fails, instead of a blank screen or spinner
  4. Opening the mini-app in Telegram dark mode automatically adapts the color scheme via tg-theme CSS variables; accent colors pass WCAG AA contrast ratio (4.5:1) in both light and dark modes
  5. The UI uses named design tokens for typography, colors, and elevation; repeated components (PillButton) are deduplicated; confirmation screens and tab transitions have smooth animations
**Plans:** 3/5 plans executed

Plans:
- [ ] 07-01-PLAN.md -- Design tokens foundation: accessible accent color, Telegram theme CSS variables, typography and elevation tokens
- [ ] 07-02-PLAN.md -- BottomTabBar accessibility + safe-area + label animation, Button scale transform, Badge design tokens
- [ ] 07-03-PLAN.md -- PillSelector extraction + 44px touch targets + elevation hierarchy
- [ ] 07-04-PLAN.md -- PaymentSheet focus trap, Settings toggle a11y, Services delete touch, DatePicker delay, Confirmation polish
- [ ] 07-05-PLAN.md -- Error states and aria-live on all 8 master-panel pages

### Phase 8: Web Admin UX Polish
**Goal**: The web admin panel has complete booking workflow actions, correct Russian localization, and professional UX details that make daily use efficient
**Depends on**: Phase 7
**Requirements**: WCRT-01, WCRT-02, WCRT-03, WCRT-04, WCRT-05, WCRT-06, WAUX-01, WAUX-02, WAUX-03, WAUX-04, WAUX-05, WAUX-06, WAUX-07, WAUX-08, WAUX-09, WAUX-10
**Success Criteria** (what must be TRUE):
  1. Master can create a new booking directly from the calendar page (via a "Create" button or by clicking on an empty time slot) and can complete, mark no-show, or reschedule a booking from the BookingDrawer -- not just cancel
  2. All table empty states, status tags, and UI strings display correct Russian text (plain UTF-8 strings, no Unicode escape artifacts); magic link redirect uses React Router navigation
  3. The admin panel remembers sidebar collapse state across sessions, sets unique page titles per route, and configures smart data caching (stale services/clients are not refetched on every navigation)
  4. PaymentsPage shows total revenue alongside payment count, resets pagination when date range changes; ClientsPage shows total client count with proper pagination controls
  5. Dark mode toggle has distinct on/off icons with aria-label; header displays breadcrumb navigation and master's business name; schedule exception form hides irrelevant fields when "day off" is selected; calendar loading uses a subtle indicator instead of a full overlay spinner
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 -> 8

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 2/2 | Complete | 2026-03-17 |
| 2. Booking Engine + Telegram | v1.0 | 4/4 | Complete | 2026-03-17 |
| 3. Payments + Tax Receipts | v1.0 | 3/3 | Complete | 2026-03-18 |
| 4. Notifications | v1.0 | 2/2 | Complete | 2026-03-18 |
| 5. Multi-Messenger Expansion | v1.0 | 3/3 | Complete | 2026-03-18 |
| 6. Web Admin Panel | v1.0 | 3/3 | Complete | 2026-03-18 |
| 7. Mini-App UX Polish | 3/5 | In Progress|  | - |
| 8. Web Admin UX Polish | v1.1 | 0/? | Not started | - |
