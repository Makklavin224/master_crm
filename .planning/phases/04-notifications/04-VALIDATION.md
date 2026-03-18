---
phase: 4
slug: notifications
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + httpx + pytest-asyncio |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `docker compose exec api uv run pytest tests/test_notifications.py tests/test_reminders.py -x -q` |
| **Full suite command** | `docker compose exec api uv run pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick notification tests
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | NOTF-03, BOOK-07 | integration | `pytest tests/test_notifications.py` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | NOTF-03, BOOK-07 | integration | `pytest tests/test_notifications.py` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | NOTF-01, NOTF-02 | unit+integration | `pytest tests/test_reminders.py` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | NOTF-01, NOTF-02 | type check | `npx tsc --noEmit` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_notifications.py` — booking confirmation + master alert tests
- [ ] `backend/tests/test_reminders.py` — APScheduler reminder service tests
- [ ] pytest fixtures for notification test data (mock adapters)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| TG reminder message format | NOTF-01/02 | Requires real TG bot | Trigger reminder, check message in TG |
| Inline cancel button works | NOTF-01/02 | Requires TG client | Tap cancel button in reminder, verify booking cancelled |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
