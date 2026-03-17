# Requirements: Master-CRM

**Defined:** 2026-03-17
**Core Value:** Master taps "Complete" -- client gets SBP payment link -- tax receipt auto-generates. 3 steps instead of 9.

## v1 Requirements

### Booking (BOOK)

- [ ] **BOOK-01**: Master can create a service catalog (name, duration, price, category)
- [ ] **BOOK-02**: Master can configure schedule (working hours per day, breaks, days off)
- [ ] **BOOK-03**: Client can see available slots and book (select service -> date -> time)
- [ ] **BOOK-04**: System prevents double-booking (PostgreSQL exclusion constraints)
- [ ] **BOOK-05**: Client can cancel or reschedule a booking (with configurable deadline)
- [ ] **BOOK-06**: Master can cancel, reschedule, or manually add a booking
- [ ] **BOOK-07**: Master receives notification about new booking/cancellation via bot

### Clients (CLNT)

- [ ] **CLNT-01**: Client database auto-populated from bookings (name, phone)
- [ ] **CLNT-02**: Client identified by phone number (E.164 normalization)
- [ ] **CLNT-03**: Master can view client visit history
- [ ] **CLNT-04**: Client from different messengers recognized as one person by phone

### Notifications (NOTF)

- [ ] **NOTF-01**: Automated reminder to client 24h before visit via bot
- [ ] **NOTF-02**: Automated reminder to client 2h before visit via bot
- [ ] **NOTF-03**: Booking confirmation to client immediately after booking

### Payments (PAY)

- [ ] **PAY-01**: Master can complete a visit and mark "Paid" (simple mode, cash/card-to-card)
- [ ] **PAY-02**: Master can optionally connect their own Robokassa for automatic SBP link
- [ ] **PAY-03**: With Robokassa connected: master taps "Complete" -> client gets SBP payment link
- [ ] **PAY-04**: Payment history with statuses (pending, paid, cancelled)

### Tax Receipts (TAX)

- [ ] **TAX-01**: Three fiscalization levels: no receipts / manual / automatic
- [ ] **TAX-02**: No receipts: master sees warning but can continue
- [ ] **TAX-03**: Manual: after payment, CRM shows ready data for "Moy Nalog" (amount, service, client)
- [ ] **TAX-04**: Automatic: with Robokassa connected, receipt auto-generated via Robochecks -> FNS

### Messengers (MSG)

- [ ] **MSG-01**: Telegram Bot -- webhook processing, notifications to master and clients
- [ ] **MSG-02**: Telegram Mini App -- client booking, master management
- [ ] **MSG-03**: MAX Bot -- webhook processing, notifications
- [ ] **MSG-04**: MAX Mini App -- same functionality as TG Mini App
- [ ] **MSG-05**: VK Bot -- webhook processing, notifications
- [ ] **MSG-06**: VK Mini App -- same functionality as TG Mini App
- [ ] **MSG-07**: Unified React Mini App code with platform detection (TG/MAX/VK bridge adapters)
- [ ] **MSG-08**: Messenger Adapter pattern on backend (unified notification router)

### Web Panel (WEB)

- [ ] **WEB-01**: Web panel -- calendar and booking list (day/week view)
- [ ] **WEB-02**: Web panel -- client management (list, visit history)
- [ ] **WEB-03**: Web panel -- service CRUD (create, edit, delete, categories)
- [ ] **WEB-04**: Web panel -- payment history and receipt statuses
- [ ] **WEB-05**: Web panel -- schedule settings and master profile

### Infrastructure (INFR)

- [ ] **INFR-01**: FastAPI backend with PostgreSQL, deployed in Docker Compose on VPS
- [ ] **INFR-02**: REST API for mini-app and web panel
- [ ] **INFR-03**: Webhook handlers for TG, MAX, VK bots
- [ ] **INFR-04**: Master authentication (registration/login via messenger)
- [ ] **INFR-05**: Multi-tenant isolation (master_id on all tables, PostgreSQL RLS)

## v2 Requirements

### Analytics

- **ANLYT-01**: Revenue per period (day/week/month)
- **ANLYT-02**: Booking count and conversion
- **ANLYT-03**: Repeat client percentage

### Client Engagement

- **ENGMT-01**: Client notes and tags
- **ENGMT-02**: Repeat visit invitations ("You haven't visited in 30 days")
- **ENGMT-03**: Master photo portfolio in mini-app

### Finance

- **FIN-01**: Income/expense tracking
- **FIN-02**: Report export (PDF/Excel)

### Growth

- **GRWTH-01**: Subscription model (Free/Pro/Business)
- **GRWTH-02**: Onboarding wizard for new master
- **GRWTH-03**: Review collection and display

## Out of Scope

| Feature | Reason |
|---------|--------|
| Inventory/stock management | Overkill for solo master |
| Payroll | CRM for solo, not salons |
| Loyalty programs | Complex, low ROI for solo |
| Telephony | Messengers replace this |
| Multi-branch management | Solo focus |
| Native mobile app | Mini-apps in messengers replace this |
| Marketplace/master catalog | Different business, requires two-sided market |
| Email campaigns | Clients are in messengers |
| AI chatbot for clients | Premature complexity, bot menu is faster |
| Complex analytics (funnels) | Solo masters are not analysts |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFR-01 | Phase 1 | Pending |
| INFR-02 | Phase 1 | Pending |
| INFR-04 | Phase 1 | Pending |
| INFR-05 | Phase 1 | Pending |
| CLNT-02 | Phase 1 | Pending |
| BOOK-01 | Phase 2 | Pending |
| BOOK-02 | Phase 2 | Pending |
| BOOK-03 | Phase 2 | Pending |
| BOOK-04 | Phase 2 | Pending |
| BOOK-05 | Phase 2 | Pending |
| BOOK-06 | Phase 2 | Pending |
| CLNT-01 | Phase 2 | Pending |
| CLNT-03 | Phase 2 | Pending |
| MSG-01 | Phase 2 | Pending |
| MSG-02 | Phase 2 | Pending |
| MSG-07 | Phase 2 | Pending |
| MSG-08 | Phase 2 | Pending |
| INFR-03 | Phase 2 | Pending |
| PAY-01 | Phase 3 | Pending |
| PAY-02 | Phase 3 | Pending |
| PAY-03 | Phase 3 | Pending |
| PAY-04 | Phase 3 | Pending |
| TAX-01 | Phase 3 | Pending |
| TAX-02 | Phase 3 | Pending |
| TAX-03 | Phase 3 | Pending |
| TAX-04 | Phase 3 | Pending |
| NOTF-01 | Phase 4 | Pending |
| NOTF-02 | Phase 4 | Pending |
| NOTF-03 | Phase 4 | Pending |
| BOOK-07 | Phase 4 | Pending |
| MSG-03 | Phase 5 | Pending |
| MSG-04 | Phase 5 | Pending |
| MSG-05 | Phase 5 | Pending |
| MSG-06 | Phase 5 | Pending |
| CLNT-04 | Phase 5 | Pending |
| WEB-01 | Phase 6 | Pending |
| WEB-02 | Phase 6 | Pending |
| WEB-03 | Phase 6 | Pending |
| WEB-04 | Phase 6 | Pending |
| WEB-05 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 40 total
- Mapped to phases: 40
- Unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after roadmap creation*
