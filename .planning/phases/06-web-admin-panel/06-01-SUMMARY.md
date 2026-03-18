---
phase: 06-web-admin-panel
plan: 01
subsystem: ui, auth, infra
tags: [react, antd, vite, vitest, zustand, tanstack-query, qr-login, magic-link, jwt, docker, caddy]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: FastAPI backend with JWT auth endpoints (login, register, /auth/me)
  - phase: 05-multi-messenger
    provides: Multi-messenger bot framework (TG/MAX/VK handlers, adapters)
provides:
  - web/ React SPA scaffolding with Ant Design 5.29, Vite 8, TypeScript 5.9
  - Zustand auth store with JWT localStorage persistence and email login
  - API client with Bearer token and 401 auto-logout
  - AdminLayout with collapsible sidebar (5 Russian menu items), theme toggle
  - Three-method LoginPage (email form, QR code poll, magic link redirect)
  - QrSession model and 4 backend auth endpoints (qr/init, qr/status, qr/confirm, magic/verify)
  - Bot handlers for QR deep link confirmation and /login magic link generation
  - Vitest configured with jsdom, 5 test files (11 tests)
  - Docker web service (port 3001) and Caddy /admin/* route
affects: [06-web-admin-panel]

# Tech tracking
tech-stack:
  added: [antd 5.29.3, @ant-design/icons 5.6.1, @fullcalendar/react 6.1.20, qrcode.react 4.2.0, vitest 4.1.0, @testing-library/react 16.3.2, jsdom 29.0.0]
  patterns: [Zustand auth store with localStorage hydrate, apiRequest with Bearer from store, ConfigProvider theme toggle, Layout.Sider sidebar navigation, QR poll-based login flow, magic link redirect flow]

key-files:
  created:
    - web/package.json
    - web/vite.config.ts
    - web/vitest.config.ts
    - web/Dockerfile
    - web/src/App.tsx
    - web/src/stores/auth.ts
    - web/src/stores/theme.ts
    - web/src/api/client.ts
    - web/src/layouts/AdminLayout.tsx
    - web/src/pages/LoginPage.tsx
    - web/src/components/StatusTag.tsx
    - web/src/theme.ts
    - backend/app/models/qr_session.py
    - backend/alembic/versions/007_add_qr_sessions_table.py
    - backend/app/bots/telegram/handlers/login.py
  modified:
    - docker-compose.yml
    - Caddyfile
    - backend/app/api/v1/auth.py
    - backend/app/schemas/auth.py
    - backend/app/models/__init__.py
    - backend/app/bots/telegram/bot.py
    - backend/app/bots/telegram/handlers/start.py
    - backend/app/core/config.py

key-decisions:
  - "antd 5.29.3 (not v6) for ecosystem stability with ProComponents compatibility"
  - "Layout.Sider + Menu instead of ProLayout (avoids umi dependency)"
  - "QR login via deep link to TG bot (/start qr_{session_id}) with 3s polling"
  - "Magic link via /login bot command, 10min expiry, inline keyboard button"
  - "web_admin_url config setting for magic link URL generation"
  - "Bot handlers: QR confirmation via direct DB call (not HTTP), same as existing patterns"
  - "SafeGetItem/SafeSetItem/SafeRemoveItem wrappers for localStorage (test environment compatibility)"

patterns-established:
  - "Auth store pattern: Zustand + localStorage hydrate on mount + 401 auto-logout"
  - "API client: apiRequest<T> with Bearer token from useAuth.getState()"
  - "Theme: ConfigProvider wrapping with algorithm toggle (light/dark)"
  - "QR auth flow: init -> QR render -> 3s poll -> confirmed -> JWT -> navigate"
  - "Protected routes: ProtectedRoute component checking useAuth.isAuthenticated"

requirements-completed: [WEB-01, WEB-02, WEB-03, WEB-04, WEB-05]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 6 Plan 1: Web Admin Panel Foundation Summary

**React SPA with Ant Design sidebar layout, three-method auth (email/QR/magic link), Zustand+TanStack Query data layer, vitest test infrastructure, and Docker/Caddy integration**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T16:11:44Z
- **Completed:** 2026-03-18T16:17:00Z
- **Tasks:** 2
- **Files modified:** 37

## Accomplishments
- Complete web/ React SPA with Ant Design 5.29, Vite 8, TypeScript 5.9, all dependencies installed
- Three-method login page: email form, QR code with 3s polling, magic link with bot /login command
- AdminLayout with collapsible sidebar (5 Russian menu items), light/dark theme toggle, logout
- Backend: QrSession model, 4 new auth endpoints, Alembic migration, bot handlers for QR confirm + /login
- Vitest configured with jsdom, 5 test files (11 tests) all passing
- Docker web service (port 3001) and Caddy reverse proxy at /admin/*

## Task Commits

Each task was committed atomically:

1. **Task 1: Web project scaffolding, auth store, API client, theme, AdminLayout, and test infrastructure** - `ff3bf2f` (feat)
2. **Task 2: Login page with three auth methods + backend QR/magic link endpoints** - `0025c39` (feat)

## Files Created/Modified
- `web/package.json` - Project config with all dependencies (antd, react, zustand, tanstack-query, fullcalendar, qrcode.react, vitest)
- `web/vite.config.ts` - Vite config with base: '/admin/', port 3001
- `web/vitest.config.ts` - Vitest with jsdom environment and setup file
- `web/Dockerfile` - Node 20 Alpine with corepack, port 3001
- `web/index.html` - Entry HTML with Inter font preconnect
- `web/src/main.tsx` - React entry point rendering App
- `web/src/App.tsx` - Router + ConfigProvider + QueryClient + ProtectedRoute + MagicLinkCallback
- `web/src/stores/auth.ts` - Zustand auth store: loginEmail, setToken, logout, hydrate with localStorage
- `web/src/stores/theme.ts` - Zustand theme store: isDark toggle with localStorage persistence
- `web/src/api/client.ts` - apiRequest with Bearer token from auth store, 401 auto-logout, ApiError
- `web/src/theme.ts` - Ant Design light/dark ThemeConfig (#6C5CE7 primary, Inter font)
- `web/src/layouts/AdminLayout.tsx` - Layout.Sider with 5 Russian menu items, theme switch, logout button
- `web/src/pages/LoginPage.tsx` - Three-tab login: email form, QR code + poll, magic link instructions
- `web/src/components/StatusTag.tsx` - BookingStatusTag and PaymentStatusTag with Russian labels
- `web/src/test/setup.ts` - @testing-library/jest-dom import + localStorage polyfill
- `web/src/__tests__/stores/auth.test.ts` - Auth store: initial state, loginEmail fetch, logout
- `web/src/__tests__/stores/theme.test.ts` - Theme store: initial state, toggle
- `web/src/__tests__/api/client.test.ts` - API client: Bearer header, ApiError on non-ok
- `web/src/__tests__/components/StatusTag.test.tsx` - StatusTag render tests
- `web/src/__tests__/layouts/AdminLayout.test.tsx` - AdminLayout: 5 menu items, theme toggle
- `backend/app/models/qr_session.py` - QrSession model (id, session_type, master_id, token, status, access_token, expires_at)
- `backend/alembic/versions/007_add_qr_sessions_table.py` - Migration creating qr_sessions table
- `backend/app/api/v1/auth.py` - Added 4 endpoints: qr/init, qr/status, qr/confirm, magic/verify
- `backend/app/schemas/auth.py` - Added QrInitResponse, QrStatusResponse, QrConfirmRequest, MagicLinkVerifyRequest
- `backend/app/models/__init__.py` - Added QrSession import
- `backend/app/bots/telegram/handlers/start.py` - Added QR deep link handling (/start qr_{session_id})
- `backend/app/bots/telegram/handlers/login.py` - New /login command handler for magic link generation
- `backend/app/bots/telegram/bot.py` - Registered login_router
- `backend/app/core/config.py` - Added web_admin_url setting
- `docker-compose.yml` - Added web service (port 3001)
- `Caddyfile` - Added /admin/* route to web:3001

## Decisions Made
- Used antd 5.29.3 (not v6) for ecosystem stability -- ProComponents beta-only for v6
- Layout.Sider + Menu instead of ProLayout to avoid umi dependency
- QR login via Telegram bot deep link with 3-second polling interval and 5-minute expiry
- Magic link via /login bot command with 10-minute expiry and inline keyboard button
- Added web_admin_url config setting (default: http://localhost:3001/admin) for magic link URL
- Bot QR confirmation uses direct DB call (not HTTP to self), consistent with existing bot handler patterns
- SafeStorage wrappers for localStorage to handle test environments gracefully

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bot handler path correction**
- **Found during:** Task 2 (bot handlers)
- **Issue:** Plan referenced `backend/app/bot/handlers.py` (singular) but actual structure is `backend/app/bots/telegram/handlers/` (plural, multi-messenger)
- **Fix:** Created handlers in the correct location: `start.py` updated for QR, new `login.py` for magic link, `bot.py` updated to register login_router
- **Files modified:** backend/app/bots/telegram/handlers/start.py, backend/app/bots/telegram/handlers/login.py, backend/app/bots/telegram/bot.py
- **Verification:** `uv run python -c "from app.bots.telegram.handlers.login import router"` succeeds
- **Committed in:** 0025c39

**2. [Rule 2 - Missing Critical] Added web_admin_url config setting**
- **Found during:** Task 2 (magic link generation)
- **Issue:** Plan referenced `{FRONTEND_URL}/admin/auth/magic?token={token}` but no such config existed
- **Fix:** Added `web_admin_url` setting to config.py with sensible default
- **Files modified:** backend/app/core/config.py
- **Verification:** Config loads correctly, login handler uses it
- **Committed in:** 0025c39

---

**Total deviations:** 2 auto-fixed (1 blocking path correction, 1 missing config)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None - Task 1 was already committed from a prior session, Task 2 backend changes (endpoints, model, migration, schemas) were partially staged.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Web SPA foundation complete with auth, layout, theme, test infrastructure
- All 5 placeholder pages (calendar, clients, services, payments, settings) ready for feature implementation
- API client and auth store ready for authenticated data fetching
- Ready for Plan 02 (feature pages: calendar, clients, services) and Plan 03 (payments, settings)

## Self-Check: PASSED

- All 15 key files verified as existing on disk
- Both commits (ff3bf2f, 0025c39) verified in git log
- pnpm build exits 0, pnpm test --run passes 11/11 tests
- QrSession model imports successfully
- Login handler router imports successfully

---
*Phase: 06-web-admin-panel*
*Completed: 2026-03-18*
