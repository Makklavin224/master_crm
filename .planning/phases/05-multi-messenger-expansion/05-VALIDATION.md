---
phase: 5
slug: multi-messenger-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + httpx + pytest-asyncio |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `docker compose exec api uv run pytest tests/test_max*.py tests/test_vk*.py -x -q` |
| **Full suite command** | `docker compose exec api uv run pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick platform-specific tests
- **After every plan wave:** Run full suite
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | MSG-03..06 | unit | `pytest tests/test_auth_max.py tests/test_auth_vk.py` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | MSG-03, CLNT-04 | unit+integration | `pytest tests/test_max_bot.py` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | MSG-04 | build | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 2 | MSG-05, CLNT-04 | unit+integration | `pytest tests/test_vk_bot.py` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 2 | MSG-06 | build | `pnpm build && pnpm test` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `backend/tests/test_max_bot.py` — MAX adapter + handler tests
- [ ] `backend/tests/test_vk_bot.py` — VK adapter + handler tests
- [ ] `frontend/src/platform/adapters/__tests__/` — bridge adapter tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MAX Mini App opens | MSG-04 | Requires MAX client | Open MAX bot, tap menu, verify app loads |
| VK Mini App opens | MSG-06 | Requires VK client | Open VK community, launch mini-app |
| Cross-messenger identity | CLNT-04 | Requires 2 platforms | Book via TG, check history in VK |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify
- [ ] Sampling continuity maintained
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
