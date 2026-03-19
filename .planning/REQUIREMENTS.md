# Requirements: Master-CRM

**Defined:** 2026-03-17
**Core Value:** Master taps "Complete" -- client gets SBP payment link -- tax receipt auto-generates. 3 steps instead of 9.

## v1 Requirements

### Booking (BOOK)

- [x] **BOOK-01**: Master can create a service catalog (name, duration, price, category)
- [x] **BOOK-02**: Master can configure schedule (working hours per day, breaks, days off)
- [x] **BOOK-03**: Client can see available slots and book (select service -> date -> time)
- [x] **BOOK-04**: System prevents double-booking (PostgreSQL exclusion constraints)
- [x] **BOOK-05**: Client can cancel or reschedule a booking (with configurable deadline)
- [x] **BOOK-06**: Master can cancel, reschedule, or manually add a booking
- [x] **BOOK-07**: Master receives notification about new booking/cancellation via bot

### Clients (CLNT)

- [x] **CLNT-01**: Client database auto-populated from bookings (name, phone)
- [x] **CLNT-02**: Client identified by phone number (E.164 normalization)
- [x] **CLNT-03**: Master can view client visit history
- [x] **CLNT-04**: Client from different messengers recognized as one person by phone

### Notifications (NOTF)

- [x] **NOTF-01**: Automated reminder to client 24h before visit via bot
- [x] **NOTF-02**: Automated reminder to client 2h before visit via bot
- [x] **NOTF-03**: Booking confirmation to client immediately after booking

### Payments (PAY)

- [x] **PAY-01**: Master can complete a visit and mark "Paid" (simple mode, cash/card-to-card)
- [x] **PAY-02**: Master can optionally connect their own Robokassa for automatic SBP link
- [x] **PAY-03**: With Robokassa connected: master taps "Complete" -> client gets SBP payment link
- [x] **PAY-04**: Payment history with statuses (pending, paid, cancelled)

### Tax Receipts (TAX)

- [x] **TAX-01**: Three fiscalization levels: no receipts / manual / automatic
- [x] **TAX-02**: No receipts: master sees warning but can continue
- [x] **TAX-03**: Manual: after payment, CRM shows ready data for "Moy Nalog" (amount, service, client)
- [x] **TAX-04**: Automatic: with Robokassa connected, receipt auto-generated via Robochecks -> FNS

### Messengers (MSG)

- [x] **MSG-01**: Telegram Bot -- webhook processing, notifications to master and clients
- [x] **MSG-02**: Telegram Mini App -- client booking, master management
- [x] **MSG-03**: MAX Bot -- webhook processing, notifications
- [x] **MSG-04**: MAX Mini App -- same functionality as TG Mini App
- [x] **MSG-05**: VK Bot -- webhook processing, notifications
- [x] **MSG-06**: VK Mini App -- same functionality as TG Mini App
- [x] **MSG-07**: Unified React Mini App code with platform detection (TG/MAX/VK bridge adapters)
- [x] **MSG-08**: Messenger Adapter pattern on backend (unified notification router)

### Web Panel (WEB)

- [x] **WEB-01**: Web panel -- calendar and booking list (day/week view)
- [x] **WEB-02**: Web panel -- client management (list, visit history)
- [x] **WEB-03**: Web panel -- service CRUD (create, edit, delete, categories)
- [x] **WEB-04**: Web panel -- payment history and receipt statuses
- [x] **WEB-05**: Web panel -- schedule settings and master profile

### Infrastructure (INFR)

- [x] **INFR-01**: FastAPI backend with PostgreSQL, deployed in Docker Compose on VPS
- [x] **INFR-02**: REST API for mini-app and web panel
- [x] **INFR-03**: Webhook handlers for TG, MAX, VK bots
- [x] **INFR-04**: Master authentication (registration/login via messenger)
- [x] **INFR-05**: Multi-tenant isolation (master_id on all tables, PostgreSQL RLS)

## v1.1 Requirements — UX Polish

### Mini-App Accessibility (MACC)

- [x] **MACC-01**: Accent color passes WCAG AA contrast (≥4.5:1 on white)
- [ ] **MACC-02**: All async list containers have `aria-live="polite"` for screen readers
- [x] **MACC-03**: PaymentSheet has focus trap and `aria-labelledby`
- [x] **MACC-04**: Settings toggle has `role="switch"` and `aria-checked`
- [x] **MACC-05**: BottomTabBar has `aria-label` on both active and inactive tabs

### Mini-App Mobile UX (MMUX)

- [x] **MMUX-01**: BottomTabBar safe-area does not collapse touch targets on iPhone (min-h instead of fixed h)
- [x] **MMUX-02**: Services delete button accessible on touch (not hover-only)
- [x] **MMUX-03**: All filter pills and action buttons meet 44px minimum touch target
- [ ] **MMUX-04**: Error states on all master-panel pages (Dashboard, Services, Schedule, Bookings, Clients, ClientDetail, Settings, PaymentHistory)
- [x] **MMUX-05**: DatePicker has 300ms settle delay before auto-advance (matching ServiceSelection pattern)

### Mini-App Visual Polish (MVIS)

- [x] **MVIS-01**: Telegram theme CSS variables supported (--tg-theme-bg-color, dark mode adaptation)
- [x] **MVIS-02**: Named typography tokens (text-heading, text-body, text-caption) instead of raw px
- [x] **MVIS-03**: Badge colors use design tokens instead of raw Tailwind colors
- [x] **MVIS-04**: Elevation hierarchy: bottom sheets and modals have progressively stronger shadows
- [x] **MVIS-05**: PillButton extracted into shared component (deduplicated from 3 implementations)
- [x] **MVIS-06**: Confirmation screen has celebratory moment (larger heading, entrance animation)
- [x] **MVIS-07**: BottomTabBar label transition animated (not instant appear/disappear)
- [x] **MVIS-08**: Button active state includes subtle scale transform

