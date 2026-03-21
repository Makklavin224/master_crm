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

- [x] **MACC-01**: Accent color passes WCAG AA contrast (>=4.5:1 on white)
- [x] **MACC-02**: All async list containers have `aria-live="polite"` for screen readers
- [x] **MACC-03**: PaymentSheet has focus trap and `aria-labelledby`
- [x] **MACC-04**: Settings toggle has `role="switch"` and `aria-checked`
- [x] **MACC-05**: BottomTabBar has `aria-label` on both active and inactive tabs

### Mini-App Mobile UX (MMUX)

- [x] **MMUX-01**: BottomTabBar safe-area does not collapse touch targets on iPhone (min-h instead of fixed h)
- [x] **MMUX-02**: Services delete button accessible on touch (not hover-only)
- [x] **MMUX-03**: All filter pills and action buttons meet 44px minimum touch target
- [x] **MMUX-04**: Error states on all master-panel pages (Dashboard, Services, Schedule, Bookings, Clients, ClientDetail, Settings, PaymentHistory)
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

- [x] **WCRT-01**: Calendar page has "Create booking" entry point (button + click-on-slot)
- [x] **WCRT-02**: BookingDrawer has action buttons (complete, no-show, reschedule) not just cancel
- [x] **WCRT-03**: StatusTag and AdminLayout use plain UTF-8 Russian strings (not Unicode escapes)
- [x] **WCRT-04**: Magic link redirect uses React Router navigate (not hardcoded window.location)
- [x] **WCRT-05**: All tables have Russian empty states (not English "No data")
- [x] **WCRT-06**: SettingsPage uses App.useApp() message API (not static import)

### Web Admin UX (WAUX)

- [x] **WAUX-01**: Dark mode toggle has distinct icons for on/off states + aria-label
- [x] **WAUX-02**: Header has breadcrumb and master profile/business name display
- [x] **WAUX-03**: PaymentsPage RangePicker resets page to 1 on change
- [x] **WAUX-04**: PaymentsPage shows total revenue statistic (not just count)
- [x] **WAUX-05**: ClientsPage has total count badge and proper pagination controls
- [x] **WAUX-06**: Sidebar collapse state persisted to localStorage
- [x] **WAUX-07**: Schedule exceptions form fields hidden when is_day_off is true
- [x] **WAUX-08**: CalendarPage uses subtle loading indicator (not full Spin overlay)
- [x] **WAUX-09**: Page titles set per route (document.title for tab identification)
- [x] **WAUX-10**: QueryClient configured with staleTime for non-realtime data (services, clients, settings)

## v2.0 Requirements — Feature Expansion

### Public Booking (PBUK)

- [x] **PBUK-01**: Master has a public profile page at /m/{username} with avatar, name, specialization, city, rating
- [x] **PBUK-02**: Master can set a unique username (latin lowercase + digits + underscore, 3-30 chars, reserved words blocked)
- [x] **PBUK-03**: Public page shows list of services with prices and "Zapisatsya" button
- [x] **PBUK-04**: Public page shows nearest available slots (3-5 days ahead)
- [x] **PBUK-05**: Client can book through web browser without a messenger (service -> date -> time -> phone+name -> confirm)
- [x] **PBUK-06**: Master can copy booking link and auto-generated QR code from settings
- [x] **PBUK-07**: Public page has SEO meta tags (title, description, OpenGraph with avatar)

### Client Cabinet (CCAB)

- [x] **CCAB-01**: Client can access cabinet at /my by entering phone number + 6-digit OTP
- [x] **CCAB-02**: OTP sent via messenger bot (TG/MAX/VK); SMS fallback for web-booked clients (~2 rub)
- [x] **CCAB-03**: OTP has 5-min expiration, max 3 attempts, 60-sec cooldown
- [x] **CCAB-04**: Client sees upcoming bookings with cancel/reschedule buttons
- [x] **CCAB-05**: Client sees past visits with "Zapisatsya snova" button (pre-fills master + service)
- [x] **CCAB-06**: Client can leave a review after completed visit (1-5 stars + optional text)
- [x] **CCAB-07**: Client sees bookings from all masters in one list

### Admin Payments (APAY)

