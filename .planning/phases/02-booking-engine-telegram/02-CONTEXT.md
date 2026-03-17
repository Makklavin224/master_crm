# Phase 2: Booking Engine + Telegram - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the core booking engine (service catalog, schedule management, slot calculation, booking CRUD) and the Telegram integration (bot via aiogram + React mini-app). Clients can discover services, view available slots, and book appointments through the TG mini-app. Masters receive notifications and manage bookings through the bot and mini-app. This is the first user-facing product — the foundation becomes real.

</domain>

<decisions>
## Implementation Decisions

### Mini-App Booking Flow
- Entry points: direct link from master (t.me/bot?start=master_id) + search by name/category inside mini-app
- Booking steps: Услуга → Дата → Время → Имя+Телефон → Подтверждение
- Client provides name + phone as the last step before confirming (form before "Записаться")
- One mini-app, two roles: client sees booking interface, master sees management panel. Role determined automatically by auth status.
- Platform detection shell for TG/MAX/VK bridge adapters (Phase 2 implements TG only, adapter pattern for future phases)

### Mini-App Visual Style
- Modern branded design — not Telegram-native theme colors. Own visual identity, clean, contemporary.
- Claude has discretion on color palette and typography (product name TBD — use working name "Мастер-CRM")
- Must look good and be convenient — user explicitly asked for красивый современный стиль

### TG Bot
- Single bot for masters AND clients (@MasterCRMBot or similar)
- Master: /start → registration/login, /today → today's bookings, /link → shareable booking link, /settings → schedule/services/profile
- Client: /start?master_id → opens mini-app for that master
- Bot commands (BotFather menu): start, today, link, settings

### Master Notifications (via bot)
- New booking: "Новая запись: Имя, Услуга, 14:00 25 марта"
- Client cancelled: "Клиент отменил запись на 14:00 25 марта"
- Client rescheduled: "Клиент перенёс запись с 14:00 на 16:00"
- All notifications include inline buttons for quick actions

### TG Auth for Masters
- /start creates new account (linked to TG user_id)
- Separate from email+password account (Phase 1)
- Link TG to existing email account later via settings (not auto-merge)
- TG initData validation for mini-app auth

### Schedule & Slots
- Weekly template: per-day working hours (Пн 10:00-20:00, Вт 10:00-18:00...) + exceptions for specific dates
- Configurable buffer between appointments: 0, 10, 15, 30 minutes
- Configurable cancellation deadline: 2h, 6h, 12h, 24h before appointment
- Slot calculation: working hours - existing bookings - buffer time = free slots
- Double-booking prevention via PostgreSQL exclusion constraints (from Phase 1 research)

### Booking Management
- Client: cancel or reschedule (subject to deadline)
- Master: cancel, reschedule, manually add booking (no deadline restriction)
- Master override always available regardless of client-facing rules

### Claude's Discretion
- React project setup (Vite + TanStack Query + Zustand — per research)
- Mini-app component library choice
- Slot grid layout (time picker design)
- Bot message formatting (markdown vs HTML)
- Webhook setup and security (HMAC validation)
- API endpoint design for booking CRUD
- Frontend build/deploy pipeline
- Platform bridge adapter pattern implementation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/PROJECT.md` — Product vision, multi-messenger architecture, pricing
- `.planning/REQUIREMENTS.md` — BOOK-01..06, CLNT-01, CLNT-03, MSG-01, MSG-02, MSG-07, MSG-08, INFR-03

### Research
- `.planning/research/STACK.md` — aiogram 3.26, @telegram-apps/sdk-react, React+Vite, TanStack Query, Zustand
- `.planning/research/ARCHITECTURE.md` — Messenger Adapter pattern, booking slot locking, platform detection shell
- `.planning/research/PITFALLS.md` — Double-booking (exclusion constraints), phone normalization, TG initData validation

### Phase 1 Foundation
- `.planning/phases/01-foundation/01-CONTEXT.md` — Monorepo structure, English code, Docker Compose, auth decisions
- `backend/app/models/` — Existing domain models (booking.py, service.py, schedule.py, client.py)
- `backend/app/services/phone_service.py` — Phone normalization (E.164)
- `backend/app/core/database.py` — Async SQLAlchemy engine
- `backend/app/core/security.py` — JWT + password hashing (PyJWT + pwdlib)
- `backend/app/api/v1/auth.py` — Existing auth endpoints (register/login/me)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/booking.py` — BookingModel with status enum, tstzrange for exclusion constraints
- `backend/app/models/service.py` — ServiceModel with name, duration, price
- `backend/app/models/schedule.py` — MasterSchedule + ScheduleException models
- `backend/app/models/client.py` — ClientModel + ClientPlatform for cross-messenger identity
- `backend/app/services/phone_service.py` — normalize_phone() for E.164
- `backend/app/core/security.py` — JWT encode/decode, password hashing
- `backend/app/core/dependencies.py` — get_db_with_rls(), get_current_master()

### Established Patterns
- Routers → Services → Models (FastAPI project pattern from Phase 1)
- RLS via SET LOCAL in dependency injection
- Alembic for schema migrations
- Docker Compose with hot-reload

### Integration Points
- New API routers: services, schedule, bookings (added to api/v1/router.py)
- New services: booking_service.py, schedule_service.py
- New directory: frontend/ (React mini-app, added to Docker Compose)
- Bot webhook handler: integrated into FastAPI app or separate service
- TG auth: new auth strategy alongside existing email+password

</code_context>

<specifics>
## Specific Ideas

- Single bot serving both masters and clients — differentiated by start parameter
- Booking link format: t.me/BotName?start=master_id (deep link into mini-app)
- Master gets instant bot notifications with inline action buttons
- Modern branded UI, not Telegram-native — should stand out and feel professional

</specifics>

<deferred>
## Deferred Ideas

- MAX + VK messenger integration — Phase 5
- Client reminders (24h/2h) — Phase 4
- Payment after booking — Phase 3
- Web admin panel — Phase 6
- Master search/discovery marketplace — out of scope

</deferred>

---

*Phase: 02-booking-engine-telegram*
*Context gathered: 2026-03-17*
