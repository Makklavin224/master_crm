---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + httpx (async) + pytest-asyncio |
| **Config file** | backend/pyproject.toml or "none — Wave 0 installs" |
| **Quick run command** | `docker compose exec api pytest tests/ -x -q` |
| **Full suite command** | `docker compose exec api pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec api pytest tests/ -x -q`
- **After every plan wave:** Run `docker compose exec api pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFR-01 | integration | `pytest tests/test_health.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | INFR-05 | unit | `pytest tests/test_models.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CLNT-02 | unit | `pytest tests/test_phone.py` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | INFR-04 | integration | `pytest tests/test_auth.py` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | INFR-02 | integration | `pytest tests/test_api.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/conftest.py` — shared fixtures (async client, test DB, auth helpers)
- [ ] `backend/tests/test_health.py` — health endpoint stub
- [ ] `backend/tests/test_models.py` — DB model creation stubs
- [ ] `backend/tests/test_phone.py` — phone normalization stubs
- [ ] `backend/tests/test_auth.py` — auth endpoint stubs
- [ ] `backend/tests/test_api.py` — basic API endpoint stubs
- [ ] pytest + httpx + pytest-asyncio — install in requirements-dev.txt

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker Compose full stack | INFR-01 | Docker-in-Docker not practical | Run `docker compose up`, verify all services healthy |
| Caddy reverse proxy | INFR-01 | Requires running Docker stack | `curl http://localhost/api/health` returns 200 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