- [x] **APAY-01**: Master can finish a visit from web admin with payment method selection (cash/card/SBP)
- [x] **APAY-02**: Payment amount pre-filled from service price, editable (discount/extra)
- [x] **APAY-03**: Fiscalization option on payment completion (auto/manual/none)
- [x] **APAY-04**: Payments page shows total revenue for selected period
- [x] **APAY-05**: Payments page has filter by payment method
- [x] **APAY-06**: Payments page has CSV export
- [x] **APAY-07**: Calendar event shows ruble icon for quick payment access

### Auto Receipts (ARCT)

- [x] **ARCT-01**: Master can bind INN in settings for auto-receipt via Robokassa ReceiptAttach
- [x] **ARCT-02**: When "auto receipt" selected, system sends receipt data to Robokassa ReceiptAttach
- [x] **ARCT-03**: Receipt works for all payment methods (cash, card, SBP) -- not just SBP
- [x] **ARCT-04**: Client receives receipt link in messenger after payment
- [x] **ARCT-05**: Failed receipt attempts retry 3 times via background job; error notification to master on failure

### Portfolio (PORT)

- [x] **PORT-01**: Master can upload up to 30 photos (max 5MB each, JPEG/PNG/WebP)
- [x] **PORT-02**: Photos auto-resized to 1200px and thumbnails generated (300px)
- [x] **PORT-03**: Photos displayed as gallery on public profile page with lightbox
- [x] **PORT-04**: Master can tag photos with service names for filtering
- [x] **PORT-05**: Upload available from both web admin and mini-app settings

### Reviews (REVW)

- [x] **REVW-01**: Bot sends review request to client 2 hours after completed visit
- [x] **REVW-02**: Client rates 1-5 stars + optional text (max 500 chars)
- [x] **REVW-03**: Reviews >=3 stars auto-publish; <3 stars require master reply
- [x] **REVW-04**: Negative reviews auto-publish after 7 days if master doesn't reply
- [x] **REVW-05**: Reviews displayed on public profile page with average rating
- [x] **REVW-06**: Only clients with real completed visits can leave reviews (1 per booking)

### Analytics (ANLT)

- [x] **ANLT-01**: Dashboard shows revenue, booking count, client count for selected period
- [x] **ANLT-02**: Revenue chart (line graph by day)
- [x] **ANLT-03**: New vs repeat clients (donut chart)
- [x] **ANLT-04**: Utilization rate (booked hours / scheduled hours)
- [x] **ANLT-05**: Average check amount
- [x] **ANLT-06**: Client retention rate (% returning within 60 days)
- [x] **ANLT-07**: Cancellation rate and no-show rate
- [x] **ANLT-08**: Top services table (service, count, revenue, % of total)
- [x] **ANLT-09**: Daily breakdown table (date, bookings, revenue, utilization)
- [x] **ANLT-10**: CSV export for reports

### Cross-Platform Auth (XAUTH)

- [ ] **XAUTH-01**: Bot /start recognizes existing master by phone/email, links platform user_id and issues JWT
- [ ] **XAUTH-02**: Mini-app auto-detects role: master → panel, client → booking flow (based on platform user_id in masters table)
- [ ] **XAUTH-03**: Master can link/unlink TG, MAX, VK accounts from web admin settings
- [ ] **XAUTH-04**: Master in mini-app has toggle to switch between "Панель мастера" and "Мои записи"
- [ ] **XAUTH-05**: New master can register through bot: enter email + phone → create Master → bind platform → JWT

## v3 Requirements (deferred)

### Client Engagement

- **ENGMT-01**: Client notes and tags
- **ENGMT-02**: Repeat visit invitations ("You haven't visited in 30 days")

### Finance

- **FIN-01**: Income/expense tracking
- **FIN-02**: Report export (PDF/Excel)

### Growth

