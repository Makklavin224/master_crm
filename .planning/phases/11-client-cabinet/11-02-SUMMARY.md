---
phase: 11-client-cabinet
plan: 02
subsystem: infra
tags: [caddy, vite, nginx, spa-routing, react-router, docker]

# Dependency graph
requires:
  - phase: 10-public-master-page
    provides: "Public SPA with /m/ route pattern, Caddy reverse proxy config"
provides:
  - "Dual-path SPA routing: /m/* (master pages) and /my/* (client cabinet)"
  - "Caddy routes both /m/* and /my/* to public:3002 without strip_prefix"
  - "Static asset serving via /assets/* Caddy handler"
  - "ClientCabinetPlaceholder component at /my/ route"
affects: [11-client-cabinet]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Full-path routing: SPA receives /m/... and /my/... paths, React Router matches them directly"
    - "No strip_prefix: Caddy forwards path as-is, SPA uses basename='/'"
    - "Asset routing: separate /assets/* Caddy handler for Vite build output with base '/'"

key-files:
  created: []
  modified:
    - Caddyfile
    - public/vite.config.ts
    - public/src/App.tsx
    - public/Dockerfile

key-decisions:
  - "Removed strip_prefix from /m/* Caddy block; SPA receives full /m/username path"
  - "Added /assets/* Caddy handler to serve Vite build output with base '/'"
  - "All navigate() calls use absolute /m/ prefix paths (pre-applied by 11-01)"

patterns-established:
  - "Dual-path SPA: same container serves /m/* and /my/* via full-path React Router routes"
  - "Asset serving: Caddy /assets/* block routes to public:3002 nginx for Vite output"

requirements-completed: [CCAB-01]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 11 Plan 02: Dual-Path SPA Routing Summary

**Caddy + Vite + Nginx reconfigured for dual-path SPA serving /m/* (master pages) and /my/* (client cabinet) from same container**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T05:09:12Z
- **Completed:** 2026-03-21T05:14:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Caddyfile updated with /m/*, /my/*, and /assets/* handlers (no strip_prefix)
- Vite base changed from "/m/" to "/" and BrowserRouter basename from "/m" to "/"
- React Router routes use full paths: /m/:username, /m/:username/book/*, /my, /my/*
- Nginx Dockerfile updated with location blocks for /m/, /my/, and /assets/
- ClientCabinetPlaceholder component added for /my/ routes (implemented in Plan 03)
- Build passes cleanly with new configuration

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Caddy, Vite, and Nginx for dual-path SPA** - `ae3c097` (feat)
2. **Task 2: Update all existing page navigation to /m/ prefix paths** - no new commit (changes pre-applied by 11-01 plan)

## Files Created/Modified
- `Caddyfile` - Added /my/* and /assets/* handlers, removed strip_prefix from /m/*
- `public/vite.config.ts` - Changed base from "/m/" to "/"
- `public/src/App.tsx` - basename="/", full-path routes, ClientCabinetPlaceholder
- `public/Dockerfile` - Nginx config with /m/, /my/, /assets/ location blocks

## Decisions Made
- Removed strip_prefix from /m/* Caddy block so SPA receives full /m/username path and React Router can distinguish /m/ from /my/ routes
- Added separate /assets/* Caddy handler because Vite base "/" generates asset URLs at /assets/* which would otherwise fall through to the API default handler
- Task 2 navigate changes were already applied by Plan 11-01 executor (no duplicate commit needed)

## Deviations from Plan

None - plan executed exactly as written. Task 2's navigate prefix changes were already present from Plan 11-01 execution, so no additional commit was needed.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- /my/ route renders placeholder; ready for Plan 03 to implement actual client cabinet UI
- /m/* routing unchanged functionally; all existing master page navigation works with /m/ prefixes
- Both paths served by same container, same build artifact

## Self-Check: PASSED

All files verified present. Commit ae3c097 verified in git log.

---
*Phase: 11-client-cabinet*
*Completed: 2026-03-21*
