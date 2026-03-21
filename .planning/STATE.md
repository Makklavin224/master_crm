---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: Bugfix & Stabilization
status: complete
stopped_at: Completed 20-02-PLAN.md (error handling UX -- reviews, card formatting, Robokassa alert)
last_updated: "2026-03-21T10:48:14Z"
last_activity: 2026-03-21 -- Completed 20-02 (ReviewsPage error state, card formatting, Robokassa Alert)
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** Master taps "Complete" -- client gets SBP payment link -- tax receipt auto-generates. 3 steps instead of 9.
**Current focus:** v2.1 Bugfix & Stabilization -- Phase 20 (Medium-Priority Fixes)

## Current Position

Phase: 20 of 20 (Medium-Priority Fixes)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-03-21 -- Completed 20-01 (30s AbortController timeout + Russian error messages)

Progress: [████████░░] 83%

## Performance Metrics

**Velocity:**
- Total plans completed: 50 (v1.0: 17, v1.1: 8, v2.0: 25)
- Average duration: ~4min
- Total execution time: ~3.5 hours

**Recent Trend (v2.0):**
- Last 5 plans: 4min, 10min, 6min, 3min, 3min
- Trend: consistent

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- v2.1 scope: 27 bugs across 7 modules, zero new features
- Phase structure from bugfix spec: Critical (18) -> High (19) -> Medium (20)
- QR fix: dual QR codes (web link + TG deeplink), BOT_USERNAME from API
- Role detection: debounce guard + localStorage persistence + bridge.ready() wait
- Client auth: dual-path (cookie + Bearer token fallback)
- [Phase 18]: QR fix: bot_username from TG_BOT_USERNAME env var, TG deeplink uses master UUID as startapp param
- [Phase 18]: Module-level _detecting guard for async singleton race prevention (avoids zustand re-renders)
- [Phase 18]: RoleSwitcher visibility uses isAuthenticated instead of role===master to persist across view toggles
- [Phase 19]: SameSite=None for cross-origin cookie support in mobile webviews
- [Phase 19]: Cookie-first, Bearer-fallback auth strategy for get_current_client
- [Phase 19]: Frontend Bearer token via localStorage injected in apiRequest (not passed through store)
- [Phase 19]: UUID validation before API call to prevent invalid booking requests
- [Phase 19]: Frontend Bearer token via localStorage injected in apiRequest (not passed through store)
- [Phase 19]: UUID validation before API call to prevent invalid booking requests
- [Phase 20]: AbortSignal.any with typeof guard for caller signal merging (graceful degradation)
- [Phase 20]: 30s timeout with Russian error "Превышено время ожидания" on all API functions
- [Phase 20]: Used antd Result component for error state (consistent with admin design)
- [Phase 20]: Card number formatting via onChange + setFieldValue (avoids controlled input complexity)

### Pending Todos

None yet.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-21T10:48:06.527Z
Stopped at: Completed 20-02-PLAN.md (error handling UX -- reviews, card formatting, Robokassa alert)
Resume file: None