- **GRWTH-01**: Subscription model (Free/Pro/Business)
- **GRWTH-02**: Onboarding wizard for new master
- **GRWTH-03**: Direct FNS API integration (after partner agreement)

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
| MACC-02 | Phase 7 | Complete |
| MACC-03 | Phase 7 | Complete |
| MACC-04 | Phase 7 | Complete |
| MACC-05 | Phase 7 | Complete |
| MMUX-01 | Phase 7 | Complete |
| MMUX-02 | Phase 7 | Complete |
| MMUX-03 | Phase 7 | Complete |
| MMUX-04 | Phase 7 | Complete |
| MMUX-05 | Phase 7 | Complete |
| MVIS-01 | Phase 7 | Complete |
| MVIS-02 | Phase 7 | Complete |
| MVIS-03 | Phase 7 | Complete |
| MVIS-04 | Phase 7 | Complete |
| MVIS-05 | Phase 7 | Complete |
| MVIS-06 | Phase 7 | Complete |
| MVIS-07 | Phase 7 | Complete |
| MVIS-08 | Phase 7 | Complete |
| WCRT-01 | Phase 8 | Complete |
| WCRT-02 | Phase 8 | Complete |
| WCRT-03 | Phase 8 | Complete |
| WCRT-04 | Phase 8 | Complete |
| WCRT-05 | Phase 8 | Complete |
| WCRT-06 | Phase 8 | Complete |
| WAUX-01 | Phase 8 | Complete |
| WAUX-02 | Phase 8 | Complete |
| WAUX-03 | Phase 8 | Complete |
| WAUX-04 | Phase 8 | Complete |
| WAUX-05 | Phase 8 | Complete |
| WAUX-06 | Phase 8 | Complete |
| WAUX-07 | Phase 8 | Complete |
| WAUX-08 | Phase 8 | Complete |
| WAUX-09 | Phase 8 | Complete |
| WAUX-10 | Phase 8 | Complete |
| PBUK-02 | Phase 9 | Complete |
| PBUK-01 | Phase 10 | Complete |
| PBUK-03 | Phase 10 | Complete |
| PBUK-04 | Phase 10 | Complete |
| PBUK-05 | Phase 10 | Complete |
| PBUK-06 | Phase 10 | Complete |
| PBUK-07 | Phase 10 | Complete |
| CCAB-01 | Phase 11 | Complete |
| CCAB-02 | Phase 11 | Complete |
| CCAB-03 | Phase 11 | Complete |
| CCAB-04 | Phase 11 | Complete |
| CCAB-05 | Phase 11 | Complete |
| CCAB-06 | Phase 11 | Complete |
| CCAB-07 | Phase 11 | Complete |
| APAY-01 | Phase 12 | Complete |
| APAY-02 | Phase 12 | Complete |
| APAY-03 | Phase 12 | Complete |
| APAY-04 | Phase 12 | Complete |
| APAY-05 | Phase 12 | Complete |
| APAY-06 | Phase 12 | Complete |
| APAY-07 | Phase 12 | Complete |
| ARCT-01 | Phase 13 | Complete |
| ARCT-02 | Phase 13 | Complete |
| ARCT-03 | Phase 13 | Complete |
| ARCT-04 | Phase 13 | Complete |
| ARCT-05 | Phase 13 | Complete |
| PORT-01 | Phase 14 | Complete |
| PORT-02 | Phase 14 | Complete |
| PORT-03 | Phase 14 | Complete |
| PORT-04 | Phase 14 | Complete |
| PORT-05 | Phase 14 | Complete |
| REVW-01 | Phase 15 | Complete |
| REVW-02 | Phase 15 | Complete |
| REVW-03 | Phase 15 | Complete |
| REVW-04 | Phase 15 | Complete |
| REVW-05 | Phase 15 | Complete |
| REVW-06 | Phase 15 | Complete |
| ANLT-01 | Phase 16 | Complete |
| ANLT-02 | Phase 16 | Complete |
| ANLT-03 | Phase 16 | Complete |
| ANLT-04 | Phase 16 | Complete |
| ANLT-05 | Phase 16 | Complete |
| ANLT-06 | Phase 16 | Complete |
| ANLT-07 | Phase 16 | Complete |
| ANLT-08 | Phase 16 | Complete |
| ANLT-09 | Phase 16 | Complete |
| ANLT-10 | Phase 16 | Complete |

**Coverage:**
- v1.0 requirements: 40 total, mapped: 40, unmapped: 0
- v1.1 requirements: 34 total, mapped: 34, unmapped: 0
- v2.0 requirements: 47 total, mapped: 47, unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-20 after v2.0 roadmap creation*
