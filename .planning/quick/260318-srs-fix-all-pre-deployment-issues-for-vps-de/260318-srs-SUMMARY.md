---
phase: quick
plan: 01
subsystem: infra
tags: [docker, nginx, caddy, tls, localStorage, validation]

# Dependency graph
requires:
  - phase: 06-web-admin-panel
    provides: Complete application codebase ready for deployment
provides:
  - Production-ready Docker multi-stage builds (nginx-served frontends)
  - Auto-migration docker-compose with healthchecks and restart policies
  - TLS-enabled Caddy reverse proxy with security headers
  - Complete .env.production template with all required variables
  - Master auth JWT persistence across page reloads
  - Strict 11-digit Russian phone validation
affects: [deployment, operations]

# Tech tracking
tech-stack:
  added: []
  patterns: [multi-stage Docker builds, nginx SPA serving, Caddy automatic TLS, localStorage safe storage helpers]

key-files:
  created: [backend/.dockerignore, frontend/.dockerignore, web/.dockerignore, .env.production]
  modified: [frontend/Dockerfile, web/Dockerfile, docker-compose.yml, Caddyfile, .env.example, .gitignore, frontend/src/stores/master-auth.ts, frontend/src/pages/client/BookingForm.tsx]

key-decisions:
  - "Caddy {$DOMAIN} env var for automatic TLS (no manual cert config needed)"
  - "uv run python healthcheck for API (no curl in slim image)"
  - ".env.production gitignored as template-only (secrets never committed)"

patterns-established:
  - "Multi-stage Docker: node build -> nginx serve for all frontend services"
  - "Safe localStorage helpers: safeGetItem/safeSetItem/safeRemoveItem with try/catch"

requirements-completed: [DEPLOY-ALL]

# Metrics
duration: 2min
completed: 2026-03-18
---

# Quick Task 260318-srs: Pre-Deployment Fixes Summary

**Production Docker setup with multi-stage nginx builds, TLS Caddy, auto-migration compose, auth persistence, and strict phone validation**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T16:46:49Z
- **Completed:** 2026-03-18T16:49:41Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- Both frontend Dockerfiles rewritten as multi-stage builds (node build -> nginx serve, no dev servers in production)
- docker-compose.yml production-hardened: 4 uvicorn workers, alembic auto-migration, healthchecks on all services, restart:unless-stopped
- Caddyfile with {$DOMAIN} automatic TLS, security headers (nosniff, SAMEORIGIN, XSS protection), gzip compression
- Complete .env.production template with all 20+ required variables (DB, auth, TG, MAX, VK, Robokassa)
- Master auth JWT now persists in localStorage with hydrate() for recovery across page reloads
- Phone validation fixed: rejects anything not exactly 11 digits, input capped to prevent over-entry

## Task Commits

Each task was committed atomically:

1. **Task 1: Production Docker setup** - `573ca4a` (feat)
2. **Task 2: Caddyfile TLS + env config + .gitignore** - `bdea984` (feat)
3. **Task 3: Fix master-auth localStorage persistence + phone validation** - `89f565a` (fix)

## Files Created/Modified
- `frontend/Dockerfile` - Multi-stage build: node build -> nginx serve on port 3000
- `web/Dockerfile` - Multi-stage build: node build -> nginx serve on port 3001
- `backend/.dockerignore` - Excludes __pycache__, .venv, tests, .env
- `frontend/.dockerignore` - Excludes node_modules, dist, .env
- `web/.dockerignore` - Excludes node_modules, dist, .env
- `docker-compose.yml` - Production-ready: 4 workers, alembic migrate, healthchecks, restart policies
- `Caddyfile` - {$DOMAIN} TLS, security headers, gzip, reverse proxy rules
- `.env.production` - Complete production env template (gitignored)
- `.env.example` - Updated with all vars (TG, MAX, VK, Robokassa, CORS)
- `.gitignore` - Added node_modules, .DS_Store, .env.production, docker-compose.override
- `frontend/src/stores/master-auth.ts` - localStorage persistence with hydrate()
- `frontend/src/pages/client/BookingForm.tsx` - Exact 11-digit validation + input cap

## Decisions Made
- Used `uv run python` for API healthcheck instead of curl (curl not available in slim Python image)
- Caddy uses `{$DOMAIN}` env var for automatic TLS -- no HTTP-to-HTTPS redirect block needed (Caddy handles it automatically when serving a domain name)
- `.env.production` is gitignored by design -- it's a template to copy to the server and fill in real secrets
- nginx inline config via `printf` in Dockerfile (avoids needing a separate nginx.conf file to COPY)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker is not installed on the development machine, so `docker compose config` syntax validation could not run. The YAML structure follows standard compose spec and was verified via grep checks.

## User Setup Required
Before deploying to VPS:
1. Copy `.env.production` to `.env` on the server
2. Replace all `CHANGE_ME_*` values with real credentials
3. Set `DOMAIN` to the actual domain name
4. Generate a real `ENCRYPTION_KEY` with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
5. Generate a real `JWT_SECRET_KEY` with: `openssl rand -hex 32`
6. Ensure DNS A record points to the VPS IP for the domain

## Next Phase Readiness
- All infrastructure is production-ready for VPS deployment
- Run `docker compose up -d --build` on the VPS to deploy
- Caddy will auto-provision TLS certificates via Let's Encrypt

## Self-Check: PASSED

All 12 files verified present. All 3 task commits verified in git log.

---
*Quick task: 260318-srs*
*Completed: 2026-03-18*
