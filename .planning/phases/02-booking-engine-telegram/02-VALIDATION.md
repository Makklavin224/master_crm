---
phase: 2
slug: booking-engine-telegram
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest 8.x + httpx + pytest-asyncio |
| **Framework (frontend)** | vitest + @testing-library/react |
| **Config file (backend)** | backend/pyproject.toml |
| **Config file (frontend)** | frontend/vitest.config.ts |
| **Quick run (backend)** | `docker compose exec api uv run pytest tests/ -x -q` |
| **Quick run (frontend)** | `cd frontend && npm test -- --run` |
| **Full suite** | `docker compose exec api uv run pytest tests/ -v --tb=short && cd frontend && npm test -- --run` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick backend tests
- **After every plan wave:** Run full suite (backend + frontend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | BOOK-01 | integration | `pytest tests/test_services.py` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | BOOK-02 | integration | `pytest tests/test_schedule.py` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | BOOK-03,04 | integration | `pytest tests/test_bookings.py` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 2 | MSG-01,INFR-03 | integration | `pytest tests/test_bot.py` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 2 | CLNT-01,CLNT-03 | integration | `pytest tests/test_clients.py` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 3 | MSG-02,MSG-07 | e2e | `npm test -- --run` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 4 | BOOK-05,06,07 | integration | `pytest tests/test_booking_management.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_services.py` — service CRUD stubs
- [ ] `backend/tests/test_schedule.py` — schedule management stubs
- [ ] `backend/tests/test_bookings.py` — booking flow + double-booking stubs
- [ ] `backend/tests/test_bot.py` — webhook handler stubs
- [ ] `backend/tests/test_clients.py` — client auto-population stubs
- [ ] `frontend/vitest.config.ts` — vitest setup
- [ ] pytest fixtures for booking-related test data

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| TG Mini App opens in Telegram | MSG-02 | Requires Telegram client | Open t.me/BotName, tap menu button, verify mini-app loads |
| Bot notifications received | MSG-01 | Requires TG client | Create booking via API, verify master gets TG message |
| Platform detection | MSG-07 | Requires TG WebApp environment | Open mini-app in TG, verify platform detected correctly |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
