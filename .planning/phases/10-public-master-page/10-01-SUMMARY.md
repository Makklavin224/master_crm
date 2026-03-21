---
phase: 10-public-master-page
plan: 01
subsystem: infra
tags: [vite, react, tailwind, docker, caddy, nginx, typescript]

# Dependency graph
requires:
  - phase: 09-backend-foundation
    provides: Public API endpoints (masters, services, slots, reviews, bookings)
provides:
  - Standalone Vite+React+TS+Tailwind SPA in public/ directory
  - API client and TypeScript types matching backend schemas
  - Docker multi-stage build (node:20-alpine + nginx:alpine) on port 3002
  - Caddy /m/* routing to public SPA
  - React Router placeholder routes for master page and booking flow
affects: [10-02, 10-03, 10-04, public-master-page]

# Tech tracking
tech-stack:
  added: [react 19, react-router-dom 7, @tanstack/react-query 5, tailwindcss 4, dayjs, lucide-react, vite 8]
  patterns: [standalone SPA per concern, shared design tokens across SPAs, public API client without auth headers]

key-files:
  created:
    - public/package.json
    - public/vite.config.ts
    - public/src/App.tsx
    - public/src/api/client.ts
    - public/src/api/types.ts
    - public/src/index.css
    - public/Dockerfile
    - public/.dockerignore
  modified:
    - docker-compose.yml
    - Caddyfile

key-decisions:
  - "Public SPA uses same dependency versions as frontend/ mini-app for consistency"
  - "No auth headers in API client (public endpoints only)"
  - "Tailwind theme tokens copied from frontend/ without Telegram theme variables"

patterns-established:
  - "public/ is third standalone SPA (alongside frontend/ and web/), each with own Vite config, Dockerfile, and Caddy route"
  - "Base path convention: /app/ for mini-app, /admin/ for web admin, /m/ for public master pages"

requirements-completed: [PBUK-01]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 10 Plan 01: Public SPA Scaffold Summary

**Standalone Vite+React+TS+Tailwind SPA in public/ with API client, Docker build, and Caddy /m/* routing**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T04:30:46Z
- **Completed:** 2026-03-21T04:33:55Z
- **Tasks:** 2
- **Files modified:** 17

## Accomplishments
- Scaffolded complete public/ project with React 19, React Router 7, TanStack Query 5, Tailwind v4
- Created API client and TypeScript interfaces matching all backend public schemas (MasterProfile, ServiceRead, AvailableSlot, ReviewRead, BookingCreate, BookingRead)
- Configured Docker multi-stage build (node:20-alpine + nginx:alpine) serving on port 3002
- Integrated with Docker Compose and Caddy reverse proxy at /m/* path

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold public/ Vite+React+TS+Tailwind project with API client and types** - `87f1c69` (feat)
2. **Task 2: Dockerfile + Docker Compose + Caddyfile integration** - `9f279f1` (feat)

## Files Created/Modified
- `public/package.json` - Project manifest with react, react-router-dom, @tanstack/react-query, tailwindcss, dayjs, lucide-react
- `public/vite.config.ts` - Vite config with base: "/m/", port 3002
- `public/tsconfig.json` - TypeScript project references
- `public/tsconfig.app.json` - App TypeScript config (ES2023, strict, react-jsx)
- `public/tsconfig.node.json` - Node TypeScript config for vite.config.ts
- `public/eslint.config.js` - ESLint config matching frontend/
- `public/index.html` - HTML entry point with Russian title
- `public/src/main.tsx` - React 19 createRoot entry
- `public/src/App.tsx` - BrowserRouter with basename="/m", routes for /:username and /:username/book/*
- `public/src/index.css` - Tailwind v4 @theme tokens (colors, fonts, shadows) without Telegram integration
- `public/src/api/client.ts` - API client (fetch wrapper) without auth headers
- `public/src/api/types.ts` - TypeScript interfaces matching backend schemas
- `public/Dockerfile` - Multi-stage build (node:20-alpine + nginx:alpine) on port 3002
- `public/.dockerignore` - Excludes node_modules, dist, .git
- `docker-compose.yml` - Added public service on port 3002 with healthcheck, added to caddy depends_on
- `Caddyfile` - Added /m redirect and /m/* handle block with strip_prefix and reverse_proxy

## Decisions Made
- Used same dependency versions as frontend/ for consistency across SPAs
- Omitted Telegram-specific packages (@telegram-apps/sdk-react, @vkontakte/vk-bridge, zustand) since public pages don't need them
- Kept Tailwind theme tokens but removed Telegram theme CSS variable mapping (--tg-theme-* not relevant for public pages)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added missing @types/node dependency**
- **Found during:** Task 1 (pnpm build)
- **Issue:** tsconfig.node.json references "types": ["node"] but @types/node was not in devDependencies
- **Fix:** Added "@types/node": "^24.12.0" to devDependencies (matching frontend/)
- **Files modified:** public/package.json
- **Verification:** pnpm build succeeds
- **Committed in:** 87f1c69 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed index.html script src path**
- **Found during:** Task 1 (pnpm build)
- **Issue:** Script src was "/m/src/main.tsx" but Vite expects "/src/main.tsx" (base path is applied during build)
- **Fix:** Changed src from "/m/src/main.tsx" to "/src/main.tsx"
- **Files modified:** public/index.html
- **Verification:** pnpm build succeeds, produces dist/index.html
- **Committed in:** 87f1c69 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for successful build. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- public/ SPA builds successfully and is ready for component development
- API client and types are ready for master profile page implementation (10-02)
- Docker and Caddy infrastructure is configured for deployment
- Placeholder routes exist for all booking flow pages (10-03, 10-04)

## Self-Check: PASSED

All 8 created files verified on disk. Both task commits (87f1c69, 9f279f1) verified in git log. Build output (public/dist/index.html) confirmed.

---
*Phase: 10-public-master-page*
*Completed: 2026-03-21*
