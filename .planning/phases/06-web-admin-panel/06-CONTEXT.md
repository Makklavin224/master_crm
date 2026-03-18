# Phase 6: Web Admin Panel - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a desktop web panel for masters to manage their entire business — schedule, clients, services, payments, and settings. Consumes the same REST API that the mini-app uses. Separate React app (not the mini-app) with Ant Design, sidebar navigation, light/dark theme toggle.

</domain>

<decisions>
## Implementation Decisions

### Layout
- Sidebar + content layout (Ant Design ProLayout or Layout.Sider)
- Left sidebar with menu: Календарь, Клиенты, Услуги, Платежи, Настройки
- Main content area on the right
- Collapsible sidebar for smaller screens

### Theme
- Light theme by default + dark theme toggle
- Uses Ant Design theme system (ConfigProvider)
- Accent color: #6C5CE7 (same as mini-app for brand consistency)

### Authentication
- All three methods from Phase 1 decision:
  - Email + password login form
  - QR code scan (bot generates QR → scan → auto-login in web panel)
  - Magic link (bot sends link → click → auto-login)
- JWT token stored in localStorage, same API endpoints as mini-app

### Pages (mirror mini-app master panel)
- **Dashboard/Calendar:** Day/week schedule view with bookings
- **Clients:** Table with search, client detail with visit history
- **Services:** CRUD table with categories
- **Payments:** History table with filters, receipt statuses
- **Settings:** Schedule, notifications, payment config, Robokassa, profile

### Separate App
- web/ directory in monorepo (alongside backend/ and frontend/)
- Own package.json, Vite config, Docker service
- Shares nothing with frontend/ mini-app (different UI framework: Ant Design vs custom Tailwind)
- Served by Caddy at /admin/ path

### Claude's Discretion
- Ant Design version and specific components
- Table column configurations
- Calendar component choice (FullCalendar, Ant Calendar, or custom)
- QR code generation for login (frontend or backend)
- Magic link token generation and validation
- Responsive breakpoints
- Data fetching patterns (TanStack Query same as mini-app, or SWR)

</decisions>

<canonical_refs>
## Canonical References

### Project Specs
- `.planning/REQUIREMENTS.md` — WEB-01..05

### Existing Code (API to consume)
- `backend/app/api/v1/` — All endpoints: auth, services, schedule, bookings, clients, payments, settings
- `backend/app/schemas/` — All request/response schemas
- `backend/app/core/security.py` — JWT auth (same tokens work for web panel)

### Prior Phase Context
- `.planning/phases/02-booking-engine-telegram/02-UI-SPEC.md` — Brand colors (#6C5CE7 accent), Inter font
- `frontend/src/pages/master/` — Mini-app master panel (reference for feature parity)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Backend API is 100% ready — web panel is a pure frontend project
- JWT auth endpoints (register, login, auth/tg, auth/max, auth/vk) all return same token format
- All schemas in backend/app/schemas/ define the API contract

### Established Patterns
- TanStack Query + Zustand (from mini-app) — reuse in web panel
- API client with Bearer token auth

### Integration Points
- New Docker service in docker-compose.yml (web/)
- New Caddy route: /admin/* → web panel
- Same backend API, no new endpoints needed

</code_context>

<specifics>
## Specific Ideas

- Desktop-optimized: tables, full calendar view, multi-column layouts — things mini-app can't do well
- Ant Design gives professional look out of the box with less custom CSS
- Calendar should show bookings visually (time blocks, not just list)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-web-admin-panel*
*Context gathered: 2026-03-18*