### Web Admin Critical (WCRT)

- [ ] **WCRT-01**: Calendar page has "Create booking" entry point (button + click-on-slot)
- [ ] **WCRT-02**: BookingDrawer has action buttons (complete, no-show, reschedule) not just cancel
- [ ] **WCRT-03**: StatusTag and AdminLayout use plain UTF-8 Russian strings (not Unicode escapes)
- [ ] **WCRT-04**: Magic link redirect uses React Router navigate (not hardcoded window.location)
- [ ] **WCRT-05**: All tables have Russian empty states (not English "No data")
- [ ] **WCRT-06**: SettingsPage uses App.useApp() message API (not static import)

### Web Admin UX (WAUX)

- [ ] **WAUX-01**: Dark mode toggle has distinct icons for on/off states + aria-label
- [ ] **WAUX-02**: Header has breadcrumb and master profile/business name display
- [ ] **WAUX-03**: PaymentsPage RangePicker resets page to 1 on change
- [ ] **WAUX-04**: PaymentsPage shows total revenue statistic (not just count)
- [ ] **WAUX-05**: ClientsPage has total count badge and proper pagination controls
- [ ] **WAUX-06**: Sidebar collapse state persisted to localStorage
- [ ] **WAUX-07**: Schedule exceptions form fields hidden when is_day_off is true
- [ ] **WAUX-08**: CalendarPage uses subtle loading indicator (not full Spin overlay)
- [ ] **WAUX-09**: Page titles set per route (document.title for tab identification)
- [ ] **WAUX-10**: QueryClient configured with staleTime for non-realtime data (services, clients, settings)

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
| INFR-01 | Phase 1 | Complete |
| INFR-02 | Phase 1 | Complete |
| INFR-04 | Phase 1 | Complete |
| INFR-05 | Phase 1 | Complete |
| CLNT-02 | Phase 1 | Complete |
| BOOK-01 | Phase 2 | Complete |
| BOOK-02 | Phase 2 | Complete |
| BOOK-03 | Phase 2 | Complete |
| BOOK-04 | Phase 2 | Complete |
| BOOK-05 | Phase 2 | Complete |
| BOOK-06 | Phase 2 | Complete |
| CLNT-01 | Phase 2 | Complete |
| CLNT-03 | Phase 2 | Complete |
| MSG-01 | Phase 2 | Complete |
| MSG-02 | Phase 2 | Complete |
| MSG-07 | Phase 2 | Complete |
| MSG-08 | Phase 2 | Complete |
| INFR-03 | Phase 2 | Complete |
| PAY-01 | Phase 3 | Complete |
| PAY-02 | Phase 3 | Complete |
| PAY-03 | Phase 3 | Complete |
| PAY-04 | Phase 3 | Complete |
| TAX-01 | Phase 3 | Complete |
| TAX-02 | Phase 3 | Complete |
| TAX-03 | Phase 3 | Complete |
| TAX-04 | Phase 3 | Complete |
| NOTF-01 | Phase 4 | Complete |
| NOTF-02 | Phase 4 | Complete |
| NOTF-03 | Phase 4 | Complete |
| BOOK-07 | Phase 4 | Complete |
| MSG-03 | Phase 5 | Complete |
| MSG-04 | Phase 5 | Complete |
| MSG-05 | Phase 5 | Complete |
| MSG-06 | Phase 5 | Complete |
| CLNT-04 | Phase 5 | Complete |
| WEB-01 | Phase 6 | Complete |
| WEB-02 | Phase 6 | Complete |
| WEB-03 | Phase 6 | Complete |
| WEB-04 | Phase 6 | Complete |
| WEB-05 | Phase 6 | Complete |
| MACC-01 | Phase 7 | Complete |
| MACC-02 | Phase 7 | Pending |
| MACC-03 | Phase 7 | Complete |
| MACC-04 | Phase 7 | Complete |
| MACC-05 | Phase 7 | Complete |
| MMUX-01 | Phase 7 | Complete |
| MMUX-02 | Phase 7 | Complete |
| MMUX-03 | Phase 7 | Complete |
| MMUX-04 | Phase 7 | Pending |
| MMUX-05 | Phase 7 | Complete |
| MVIS-01 | Phase 7 | Complete |
| MVIS-02 | Phase 7 | Complete |
| MVIS-03 | Phase 7 | Complete |
| MVIS-04 | Phase 7 | Complete |
| MVIS-05 | Phase 7 | Complete |
| MVIS-06 | Phase 7 | Complete |
| MVIS-07 | Phase 7 | Complete |
| MVIS-08 | Phase 7 | Complete |
| WCRT-01 | Phase 8 | Pending |
| WCRT-02 | Phase 8 | Pending |
| WCRT-03 | Phase 8 | Pending |
| WCRT-04 | Phase 8 | Pending |
| WCRT-05 | Phase 8 | Pending |
| WCRT-06 | Phase 8 | Pending |
| WAUX-01 | Phase 8 | Pending |
| WAUX-02 | Phase 8 | Pending |
| WAUX-03 | Phase 8 | Pending |
| WAUX-04 | Phase 8 | Pending |
| WAUX-05 | Phase 8 | Pending |
| WAUX-06 | Phase 8 | Pending |
| WAUX-07 | Phase 8 | Pending |
| WAUX-08 | Phase 8 | Pending |
| WAUX-09 | Phase 8 | Pending |
| WAUX-10 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 40 total, mapped: 40, unmapped: 0
- v1.1 requirements: 34 total, mapped: 34, unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-19 after v1.1 roadmap creation*
