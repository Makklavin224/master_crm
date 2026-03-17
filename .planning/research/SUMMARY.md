# Project Research Summary

**Project:** Master-CRM
**Domain:** Multi-messenger CRM with booking, SBP payments, and auto-tax receipts for self-employed professionals (Russia)
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

Master-CRM targets a validated and specific gap in the Russian market: no existing product combines online booking, SBP payment collection, and automatic FNS "Moy Nalog" tax receipt generation -- all accessible natively inside Telegram, MAX, and VK messengers. The 15M+ self-employed professionals in Russia currently choose between enterprise-grade salon software (YCLIENTS at 686+/mo, DIKIDI at 450+/mo) that is overpriced and bloated for solo practitioners, lightweight Telegram bots (Okoshki, ZapishiMenya) that lack payments or tax integration, or tax-only tools (samoCRM, Master CRM) with no booking capability. The killer feature -- master taps "Complete", client gets SBP payment link, tax receipt auto-generates in "Moy Nalog" via Robochecks -- reduces a 9-step manual process to 3 steps. At a planned price of 99 RUB/mo, this undercuts every competitor while offering the only complete solution.

The recommended approach is a Python FastAPI modular monolith with a single React TypeScript codebase for mini-apps deployed across three messengers. The stack is mature and well-documented: FastAPI 0.135 + SQLAlchemy 2.0 + asyncpg for the backend, aiogram 3.26 / maxapi 0.9.16 / vkbottle 4.7 for bot frameworks, and React 18 + Vite + Tailwind for the frontend. A separate Ant Design admin panel shares the same API. The architecture uses a service layer with messenger adapters (Strategy pattern) so all platform-specific logic is isolated from business rules. PostgreSQL with Row-Level Security provides multi-tenant isolation. The whole thing deploys as Docker Compose on a single VPS with Caddy for auto-HTTPS.

The primary risks are well-understood. Double-booking race conditions must be prevented with PostgreSQL exclusion constraints from day one -- not retrofitted later. Robokassa payment callback handling must be idempotent because lost or duplicate callbacks cause real financial harm (incorrect tax receipts, FNS scrutiny). Phone number normalization to E.164 is foundational for cross-messenger client identity and cannot be added after launch without painful deduplication. The MAX Mini App SDK is the largest unknown (MEDIUM confidence -- young ecosystem, sparse bridge API documentation), but the architectural adapter pattern means MAX integration is isolated and won't destabilize the rest of the system. The MAX business platform opening in spring 2026 creates a time-sensitive first-mover opportunity.

## Key Findings

### Recommended Stack

The backend is Python-native: FastAPI for async API, SQLAlchemy 2.0 + asyncpg for database access (5x faster than psycopg3), Alembic for migrations, ARQ for async task scheduling (reminders, payment checks). Three bot frameworks handle the three messengers. The frontend uses a pnpm monorepo with shared types between the mini-app and admin panel. See [STACK.md](./STACK.md) for complete version matrix.

**Core technologies:**
- **FastAPI 0.135 + Pydantic 2.12**: Async API with auto-generated OpenAPI docs, dependency injection, request validation. The standard for Python async APIs in 2026.
- **SQLAlchemy 2.0 + asyncpg + Alembic**: Async ORM with the fastest PostgreSQL driver available. Alembic handles schema migrations. RLS for tenant isolation.
- **PostgreSQL 16**: Primary database. JSONB for flexible metadata, exclusion constraints for double-booking prevention, RLS for multi-tenant isolation.
- **aiogram 3.26 / maxapi 0.9.16 / vkbottle 4.7**: One bot framework per messenger. All async, all actively maintained (Feb-Mar 2026 updates).
- **React 18 + TypeScript + Vite 6**: Single mini-app codebase for all three messengers. Vite produces small bundles critical for mini-app cold start. Platform detection at the shell level with dynamic imports.
- **Ant Design 5.x**: Admin panel UI. Table, Calendar, Form, Modal -- out of the box. Faster than building from shadcn primitives.
- **Zustand + TanStack Query 5**: Client-side state (1KB, zero boilerplate) + server-state caching with optimistic updates. Shared between mini-app and admin panel.
- **Custom Robokassa integration**: Payment link generation (HMAC-signed URL), ResultURL callback handler, Robochecks for auto-receipts. Existing Python libraries are too thin -- build a 200-line wrapper.
- **Docker Compose + Caddy**: Single VPS deployment. Caddy provides automatic Let's Encrypt SSL in 3 lines of config vs 50+ for Nginx + certbot.

