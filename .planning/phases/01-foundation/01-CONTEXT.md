# Phase 1: Foundation - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffolding, database schema for all domain entities, master authentication, phone normalization, and Docker Compose deployment. This phase produces a running backend with health checks, auth endpoints, and a deployable Docker stack. No UI, no bots, no booking logic — just the foundation that everything else builds on.

</domain>

<decisions>
## Implementation Decisions

### Master Authentication
- Multiple auth methods: TG bot auth (primary), email+password (web panel fallback), QR code/magic link from bot for web panel quick login
- No SMS/OTP for now — too expensive for pre-revenue stage. Can be added later.
- TG auth flow: master sends /start → bot creates account → JWT token issued
- Web panel: login via email+password OR scan QR from bot OR click magic link sent by bot
- MAX and VK bot auth follows same pattern as TG bot auth

### Client Authentication
- Clients don't register — no accounts needed
- Client simply provides name + phone when making a booking
- Phone number is the identifier across messengers (E.164 normalization)

### Repository Structure
- Monorepo: backend/, frontend/, bots/ all in one repository
- Single `docker-compose.yml` at root for full stack
- Shared types/schemas between components

### Code Language
- All English: table names, API fields, variable names, comments
- Russian only in user-facing strings (UI text, bot messages, notifications)

### Development Environment
- Everything in Docker for local dev: `docker compose up` starts full stack
- Docker Compose with hot-reload for backend (uvicorn --reload with volume mount)
- PostgreSQL in Docker container, persistent volume for data

### Claude's Discretion
- FastAPI project layout (routers, services, repositories pattern)
- Alembic vs raw SQL for migrations
- JWT implementation details (secret rotation, token expiry)
- Docker Compose service naming and networking
- Caddy vs nginx for reverse proxy
- Redis inclusion (if needed for sessions/cache)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Specs
- `.planning/PROJECT.md` — Product vision, constraints, pricing, tech stack decisions
- `.planning/REQUIREMENTS.md` — Full v1 requirements with REQ-IDs (INFR-01..05, CLNT-02 for this phase)

### Research
- `.planning/research/STACK.md` — Verified stack versions (FastAPI 0.135+, SQLAlchemy 2.0, asyncpg, etc.)
- `.planning/research/ARCHITECTURE.md` — Modular monolith architecture, DB schema design, RLS patterns
- `.planning/research/PITFALLS.md` — E.164 normalization, double-booking prevention, webhook security

### External Research
- `/Users/yannovak/docs/two-products-deep-dive-march-2026.md` — Original product research with architecture diagrams

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, empty repository

### Established Patterns
- None yet — this phase establishes the foundational patterns

### Integration Points
- Phase 2 (Booking + TG) will add booking logic on top of the data model and auth created here
- Phase 3 (Payments) will extend the schema with payment/receipt tables
- Phase 5 (MAX + VK) will add bot adapters using the messenger adapter pattern established here
- Phase 6 (Web Panel) will consume the REST API built here

</code_context>

<specifics>
## Specific Ideas

- User has experience with Supabase (used in Design Finance app) but chose self-hosted PostgreSQL for full control
- Docker Compose is the deployment target — no Kubernetes, no cloud services
- VPS deployment (likely Timeweb or Hetzner)
- Robokassa is registered but store not configured yet — payment integration comes in Phase 3

</specifics>

<deferred>
## Deferred Ideas

- SMS OTP authentication — deferred due to cost, add when revenue justifies it
- MAX/VK specific auth quirks — will be addressed in Phase 5

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-17*