### Expected Features

The critical dependency chain is: Service Catalog -> Working Hours -> Online Booking -> Client Database -> SBP Payment -> Auto Tax Receipt. This chain defines the MVP build order. See [FEATURES.md](./FEATURES.md) for detailed competitor analysis and pricing context.

**Must have (table stakes):**
- Service catalog (name, duration, price, categories)
- Calendar / schedule view with real-time updates
- Working hours, days off, break configuration
- Online self-booking via mini-app with slot calculation
- Client database auto-populated from bookings (phone as primary identifier)
- Booking confirmations and automated reminders (24h + 2h via messenger)
- Booking management (client cancel/reschedule with configurable cutoffs)
- Push notifications for master on new bookings/cancellations

**Should have (differentiators -- these are the product's moat):**
- Auto tax receipt via Robokassa Robochecks -- the KILLER FEATURE, no booking competitor does this
- SBP payment link after service completion -- master taps "Complete", client gets link in chat
- Multi-messenger presence (TG + MAX + VK) -- no competitor covers all three, MAX has 100M users and near-zero CRM competition
- Cross-messenger client identity via phone normalization -- unique to multi-messenger approach
- Zero-download client experience -- mini-app opens in messenger, no registration required
- Free reminders via messenger (YCLIENTS charges extra for SMS; messenger reminders have 80%+ open rate vs 20% for SMS)
- Web admin panel for desktop management

**Defer (v2+):**
- Revenue analytics beyond basic income per period
- Client notes, tags, photo portfolio
- Repeat visit invitations, loyalty basics
- Income/expense tracking

**Anti-features (never build):**
- Inventory management, payroll, multi-branch (salon territory, not solo-master)
- Native mobile app (mini-apps replace this)
- Marketplace / client discovery (different business entirely)
- AI chatbot for client interaction (premature sophistication)

### Architecture Approach

A modular monolith deployed via Docker Compose. Single FastAPI application with three router groups (REST API for mini-apps, webhook handlers for bots + Robokassa, admin API for the web panel), a shared service layer (BookingService, PaymentService, ScheduleService, NotificationService), and adapter layers for messengers and payments. The adapter pattern is the single most important architectural decision -- it isolates all platform-specific logic so adding MAX or VK does not touch booking or payment code. PostgreSQL RLS provides defense-in-depth for multi-tenant data isolation beyond application-level `master_id` filtering. See [ARCHITECTURE.md](./ARCHITECTURE.md) for component diagrams, data flow sequences, and database schema.

**Major components:**
1. **Messenger Adapters (TG/MAX/VK)** -- Translate between platform-specific bot APIs and internal IncomingEvent/OutgoingMessage format. Each adapter is under 100 lines. Business logic never touches platform-specific types.
2. **Service Layer** -- Core business logic: BookingService (slot calculation, conflict prevention), PaymentService (Robokassa integration, idempotent callbacks), ScheduleService (working hours, exceptions), NotificationService (platform-agnostic message routing).
3. **Platform-Aware Mini App Shell** -- Thin React context that detects TG/MAX/VK at startup, loads the correct bridge SDK via dynamic import, and exposes a unified PlatformBridge interface to all components.
4. **PostgreSQL with RLS** -- Shared database, all masters' data in the same tables, isolated by `master_id` with RLS policies. Phone-based client identity with E.164 normalization. `client_platforms` junction table for cross-messenger linking.

### Critical Pitfalls

Top 5 pitfalls from [PITFALLS.md](./PITFALLS.md) that must be addressed during implementation:

1. **Double-booking race conditions** -- Two clients book the same slot simultaneously. Prevent with PostgreSQL `SELECT FOR UPDATE` and `EXCLUDE USING gist` constraints on time ranges. Must be in the first booking implementation, not retrofitted.
2. **Robokassa callback mishandling** -- Lost or duplicate payment processing causes financial harm. Return `OK{InvId}` immediately, process asynchronously, use InvId as idempotency key with UNIQUE constraint. Validate signatures strictly (Password2, case-sensitive).
3. **Tax receipt cancellation on refund** -- Receipt auto-generates on payment, but if client cancels or no-shows, the receipt must be annulled in "Moy Nalog" or the master pays tax on un-received income. Design the refund/cancellation flow as a first-class feature, not an afterthought.
4. **Phone number normalization chaos** -- Same client appears as three different people across messengers because of format differences (+7, 8, no prefix). Normalize ALL phones to E.164 at entry point. Must be in the data model from Phase 1.
5. **Mini-app SDK abstraction bloat** -- Three platform SDKs with different APIs for auth, haptics, and UI. Use a thin adapter interface (under 100 lines per platform), dynamic imports per entry point, and keep business logic 100% platform-agnostic.

## Implications for Roadmap

Based on combined research findings, the following phase structure aligns with the feature dependency chain, architecture component boundaries, and pitfall prevention requirements.

### Phase 1: Foundation and Data Model
**Rationale:** Every component depends on the data layer. Getting the schema right prevents painful migrations later. Phone normalization, master_id scoping, and TIMESTAMPTZ must be foundational -- not bolted on.
**Delivers:** Project scaffolding (FastAPI + Alembic + Docker Compose + PostgreSQL), core SQLAlchemy models (masters, services, clients, client_platforms, master_schedules, schedule_exceptions, bookings, payments, reminders), auth system (master registration/login), E.164 phone normalization utility, RLS policies, Caddy reverse proxy.
**Addresses features:** Service catalog data model, client database structure, working hours model
**Avoids pitfalls:** Phone normalization chaos (4), multi-tenant data isolation gaps (12), timezone mishandling (7)

### Phase 2: Booking Engine and Telegram Bot
**Rationale:** The booking flow is the core product interaction. Building it with Telegram first validates the full flow with the largest Russian messenger audience before adding multi-messenger complexity. The adapter pattern is established here with TelegramAdapter as the first concrete implementation.
**Delivers:** BookingService with slot calculation and double-booking prevention (exclusion constraints), ScheduleService (working hours, breaks, exceptions), TG bot via aiogram (webhook mode), TelegramAdapter, TG mini-app with service catalog view + calendar/slot picker + booking flow, booking confirmations and new-booking alerts to master.
**Addresses features:** Online self-booking, calendar/schedule view, booking confirmations, booking management (cancel/reschedule), client visit history, basic mobile access
**Avoids pitfalls:** Double-booking race conditions (1), bot instance conflicts (8 -- webhooks from day one), schedule edge cases (15)

### Phase 3: Payments and Auto-Receipts
**Rationale:** This is the killer differentiator that no competitor offers. It must work flawlessly before public launch. Building it after the booking engine means there is a complete booking flow to test end-to-end.
**Delivers:** Robokassa payment adapter (SBP link generation, HMAC signature, ResultURL callback), idempotent payment processing, Robochecks auto-receipt integration, payment status tracking, receipt status tracking (pending/issued/cancelled), refund data model and cancellation flow design.
**Addresses features:** SBP payment link, auto tax receipt via Robochecks
**Avoids pitfalls:** Robokassa callback mishandling (2), InvId collision (14), tax receipt cancellation gaps (3), SBP refund complexity (9)

### Phase 4: Reminders and Background Tasks
**Rationale:** Automated reminders reduce no-shows by 30-50% and are table stakes for any booking system. This phase introduces the ARQ task queue which also serves payment expiry checks and future scheduled tasks.
**Delivers:** ARQ worker connected to Redis, 24h and 2h reminder scheduling with timezone-aware delivery, per-platform rate limiting, delivery tracking (can_receive_messages boolean per client per platform), idempotent reminder processing.
**Addresses features:** Automated reminders (24h + 2h), push notifications for master
**Avoids pitfalls:** Reminder delivery failures (11), timezone mishandling (7), API rate limits (16)

### Phase 5: MAX and VK Messenger Expansion
**Rationale:** The adapter pattern from Phase 2 makes adding messengers mechanical. MAX has a time-sensitive business platform window (spring 2026) and 100M users with near-zero CRM competition. VK completes the multi-messenger story. Both messengers reuse the existing mini-app codebase with platform detection.
**Delivers:** MaxAdapter + VKAdapter, MAX bot (maxapi) + VK bot (vkbottle) in webhook mode, mini-app platform detection shell with dynamic imports, three entry points (tg.html, vk.html, max.html), cross-messenger client identity merging via phone, platform-specific moderation compliance.
**Addresses features:** Multi-messenger presence (TG + MAX + VK), cross-messenger client identity, zero-download client experience on all platforms
**Avoids pitfalls:** SDK abstraction bloat (5), bundle size from three SDKs (13), platform moderation rejection (10)

### Phase 6: Web Admin Panel
**Rationale:** APIs are stable from phases 1-4. The admin panel is a separate React app consuming the same API -- it does not block mini-app development and is best built after the API surface is finalized.
**Delivers:** React admin panel with Ant Design, schedule grid view (day/week), client search and management, service catalog CRUD, booking management, payment history, basic revenue reporting (income per period, booking count, repeat rate).
**Addresses features:** Web admin panel for master, desktop schedule management
**Avoids pitfalls:** Building admin before APIs stabilize (wasted rework)

### Phase 7: Polish, Monitoring, and Launch
**Rationale:** Production readiness before real money flows through the system. Sentry, structured logging, and onboarding flows are critical for a product handling payments and tax receipts.
**Delivers:** Sentry integration (Python + JS), structlog for JSON-formatted server logs, master onboarding flow, error handling hardening, edge case coverage, beta testing program.
**Addresses features:** Final UX polish, error states, production monitoring
**Avoids pitfalls:** Launching without observability, "Moy Nalog" integration downtime handling (17)

### Phase Ordering Rationale

- **Data model first** because every feature depends on it, and foundational decisions (E.164 phones, TIMESTAMPTZ, master_id on all tables, RLS) cannot be retrofitted without painful migration and deduplication
- **TG-first** validates the complete booking-to-payment-to-receipt flow with one messenger before multi-messenger complexity; TG has the largest Russian audience and the most mature mini-app SDK
- **Payments before reminders** because payments are the revenue-generating killer differentiator; reminders are important but standard
- **MAX/VK after core flow** because the adapter pattern is proven with TG first, reducing integration risk; MAX's spring 2026 window is well-served by a Phase 5 timeline
- **Admin panel after API stabilization** because it is a separate frontend consuming existing endpoints -- no backend changes needed
- **Phase 6 (admin panel) can run in parallel** with Phase 5 (MAX/VK expansion) since they share the same backend APIs but have no frontend dependencies on each other

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3 (Payments):** Robochecks receipt cancellation/annulment API is poorly documented publicly. Needs testing with a live Robokassa test store and possibly contacting Robokassa technical support. The receipt cancellation reason codes ("return of funds" vs "receipt formed in error") have legal implications.
- **Phase 5 (MAX):** MAX Mini App bridge API documentation is sparse. The @maxhub/max-ui package has a Storybook but lacks documentation on bridge methods (getUserData, phone access, theme params). Needs investigation closer to implementation -- possibly contacting MAX developer support or reverse-engineering the SDK. The platform is evolving quickly and docs may improve by the time Phase 5 starts.
- **Phase 5 (VK moderation):** VK Mini Apps require specific UI patterns (VKUI compliance) and privacy disclosures. Submit a minimal version for moderation early to learn requirements.

**Phases with standard patterns (skip phase research):**
- **Phase 1 (Foundation):** FastAPI + SQLAlchemy + Alembic + Docker Compose -- extremely well-documented, established patterns, no surprises expected.
- **Phase 2 (Booking + TG):** aiogram 3.x webhooks, PostgreSQL exclusion constraints, React mini-app with @telegram-apps/sdk-react -- all thoroughly documented with high-quality official docs.
- **Phase 4 (Reminders):** ARQ + Redis for scheduled tasks -- straightforward, well-documented.
- **Phase 6 (Admin Panel):** Ant Design + React + TanStack Router -- standard admin panel patterns, nothing domain-specific.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack - Backend | HIGH | All packages verified on PyPI with Feb-Mar 2026 release dates. FastAPI + SQLAlchemy + aiogram is the dominant Python async stack. |
| Stack - Frontend | HIGH | React + Vite + TypeScript + Tailwind is industry standard. TG and VK SDKs are official and actively maintained. |
| Stack - MAX SDK | MEDIUM | @maxhub/max-ui exists (GitHub: 42 stars) but bridge API docs are thin. Platform is young and evolving. |
| Stack - Robokassa | HIGH for payments, MEDIUM for Robochecks | Payment API is simple and well-documented. Robochecks auto-receipt is documented, but annulment/cancellation flow is not. |
| Features | HIGH | Based on analysis of 10+ competitors (YCLIENTS, DIKIDI, EasyWeek, Okoshki, Beauty-Bot, samoCRM, and more). Gap validation is strong -- no product fills the booking+payment+receipt+multi-messenger niche. |
| Architecture | HIGH | Modular monolith with service layer and adapter pattern is textbook for this domain. PostgreSQL RLS for multi-tenant SaaS is recommended by AWS, Supabase, and CrunchyData. |
| Pitfalls | HIGH | Double-booking, payment callback idempotency, and phone normalization are widely documented industry pitfalls with established solutions. |

**Overall confidence:** HIGH

### Gaps to Address

- **MAX Mini App bridge API:** No public documentation for bridge methods (user data, phone, theme). Must investigate when Phase 5 planning begins. Worst case: reverse-engineer the SDK or contact MAX developer support.
- **Robochecks receipt annulment:** Auto-generation is documented, but the cancellation flow for refunds/no-shows needs testing with a live Robokassa test store. This is a legal requirement -- masters must not pay tax on un-received income.
- **Telegram accessibility in Russia:** As of March 2026, TG is experiencing significant blocking (8000+ complaints/hour). The multi-messenger strategy mitigates this, but the TG-first build order assumes 60-70M Russians continue using TG via VPN. If blocking escalates dramatically, consider reordering to MAX-first.
- **MAX business platform timeline:** "Spring 2026" opening is mentioned in Kommersant reporting but no official date is confirmed. Phase 5 timing should watch for official announcements from MAX.
- **ARQ vs Taskiq:** ARQ was chosen for simplicity. If task requirements grow beyond simple scheduling (complex workflows, task chaining, result inspection), revisit this choice at Phase 4 planning.
- **Robokassa merchant model:** Whether each master gets their own Robokassa merchant account or payments flow through a single platform account affects InvId strategy, commission handling, and onboarding complexity. This needs a business decision before Phase 3.

## Sources

### Primary (HIGH confidence)
- [FastAPI 0.135.1 (PyPI)](https://pypi.org/project/fastapi/) -- framework version, features
- [aiogram 3.26.0 (PyPI)](https://pypi.org/project/aiogram/) -- TG bot framework
- [SQLAlchemy 2.0 async docs](https://docs.sqlalchemy.org/en/20/) -- ORM patterns
- [Robokassa API docs](https://docs.robokassa.ru/) -- payment integration
- [Robokassa Robochecks for self-employed](https://robokassa.com/online-check/robocheck-smz/) -- auto-receipt
- [Telegram Mini Apps docs](https://docs.telegram-mini-apps.com/) -- TG SDK, initData validation
- [VK Bridge SDK](https://github.com/VKCOM/vk-bridge) -- VK mini-app bridge
- [PostgreSQL RLS (CrunchyData)](https://www.crunchydata.com/blog/row-level-security-for-tenants-in-postgres) -- multi-tenant pattern
- [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) -- FOR UPDATE, advisory locks

### Secondary (MEDIUM confidence)
- [maxapi 0.9.16 (PyPI)](https://pypi.org/project/maxapi/) -- MAX bot library
- [MAX UI GitHub](https://github.com/max-messenger/max-ui) -- MAX mini-app components
- [DIKIDI reviews (77 reviews, CRMIndex)](https://crmindex.ru/products/dikidi/reviews) -- competitor analysis
- [YCLIENTS reviews (118 reviews, CRMIndex)](https://crmindex.ru/products/yclients/reviews) -- competitor analysis
- [MAX business platform (Kommersant)](https://www.kommersant.ru/doc/8401240) -- spring 2026 timeline
- [Multi-channel bot abstraction pattern](https://dev.to/quintana/i-built-a-multi-channel-conversation-framework-in-python-heres-why-5fi9) -- adapter pattern

### Tertiary (LOW confidence)
- MAX Mini App bridge API specifics -- inferred from SDK code, not documented
- Receipt cancellation reason codes for "Moy Nalog" -- based on self-employed accounting guides, not Robochecks API docs

---
*Research completed: 2026-03-17*
*Ready for roadmap: yes*
